<?php

require_once "db/bootstrap.php";
require_once "inc/Settings.php";

/**
 * ChunkManager
 *
 * This class manages the chunks both in database and filesystem.
 **/

class ChunkManager {

    /* Entity Manager. */
    private $em;

    /**
     * Constructor.
     **/

    public function __construct($entityManager) {
        $this->em = $entityManager;
    }

    /**
     * error
     *
     * Returns an error as expected by any client.
     **/

    public function error($reason) {
        header('HTTP/1.0 404 '.$reason);
        die($reason);
    }

    /**
     * getConsumedSpace
     *
     * Compute the global size of all chunks.
     *
     * @return int Size consumed in bytes.
     **/

    public function getConsumedSpace() {
        $dql = "SELECT SUM(c.filesize) FROM Chunk c";
        $query = $this->em->createQuery($dql);
        return $query->getSingleScalarResult();
    }


    /**
     * getFreeSpace
     *
     * Compute free space based on quota.
     *
     * @return int Free space in bytes.
     **/

    public function getFreeSpace() {
        return (Settings::getMaxFsSpace() - $this->getConsumedSpace());
    }

    
    /**
     * removeOldestChunk
     *
     * Delete the oldest chunk.
     * $return int Oldest chunk id.
     **/

    protected function removeOldest() {
        $oldest_chunk = $this->getOldest();

        if ($oldest_chunk) {

            /* Remove chunk content from disk. */
            if (file_exists(Settings::getChunksDirectory().'/'.$oldest_chunk->getName())) {
                @unlink(Settings::getChunksDirectory().'/'.$oldest_chunk->getName());
            }

            /* Remove metadata from database. */
            $this->em->remove($oldest_chunk);
            $this->em->flush();
        }
    }


    /**
     * makeRoom
     *
     * Make enough room on this node. This operation causes
     * one or more calls to removeOldestChunk to free enough
     * FS space.
     **/

    public function makeRoom($space) {
        if ($space <= 32768) {
            while ($this->getFreeSpace() < $space) {
                $this->removeOldest();
            }
        }
    }


    /**
     * getOldestChunk
     *
     * Returns the oldest chunk, if any.
     *
     * @return Chunk Oldest chunk if found, NULL otherwise.
     **/

    private function getOldest() {
        $qb = $this->em->createQueryBuilder();
        $query = $qb->select('c')
                    ->from('Chunk','c')
                    ->orderBy('c.created', 'DESC')
                    ->getQuery();
        $chunks = $query->getResult();
        if (count($chunks) > 0) {
            return $chunks[0];
        } else {
            return NULL;
        }
    }

    /**
     * get
     *
     * Returns the content of a chunk.
     *
     * @param $id int Chunk identifier (md5 hash)
     * @return string Chunk content (base64 encoded)
     **/

    public function get($name) {
        $chunk = $this->em->getRepository('Chunk')->findOneBy(array(
            "name" => $name
        ));

        if ($chunk) {
            /* Update chunk. */
            $chunk->pull();
            $this->em->persist($chunk);
            $this->em->flush();

            /* Return chunk content. */
            return @base64_encode(file_get_contents(
                Settings::getChunksDirectory().'/'.$chunk->getName()
            ));
        } else {
            $this->error('ERR_UNK');
        }
    }


    /**
     * createChunk
     *
     * Create a chunk from supplied data.
     *
     * @param $data string Base64-encoded data to store in our chunk.
     **/

    public function create($data) {
        /* Ensure size. */
        $data = @base64_decode($data);
        if (strlen($data) > 32768)
            $this->error('ERR_TOO_LARGE');

        /* Check if chunk exists. */
        $chunk_name = md5($data.$_SERVER['REMOTE_ADDR'].time().rand());
        $chunks = $this->em->getRepository('Chunk')->findBy(array(
            "name" => $chunk_name
        ));
        if (count($chunks) == 0) {
            /* Make enough room for this chunk. */
            $this->makeRoom(strlen($data));

            /* Create chunk metadata. */
            $chunk = new Chunk($chunk_name, strlen($data));

            /* Write chunk content on disk. */
            $f = fopen(Settings::getChunksDirectory().'/'.$chunk->getName(), 'wb');
            if ($f) {
                fwrite($f, $data);
                fclose($f);

                /* If write is successful, update db. */
                $this->em->persist($chunk);
                $this->em->flush();

                return $chunk->getName();
            } else {
                $this->error('ERR_IO_ERROR');
            }
        } else {
            /* TODO: handles when md5 conflicts. Returns an error at the moment. */
            $this->error('ERR_EXISTS');
        }
    }


    /**
     * getMinChunkLifetime
     *
     * Compute the minimal chunk lifetime. This computation is based
     * on the age of the oldest chunk.
     *
     * @return int Minimum chunk lifetime in seconds.
     **/

    public function getMinChunkLifetime() {
        $now = new DateTime('now');
        $oldest_chunk = $this->getOldest();

        if ($oldest_chunk) {
            return ($now->getTimestamp() - $oldest_chunk->getCreationDate()->getTimestamp());
        } else {
            return -1;
        }
    }

    /**
     * getAverageUploadRate
     *
     * Compute the average upload rate. This computation is based on
     * the number of bytes uploaded in the last supplied time.
     *
     * @param $interval int Measure interval, in minutes.
     * @return array Upload rates (bytes/min) for each minute.
     **/

    public function getAverageUploadRate($interval) {
        /* We compute how much bytes have been uploaded since 0
         * to $interval minutes, minute by minute (max 30).
         */

        if ($interval > 30)
            $interval = 30;

        $upload_rates = array();
        for ($i = $interval; $i > 0; $i--) {
            $query = $this->em->createQueryBuilder()
                ->select('SUM(c.filesize)')
                ->from('Chunk', 'c')
                ->where('c.created > :last')
                ->setParameter('last', new DateTime('-'.$i.' minutes'), \Doctrine\DBAL\Types\Type::DATETIME)
                ->getQuery();
            $sum_bytes = $query->getSingleScalarResult();
            if (!$sum_bytes)
                $sum_bytes = 0;
            $upload_rates[$interval - $i] = $sum_bytes;
        }

        return $upload_rates;
    }


    /**
     * stats
     *
     * Displays the computed following stats:
     * - minimum chunk age
     * - last hour upload rate
     * - reputation
     **/

    public function stats() {
        /* Retrieve minimum chunk age. */
        $minAge = $this->getMinChunkLifetime();

        /* Compute last hour upload rate in bytes. */
        $query = $this->em->createQueryBuilder()
            ->select('SUM(c.filesize)')
            ->from('Chunk', 'c')
            ->where('c.created > :last')
            ->setParameter('last', new DateTime('-1 hour'), \Doctrine\DBAL\Types\Type::DATETIME)
            ->getQuery();
        $lastHourRate = $query->getSingleScalarResult();

        /* Displays the result. */
        if ($minAge == 0)
            $minAge = '0';
        if ($lastHourRate == 0)
            $lastHourRate = '0';
        die($minAge.','.$lastHourRate);
    }
}

