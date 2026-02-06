import functools
import math
from enum import Enum

# Essentially vectors with their basic operations
class Coordinates:
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def from_tuple(t: tuple[int, int, int]):
        return Coordinates(t[0], t[1], t[2])

    def __add__(self, other):
        if isinstance(other, Step):
            other = other.value
        return Coordinates(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        if isinstance(other, Step):
            other = other.value
        return Coordinates(self.x - other.x, self.y - other.y, self.z - other.z)

    def invert(self):
        return Coordinates(-self.x, -self.y, -self.z)

    def mul(self, scalar: int):
        return Coordinates(self.x * scalar, self.y * scalar, self.z * scalar)

    def div(self, scalar: int):
        return Coordinates(int(self.x / scalar), int(self.y / scalar), int(self.z / scalar))

    def normalized(self):
        return self.div(int(math.sqrt(self.dot(self))))

    def dot(self, other) -> int:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def get_manhattan_distance(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z)

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def as_tuple(self):
        return self.x, self.y, self.z

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.as_tuple())

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    @functools.total_ordering
    def __lt__(self, other):
        return self.as_tuple().__lt__(other.as_tuple())

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

class Step(Enum):
    # Represented by unit vectors
    XP = Coordinates(+1, 0, 0)
    XM = Coordinates(-1, 0, 0)
    YP = Coordinates(0, +1, 0)
    YM = Coordinates(0, -1, 0)
    ZP = Coordinates(0, 0, +1)
    ZM = Coordinates(0, 0, -1)

    def __str__(self):
        return f"Step.{self.name}"

class Reach(Enum):
    # Represented by their normal vectors
    XYZ = Coordinates(0, 0, 0)
    XY = Coordinates(0,0,  +1)
    XZ = Coordinates(0,  +1,0)
    YZ = Coordinates(  +1,0,0)

    def contains(self, point: Coordinates) -> bool:
        if isinstance(point, Step):
            point = point.value
        # Dot product will tell us whether the step lies in this plane
        return self.value.dot(point) == 0

    def get_step_constellation(self) -> list[Step]:
        return [ step for step in BlockGraphSpace.STEPS if self.contains(step.value) ]

    def __str__(self):
        return f"Plane.{self.name}"

class BlockGraphSpace:
    ORIGIN = Coordinates(0, 0, 0)

    STEPS = [ Step.XP, Step.XM, Step.YP, Step.YM, Step.ZP, Step.ZM ]
    PLANES = [Reach.XY, Reach.XZ, Reach.YZ]

    @staticmethod
    def get_orthogonal_plane(plane: Reach, line_of_intersection: Coordinates) -> Reach:
        if isinstance(line_of_intersection, Step):
            line_of_intersection = line_of_intersection.value

        if not plane.contains(line_of_intersection):
            raise ValueError(f"Line of intersection {line_of_intersection} does not lie in plane {plane}.")

        reach = plane.value

        if abs(reach.x) == abs(line_of_intersection.x):
            return Reach.YZ
        elif abs(reach.y) == abs(line_of_intersection.y):
            return Reach.XZ
        else: # abs(reach.z) != abs(line_of_intersection.z)
            return Reach.XY

    @staticmethod
    def get_constellation(position: Coordinates, restriction: Reach = None) -> list[Coordinates]:
        constellation = []
        for step in BlockGraphSpace.STEPS:
            if restriction is None or restriction.contains(step.value):
                constellation.append(position + step.value)
        return constellation