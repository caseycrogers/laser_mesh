import numpy as np
from rectpack import float2dec


class PackingBox(object):
    def __init__(self, x_min, x_max, y_min, y_max):
        self.bottom_left = np.array([x_min, y_min])
        self.bottom_right = np.array([x_max, y_min])
        self.top_left = np.array([x_min, y_max])
        self.top_right = np.array([x_min, y_max])
        self.width = x_max - x_min
        self.height = y_max - y_min
        self._points = ((x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max))

    @property
    def rect(self):
        return float2dec(self.width, 2), float2dec(self.height, 2)

    @property
    def points(self):
        return self._points
