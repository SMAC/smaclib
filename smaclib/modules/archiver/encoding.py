"""
A ffmpeg based encoder to be used in a asynchronous task.
"""

import os
import re

from smaclib import tasks
from smaclib.twisted.internet import utils

from twisted.internet import defer
from twisted.internet import error
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import filepath


class EncoderProtocol(protocol.ProcessProtocol):
    def __init__(self, encoder):
        self.encoder = encoder
        self.task = tasks.Task("Video encoding", self.abort)
        self.duration = None
        self.cancelled = False

    def abort(self, task):
        self.cancelled = True
        self.transport.signalProcess('KILL')

    def get_time(self, pattern, data, default=0):
        match = re.search(pattern, data)

        if match is None:
            return default

        groups = match.groups(0)
        exp = len(groups) - 1

        return sum(int(groups[i]) * 60 ** (exp - i) for i in range(exp + 1))

    def errReceived(self, data):
        # Search for the duration or time string.
        # Discard the milliseconds as we don't need such precision.
        duration_pattern = r'Duration: (\d\d):(\d\d):(\d\d).\d\d'
        time_pattern = r' time=(\d\d:(\d\d:(\d\d:)?)?)?(\d?\d).\d\d'
        
        if self.duration is None:
            self.duration = self.get_time(duration_pattern, data, None)
        else:
            time = self.get_time(time_pattern, data)

            self.task.completed =  1. / self.duration * time * 100

    def processEnded(self, status):
        if self.cancelled:
            status.trap(error.ProcessTerminated)
        else:
            status.trap(error.ProcessDone)
            self.task.callback(self.encoder)


class FFmpegEncoder(object):
    """
    A wrapper for the ffmpeg command line utility.
    """

    def __init__(self, bin='/usr/local/bin/ffmpeg'):
        self.bin = bin
        self.codecs = {}
        self.destination = ''
        self.arguments = []

    def write_to(self, destination):
        self.destination = destination
        return self

    def read_from(self, source):
        return self.option('i', source)

    def flag(self, name):
        self.arguments += ['-' + name]
        return self

    def option(self, name, value):
        self.arguments += ['-' + name, value]
        return self

    def encode(self):
        process = EncoderProtocol(self)
        reactor.spawnProcess(process, self.bin, self._command, env=os.environ)
        process.task.addErrback(self._cleanup)
        return process.task

    def _cleanup(self, failure):
        filepath.FilePath(self.destination).remove()
        return failure

    @property
    def _command(self):
        return [self.bin] + self.arguments + [self.destination]

    def can_encode(self, extension):
        # TODO: Find the right way to convert between guessed file extension
        #       and ffmpeg format, as this one is not the right one... ;-)
        # NEWS: Uses now the formats argument instead of the codecs ons...
        #       maybe this is the right one.
        try:
            return 'E' in self.codecs[extension.lstrip('.')][0]
        except KeyError:
            return False

    def can_decode(self, extension):
        # TODO: Find the right way to convert between guessed file extension
        #       and ffmpeg format, as this one is not the right one... ;-)
        # NEWS: Uses now the formats argument instead of the codecs ons...
        #       maybe this is the right one.
        try:
            return 'D' in self.codecs[extension.lstrip('.')][0]
        except KeyError:
            return False

    def validate_bitrate(self, value):
        """
        Simplistic bitrate validation. Only checks that the given value is
        composed by digits and ends with a 'k'.
        """
        # TODO: Enfore a more strict check (min/max bitrates, allowed values
        #       only,...)
        return re.match(r'\d+k$', value) is not None

    @defer.inlineCallbacks
    def init(self):
        self.codecs = yield self._get_codecs()

    @defer.inlineCallbacks
    def _get_codecs(self):
        out = yield utils.get_process_output(self.bin, ['-formats'], errortoo=False)

        try:
            out = out.split(' --\n', 1)[1].strip()
        except IndexError:
            # Something went wrong while capturing the output
            defer.returnValue({})

        codecs = {}

        for codec in out.splitlines():
            if not codec:
                continue

            flags = codec[:4]
            flags = list(flags.replace(' ', ''))

            try:
                extension, name = codec[4:].strip().split(' ', 1)
                name = name.strip()
            except IndexError:
                # Something went wrong while capturing the output
                continue

            for ext in extension.split(','):
                codecs[ext] = flags, name

        defer.returnValue(codecs)
