import numpy as np

from topologiq.utils.classes import StandardCoord

Coordinates = np.ndarray

class RayBeam:
    ORIGIN = np.zeros(3)

    def __init__(self, source: StandardCoord, direction: StandardCoord):
        self.source = np.array( source )
        self.direction = np.array( direction )

    @staticmethod
    def colinear_distance(v1: Coordinates, v2: Coordinates):
        agreement = sum(1 for i in range(3) if v1[i] == v2[i])
        return v2 - v1 if agreement == 2 else RayBeam.ORIGIN

    def interrupted_by(self, that: Coordinates):
        # Check whether that - self.source is colinear with self.direction
        difference = that - self.source

        if np.array_equal(RayBeam.ORIGIN, difference):
            return False

        cross = np.linalg.cross(difference, self.direction)

        condition = np.dot(difference, self.direction) > 1 and np.array_equal(RayBeam.ORIGIN, cross)
        if condition != self.interrupted_by_array(that):
            raise Exception(f"INTERRUPTION inconsistency detected: {self} / {that}")

        return np.dot(difference, self.direction) > 1 and np.array_equal(RayBeam.ORIGIN, cross)

    def interrupted_by_array(self, that):
        return any(np.array_equal(pos, that) for pos in self.to_array())

    # TODO: expand to 3D.
    def intersected_by(self, that):
        cross = np.linalg.cross(self.direction, that.direction)
        delta = self.__inner_determinant(self.direction, cross, -that.direction)

        if delta == 0:
            return False

        sigma = that.source - self.source
        t1 = np.linalg.det(np.column_stack( (sigma, self.direction, cross) )) / delta
        t2 = np.linalg.det(np.column_stack( (sigma, that.direction, cross) )) / delta
        # t1 = self.__inner_determinant(sigma, self.direction, cross) / delta
        # t2 = self.__inner_determinant(sigma, that.direction, cross) / delta
        # dt = self.__inner_determinant(sigma, self.direction, that.direction) / delta

        condition = t1 >= 1 and t2 >= 1
        if condition != self.intersected_by_array(that):
            raise Exception(f"INTERSECTION inconsistency detected: {self} / {that}")

        return t1 >= 1 and t2 >= 1

    # Manhattan-collinearity
    @staticmethod
    def __colinear(v1: Coordinates, v2: Coordinates):
        return sum(1 for i in range(3) if v1[i] == v2[i]) == 2

    def intersected_by_array(self, that):
        array1 = self.to_array()
        array2 = that.to_array()
        return not RayBeam.__colinear(self.source, that.source) and sum(
            1 for p1 in array1 if any(np.array_equal(p1, p2) for p2 in array2)) == 1

    @staticmethod
    def __inner_determinant(v1: Coordinates, v2: Coordinates, v3: Coordinates):
        return np.linalg.det(
            np.column_stack( (v1, v2, v3) )
        )

    def to_array(self, length: int = 10):
        return [ self.source + i * self.direction for i in range(1, length+1) ]

    def __eq__(self, other):
        return np.array_equal(self.source, other.source) and np.array_equal(self.direction, other.direction)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return f"@{self.source}->{self.direction}"

    def __repr__(self):
        return str(self)