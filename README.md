Vodstok version 1.2.5 RC2
=========================


Introduction
------------

Vodstok is an opensource and free and viral project that aims
to provide a collaborative distributed storage to users who
want to store and share temporarily files on the Internet with
other users. 

Why "Voluntary Distributed Storage" ?
-------------------------------------

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

What does Vodstok need to be installed ?
----------------------------------------

You only have to own a web server, with PHP version 4.X or 5.X.
Drop the content inside the www directory and make sure the 'chunks'
and 'endpoints' directory are writeable and not indexable on your server.
Browse your remote folder and set up vodstok.

Once done, you can upload and download files to your server, and
share them through dedicated URLs. The whole stuff is completely
transparent to the user, since an HTML5 client is displayed by
default for every visitor, making them able to upload/download
files through your node.

You'd also consider registering other vodstok servers thanks to
the feature provided on this web client.

Make some noise, spread the word !
----------------------------------

Vodstok provides:

 * On-the-fly encryption
 * Client to client file sharing
 * A decentralized voluntary-based storage network

Spread the word, make some noise and let your friends
know about this project !
