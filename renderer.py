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


CUT_THICK = Color(0, 0, 255, "CUT_THICK")
CUT_THIN = Color(255, 0, 0, "CUT_THIN")
ENGRAVE_THICK = Color(0, 128, 0, "ENGRAVE_THICK")
ENGRAVE_THIN = Color(255, 165, 0, "ENGRAVE_THIN")
FRAME = Color(128, 128, 128, "FRAME")
DEBUG = Color(0, 0, 0, "DEBUG")


class _MatPlotLibRenderer:
    def __init__(self, panels=True, axis_range=None):
        plt.axes().set_aspect('equal')
        self._ax = plt.subplot(111)
        self._colors = set()
        self._axis_range = axis_range
        if axis_range is not None:
            self._ax.set_xlim(left=0, right=axis_range[0])
            self._ax.set_ylim(bottom=0, top=axis_range[1])
        self._render_panels = panels

    @staticmethod
    def _convert_color(color):
        return color.r / 255.0, color.g / 255.0, color.b / 255.0

    def add_line(self, a, b, color=CUT_THICK, tab=0.0):
        if tab > 0:
            mid = midpoint(a, b)
            # leave a gap in the center
            self.add_line(a, mid - tab/2.0*normalized(mid - a), color=color)
            return self.add_line(mid + tab/2.0*normalized(mid - a), b, color=color)
        self._colors.add(color)
        self._ax.plot([a[0], b[0]], [a[1], b[1]], color=self._convert_color(color))

    def add_circle(self, a, d, color=CUT_THICK):
        self._colors.add(color)
        self._ax.add_patch(patches.Circle(a, d/2.0, color=self._convert_color(color)))

    def add_text(self, a, v, text, max_w, max_h, color=ENGRAVE_THICK, h_center=False, v_center=False):
        self._colors.add(color)
        text_path = TextPath([0, 0], text, font_properties=FontProperties(fname=Config.font_file))
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

    def add_polygon(self, polygon, translation=np.array([0, 0])):
        def _get_adjusted_points(polygon):
            points_2d = [polygon.flatten_point(p)[0:2] for p in polygon.points]
            offsets = [find_joint_offset(Config.mat_thickness, e.get_edge_angle)
                       if not e.is_open else 0.0
                       for e in polygon.edges]
            return offset_polygon_2d(points_2d, offsets)
        adjusted_points = _get_adjusted_points(polygon)

        def render_cutout():
            cutout = [p + translation for p in
                      offset_polygon_2d(adjusted_points,
                                        len(adjusted_points)*[Config.joint_depth + Config.min_thickness])]
            if not cutout:
                print("Shape too small for cutout!")
            for line in adjacent_nlets(cutout, 2):
                self.add_line(line[0], line[1])

        def render_holes():
            cutout = [p + translation for p in
                      offset_polygon_2d(adjusted_points,
                                        len(adjusted_points)*[(Config.joint_depth + Config.min_thickness)/2.0])]
            for point in cutout:
                self.add_circle(point, Config.nail_hole_diameter)
                self.add_circle(point, Config.nail_hole_diameter + .4, color=CUT_THIN)

        render_cutout()
        render_holes()

        for i, edge in enumerate(polygon.edges):
            # convert to 2D coordinate space
            a_orig = polygon.flatten_point(edge.point_a)[0:2] + translation
            b_orig = polygon.flatten_point(edge.point_b)[0:2] + translation
            # we need to offset edges at convex joints to account for material thickness
            a = adjusted_points[i] + translation
            b = adjusted_points[(i + 1) % len(adjusted_points)] + translation
            mid = midpoint(a, b)
            width = distance(a, b)

            cs = CoordinateSystem2D(normalized(b - a), normal(b, a))
            mirrored = lambda p: cs.mirror_x(p, mid)

            def render_joint(joint_point):
                # reduce angles from 0 - 360 to 0 - 180 for simplicity
                joint_angle = edge.get_edge_angle if not edge.is_concave else 2 * np.pi - edge.get_edge_angle
                joint_width = Config.mat_thickness + 2*Config.t
                joint_depth = Config.joint_depth + 2*Config.t

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
                self.add_text(p5, p2 - p5, str(edge.index), distance(p2, p5) - Config.text_offset, joint_width,
                              v_center=True)
                p7 = p6 + cs.left(joint_width)
                self.add_line(p6, p7, tab=Config.attachment_tab)
                return p6

            def get_joint_bias():
                def bias(theta):
                    # place joint nearer to obtuse angles, further from acute ones
                    return 1 - min(theta / np.pi, 1)
                mate = edge.get_edge_mate
                # invert the ratios for the angles on the right relative to this edge
                bias_from_left = np.average([bias(edge.angle_a), 1 - bias(edge.angle_b),
                                             1 - bias(mate.angle_a), bias(mate.angle_b)])
                return bias_from_left

            def render_edge():
                notch_width = Config.mat_thickness - 2*Config.t
                # joint center needs to be positioned respective to the original side otherwise
                # mating joins will not line up properly depending on their respective offsets
                # pick the joint point biased towards the centers of the offset polygon edges
                biased_point = a_orig + cs.right(distance(a_orig, b_orig) * get_joint_bias())
                joint_center = nearest_point_on_line(a, b, biased_point)
                if distance(a, joint_center) + notch_width / 2.0 > distance(a, b):
                    print('Joint is falling off the end of the edge.')
                p1 = a
                p2 = joint_center + cs.left(notch_width / 2.0)
                self.add_line(p1, p2, tab=Config.attachment_tab)
                p3 = p2 + cs.up(Config.joint_depth)
                self.add_line(p2, p3)
                p4 = p3 + cs.right(notch_width)
                self.add_line(p3, p4)
                p5 = p4 + cs.down(Config.joint_depth)
                self.add_line(p4, p5)

                p6 = render_joint(p5) if edge.is_male else p5
                p7 = b
                self.add_line(p6, p7)

            def render_text():
                text_point = mid + cs.right(Config.mat_thickness / 2.0 + Config.text_offset) + \
                             cs.up(Config.text_offset)
                self.add_text(text_point, b - a,
                              str(edge.index) + ('c' if edge.is_concave else ''),
                              distance(b, text_point) - Config.text_offset, Config.text_height - 2*Config.text_offset)

            def render_panel_edge():
                self.add_line(a_orig, b_orig, color=CUT_THIN, tab=2*Config.attachment_tab)

            def render_panel_guide():
                self.add_line(a + cs.left(1), a + cs.right(1), color=ENGRAVE_THIN)
                self.add_line(b + cs.left(1), b + cs.right(1), color=ENGRAVE_THIN)

            def render_panel_text():
                text_point = midpoint(a_orig, b_orig) + cs.up(Config.text_offset)
                self.add_text(text_point, b_orig - a_orig,
                              str(edge.index),
                              distance(b, text_point) - Config.text_offset, Config.text_height, ENGRAVE_THIN,
                              h_center=True)

            if self._render_panels:
                # render panel edge whether or not the edge is open
                render_panel_edge()
                render_panel_guide()
            if edge.is_open:
                # Don't add anything to an open edge
                self.add_line(a, b)
            else:
                render_edge()
                render_text()
                if self._render_panels:
                    render_panel_text()

                if width < Config.min_edge_width:
                    print('side with length {0} is shorter than minimum length {1}'.format(
                        width, Config.min_edge_width))


class DXFRenderer(_MatPlotLibRenderer):
    def __init__(self, panels=True, axis_range=None):
        _MatPlotLibRenderer.__init__(self, panels=panels, axis_range=axis_range)
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
    def __init__(self, panels=True, ):
        _MatPlotLibRenderer.__init__(self, panels=panels)
        self._ax = None
        # garbage comparable minimum and maximum values
        self._x_min = sys.float_info.max
        self._x_max = sys.float_info.min
        self._y_min = sys.float_info.max
        self._y_max = sys.float_info.min
        self._polygon = None

    def add_polygon(self, polygon, translation=None):
        _MatPlotLibRenderer.add_polygon(self, polygon)
        assert self._polygon is None, 'PackingBoxRenderer should only ever be called with one polygon.'
        self._polygon = polygon

    def add_line(self, a, b, color=CUT_THICK, tab=0.0):
        for x in (a[0], b[0]):
            self._x_min = min(self._x_min, x)
            self._x_max = max(self._x_max, x)
        for y in (a[1], b[1]):
            self._y_min = min(self._y_min, y)
            self._y_max = max(self._y_max, y)

    def add_text(self, a, v, text, max_w, max_h, color=ENGRAVE_THICK, h_center=True, v_center=True):
        pass

    def add_circle(self, a, r, color=CUT_THICK):
        pass

    def update(self):
        pass

    def finish(self, name):
        return PackingBox(self._polygon,
                          self._x_min - Config.padding,
                          self._x_max + Config.padding,
                          self._y_min - Config.padding,
                          self._y_max + Config.padding)
