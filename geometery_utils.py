import numpy as np


def midpoint(a, b):
    return (a + b)/2


def length(a, b):
    return np.linalg.norm(a - b)


def normal(a, b):
    v = (b - a)
    return normalized(np.array([v[1], -v[0]]))


def normalized(v):
    return v/np.linalg.norm(v)
