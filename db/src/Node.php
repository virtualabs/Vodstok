<?php
/**
 * @Entity @Table(name="nodes")
 **/

class Node {

    /**
     * @Id @Column(type="integer") @GeneratedValue
     * @var int
     **/
    protected $id;

    /**
     * @Column(type="string")
     * @var string
     **/
    protected $url;

    /**
     * Getters
     **/

    public function getUrl() {
        return $this->url;
    }

    public function getId() {
        return $this->id;
    }

    /**
     * Setters
     **/

    public function setUrl($url) {
        $this->url = $url;
    }
};
