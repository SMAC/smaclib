"""
A rasterizer object is capable to rasterize a PDF document to an image format
of choice.
"""


import re
import os

from smaclib import tasks
from smaclib import process

from twisted.internet import reactor
from twisted.internet import error
from twisted.python import log

from zope.interface import implements


class RasterizationProtocol(process.DeferredProcessProtocol):

    def __init__(self, task_name, delegate):
        super(RasterizationProtocol, self).__init__(task_name, delegate)

        self.pages = None
        self.page = 0

    def update_task(self):
        self.task.completed =  1. / self.pages * self.page

        self.task.name = "Processing page {1}/{0.pages}".format(self, self.page + 1)

        if self.page == self.pages:
            log.msg("Document rasterization finished")
            self.task.callback(self.delegate)
        else:
            log.msg(self.task.name)

    def outLineReceived(self, line):
        self.completed = 0

        if self.pages is None:
            match = re.search(r'Processing pages \d+ through (?P<pages>\d+)\.', line)

            if match:
                self.pages = int(match.group('pages'))
                self.update_task()
        else:
            match = re.search(r'Page (?P<page>\d+)', line)

            if match:
                self.resize_page(int(match.group('page')) - 1)

    def resize_page(self, page):
        if page <= 0:
            return

        filename = self.delegate.target % page
        self.delegate.resize(filename).addCallback(self.page_done)

    def processEnded(self, status):
        if self.cancelled:
            status.trap(error.ProcessTerminated)
        else:
            status.trap(error.ProcessDone)
            self.resize_page(self.pages)

    def page_done(self, _):
        self.page += 1
        self.update_task()


class ImageGenerator(object):

    implements(tasks.ITaskRunner)

    supersampling_factor = 4

    def __init__(self, source):
        self.source = source

        task_name = "Generating images for {0}".format(source)
        self.process = RasterizationProtocol(task_name, self)

    def resize(self, filename, size=(1024, 1024)):

        bin = 'mogrify'

        args = [
            '-scale', '{0:d}x{0:d}'.format(*size),
            filename,
            '-density', str(72/2.54),
            filename,
        ]

        proto = process.DeferredProcessProtocol()
        reactor.spawnProcess(proto, bin, [bin] + args, env=os.environ)
        return proto.task

    def getTask(self):
        return self.process.task

    def start(self):
        self.target_dir = os.path.splitext(self.source.basename())[0]
        self.target_dir = self.source.parent().child(self.target_dir)

        if not self.target_dir.exists():
            self.target_dir.makedirs()

        self.target = "{0}%03d.png".format(self.target_dir.child('slide-').path)

        bin = 'gs'

        args = [
            '-sDEVICE=pngalpha',
            '-r' + str(72 * self.supersampling_factor),
            '-o', self.target,
            self.source.path
        ]

        reactor.spawnProcess(self.process, bin, [bin] + args, env=os.environ)


