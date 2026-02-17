from logging import getLogger

from topologiq.dzw.utils.CubeBeams import CubeBeams
from topologiq.dzw.utils.EdgeType import EdgeType

console = getLogger(__name__)

from collections import deque

from topologiq.utils.classes import NodeBeams

from topologiq.dzw.utils.AugmentedNxGraph import AugmentedNxGraph
from topologiq.dzw.utils.CubeKind import CubeKind
from topologiq.dzw.utils.Spacetime import Coordinates
from topologiq.dzw.utils.Path import Path

from topologiq.dzw.helpers.SpacetimeHelper import SpacetimeHelper

CubeList = list[tuple[CubeKind, Coordinates]]
PipeList = list[EdgeType]

# pathfinder.py
class SpacetimePathFinder:
    def __init__(self, nx_graph: AugmentedNxGraph):
        self.nx_graph = nx_graph

    def find_target_realisation(self, source: int, target: int) -> list[Path]:
        target_suitable_kinds = CubeKind.suitable_kinds(self.nx_graph.get_node_type(target))

        console.info(f"Searching for realisation of target node #{target} [type={self.nx_graph.get_node_type(target)}]")
        console.info(f"> Suitable target kinds : {target_suitable_kinds}")

        solutions = []
        for max_md in range(1, 10):
            solutions = self.__core_pathfinder(
                source = source, target = target, maximal_md = max_md,
                goal_reached = lambda kind, position :
                    kind in target_suitable_kinds and position not in self.nx_graph.occupied
            )
            if len(solutions) > 0:
                break

        return solutions

    def find_edge_realisation(self,
        source: int, target: int,
        node_beams: dict[int, NodeBeams] = None
    ) -> list[Path]:
        target_cube = self.nx_graph.get_cube(target)
        target_kind = self.nx_graph.get_cube_kind(target_cube)
        target_position = self.nx_graph.get_cube_position(target_cube)
        edge_type = self.nx_graph.get_edge_type(source, target)

        console.info(f"Searching for realisation of edge {source}-{target} [type={edge_type}]")
        console.info(f"> Target cube #{target_cube} : {target_kind}@{target_position}")

        return self.__core_pathfinder(
            source = source, target = target,
            node_beams= node_beams, maximal_md = 20,
            goal_reached =
                lambda kind, position : kind == target_kind and position == target_position,
            terminate_on_first_found = True
        )

    # TODO: deal with Hadamard EdgeType !!
    # TODO: add suggestions of candidate coordinates ?
    # TODO: add cutoff threshold once enough of the bounding box has been reached
    def __core_pathfinder(self,
        source: int, target: int,
        node_beams: dict[int, NodeBeams] = None,
        maximal_md: int = 3,
        goal_reached = lambda next_kind, next_position : True,
        terminate_on_first_found = False
    ) -> list[Path]:
        if node_beams is None:
            node_beams = {}

        if not self.nx_graph.is_node_realised(source):
            raise Exception(f"Source node #{source} is not realised; cannot use as a start for path-finding.")

        source_cube = self.nx_graph.get_cube(source)
        source_kind = self.nx_graph.get_cube_kind(source_cube)
        source_position = self.nx_graph.get_cube_position(source_cube)

        edge_type = self.nx_graph.get_edge_type(source, target)

        console.info(f"> Start cube #{source_cube} : {source_kind}@{source_position}")
        console.info(f"> Occupied : {self.nx_graph.occupied}")

        # Initialise queue with the source cube
        start_cube = (source_kind, source_position)
        queue = deque([ start_cube ])
        paths = { start_cube : ([start_cube],[]) }
        visited : dict[tuple[tuple[CubeKind, Coordinates], Coordinates], int] = {}
        solutions : list[tuple[CubeList, PipeList]] = []

        while queue:
            current_cube = queue.popleft()
            current_cubes, current_pipes = paths[current_cube]
            terminal_kind, terminal_position = current_cubes[-1]

            if goal_reached(terminal_kind, terminal_position):
                console.debug(f"Goal reached : {terminal_kind}@{terminal_position}.")
            else:
                console.debug(f"Terminal cube : {terminal_kind}@{terminal_position}.")

            # Discard current_path if it is beyond the maximal Manhattan Distance requested
            current_md = source_position.get_manhattan_distance(terminal_position)
            if current_md > maximal_md:
                continue

            # TODO: deal with Hadamard-consistency
            pipe_type = EdgeType.HADAMARD if current_md == 0 and edge_type == EdgeType.HADAMARD else EdgeType.IDENTITY
            constellation = SpacetimeHelper.get_candidate_constellation(terminal_kind, terminal_position, pipe_type)
            console.debug(f"> Constellation of {terminal_kind}@{terminal_position} : {constellation}.")
            for next_kind, next_position in constellation:
                next_md = source_position.get_manhattan_distance(next_position)

                # Ignore step if it brings us to an occupied position, unless that is the goal
                if next_position in self.nx_graph.occupied and not goal_reached(next_kind, next_position):
                    console.debug(f"> Next position is already occupied [{next_kind}@{next_position}].")
                    continue

                # Ignore step if it brings us to a position used by the current path
                if any([position == next_position for _, position in current_cubes]):
                    console.debug(f"> Next position is already occupied in current_path [{next_kind}@{next_position}].")
                    continue

                # Ignore step if it brings us beyond the maximal MD or is not of a suitable kind
                if next_md > maximal_md:
                    console.debug(f"> Next position lies beyond maximal Manhattan Distance [{next_kind}@{next_position}/md:{next_md}].")
                    continue

                next_cube = (next_kind, next_position)
                next_cubes = current_cubes + [ next_cube ]
                next_pipes = current_pipes + [ pipe_type ]

                # Ignore step if it doesn't improve our current knowledge
                next_visitation = (next_cube, next_position - terminal_position)
                if next_cube in visited and len(next_cubes) >= visited[next_visitation]:
                    console.debug(f"> Next path doesn't improve previously known [{next_cubes}].")
                    continue

                # Happily update our current knowledge with this new path
                visited[next_visitation] = len(next_cubes)
                paths[next_cube] = (next_cubes, next_pipes)
                # Consider next_path for further extension only if its terminal cube is not a leaf cube-kind
                if next_kind not in [ CubeKind.OOO , CubeKind.YYY ]:
                    queue.append( next_cube )

                console.debug(f"> Adding next path to {next_kind}@{next_position} [{next_cubes}].")

                # TODO: deal with broken beams (cfr. pathfinder lines 299-329)
                critical_interruptions = self.check_critical_interruptions(source, target, node_beams, current_cubes)

                if not critical_interruptions and goal_reached(next_kind, next_position):
                    console.debug(f"Found new path to {next_kind}@{next_position} : {next_cubes}")
                    solutions.append( (next_cubes, next_pipes) )

            if terminate_on_first_found and len(solutions) > 0:
                break

        console.info(f"Solutions found : {len(solutions)}")

        valid_solutions = []
        for proposed_cubes, proposed_pipes in solutions:
            proposed_kind, proposed_position = proposed_cubes[-1]
            proposed_beams = CubeBeams(proposed_kind, proposed_position,
                                       extras = proposed_cubes[1:-1], occupied = self.nx_graph.occupied
                                       )
            target_cube = self.nx_graph.get_cube(target)
            candidate_path = Path(source_cube, target_cube, edge_type, proposed_beams, proposed_cubes, proposed_pipes)
            if self.nx_graph.is_path_valid(candidate_path, edge_type):
                valid_solutions.append( candidate_path )

        return valid_solutions

    def check_critical_interruptions(self, source, target, node_beams, current_path):
        critical_interruptions = False

        for node, beams in node_beams.items():
            if node == source or node == target:
                continue

            beams_interrupted = 0
            unrealised_edges = self.nx_graph.get_edges_unrealised(node)
            for beam in beams:
                if any([position.as_tuple() in beam for _, position in current_path]):
                    beams_interrupted += 1
                    # Additionally, add any number of beam-to-beam clashes for the node
                    # currently under investigation because, if they exist, they likely are already
                    # using the cushion that allows breaking some beams
                    for other, obeams in node_beams.items():
                        for obeam in obeams:
                            if any([position in beam for position in obeam]):
                                beams_interrupted += 1

            beams_remaining = len(beams) - beams_interrupted
            adjust_for_source_node = 1 if node in (source, target) else 0
            if beams_remaining + adjust_for_source_node < unrealised_edges:
                critical_interruptions = True
                break

        return critical_interruptions

    # TODO: remove once its logic is integrated into the above function
    def former_check_continue(self, source, target, critical_beams, full_path_coords):
        # Abort if next position clashes with a critical beam
        src_tgt_ids = (source, target)
        continue_flag = False

        for node, beams in critical_beams.items():
            beams_interrupted = 0
            unrealised_edges = self.nx_graph.get_edges_unrealised(node)
            for beam in beams:
                # If a coord breaks a beam, add one to broken beams because beam
                # of node has been broken
                if any([coord in beam[:6] for coord in full_path_coords]):
                    beams_interrupted += 1
                    # Additionally, add any number of beam-to-beam clashes for the node
                    # currently under investigation because, if they exist, they likely are already
                    # using the cushion that allows breaking some beams
                    if node not in src_tgt_ids:
                        for n_id in critical_beams.keys():
                            all_beams = critical_beams[n_id][1]
                            for single_beam in all_beams:
                                if any([coord in beam[:6] for coord in single_beam]):
                                    beams_interrupted += 1

            adjust_for_source_node = 1 if node in src_tgt_ids else 0
            if len(beams) + adjust_for_source_node - beams_interrupted < unrealised_edges:
                continue_flag = True
                break
            else:
                continue_flag = False

        return continue_flag