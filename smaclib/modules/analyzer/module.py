"""
SMAC analysis module
====================

This simple implementation of the analysis interface offers three main
capabilities:

 1. **Video segmentation:** Given the ID of the asset as stored on the archvier,
    this method retrieves it and detects the slide changes. The resulting XML
    file is stored on the archiver as soon as the operation completes.

 2. **Slides alignement:** Given the ID of the XML file containing the
    segmentation information and the ID of the slideshow to align to the
    segmented video, assigns a slide to each segment in the video.
    The resulting XML file is stored on the archiver as soon as the operation
    completes.

 3. **Metadata extraction:** Given a document ID, extracts all possible
    metadata (if an extractor for the specific document type exists) and stores
    the result on the archiver as an XML file.

"""

import os
import tempfile
import tarfile
import blist
import cStringIO as StringIO

from lxml import etree

from smaclib.modules.base import Module
from smaclib.modules.analyzer import tasks as analyzer_tasks
from smaclib.modules import tasks as common_tasks
from smaclib.modules.analyzer import segmentation
from smaclib.modules.analyzer import alignment
from smaclib import tasks

from twisted.internet import defer
from twisted.internet import threads
from twisted.python import log
from twisted.python import filepath

from zope.interface import implements


class SlideAnalysisDelegate(object):

    implements(tasks.ITaskRunner)

    def __init__(self, slides_url, upload_url):
        self.slides_url = slides_url

        self.runners = {
            'download': common_tasks.FileDownloadTask(slides_url),
            'extract': tasks.DeferredRunner("Slideshow bundle extraction", self._extract),
            'analyze': analyzer_tasks.SlideAnalysisTask(),
            'encode': tasks.DeferredRunner("Analysis results encoding", self._serialize),
            'upload': analyzer_tasks.FileUploadTask(destination=upload_url)
        }

        alltasks = [r.getTask() for r in self.runners.values()]
        self.task = tasks.CompoundTask('Slide analysis', self, alltasks)

    def getTask(self):
        return self.task

    def start(self):
        d = self.download()
        d.addCallback(self.extract)
        d.addCallback(self.analyze)
        d.addCallback(self.serialize)
        d.addCallback(self.upload)
        d.addCallback(self.cleanup)

    def download(self):
        basename = os.path.basename(self.slides_url)
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

    def analyze(self, tempdir):
        self.tempdir = tempdir
        slides = []

        for slide in tempdir.globChildren('*/*.png'):
            slide_id = int(slide.basename().split('-', 1)[1].split('.', 1)[0])
            slides.append(segmentation.Slide(slide_id, slide.path))

        slides.sort()

        runner = self.runners['analyze']
        runner.slides = slides
        return runner.getTask()()

    def serialize(self, slides):
        self.slides = slides
        return self.runners['encode'].getTask()()

    def cleanup(self, result):
        self.tempdir.remove()
        return result

    def _serialize(self):
        root = etree.Element("slides")

        root.set("count", str(len(self.slides)))

        for slide in self.slides:
            root.append(slide.toxml())

        return root

    def upload(self, document):
        result = etree.tostring(document, pretty_print=True)

        runner = self.runners['upload']
        runner.source = StringIO.StringIO(result)
        runner.size = len(result)
        runner.name = "analysis results"
        return runner.getTask()()

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


class VideoAnalysisDelegate(object):

    implements(tasks.ITaskRunner)

    def __init__(self, video_url, upload_url):
        self.video_url = video_url

        self.runners = {
            'download': analyzer_tasks.FileDownloadTask(video_url),
            'segment': analyzer_tasks.VideoSegmentationTask(),
            'crop': analyzer_tasks.VideoCroppingTask(),
            'analyze': analyzer_tasks.FrameAnalysisTask(),
            'encode': tasks.DeferredRunner("Analysis results encoding", self._serialize),
            'upload': analyzer_tasks.FileUploadTask(destination=upload_url)
        }

        alltasks = [r.getTask() for r in self.runners.values()]
        self.task = tasks.CompoundTask('Video analysis', self, alltasks)

    def getTask(self):
        return self.task

    def start(self):
        d = self.download()
        d.addCallback(self.segment)
        d.addCallback(self.save_details)
        d.addCallback(self.crop)
        d.addCallback(self.analyze)
        d.addCallback(self.serialize)
        d.addCallback(self.upload)

    def save_details(self, res):
        sequences, self.duration, self.framerate, self.framescount = res
        return sequences

    def download(self):
        basename = os.path.basename(self.video_url)
        fd, name = tempfile.mkstemp(suffix='-' + basename)
        destination = os.fdopen(fd, 'w')

        def close(dest):
            dest.close()
            return name

        runner = self.runners['download']
        runner.destination = destination
        return runner.getTask().addCallback(close)()

    def segment(self, filename):
        def cleanup(result):
            os.remove(filename)
            return result

        runner = self.runners['segment']
        runner.video_file = filename
        return runner.getTask().addBoth(cleanup)()

    def crop(self, sequences):
        runner = self.runners['crop']
        runner.sequences = sequences
        return runner.getTask()()

    def analyze(self, sequences):
        runner = self.runners['analyze']
        runner.sequences = sequences
        return runner.getTask()()

    def serialize(self, sequences):
        self.sequences = sequences
        return self.runners['encode'].getTask()()

    def _serialize(self):
        root = etree.Element("sequences")

        root.set("duration", str(self.duration))
        root.set("framerate", str(self.framerate))
        root.set("framescount", str(self.framescount))

        for seq in self.sequences:
            root.append(seq.toxml())

        return root

    def upload(self, document):
        result = etree.tostring(document, pretty_print=True)

        runner = self.runners['upload']
        runner.source = StringIO.StringIO(result)
        runner.size = len(result)
        runner.name = "analysis results"
        return runner.getTask()()


class IdentificationDelegate(object):

    implements(tasks.ITaskRunner)

    def __init__(self, segmentation_url, metadata_url, upload_url):
        upload_url += '/alignment.xml'
        
        self.segmentation_url = segmentation_url
        self.metadata_url = metadata_url

        self.runners = {
            'download_segmentation': analyzer_tasks.FileDownloadTask(segmentation_url),
            'download_metadata': analyzer_tasks.FileDownloadTask(metadata_url),
            'identify': alignment.Identification(),
            #'encode': None,
            'upload': analyzer_tasks.FileUploadTask(destination=upload_url)
        }

        alltasks = [r.getTask() for r in self.runners.values()]
        self.task = tasks.CompoundTask('Video analysis', self, alltasks)

    def getTask(self):
        return self.task

    @defer.inlineCallbacks
    def start(self):
        # Launch downloads concurrently
        segmentation = self.download(
            self.segmentation_url,
            self.runners['download_segmentation']
        )
        metadata = self.download(
            self.metadata_url,
            self.runners['download_metadata']
        )

        # Parse the slideshow metadata
        metadata_temp = yield metadata
        metadata = etree.parse(metadata_temp)

        slides = blist.sortedset()
        for slide in metadata.xpath('slide'):
            features = slide.xpath('features/text()')[0].split(' ')
            features = [float(i) for i in features]

            path = slide.get('imagepath')
            num = int(slide.get('id'))
            slides.add(alignment.Slide(num, features, path))

        # Parse the video segmentation
        segmentation_temp = yield segmentation
        segmentation = etree.parse(segmentation_temp)

        framerate = float(segmentation.getroot().get('framerate'))

        sequences = blist.sortedset()
        for sequence in segmentation.xpath('sequence'):
            features = sequence.xpath('features/text()')[0].split(' ')
            features = [float(i) for i in features]

            first = int(sequence.xpath('first-frame/@number')[0])
            first = alignment.Frame(first, framerate=framerate)

            last = int(sequence.xpath('last-frame/@number')[0])
            last = alignment.Frame(last, features, framerate=framerate)

            isunstable = not int(sequence.get('stable'))

            sequences.add(alignment.Sequence(first, last, unstable=isunstable))

        # Start identification task
        ident = self.runners['identify']
        ident.slides = slides
        ident.segmentation = sequences
        matches = yield ident.getTask()()
        
        # Serialize results
        root = etree.Element("alignment")

        for match in matches:
            root.append(match.toxml())

        # Cleanup temporary files
        filepath.FilePath(metadata_temp).remove()
        filepath.FilePath(segmentation_temp).remove()

        # Upload results
        result = etree.tostring(root, pretty_print=True)

        runner = self.runners['upload']
        runner.source = StringIO.StringIO(result)
        runner.size = len(result)
        runner.name = "alignment results"
        runner.getTask()()

    def download(self, url, runner):
        basename = os.path.basename(url)
        fd, name = tempfile.mkstemp(prefix='smac-', suffix='-' + basename)
        destination = os.fdopen(fd, 'w')

        def close(dest):
            dest.close()
            return name

        runner.destination = destination
        return runner.getTask().addCallback(close)()

class Analyzer(Module):

    def remote_segmentVideo(self, video_url, upload_url):
        """
        :rtype: TaskID
        """
        upload_url += '/segmentation.xml'

        delegate = VideoAnalysisDelegate(video_url, upload_url)
        task = delegate.getTask()
        task.addTaskObserver(log.msg)
        self.task_manager.schedule(task)

        return task.id

    def remote_alignSlides(self, segmentation_url, slides_metadata_url, upload_url):
        delegate = IdentificationDelegate(segmentation_url, slides_metadata_url, upload_url)
        task = delegate.getTask()
        task.addTaskObserver(log.msg)
        self.task_manager.schedule(task)
        
        return task.id

    def remote_extractMetadata(self, slides_url, upload_url):
        upload_url += '/metadata.xml'

        delegate = SlideAnalysisDelegate(slides_url, upload_url)
        task = delegate.getTask()
        task.addTaskObserver(log.msg)
        self.task_manager.schedule(task)

        return task.id

