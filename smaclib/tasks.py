from __future__ import absolute_import

import uuid

from smaclib.api.errors import ttypes as error
from smaclib.api.ttypes import TaskStatus
from smaclib.utils import sleep

from twisted.internet import defer

from zope.interface import Interface
from zope.interface import implements


class TaskError(Exception):
    pass


class AlreadyStarted(TaskError):
    pass


class TaskManager(object):
    """
    A simple (dict-like) task manager to hold tasks and operate upon them.
    """

    remove_timeout = 5

    def __init__(self):
        self.tasks = {}

    @property
    def task_ids(self):
        return self.tasks.keys()

    def register(self, task):
        assert task.id not in self.tasks

        def _unreg(result, task):
            d = sleep(self.remove_timeout)
            d.addCallback(lambda _: self.unregister(task))
            return result

        task.addBoth(_unreg, task)

        self.tasks[task.id] = task

    def schedule(self, task):
        self.register(task)

        task()

        try:
            for t in task.tasks:
                self.register(t)
        except AttributeError:
            pass

    def unregister(self, task):
        if not isinstance(task, basestring):
            task = task.id
        del self.tasks[task]

    def get(self, taskid):
        try:
            return self.tasks[taskid]
        except KeyError:
            raise error.TaskNotFound(taskid)


class ITaskRunner(Interface):
    """
    An interface for objects providing access to long running processes with
    support for monitoring and management.
    """

    def getTask():
        """
        Returns the currently running task if this runner was already executed
        or the stub of the task which will be started once this runner is
        executed.
        """

    def start():
        """
        Executes the operation for which this runner was implemented and
        keeps the task updated. This method is normally called by
        """


class IPauseableTaskRunner(ITaskRunner):
    def pause():
        """
        Called by the task object when a pause action is requested.
        """

    def unpause():
        """
        Called by the task object when an unpause action is requested.
        """


class ICancelableTaskRunner(ITaskRunner):
    """
    Task runner with support for cancelling the running task.
    """

    def cancel():
        """
        Called by the task object when a cancel action is requested.
        """


class DeferredRunner(object):

    implements(ITaskRunner)

    def __init__(self, name, f, *args, **kwargs):
        self.task = Task(name, self)
        self.function = f
        self.args = args
        self.kwargs = kwargs

    def getTask(self):
        return self.task

    def start(self):
        d = defer.maybeDeferred(self.function, *self.args, **self.kwargs)
        d.addCallbacks(self.taskCompleted, self.taskFailed)
        return d.chainDeferred(self.task)

    def taskCompleted(self, result):
        return result

    def taskFailed(self, failure):
        return failure


class CompoundTask(defer.DeferredList, object):
    def __init__(self, name, runner, deferredList=None, taskid=None):
        self.name = name
        self.runner = runner
        self.tasks = deferredList or []
        self.id = taskid or str(uuid.uuid4())

        super(CompoundTask, self).__init__(deferredList or [], True)
        self.fireOnOneCallback = False

        if deferredList == None:
            self.pause()


    def __call__(self, *dummy, **kwdummy):
        if self.status != TaskStatus.WAITING:
            raise RuntimeError("Task already started")

        self.runner.start()

    def addTask(self, task):
        assert not self.called

        self.tasks.append(task)
        index = len(self.resultList)
        self.resultList.append(None)
        task.addCallbacks(self._cbDeferred, self._cbDeferred,
                          callbackArgs=(index,defer.SUCCESS),
                          errbackArgs=(index,defer.FAILURE))

    @property
    def status(self):
        """
        In this order:

        One or more WAITING: status is waiting
        One or more RUNNING: status is running
        One or more PAUSED:  status is paused
        One or more FAILED:  status is failed
        All COMPLETED:       status is completed
        """

        if not self.tasks:
            return TaskStatus.WAITING

        statuses = [0, 0, 0, 0, 0]

        for t in self.tasks:
            statuses[t.status] += 1

        if statuses[TaskStatus.WAITING]:
            return TaskStatus.WAITING

        if statuses[TaskStatus.RUNNING]:
            return TaskStatus.RUNNING

        if statuses[TaskStatus.PAUSED]:
            return TaskStatus.PAUSED

        if statuses[TaskStatus.FAILED]:
            return TaskStatus.FAILED

        return TaskStatus.COMPLETED

    @property
    def completed(self):
        """
        Returns None if the completed property of any of the child tasks is
        None, else the average of all the progresses.
        """

        if not self.tasks:
            return -1

        completed = 0

        for r in self.tasks:
            if r.completed >= 0:
                completed += r.completed
            else:
                return -1

        return completed / len(self.tasks)


class Task(defer.Deferred, object):

    UNDEFINED = -1

    def __init__(self, name, runner, taskid=None):
        self.id = taskid or str(uuid.uuid4())
        self.runner = ITaskRunner(runner)

        super(Task, self).__init__(self._cancel)

        self.observers = []

        # Task specific public properties
        self.name = name
        self.parent = None
        self.threshold = 1
        self._completed = Task.UNDEFINED
        self._statustext = 'Waiting to be started...'
        self._status = TaskStatus.WAITING

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, value):
        assert 0 <= value <= 1 or value is Task.UNDEFINED

        difference = int(value * 100) - int(self._completed * 100)
        notify = abs(difference) >= self.threshold
        self._completed = value

        if notify:
            self.notifyObservers()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        assert value in TaskStatus._VALUES_TO_NAMES

        if self._status == value:
            return

        self._status = value
        self.notifyObservers()

    @property
    def statustext(self):
        return self._status

    @statustext.setter
    def statustext(self, value):
        value = unicode(value)

        if self._statustext == value:
            return

        self._statustext = value
        self.notifyObservers()

    def notifyObservers(self):
        for observer, args, kwargs in self.observers:
            observer(self, *args, **kwargs)

    def addTaskObserver(self, callback, *args, **kwargs):
        self.observers.append((callback, args, kwargs))

    def setTaskParent(self, task):
        if self.parent is not None:
            raise RuntimeError("This task already has a parent.")

        self.notifyObservers()
        self.parent = task

    def __str__(self):
        task = '{0.name}: {0.statustext}'.format(self)
        
        if self.completed >= 0:
            completed = '{0:.2f}'.format(self.completed * 100)
            completed = completed.strip('0').strip('.')
            
            task = '{0} ({1}% completed)'.format(task, completed)

        return task

    def __call__(self, *dummy, **kwdummy):
        if self.status != TaskStatus.WAITING:
            raise AlreadyStarted(self)

        self.runner.start()
        self.status = TaskStatus.RUNNING

    def pause(self):
        super(Task, self).pause()
        self._update_status()

    def unpause(self):
        self.paused = self.paused - 1

        self._update_status()

        if self.paused:
            return

        if self.called:
            self._runCallbacks()

    def errback(self, fail=None):
        self.status = TaskStatus.FAILED
        super(Task, self).errback(fail)

    def callback(self, result):
        assert not isinstance(result, defer.Deferred)

        self.status = TaskStatus.COMPLETED
        self.completed = 1

        super(Task, self).callback(result)

    def cancel(self):
        self.status = TaskStatus.FAILED
        super(Task, self).cancel()

    def _update_status(self):
        if self.paused and self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.PAUSED
            IPauseableTaskRunner(self.runner).pause()
        elif not self.paused and self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
            IPauseableTaskRunner(self.runner).unpause()

    def _cancel(self):
        ICancelableTaskRunner(self.runner).cancel()

