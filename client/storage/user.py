"""
Storage helpers
"""

import os
from servers import *

class User:
	
	PROJECT_DIR = '.vodstok'
	TEMP_DIR = 'temp'
	
	def __init__(self):
		self.__homedir = os.getenv('USERPROFILE') or os.getenv('HOME')
		self.__projdir = os.path.join(self.__homedir,User.PROJECT_DIR)
		self.__servers = None
		self.__cache = None

	def getProjectDir(self):
		return self.__projdir

	def load(self):
		if not self.isInstalled():
			self.install()
		self.__servers = ServersDB(self.__projdir)
		return

	def enumServers(self):
		return self.__servers.enum()

	def isInstalled(self):
		#try:
		if 1:
			return os.path.exists(os.path.join(self.__homedir,User.PROJECT_DIR))
		#except:
		#	raise StorageException()
		
	def install(self):
		try:
			os.mkdir(self.__projdir)
		except:
			raise StorageException()
			
if __name__ == '__main__':
	sto = UserStorage()
	sto.load()