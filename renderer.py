from matplotlib import transforms
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib import patches

from geometery_utils import *


class Color:
    def __init__(self, r, g, b, description):
        self.description = description
        self.r, self.g, self.b = r, g, b

    def __hash__(self):
        return hash((self.r, self.g, self.b, self.description))


CUT = Color(255, 0, 255, "CUT")
PERFORATED = Color(0, 255, 255, "PERFORATE")
DEBUG = Color(0, 0, 0, "DEBUG")
FONT_PROPERTIES = FontProperties(family="Inconsolata-Regular", size=6)


class _MatPlotLibRenderer:
    def __init__(self, name):
        plt.axes().set_aspect('equal')
        self._ax = plt.subplot(111)

        self.colors = set()
        self.name = name

    @staticmethod
    def _convert_color(color):
        return color.r / 255.0, color.g / 255.0, color.b / 255.0

    def add_line(self, a, b, color=CUT):
        self.colors.add(color)
        self._ax.plot([a[0], b[0]], [a[1], b[1]], color=self._convert_color(color))

    def add_text(self, a, v, text, max_w, max_h, color=CUT):
        self.colors.add(color)
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


class DXFRenderer(_MatPlotLibRenderer):
    def __init__(self, name):
        _MatPlotLibRenderer.__init__(self, name)

    def render(self):
        plt.axis('off')
        plt.margins(0, 0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

        x_bound = map(mm_to_inch, self._ax.get_xbound())
        y_bound = map(mm_to_inch, self._ax.get_ybound())
        plt.gcf().set_size_inches(x_bound[1] - x_bound[0], y_bound[1] - y_bound[0])
        plt.gcf().savefig('{0}.svg'.format(self.name, format='svg'), bbox_inches='tight', pad_inches=0)
        plt.clf()


class DebugRenderer(_MatPlotLibRenderer):
    def __init__(self, name):
        _MatPlotLibRenderer.__init__(self, name)

    def render(self):
        colors, descriptions = zip(*[(c, c.description) for c in self.colors])
        self._ax.legend(
            [Line2D([0], [0], color=self._convert_color(c), lw=4) for c in colors],
            descriptions
        )

        plt.show()
