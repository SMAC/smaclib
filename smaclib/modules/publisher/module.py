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

from zope.interface import implements


class PublishingDelegate(object):

    implements(tasks.ITaskRunner)

    def __init__(self, talk_id, bundle_url):
        self.bundle_url = bundle_url
        self.talk_id = talk_id

        self.runners = {
            'download': common_tasks.FileDownloadTask(bundle_url),
            'extract': tasks.DeferredRunner("Talk bundle extraction", self._extract),
            'publish': tasks.DeferredRunner("File structure creation", self._publish),
        }

        alltasks = [r.getTask() for r in self.runners.values()]
        self.task = tasks.CompoundTask('Talk publishing', self, alltasks)

    def getTask(self):
        return self.task

    def start(self):
        d = self.download()
        d.addCallback(self.extract)
        d.addCallback(self.publish)

    def download(self):
        basename = os.path.basename(self.bundle_url)
        fd, name = tempfile.mkstemp(suffix='-' + basename)
        destination = os.fdopen(fd, 'w')

        def close(dest):
            dest.close()
            return name

        runner = self.runners['download']
        runner.destination = destination
        return runner.getTask().addCallback(close)()

    def extract(self, tarbundle):
        self.tarbundle = filepath.FilePath(tarbundle)
        return self.runners['extract'].getTask()()

    def _extract(self):
        return threads.deferToThread(self.extractBundle, self.tarbundle)
    
    def publish(self, dest):
        self.dest = dest
        return self.runners['publish'].getTask()()

    def _publish(self):
        return threads.deferToThread(self.publishTalk, self.talk_id, self.dest)

    @staticmethod
    def publishTalk(talk_id, extracted):
        data_root = settings.data_root.child('data').child(talk_id)
        
        if data_root.exists():
            data_root.remove()
        
        def format(context, formatting, arg):
            return formatting % int(arg[0])
        
        data_root.makedirs()
        
        extracted.child('video').moveTo(data_root.child('video'))
        extracted.child('slideshow').moveTo(data_root.child('slideshow'))
        
        
        #extracted.globChildren('*-alignment.xml')[0].moveTo(data_root)
        
        # Create XML file
        trans = xml.Transformation(filepath.FilePath(__file__).parent().child('publisher.xsl').path)
        
        slide_fmt = data_root.globChildren('slideshow/*/*.png')[0].path
        slide_fmt = slide_fmt[len(data_root.path)+1:]
        slide_fmt = slide_fmt.replace('-001.png', '-%03d.png')
        
        video_file = data_root.globChildren('video/*.flv')[0].path
        video_file = video_file[len(data_root.path)+1:]
        
        trans.parameters['video'] = "'{0}'".format(video_file)
        trans.parameters['slides'] = "'{0}'".format(slide_fmt)
        
        trans.register_function('http://smac.hefr.ch/publisher',
                                format, 'format-string')
        
        trans.transform(extracted.globChildren('*-alignment.xml')[0].path,
                        data_root.child('conference.xml').path)
        

    @staticmethod
    def extractBundle(temptar):
        tempdir = tempfile.mkdtemp(prefix='smac-', suffix='-bundle')
        tempdir = filepath.FilePath(tempdir)

        bundle = tarfile.open(name=temptar.path, mode='r:*')

        # Check paths (preauthChild raises InsecurePath if f is not a child of
        # tempdir)
        [tempdir.preauthChild(f) for f in bundle.getnames()]

        # Extract all
        bundle.extractall(path=tempdir.path)
        bundle.close()
        del bundle

        # Delete temp directory
        temptar.remove()

        return tempdir


class Publisher(Module):
    
    def remote_publishTalk(self, talk_id, bundle_url):
        # Get file
        delegate = PublishingDelegate(talk_id, bundle_url)
        task = delegate.getTask()
        task.addTaskObserver(log.msg)
        self.task_manager.schedule(task)
        
        # Untar
        
        # Move files
        return task.id