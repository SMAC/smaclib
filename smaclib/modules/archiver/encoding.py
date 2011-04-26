"""
A ffmpeg based encoder to be used in a asynchronous task.
"""

import os
import re

from smaclib import tasks
from smaclib import process

from twisted.internet import reactor
from twisted.python import filepath

from zope.interface import implements


class EncoderProtocol(process.DeferredProcessProtocol):
    def __init__(self, encoder):
        super(EncoderProtocol, self).__init__("Video encoding", encoder)
        self.duration = None

    def get_time(self, pattern, data, default=0):
        match = re.search(pattern, data)

        if match is None:
            return default

        groups = match.groups(0)
        exp = len(groups) - 1

        return sum(int(groups[i]) * 60 ** (exp - i) for i in range(exp + 1))

    def errLineReceived(self, data):
        # Search for the duration or time string.
        # Discard the milliseconds as we don't need such precision.
        duration_pattern = r'Duration: (\d\d):(\d\d):(\d\d).\d\d'
        time_pattern = r' time=(\d\d:(\d\d:(\d\d:)?)?)?(\d?\d).\d\d'

        if self.duration is None:
            self.duration = self.get_time(duration_pattern, data, None)
        else:
            time = self.get_time(time_pattern, data)
            self.task.completed =  1. / self.duration * time


class FFmpegEncoder(object):
    """
    A wrapper for the ffmpeg command line utility.
    """

    implements(tasks.ITaskRunner)

    def __init__(self, source, video_bitrate, audio_bitrate, sampling_rate):
        self.source = source
        self.codecs = {}
        
        self.video_bitrate = video_bitrate
        self.audio_bitrate = audio_bitrate
        self.sampling_rate = sampling_rate
        
        self.process = EncoderProtocol(self)

    def getTask(self):
        return self.process.task

    def start(self):
        bin = 'ffmpeg'

        self.target = os.path.splitext(self.source.basename())[0] + ".flv"
        self.target = self.source.parent().child(self.target)

        args = [
            '-y',
            '-i', self.source.path,
            '-vb', self.video_bitrate,
            '-ab', self.audio_bitrate,
            '-ar', self.sampling_rate,
            self.target.path,
        ]

        reactor.spawnProcess(self.process, bin, [bin] + args, env=os.environ)
        self.process.task.addErrback(self.cleanup)

    def cleanup(self, failure):
        filepath.FilePath(self.destination).remove()
        return failure
