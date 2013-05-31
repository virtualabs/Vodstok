"""
Vodstok server database
"""

import pickle
import os
from random import shuffle

from core.settings import Settings
from core.server import Server

class ServersDB:

    """
    Vodstok server database

    This version of the database is a bit crappy, but this will be
    improved in the upcoming versions.

    The actual database only stores servers URL in a file called
    'servers' in the user's project directory. The data inside this file
    is pickled.
    """

    def __init__(self, homedir):
        # try to load our database
        self._db = os.path.join(homedir, 'servers')
        self.version = Settings.version
        if os.path.isdir(homedir):
            if os.path.isfile(self._db):
                database = open(self._db, 'rb')
                try:
                    version, servers = pickle.load(database)
                    self.servers = []
                    for server in servers:
                        self.servers.append(Server.unserialize(server))
                    database.close()
                except:
                    self.servers = []
                    self.sync()
            else:
                self.servers = []
                self.sync()
        else:
            os.mkdir(homedir)
            self.servers = []
            self.sync()

    def __len__(self):
        return len(self.servers)

    def has(self, server):
        """
        Check if a server is already known
        """
        return (server in self.servers)

    def sync(self):
        """
        Synchronize memory data and disk data.
        """
        database = open(self._db,'wb')
        db_content = Settings.version, [s.serialize() for s in self.servers]
        pickle.dump(db_content, database)
        database.close()

    def remove(self, server):
        """
        Remove a server from the DB given its URL.
        """
        if server in self.servers:
            self.servers.remove(server)
            self.sync()
            return True
        return False

    def add(self, server):
        """
        Add a server given its URL.

        The server URL is not added if already present.
        """
        if server not in self.servers:
            self.servers.append(server)
            self.sync()
            return True
        return False

    def update(self, server):
        """
        Update a server given its URL.
        """
        if server in self.servers:
            self.servers.remove(server)
            self.servers.append(server)
            self.sync()
            return True
        return False

    def count_active(self):
        active = 0
        if self.servers is not None:
            for server in self.servers:
                if server.is_active():
                    active += 1
        return active

    def enum(self, active=True):
        """
        Yields every server URL wrapped into a Server object.

        This is a generator, meant to be used in a for loop.
        """
        if self.servers is not None:
            for server in self.servers:
                if active:
                    if server.is_active():
                        yield server
                else:
                    yield server

    def pick_random(self, count=1):
        """
        Return a randomly chosen server.
        """
        # keeps only active servers
        active_servers = []
        for server in self.servers:
            if server.is_active():
                active_servers.append(server)
        # shuffle
        shuffle(active_servers)

        # return a random slice
        if self.count_active()>0:
            if count>1:
                return active_servers[:count]
            else:
                return active_servers[0]
        else:
            return active_servers

