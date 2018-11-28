import numpy as np
from geometery_utils import *
from renderer import PERFORATED, DEBUG


class Triangle(object):
    def __init__(self, face_normal, edge_a, edge_b, edge_c):
        self.edges = [edge_a, edge_b, edge_c]

        self.unit_norm = face_normal / np.linalg.norm(face_normal)
        self.x_prime = (edge_a.point_b - edge_a.point_a)/np.linalg.norm(edge_a.point_b - edge_a.point_a)
        self.y_prime = np.cross(self.unit_norm, self.x_prime)

        basis_matrix = np.row_stack((self.x_prime, self.y_prime, self.unit_norm))
        self.transformation_matrix = np.linalg.solve(np.identity(3), basis_matrix)

        self._height = 6
        self._offset = 2

        self._cut = 5
        self._cut_offset = 1.5

        self._tab_snap = .5
        self._tab_t = .2
        self._tab_height = self._height - 2 * self._cut_offset

        self._text_width = 4.5
        self._text_offset = .5

        self._min_width = 2 * (self._cut + self._cut_offset) + self._text_width
        self._min_edge = 2 * self._offset + self._min_width

    def __str__(self):
        return "_".join([str(e.index) for e in self.edges] +
                        [str(int(e.length)) for e in self.edges])

    @property
    def points(self):
        # flatten and dedupe
        return [e.point_b for e in self.edges]

    @property
    def center_point(self):
        return sum(self.points)/3

    def transform(self, point):
        ret = self.transformation_matrix.dot(point)
        return ret

    def render(self, name, renderer):
        r = renderer(name)
        for edge in self.edges:
            # convert to 2D coordinate space
            a, b = self.transform(edge.point_a)[0:2], self.transform(edge.point_b)[0:2]
            right = normalized(b - a)
            down = normal(a, b)
            l = length(a, b)

            # add rectangular outline for tabs
            p1, p2 = a, a + self._offset*right
            r.add_line(p1, p2)
            p3 = p2 + self._height*down
            r.add_line(p2, p3)
            p4 = p3 + (l - 2*self._offset)*right
            r.add_line(p3, p4)
            p5 = p4 - self._height*down
            r.add_line(p4, p5)
            r.add_line(p2, p5, color=PERFORATED)
            p6 = p5 + self._offset*right
            r.add_line(p5, p6)

            # add the tabs and cuts
            def build_tab_or_cut(c1):
                c2 = c1 + self._cut*right
                if edge.male:
                    r.add_line(c1, c2, color=PERFORATED)
                    # add tab on male piece
                    c3 = c2 + self._tab_snap * right + self._tab_t * down
                    r.add_line(c2, c3)
                    c4 = c2 - self._tab_snap * right + self._tab_height * down
                    r.add_line(c3, c4)
                    c5 = c4 - (self._cut - 2 * self._tab_snap) * right
                    r.add_line(c4, c5)
                    c6 = c5 - 2*self._tab_snap*right - (self._tab_height - self._tab_t)*down
                    r.add_line(c5, c6)
                    r.add_line(c6, c1)
                else:
                    r.add_line(c1, c2)
            left_cut = a + (self._offset + self._cut_offset)*right + self._cut_offset*down
            build_tab_or_cut(left_cut)
            right_cut = b - (self._offset + self._cut_offset + self._cut)*right + self._cut_offset*down
            build_tab_or_cut(right_cut)

            # add the text label
            bottom_left = a + (self._offset + self._cut_offset + self._cut)*right + \
                (self._height - self._text_offset)*down
            r.add_text(bottom_left, right, str(edge.index))
        r.render()


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
