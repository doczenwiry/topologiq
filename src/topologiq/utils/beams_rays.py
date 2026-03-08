from itertools import product

import numpy as np
Coordinates = np.ndarray

class RayBeam:
    ORIGIN = np.zeros(3, dtype = np.int32)

    def __init__(self, source: np.ndarray, direction: np.ndarray):
        self.source = source
        self.direction = direction

    @staticmethod
    def colinear_distance(v1: Coordinates, v2: Coordinates):
        agreement = sum(1 for i in range(3) if v1[i] == v2[i])
        return v2 - v1 if agreement == 2 else RayBeam.ORIGIN

    def interrupted_by(self, that: Coordinates):
        sigma = that - self.source
        cross = np.cross(self.direction, sigma)
        return np.dot(cross, cross) == 0 and np.dot(self.direction, sigma) >= 0

    def interrupted_by_array(self, that):
        return any(np.array_equal(pos, that) for pos in self.to_array())

    def intersected_by(self, that):
        relative_orientation = np.dot(self.direction, that.direction)

        # Based on the relative orientation, the source of that beam must be located in the correct quadrant.
        sigma = that.source - self.source
        if relative_orientation == 0:
            # Beams are orthogonal; source of the other beam must be in the positive quadrant
            # of the subspace spanned by { self.direction, -that.direction }
            basis = self.direction - that.direction
            intersecting_rays = np.all( (sigma == 0) | (np.sign(sigma) == np.sign(basis)) )
        else:
            # Beams are parallel; source of that beam must be on the same line as the direction of this beam
            cross = np.cross(self.direction, sigma)
            intersecting_rays = np.dot(cross, cross) == 0
            if relative_orientation == -1:
                # Beams are in opposite directions; source of that beam cannot be behind the source of this beam
                intersecting_rays &= np.dot(self.direction, sigma) >= 0

        return intersecting_rays

    def intersected_by_array(self, that):
        array1 = self.to_array()
        array2 = that.to_array()
        return any(np.array_equal(p1, p2) for p1, p2 in product(array1, array2))

    def to_array(self, length: int = 10):
        return [ self.source + i * self.direction for i in range(length) ]

    def __eq__(self, other):
        return np.array_equal(self.source, other.source) and np.array_equal(self.direction, other.direction)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return f"@{self.source}->{self.direction}"

    def __repr__(self):
        return str(self)