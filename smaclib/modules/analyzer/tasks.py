import os
import sys
import functools
import tempfile

from smaclib.modules.analyzer import segmentation
from smaclib.modules.analyzer import cropping
from smaclib import tasks
from smaclib import utils

from zope.interface import implements
from twisted.internet import reactor
from twisted.internet import threads


class VideoCroppingTask(object):
    implements(tasks.ITaskRunner)

    analyzing = "Analyzing frame {current}/{tot}..."
    cropping = "Cropping frame {current}/{tot}..."


    def __init__(self, sequences=None):
        self.sequences = sequences
        self.analyzed = 0
        self.cropped = 0
        self.task = tasks.Task("Border cropping", self)

    def getTask(self):
        return self.task

    def start(self):
        self.task._statustext = self.analyzing.format(
            current=1,
            tot=len(self.sequences)
        )
        d = threads.deferToThread(self.crop)
        d.addCallback(self.cropping_completed)

    def crop(self):
        cropper = cropping.BorderCropper()

        for seq in self.sequences:
            frame = seq.last_frame
            reactor.callFromThread(self.frame_processed)
            cropper.process(frame.image)
            frame.close()

        border = cropper.compute_border()

        for seq in self.sequences:
            frame = seq.last_frame
            reactor.callFromThread(self.frame_cropped)
            frame.image = frame.image.crop(border)
            frame.save()

    def update_completion(self):
        # Approximate a linear task completion time
        analysis_weight = 0.8
        cropping_weight = 1.0 - analysis_weight

        completed = self.analyzed * analysis_weight \
                  + self.cropped * cropping_weight

        self.task.completed =  completed / len(self.sequences)

    def frame_processed(self):
        self.task._statustext = self.analyzing.format(
            current=self.analyzed + 1,
            tot=len(self.sequences)
        )
        self.update_completion()
        self.analyzed += 1

    def frame_cropped(self):
        self.task._statustext = self.cropping.format(
            current=self.cropped + 1,
            tot=len(self.sequences)
        )
        self.update_completion()
        self.cropped += 1

    def cropping_completed(self, _):
        status = "Border cropping completed ({tot} frames processed)".format(
            tot=len(self.sequences)
        )
        self.task.callback(self.sequences, status)


class VideoSegmentationTask(object):
    implements(tasks.ITaskRunner)

    title = "Segmenting video '{path}', {sequences} sequences found"

    def __init__(self, video_file=None):
        if video_file is not None:
            self.video_file = video_file
        self.sequences = []

        self.task = tasks.Task("Video segmentation", self)

    @property
    def video_file(self):
        return self._video_file
    
    @video_file.setter
    def video_file(self, video_file):
        self._video_file = video_file
        self.path = os.path.basename(video_file)

    def getTask(self):
        return self.task

    def start(self):
        self.task._statustext = self.title.format(
            path=self.path,
            sequences=len(self.sequences)
        )
        d = threads.deferToThread(self.segment)
        d.addCallback(self.segmentation_completed)

    def segment(self):
        callback = functools.partial(reactor.callFromThread,
                                     self.segmentation_advanced)

        with utils.discard(sys.stderr, 2):
            with utils.discard(1):
                reader = ObservableVideoReader(
                    video_path=self.video_file,
                    callback=callback
                )
            self.framescount = reader.framescount
            self.duration = reader.duration
            self.framerate = reader.framerate
            segmenter = segmentation.VideoSegmenter(reader)

            for sequence in segmenter.sequences():
                reactor.callFromThread(self.sequence_found, sequence)

    def segmentation_completed(self, result):
        status = u"Segmentation of '{path}' done, {sequences} sequences found"
        status = status.format(path=self.path, sequences=len(self.sequences))

        res = self.sequences, self.duration, self.framerate, self.framescount

        self.task.callback(res, status)

    def segmentation_advanced(self, frame):
        self.task.completed =  1. * frame.number / self.framescount

    def sequence_found(self, sequence):
        self.sequences.append(sequence)
        fd, name = tempfile.mkstemp(suffix='-frame-{0:09d}.png'.format(sequence.last_frame.number))
        os.close(fd)
        sequence.last_frame.save(name)
        sequence.first_frame.image = None
        self.task.statustext = self.title.format(
            path=self.path,
            sequences=len(self.sequences)
        )


class SlideAnalysisTask(object):
    implements(tasks.ITaskRunner)

    title = "Analyzing slide {current}/{tot}..."

    def __init__(self, slides=None):
        self.slides = slides
        self.analyzed = 0
        self.task = tasks.Task("Feature vector generation", self)

    def getTask(self):
        return self.task

    def start(self):
        self.task._statustext = self.title.format(
            current=1,
            tot=len(self.slides)
        )
        d = threads.deferToThread(self.analyze)
        d.addCallback(self.analysis_completed)

    def analyze(self):
        for slide in self.slides:
            reactor.callFromThread(self.slide_processed)
            # Trigger generation
            features = slide.features

    def slide_processed(self):
        self.analyzed += 1
        self.task._statustext = self.title.format(
            current=self.analyzed,
            tot=len(self.slides)
        )
        self.task.completed = (self.analyzed - 1.) / len(self.slides)

    def analysis_completed(self, features):
        status = "Slide analysis completed ({tot} slides processed)".format(
            tot=len(self.slides)
        )
        self.task.callback(self.slides, status)


class FrameAnalysisTask(object):
    implements(tasks.ITaskRunner)

    title = "Analyzing frame {current}/{tot}..."

    def __init__(self, sequences=None):
        self.sequences = sequences
        self.analyzed = 0
        self.task = tasks.Task("Feature vector generation", self)

    def getTask(self):
        return self.task

    def start(self):
        self.task._statustext = self.title.format(
            current=1,
            tot=len(self.sequences)
        )
        d = threads.deferToThread(self.analyze)
        d.addCallback(self.analysis_completed)

    def analyze(self):
        for seq in self.sequences:
            frame = seq.last_frame
            reactor.callFromThread(self.frame_processed)
            # Trigger generation
            seq.features = frame.features
            frame.close()
            frame.delete()

    def frame_processed(self):
        self.analyzed += 1
        self.task._statustext = self.title.format(
            current=self.analyzed,
            tot=len(self.sequences)
        )
        self.task.completed =  (self.analyzed - 1.) / len(self.sequences)

    def analysis_completed(self, features):
        status = "Frame analysis completed ({tot} frames processed)".format(
            tot=len(self.sequences)
        )
        self.task.callback(self.sequences, status)


class ObservableVideoReader(segmentation.VideoReader):

    def __init__(self, callback, *args, **kwargs):
        super(ObservableVideoReader, self).__init__(*args, **kwargs)
        self.callback = callback

    def iterframes(self, *args, **kwargs):
        iterator = super(ObservableVideoReader, self).iterframes(*args, **kwargs)

        for frame in iterator:
            self.callback(frame)
            yield frame

