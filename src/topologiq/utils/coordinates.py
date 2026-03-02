from typing import NamedTuple

class Coordinates(NamedTuple):
    x: int
    y: int

    def __add__(self, other):
        return Coordinates(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Coordinates(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Coordinates(self.x * other, self.y * other)
    __rmul__ = __mul__

    def non_zeroes(self):
        return sum(1 for e in self if e != 0)

    def __different_components(self, other):
        return sum(1 for i in range(2) if self[i] != other[i])

    def colinear(self, other):
        return self.x == other.x or self.y == other.y # self.__different_components(other) == 1

    def dot(self, other):
        return sum(self[i] * other[i] for i in range(2))

    def cross(self, other):
        return self.x * other.y - self.y * other.x
        # return Coordinates(self.y * other.z - self.y * other.z,
        #                    self.z * other.x - self.z * other.x,
        #                    self.x * other.y - self.x * other.y)

    def __len__(self):
        return self.dot(self)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return f"({self.x}, {self.y})"