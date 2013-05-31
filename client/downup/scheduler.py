"""
Vodstok asynchronous task scheduler

Okay, maybe Twisted may help a bit but i'm not a twisted lover.
"""

import sys
from time import sleep
from threading import Thread, Lock
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
        """
        Cancel this worker
        """
        self.__canceled = True

    def run(self):
        """
        Worker's main loop.

        This is where the worker grab task to perform, performs them and notify
        their results.
        """
        while not self.__canceled:
            sys.stdout.flush()
            task = self.sched.get_pending_task()
            if task is not None:
                if task.process(self.sched.acquire_repository()):
                    self.sched.release_repository()
                    self.sched.on_worker_done(task)
                else:
                    self.sched.on_worker_error(task)
            pass


class Scheduler(Thread):

    """
    Custom task scheduler.

    This scheduler is built upon threads, handling a pool of tasks. Each task
    is performed separately, and the whole process is supervised.
    The scheduler provides a way to easily enqueue and manage tasks.
    """

    def __init__(self, rep_manager):
        Thread.__init__(self)
        self.__rep_manager = rep_manager
        self.workers = [Worker(self, None) for i in range(Settings.max_threads)]
        self.tasks = []
        self.__canceled = False
        self.__lock = Lock()

    def cancel(self):
        """
        Cancel every workers.
        """
        for worker in self.workers:
            worker.cancel()
        self.__canceled = True

    def get_random_repository(self):
        """
        Return a random repository (not used yet)
        """
        return

    def acquire_repository(self):
        """
        Acquire a random repository (vodstok server)
        """
        return self.__rep_manager.pick_random()

    def release_repository(self):
        """
        No locking yet. Should be implemented soon.
        """
        return

    def queue_task(self, task):
        """
        Enqueue a given task.
        """
        self.tasks.append(task)

    def remove_task(self, task):
        """
        Remove a given task from task queue
        """
        if task in self.tasks:
            self.tasks.remove(task)

    def get_pending_task(self):
        """
        Return the top pending task, then send it at the end
        """
        self.__lock.acquire()
        if len(self.tasks)>0:
            file_task = self.tasks[0]
            if file_task is None:
                self.__lock.release()
                return None
            else:
                if not file_task.is_completed():
                    # get a chunk task from the file task
                    chunk_task = file_task.get_next_task()
                    if chunk_task is not None:
                        # put the file task at the end of the list
                        self.tasks.append(self.tasks.pop(0))
                        self.__lock.release()
                        return chunk_task
                    else:
                        self.__lock.release()
                else:
                    self.tasks.remove(file_task)
                    self.__lock.release()
                    return None
        else:
            self.__lock.release()
            return None

    def on_worker_done(self, chunk_task):
        """
        Called when a worker processed a task. Task is then notified.
        """
        file_task = chunk_task.get_parent_filetask()
        file_task.on_task_done(chunk_task)

    def on_worker_error(self, chunk_task):
        """
        Called when a worker encountered an error while processing a task
        Task is notified of this failure.
        """
        file_task = chunk_task.get_parent_filetask()
        file_task.on_task_error(chunk_task)

    def run(self):
        """
        Scheduler main loop

        Workers are started, and the scheduler runs until all workers are
        stopped (or canceled)
        """
        # start workers
        for worker in self.workers:
            worker.start()
        # let workers do the job
        while len(self.tasks)>0 and not self.__canceled:
            # using pass is better than sleep =)
            sleep(0.1)

