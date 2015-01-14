<?php

/**
 * Node votes
 *
 * A given IP may be able to vote X times per hour, to avoid trafficking. A vote basically tells
 * the node that this client trusts a given node. It may be same node or similar. If this is a new
 * node, it should be automatically registered.
 *
 * Only a single vote/ip is accepted. If a given vote/ip already exists, then the associated timestamp
 * is updated. Votes are cleaned on a regular basis (defined in settings ?). 
 **/

/**
 * @Entity @Table(name="votes")
 **/

class Vote {
    /**
     * @Id @Column(type="integer") @GeneratedValue
     * @var int
     **/

    protected $id;

    /**
     * @Column(type="string")
     * @var string
     **/

    protected $ip;

    /**
     * @ManyToOne(targetEntity="Node", inversedBy="votes")
     **/
    protected $node;

    /**
     * @Column(type="datetime")
     * @var DateTime
     **/

    protected $timestamp;

    /**
     * Getters
     **/

    public function getId() {
        return $this->id;
    }

    public function getIp() {
        return $this->ip;
    }

    public function getNode() {
        return $this->node;
    }

    public function getTimestamp() {
        return $this->timestamp;
    }

    /**
     * Setters
     **/

    public function setIp($ip) {
        $this->ip = $ip;
    }

    public function setNode($node) {
        $this->node = $node;
    }

    public function update() {
        $this->timestamp = new DateTime('now');
    }

};
