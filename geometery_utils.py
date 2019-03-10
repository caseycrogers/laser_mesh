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


def angle_between_three_points_2d(a, p0, p1):
    return angle_between_three_points(np.append(a, 0.0), np.append(p0, 0.0), np.append(p1, 0.0),
                                      np.array([0.0, 0.0, 1.0]))


def angle_between_three_points(a, p0, p1, n):
    return angle_between_vectors(p0 - a, p1 - a, n)


def angle_between_vectors(u, v, n):
    return np.arctan2(np.linalg.det(np.column_stack((u, v, n))), np.dot(u, v))


def rotate_around_origin_2d(v, theta):
    # no dammit stackoverflow I wanted CC rotation
    theta = -theta
    x, y = v
    return np.array([x * np.cos(theta) + y * np.sin(theta), -x * np.sin(theta) + y * np.cos(theta)])


def nearest_point_on_line(a, b, c):
    n = normalized(b - a)
    s = np.dot(c - a, n)
    return a + s * n


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


def unit_vector_from_points(a, b):
    return normalized(b - a)


def mm_to_inch(mm):
    return 0.0393701*mm


def find_joint_offset(t, theta):
    if theta >= np.pi:
        # Only convex joints need to be offset
        return 0
    return t / np.tan(theta / 2.0)


def offset_triangle_2d(points, edge_offsets):
    adjusted = [np.copy(p) for p in points]
    for i in range(len(points)):
        a_i, b_i, c_i = i, (i + 1) % len(points), (i + 2) % len(points)
        a, b, c = points[a_i], points[b_i], points[c_i]
        alpha = angle_between_three_points_2d(a, b, c)
        beta = angle_between_three_points_2d(b, c, a)
        adjusted[a_i] += edge_offsets[a_i] * normalized(c - a) / np.sin(alpha)
        adjusted[b_i] += edge_offsets[a_i] * normalized(c - b) / np.sin(beta)
    return adjusted


def adjacent_nlets(q, n):
    return zip(*[q[c:] + q[:c] for c in range(n)])
