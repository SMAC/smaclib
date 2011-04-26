import itertools
import functools
import collections

import ImageFilter

try:
    import psyco
    psyco # Shutup pyflakes
except ImportError:
    psyco = None


def optimize(func):
    """
    A decorator to wrap a function or method in a ``psyco.proxy`` call to
    optimize it, falling back to the original function if psyco is not
    available.
    """
    if psyco is None:
        return func
    
    return functools.update_wrapper(psyco.proxy(func), func)


LR, TD, Y_AXIS = 1, 2, 4
TOP_DOWN = TD | LR | Y_AXIS
BOTTOM_UP = LR | Y_AXIS
RIGHT_TO_LEFT = RTL = TD
LEFT_TO_RIGHT = LTR = TD | LR


@optimize
def itercoords(direction, width, height):
    """
    Generator to iterate over an (x, y) coordinates pair starting from a given
    side (TOP_DOWN, BOTTOM_UP, RIGHT_TO_LEFT, LEFT_TO_RIGHT).
    """
    height = xrange(height)
    if not (direction & TD):
        height = reversed(height)
    
    width = xrange(width)
    if not (direction & LR):
        width = reversed(width)
    
    swap = direction & LR and direction & Y_AXIS
    
    if swap:
        width, height = height, width
    
    for x, y in itertools.product(width, height):
        if swap:
            yield y, x
        else:
            yield x, y


class BorderCropper(object):
    """
    Utility class to find the black border on a set of images extracted from 
    video frames and removing it.
    """
    
    # TODO: Why do we need to use the filter?
    image_filter = ImageFilter.MedianFilter(size=9)
    """
    Filter to be applied to each image before searching for the borders. Set
    this to ``None`` to not apply any filter.
    """
    
    border_detection_threshold = 80
    """
    Color magnitude thresold for the border removal algorithm. Used to detect
    the end of a black border. Color magnitude is simply defined as the sum of
    each color channel value.
    """
    
    min_ratio = 1.15
    """
    Minimum width-to-height ratio the video frame must have after removing the
    border.
    """
    max_ratio = 1.34
    """
    Maximum width-to-height ratio the video frame must have after removing the
    border.
    """
    
    def __init__(self):
        self.borders = collections.defaultdict(lambda: 0)
        """
        A mapping of borders (left, top, right, bottom) to an integer
        representing the number of times this border was encountered.
        """
        
        self.max_width = 0
        """
        The maximum processed image width. Used to create the border if no
        other border satifies the ratio conditions.
        """
        
        self.max_height = 0
        """
        The maximum processed image height. Used to create the border if no
        other border satifies the ratio conditions.
        """

    def process_side(self, pixels, size, side):
        for x, y in itercoords(side, *size):
            if sum(pixels[x, y]) > self.border_detection_threshold:
                break
        return x, y

    @optimize
    def process(self, image):
        """
        Processes a single image and adds its border to the internal mapping
        for later computing.
        """
        if self.image_filter:
            image = image.filter(self.image_filter)
        
        pixels = image.load()
        
        self.max_width = max(self.max_width, image.size[0])
        self.max_height = max(self.max_height, image.size[1])
        
        top = self.process_side(pixels, image.size, TOP_DOWN)[1]
        bottom = self.process_side(pixels, image.size, BOTTOM_UP)[1]
        
        if top > bottom:
            return
        
        left = self.process_side(pixels, image.size, LTR)[0]
        right = self.process_side(pixels, image.size, RTL)[0]
        
        if left > right:
            return
        
        self.borders[left, top, right, bottom] += 1
        
        return (left, top, right, bottom)
    
    def compute_border(self):
        """
        Computes the final border to be applied to the set of processed images.
        """
        borders = self.borders.items()
        borders.sort(key=lambda b: b[1], reverse=True)
        
        for border, _ in borders:
            left, top, right, bottom = border
            ratio = float(right - left) / float(bottom - top)
            if self.min_ratio < ratio < self.max_ratio:
                return left, top, right, bottom
        else:
            return 0, 0, self.max_width - 1, self.max_height - 1


