from geometery_utils import *


class Polygon(object):
    def __init__(self, face_normal, edges):
        self.edges = edges
        self.adj_unit_norms = []

        self.unit_norm = face_normal / np.linalg.norm(face_normal)
        # Use the vector defined by the largest edge as the x axis to maximize packing efficiency
        # (long flat rectangles seem to pack easier)
        best_edge = sorted(edges, key=lambda e: -e.length)[0]
        self.x_prime = unit_vector_from_points(best_edge.point_b, best_edge.point_a)
        self.y_prime = np.cross(self.unit_norm, self.x_prime)

        basis_matrix = np.row_stack((self.x_prime, self.y_prime, self.unit_norm))
        self.flatten_matrix = np.linalg.solve(np.identity(3), basis_matrix)

    def __str__(self):
        return "_".join([str(e.index) for e in self.edges] +
                        [str(int(e.length)) for e in self.edges] +
                        ['m' if e.male else 'f' for e in self.edges])

    @property
    def points(self):
        return [e.point_a for e in self.edges]

    def flatten_point(self, point):
        ret = self.flatten_matrix.dot(point)
        return ret


class Edge:
    open = 0
    male = 1
    female = 2

    @staticmethod
    def opposite_type(type):
        assert type != Edge.open
        if type == Edge.male:
            return Edge.female
        return Edge.male

    def __init__(self, point_a, point_b, angle_a, angle_b):
        self.points = [point_a, point_b]
        self.angles = [angle_a, angle_b]
        self._angle = None
        self.index = None
        self._adj_face_normal = None
        self._edge_type = Edge.open
        self._edge_mate = None

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.point_a == other.point_a and self.point_b == other.point_b:
            return True
        if self.point_a == other.point_b and self.point_b == other.point_a:
            return True

    def __str__(self):
        return 'Edge({0}, {1})'.format(tuple(self.point_a), tuple(self.point_b))

    def indexable(self):
        # Convert to a frozenset of tuples for dictionary indexing
        return frozenset((tuple(self.point_a), tuple(self.point_b)))

    def set_type(self, edge_type):
        self._edge_type = edge_type

    def set_edge_angle(self, edge_angle):
        self._angle = edge_angle

    def set_edge_mate(self, edge_mate):
        self._edge_mate = edge_mate

    def set_angle_a(self, angle):
        self.angles[0] = angle

    def set_angle_b(self, angle):
        self.angles[1] = angle


    @property
    def angle_b(self):
        return self.angles[1]

    @property
    def get_edge_angle(self):
        return self._angle

    @property
    def get_edge_mate(self):
        return self._edge_mate

    @property
    def is_open(self):
        return self._edge_type == Edge.open

    @property
    def is_concave(self):
        return not self.is_open and self._angle > np.pi

    @property
    def is_male(self):
        return self._edge_type == Edge.male

    @property
    def is_female(self):
        return self._edge_type == Edge.female

    @property
    def point_a(self):
        return self.points[0]

    @property
    def point_b(self):
        return self.points[1]

    @property
    def angle_a(self):
        return self.angles[0]

    @property
    def angle_b(self):
        return self.angles[1]

    @property
    def length(self):
        return np.linalg.norm(self.point_a - self.point_b)
