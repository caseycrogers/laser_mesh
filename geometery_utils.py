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

    def rotated_copy(self, theta):
        return CoordinateSystem2D(rotate_around_origin_2d(self._x_vector, theta),
                                  rotate_around_origin_2d(self._y_vector, theta))


def midpoint(a, b):
    return (a + b) / 2.0


def distance(a, b):
    return np.linalg.norm(a - b)


def normal(a, b):
    v = (b - a)
    return normalized(np.array([v[1], -v[0]]))


def normalized(v):
    return v/np.linalg.norm(v)


def vector_angle_2d(v):
    return np.arctan2(v[1], v[0])


def rotate_around_origin_2d(v, theta):
    # no dammit stackoverflow I wanted CC rotation
    theta = -theta
    x, y = v
    return np.array([x * np.cos(theta) + y * np.sin(theta), -x * np.sin(theta) + y * np.cos(theta)])


# a and b are the non-shared points on the two respective faces
# v and u are the two faces respective unit normals
def angle_between_faces(a, b, v, u):
    angle = np.pi - np.arccos(np.clip(np.dot(v, u), -1.0, 1.0))
    if is_convex(a, b, v):
        return angle
    else:
        return 2*np.pi - angle


def is_convex(a, b, v):
    return np.dot(a - b, v) > 0


def point_equals(a, b):
    return tuple(a) == tuple(b)


def mm_to_inch(mm):
    return 0.0393701*mm
