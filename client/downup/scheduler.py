from threading import Thread
from time import sleep
from core.settings import Settings

class Worker(Thread):
    
    """
    Scheduler worker
    """
    
    def __init__(self, scheduler, task):
        Thread.__init__(self)
        self.task = task
        self.sched = scheduler
        self.__canceled = False

    def cancel(self):
        self.__canceled = True
		
    def run(self):
        while not self.__canceled:
            task = self.sched.getPendingTask()
            if task is not None:
                if task.process(self.sched.acquireRepository()):
                    self.sched.releaseRepository()
                    self.sched.onWorkerDone(task)
                else:
                    self.sched.onWorkerError(task)
            sleep(0.1)


class Scheduler(Thread):

    def __init__(self, rep_manager):
        Thread.__init__(self)
        self.__rep_manager = rep_manager
        self.workers = [Worker(self, None) for i in range(Settings.max_threads)]
        self.tasks = []
        self.__canceled = False

    def cancel(self):
        for w in self.workers:
            w.cancel()
        self.__canceled = True

    def getRandomRepository(self):
        return
		
    def acquireRepository(self):
        return self.__rep_manager.pickRandom()
		
    def releaseRepository(self):
        return

    def queueTask(self, task):
        self.tasks.append(task)
		
    def removeTask(self, task):
        if task in self.tasks:
            self.tasks.remove(task)

    def getPendingTask(self):
        if len(self.tasks)>0:
            file_task = self.tasks[0]
            if file_task is None:
                return None
            else:
                if not file_task.isCompleted():
                    # get a chunk task from the file task
                    chunk_task = file_task.getNextTask()
                    if chunk_task is not None:
                        # put the file task at the end of the list
                        self.tasks.append(self.tasks.pop(0))
                        return chunk_task
                else:
                    self.tasks.remove(file_task)
                    return None
        else:
            return None
		
    def onWorkerDone(self, chunk_task):
        file_task = chunk_task.getParentFileTask()
        file_task.onTaskDone(chunk_task)					

	def onWorkerError(self, chunk_task):
		file_task = chunk_task.getParentFileTask()
		file_task.onTaskError(chunk_task)

    def run(self):
        # start workers
        for w in self.workers:
            w.start()
        # let workers do the job
        while len(self.tasks)>0 and not self.__canceled:
            sleep(0.1)
			
