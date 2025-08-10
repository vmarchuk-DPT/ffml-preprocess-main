import math

##############################################################################
#
# Functions related to the geometry of paths, points, and line segments.
#
##############################################################################


# Rotate a point around a given point.
# pt and origin are tuples (x,y)
def rotatePoint(pt, origin, degrees):

    radians = degrees * math.pi / 180

    x, y = pt
    offset_x, offset_y = origin
    adjusted_x = x - offset_x
    adjusted_y = y - offset_y
    cos_rad = math.cos(radians)
    sin_rad = math.sin(radians)
    qx = offset_x + cos_rad * adjusted_x + sin_rad * adjusted_y
    qy = offset_y + -sin_rad * adjusted_x + cos_rad * adjusted_y

    return qx, qy


# A function to normalize the mouse path to
# the space 0,0:1,1. The starting point is
# set to 0,0, and the end point is 1,1.

# Expects raw path of form:
# 		[(time,x,y),(time,x,y)]

# There is an assumption that the first point
# in the sequence is the stimulus, and the
# last point is the chosen target. We ensure
# this by using the midpoints and response
# data to capture the start-end of the path.


# NB: It is possible for mouse coordinates to
# fall outside of the 0,0, 1,1 continuum, in
# so far as the capturing window encapsulates
# the choice set/stimulus.
def bipartiteNormPath(raw, midpoints, options, response, start, end):

    # Do not allow empty paths, or paths that have fewer
    # than two points (as can happen with touch screens).
    if not raw or len(raw) < 2:
        return []

    # Due to the API bug storing coordinates in different systems for
    # mouse path vs elements on screen, these checks cannot be performed.
    # start_point = (raw[0][1],raw[0][2])
    # end_point = (raw[-1][1],raw[-1][2])#midpoints[options[response]]

    # Normalize coordinates:
    # 	1. Standard Orientation
    # 	2. Norm to Axes
    # 	3. Scale to Bounding Box
    # 	4. All paths end at 1,1

    path = []

    # Right now, 0,0 is in the top-left corner of the screen.
    # We need to flip the coordinates around.
    plane = (raw[0][2] - raw[-1][2]) / 2 + raw[-1][2]

    time = None

    for i in raw:

        t = i[0]
        x = i[1]
        y = i[2]

        # Get the start time of tracking
        if not time:
            time = t

        # Normalize times to the start.
        t = t - time

        # Flip coordinate system around y-midpoint of first and last point
        dist = abs(y - plane)
        if y > plane:
            y = y - 2 * dist
        else:
            y = y + 2 * dist

        path.append([float(x), float(y), float(t)])

    norm = []

    # flip = True if (path[0][1] > path[-1][1]) else False

    # pivot_x = path[0][0]
    # pivot_y = (max(path[0][1],path[-1][1])
    # 		   - abs(path[0][1] - path[-1][1])/2)

    offset_x = path[0][0]
    offset_y = path[0][1]

    scale_x = abs(path[0][0] - path[-1][0])
    scale_y = abs(path[0][1] - path[-1][1])

    # Do not allow rendering of options
    # in a stacked manner or side-by-side.
    if scale_x == 0 or scale_y == 0:
        raise ValueError("Invalid layout detected: answers stacked.")

    for point in path:

        x = point[0]
        y = point[1]
        t = point[2]

        # Move to x = 0
        x = x - offset_x

        # Move to y = 0
        y = y - offset_y

        # Scale y to 0:1
        y = y / scale_y

        # Scale x to -1:1
        x = x / scale_x

        # if flip:
        # Ensure all paths start at the base and go up.
        # delta_x = x - pivot_x
        # x = pivot_x - delta_x
        # delta_y = y - pivot_y
        # y = pivot_y - delta_y

        if path[-1][0] < path[0][0]:
            # Ensure all paths end at the same target
            x = x * -1

        # Add the normalized point
        norm.append([x, y, t])

    norm_path = []
    for i in norm:
        norm_path.append((i[0], i[1]))
    # xy_chart2 = pygal.XY()
    # xy_chart2.title = "Mousepath"
    # xy_chart2.add("Norm", norm_path)
    # xy_chart2.render_to_png("norm.png")

    return norm


def tripartiteNormPath(raw, midpoints, options, response, start, end):

    # If there are three options, and the response is either
    # on the left or right, call bipartiteNormPath directly.
    # Otherwise, rotate the line by 45 degrees clockwise around
    # its first point, adjust the midpoints we send to account for
    # this rotation.
    if len(options) != 3:
        raise ValueError("Incorrect number of options for a tripartite question.")

    new_raw = []
    new_mid = []
    # Do we need to rotate?
    # 'option1' is assumed/guaranteed to be the middle option in tripartite.
    if options[response] == "option1":
        for i in raw:
            new_pt = rotatePoint((i[1], i[2]), (raw[0][1], raw[0][2]), 45)
            new_raw.append((i[0], new_pt[0], new_pt[1]))
        new_mid = midpoints
        new_mid["option1"] = (new_raw[-1][1], new_raw[-1][2])
    else:
        new_raw = raw
        new_mid = midpoints

    return bipartiteNormPath(new_raw, new_mid, options, response, start, end)


# A utility class to represent points in 2d space
class Point(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"

    def __repr__(self):
        return str(self)


# Calculate the shortest distance between a point and a line
# where the line is expressed as two points
def pointToLine(a, b, c):

    denominator = math.sqrt(pow(b.y - a.y, 2) + pow(b.x - a.x, 2))

    # Avoid division by 0 for vertical/horizontal lines.
    # Our lines should always be |slope| = 1
    if not denominator:
        return 0

    numerator = abs((b.y - a.y) * c.x - (b.x - a.x) * c.y + b.x * a.y - b.y * a.x)

    return numerator / denominator


# Calculate the distance between two points
def pointToPoint(a, b):

    # Euclidean distance between two points.
    return math.sqrt(pow(abs(a.x - b.x), 2) + pow(abs(a.y - b.y), 2))


# Given three colinear points p, q, r, the function checks if
# point q lies on line segment 'pr'
def onSegment(p, q, r):

    if (
        q.x <= max(p.x, r.x)
        and q.x >= min(p.x, r.x)
        and q.y <= max(p.y, r.y)
        and q.y >= min(p.y, r.y)
    ):
        return True

    return False


# To find orientation of ordered triplet (p, q, r).
# The function returns following values
# 0 --> p, q and r are colinear
# 1 --> Clockwise
# 2 --> Counterclockwise
def orientation(p, q, r):

    # See https://www.geeksforgeeks.org/orientation-3-ordered-points/
    # for details of below formula.
    val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)

    if val == 0:
        return 0  # colinear

    return 1 if (val > 0) else 2  # clock or counterclock wise


# The main function that returns true if line segment 'p1q1'
# and 'p2q2' intersect.
def doIntersect(p1, q1, p2, q2):

    # Find the four orientations needed for general and
    # special cases
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if o1 != o2 and o3 != o4:
        return True

    # Special Cases
    # p1, q1 and p2 are colinear and p2 lies on segment p1q1
    if o1 == 0 and onSegment(p1, p2, q1):
        return True

    # p1, q1 and q2 are colinear and q2 lies on segment p1q1
    if o2 == 0 and onSegment(p1, q2, q1):
        return True

    # p2, q2 and p1 are colinear and p1 lies on segment p2q2
    if o3 == 0 and onSegment(p2, p1, q2):
        return True

    # p2, q2 and q1 are colinear and q1 lies on segment p2q2
    if o4 == 0 and onSegment(p2, q1, q2):
        return True

    return False  # Doesn't fall in any of the above cases
