<?php
use Doctrine\ORM\Tools\Setup;

require_once "vendor/autoload.php";



$paths = array(__DIR__."/src");
$isDevMode = true;

// the connection configuration
/* Mysql config -- not used right now
$dbParams = array(
    'driver'   => 'pdo_mysql',
    'user'     => 'dev',
    'password' => 'dev',
    'dbname'   => 'vodstok',
); */

/* sqlite config */
$dbParams = array(
    'driver' => 'pdo_sqlite',
    'path' => __DIR__ . '/vodstok.sqlite',
);

$config = Setup::createAnnotationMetadataConfiguration($paths, $isDevMode);
$entityManager = \Doctrine\ORM\EntityManager::create($dbParams, $config);
