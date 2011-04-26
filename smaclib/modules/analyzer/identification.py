"""
Provides image identification means to the SMAC infrastructure.

@author: U{Jean Revertera <mailto:jean.revertera@unifr.ch>}
@since: August 2008

@type t: C{int}
@var t: Define the size of the extraction matrices as well as how the "tracing"
will be applied.
@type N: C{int}
@var N: Number of columns in which the images will be segmented.
@type M: C{int}
@var M: Number of lines in which the images will be segmented.
@type GRADIENT_THRESOLD: C{int}
@var GRADIENT_THRESOLD: The mininum magnitude that an edge should have to be
validated.
@type gx: C{2d-array} of C{int}
@var gx: Matrix used to extract the horizontal edges magnitudes. Will be
applied by convolution on the grayscaled image.
@type gy: C{2d-array} of C{int}
@var gy: Matrix used to extract the vertical edges magnitudes.  Will be
applied by convolution on the grayscaled image.
"""
__author__ = 'Jean Revertera <jean.revertera@hefr.ch>' 
__docformat__ = 'epytext en'
__version__ = '0.1-final'

# Standards libs.
import sys

# External libs.
import ImageFilter
from numpy import reshape
from convolve import convolve2d


#full()
t = 8
N = 13 # 21
M = int(round(N / 1.333333))
GRADIENT_THRESOLD = 10
# We have to bypass the Python default limit number of recursive call.
sys.setrecursionlimit(2000)

# Construct the gx and gy matrices.
v = t/2
gx = [[-1, -2, -1]]
for i in xrange(0,v):
    gx.append([0,0,0])
gx.append([1,2,1])
gy = []

l1 = [-1]
l2 = [-2]
l3 = [-1]
for i in xrange(0,v):
    l1.append(0)
    l2.append(0)
    l3.append(0)
l1.append(1)
l2.append(2)
l3.append(1)

gy.append(l1)
gy.append(l2)
gy.append(l3)
"""
gx = [[1,1,1,1,2,1,1,1,1],[1,1,1,2,3,2,1,1,1],[1,1,2,3,4,3,2,1,1],[1,2,3,4,5,4,3,2,1],[0,0,0,0,0,0,0,0,0],[-1,-2,-3,-4,-5,-4,-3,-2,-1],[-1,-1,-2,-3,-4,-3,-2,-1,-1],[-1,-1,-1,-2,-3,-2,-1,-1,-1],[-1,-1,-1,-1,-2,-1,-1,-1,-1]]

gy = [[1,1,1,1,0,-1,-1,-1,-1],[1,1,1,2,0,-2,-1,-1,-1],[1,1,2,3,0,-3,-2,-1,-1],[1,2,3,4,0,-4,-3,-2,-1],[2,3,4,5,0,-5,-4,-3,-2],[1,2,3,4,0,-4,-3,-2,-1],[1,1,2,3,0,-3,-2,-1,-1],[1,1,1,2,0,-2,-1,-1,-1],[1,1,1,1,0,-1,-1,-1,-1]]

"""
# Delete temporary variables.
del i
del v
del l1
del l2
del l3

def _filter_edges(hm, vm, directions, edges, index, width, height):
    """
    Internal method used to filter edges.

    @type hm: C{2d-array} of C{int}
    @param hm: Matrix containing the horizontal edges magnitude.
    @type vm: C{2d-array} of C{int}
    @param vm: Matrix containing the vertical edges magnitude.
    @type directions: C{2d-array} of C{bool}
    @param directions: Matrix referencing the directions of the edges. C{True}
    denotes a vertical edge, while C{False} denotes a horizontal edge.
    @type edges: C{2d-array} of C{bool}
    @param edges: Matrix referencing where are located the edges.
    @type index: C{int}
    @param index: the pixel linearized position which has to be tested.
    @type width: C{int}
    @param width: The width of image.
    @type height: C{int}
    @param height: The height of image.
    """
    # Get the edge direction.
    dir = directions[index]
    # Translate the index into polar coordinates.
    x = index % width
    y = index / width
    # If the edge magnitude is superior to the gradient thresold:
    if((not dir and hm[y][x] < GRADIENT_THRESOLD) or (dir and
            vm[y][x] < GRADIENT_THRESOLD)):
        edges[index] = False

def gen_feature_vect(img, low_quality=False):
    """
    Generate a feature vector from the image at the specified location.

    @type fname: C{string}
    @param fname: Path to the image file.
    @type low_quality: C{bool}
    @param low_quality: C{True} if the image is considered of a low quality,
    C{False} otherwise. A sharpening filter is applied on low quality
    images. In the current case of SMAC, the video frame are considered of low
    quality, which is not the case of the slide pictures.

    @rtype: C{list} of C{float}
    @return: The feature vector corresponding to this image.
    """
    # If the image is from a low-quality source, we first try to sharpen its
    # its edges.
    if low_quality:
        img = img.filter(ImageFilter.SHARPEN)

    # Convert to grayscale with respect to the image luminosity, by doing a
    # Luma conversion.
    # See: http://www.pythonware.com/library/pil/handbook/image.htm
    img = img.convert("L")
    width = img.size[0]
    height = img.size[1]
    # The image nb of pixels.
    pixel_nb  = width * height
    # The data structure returned by the Image module is a 1-D shape, we
    # have to transform it to a 2D-matrix.
    m = reshape(img.getdata(), (height, width))
    # Proceed with the convolution to extract edge magnitues.
    hm = convolve2d(m, gx).tolist()
    vm = convolve2d(m, gy).tolist()
    # This boolean matrix will describe edge direction for each pixel. True
    # means a vertical edge, and False a horizontal edge.
    directions = [False] * pixel_nb
    # This boolean matrix describe which pixels are considered as edge (True
    # if it's the case, false otherwise). At the beginning, we consider that
    # ALL pixels are potential edges.
    edges = [True] * pixel_nb
    # Variable representing a linarized version of polar coordinates.
    index = 0

    # We first define the edge direction for every pixel in the image.
    for y in xrange(0, height):
      for x in xrange(0, width):
        index = y * width + x
        # The greather (vertical or horizontal) edge magnitude defines the
        # edge direction.
        if(hm[y][x] < vm[y][x]):
            directions[index] = True
        continue

    # Filter the edges.
    for index in xrange(0, pixel_nb):
        _filter_edges(hm, vm, directions, edges, index, width, height)

    # Width of partitionned columns.
    cell_w = width / N

    # Height of partitionned lines.
    cell_h = height / M

    # Contains the sum of the vertical edge magnitudes from the partitionned
    # image.
    vert_em = []
    # For every cell of the partitionned image:
    for m in range(0, M):
        # Temporary variable. Used to build each line of vert_em.
        em_entry = []
        for n in range(0, N):
            # Compute the sum of the edge magnitudes.
            total_em = 0
            for y in xrange(m * cell_h, m * cell_h + cell_h):
                for x in xrange(n * cell_w, n * cell_w + cell_w):
                    index = y * width + x
                    if(directions[index] and edges[index]):
                        total_em += vm[y][x]
            # Append the normalized sum to the result.
            em_entry.append((1.0/(cell_w *  cell_h)) * total_em)
        vert_em.append(em_entry)
    
    # Contains the sum of the horizontal edge magnitudes from the partitionned
    # image.
    hor_em = []
    # For every cell of the partitionned image:
    for m in range(0, M):
        # Temporary variable. Used to build each line of hor_em.
        em_entry = []
        for n in range(0, N):
            # Compute the sum of the edge magnitudes.
            total_em = 0
            for y in xrange(m * cell_h, m * cell_h + cell_h):                
                for x in xrange(n * cell_w, n * cell_w + cell_w):
                    index = y * width + x
                    if (not directions[index]) and edges[index]:
                        total_em += hm[y][x]
            # Append the normalized sum to the result.
            em_entry.append((1.0/(cell_w * cell_h)) * total_em)
        hor_em.append(em_entry)

    # The feature vector of the image.
    F = []
    # The two global feature (the sum of all edge magnitudes).
    vert_gm = 0
    hor_gm = 0
    for m in range(0, M):    
        for n in range(0, N):
            hm = hor_em[m][n]
            vm = vert_em[m][n]
            vert_gm += vm
            hor_gm += hm
            F.append(hm)
            F.append(vm)
    factor = 1.0/(M*N)
    # Normalize the global features and add them to the vector.
    F.append(hor_gm * factor)
    F.append(vert_gm * factor)
    # Return the feature vector.
    return F

def get_diff_score(f1, f2):
    """
    Return the difference score between two features vectors. We obtain it
    simply by computing the norm I{L2} of their differences.

    @type f1: C{list} of C{float}
    @param f1: Features vector of the first image.
    @type f2: C{list} of C{float}
    @param f2: Features vector of the second image.
    
    @rtype: C{float}
    @return: The difference score between the two features vector.
    """
    diff = 0
    for j in range(0, len(f1)):
        diff += (f1[j]-f2[j])**2
    return diff
