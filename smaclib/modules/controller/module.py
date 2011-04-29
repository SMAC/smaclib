"""
Archiver module interface implementation with FTP based file serving.
"""

import os
import tempfile
import tarfile

from smaclib.modules.base import Module
from smaclib.modules import tasks as common_tasks
from smaclib import tasks
from smaclib import xml
from smaclib.conf import settings

from twisted.internet import threads
from twisted.python import filepath
from twisted.python import log


class Controller(Module):

    def remote_setupSession(self):
        raise NotImplementedError

    def remote_startRecording(self):
        raise NotImplementedError

    def remote_stopRecording(self):
        raise NotImplementedError

    def remote_archive(self):
        raise NotImplementedError

    def remote_analyze(self):
        raise NotImplementedError

    def remote_publish(self):
        raise NotImplementedError

