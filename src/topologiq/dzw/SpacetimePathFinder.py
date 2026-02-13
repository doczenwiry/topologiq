from logging import getLogger
console = getLogger(__name__)

from collections import deque

from topologiq.utils.classes import NodeBeams

from topologiq.dzw.utils.AugmentedNxGraph import AugmentedNxGraph
from topologiq.dzw.utils.CubeKind import CubeKind
from topologiq.dzw.utils.Spacetime import Coordinates

from topologiq.dzw.helpers.SpacetimeHelper import SpacetimeHelper

# pathfinder.py
class SpacetimePathFinder:
    def __init__(self, nx_graph: AugmentedNxGraph):
        self.nx_graph = nx_graph

    def find_target_realisation(self, source: int, target: int):
        target_suitable_kinds = CubeKind.suitable_kinds(self.nx_graph.get_node_type(target))

        console.info(f"Searching for realisation of target node #{target} [type={self.nx_graph.get_node_type(target)}]")
        console.info(f"> Suitable target kinds : {target_suitable_kinds}")

        proposed_paths = []
        for max_md in range(1, 10):
            proposed_paths = self.__core_pathfinder(
                source = source, target = target, maximal_md = max_md,
                goal_reached =
                    lambda kind, position : kind in target_suitable_kinds and position not in self.nx_graph.occupied
            )
            if len(proposed_paths) > 0:
                break

        return proposed_paths

    def find_edge_realisation(self,
        source: int, target: int,
        critical: dict[int, tuple[int, NodeBeams]] = None
    ):
        target_cube = self.nx_graph.get_cube(target)
        target_kind = self.nx_graph.get_cube_kind(target_cube)
        target_position = self.nx_graph.get_cube_position(target_cube)
        edge_type = self.nx_graph.get_edge_type(source, target)

        console.info(f"Searching for realisation of edge {source}-{target} [type={edge_type}]")
        console.info(f"> Target cube #{target_cube} : {target_kind}@{target_position}")

        return self.__core_pathfinder(
            source = source, target = target,
            critical = critical, maximal_md = 20,
            goal_reached =
                lambda kind, position : kind == target_kind and position == target_position,
            terminate_on_first_found = True
        )

    # TODO: deal with Hadamard EdgeType !!
    # TODO: add suggestions of candidate coordinates ?
    # TODO: add cutoff threshold once enough of the bounding box has been reached
    def __core_pathfinder(self,
        source: int, target: int,
        critical: dict[int, tuple[int, NodeBeams]] = None,
        maximal_md: int = 3,
        goal_reached = lambda next_kind, next_position : True,
        terminate_on_first_found = False
    ) -> list[list[tuple[CubeKind, Coordinates]]]:
        if critical is None:
            critical = {}

        if not self.nx_graph.is_node_realised(source):
            raise Exception(f"Source node #{source} is not realised; cannot use as a start for path-finding.")

        source_cube = self.nx_graph.get_cube(source)
        source_kind = self.nx_graph.get_cube_kind(source_cube)
        source_position = self.nx_graph.get_cube_position(source_cube)

        console.info(f"> Start cube #{source_cube} : {source_kind}@{source_position}")
        console.info(f"> Occupied : {self.nx_graph.occupied}")

        # Initialise queue with the source cube
        start_cube = (source_kind, source_position)
        queue = deque([ start_cube ])
        paths = { start_cube : [ start_cube] }
        visited : dict[tuple[tuple[CubeKind, Coordinates], Coordinates], int] = {}
        solutions : list[list[tuple[CubeKind, Coordinates]]] = []

        while queue:
            current_cube = queue.popleft()
            current_path = paths[current_cube]
            terminal_kind, terminal_position = current_path[-1]

            if goal_reached(terminal_kind, terminal_position):
                console.debug(f"Goal reached : {terminal_kind}@{terminal_position}.")
            else:
                console.debug(f"Terminal cube : {terminal_kind}@{terminal_position}.")

            # Discard current_path if it is beyond the maximal Manhattan Distance requested
            current_md = source_position.get_manhattan_distance(terminal_position)
            if current_md > maximal_md:
                continue

            # TODO: deal with Hadamard-consistency
            constellation = SpacetimeHelper.get_candidate_constellation(terminal_kind, terminal_position)
            console.debug(f"> Constellation of {terminal_kind}@{terminal_position} : {constellation}.")
            for next_kind, next_position in constellation:
                next_md = source_position.get_manhattan_distance(next_position)

                # Ignore step if it brings us to an occupied position, unless that is the goal
                if next_position in self.nx_graph.occupied and not goal_reached(next_kind, next_position):
                    console.debug(f"> Next position is already occupied [{next_kind}@{next_position}].")
                    continue

                # Ignore step if it brings us to a position used by the current path
                if any([position == next_position for _, position in current_path]):
                    console.debug(f"> Next position is already occupied in current_path [{next_kind}@{next_position}].")
                    continue

                # Ignore step if it brings us beyond the maximal MD or is not of a suitable kind
                if next_md > maximal_md:
                    console.debug(f"> Next position lies beyond maximal Manhattan Distance [{next_kind}@{next_position}/md:{next_md}].")
                    continue

                next_cube = (next_kind, next_position)
                next_path = current_path + [ next_cube ]

                # Ignore step if it doesn't improve our current knowledge
                next_visitation = (next_cube, next_position - terminal_position)
                if next_cube in visited and len(next_path) >= visited[next_visitation]:
                    console.debug(f"> Next path doesn't improve previously known [{next_path}].")
                    continue

                # Happily update our current knowledge with this new path
                visited[next_visitation] = len(next_path)
                paths[next_cube] = next_path
                # Consider next_path for further extension only if its terminal cube is not a leaf cube-kind
                if next_kind not in [ CubeKind.OOO , CubeKind.YYY ]:
                    queue.append( next_cube )

                console.debug(f"> Adding next path to {next_kind}@{next_position} [{next_path}].")

                # TODO: deal with broken beams (cfr. pathfinder lines 299-329)
                critical_break = False
                if critical:
                    for node, data in critical.items():
                        if node in (source, target):
                            continue

                        broken_beams = 0
                        min_exit_num, beams = data
                        for beam in beams:
                            if any([position.as_tuple() in beam for _, position in current_path]):
                                broken_beams += 1
                                # Additionally, add any number of beam-to-beam clashes for the node
                                # currently under investigation because, if they exist, they likely are already
                                # using the cushion that allows breaking some beams
                                for n_id in critical.keys():
                                    all_beams = critical[n_id][1]
                                    for single_beam in all_beams:
                                        if any([position in beam for position in single_beam]):
                                            broken_beams += 1

                        adjust_for_source_node = 1 if node in (source,target) else 0
                        if len(beams) + adjust_for_source_node - broken_beams < min_exit_num:
                            critical_break = True
                            break

                    if critical_break:
                        continue

                if not critical_break and goal_reached(next_kind, next_position):
                    console.debug(f"Found new path to {next_kind}@{next_position} : {next_path}")
                    solutions.append(next_path)

            if terminate_on_first_found and len(solutions) > 0:
                break

        console.info(f"Solutions found : {len(solutions)}")
        return solutions
