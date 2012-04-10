import os
import re
import urlparse
import uuid
from time import time
from core.settings import Settings
from stream import MemoryStream,FileStream
from scheduler import Scheduler,dummyRepManager
from tasks import DownloadFileTask,UploadFileTask,UpTask,DownTask,TaskStatus,TaskRef


class DownUpManager:

	gDownUpManager = None

	@staticmethod
	def getInstance():
		if DownUpManager.gDownUpManager is None:
			DownUpManager.gDownUpManager = DownUpManager()
		return DownUpManager.gDownUpManager
	
	def __init__(self):
		self.__scheduler = Scheduler(dummyRepManager())
		self.__tasks = {}
		self.__running = False
		self.__listeners = []
		self.ensureRun()
		
	def ensureRun(self):
		if self.__running == False:
			self.__scheduler.start()
			self.__running = True

	## Listeners 

	def registerListener(self, listener):
		if listener not in self.__listeners:
			self.__listeners.append(listener)

	def removeListener(self, listener):
		if listener in self.__listeners:
			self.__listeners.remove(listener)

	## Events

	def notifyTaskDone(self, task):
		for listener in self.__listeners:
			listener.onTaskDone(task)
			
	def notifyTaskProgress(self, task, progress):
		for listener in self.__listeners:
			listener.onTaskProgress(task, progress)

	def notifyTaskCancel(self, task):
		for listener in self.__listeners:
			listener.onTaskCancel(task)
			
	def notifyTaskSuspended(self, task):
		for listener in self.__listeners:
			listener.onTaskSuspended(task)

	def notifyTaskResumed(self, task):
		for listener in self.__listeners:
			listener.onTaskResumed(task)

	def notifyTaskError(self, task):
		for listener in self.__listeners:
			listener.onTaskError(task)

	## Task management

	def queueTask(self, task):
		self.__scheduler.queueTask(task)

	def __registerTask(self, task):
		if task.uuid not in self.__tasks:
			self.__tasks[task.uuid] = TaskRef(task)

	def upload(self, filename):
		t = UpTask(self, filename)
		self.__registerTask(t)
		return t.uuid
		
	def download(self, url):
		t = DownTask(self, url)
		self.__registerTask(t)
		return t.uuid
		
	def startTask(self, task):
		if task in self.__tasks:
			self.__tasks[task].object.process()

	def removeTask(self, task):
		if task in self.__tasks:
			self.__tasks[task].cancel()
			del self.__tasks[task]
			
	def suspendTask(self, task):
		if task in self.__tasks:
			self.__tasks[task].suspend()
			
	def resumeTask(self, task):
		if task in self.__tasks:
			self.__tasks[task].resume()		

	def getTaskStatus(self, task):
		if task in self.__tasks:
			return self.__tasks[task].status

	def getTask(self, task):
		if task in self.__tasks:
			return self.__tasks[task]
		else:
			return None

	def cancel(self, task):
		if task in self.__tasks:
			self.__tasks[task].cancel()
		self.notifyTaskCancel(task)

	def shutdown(self):
		self.__scheduler.cancel()
		self.__scheduler.join()


	## Events
		
	def onTaskDone(self, task):
		if task.uuid in self.__tasks:
			self.__tasks[task.uuid].status=TaskStatus.TASK_DONE
			self.notifyTaskDone(task.uuid)
			
	def onTaskError(self, task):
		if task.uuid in self.__tasks:
			self.__tasks[task.uuid].status=TaskStatus.TASK_ERR
			self.notifyTaskError(task.uuid)
			
	def onTaskProgress(self, task, done, total):
		if task.uuid in self.__tasks:
			self.__tasks[task.uuid].update(done, total)
			self.notifyTaskProgress(task.uuid,float(done)/total)
		
