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

    public function hasEmpltySlot() {
        $nb_slots = $this->em->getRepository('Node')
                    ->createQueryBuilder()
                    ->select('COUNT(n.id)')
                    ->from('Node','n')
                    ->getQuery()
                    ->getSingleScalarResult();

        return ($nb_slots < Settings::getMaxNodeSlots());
    }

    /**
     * random
     *
     * Return a random list of nodes, based on their reputation.
     *
     **/

    public function random() {
        return 'http://share.local/';
    }

    /**
     * find
     *
     * TODO
     *
     * Find node given its URL, if existing
     *
     * @param string urlNode Node's url
     * @return Node Similar node if found, null otherwise.
     **/

    public function find($urlNode) {
        /* 1. Explode the URL and keeps interesting parts. */
        /* 2. Compare fqdn against shorter forms (i.e. virtualabs.fr instead of www.virtualabs.fr)
         *    and try to find an existing node based on this. */
    }

    /**
     * removeOldest
     *
     * TODO
     *
     * Remove the oldest node
     **/

    public function removeOldest() {
    }
    
    /**
     * register
     *
     * Register node based on its URL.
     *
     * @param string urlNode Node's url
     * @return bool True on success, false otherwise.
     **/

    public function register($urlNode) {
        /* If this node does not exist, register it. */
        $node = $this->find($urlNode);
        if (!$node) {
            /* If no more slots available, free the oldest one. */
            if (!$this->hasEmptySlot)
                $this->removeOldest();

            /* Register node. */
            $node = new Node();
            $node->setUrl($urlNode);
            $this->em->persist($node);
            $this->em->flush();
        }

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
        /* Get node. */
        $node = $this->register($urlNode);

        /* Find previous vote if any. */
        $vote = $this->em->getRepository('Vote')->createQueryBuilder()
            ->select('v')
            ->from('Vote','v')
            ->where('v.ip == :ip AND v.node == :node')
            ->setParameter('ip', $ip)
            ->setParameter('node', $node)
            ->getQuery()
            ->getResult();

        if ($vote) {
            /* If already voted, update. */
            $vote->update();
            $this->em->persist($vote);
        } else {
            /* If first vote, create. */
            $vote = new Vote();
            $vote->setIp($ip);
            $vote->setNode($node);
        }

        /* Flush database. */
        $this->em->flush();
    }

}

