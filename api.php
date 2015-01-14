<?php

/* Allow access from other domains: this is a web API ! */
header("Access-Control-Allow-Origin: *");

/**
 * Includes
 */

require_once('inc/ChunkManager.php');

$chunkManager = new ChunkManager($entityManager);

/* Chunk creation/retrieval. */
if (isset($_GET['chunk'])) {
    die($chunkManager->get($_GET['chunk']));
} else if (isset($_POST['chunk'])) {
    $chunkManager->create($_POST['chunk']);
} else if (isset($_GET['stats'])) {
    $chunkManager->stats();
}


