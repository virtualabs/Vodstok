"""
Storage helpers
"""

import os
from storage.servers import ServersDB
from core.exception import StorageException

class User:
	
    """
    User
	
    This class is used to get user-related information such as servers
    (repositories) list, home path, ...
    """
	
    PROJECT_DIR = '.vodstok'
    TEMP_DIR = 'temp'
	
    gUser = None
    
    @staticmethod
    def getInstance():
        """
        Returns a single instance of User class.
        
        Use this method to retrieve the unique instance of User().
        """
        if User.gUser is None:
            User.gUser = User()
        return User.gUser
	
    def __init__(self):
        """
        Constructor
        """
        self.__homedir = os.getenv('USERPROFILE') or os.getenv('HOME')
        self.__projdir = os.path.join(self.__homedir, User.PROJECT_DIR)
        self.__servers = None
        self.load()

    def getProjectDir(self):
        """
        Retrieve the project directory (win & nux compatible)
        """
        return self.__projdir

    def load(self):
        """
        Load user's profile.
        
        This method loads the current user profile or creates it if this
        profile does not exist.
        """
        if not self.isInstalled():
            self.install()
        self.__servers = ServersDB(self.__projdir)

    def getServersDB(self):
        """
        Return an instance of ServersDB class.
        """
        return self.__servers

    def enumServers(self):
        """
        Yields every server registered in the user's database.
        """
        return self.__servers.enum()

    def isInstalled(self):
        """
        Check if Vodstok is correctly installed and install it if not.
        """
        try:
            return os.path.exists(
                os.path.join(self.__homedir, User.PROJECT_DIR)
            )
        except:
            raise StorageException()
		
    def install(self):
        """
        Create the project directory (install routine)
        """
        try:
            os.mkdir(self.__projdir)
        except:
            raise StorageException()
