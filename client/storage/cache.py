import pickle,os

class Cache:
		# try to load our database
		self.db = os.path.join(homedir,'cache')
		if os.path.isdir(homedir):
			if os.path.isfile(self.db):
				f = open(self.db,'rb')
				self.files = pickle.load(f)
				f.close()
			else:
				self.files = []
				self.sync()
		else:
			os.mkdir(homedir)
			self.files = []
			self.sync()

	def sync(self):
		f = open(self.db,'wb')
		pickle.dump(self.files, f)
		f.close()

	def add(self, f):
		self.files.append(f)
		
	def remove(self, f):
		self.files.remove(f)
			
	def enum(self):
		for file in self.files:
			yield file
 