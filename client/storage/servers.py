"""
Vodstok server database
"""

import pickle
import os
from random import choice

from downup.server import Server
from core.helpers import normalize

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
        if os.path.isdir(homedir):
            if os.path.isfile(self._db):
                database = open(self._db, 'rb')
                self.servers = pickle.load(database)
                database.close()
            else:
                self.servers = []
                self.sync()
        else:
            os.mkdir(homedir)
            self.servers = []
            self.sync()

    def __len__(self):
        return len(self.servers)
    
    def sync(self):
        """
        Synchronize memory data and disk data.
        """
        database = open(self._db,'wb')
        pickle.dump(self.servers, database)
        database.close()

    def remove(self, server):
        """
        Remove a server from the DB given its URL.
        """
        server = normalize(server) 
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
        server = normalize(server)
        if server not in self.servers:
            self.servers.append(server)
            self.sync()
            return True
        return False
            
    def enum(self):
        """
        Yields every server URL wrapped into a Server object.
        
        This is a generator, meant to be used in a for loop.
        """
        for server in self.servers:
            yield Server(server)
            
    def pick_random(self):
        """
        Return a randomly chosen server.
        """
        return Server(choice(self.servers))
 