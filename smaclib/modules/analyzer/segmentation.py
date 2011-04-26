import os
import sys
import cPickle as pickle
from collections import namedtuple

import pyffmpeg
from lxml import etree
import Image
import ImageFilter
import ImageChops
import ImageStat

from smaclib.modules.analyzer import identification


# pylint: disable=W0105,C0103


def difference(img_a, img_b):
    """
    Calculates the difference between two images, defined as the sum of the
    variance of each color channel contained by the image resulting from their
    subtraction.
    """
    return sum(ImageStat.Stat(ImageChops.difference(img_a, img_b)).var)


class Sequence(object):
    """
    A sequence recognized in the automatic segmentation process. Has a first
    and a last frame, the score at which it was recognized and a flag to
    indicate if it is unstable or not.
    """
    def __init__(self, first_frame, score):
        self.score = score
        self.first_frame = first_frame
        self.last_frame = first_frame
        self.unstable = False

    @property
    def id(self):
        return self.first_frame

    def toxml(self):
        seq = etree.Element("sequence")
        seq.set("stable", str(int(not self.unstable)))
        seq.set("score", str(self.score))
        
        frame = etree.SubElement(seq, "first-frame")
        frame.set("number", str(self.first_frame.number))
        frame.set("timestamp", str(self.first_frame.timestamp))
        
        frame = etree.SubElement(seq, "last-frame")
        frame.set("number", str(self.last_frame.number))
        frame.set("timestamp", str(self.last_frame.timestamp))
        
        features = etree.SubElement(seq, "features")
        features.text = " ".join([str(f) for f in self.features])
        
        return seq

    def __str__(self):
        attrs = 'start_frame="{0.first_frame.number}" end_frame="{0.last' \
                '_frame.number}" id="{0.last_frame.number}" score="{1}"'
        attrs = attrs.format(self, int(self.score))

        if self.unstable:
            return "    <unst_vid_seq {0} />".format(attrs)
        else:
            return "    <vid_seq {0} />".format(attrs,
                                                self.first_frame.timestamp)


class Slide(object):
    def __init__(self, slide_id, image_file):
        self.id = slide_id
        self.image_file = image_file
        self.displayed = True
        self._features = []

    @property
    def features(self):
        if not self._features:
            img = Image.open(self.image_file)
            self._features = identification.gen_feature_vect(img, low_quality=False)
            del img

        return self._features

    def __cmp__(self, other):
        return self.id.__cmp__(other.id)

    def toxml(self):
        slide = etree.Element("slide")
        slide.set("displayed", str(int(self.displayed)))
        slide.set("id", str(self.id))
        slide.set("imagepath", self.image_file)

        features = etree.SubElement(slide, "features")
        features.text = " ".join([str(f) for f in self.features])

        return slide


class Frame(namedtuple('Frame', 'number timestamp image')):
    """
    Named tuple to hold frame objects with an image, a number and a timestamp
    attribute.
    """
    def __init__(self, number, timestamp, image):
        self._number = number
        self._timestamp = timestamp
        self._image = image
        self._filename = None
    
    @property
    def number(self):
        return self._number
    
    @property
    def timestamp(self):
        return self._timestamp
    
    @property
    def image(self):
        if self._image is None:
            self._image = Image.open(self._filename)
        return self._image

    @property
    def features(self):
        return identification.gen_feature_vect(self.image, low_quality=True)

    @image.setter
    def image(self, image):
        self._image = image
    
    def delete(self):
        if self._filename is None:
            return
        
        os.remove(self._filename)

    def close(self):
        assert self._filename is not None, "Save the frame before closing it."
        self._image = None

    def save(self, filename=None, close=True, *args, **kwargs):
        """
        Proxy method to the ``Image.save`` method of the frame image.
        """
        if filename is not None:
            self._filename = filename.format(frame=self)
        
        assert self._filename is not None, "You have to provide a filename."
        
        self.image.save(self._filename, *args, **kwargs)
        
        if close:
            self.close()


class VideoReader(object):

    def __init__(self, video_path):
        self.filename = video_path

        self.reader = pyffmpeg.FFMpegReader()
        """The reader for the given video file."""

        self.reader.open(video_path, pyffmpeg.TS_VIDEO_PIL)

        self.__video = None
        self.__framescount = None

    @property
    def video(self):
        if self.__video is None:
            self.__video = self.reader.get_tracks()[0]

        return self.__video

    @property
    def duration(self):
        return max(self.video.duration_time(), self.reader.duration_time())

    @property
    def framerate(self):
        return self.video.get_fps()

    @property
    def framescount(self):
        if self.__framescount is None:
            self.__framescount = int(self.duration * self.framerate)

        return self.__framescount

    def iterframes(self, step=1):
        """
        Generator of frame images and metadata for the currently open video
        stream.

        By default the generator yields a result each frame; this value can be
        adjusted by setting the optional ``step`` parameter.

        The tuple returned for each step contains the following values:

            (frame_number, frame_timestamp, frame_image)

        """
        for frame_num in xrange(1, self.framescount, step):
            self.video.seek_to_frame(frame_num)
            #video.get_current_frame() -> pts, count, frame, frametype, vectors
            pts, _, image, _, _ = self.video.get_current_frame()
            yield Frame(frame_num, pts / 1000000., image.copy())


class VideoSegmenter(object):
    """
    An object specialized in segmenting a video of a slideshow into chunks by
    comparing subsequent frames with a certain time-resolution.
    """

    frame_filter = ImageFilter.Kernel(
        (5, 5),
        [0, 0, 1, 0, 0,
         0, 0, 1, 0, 0,
         0, 0, 1, 0, 0,
         0, 0, 1, 0, 0,
         0, 0, 1, 0, 0]
    )
    """
    Filter to be applied to the frame image before starting to process it.
    """

    resolution = 25
    """
    Detection granularity in frames.
    """

    scd_adjust_interval = 180.0
    """
    Define after how many frames we check the detection rate to adjust it to
    the upper or lower threshold, if necessary.
    """

    scd_upper_threshold = 200
    """
    Upper score threshold for detecting a slide change. The score is defined as
    the sum of the variance of each color channel of the difference of two
    frames.
    """

    scd_lower_threshold = 100
    """
    Lower score threshold for detecting a slide change. The score is defined as
    the sum of the variance of each color channel of the difference of two
    frames. This is the default threshold.
    """

    scd_rate_upper_threshold = 0.5
    """
    Minimum slide change detection rate we have to reach for switching to the
    upper threshold.
    """

    scd_rate_lower_threshold = 0.3
    """
    Maximum slide change detection rate we have to reach for switching to the
    lower threshold.
    """

    max_changes_in_a_row = 2
    """
    Maximum of detection in a row before switching to passive mode.
    """

    def __init__(self, video_reader):
        """
        Creates a new segmentetion helper for the video read by the
        ``video_reader`` video_reader.
        """
        self.reader = video_reader
        """The reader for the given video file."""

        self.scd_interval = 0
        """Frames passed since the last threshold adjustement."""

        self.counters = {'changes': 0, 'static': 0, 'nochanges': 0}
        """Number of detected/no-changes/statics since the last threshold
        adjustement."""

        self.scores = {'changes': 0, 'static': 0, 'nochanges': 0}
        """Number of detected/no-changes/statics since the last threshold
        adjustement."""

        self.threshold = self.scd_lower_threshold
        """Current threshold for a slide change to be detected."""

        self.changes_in_a_row = 0
        """Number of slide changes detects in a row."""

    def adjust_threshold(self):
        """
        Checks the slide change detection threshold each
        ``VideoSegmenter.scd_adjust_interval`` frames and adjust it to the
        upper or lower threshold, as necessary.
        """

        self.scd_interval += self.resolution

        if self.scd_interval < self.scd_adjust_interval:
            return

        scd_rate = self.counters['changes'] / self.scd_adjust_interval

        if not self.counters['changes']:
            self.scores['changes'] = 0
            self.counters['changes'] = 1

        if not self.counters['nochanges']:
            self.scores['nochanges'] = 0
            self.counters['nochanges'] = 1

        mean_change = self.scores['changes'] / self.counters['changes']
        mean_nochange = self.scores['nochanges'] / self.counters['nochanges']

        # TODO: log
        #print "CHECK: current scd rate: %f, mean_change_score is %f" % (
        #scd_rate, mean_change_score)

        if self.threshold == self.scd_lower_threshold:
            if scd_rate > self.scd_rate_upper_threshold \
               and mean_change < self.scd_upper_threshold:
                # TODO: log
                #print "My threshold is maybe too low... Fallback to the upper
                #threshold."
                self.threshold = self.scd_upper_threshold
        else:
            if scd_rate < self.scd_rate_lower_threshold \
               and mean_nochange > self.scd_lower_threshold:
                # TODO: log
                #print "My threshold is maybe too high... Fallback to the lower
                #threshold."
                self.threshold = self.scd_lower_threshold

        self.scd_interval = 0

        self.counters['changes'] = 0
        self.counters['nochanges'] = 0

        self.scores['changes'] = 0
        self.scores['nochanges'] = 0

    def detect_change(self, previous, current):
        """
        Returns a tuple containing the score of the difference between the
        ``previous`` and ``current`` images (or 0 if no change was detected)
        and the number of changes in a row (or 0 if no change was detected).

        This method also does all bookkeeping for the different statistics
        needed to switch modes or adjust the threshold.
        """

        current_magnitude = difference(previous, current)

        if current_magnitude > self.threshold:
            self.counters['changes'] += 1
            self.scores['changes'] += current_magnitude

            self.counters['static'] = 0
            self.scores['static'] = 0

            self.changes_in_a_row += 1
        else:
            self.counters['nochanges'] += 1
            self.scores['nochanges'] += current_magnitude

            self.counters['static'] += 1
            self.scores['static'] += current_magnitude

            self.changes_in_a_row = 0
            current_magnitude = 0

        passive_mode = self.changes_in_a_row > self.max_changes_in_a_row

        self.adjust_threshold()

        return current_magnitude, passive_mode

    def sequences(self):
        """
        Generator for ``Sequence`` objects describing the segmentation of the
        video into different slide-related chunks.

        Note: the PIL library reuses image objects. Be sure to copy it if you
        want to reuse in sucessive generator iterations (use the .copy method)
        """

        frame = prev_frame = self.reader.iterframes(self.resolution).next()
        prev_blurred = frame.image.filter(self.frame_filter)

        seq = Sequence(frame, sys.maxint)
        seq.last_frame = frame

        for frame in self.reader.iterframes(self.resolution):
            blurred = frame.image.filter(self.frame_filter)

            score, passive_mode = self.detect_change(prev_blurred, blurred)

            if score:
                if passive_mode:
                    seq.unstable = True
                else:
                    yield seq
                    seq = Sequence(frame, score)

                # Always compare to the first frame of the sequence.
                prev_blurred = blurred
            else:
                if seq.unstable:
                    # Save the score before yielding the object in order to
                    # avoid its modification outside of the generator.
                    score = seq.score

                    # Set the last frame to the 2nd-last analyzed frame, as the
                    # previous one already belongs to the new sequence.
                    first_frame, seq.last_frame = seq.last_frame, prev_frame

                    yield seq
                    seq = Sequence(first_frame, score)

            prev_frame, seq.last_frame = seq.last_frame, frame

        yield seq


def main():
    """
    Test run
    """

    base = os.path.join(os.path.dirname(__file__), 'test-contrib')
    segm = os.path.join(base, 'segmentation.xml')

    save_pattern = os.path.join(base, 'frames', '{0:d}.png')

    if not os.path.exists(os.path.dirname(save_pattern)):
        os.makedirs(os.path.dirname(save_pattern))

    cropper = BorderCropper()
    frames = []

    with open(segm, 'w') as fh:
        fh.write('<xml>\n<vid_sequences contrib_id="test-contrib" total_'\
                 'length="934.040000" framerate="25.000000">\n')
        with discard(sys.stderr):
            for seq in VideoSegmenter(sys.argv[1]).sequences():
                name = save_pattern.format(seq.last_frame.number)
                frame = seq.last_frame.image
                frames.append(name)
                cropper.process(frame)
                frame.save(name, quality=100)
                fh.write(str(seq) + "\n")
                fh.flush()
                print name, "done"
        fh.write("</vid_sequences>\n</xml>")

    border = cropper.compute_border()

    archive(frames, os.path.join(base, 'frames.pickle'), border)

def archive(frames, dest, border=None):
    """
    Archiving process testing method
    """

    archived_frames = []

    for name in frames:
        im = Image.open(name)

        if border:
            im = im.crop(border)
            im.load()
            im.save(name)

        features = pickle.dumps(gen_feature_vect(im, low_quality=True))

        num = int(os.path.basename(name).split('.', 1)[0])
        archid = 'frame-{0}'.format(num)
        archived_frames.append((
            'test-contrib', os.path.basename(name), archid, 'frame', {
                "format": name.split('.')[1],
                "type": "video_slide",
                "features_vector" : features,
                "video_source" : 'video-id',
                "frame_number" : num
            }
        ))

    with open(dest, 'w') as fh:
        pickle.dump(archived_frames, fh)


if __name__ == '__main__':
    """
    To run the segmentation test, execute the following command:

        python segment.py path/to/the/videofile.avi

    The results will be in a directory called test-contrib. It will contain a
    frames directory with the cropped images of each frame, a frames.pickle file
    with a list of all frames and their features vectory and a segmentation.xml
    file with the segmentation information for the video.
    """
    main()
