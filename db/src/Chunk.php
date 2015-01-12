<?php

/**
 * @Entity @Table(name="chunks")
 **/
class Chunk {
    /**
     * @Id @Column(type="string")
     * @var string
     **/
    protected $name;

    /**
     * @Column(type="datetime", options={"default": 0})
     * @var DateTime
     **/
    protected $created;

    /**
     * @Column(type="datetime", options={"default" : 0})
     * @var DateTime
     **/
    protected $last_pulled;

    /**
     * @Column(type="integer")
     * @var int
     **/

    protected $filesize = 0;

    /**
     * Constructor.
     **/

    public function __construct($name, $filesize) {
        /* Get actual datetime. */
        $now = new DateTime('now');

        /* Set name and filesize. */
        $this->setName($name);
        $this->setFilesize($filesize);

        /* Set creation and pull dates. */
        $this->created = $now;
        $this->last_pulled = $now;
    }

    /**
     * Getters
     */

    public function getCreationDate() {
        return $this->created;
    }

    public function getLastPullDate() {
        return $this->last_pulled;
    }

    public function getName() {
        return $this->name;
    }

    public function getFilesize() {
        return $this->filesize;
    }

    /**
     * Setters
     **/

    public function pull() {
        $this->last_pulled = new DateTime('now');
    }

    public function setName($name) {
        $this->name = $name;
    }

    public function setFilesize($filesize) {
        $this->filesize = $filesize;
    }

};
