import numpy as np

from itertools import chain

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


def offset_polygon_2d(points, offsets):
    adjusted = [np.copy(p) for p in points]
    for a_i, a, b_i, b, c_i, c, d_i, d in map(chain.from_iterable, adjacent_nlets(list(enumerate(points)), 4)):
        alpha = angle_between_three_points_2d(a, b, c)
        beta = angle_between_three_points_2d(b, c, d)
        adjusted[a_i] += offsets[a_i] * normalized(c - a) / np.sin(alpha)
        adjusted[b_i] += offsets[a_i] * normalized(c - b) / np.sin(beta)
    return adjusted


def adjacent_nlets(q, n):
    return zip(*[q[c:] + q[:c] for c in range(n)])


def merge_coplanar_faces(faces, face_normals):
    def indexable(a):
        try:
            return tuple(indexable(v) for v in a)
        except TypeError:
            return a

    def merge(a, b, shared):
        def rotated(f):
            i = max(map(indexable, a).index(shared[0]), map(indexable, b).index(shared[1]))
            return f[i:] + f[:i]
        # only strong IC's can read this
        c = rotated(a) + rotated(b)[1:-1]
        del a[:]
        a += c

    point_tup_to_face = {}
    point_tup_to_face_normal = {}
    merged_faces = []
    merged_normals = []
    for face, norm in zip(map(list, faces), face_normals):
        merged = False
        for e in adjacent_nlets(face, 2):
            point_set = frozenset(indexable(e))
            try:
                face_mate = point_tup_to_face[point_set]
                norm_mate = point_tup_to_face_normal[point_set]
                if np.dot(normalized(norm), normalized(norm_mate)) == 1.0:
                    merged = True
                    merge(face_mate, face, tuple(point_set))
            except KeyError:
                point_tup_to_face[point_set] = face
                point_tup_to_face_normal[point_set] = norm
        if not merged:
            merged_faces.append(face)
            merged_normals.append(norm)
    return merged_faces, merged_normals
