<?php

require_once "db/bootstrap.php";
require_once "inc/Settings.php";

/**
 * NodeManager
 *
 * This class handles the nodes and their associated votes.
 **/

class NodeManager {
    
    /* Entity Manager. */
    private $em;

    /**
     * Constructor.
     **/

    public function __construct($entityManager) {
        $this->em = $entityManager;
    }

    /**
     * hasEmptySlot
     *
     * Check if an empty slot is available.
     *
     * @return bool true if an empty slot is found, false otherwise.
     **/

    public function hasEmptySlot() {
        $nb_slots = $this->em->createQueryBuilder()
                    ->select('COUNT(n.id)')
                    ->from('Node','n')
                    ->getQuery()
                    ->getSingleScalarResult();

        return ($nb_slots < Settings::getMaxNodeSlots());
    }

    /**
     * random
     *
     * TODO
     *
     * Return a random list of nodes, based on their reputation.
     *
     **/

    public function random($count) {
        $nodes = $this->em->getRepository('Node')->findAll();

        /* Populate an array based on votes. */ 
        $nodes_array = array();
        foreach ($nodes as $node) {
            for ($i=0; $i<$node->countVotes(); $i++)
                array_push($nodes_array,$node->getUrl());
        }

        /* Randomly chose $count of them. */
        shuffle($nodes_array);
        return array_slice($nodes_array, 0, $count);
    }

    /**
     * find
     *
     * Find node given its URL, if existing
     *
     * @param string urlNode Node's url
     * @return Node Similar node if found, null otherwise.
     **/

    public function find($urlNode) {
        $fragments = parse_url($urlNode);
        $scheme = $fragments['scheme'];
        $host = $fragments['host'];
        if (array_key_exists('port', $fragments))
           $port = $fragments['port'];
        else
            $port = null;
        $uri = $fragments['path'];

        /* First search by http scheme. */
        $url = 'http://'.$host;
        if ($port)
            $url .= $port;
        $url .= $uri;

        $node = $this->em->getRepository('Node')
            ->findOneBy(array(
                'url' => $url
            ));

        if ($node) {
            return $node;
        } else {
            $url = 'https://'.$host;
            if ($port)
                $url .= $port;
            $url .= $uri;

            $node = $this->em->getRepository('Node')
                ->findOneBy(array(
                    'url' => $url
                ));

            return $node;
        }   
    }

    /**
     * removeOldest
     *
     * TODO
     *
     * Remove the node with the oldest votes.
     **/

    public function removeOldest() {
        $query = $this->em->createQuery('SELECT
            n,
            (SELECT MAX(v.timestamp) FROM Vote v WHERE v.node = n) as last_vote
            FROM Node n 
            ORDER BY last_vote ASC'
        );
        $nodes = $query->getResult();
        if ($nodes) {
            $oldest_node = $nodes[0][0];
            $this->em->remove($oldest_node);
            $this->em->flush();
        }
    }
    
    /**
     * register
     *
     * Register node based on its URL.
     *
     * @param string urlNode Node's url
     * @return bool True on success, false otherwise.
     **/

    public function register($ip, $urlNode) {
        /* If this node does not exist, register it. */
        $node = $this->find($urlNode);
        if (!$node) {
            /* If no more slots available, free the oldest one. */
            if (!$this->hasEmptySlot())
                $this->removeOldest();

            /* Register node. */
            $node = new Node();
            $node->setUrl($urlNode);
            $this->em->persist($node);
            $this->em->flush();
        }

        /* Vote for this node. This will also commit db changes. */
        $this->vote($ip, $urlNode);

        /* Returns node. */
        return $node;
    }

    /**
     * vote
     *
     * Vote for a given node. A vote is based on IP and Node.
     *
     * @param string ip Votant IP address
     * @param string urlNode Node's URL
     * @return bool true on success, false otherwise
     **/

    public function vote($ip, $urlNode) {

        $node = $this->find($urlNode);

        /* Find previous vote if any. */
        $vote = $this->em->getRepository('Vote')
            ->findOneBy(array(
                'ip' => $ip,
                'node' => $node
        ));

        if ($vote) {
            /* If already voted, update. */
            $vote->update();
            $this->em->persist($vote);
        } else {
            /* If first vote, create. */
            $vote = new Vote();
            $vote->setIp($ip);
            $vote->setNode($node);
            $vote->update();
            $this->em->persist($vote);
        }

        /* Flush database. */
        $this->em->flush();
    }

}

