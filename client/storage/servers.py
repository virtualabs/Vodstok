import pickle,os,urlparse
from random import choice
from downup.server import Server

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
		self.db = os.path.join(homedir,'servers')
		if os.path.isdir(homedir):
			if os.path.isfile(self.db):
				f = open(self.db,'rb')
				self.servers = pickle.load(f)
				f.close()
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
		f = open(self.db,'wb')
		pickle.dump(self.servers, f)
		f.close()

	def normalize(self, url):
		"""
		Clean an url in order to add it to the servers list
		"""
		url_info = urlparse.urlparse(url)
		server = url_info.netloc
		uri = url_info.path
		while '//' in uri:
			uri = uri.replace('//','/')
		url = 'http://%s%s' % (server,uri)
		if url[-1]!='/':
			url += '/'
		return url


	def remove(self, server):
		"""
		Remove a server from the DB given its URL.
		"""
		server = self.normalize(server) 
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
		server = self.normalize(server)
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
			
	def pickRandom(self):
		"""
		Return a randomly chosen server.
		"""
		return Server(choice(self.servers))
 