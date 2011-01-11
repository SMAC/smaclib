from __future__ import absolute_import

import uuid

from smaclib.api.errors import ttypes as error
from smaclib.api.ttypes import TaskStatus

from twisted.internet import defer


class TaskManager(object):
    """
    A simple (dict-like) task manager to hold tasks and operate upon them.
    """

    def __init__(self):
        self.tasks = {}
        
    @property
    def task_ids(self):
        return self.tasks.keys()

    def register(self, task):
        assert task.id not in self.tasks
        
        def _unreg(result, task):
            # TODO: Shall we wait a little before removing it?
            self.unregister(task)
            return result
        
        task.addBoth(_unreg, task)
        
        self.tasks[task.id] = task

    def unregister(self, task):
        if not isinstance(task, basestring):
            task = task.id
        del self.tasks[task]

    def get(self, taskid):
        try:
            return self.tasks[taskid]
        except KeyError:
            raise error.TaskNotFound(taskid)


class Task(defer.Deferred, object):

    def __init__(self, name, canceller=None, taskid=None):
        self.name = name
        self.id = taskid or str(uuid.uuid4())

        if canceller is None:
            canceller = self._cancel

        super(Task, self).__init__(canceller)

        self.completed = 0
        self.status = TaskStatus.RUNNING

    def __str__(self):
        return self.name

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
            self._pause()
        elif not self.paused and self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
            self._unpause()

    def _cancel(self):
        raise NotImplementedError("This task does not support cancelling.")

    def _pause(self):
        raise NotImplementedError("This task does not support pausing.")

    def _unpause(self):
        raise NotImplementedError("This task does not support pausing.")

