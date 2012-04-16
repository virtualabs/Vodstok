import pickle,os,urlparse
from random import choice
from downup.server import Server

class ServersDB:
	
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

	def sync(self):
		f = open(self.db,'wb')
		pickle.dump(self.servers, f)
		f.close()

	def normalize(self, url):
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
		server = self.normalize(server) 
		if server in self.servers:
			self.servers.remove(server)
			self.sync()
			return True
		return False
	
	def add(self, server):
		server = self.normalize(server)
		if server not in self.servers:
			self.servers.append(server)
			self.sync()
			return True
		return False
			
	def enum(self):
		for server in self.servers:
			yield Server(server)
			
	def pickRandom(self):
		return Server(choice(self.servers))
 