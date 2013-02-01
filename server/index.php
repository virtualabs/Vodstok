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

/* Check if query string matches an ID */
if (preg_match('/^[a-f0-9]{32}-[a-f0-9]{32}$/i',$_SERVER['QUERY_STRING']))
{
    /* Uses a dedicated MIME type, for further usages (app, browser ext., ...) */
    header('Content-Type: application/x-vodstok');
    $url = 'http';
    if ($_SERVER['HTTPS']=='on')
        $url .= 's';
    $url .= '//';
    $url .= $_SERVER['SERVER_NAME'].':'.$_SERVER['SERVER_PORT'];
    $url .= $_SERVER['REQUEST_URI'];
    die($url);
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
?>
<html>
<head>
<title>Vodstok - Voluntary distributed Storage Kit</title>
</head>
<body>
<pre>
		VODSTOK version <?php echo(VERSION); ?>  
	(Voluntary Distributed Storage Kit)


1. Introduction

Vodstok is an opensource and free and viral project that aims
to provide a collaborative distributed storage to users who
want to store and share temporarily files on the Internet with
other users. 

2. Why "Voluntary Distributed Storage" ?

The concept of "Voluntary distributed storage" is very simple:
volunteers agree to let other users store data on a part of 
their webservers, and all those parts put together create a
big storage place where data can be pushed and pulled. Data is
sent encrypted (AES128) and a key is required to decrypt the
content, that means nobody can tell what is stored on a server.

Files are cut in parts (called "chunks") and these parts are sent
to several servers where Vodstok is installed (called "endpoints").
Endpoints are in fact open storage points where clients can send
data to store, whatever this data is. 

3. What does Vodstok need to be installed ?

You only have to own a web server, with PHP version 4.X or 5.X.
Drop the content of the www/ directory in a directory called
"vodstok" for instance, and make sure the chunks/ directory is
not readable on your server. 

Get the vodstok client (located in the client/ directory) and 
declare your endpoint:

$ ./vodstok -a http://your.web.server/vodstok/

Once done, you can upload and download files to your server, and
share its URL. Other people using vodstok will be able to register
and use your endpoint for file sharing. If a server goes down, the
whole network stays available (but in fact many files could have
been impacted by the shutdown, the actual vodstok client providing
no redundancy at all).

4. Why is this project "viral" ?

Once your Vodstok server functional, please drop the last version
of Vodstok in the root directory of this web application. A webpage
will be displayed when browsing the index page, and the kit would
be available from this page. This is the "viral" part.

5. How to use Vodstok client ?

Vodstok client is pretty simple and still in beta. Server-side
scripts are very lite and would not be modified later, but our
client will be updated regularly.

Many operations can be performed with the provided client:
- endpoint management (registration, removal, listing)
- global capacity assessment
- upload of a file
- download of a file thanks to a specific URL
</pre>
<br/><br/>
<b><a href="https://github.com/virtualabs/Vodstok/">Download Vodstok !</a></b>
</body>
</html>

<?php
}
?>
