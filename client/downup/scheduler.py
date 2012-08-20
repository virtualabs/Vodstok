"""
Vodstok asynchronous task scheduler

Okay, maybe Twisted may help a bit but i'm not a twisted lover.
"""

import sys
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
            sys.stdout.flush()
            task = self.sched.get_pending_task()
            if task is not None:
                if task.process(self.sched.acquire_repository()):
                    self.sched.release_repository()
                    self.sched.on_worker_done(task)
                else:
                    self.sched.on_worker_error(task)
            sleep(0.1)


class Scheduler(Thread):

    def __init__(self, rep_manager):
        Thread.__init__(self)
        self.__rep_manager = rep_manager
        self.workers = [Worker(self, None) for i in range(Settings.max_threads)]
        self.tasks = []
        self.__canceled = False

    def cancel(self):
        for worker in self.workers:
            worker.cancel()
        self.__canceled = True

    def get_random_repository(self):
        return
		
    def acquire_repository(self):
        return self.__rep_manager.pick_random()
		
    def release_repository(self):
        return

    def queue_task(self, task):
        self.tasks.append(task)
		
    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)

    def get_pending_task(self):
        if len(self.tasks)>0:
            file_task = self.tasks[0]
            if file_task is None:
                return None
            else:
                if not file_task.is_completed():
                    # get a chunk task from the file task
                    chunk_task = file_task.get_next_task()
                    if chunk_task is not None:
                        # put the file task at the end of the list
                        self.tasks.append(self.tasks.pop(0))
                        return chunk_task
                else:
                    self.tasks.remove(file_task)
                    return None
        else:
            return None
		
    def on_worker_done(self, chunk_task):
        file_task = chunk_task.get_parent_filetask()
        file_task.on_task_done(chunk_task)					

    def on_worker_error(self, chunk_task):
        file_task = chunk_task.get_parent_filetask()
        file_task.on_task_error(chunk_task)

    def run(self):
        # start workers
        for worker in self.workers:
            worker.start()
        # let workers do the job
        while len(self.tasks)>0 and not self.__canceled:
            # using pass is better than sleep =)
            pass
			
