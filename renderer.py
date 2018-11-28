import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class Color:
    def __init__(self, r, g, b, description):
        self.description = description
        self.r, self.g, self.b = r, g, b

    def __hash__(self):
        return hash((self.r, self.g, self.b, self.description))


CUT = Color(255, 0, 255, "CUT")
PERFORATED = Color(0, 255, 255, "PERFORATE")
DEBUG = Color(0, 0, 0, "DEBUG")


class _MatPlotLibRenderer:
    def __init__(self, name):
        plt.axes().set_aspect('equal')
        self.ax = plt.subplot(111)
        self.colors = set()
        self.name = name

    @staticmethod
    def _convert_color(color):
        return color.r / 255.0, color.g / 255.0, color.b / 255.0

    def add_line(self, a, b, color=CUT):
        self.colors.add(color)
        self.ax.plot([a[0], b[0]], [a[1], b[1]], color=self._convert_color(color))

    def add_text(self, a, v, text, color=CUT):
        self.colors.add(color)
        self.ax.text(a[0], a[1], text, {'va': 'center', 'ha': 'center'})


class DXFRenderer(_MatPlotLibRenderer):
    def __init__(self, name):
        _MatPlotLibRenderer.__init__(self, name)

    def render(self):
        plt.axis('off')
        plt.savefig('{0}.svg'.format(self.name))
        plt.clf()


class DebugRenderer(_MatPlotLibRenderer):
    def __init__(self, name):
        _MatPlotLibRenderer.__init__(self, name)

    def render(self):
        colors, descriptions = zip(*[(c, c.description) for c in self.colors])
        self.ax.legend(
            [Line2D([0], [0], color=self._convert_color(c), lw=4) for c in colors],
            descriptions
        )
        plt.show()
