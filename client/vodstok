#!/usr/bin/python

"""

                  Voluntary Distributed Storage Kit
                    ----------------------------
                       Download/Upload client

"""

import sys
import os
import re
import socket
from optparse import OptionParser
from core.helpers import convert_bytes
from downup.manager import CmdLineManager
from core.server import Server, ServerIOError
from storage.user import User
from core.settings import Settings
from base64 import b64encode

socket.setdefaulttimeout(10.0)

class Options(OptionParser):
    """
    Command-line option parser (using optparse)
    """
    def __init__(self):
        OptionParser.__init__(self, usage="usage: %prog [options] [list|add|rm|announce|update|size] [URL | FILE]")
        self.add_option('-w', '--write', action="store", dest='dest_dir',
            metavar='DIRECTORY', help="Set destination directory", default='')
        self.add_option('-v', '--version', action="store_true", dest="showver",
            help="Show version")


class Vodstok:
    """
    Vodstok client.
    """
    def __init__(self):
        # read user's endpoint list
        self._db = User.get_instance().get_servers_db()



    #
    #       Servers management
    #

    def list_servers(self):
        """
        Displays every storage server declared
        """
        print '[+] Registered servers:'
        i = 0
        for server in self._db.enum():
            print ' + %s (%s)' % (server,convert_bytes(server.capacity))
            i += 1
        print '[i] %d registered server(s)' % i

    def has_duplicates(self, server):
        """
        Find duplicated servers.
        """
        data = b64encode(os.urandom(16))
        try:
            chunk = server.upload(data)
        except ServerIOError:
            server.down()
        for s in self._db.enum():
            try:
                dl = s.download(chunk)
                if (dl == data) and (server != s):
                    return True
            except ServerIOError, error:
                pass
        return False

    def add_server(self, server):
        """
        Add a server to the servers database
        """
        _server = Server(server)
        try:
            _version = _server.get_version()
            print '[i] Remote server version is %s' % _version
            _capacity = _server.get_capacity()
            print '[i] Remote server shares %s' % convert_bytes(_server.capacity)
            if _server.check():
                _server.set_version(_version)
                _server.set_active(True)
                self._db.add(_server)
                return True
            else:
                return False
        except ServerIOError:
            return False

    def remove_server(self, server):
        """
        Remove a server from the servers database
        """
        if not self._db.remove(Server(server)):
            print '[!] Unknown server'
        return

    def publish_server(self, server):
        """
        Publish a given server on every other servers
        """
        for _server in self._db.enum():
            if _server.url != server:
                sys.stdout.write(' + publishing on %s ... ' % _server.url)
                if _server.publish(server):
                    sys.stdout.write('ok\n')
                else:
                    sys.stdout.write('ko\n')

    def test_server(self, url):
        """
        Test a remote server to check if it is a valid vodstok storage server
        """
        return Server(url).check()

    def update_servers(self):
        """
        Publish a given server on every other servers
        """

        # Step 0: checking current servers
        print '[+] Checking current servers ...'
        for server in self._db.servers:
            sys.stdout.write(' > checking %s ... ' % server.url)
            sys.stdout.flush()
            if not server.check() and server.is_active():
                sys.stdout.write('not working, disabled\n')
                sys.stdout.flush()
                server.set_active(False)
            else:
                sys.stdout.write('success\n')
                sys.stdout.flush()
                server.set_active(True)
        self._db.sync()

        # Step 1: get a pool of 10 random active servers
        print '[+] Collecting new servers from Vodstok network ...'
        pot_servers = []
        dictionaries = self._db.pick_random(10)
        if len(dictionaries)>0:
            for dictionary in dictionaries:
                try:
                    servers = dictionary.list_registered_endpoints()
                    if servers is not None:
                        for server in servers:
                            if (not self._db.has(server)) and (not server in pot_servers):
                                pot_servers.append(server)
                except ServerIOError:
                    pass
        else:
            print "[!] No server registered. Use 'add' to register one."
            return

        done = 0
        if len(pot_servers)>0:
            print '[+] %d new servers collected.' % len(pot_servers)
            print '[+] Checking collected servers ... '
            for server in pot_servers:
                sys.stdout.write(' > checking %s ... ' % server)
                sys.stdout.flush()
                try:
                    version = server.get_version()
                    if server.check():
                        if not self.has_duplicates(server):
                            server.set_version(version)
                            server.set_active(True)
                            self._db.add(server)
                            sys.stdout.write('registered\n')
                            sys.stdout.flush()
                            done +=1
                        else:
                            sys.stdout.write('existing\n')
                            sys.stdout.flush()
                            server.set_active(False)
                            self._db.add(server)
                    else:
                        sys.stdout.write('not working\n')
                        sys.stdout.flush()
                        server.set_active(False)
                        self._db.add(server)
                except ServerIOError:
                    server.set_active(False)
                    self._db.add(server)
                    pass
            print '[+] %d new servers registered' % done
        else:
            print '[!] No new servers found'

        print '[+] Propagating servers URLs ...'
        for _server in self._db.enum():
            endpoint = self._db.pick_random()
            try:
                endpoint.publish(_server.url)
            except ServerIOError:
                pass
        print '[i] Done.'
        self._db.sync()

    def get_random_server(self, filesize=0):
        """
        Retrieve a random server from registered servers
        """
        return self._db.pick_random()

    def is_vds_url(self, url):
        """
        Check wether the provided URL is a Vodstok URL or not
        """
        return (re.match('^(http|https)://([^#]+)#(.*)$', url) is not None)

    def get_global_capacity(self):
        """
        Computes the overall storage capacity (based on every servers declared)
        """
        total_chunks = 0
        total_used = 0
        total_quota = 0
        i = 1
        for server in self._db.enum():
            cap = (float(i)*100/len(self._db))
            sys.stdout.write('\r[+] Computing global capacity ... %0.2f%%' % cap)
            sys.stdout.flush()
            res = server.get_capacity()
            if res:
                quota, used, chunks, usage = res
                total_chunks += chunks
                total_used += used
                total_quota += quota
            i += 1
        sys.stdout.write('\n')
        return (total_quota, total_used, total_chunks)


#
#       Vodstok Main
#

if __name__ == '__main__':
    a = Vodstok()
    (options, args) = Options().parse_args()
    if options.showver:
        print 'Vodstok version %s' % Settings.version
    elif len(args)>=1:
        if len(args)==2:
            if args[0] == 'add':
                print '[i] Testing remote server ...'
                if a.add_server(args[1]):
                    print '[i] Registered server %s' % args[1]
                else:
                    print '[!] Server does not seem to work properly.'
            elif args[0] == 'rm':
                print '[i] Removing server ...'
                a.remove_server(args[1])
                print '[i] Servers list:'
                a.list_servers()
            elif args[0] == 'announce':
                print '[i] Announcing server ...'
                a.publish_server(args[1])
        else:
            if args[0] == 'update':
                #print '[i] Updating servers ...'
                a.update_servers()
            elif args[0] == 'list':
                a.list_servers()
            elif args[0] == 'size':
                quota, used, chunks = a.get_global_capacity()
                print ''
                print 'Statistics:'
                print ''
                print '- Global storage space   : %s' % convert_bytes(quota)
                print '- Used storage space     : %s' % convert_bytes(used)
                print '- # of chunks            : %d' % chunks
            elif a.is_vds_url(args[0]):
                manager = CmdLineManager()
                manager.download(args[0], options.dest_dir)
            else:
                if os.path.exists(args[0]):
                    manager = CmdLineManager()
                    manager.upload(args[0])
                else:
                    Options().print_help()
    else:
        Options().print_help()
