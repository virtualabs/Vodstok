import sys
from time import time
from core.helpers import formatSpeed
from core.exception import IncorrectParameterError, IncorrectFormatError
from downup.server import Server
from storage.user import User
from downup.scheduler import Scheduler
from downup.tasks import UpTask, DownTask, TaskStatus, TaskRef

class ServersManager:

    """
    This class manages the user's servers database.

    It only adds servers checking at the moment, but in further versions
    it will be used as a manager handling regular servers list updates
    and background checks.
    """
    
    gInst = None
    
    @staticmethod
    def getInstance():
        """
        Static method returning a single instance
        """
        if ServersManager.gInst is None:
            ServersManager.gInst = ServersManager()
        return ServersManager.gInst

    def __init__(self):
        self.__db = User.getInstance().getServersDB()

    def checkServers(self):
        print '[i] Checking servers ...'
        for server in self.__db.enum():
            sys.stdout.write('+ checking %s ... '%server.url)
            sys.stdout.flush()
            if not server.check():
                sys.stdout.write('KO\n')
            else:
                sys.stdout.write('OK\n')
            sys.stdout.flush()

    def remove(self, url):
        return self.__db.remove(url)

    def add(self, url):
        if Server(url).check():
            return self.__db.add(url)
        return False

    def pickRandom(self):
        return self.__db.pickRandom()


class DownUpManager:

    """
    Download/Upload manager.

    This manager handles upload and download tasks and allows task management
    (start,suspend,stop,cancel).

    Notifications are sent by this manager to every registered listeners, making
    them able to react on events and interact with active tasks (upload or down-
    load tasks).

    Tasks are referenced by UUIDs, instead of using objects. That is, it is very
    easy to manage tasks without having complex objects.

    This class is an interface for every background running tasks.
    """

    gDownUpManager = None

    @staticmethod
    def getInstance():
        if DownUpManager.gDownUpManager is None:
            DownUpManager.gDownUpManager = DownUpManager()
        return DownUpManager.gDownUpManager

    def __init__(self):
        self.__scheduler = Scheduler(ServersManager.getInstance())
        self.__tasks = {}
        self.__running = False
        self.__listeners = []
        self.__ensureRun()

    def __ensureRun(self):
        """
        Make sure the scheduler is running
        """
        if self.__running == False:
            self.__scheduler.start()
            self.__running = True

	## Listeners

    def registerListener(self, listener):
        """
        Register a listener
        """
        if listener not in self.__listeners:
            self.__listeners.append(listener)

    def removeListener(self, listener):
        """
        Unregister a listener
        """
        if listener in self.__listeners:
            self.__listeners.remove(listener)

	## Events

    def notifyTaskCreated(self, task):
        """
        Notify listeners about a new task
        """
        for listener in self.__listeners:
            listener.onTaskCreated(task)

    def notifyTaskStarted(self, task):
        """
        Notify listeners about a started task
        """
        for listener in self.__listeners:
            listener.onTaskStarted(task)

    def notifyTaskDone(self, task):
        """
        Notify listeners about a completed task
        """
        for listener in self.__listeners:
            listener.onTaskDone(task)

    def notifyTaskProgress(self, task, progress):
        """
        Notify listeners about an active task
        """
        for listener in self.__listeners:
            listener.onTaskProgress(task, progress)

    def notifyTaskCancel(self, task):
        """
        Notify listeners about a canceled task
        """
        for listener in self.__listeners:
            listener.onTaskCancel(task)

    def notifyTaskSuspended(self, task):
        """
        Notify listeners about a suspended task
        """
        for listener in self.__listeners:
            listener.onTaskSuspended(task)

    def notifyTaskResumed(self, task):
        """
        Notify listeners about a resumed task
        """
        for listener in self.__listeners:
            listener.onTaskResumed(task)

    def notifyTaskError(self, task):
        """
        Notify listeners about an error that occured during task processing
        """
        for listener in self.__listeners:
            listener.onTaskError(task)

    ## Task management

    def queueTask(self, task):
        """
        Queue a given task (forward the task directly to the scheduler)
        """
        self.__scheduler.queueTask(task)

    def __registerTask(self, task):
        """
        Register a new task
        """
        if task.uuid not in self.__tasks:
            self.__tasks[task.uuid] = TaskRef(task)
            self.notifyTaskCreated(task.uuid)

    def upload(self, filename):
        """
        Upload a file
        """
        task = UpTask(self, filename)
        self.__registerTask(task)
        return task.uuid

    def download(self, url, prefix=''):
        """
        Download a file.

        The prefix parameter can be used to specify a destination directory
        """
        task = DownTask(self, url, prefix)
        self.__registerTask(task)
        return task.uuid
            
    def startTask(self, task):
        """
        Start a given task

        Task must be registered before start
        """
        if task in self.__tasks:
            self.__tasks[task].object.process()
            self.notifyTaskStarted(task)

    def removeTask(self, task):
        """
        Remove task.

        Cancel task and unregister it.
        """
        if task in self.__tasks:
            self.__tasks[task].cancel()
            del self.__tasks[task]

    def suspendTask(self, task):
        """
        Suspend task.

        Task must have been registered before.
        """
        if task in self.__tasks:
            self.__tasks[task].suspend()

    def resumeTask(self, task):
        """
        Resume task.

        Task must have been registered before.
        """
        if task in self.__tasks:
            self.__tasks[task].resume()

    def getTaskStatus(self, task):
        """
        Retrieve task status.

        Return a AbstractTask status code.
        """
        if task in self.__tasks:
            return self.__tasks[task].status

    def getTask(self, task):
        """
        Return an internal task object
        """
        if task in self.__tasks:
            return self.__tasks[task]
        else:
            return None

    def cancel(self, task):
        """
        Cancel task.
        """
        if task in self.__tasks:
            self.__tasks[task].cancel()
        self.notifyTaskCancel(task)

    def shutdown(self):
        """
        Shutdown upload/download manager.

        Cause the scheduler to shutdown.
        """
        self.__scheduler.cancel()
        self.__scheduler.join()


    ## Events

    def onTaskDone(self, task):
        if task.uuid in self.__tasks:
            self.__tasks[task.uuid].status = TaskStatus.TASK_DONE
            self.notifyTaskDone(task.uuid)

    def onTaskError(self, task):
        if task.uuid in self.__tasks:
            self.__tasks[task.uuid].status = TaskStatus.TASK_ERR
            self.notifyTaskError(task.uuid)

    def onTaskProgress(self, task, done, total):
        if task.uuid in self.__tasks:
            self.__tasks[task.uuid].update(done, total)
            self.notifyTaskProgress(task.uuid, float(done)/total)


class CmdLineManager:

    """
    Command line dummy manager.

    This manager can handle a single upload/download.
    It displays progress information such as global progress and bitrate.
    """

    def __init__(self):
        self._manager = DownUpManager()
        self._manager.registerListener(self)
        self.task = None
        self.kind = ''
        self.start = time()

    def upload(self, filename):
        """
        Upload a file
        """
        try:
            self.kind = 'up'
            self.task = self._manager.upload(filename)
            self._manager.startTask(self.task)
        except IncorrectParameterError:
            print '[!] Error: bad file name'
            self._manager.shutdown()


    def download(self, filename, prefix=''):
        """
        Download a file
        
        @throws IncorrectParameterError
        """
        try:
            self.kind = 'down'
            self.task = self._manager.download(filename, prefix)
            self._manager.startTask(self.task)
        except IncorrectFormatError:
            print '[!] Error: bad URL format'
            self._manager.shutdown()
            
    def onTaskDone(self, task):
        """
        Task completed callback
        """
        if task == self.task:
            if self.kind == 'up':
                action = 'Uploading '
            else:
                action = 'Downloading '
            sys.stdout.write('\r%s: [' % action +'='*40 + '] %s     ' % \
                formatSpeed(self._manager.getTask(task).speed))
            sys.stdout.write('\n')
            if self.kind == 'up':
                print 'Url: %s' % self._manager.getTask(task).getUrl()
            else:
                print 'File downloaded to %s' % self._manager.getTask(task).filename
            self._manager.shutdown()

    def onTaskProgress(self, task, progress):
        """
        Task progress callback
        """
        if task == self.task:
            if self.kind == 'up':
                action = 'Uploading '
            else:
                action = 'Downloading '
            width = int(progress*40)
            sys.stdout.write('\r%s: [' % action +'='*width + ' '*(40-width)+'] %s     ' % \
                formatSpeed(self._manager.getTask(task).speed))
            sys.stdout.flush()

    def onTaskCancel(self, task):
        """
        Task canceled callback (implemented but never called since we do not allow task cancelation)
        """
        return

    def onTaskError(self, task):
        """
        Task error callback.

        Stop everything if an error occured.
        """
        if task == self.task:
            sys.stdout.write('\n')
            print '[!] Unable to upload'
            self._manager.shutdown()
            
    def onTaskCreated(self, task):
        if self.kind == 'up':
            action = 'Uploading '
        else:
            action = 'Downloading '
        sys.stdout.write('\r%s: [' % action +' '*40 + '] %s     ' % \
            formatSpeed(self._manager.getTask(task).speed))
        return
        
    def onTaskStarted(self, task):
        return
