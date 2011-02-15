"""
Base class and dependencies for all module implementations. Provides the basic
services exposed by each module, such as the ability to shutdown or restart it
or general task management tools.
"""


import hashlib
import uuid
import warnings

from smaclib import tasks
from smaclib.api import ttypes
from smaclib.api.errors import ttypes as error
from smaclib.api.module import Module as ThriftModule
from smaclib.conf import settings

from twisted.internet import reactor

from zope.interface import implements


class Module(object):
    """
    Base class for all modules.
    """

    implements(ThriftModule.Iface)

    def __init__(self):
        """
        Initializes a general purpose module.
        """
        self.task_manager = tasks.TaskManager()

    def remote_getID(self):
        return self.getID()

    def getID(self):
        """
        Returns a unique id for this module. Normally this is defined in the
        settings and has a well known value.
        
        This module ID is used for example when storing assets using multiple
        archivers on different systems. Then a given asset can only be
        retrieved by asking a well-known archiver and we need thus to store
        the archiver ID along with the asset in the database.
        
        If the ID is not defined in the settings, then a warning is issued, but
        a calculated ID is returned.
        
        The ID is calculated using an hash of the MAC address. The MAC address
        is retrieved using the uuid.getnode function; please note that this
        function does not always return the same value (refer to the python
        documentation: http://docs.python.org/library/uuid.html#uuid.getnode
        for further information).
        """
        if settings.module_id is not None:
            return settings.module_id
        
        # The ID was not defined in the settings, issue a warning and calculate
        # an (hopefully) fixed value.
        warnings.warn("Undefined module ID. Trying to guess one from the MAC" \
                      " address.", RuntimeWarning)
        
        return hashlib.sha256(str(uuid.getnode())).hexdigest()

    def remote_getAllTasks(self):
        """
        Returns a list TaskInfo instances describing all tasks currently
        registered to the task manager of this module.
        """
        return [self.remote_getTask(t) for t in self.task_manager.task_ids]

    def remote_getTask(self, task_id):
        """
        Returns the details about the task identified by task_id registered to
        the task manager of this module.

        Raises a TaskNotFound exception if the task for the given id doesn't
        exist.
        """
        task = self.task_manager.get(task_id)
        return ttypes.TaskInfo(task.id, task.name, task.status, task.completed)

    def remote_abortTask(self, task_id):
        """
        Tries to cancel the task identified by task_id. If the task does not
        support cancelling, an OperationNotSupported exception is raised.
        """
        try:
            self.task_manager.get(task_id).cancel()
        except NotImplementedError:
            raise error.OperationNotSupported(task_id, "cancelled")

    def remote_pauseTask(self, task_id):
        """
        Tries to pause the task identified by task_id. If the task does not
        support resuming, an OperationNotSupported exception is raised.

        True is returned if the task was running before the method call.
        """
        task = self.task_manager.get(task_id)
        running = not task.paused
        try:
            task.pause()
        except NotImplementedError:
            raise error.OperationNotSupported(task_id, "paused")
        else:
            return running

    def remote_resumeTask(self, task_id):
        """
        Tries to resume the task identified by task_id. If the task does not
        support resuming, an OperationNotSupported exception is raised.

        True is returned if the task was paused before the method call.
        """
        task = self.task_manager.get(task_id)
        paused = task.paused
        try:
            task.unpause()
        except NotImplementedError:
            raise error.OperationNotSupported(task_id, "unpaused")
        else:
            return paused

    def remote_ping(self):
        """
        Simple noop method to check if the communication with a remote module
        is working as expected.
        """

    def remote_restart(self):
        """
        Restarts the module by terminating the process completely and
        restarting it.

        Nota that if something here fails, probabily it will not be possible
        to access the module anymore.
        """
        # TODO: Provide an implementation

    def shutdown(self):
        """
        Terminates the server process.
        """
        # TODO: Logging
        reactor.stop()


