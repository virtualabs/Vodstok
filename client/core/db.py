import os
import pickle

class VodstokDB:
	
	def __init__(self):
		# try to load our database
		homedir = os.path.expanduser('~/.vodstok')
		self.db = homedir+'/endpoints'
		if os.path.isdir(homedir):
			if os.path.isfile(self.db):
				f = open(self.db,'rb')
				self.endpoints = pickle.load(f)
				f.close()
			else:
				self.endpoints = []
				self.sync()
		else:
			os.mkdir(homedir)
			self.endpoints = []
			self.sync()

	def sync(self):
		f = open(self.db,'wb')
		pickle.dump(self.endpoints, f)
		f.close()

	def removeEndpoint(self, endpoint):
		if endpoint in self.endpoints:
			self.endpoints.remove(endpoint)
			self.sync()	
	
	def addEndpoint(self, endpoint):
		if endpoint not in self.endpoints:
			self.endpoints.append(endpoint)
			self.sync()
			
	def listEndpoints(self):
		for endpoint in self.endpoints:
			yield endpoint
 