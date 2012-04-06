import socket,sys,urllib
from threading import Thread
from random import choice
from httplib import HTTPException
from client import VodstokStorage
from db import VodstokDB

WORKERS = 5


#
#	Upload management
#


class UploadTask:
	def __init__(self, endpoint, id, data):
		self.endpoint = endpoint
		self.id = id
		self.data = data

class UploadWorker(Thread):
	
	def __init__(self, callback):
		Thread.__init__(self)
		self.callback = callback
		
	def run(self):
		# get pending task
		task = self.callback.getPendingTask()
		
		# process task
		while task is not None:
			try:
				#print '[+] Start download chunk #%d' % task.id
				chunk_id = task.endpoint.upload(task.data)
				if chunk_id is None:
					#self.callback.chunkError(task.id)
					task.endpoint = self.callback.getRandomEndpoint()
					continue
				#print '[+] Chunk #%d uploaded' % task.id
				self.callback.chunkUploaded(task.id, chunk_id, task.endpoint)
			except HTTPException,e:
				#print '[!] Chunk #%d upload error' % task.id
				#self.callback.chunkError(task.id)
				# change endpoint
				task.endpoint = self.callback.getRandomEndpoint()
				continue
			except socket.error,e:
				#print '[!] Chunk #%d upload errpr' % task.id
				task.endpoint = self.callback.getRandomEndpoint()
				continue
			task = self.callback.getPendingTask()
						
class UploadManager:

	def __init__(self, endpoints, chunks, filesize):
		self.workers = [UploadWorker(self) for i in range(WORKERS)]
		self.pending_tasks = []
		self.endpoints = endpoints
		self.chunk_ids = [None for i in chunks]
		self.chunks = chunks
		self.filesize = filesize

	def getRandomEndpoint(self):
		eps = []
		for e,capacity in self.endpoints:
			if capacity>self.filesize:
				eps.append(e)
		if len(eps)==0:
			return None
		return choice(eps)

	def getPendingTask(self):
		if len(self.pending_tasks)>0:
			return self.pending_tasks.pop()
		else:
			return None

	def chunkUploaded(self, chunk_pos, chunk_id, endpoint):
		self.chunk_ids[chunk_pos] = (endpoint.url,chunk_id)
		sys.stdout.write('\r[+] Uploading ... %0.2f%%' % (float(len(self.chunks)-len(self.pending_tasks))*100.0/len(self.chunks)))		
		sys.stdout.flush()

	def upload(self):
		# add everything as pending tasks
		for i in range(len(self.chunks)):
			self.pending_tasks.append(UploadTask(self.getRandomEndpoint(), i , self.chunks[i]))
		
		sys.stdout.write('\r[+] Uploading ... %0.2f%%' % (float(len(self.chunks)-len(self.pending_tasks))*100.0/len(self.chunks)))		
		sys.stdout.flush()
		
		# and start processing
		for worker in self.workers:
			worker.start()
			
		# wait until workers stop
		for worker in self.workers:
			worker.join()
			
		sys.stdout.write('\n')
		sys.stdout.flush()
		return self.chunk_ids


#
#	Download management
#


class DownloadTask:
	def __init__(self, pos, chunk):
		self.pos = pos
		self.url,self.chunk_id = chunk
		

class DownloadWorker(Thread):
	
	def __init__(self, callback):
		Thread.__init__(self)
		self.callback = callback
		
	def run(self):
		# get pending task
		task = self.callback.getPendingTask()
		
		# process task
		while task is not None and not self.callback.shouldStop():
			try:
				#print '[+] Start download chunk #%d' % task.id
				chunk = VodstokStorage(task.url).download(task.chunk_id)
				if chunk is None:
					self.callback.chunkError(task.pos)
				#print '[+] Chunk #%d uploaded' % task.id
				self.callback.chunkDownloaded(task, chunk)
			except urllib.URLError,e:
				self.callback.chunkError(task.pos)
			except socket.error,e:
				self.callback.chunkError(task.pos)
			task = self.callback.getPendingTask()

class DownloadManager:

	def __init__(self, chunks):
		self.workers = [DownloadWorker(self) for i in range(WORKERS)]
		self.pending_tasks = []
		self.chunks = chunks
		self.content = [None for i in self.chunks]
		self.canceled = False
		self.db = VodstokDB()

	def getPendingTask(self):
		if len(self.pending_tasks)>0:
			return self.pending_tasks.pop()
		else:
			return None

	def chunkDownloaded(self, task, chunk):
		print task.pos,len(chunk)
		self.content[task.pos] = chunk
		self.db.addEndpoint(task.url)
		sys.stdout.write('\r[+] Downloading ... %0.2f%%' % (float(len(self.chunks)-len(self.pending_tasks))*100.0/len(self.chunks)))		
		sys.stdout.flush()

	def chunkError(self):
		self.canceled = True
		
	def shouldStop(self):
		return self.canceled

	def download(self):
		# add everything as pending tasks
		for i in range(len(self.chunks)):
			self.pending_tasks.append(DownloadTask(self.chunks[i][0],self.chunks[i][1]))
		
		sys.stdout.write('\r[+] Downloading ... %0.2f%%' % (float(len(self.chunks)-len(self.pending_tasks))*100.0/len(self.chunks)))		
		sys.stdout.flush()
		
		# and start processing
		for worker in self.workers:
			worker.start()
			
		# wait until workers stop
		for worker in self.workers:
			worker.join()
		sys.stdout.write('\n')
		sys.stdout.flush()
		return ''.join(self.content)

