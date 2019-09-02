import numpy as np
from rectpack import float2dec


class PackingBox(object):
    def __init__(self, triangle, x_min, x_max, y_min, y_max):
        self.triangle = triangle
        self.bottom_left = np.array([x_min, y_min])
        self.width = x_max - x_min
        self.height = y_max - y_min
        self._points = ((x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max))

    @property
    def rect(self):
        return float2dec(self.width, 2), float2dec(self.height, 2)

    @property
    def points(self):
        return self._points
