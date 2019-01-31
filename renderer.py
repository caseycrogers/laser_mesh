from matplotlib import transforms
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import TextPath
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

    def add_text(self, a, v, text, max_w, max_h, color=ENGRAVE, h_center=False, v_center=False):
        self._colors.add(color)
        text_path = TextPath([0, 0], text)
        bb = text_path.get_extents()
        h_adjust, v_adjust = 0, 0
        if h_center:
            h_adjust = -(bb.xmin + bb.xmax) / 2
        if v_center:
            v_adjust = -(bb.ymin + bb.ymax) / 2
        text_path = text_path.transformed(
            transforms.Affine2D().translate(h_adjust, v_adjust)
        )
        x_scale = max_w / (bb.xmax - bb.xmin)
        y_scale = max_h / (bb.ymax - bb.ymin)
        text_path = text_path.transformed(
            transforms.Affine2D()
                # align text with the respective side
                .rotate(vector_angle_2d(v))
                # make text as large as will fit in x and y bounds
                .scale(min(x_scale, y_scale))
                # move the text to the text point
                .translate(a[0], a[1])
        )
        self._ax.add_patch(patches.PathPatch(text_path, facecolor='none', edgecolor=self._convert_color(color)))

    def add_triangle(self, triangle, translation=np.array([0, 0])):
        for edge in triangle.edges:
            # convert to 2D coordinate space
            a = triangle.flatten_point(edge.point_a)[0:2] + translation
            b = triangle.flatten_point(edge.point_b)[0:2] + translation
            mid = midpoint(a, b)
            width = distance(a, b)

            cs = CoordinateSystem2D(normalized(b - a), normal(b, a))
            mirrored = lambda p: cs.mirror_x(p, mid)

            def render_edge():
                p1 = a
                p2 = mid + cs.left(Config.mat_thickness / 2.0)
                self.add_line(p1, p2)
                p3 = p2 + cs.up(Config.mat_thickness / 2.0)
                self.add_line(p2, p3)
                p4 = p3 + cs.right(Config.mat_thickness)
                self.add_line(p3, p4)
                p5 = p4 + cs.down(Config.mat_thickness / 2.0)
                self.add_line(p4, p5)
                p6 = b
                self.add_line(p5, p6)

            def render_text():
                text_point = mid + cs.right(Config.mat_thickness / 2.0 + Config.text_offset) + \
                             cs.up(Config.text_offset)
                self.add_text(text_point, b - a,
                              str(edge.index) + ('c' if edge.is_concave else ''),
                              distance(b, text_point) - Config.mat_thickness, Config.text_height)

            def render_joint(joint_point):
                # reduce angles from 0 - 360 to 0 - 180 for simplicity
                joint_angle = edge.get_angle if not edge.is_concave else edge.get_angle - np.pi
                joint_width = Config.mat_thickness
                joint_depth = Config.mat_thickness / 2.0

                rot_cs = cs.rotated_copy(np.pi / 2.0 - joint_angle)
                long_edge = joint_depth + joint_width / np.tan(joint_angle / 2.0)

                p1 = joint_point
                p2 = p1 + cs.down(long_edge)
                self.add_line(p1, p2)

                p3 = p2 + rot_cs.right(long_edge)
                self.add_line(p2, p3)
                p4 = p3 + rot_cs.up(joint_width)
                self.add_line(p3, p4)
                p5 = p4 + rot_cs.left(joint_depth)
                self.add_line(p4, p5)

                p6 = p5 + cs.up(joint_depth)
                self.add_line(p5, p6)
                p7 = p1
                self.add_line(p6, p7)
                self.add_text(p5, p2 - p5, str(edge.index), distance(p2, p5) - Config.text_offset, Config.text_height,
                              v_center=True)

            if edge.is_open:
                # Don't add anything to an open edge
                self.add_line(a, b)
            else:
                if edge.is_male:
                    render_joint(midpoint(a, b) + cs.left(Config.mat_thickness / 2.0))
                render_edge()
                render_text()

                if width < Config.min_edge_width:
                    print 'side with length {0} is shorter than minimum length {1}'.format(
                        width, Config.min_edge_width)


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

    def add_line(self, a, b, color=CUT, left_tab=False, right_tab=False):
        for x in (a[0], b[0]):
            self._x_min = min(self._x_min, x)
            self._x_max = max(self._x_max, x)
        for y in (a[1], b[1]):
            self._y_min = min(self._y_min, y)
            self._y_max = max(self._y_max, y)

    def add_text(self, a, v, text, max_w, max_h, color=ENGRAVE, h_center=True, v_center=True):
        pass

    def update(self):
        pass

    def finish(self, name):
        return PackingBox(self._triangle,
                          self._x_min - Config.padding,
                          self._x_max + Config.padding,
                          self._y_min - Config.padding,
                          self._y_max + Config.padding)
