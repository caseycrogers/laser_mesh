from geometery_utils import *

class Triangle(object):
    def __init__(self, face_normal, edge_a, edge_b, edge_c):
        self.edges = [edge_a, edge_b, edge_c]

        self.unit_norm = face_normal / np.linalg.norm(face_normal)
        self.x_prime = (edge_a.point_b - edge_a.point_a) / np.linalg.norm(edge_a.point_b - edge_a.point_a)
        self.y_prime = np.cross(self.unit_norm, self.x_prime)

        basis_matrix = np.row_stack((self.x_prime, self.y_prime, self.unit_norm))
        self.flatten_matrix = np.linalg.solve(np.identity(3), basis_matrix)

    def __str__(self):
        return "_".join([str(e.index) for e in self.edges] +
                        [str(int(e.length)) for e in self.edges] +
                        ['m' if e.male else 'f' for e in self.edges])

    @property
    def points(self):
        # flatten and dedupe
        return [e.point_b for e in self.edges]

    def flatten_point(self, point):
        ret = self.flatten_matrix.dot(point)
        return ret


class Edge:
    def __init__(self, point_a, point_b):
        self.points = [point_a, point_b]
        self.index = None
        self.male = True

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.point_a == other.point_a and self.point_b == other.point_b:
            return True
        if self.point_a == other.point_b and self.point_b == other.point_a:
            return True

    def indexable(self):
        # convert to a frozenset of tuples for dictionary indexing
        return frozenset((tuple(self.point_a), tuple(self.point_b)))

    @property
    def point_a(self):
        return self.points[0]

    @property
    def point_b(self):
        return self.points[1]

    @property
    def length(self):
        return np.linalg.norm(self.point_a - self.point_b)
