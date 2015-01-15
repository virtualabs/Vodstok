<?php

/* Allow access from other domains: this is a web API ! */
header("Access-Control-Allow-Origin: *");

/**
 * Includes
 */

require_once('inc/ChunkManager.php');
require_once('inc/NodeManager.php');

$chunkManager = new ChunkManager($entityManager);
$nodeManager = new NodeManager($entityManager);

/* Chunk creation/retrieval. */
if (isset($_GET['chunk'])) {
    die($chunkManager->get($_GET['chunk']));
} else if (isset($_POST['chunk'])) {
    die($chunkManager->create($_POST['chunk']));
} else if (isset($_GET['stats'])) {
    $chunkManager->stats();
} else if (isset($_GET['endpoints'])) {
    die($nodeManager->random());
} else if (isset($_GET['register'])) {
    $nodeManager->register($_SERVER['REMOTE_ADDR'], $_GET['register']);
} else if (isset($_GET['version'])) {
    die(Settings::getVersion());
} else {
    readfile('vodka.old.html');
}


