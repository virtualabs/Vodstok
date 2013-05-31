"""
Vodstok server HTTP/S client

Manage communications between Vodstok's client and remote servers
"""

import re
import os
import socket
import urllib
import httplib
import urllib2
import urlparse
from base64 import b64encode
from core.exception import ServerIOError
from core.helpers import normalize

class Server:
    """
    Vodstok remote storage client

    This class is used to communicate with Vodstok's servers.
    """

    def __init__(self, url):
        self.version = None
        self.capacity = 0
        self.usage = -1
        self.note = 5
        self.active = True
        self.set_url(normalize(url))
        self.headers = { "Accept" : "*/*" }

    def set_version(self, version):
        self.version = version

    def set_capacity(self, capacity):
        self.capacity = capacity

    def set_active(self, active):
        self.active = active

    def is_active(self):
        return self.active

    def set_note(self, note):
        self.note = note

    def up(self):
        if self.is_active() and self.note < 5:
            # server is active and its note can be increased ? increase.
            self.note += 1
        elif not self.is_active():
            # server was inactive and is now active and working, increase note
            # and no longer marked as inactive.
            self.note += 1
            self.set_active(True)

    def down(self):
        if self.is_active() and self.note > 0:
            self.note -= 1
            if self.note == 0:
                self.set_active(False)

    def set_url(self, url):
        url_info = urlparse.urlparse(url)
        self.scheme = url_info.scheme
        self.server = url_info.netloc
        self.uri = url_info.path
        self.url = urlparse.urlunparse(
            (
                self.scheme,
                self.server,
                self.uri,
                '',
                '',
                ''
            )
        )
        self.posturl = self.uri
        self.dlurl = '%s://%s%s?chunk=' % (self.scheme, self.server, self.uri)
        self.puburl = '%s://%s%s?register=' % (
            self.scheme, self.server, self.uri
        )
        self.statsurl = '%s://%s%s?stats' % (
            self.scheme, self.server, self.uri
        )
        self.epurl = '%s://%s%s?endpoints' % (
            self.scheme, self.server, self.uri
        )
        self.versionurl = '%s://%s%s?version' % (
            self.scheme, self.server, self.uri
        )

    def upload(self, chunk):
        """
        Upload of raw chunk of datae
        """
        params = {
            'chunk':chunk,
        }
        try:
            # Send request
            p = urllib.urlencode(params)
            r = httplib.HTTPConnection(self.server)
            r.putrequest('POST', self.posturl)
            r.putheader('Content-Type', 'application/x-www-form-urlencoded')
            r.putheader('Content-Length', str(len(p)))
            r.putheader('User-Agent','vodstok')
            r.putheader('Accept','*/*')
            r.endheaders()
            r.send(p)

            # Analyze response
            resp = r.getresponse()
            if resp.status == 200:
                # check if the returned ID is a MD5 hash
                id = resp.read()
                if re.match('[0-9a-fA-F]{32}', id):
                    return id
                else:
                    raise ServerIOError()
            else:
                raise ServerIOError()
        except:
            raise ServerIOError()

    def download(self, id):
        """
        Download a chunk of data based on its ID
        (returned by the upload method above)
        """
        try:
            r = urllib2.Request(self.dlurl+id, headers=self.headers)
            resp = urllib2.urlopen(r)
            if resp:
                return resp.read()
            else:
                raise ServerIOError()
        except urllib2.HTTPError:
            raise ServerIOError()
        except urllib2.URLError:
            raise ServerIOError()
        except httplib.IncompleteRead:
            raise ServerIOError()
        except httplib.BadStatusLine:
            raise ServerIOError()
        except socket.timeout:
            raise ServerIOError()
        except socket.error:
            raise ServerIOError()

    def publish(self, endpoint_url):
        """
        Publish a given endpoint on this endpoint
        """
        try:
            r = urllib2.Request(self.puburl+urllib.quote(endpoint_url), headers=self.headers)
            resp =  urllib2.urlopen(r)
            if resp:
                return (resp.getcode() == 200)
            return False
        except urllib2.URLError, error:
            raise ServerIOError()
        except urllib2.HTTPError, error:
            if error.getcode() == 404:
                return False
            raise ServerIOError()

    def list_registered_endpoints(self):
        """
        Retrieve a sample of published endpoints
        """
        try:
            r = urllib2.Request(self.epurl, headers=self.headers)
            resp =  urllib2.urlopen(r)
            if resp:
                return [Server(url) for url in resp.read().split(',')]
            return []
        except urllib2.HTTPError:
            raise ServerIOError()
        except urllib2.URLError:
            raise ServerIOError()
        except httplib.IncompleteRead:
            raise ServerIOError()
        except httplib.BadStatusLine:
            raise ServerIOError()
        except socket.timeout:
            raise ServerIOError()
        except socket.error:
            raise ServerIOError()

    def alias(self, a):
        return '%s?%s' % (self.url, a)

    def check(self):
        try:
            self.get_capacity()
            self.get_version()
            data = b64encode(os.urandom(16))
            chunk_id = self.upload(data)
            output = self.download(chunk_id)
            return (output == data)
        except ServerIOError:
            return False

    def get_capacity(self):
        """
        Get endpoint statistics (quota, used space and number of chunks present)
        """
        try:
            r = urllib2.Request(self.statsurl, headers=self.headers)
            resp = urllib2.urlopen(r)
            if resp:
                content = resp.read()
                r = re.search(
                    ('quota:([0-9]+),used:([0-9]+),'
                    'chunks:([0-9]+),usage:([0-9]+)'),
                    content
                )
                if r:
                    self.capacity = int(r.group(1))
                    self.usage = int(r.group(4))
                    return (
                        int(r.group(1)),
                        int(r.group(2)),
                        int(r.group(3)),
                        int(r.group(4))
                    )
                else:
                    return None
            else:
                return None
        except urllib2.HTTPError:
            raise ServerIOError()
        except urllib2.URLError:
            raise ServerIOError()
        except httplib.IncompleteRead:
            raise ServerIOError()
        except httplib.BadStatusLine:
            raise ServerIOError()
        except socket.timeout:
            raise ServerIOError()
        except socket.error:
            raise ServerIOError()
        except ValueError:
            raise ServerIOError()

    def __str__(self):
        return self.url

    def __eq__(self, other):
        return (self.url==other.url)

    def get_version(self):
        """
        Retrieve server version
        """
        try:
            r = urllib2.Request(self.versionurl, headers=self.headers)
            resp = urllib2.urlopen(r)
            if resp:
                self.version = resp.read()
                return self.version
            else:
                return None
        except urllib2.HTTPError:
            return None
        except urllib2.URLError:
            return None
        except httplib.InvalidURL:
            return None
        except ValueError:
            return None
        except socket.error:
            return None

    def serialize(self):
        return {
            'url':self.url,
            'version':self.version,
            'note':self.note,
            'active':self.active,
            'capacity':self.capacity
        }

    @staticmethod
    def unserialize(serialized):
        check_keys = ['url', 'version', 'active', 'capacity', 'note']
        for key in check_keys:
            if key not in serialized:
                return None
        server = Server(serialized['url'])
        server.set_active(serialized['active'])
        server.set_version(serialized['version'])
        server.set_capacity(serialized['capacity'])
        server.set_note(serialized['note'])
        return server

