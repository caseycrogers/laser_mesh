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

FONT_PROPERTIES = FontProperties(family="Inconsolata-Regular", size=6)


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
        text_path = TextPath([0, 0], text, prop=FONT_PROPERTIES)
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
            right = normalized(b - a)
            down = normal(a, b)
            w = length(a, b)
            if w < Config.min_single_tab_width:
                print 'side with length {0} is shorter than minimum length {1}'.format(
                    w, Config.min_single_tab_width)
            # true if this edge is too short for two tabs
            single_tab = w < Config.min_double_tab_width

            # add rectangular outline for tabs
            p1, p2 = a, a + Config.offset * right
            self.add_line(p1, p2)
            p3 = p2 + Config.height * down
            self.add_line(p2, p3)
            p4 = p3 + (w - 2 * Config.offset) * right
            self.add_line(p3, p4)

            # add material thickness to make triangles flush
            p5 = p4 - (Config.height + Config.mat_thickness) * down
            self.add_line(p4, p5)
            p6 = p5 - (w - 2 * Config.offset) * right
            self.add_line(p5, p6, PERFORATED)
            self.add_line(p6, p2)
            p7 = p5 + Config.mat_thickness * down
            self.add_line(p7, b)

            # add the tabs and cuts
            def build_tab_or_cut(c1):
                if edge.male:
                    c2 = c1 + Config.cut * right
                    self.add_line(c1, c2, color=PERFORATED)

                    c3 = c2 + (2 * Config.t + Config.mat_thickness) * down
                    self.add_line(c2, c3)
                    c4 = c3 + Config.tab_snap * right
                    self.add_line(c3, c4)
                    c5 = c2 - Config.tab_snap * right + Config.tab_height * down
                    self.add_line(c4, c5)
                    c6 = c5 - (Config.cut - 2 * Config.tab_snap) * right
                    self.add_line(c5, c6)
                    c7 = c6 - 2 * Config.tab_snap * right - \
                         (Config.tab_height - 2 * Config.t - Config.mat_thickness) * down
                    self.add_line(c6, c7)
                    c8 = c7 + Config.tab_snap * right
                    self.add_line(c7, c8)
                    c9 = c8 - (2 * Config.t + Config.mat_thickness) * down
                    self.add_line(c8, c9)
                    self.add_line(c9, c1)
                else:
                    # widen cut by _t to ensure fit
                    cut_length = Config.cut + Config.t * 2
                    cut_width = Config.mat_thickness + Config.t * 2
                    c1 = c1 - Config.t * right - Config.t * down
                    c2 = c1 + cut_length * right
                    self.add_line(c1, c2)
                    c3 = c2 + cut_width * down
                    self.add_line(c3, c2)
                    c4 = c3 - cut_length * right
                    self.add_line(c3, c4)
                    self.add_line(c4, c1)

            if single_tab:
                center_cut = midpoint(a, b) - (Config.cut / 2.0) * right + Config.cut_offset * down
                build_tab_or_cut(center_cut)
            else:
                left_cut = a + (Config.offset + Config.cut_offset) * right + Config.cut_offset * down
                build_tab_or_cut(left_cut)
                right_cut = b - (Config.offset + Config.cut_offset + Config.cut) * right + Config.cut_offset * down
                build_tab_or_cut(right_cut)

            # add the text label
            center = midpoint(a, b) + Config.height / 2.0 * down
            max_text_width = w - 2 * Config.offset
            self.add_text(center, right, str(edge.index), max_text_width, Config.text_height)


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
        plt.gcf().savefig('{0}.svg'.format(name, format='svg'), bbox_inches='tight', pad_inches=0)
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
