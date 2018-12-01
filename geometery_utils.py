import numpy as np


class CoordinateSystem2D(object):
    def __init__(self, x_vector, y_vector):
        self._x_vector = x_vector
        self._y_vector = y_vector

    def up(self, delta):
        return self._y_vector*delta

    def down(self, delta):
        return -self._y_vector*delta

    def left(self, delta):
        return -self._x_vector*delta

    def right(self, delta):
        return self._x_vector*delta

    def mirror_x(self, a, mirror_point):
        return a + self.right(2 * np.dot(mirror_point - a, self._x_vector))

def midpoint(a, b):
    return (a + b) / 2.0


def distance(a, b):
    return np.linalg.norm(a - b)


def normal(a, b):
    v = (b - a)
    return normalized(np.array([v[1], -v[0]]))


def normalized(v):
    return v/np.linalg.norm(v)


def angle(v):
    return np.arctan2(v[1], v[0])


def mm_to_inch(mm):
    return 0.0393701*mm
