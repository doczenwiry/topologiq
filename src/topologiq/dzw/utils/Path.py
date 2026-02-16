from topologiq.dzw.utils.CubeBeams import CubeBeams
from topologiq.dzw.utils.CubeKind import CubeKind
from topologiq.dzw.utils.EdgeType import EdgeType
from topologiq.dzw.utils.Spacetime import Coordinates, Reach

from logging import getLogger
console = getLogger(__name__)

class Path:
    PATH_LEN_HP = -1
    BEAMS_BROKEN_HP = -1

    def __init__(self, source: int, target: int, edge_type: EdgeType, proposed_beams: CubeBeams,
            proposed_cubes: list[tuple[CubeKind, Coordinates]], proposed_pipes: list[EdgeType]
    ):
        self.__source = source
        self.__target = target
        self.__edge_type = edge_type
        proposed_kind, proposed_position = proposed_cubes[-1]
        self.__target_kind = proposed_kind
        self.__target_position = proposed_position
        self.__proposed_cube_beams = proposed_beams
        self.__cubes = proposed_cubes
        self.__pipes = proposed_pipes
        self.__cube_beams = None
        self.__total_beams_interrupted = None

    def get_source(self):
        return self.__source

    def get_target(self):
        return self.__target

    def get_target_kind(self):
        return self.__target_kind

    def get_target_position(self):
        return self.__target_position

    def get_cubes(self):
        return self.__cubes

    def get_extra_cubes(self):
        return self.__cubes[1:-1]

    def get_pipes(self):
        return self.__pipes

    def get_cube_beams(self):
        return self.__cube_beams

    def set_cube_beams(self, beams: CubeBeams):
        self.__cube_beams = beams

    def get_total_beams_interrupted(self):
        return self.__total_beams_interrupted

    def set_total_beams_interrupted(self, total_interrupted_beams: int):
        self.__total_beams_interrupted = total_interrupted_beams

    def weight(self):
        return len(self.__pipes) * Path.PATH_LEN_HP + self.__total_beams_interrupted * Path.BEAMS_BROKEN_HP

    # @staticmethod
    # def is_path_valid(
    #         nx_graph: AugmentedNxGraph,
    #         source: int, target: int,
    #         cubes: list[tuple[CubeKind, Coordinates]],
    #         pipes: list[EdgeType]
    # ) -> bool:
    #     is_hadamard_path = False
    #
    #     source_cube = nx_graph.get_cube(source)
    #     source_kind: CubeKind = nx_graph.get_cube_kind(source_cube)
    #     source_position: Coordinates = nx_graph.get_cube_position(source_cube)
    #
    #     edge_type = nx_graph.get_edge_type(source, target)
    #
    #     proposed_target_kind, proposed_target_position = cubes[-1]
    #
    #     extra_positions = set()
    #
    #     console.info(f"Checking path validity:")
    #     console.info(f"> Source cube #{source_cube} [{source_kind}@{source_position}]")
    #     console.info(f"> Proposed target cube : {proposed_target_kind}@{proposed_target_position}")
    #     console.info(f"> Path cubes : {cubes}")
    #     console.info(f"> Path pipes : {pipes}")
    #
    #     previous_kind = source_kind
    #     previous_position = source_position
    #     previous_reach: Reach = source_kind.get_reach()
    #
    #     n = len(cubes)
    #     for index in range(1, n):
    #         current_kind, current_position = cubes[index]
    #         current_reach = current_kind.get_reach()
    #
    #         if index != n-1:
    #             # Check that the cube type is either X or Z (Y and boundaries must be leaves)
    #             if current_kind in [ CubeKind.OOO, CubeKind.YYY ]:
    #                 console.debug(f"> CubeKind.OOO and CubeKind.YYY can only appear at the ends of a path : {current_kind}.")
    #                 return False
    #
    #             # Check that the current_position is not already occupied
    #             if current_position in nx_graph.occupied:
    #                 console.debug(f"> Current position is already occupied : {current_kind}@{current_position}")
    #                 return False
    #
    #         # Check that the step taken lies in both reaches of successive cubes
    #         step_taken = current_position - previous_position
    #         if not previous_reach.contains(step_taken) or not current_reach.contains(step_taken):
    #             console.debug(f"> Previous reach contains step : {previous_reach.contains(step_taken)}")
    #             console.debug(f"> Current reach contains step : {current_reach.contains(step_taken)}")
    #             return False
    #
    #         # Check that the current_position is not already occupied by an extra cube
    #         if current_position in extra_positions:
    #             console.debug(f"> Current position is already in path : {current_kind}@{current_position}")
    #             return False
    #         extra_positions.add(current_position)
    #
    #         # Check that the current pipe has a type consistent with what is allowed
    #         current_pipe_type = pipes[index-1]
    #         if not current_pipe_type in SpacetimeHelper.infer_pipe_type(previous_kind, current_kind):
    #             console.debug(f"> Current pipe type is not allowed between {previous_kind} and {current_kind} [{current_pipe_type}].")
    #             return False
    #
    #         if current_pipe_type == EdgeType.HADAMARD:
    #             is_hadamard_path = not is_hadamard_path
    #
    #         previous_position = current_position
    #         previous_kind = current_kind
    #         previous_reach = current_reach
    #
    #     if nx_graph.is_node_realised(target):
    #         target_cube = nx_graph.get_cube(target)
    #         if proposed_target_kind != nx_graph.get_cube_kind(target_cube):
    #             console.debug(f"> Proposed target kind does not match its existing realisation.")
    #             return False
    #         if proposed_target_position != nx_graph.get_cube_position(target_cube):
    #             console.debug(f"> Proposed target position does not match its existing realisation.")
    #             return False
    #     elif proposed_target_position in nx_graph.occupied:
    #         console.debug(f"> Proposed target position is already occupied.")
    #         return False
    #
    #     hadamard_consistent = is_hadamard_path == (edge_type == EdgeType.HADAMARD)
    #
    #     if not hadamard_consistent:
    #         console.debug(f"> Proposed path is Hadamard-inconsistent with its purported edge [{edge_type}].")
    #
    #     return hadamard_consistent