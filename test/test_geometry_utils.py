import unittest
import numpy as np

from geometery_utils import *


class TestGeometryUtils(unittest.TestCase):

    def test_merge(self):
        tri_a = [npa(0, 0), npa(1, 0), npa(1, 1)]
        tri_b = [npa(0, 1), npa(0, 0), npa(1, 1)]
        rect_a = [npa(0, 0), npa(1, 0), npa(1, 1), npa(0, 1)]
        self.assert_shape_equals(merge(tri_a, tri_b), rect_a)

    def assert_shape_equals(self, actual, expected):
        actual, expected = indexable(actual), indexable(expected)

        def fail_suffix():
            return "expected: {0}\nactual: {1}".format(
                indexable(expected),
                indexable(actual),
            )
        assert len(expected) == len(actual), "Expected length {0} != expected length {1}.\n{2}".format(
            len(expected), len(actual), fail_suffix()
        )
        for i in range(len(expected)):
            if expected[i] == actual[0]:
                expected = expected[i:] + expected[:i]
                self.assertTupleEqual(expected, actual)


def indexable(a):
    try:
        return tuple(indexable(v) for v in a)
    except TypeError:
        return a


def npa(*elems):
    return np.array(elems)