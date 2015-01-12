<?php

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
}


