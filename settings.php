<?php


class Settings {

    public static $maxFsSpace;

    public static function setMaxFsSpace($space) {
        self::$maxFsSpace = $space;
    }

    public static function getMaxFsSpace() {
        return self::$maxFsSpace;
    }

}
