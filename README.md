		VODSTOK version 1.2
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
not readable on your server. Browse your remote folder and set
up vodstok.

Get the vodstok client (located in the client/ directory) and 
declare your endpoint:

$ ./vodstok add http://your.web.server/vodstok/

Once done, you can upload and download files to your server, and
share its URL. Other people using vodstok will be able to register
and use your endpoint for file sharing. If a server goes down, the
whole network stays available (but in fact many files could have
been impacted by the shutdown, the actual vodstok client providing
no redundancy at all).

It is also strongly recommended to publish your endpoint (through
the 'announce' option) and to update the endpoints list on a regular basis
(thanks to the 'update' option).

5. How to use Vodstok client ?

Vodstok client is pretty simple and still in beta. Server-side
scripts are very lite and would not be modified later, but our
client will be updated regularly.

Many operations can be performed with the provided client:
- endpoint management (registration, removal, listing, publishing)
- global capacity assessment
- file upload
- file download from a vodstok's URL


