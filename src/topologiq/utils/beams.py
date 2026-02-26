from sympy import Ray3D

from topologiq.utils.classes import StandardCoord, Coordinates

class RayBeam:
    def __init__(self, cube_position: StandardCoord, beam_direction: StandardCoord):
        source_position = Coordinates(cube_position[0], cube_position[1], cube_position[2])
        beam_direction = Coordinates(beam_direction[0], beam_direction[1], beam_direction[2])
        start_position = source_position + beam_direction
        self.__start = start_position
        self.__direction = beam_direction
        self.__beam = Ray3D(p1 = start_position, pt = start_position + beam_direction)

    def contains(self, cube_position: Coordinates):
        return self.__beam.contains(cube_position)

    def intersects(self, other):
        return bool(self.__beam.intersection(other.__beam))

    def __eq__(self, other):
        return self.__start == other.__start and self.__direction == other.__direction

    def __hash__(self):
        return hash((self.__start, self.__direction))

    def __str__(self):
        return str(f"@{self.__start}->{self.__direction}")

    def __repr__(self):
        return str(f"@{self.__start}->{self.__direction}")