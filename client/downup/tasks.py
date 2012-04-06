import uuid,urlparse,os
from time import time
from core.client import VodstokStorage
from stream.filestream import *
from random import shuffle
from threading import Lock

class EndpointIOError(Exception):
	def __init__(self):
		Exception.__init__(self)

class ChunkTask:
	def __init__(self, parent, index, alias=None, chunk=None):
		self.__parent = parent
		self.__index = index
		self.chunk = chunk
		self.alias = alias
		
	def getIndex(self):
		return self.__index

	def getParentFileTask(self):
		return self.__parent

	def getAlias(self):
		return self.alias

	def getChunk(self):
		return self.chunk				

class DownloadChunkTask(ChunkTask):
	def __init__(self, parent, index, alias):
		ChunkTask.__init__(self, parent, index,alias=alias)

	def process(self, server):
		try:
			server,alias = self.alias.split('#')
			self.chunk = VodstokStorage(server).download(alias)
			return (self.chunk is not None)
		except EndpointIOError,e:
			self.chunk = None
			return False

class UploadChunkTask(ChunkTask):
	def __init__(self, parent, index, chunk):
		ChunkTask.__init__(self, parent, index, chunk=chunk)
				
	def process(self, server):
		try:
			self.alias = server.upload(self.chunk)
			if self.alias is not None:
				self.alias = server.alias(self.alias)
			return (self.alias is not None)
		except EndpointIOError,e:
			self.alias = None
			return False

class DownloadFileTask:
	
	def __init__(self, manager, aliases, stream):
		self.__manager = manager
		self.__stream = stream
		self.__downloaded_chunks = []
		self.__ntasks = len(aliases)
		self.__chunk_downloading = []
		self.__chunk_tasks = [(i,aliases[i]) for i in range(len(aliases))]
		self.__start = 0.0
		self.__remaining = 0.0
		self.__completed = False
		self.__file_lock = Lock()
		self.__suspended = False

	def isCompleted(self):
		return self.__completed

	def isCompleted(self):
		return self.__completed
		
	def isSuspended(self):
		return self.__suspended
		
	def suspend(self):
		self.__suspended = True
		
	def resume(self):
		self.__suspended = False

	def cancel(self):
		self.__completed = True

	def getNextTask(self):
		if len(self.__chunk_tasks)>0:
			next_task,task_alias = self.__chunk_tasks.pop(0)
			chunk_task = DownloadChunkTask(self,next_task,task_alias)
			self.__chunk_downloading.append(next_task)
			return chunk_task
		else:
			return None
			
	def onTaskDone(self, task):
		"""
		Callback called when upload task is done
		"""
		print '[i] Task #%d done: %s' % (task.getIndex(),task.getAlias()) 
		if task.getIndex() in self.__chunk_downloading:
			print '[i] Removing task from downloading list'
			print '[i] Left: %d chunks' % len(self.__chunk_tasks)
			self.__chunk_downloading.remove(task.getIndex())
			self.__downloaded_chunks.append(task.getIndex())
			print '[i] Write chunk to disk'
			self.__file_lock.acquire()
			self.__stream.writeChunk(task.getChunk(),index=task.getIndex())
			self.__file_lock.release()
			if len(self.__chunk_downloading)==0 and len(self.__chunk_tasks)==0:
				self.onCompleted()
			else:
				if self.__manager is not None:
					self.__manager.onProgress(self, len(self.__downloaded_chunks), self.__ntasks)
			return True
		else:
			return False
		
	def onTaskError(self, task):
		print '[!] Error during task #%d' % task.getIndex()
		self.__chunk_downloading.remove(task.getIndex())
		self.__chunk_tasks.append((task.getIndex(),task.getAlias()))
		return
		
	def onCompleted(self):
		self.__completed = True
		if self.__manager is not None:
			self.__manager.onDownloadFileCompleted(self)
	

class UploadFileTask:
	
	def __init__(self, manager, stream):
		self.__manager = manager
		self.__stream = stream
		self.__uploaded_chunks = []
		self.__ntasks = self.__stream.getNbChunks()
		self.__chunk_uploading = []
		self.__chunk_tasks = [i for i in range(self.__stream.getNbChunks())]
		shuffle(self.__chunk_tasks)
		self.__start = 0.0
		self.__remaining = 0.0
		self.__completed = False
		self.__file_lock = Lock()
		self.__errors = 0
		self.__suspended = False

	def isCompleted(self):
		return self.__completed
		
	def isSuspended(self):
		return self.__suspended
		
	def suspend(self):
		self.__suspended = True
		
	def cancel(self):
		self.__completed = True
		
	def resume(self):
		self.__suspended = False

	def getNextTask(self):
		if len(self.__chunk_tasks)>0:
			next_task = self.__chunk_tasks.pop()
			self.__file_lock.acquire()
			chunk_task = UploadChunkTask(self, next_task, self.__stream.readChunk(index=next_task))
			self.__file_lock.release()
			self.__chunk_uploading.append(next_task)
			return chunk_task
		else:
			return None

	def onTaskDone(self, task):
		"""
		Callback called when upload task is done
		"""
		#print '[i] Task #%d done: %s' % (task.getIndex(),task.getAlias()) 
		self.__errors = 0
		if task.getIndex() in self.__chunk_uploading:
			#print '[i] Removing task from uploading list'
			#print '[i] Left: %d chunks' % len(self.__chunk_tasks)
			self.__chunk_uploading.remove(task.getIndex())
			self.__uploaded_chunks.append((task.getIndex(),task))
			if len(self.__chunk_uploading)==0 and len(self.__chunk_tasks)==0:
				self.onCompleted()
			else:
				if self.__manager is not None:
						self.__manager.onProgress(self, len(self.__uploaded_chunks), self.__ntasks)
			return True
		else:
			return False
		
	def onTaskError(self, task):
		self.__errors += 1
		if self.__errors > 3:
			if self.__manager is not None:
				self.__manager.onError(self)
		else:
			self.__chunk_uploading.remove(task.getIndex())
			self.__chunk_tasks.append(task.getIndex())
		return
		
	def onCompleted(self):
		self.__completed = True
		if self.__manager is not None:
			self.__manager.onUploadFileCompleted(self)

	def getAliases(self):
		self.__uploaded_chunks.sort()
		return [a[1].getAlias() for a in self.__uploaded_chunks]

class DownTask:
	
	INIT=-1
	SUMMARY=0
	RECVING=1
	DONE=2
	
	def __init__(self, manager=None, url=''):
		self.uuid = uuid.uuid1()
		self.__manager = manager
		self.__filename = None
		self.__key = None
		self.__alias = None
		self.__url = url
		self.__scheme = None
		self.__chunk_id = None
		self.__state = DownTask.INIT
		self.__task = None
		self.__parse()
		
	def __parse(self):
		r = urlparse.urlparse(self.__url)
		self.__scheme = r.scheme
		self.__key,self.__server = r.netloc.split('@')
		self.__key = self.__key.decode('hex')
		self.__path = r.path
		self.__chunk_id = r.fragment
		self.__file = MemoryStream('',key=self.__key)
		self.__alias = '%s://%s%s' % (self.__scheme,self.__server,self.__path)

	def cancel(self):
		self.__task.cancel()
		
	def suspend(self):
		self.__task.suspend()
		
	def resume(self):
		self.__task.resume()

	def setManager(self, manager=None):
		self.__manager = manager
	
	def process(self):
		self.__state = DownTask.SUMMARY
		print self.__alias+'#'+self.__chunk_id
		self.__task = DownloadFileTask(self, [self.__alias+'#'+self.__chunk_id], self.__file)
		if self.__manager is not None:
			self.__manager.queueTask(self.__task)
		
	def onDownloadFileCompleted(self, task):
		if self.__state == DownTask.SUMMARY:
			filename,chunks = self.__file.read().split('|')
			if filename=='metadata':
				self.__file = MemoryStream('',key=self.__key)
				self.__task = DownloadFileTask(self, chunks, self.__file)
			else:
				self.__state=DownTask.RECVING
				self.__file = FileStream(open(filename,'wb'), key=self.__key)
				self.__task = DownloadFileTask(self, chunks.split(','), self.__file)
			if self.__manager is not None:
				self.__manager.queueTask(self.__task)
		elif self.__state == DownTask.RECVING:
			self.__state = DownTask.DONE
			self.__file.close()
			if self.__manager is not None:
				self.__manager.onTaskDone(self)
	
	def onProgress(self, task, done, total):
		if self.__state == DownTask.RECVING:
			if self.__manager is not None:
				self.__manager.onTaskProgress(self, done, total)

	def onError(self, task):
		self.__manager.onTaskError(self)

class UpTask:
	
	INIT=-1
	SENDING=0
	SUMMARY=1
	DONE=2	
	
	def __init__(self, manager=None, filename='unk.bin'):
		self.uuid = uuid.uuid1()
		self.__manager = manager
		self.__filename = os.path.basename(filename)
		self.__file = FileStream(open(filename,'rb'))
		self.__key = self.__file.getKey()
		self.__state = UpTask.INIT
		self.__task = UploadFileTask(self, self.__file)
		self.__alias = None

	def setManager(self, manager=None):
		self.__manager = manager

	def process(self):
		# process task
		# -> launch a file upload
		print '[+] Sending chunks ...'
		self.__state = UpTask.SENDING
		if self.__manager is not None:
			self.__manager.queueTask(self.__task)

	def cancel(self):
		self.__task.cancel()
		
	def suspend(self):
		self.__task.suspend()
		
	def resume(self):
		self.__task.resume()

	def onUploadFileCompleted(self, task):
		if self.__state == UpTask.SENDING:
			meta = '%s|%s'%(self.__filename,','.join(task.getAliases()))
			if len(meta)>Settings.chunk_size:
				print '[+] Sending metadata ...'
				meta = 'metadata|%s'%(','.join(task.getAliases()))
				if self.__manager is not None:
					self.__task = UploadFileTask(self, MemoryStream(meta, key=self.__key))
					self.__manager.queueTask(self.__task)
					#self.__manager.uploadFile(self, 'metadata', MemoryStream(meta, key=self.__key))
			else:
				print '[+] Sending summary ...'
				self.__state = UpTask.SUMMARY
				self.__task = UploadFileTask(self, MemoryStream(meta, key=self.__key))
				if self.__manager is not None:
					self.__manager.queueTask(self.__task)
		elif self.__state == UpTask.SUMMARY:
			self.__state = UpTask.DONE
			self.__alias = task.getAliases()[0]
			if self.__manager is not None:
				self.__manager.onTaskDone(self)

	def getUrl(self):
		if self.__state == UpTask.DONE:
			# split the alias
			p = urlparse.urlparse(self.__alias)
			k = self.__key.encode('hex')
			return '%s://%s@%s%s#%s' % (p.scheme,k,p.netloc,p.path,p.fragment)
		else:
			return None
		

	def onProgress(self, task, done, total):
		if self.__state == UpTask.SENDING:
			if self.__manager is not None:
				self.__manager.onTaskProgress(self, done, total)
				
	def onError(self, task):
		self.__manager.onTaskError(self)

	
	def getKey(self):
		return self.__key

class TaskStatus:
	TASK_PENDING = -1
	TASK_CANCEL = 0
	TASK_RUNNING = 1
	TASK_DONE = 2	
	TASK_ERR = 3

class TaskRef:
	def __init__(self, task, status=TaskStatus.TASK_PENDING, progress=0.0, speed=0.0):
		self.object = task
		self.status = status
		self.progress = progress
		self.speed = speed
		self.last = (0,time())
		
	def update(self, done, total):
		c,t = self.last
		now = time()
		if (time()-t)>0:
			self.speed = float((done - c)*Settings.chunk_size)/(now-t)
		else:
			self.speed = 0
		self.progress = float(done)/total
		
	def __getattr__(self, attr):
		if hasattr(self.object, attr):
			return getattr(self.object, attr)
		else:
			raise AttributeError()
