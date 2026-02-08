from enum import Enum

from topologiq.dzw.utils.CubeKind import CubeKind
from topologiq.dzw.utils.Spacetime import Spacetime, Coordinates, Step

from logging import getLogger
console = getLogger(__name__)

class CubeBeams:
    class ConflictType(Enum):
        TYPE0 = 0 # No line-of-sight
        TYPE1 = 1 # Cubes are CO-PLANAR (beams clash)
        TYPE2 = 2 # Cubes are CO-LINEAR (beams break)

    def __init__(self, cube_kind: CubeKind, cube_position: Coordinates, occupied: set[Coordinates] = None):
        if occupied is None:
            occupied = set()

        self.__cube_kind: CubeKind = cube_kind
        self.__cube_position: Coordinates = cube_position
        self.__available_beams: list[Coordinates] = []
        cube_reach = cube_kind.get_reach()

        lines_of_sight = set()
        for position in occupied:
            if cube_position.colinear(position):
                lines_of_sight.add(cube_position.get_line_of_sight(position))

        for step in Spacetime.STEPS:
            if cube_reach.contains(step) and step.value not in lines_of_sight:
                self.__available_beams.append( step.value )

    def number_available(self):
        return len(self.__available_beams)

    def count_interrupted(self, lines_of_sight: set[Coordinates]) -> int:
        if any( [Spacetime.ORIGIN.get_manhattan_distance(los) != 1 for los in lines_of_sight] ):
            raise Exception(f"Computing remaining beam count requires lines-of-sight of unit length.")

        return sum(1 for los in lines_of_sight if los in self.__available_beams)

    def count_intersected(self, node_beams, target_beams) -> int:
        beams_intersected = 0
        for node_beam in node_beams:
            for target_beam in target_beams:
                if any([ c in node_beam for c in target_beam ]):
                    beams_intersected += 1

        return beams_intersected

    def close_beam(self, beam: Coordinates):
        if beam not in self.__available_beams:
            raise Exception(f"Closing non-existent beam for cube {self.__cube_kind}@{self.__cube_position} [{beam}].")

        self.__available_beams.remove(beam)

    def __repr__(self):
        formatted = f"{self.__cube_kind}@{self.__cube_position} :"
        for beam in self.__available_beams:
            formatted += f" {beam}"
        return formatted

    # # TODO: deal with broken beams (cfr. pathfinder lines 299-329)
    # critical_break = False
    # if critical:
    #     for node, data in critical.items():
    #         broken_beams = 0
    #         min_exit_num, beams = data
    #         for beam in beams:
    #             if any([position in beam for _, position in current_path]):
    #                 broken_beams += 1
    #                 # Additionally, add any number of beam-to-beam clashes for the node
    #                 # currently under investigation because, if they exist, they likely are already
    #                 # using the cushion that allows breaking some beams
    #                 if node in (source, target):
    #                     continue
    #
    #                 for n_id in critical.keys():
    #                     all_beams = critical[n_id][1]
    #                     for single_beam in all_beams:
    #                         if any([position in beam for position in single_beam]):
    #                             broken_beams += 1
    #
    #         adjust_for_source_node = 1 if node in (source, target) else 0
    #         if len(beams) + adjust_for_source_node - broken_beams < min_exit_num:
    #             critical_break = True
    #             break
    #
    #     if critical_break:
    #         continue