import sys
from time import time
from core.helpers import format_speed
from core.exception import IncorrectParameterError, IncorrectFormatError, \
    ServerIOError
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
    def get_instance():
        """
        Static method returning a single instance
        """
        if ServersManager.gInst is None:
            ServersManager.gInst = ServersManager()
        return ServersManager.gInst

    def __init__(self):
        self.__db = User.get_instance().get_servers_db()

    def check_servers(self):
        """
        Check servers based on user's servers list.

        The check is performed by sending a chunk to the target server
        and then retrieving it. If everything is OK, then the server is
        considered as OK.
        """
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
        """
        Store a given server URL in user's servers list
        """
        return self.__db.remove(url)

    def add(self, server):
        """
        Add a given server in user's servers list.
        """
        return self.__db.add(server)

    def has(self, server):
        """
        Check if server is already known
        """
        return self.__db.has(server)

    def pick_random(self):
        """
        Pick a random server from user's servers list
        """
        return self.__db.pick_random()


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
    def get_instance():
        if DownUpManager.gDownUpManager is None:
            DownUpManager.gDownUpManager = DownUpManager()
        return DownUpManager.gDownUpManager

    def __init__(self):
        self.__manager = ServersManager.get_instance()
        self.__scheduler = Scheduler(self.__manager)
        self.__tasks = {}
        self.__running = False
        self.__listeners = []
        self.__ensure_run()

    def __ensure_run(self):
        """
        Make sure the scheduler is running
        """
        if self.__running == False:
            self.__scheduler.start()
            self.__running = True

	## Listeners

    def register_listener(self, listener):
        """
        Register a listener
        """
        if listener not in self.__listeners:
            self.__listeners.append(listener)

    def remove_listener(self, listener):
        """
        Unregister a listener
        """
        if listener in self.__listeners:
            self.__listeners.remove(listener)

	## Events

    def notify_task_created(self, task):
        """
        Notify listeners about a new task
        """
        for listener in self.__listeners:
            listener.on_task_created(task)

    def notify_task_started(self, task):
        """
        Notify listeners about a started task
        """
        for listener in self.__listeners:
            listener.on_task_started(task)

    def notify_task_done(self, task):
        """
        Notify listeners about a completed task
        """
        for listener in self.__listeners:
            listener.on_task_done(task)

    def notify_task_progress(self, task, progress):
        """
        Notify listeners about an active task
        """
        for listener in self.__listeners:
            listener.on_task_progress(task, progress)

    def notify_task_cancel(self, task):
        """
        Notify listeners about a canceled task
        """
        for listener in self.__listeners:
            listener.on_task_cancel(task)

    def notify_task_suspended(self, task):
        """
        Notify listeners about a suspended task
        """
        for listener in self.__listeners:
            listener.on_task_suspended(task)

    def notify_task_resumed(self, task):
        """
        Notify listeners about a resumed task
        """
        for listener in self.__listeners:
            listener.on_task_resumed(task)

    def notify_task_error(self, task):
        """
        Notify listeners about an error that occured during task processing
        """
        for listener in self.__listeners:
            listener.on_task_error(task)


    ## Task management

    def queue_task(self, task):
        """
        Queue a given task (forward the task directly to the scheduler)
        """
        self.__scheduler.queue_task(task)

    def __register_task(self, task):
        """
        Register a new task
        """
        if task.uuid not in self.__tasks:
            self.__tasks[task.uuid] = TaskRef(task)
            self.notify_task_created(task.uuid)

    def upload(self, filename):
        """
        Upload a file
        """
        task = UpTask(self, filename)
        self.__register_task(task)
        return task.uuid

    def download(self, url, prefix=''):
        """
        Download a file.

        The prefix parameter can be used to specify a destination directory
        """
        task = DownTask(self, url, prefix)
        self.__register_task(task)
        return task.uuid

    def start_task(self, task):
        """
        Start a given task

        Task must be registered before start
        """
        if task in self.__tasks:
            self.__tasks[task].object.process()
            self.notify_task_started(task)

    def remove_task(self, task):
        """
        Remove task.

        Cancel task and unregister it.
        """
        if task in self.__tasks:
            self.__tasks[task].cancel()
            del self.__tasks[task]

    def suspend_task(self, task):
        """
        Suspend task.

        Task must have been registered before.
        """
        if task in self.__tasks:
            self.__tasks[task].suspend()

    def resume_task(self, task):
        """
        Resume task.

        Task must have been registered before.
        """
        if task in self.__tasks:
            self.__tasks[task].resume()

    def get_task_status(self, task):
        """
        Retrieve task status.

        Return a AbstractTask status code.
        """
        if task in self.__tasks:
            return self.__tasks[task].status

    def get_task(self, task):
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
        self.notify_task_cancel(task)

    def shutdown(self):
        """
        Shutdown upload/download manager.

        Cause the scheduler to shutdown.
        """
        self.__scheduler.cancel()
        self.__scheduler.join()


    ## Events

    def on_task_done(self, task):
        """
        Task done event handler
        """
        if task.uuid in self.__tasks:
            self.__tasks[task.uuid].status = TaskStatus.TASK_DONE
            self.notify_task_done(task.uuid)

    def on_task_error(self, task):
        """
        Task error event handler
        """
        if task.uuid in self.__tasks:
            self.__tasks[task.uuid].status = TaskStatus.TASK_ERR
            self.notify_task_error(task.uuid)

    def on_task_progress(self, task, done, total):
        """
        Task progress event handler
        """
        if task.uuid in self.__tasks:
            self.__tasks[task.uuid].update(done, total)
            self.notify_task_progress(task.uuid, float(done)/total)

    def on_server_discovered(self, server):
        """
        New server discovered event handler
        """
        if not self.__manager.has(server):
            # check server and register it
            # this would normally not cause an error
            # but who knows =)
            try:
                server.get_version()
                server.get_capacity()
                self.__manager.add(server)
            except ServerIOError:
                pass



class CmdLineManager:

    """
    Command line dummy manager.

    This manager can handle a single upload/download.
    It displays progress information such as global progress and bitrate.
    """

    def __init__(self):
        self._manager = DownUpManager()
        self._manager.register_listener(self)
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
            self._manager.start_task(self.task)
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
            self._manager.start_task(self.task)
        except IncorrectFormatError:
            print '[!] Error: bad URL format'
            self._manager.shutdown()
        except VersionError:
            sys.stdout.write('\n')
            print '[!] This link was created with a more recent version of '+ \
                'vodstok, please update your client\n' + \
                '[!] Check https://github.com/virtualabs/vodstok/'
            self._manager.shutdown()

    def on_task_done(self, task):
        """
        Task completed callback
        """
        if task == self.task:
            if self.kind == 'up':
                action = 'Uploading '
            else:
                action = 'Downloading '
            sys.stdout.write('\r%s: [' % action +'='*40 + '] %s     ' % \
                format_speed(self._manager.get_task(task).speed))
            sys.stdout.write('\n')
            if self.kind == 'up':
                print 'Url: %s' % self._manager.get_task(task).get_url()
            else:
                print 'File downloaded to %s' % \
                self._manager.get_task(task).filename
            self._manager.shutdown()

    def on_task_progress(self, task, progress):
        """
        Task progress callback
        """
        if task == self.task:
            if self.kind == 'up':
                action = 'Uploading '
            else:
                action = 'Downloading '
            width = int(progress*40)
            sys.stdout.write('\r%s: [' % action +'='*width)
            sys.stdout.write(' '*(40-width))
            sys.stdout.write('] %s     ' % \
                format_speed(self._manager.get_task(task).speed))
            sys.stdout.flush()

    def on_task_cancel(self, task):
        """
        Task canceled callback (implemented but never called since we do not allow task cancelation)
        """
        return

    def on_task_error(self, task):
        """
        Task error callback.

        Stop everything if an error occured.
        """
        if task == self.task:
            sys.stdout.write('\n')
            print '[!] An I/O Error occured'
            self._manager.shutdown()

    def on_task_created(self, task):
        if self.kind == 'up':
            action = 'Uploading '
        else:
            action = 'Downloading '
        sys.stdout.write('\r%s: [' % action +' '*40 + '] %s     ' % \
            format_speed(self._manager.get_task(task).speed))
        return

    def on_task_started(self, task):
        return

