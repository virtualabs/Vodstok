<?php

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

    public function getTimestamp() {
        return $this->timestamp;
    }

};
