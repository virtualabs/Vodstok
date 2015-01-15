<?php


class Settings {

    /* Max space on FS. */
    public static $maxFsSpace;

    /* Chunks storage directory. */
    public static $chunksDirectory;

    /* Max number of slots for node dictionnary. */
    public static $maxNodeSlots;

    public static function setMaxFsSpace($space) {
        self::$maxFsSpace = $space;
    }

    public static function getMaxFsSpace() {
        return self::$maxFsSpace;
    }

    public static function setChunksDirectory($chunksDir) {
        self::$chunksDirectory = $chunksDir;
    }

    public static function getChunksDirectory() {
        return self::$chunksDirectory;
    }

    public static function setMaxNodeSlots($nbSlots) {
        self::$maxNodeSlots = $nbSlots;
    }

    public static function getMaxNodeSlots() {
        return self::$maxNodeSlots;
    }

}

Settings::setMaxFsSpace(100 * 1024);
Settings::setChunksDirectory('chunks/');
Settings::setMaxNodeSlots(100);
