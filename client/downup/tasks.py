import uuid,urlparse,os
from time import time
from core.client import VodstokStorage
from stream.filestream import *
from random import shuffle
from threading import Lock

class Task:

	ST_SUSPENDED = 1
	ST_RUNNING = 0
	ST_CANCEL = 2
	
	def __init__(self):
		self.__state = Task.ST_RUNNING
		self.__processing = []
		self.__processed = []
		self.__left = []
		
	def getLeft(self):
		return self.__left
		
	def getTopLeft(self):
		if len(self.__left)>0:
			return self.__left[0]
		else:
			return None
		
	def getProcessed(self):
		return self.__processed
		
	def getProcessing(self):
		return self.__processing		

	def isProcessing(self, task):
		return (task in self.__processing)
	
	def setLeft(self, left):
		self.__left = left
		
	def markAsProcessed(self, task):
		if task in self.__processing:
			self.__processing.remove(task)
			self.__processed.append(task)
	
	def markAsProcessing(self, task):
		if task in self.__left:
			self.__left.remove(task)
			self.__processing.append(task)
			
	def markAsLeft(self, task):
		if task in self.__processing:
			self.__processing.remove(task)
			self.__left.append(task)
		
	def resume(self):
		if self.__state == Task.ST_SUSPENDED:
			print '[+] Task resumed'
			self.__state = Task.ST_RUNNING
		
	def suspend(self):
		if self.__state == Task.ST_RUNNING:
			print '[+] Task suspended'
			self.__state = Task.ST_SUSPENDED
			
	def cancel(self):
		self.__state = Task.ST_CANCEL
		
	def isCanceled(self):
		return self.__state == Task.ST_CANCEL
		
	def isSuspended(self):
		return self.__state == Task.ST_SUSPENDED
		
	def isRunning(self):
		return self.__state == Task.ST_RUNNING	

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
		except ServerIOError,e:
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
		except ServerIOError,e:
			self.alias = None
			return False

class DownloadFileTask(Task):
	
	def __init__(self, manager, aliases, stream):
		Task.__init__(self)
		self.__manager = manager
		self.__stream = stream
		self.__ntasks = len(aliases)
		self.__completed = False
		self.__file_lock = Lock()
		
		# init tasks
		tasks = [DownloadChunkTask(self, i,aliases[i]) for i in range(len(aliases))]
		shuffle(tasks)
		self.setLeft(tasks)

	def isCompleted(self):
		return self.__completed

	def getNextTask(self):
		if len(self.getLeft())>0 and self.isRunning():
			self.__file_lock.acquire()
			chunk_task = self.getTopLeft()
			self.markAsProcessing(chunk_task)
			self.__file_lock.release()
			return chunk_task
		else:
			return None
			
	def onTaskDone(self, task):
		"""
		Callback called when upload task is done
		"""
		if self.isProcessing(task):
			self.markAsProcessed(task)
			self.__file_lock.acquire()
			self.__stream.writeChunk(task.getChunk(),index=task.getIndex())
			self.__file_lock.release()
			if len(self.getProcessing())==0 and len(self.getLeft())==0:
				self.onCompleted()
			else:
				if self.__manager is not None:
					self.__manager.onProgress(self, len(self.getProcessed()), self.__ntasks)
			return True
		else:
			return False

	def onTaskError(self, task):
		print '[!] Error during task #%d' % task.getIndex()
		self.markAsLeft(task)
		return
		
	def onCompleted(self):
		self.__completed = True
		if self.__manager is not None:
			self.__manager.onDownloadFileCompleted(self)
	

class UploadFileTask(Task):
	
	def __init__(self, manager, stream):
		Task.__init__(self)
		self.__manager = manager
		self.__stream = stream
		self.__ntasks = self.__stream.getNbChunks()
		self.__completed = False
		self.__file_lock = Lock()
		self.__errors = 0

		# init tasks
		tasks = [i for i in range(self.__stream.getNbChunks())]
		shuffle(tasks)
		self.setLeft(tasks)
		self.__chunks = []
		

	def isCompleted(self):
		return self.__completed
		
	def getNextTask(self):
		if len(self.getLeft())>0 and self.isRunning():
			self.__file_lock.acquire()
			task = self.getTopLeft()
			self.markAsProcessing(task)
			chunk_task = UploadChunkTask(self, task, self.__stream.readChunk(index=task))
			self.__file_lock.release()
			return chunk_task
		else:
			return None

	def onTaskDone(self, task):
		"""
		Callback called when upload task is done
		"""
		self.__errors = 0
		if self.isProcessing(task.getIndex()):
			self.markAsProcessed(task.getIndex())
			self.__chunks.append((task.getIndex(), task))
			if len(self.getProcessing())==0 and len(self.getLeft())==0:
				self.onCompleted()
			else:
				if self.__manager is not None:
						self.__manager.onProgress(self, len(self.getProcessed()), self.__ntasks)
			return True
		else:
			return False
		
	def onTaskError(self, task):
		self.__errors += 1
		if self.__errors > 3:
			if self.__manager is not None:
				self.__manager.onError(self)
		else:
			self.markAsLeft(task.getIndex())
		return
		
	def onCompleted(self):
		self.__completed = True
		if self.__manager is not None:
			self.__manager.onUploadFileCompleted(self)

	def getAliases(self):
		self.__chunks.sort()
		return [a[1].getAlias() for a in self.__chunks]


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
		#print self.__alias+'#'+self.__chunk_id
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
