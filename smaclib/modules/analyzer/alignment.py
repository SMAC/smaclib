import sys
import itertools
import blist

from lxml import etree

from twisted.internet import reactor
from twisted.internet import threads
from twisted.internet import defer
from smaclib import tasks
from smaclib.modules.analyzer.identification import get_diff_score

from zope.interface import implements

class Identification(object):

    implements(tasks.ITaskRunner)

    def __init__(self, sequences=None, slides=None):
        """
        The segmentation sortedset is modified in place.
        """
        self.task = tasks.Task("Slides alignment", self)
        self.segmentation = sequences
        self.slides = slides

    def getTask(self):
        return self.task

    @defer.inlineCallbacks
    def start(self):
        res = yield threads.deferToThread(self.identify)
        self.task.callback(res, "Alignment completed")

    def updateTask(self, statustext):
        def update():
            self.task.statustext = statustext
        reactor.callFromThread(update)

    def get_sequences(self, segmentation, slides):
        """
        Returns a list of sequences representing the first basic identification
        obtained by matching the features vector of each frame with the
        features vectors of each slide.
        """

        sequences = blist.sortedset()

        for sequence in segmentation:
            for slide in slides:
                sequence.process_candidate(slide)

            if sequence.keep():
                sequences.add(sequence)

        return sequences

    def get_base_matches(self, sequences):
        results = {}

        for sequence in sequences:
            for slide in sequence.candidates:
                self._get_path(sequences, results, sequence, slide)

        path = max(results.values(), key=lambda p: p[0])[1]

        for match in path:
            match.mark_as_assigned()

        return blist.sortedset(path)

    def _get_path(self, sequences, results, sequence, slide):
        if (sequence, slide) in results:
            return results[sequence, slide]

        max_confidence = 0
        best_moves = []

        for test_seq in sequences[sequences.index(sequence) + 1:]:
            for test_slide in test_seq.candidates:
                if test_slide.id <= slide.id:
                    continue

                confidence, moves = self._get_path(sequences, results,
                                                   test_seq, test_slide)

                if confidence > max_confidence:
                    max_confidence = confidence
                    best_moves = moves

        moves = [Match(sequence, slide)] + best_moves
        results[sequence, slide] = (max_confidence + sequence.confidence, moves)

        return results[sequence, slide]

    def identify(self):
        self.updateTask("Building base sequences...")
        sequences = self.get_sequences(self.segmentation, self.slides)

        self.updateTask("Getting base matches...")
        matches = self.get_base_matches(sequences)

        # Find extra slide candidates
        self.updateTask("Finding extra slide candidates...")
        extra_matches = (seq for seq in sequences if seq.is_remnant)
        extra_matches = [Match(s, s.candidates[0], False) for s in extra_matches]
        extra_matches = blist.sortedset(extra_matches)

        self.updateTask("Merging off sequence slides...")
        self.merge_off_sequence_slides(matches, extra_matches)

        self.updateTask("Merging redundant sequences (pass 1/2)...")
        self.merge_redundant_sequences(matches)

        self.updateTask("Merging remnant sequences...")
        self.merge_remnant_sequences(matches, extra_matches)

        self.updateTask("Merging redundant sequences (pass 2/2)...")
        self.merge_redundant_sequences(matches)

        self.updateTask("Assigning orphan sequences...")
        self.assign_orphan_sequences(matches, self.slides)

        self.updateTask("Filtering trailing sequences...")
        self.filter_trailling_sequences(matches)

        return matches

    @staticmethod
    def filter_trailling_sequences(matches):
        """
        Remove trailing matches with too short sequences from the ``matches``
        sorted set.
        """

        while matches[-1].sequence.discard_trailing:
            matches.pop()

        return None # Data structures are modified in-place

    def assign_orphan_sequences(self, matches, slides):
        """
        Assign unidentified (orphan) sequences either to the previous or the
        following formally identified slide according to the result of the
        presentation file analysis (if available).

        @postcondition: The result sequence contains no more "gap": all the
        sequences are assigned to a well defined slide.
        """

        if not hasattr(slides, 'analyzed'):
            # We simply proceed with default behaviour: all orphan sequences
            # will be assigned to the following formally identified slides
            # (this is related to the fact that identification will mostly
            # succeed with the slide in their final displayed state).

            first_match = matches[0]
            if first_match.extended:
                end_frame = first_match.extended
            else:
                end_frame = first_match.sequence.end_frame
            prev_end_frame = end_frame
            first_match.sequence.end_frame = end_frame

            for match in matches[1:]:
                seq_id = match.sequence.end_frame
                match.sequence.start_frame = prev_end_frame
                ext = match.extended
                if ext:
                    end_frame = ext
                else:
                    end_frame = seq_id
                match.sequence.end_frame = end_frame
                prev_end_frame = end_frame
        else:
            raise NotImplementedError()

        ## The presentation file analysis result is available.
        #TRANSITION_AVG_TIME = 3.0
        #
        ## We first retrieve which are possibly animated and which are not.
        ## is_static: dictionary (slide_id, is_not_animated).
        #animated = set()
        #
        ## Parse the presentation file analysis result.
        #dom = parseString(analyzed_content)
        #
        #for slide in dom.getElementsByTagName("Slide"):
        #    slide_id = int(slide.getAttribute("displayOrder"))
        #
        #    for object in slide.getElementsByTagName("Object"):
        #        contains_no_anim = object.getAttribute("static").lower()
        #        if contains_no_anim in ("false", "maybe"):
        #            animated.add(slide_id)
        #            break
        #
        ## Proceed with the assignement.
        #seq = result_sequence[0]
        #seq_id = seq["sequence_id"]
        #ext = seq["extended_to"]
        #prev_end_frame = ext if ext else seq["end_frame"]
        #prev_seq = seq
        #
        #for seq in result_sequence[1:]:
        #    slide_id = seq["matched_slide"]
        #    seq_id = seq["sequence_id"]
        #    start_frame = seq["start_frame"]
        #
        #    # Check: if the current slide contains no anim, or if the delay
        #    # with the previous slide is short enough: we assign the orphan
        #    # sequence to the previous slide (non-default assignment).
        #    if (start_frame - prev_end_frame) / framerate < TRANSITION_AVG_TIME or slide_id in animated:
        #        seq["start_frame"] = start_frame = prev_end_frame + 1
        #
        #    ext = seq["extended_to"]
        #    prev_end_frame = ext if ext else seq["end_frame"]
        #
        #    # Whatever the type of assignment we choosed, we can set the end
        #    # of the previous sequence just before the start of the current
        #    # sequence.
        #    prev_seq["end_frame"] = start_frame - 1
        #    prev_seq = seq
        #prev_seq["end_frame"] = prev_end_frame

    def merge_remnant_sequences(self, matches, extra_matches):
        result_seq_index = 0
        prev_slide = -1
        next_seq = matches[0].sequence
        next_slide = matches[0].slide

        for extra_match in extra_matches:
            seq = extra_match.sequence

            try:
                while seq >= next_seq:
                    result_seq_index += 1
                    prev_slide = next_slide
                    next_slide = matches[result_seq_index].slide
                    next_seq = matches[result_seq_index].sequence
            except IndexError:
                next_slide = -1
                next_seq = sys.maxint

            if result_seq_index:
                ext = matches[result_seq_index - 1].extended
                if ext and ext >= seq.end_frame:
                    # Overlapping extra slide, ignore it
                    continue

            if extra_match.slide in (next_slide, prev_slide):
                matches.insert(result_seq_index, extra_match)
                result_seq_index += 1

    @staticmethod
    def merge_redundant_sequences(matches):
        """
        Merge the redundant sequences in the result sequence. We just check
        the slide of each element, if we find a redundancy, we merge them.

        The merge operation is done by suppressing the second element and
        updating the metadata of the first element to extend it to the end of
        the second one.
        """
        prev_match = matches[0]
        i = 1

        while i < len(matches):
            match = matches[i]

            if match.slide == prev_match.slide:
                prev_match.extend_to(match)
                matches.remove(match)
                match = prev_match
            else:
                prev_match = match
                i += 1

        return None # Data structures are modified in-place

    @staticmethod
    def merge_off_sequence_slides(matches, extra_matches):
        """
        Inserts extra matches considered as off-sequence matches into the
        result set and removes them from the extra matches set.
        """

        off_matches = [match for match in extra_matches if match.is_off]

        extra_matches -= off_matches
        matches |= off_matches

        return None # Data structures are modified in-place

class Frame(object):

    framerate = 25.

    def __init__(self, frame_num, features=None, framerate=25.):
        self.framerate = framerate
        self.num = frame_num
        self.timestamp = (frame_num - 1.) / self.framerate
        self.features = features

    def __str__(self):
        return str(self.num)

    def __repr__(self):
        return str(self.num)

    def __sub__(self, other):
        if type(other) == int:
            return Frame(self.num - other)

        return Frame(self.num - other.num)


class Match(object):

    def __init__(self, seq, slide, base=True):
        self.sequence = seq
        self.slide = slide
        self.base = base
        self.extended = None

    def extend_to(self, match):
        self.extended = match.extended if match.extended else match.sequence.end_frame

        if match.base:
            self.base = True

        return self

    def __cmp__(self, other):
        return self.sequence.__cmp__(other.sequence)

    @property
    def is_off(self):
        if self.sequence.duration <= self.sequence.off_seq_min_duration:
            return False

        if self.sequence.confidence <= self.sequence.off_seq_min_conf:
            return False

        if self.sequence.unstable:
            return False

        if self.slide.assigned_to is None:
            return True

        if self.sequence.confidence >= self.sequence.dupl_seq_conf_thsld:
            return True

        slide_base_score = self.slide.assigned_to.best_score
        slide_score = self.sequence.best_score

        if slide_score >= slide_base_score:
            return True

        if (slide_base_score / slide_score) >= self.sequence.dupl_seq_max_var:
            return True

        return False

    def mark_as_assigned(self):
        self.sequence.assigned_slide = self.slide
        self.slide.assigned_to = self.sequence

    def toxml(self):
        seq = etree.Element("sequence")

        seq.set('slide-num', str(self.slide.id))

        frame = etree.SubElement(seq, "first-frame")
        frame.set("number", str(self.sequence.start_frame.num))
        frame.set("timestamp", str(self.sequence.start_frame.timestamp))

        frame = etree.SubElement(seq, "last-frame")
        frame.set("number", str(self.sequence.end_frame.num))
        frame.set("timestamp", str(self.sequence.end_frame.timestamp))

        return seq

    def __repr__(self):
        return '<Match sequence: {0!r}, slide: {1!r}>'.format(self.sequence, self.slide)


class Slide(object):
    def __init__(self, slide_id, features=None, imagepath=''):
        self.id = slide_id
        self.imagepath = imagepath
        self.features = features
        self.displayed = True
        self.assigned_to = None

    def __cmp__(self, other):
        return self.id.__cmp__(other.id)

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return "Slide({0!s})".format(self)


class Sequence(object):

    trailling_seq_min_duration = 3.0
    """
    Minimum duration for tralling sequence.
    """

    dupl_seq_max_var = 0.6
    """
    The maximum difference score variance a segment may have against an already
    matched slide in the base sequence (if such exists).
    """

    dupl_seq_conf_thsld = 5.0
    """
    If the identification confidence is higher than this thresold, then the
    matching is considered reliable enough to skip the duplicata during the
    "base sequence" check.
    """

    missing_max_confidence = 0.15
    """
    Maximum relative confidence against the best match an alternative candidate
    to be so-considered. This thresold permits to define with which sensibility
    we want to look for missing slide in the base sequence.
    """

    min_confidence = 0.1
    """
    Confidence thresold for unidentifiable sequence filtering. In order to be
    filtered the sequence have to more than C{max_nb_of_candidates} and
    confidence lesser than this thresold.
    """

    max_nb_of_candidates = 5
    """
    Maximal number of alternative candidates a usable identification should
    have. Used coinjointly with C{min_confidence}.
    """

    remnant_seq_min_conf = 0.4
    """
    Minimum confidence a segment must have to be considered as a potential
    remnant slide.
    """

    off_seq_min_conf = 0.5
    """
    Minimum identification confidence a segment must have in order to be
    considered as a potential off-sequence slide.
    """

    off_seq_min_duration = 3.0
    """
    Minimum duration a segment must have in order to be considered as a
    potential off-sequence slide. Properly speaking, the off-sequence slide
    has to display an identifiable state for at least C{off_seq_min_duration}.
    This is to avoid that most skipped slide to be considered off-sequence
    when going back in the slide stream.
    """

    def __init__(self, start_frame, end_frame, unstable=False):
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.unstable = unstable
        self.assigned_slide = None
        self._candidates = [{}, None, 0]

    def __cmp__(self, other):
        return self.id.__cmp__(other.id)

    @property
    def discard_trailing(self):
        return self.duration < self.trailling_seq_min_duration

    @property
    def is_remnant(self):
        return self.assigned_slide is None and self.confidence > self.remnant_seq_min_conf

    @property
    def duration(self):
        return self.end_frame.timestamp - self.start_frame.timestamp

    @property
    def id(self):
        return self.end_frame.num

    def process_candidate(self, slide):
        diff = get_diff_score(slide.features, self.end_frame.features)
        self._candidates[0][slide] = diff
        self._candidates[1] = None

    @property
    def best_score(self):
        return self._candidates[0][self.candidates[0]]

    @property
    def candidates(self):
        if self._candidates[1] is None:
            self._process_candidates()

        return self._candidates[1]

    def _process_candidates(self):
        candidates = self._candidates[0].items()
        candidates.sort(key=lambda c: c[1])

        best = candidates[0][1]
        second_best = candidates[1][1]

        take = lambda c: (c[1] - best) / best <= self.missing_max_confidence
        candidates = itertools.takewhile(take, candidates)
        candidates = [c for c, _ in candidates if c.displayed]

        self._candidates[1] = candidates
        self._candidates[2] = (second_best - best) / best

    def keep(self):
        if self.confidence >= self.min_confidence:
            return True

        if len(self.candidates) <= self.max_nb_of_candidates:
            return True

        return False

    @property
    def confidence(self):
        if self._candidates[1] is None:
            self._process_candidates()

        return self._candidates[2]

    def __repr__(self):
        return "Sequence({0!s}, {1!s})".format(self.start_frame, self.end_frame)

