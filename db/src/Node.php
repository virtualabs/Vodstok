<?php
/**
 * @Entity @Table(name="nodes")
 **/

class Node {

    /**
     * @Id @Column(type="integer") @Generated
     * @var int
     **/
    protected $id;

    /**
     * @Column(type="string")
     * @var string
     **/
    protected $url;

    /**
     * @OneToMany(targetEntity="Vote", mappedBy="node")
     **/
    protected $votes = null;

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
