<?php

/**
 * Includes
 */

require_once('utils.php');

/**
 * Main dispatcher
 */

/* Is Vodstok installed ? */
if (!defined('INSTALLED'))
{
    /* Nope, let's install ! */
    header('Location: install.php');
    die('please install');
}

/* Version request */
else if (isset($_GET['version']))
    die(VERSION);
/* Statistics request */
else if (isset($_GET['stats']))
	dispStats();
/* Chunk retrieval request */
else if (isset($_GET['chunk']))
	dlChunk($_GET['chunk']);
/* Chunk upload request */
else if (isset($_POST['chunk']))
	createChunk($_POST['chunk']);
/* Servers (endpoints) dictionnary request */
else if (isset($_GET['endpoints']))
    listRandomServers();
/* Server announcement request */
else if (isset($_GET['register']))
    registerServer($_SERVER['REMOTE_ADDR'],$_GET['register']);
else
{
/* Main index page */
readfile('vodka.html');
}

