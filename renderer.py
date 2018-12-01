from matplotlib import transforms
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib import patches
from config import Config
import sys

from geometery_utils import *
from packing_box import PackingBox


class Color:
    def __init__(self, r, g, b, description):
        self.description = description
        self.r, self.g, self.b = r, g, b

    def __hash__(self):
        return hash((self.r, self.g, self.b, self.description))


CUT = Color(255, 0, 255, "CUT")
PERFORATED = Color(0, 255, 255, "PERFORATE")
ENGRAVE = Color(255, 255, 0, "ENGRAVE")
FRAME = Color(128, 128, 128, "FRAME")
DEBUG = Color(0, 0, 0, "DEBUG")


class _MatPlotLibRenderer:
    def __init__(self, axis_range=None):
        plt.axes().set_aspect('equal')
        self._ax = plt.subplot(111)
        self._colors = set()
        self._axis_range = axis_range
        if axis_range is not None:
            self._ax.set_xlim(left=0, right=axis_range[0])
            self._ax.set_ylim(bottom=0, top=axis_range[1])

    @staticmethod
    def _convert_color(color):
        return color.r / 255.0, color.g / 255.0, color.b / 255.0

    def add_line(self, a, b, color=CUT):
        self._colors.add(color)
        self._ax.plot([a[0], b[0]], [a[1], b[1]], color=self._convert_color(color))

    def add_text(self, a, v, text, max_w, max_h, color=ENGRAVE):
        self._colors.add(color)
        text_path = TextPath([0, 0], text)
        bb = text_path.get_extents()
        # center text on origin
        text_path = text_path.transformed(
            transforms.Affine2D().translate(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2)
        )
        x_scale = max_w / (bb.xmax - bb.xmin)
        y_scale = max_h / (bb.ymax - bb.ymin)
        text_path = text_path.transformed(
            transforms.Affine2D()
                # align text with the respective side
                .rotate(angle(v))
                # make text as large as will fit in x and y bounds
                .scale(min(x_scale, y_scale))
                # move the center of the bounding box to a
                .translate(a[0], a[1])
        )
        self._ax.add_patch(patches.PathPatch(text_path, facecolor='none', edgecolor=self._convert_color(color)))

    def add_triangle(self, triangle, translation=np.array([0, 0])):
        for edge in triangle.edges:
            # convert to 2D coordinate space
            a = triangle.flatten_point(edge.point_a)[0:2] + translation
            b = triangle.flatten_point(edge.point_b)[0:2] + translation
            mid = midpoint(a, b)
            w = distance(a, b)

            cs = CoordinateSystem2D(normalized(b - a), normal(b, a))
            up, down, left, right, mirrored = cs.up, cs.down, cs.left, cs.right, lambda p: cs.mirror_x(p, mid)

            if w < Config.min_edge_width:
                print 'side with length {0} is shorter than minimum length {1}'.format(
                    w, Config.min_edge_width)

            def add_snap(snap_point):

                def tab_mirror(p):
                    return cs.mirror_x(p, snap_point)
                if edge.male:
                    t1 = snap_point + left(Config.cut / 2.0)
                    self.add_line(snap_point, t1, color=PERFORATED)
                    self.add_line(mirrored(snap_point), mirrored(t1), color=PERFORATED)
                    t2 = t1 + down(2 * Config.t + Config.mat_thickness)
                    self.add_line(t1, t2)
                    self.add_line(tab_mirror(t1), tab_mirror(t2))
                    t3 = t2 + left(Config.tab_snap)
                    self.add_line(t2, t3)
                    self.add_line(tab_mirror(t2), tab_mirror(t3))
                    t4 = t3 + down(Config.tab_height - Config.mat_thickness - 2 * Config.t) + \
                         right(2 * Config.tab_snap)
                    self.add_line(t3, t4)
                    self.add_line(tab_mirror(t3), tab_mirror(t4))
                else:
                    w = Config.cut + 2 * Config.t
                    h = Config.mat_thickness + 2 * Config.t
                    t1 = snap_point + left(w / 2.0) + up(h / 2.0)
                    t2 = t1 + down(h)
                    self.add_line(t1, t2)
                    t3 = t2 + right(w)
                    self.add_line(t2, t3)
                    t4 = t3 + up(h)
                    self.add_line(t3, t4)
                    self.add_line(t4, t1)

            third = distance(a, b)/3
            if third > 2 * Config.cut + 3 * Config.cut_offset:
                offset = third
                snap_point = offset + right(Config.cut_offset + Config.cut / 2.0) + \
                    down(Config.cut_offset - Config.mat_thickness)
                add_snap(snap_point)
                add_snap(mirrored(snap_point))
            else:
                offset = Config.min_offset
                snap_point = mid + down(Config.cut_offset - Config.mat_thickness)
                add_snap(snap_point)

            p1 = a + right(offset)
            self.add_line(a, p1)
            self.add_line(mirrored(a), mirrored(p1))
            # shift up by material thickness to make triangles flush
            p1_a = p1 + cs.up(Config.mat_thickness)
            self.add_line(p1_a, mirrored(p1_a), color=PERFORATED)
            p2 = p1_a + cs.down(Config.height)
            self.add_line(p1_a, p2)
            self.add_line(mirrored(p1_a), mirrored(p2))
            p3 = p2 + right(w / 2.0 - offset)
            self.add_line(p2, p3)
            self.add_line(mirrored(p2), mirrored(p3))

            # add the text label
            center = midpoint(a, b) + cs.down(Config.height / 2.0)
            max_text_width = distance(p1_a, mirrored(p1_a))
            self.add_text(center, b - a, str(edge.index), max_text_width, Config.text_height)


class DXFRenderer(_MatPlotLibRenderer):
    def __init__(self, axis_range=None):
        _MatPlotLibRenderer.__init__(self, axis_range)
        plt.axis('off')
        plt.margins(0, 0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

    def update(self):
        pass

    def finish(self, name):
        if self._axis_range is not None:
            x_bound = map(mm_to_inch, self._ax.get_xbound())
            y_bound = map(mm_to_inch, self._ax.get_ybound())
            plt.gcf().set_size_inches(x_bound[1] - x_bound[0], y_bound[1] - y_bound[0])
        plt.gcf().savefig('{0}.svg'.format(name, format='svg'), bbox_inches=0, pad_inches=0, transparent=True)
        plt.clf()


class DebugRenderer(_MatPlotLibRenderer):
    def __init__(self, axis_range=None):
        _MatPlotLibRenderer.__init__(self, axis_range)

    def update(self):
        colors, descriptions = zip(*[(c, c.description) for c in self._colors])
        self._ax.legend(
            [Line2D([0], [0], color=self._convert_color(c), lw=4) for c in colors],
            descriptions
        )
        plt.pause(.1)

    def finish(self, name):
        plt.show()
        plt.clf()


class PackingBoxRenderer(_MatPlotLibRenderer):
    def __init__(self):
        _MatPlotLibRenderer.__init__(self)
        self._ax = None
        # garbage comparable minimum and maximum values
        self._x_min = sys.float_info.max
        self._x_max = sys.float_info.min
        self._y_min = sys.float_info.max
        self._y_max = sys.float_info.min
        self._triangle = None

    def add_triangle(self, triangle, translation=None):
        _MatPlotLibRenderer.add_triangle(self, triangle)
        assert self._triangle is None, 'PackingBoxRenderer should only ever be called with one triangle.'
        self._triangle = triangle

    def add_line(self, a, b, color=CUT):
        for x in (a[0], b[0]):
            self._x_min = min(self._x_min, x)
            self._x_max = max(self._x_max, x)
        for y in (a[1], b[1]):
            self._y_min = min(self._y_min, y)
            self._y_max = max(self._y_max, y)

    def add_text(self, a, v, text, max_w, max_h, color=ENGRAVE):
        pass

    def update(self):
        pass

    def finish(self, name):
        return PackingBox(self._triangle,
                          self._x_min - Config.padding,
                          self._x_max + Config.padding,
                          self._y_min - Config.padding,
                          self._y_max + Config.padding)
