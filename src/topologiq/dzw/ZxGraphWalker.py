import random
from collections import deque

import pyzx as zx
import networkx as nx

from logging import getLogger
console = getLogger(__name__)

from topologiq.dzw.AugmentedNxGraph import AugmentedNxGraph
from topologiq.dzw.BlockGraphSpace import BlockGraphSpace, Coordinates
from topologiq.dzw.BlockGraphComponents import CubeKind
from topologiq.dzw.ZxGraphComponents import EdgeType, NodeType

from topologiq.dzw.SpacetimePathFinder import SpacetimePathFinder

# TODO: remove once rewrite is done
from topologiq.scripts.graph_manager import run_pathfinder
from topologiq.scripts.pathfinder import pathfinder, get_taken_coords
from topologiq.utils.utils_greedy_bfs import gen_tent_tgt_coords
from topologiq.utils.classes import NodeBeams, PathBetweenNodes

kwargs: dict[str, tuple[int, int] | int] = {
    "weights": (-1, -1),
    "length_of_beams": 99,
}

# graph_manager.py
class ZxGraphWalker:
    def __init__(self, pyzx_graph: zx.graph.base.BaseGraph, circuit_name: str = "circuit"):
        self.name = circuit_name
        self.hide_ports = False # This really belongs in the visualisation layer
        self.min_success_rate = 50
        self.nx_graph = AugmentedNxGraph(pyzx_graph)
        self.pathfinder = SpacetimePathFinder(self.nx_graph)
        self.number_1st_pass_edges = 0
        self.number_2nd_pass_edges = 0
        self.node_realisation_order = []
        self.edge_realisation_order = []
        self.node_cube_beams : dict[int, NodeBeams] = dict()

    def pick_root(self, central_spider: bool = True, deterministic: bool = False) -> int:
        """Pick the spider that will serve as the root of the construction.

        Args:
            deterministic (bool, optional):
                True  => return the candidate spider with the lowest ID
                False => return a random candidate spider
            central_spider (bool, optional):
                True  => candidates are all spiders with maximal degree
                False => candidates are all spiders

        Returns:
            ID of the spider that has been selected as the root
        """

        if self.nx_graph.number_of_nodes() == 0:
            raise nx.exception.NodeNotFound("Graph is empty.")

        # TODO: shouldn't we ignore boundaries when computing degree ?
        if central_spider:
            # n.b. entries of self.degree are tuples of the form (node_id, degree)
            (_, max_degree) = max([self.nx_graph.get_degree(node) for node in self.nx_graph.get_nodes()], key=lambda entry: entry[1])
            candidates = [node for node in self.nx_graph.get_nodes() if self.nx_graph.is_spider(node) and self.nx_graph.get_degree(node) == max_degree]
        else:
            candidates = [node for node in self.nx_graph.get_nodes() if self.nx_graph.is_spider(node)]

        return min(candidates) if deterministic else random.choice(candidates)

    def construct(self, root_choice: tuple[int, CubeKind] = None):
        # Prepare the root node of the construction.
        if root_choice is None:
            root = self.pick_root()
            kind = random.choice(CubeKind.suitable_kinds(self.nx_graph.get_node_type(root)))
        else:
            (root, kind) = root_choice
        self.nx_graph.realise_node(root, kind, BlockGraphSpace.ORIGIN)
        self.node_cube_beams[root] = self.compute_beams(kind, BlockGraphSpace.ORIGIN)

        queue : deque[int] = deque([root])
        visited: set[int] = set()

        # Proceed with the main loop of the BFS
        while queue:
            source: int = queue.popleft()
            visited.add(source)

            self.node_realisation_order.append(source)

            for target in self.nx_graph.get_neighbours(source):
                console.info(f"Processing {source}-{target} : [target_visited={target in visited}, edge_realised={self.nx_graph.is_edge_realised(source, target)}]")
                if target in visited or self.nx_graph.is_edge_realised(source, target):
                    continue

                path = None

                if not self.nx_graph.is_node_realised(target):
                    # First-pass edge
                    # Goal: find a path to some position where a suitable cube can be placed within some maximal MD
                    (target_kind, target_position, path) = self.find_target_realisation(source, target)

                    if target_kind is None or target_position is None:
                        raise Exception(f"Target realisation failure [{target}]")

                    # Realise the target node as a cube with kind and position provided by the pathfinder
                    self.nx_graph.realise_node(target, target_kind, target_position)

                    self.number_1st_pass_edges += 1
                    queue.append(target)
                elif not self.nx_graph.is_edge_realised(source, target):
                    # Second-pass edge
                    # Goal: find a path towards the position of a cube representing the target node
                    path = self.find_edge_realisation(source, target)

                    self.number_2nd_pass_edges += 1

                if path is None:
                    # TODO: reporting(..) and animation(..)
                    raise Exception(f"Edge realisation failure [{source}-{target}]")

                target_cube = self.nx_graph.get_cube(target)
                target_kind = self.nx_graph.get_cube_kind(target_cube)
                target_position = self.nx_graph.get_cube_position(target_cube)

                # Realise the edge using the path
                self.nx_graph.realise_edge(source, target, path)

                # Compute the beams for the target cube.
                self.node_cube_beams[target] = self.compute_beams(target_kind, target_position)

                # Store the path that realises the current edge
                self.edge_realisation_order.append( (source,target) )

                # Incorporate the positions that are occupied by the extra cubes in the path
                for position, _ in path:
                    self.nx_graph.occupied.add(position)

                self.prune_beams()

        # Prepare final BlockGraph and return it ?
        return True

    def find_target_realisation(self, source, target):
        outcome = self.place_nxt_block(source, target)

        if outcome is None:
            outcome = (None, None, None)

        return outcome

    def is_path_viable(self, source, target, clean_path) -> tuple[bool, int, int]:
        target_type = self.nx_graph.get_node_type(target)
        target_degree = self.nx_graph.get_degree(target)

        target_kind, target_position = clean_path[-1]
        console.debug(f"> Clean path [{target_kind}@{target_position}]: {clean_path}")
        coordinates_in_path = get_taken_coords(clean_path)
        target_beams = self.compute_beams(target_kind, target_position, coordinates_in_path)
        target_unobstructed_exits = len(target_beams)

        if target_type == NodeType.O:
            target_unobstructed_exits, target_beams = (6, [])

        source_beams = self.node_cube_beams[source]

        if not (target_unobstructed_exits >= target_degree - 1 or any(
                [clean_path[1][0] in beam for beam in source_beams])):
            console.debug(f">> enough_exits={target_unobstructed_exits >= target_degree - 1} broken={any(
                [clean_path[1][0] in beam for beam in source_beams])}")
            return False, 0, 0

        critical_broken = False
        beams_broken_by_path = 0
        for node in self.nx_graph.get_nodes():
            if node not in self.node_cube_beams:
                continue

            node_beams = self.node_cube_beams[node]
            broken = len(list(filter(lambda beam: any([c in coordinates_in_path for c in beam[:7]]), node_beams)))
            beams_broken_by_path += broken
            adjust_for_source_node = 1 if node == source else 0
            node_degree = self.nx_graph.get_degree(node)
            edges_realised = self.nx_graph.get_edges_realised(node)
            remaining_edges = node_degree - edges_realised
            if (len(node_beams) - broken + adjust_for_source_node) < remaining_edges:
                console.debug(f"> Broken for {node} [L:{len(node_beams)},B:{broken},A:{adjust_for_source_node},R:{remaining_edges}]")
                critical_broken = True

        critical_clash = False
        for node in self.node_cube_beams.keys():
            if node == source or node == target:
                continue

            node_beams = self.node_cube_beams[node]
            clashes = 0  # This is inside the following loop in the original code ...
            for node_beam in node_beams:
                clashes += len(list(filter(
                    lambda target_beam: sum([(c in node_beam[:9]) for c in target_beam[:9]]) > len(
                        target_beams) - target_degree, target_beams)))
            node_degree = self.nx_graph.get_degree(node)
            edges_realised = self.nx_graph.get_edges_realised(node)
            remaining_edges = node_degree - edges_realised
            if len(node_beams) - clashes < remaining_edges:
                console.debug(f"> Clash with {node}")
                critical_clash = True

        viable = not critical_broken and not critical_clash
        return viable, beams_broken_by_path, critical_clash

    # TODO: the BgPathFinder should provide a function to find a path towards some position where a suitable cube can be placed
    def place_nxt_block(self, source: int, target: int):
        if not self.nx_graph.is_node_realised(source):
            raise Exception(f"{source} is not placed and has no kind; cannot connect with a path.")

        if self.nx_graph.is_node_realised(target):
            raise Exception(f"{target} is already placed and has a kind.")

        clean_paths = self.pathfinder.find_target_realisation(source, target)

        # clean_paths, pathfinder_vis_data = run_pathfinder(
        #     (source_position.as_tuple(), source_kind.name.lower()),
        #     target_type.name,
        #     init_step,
        #     taken = [ position.as_tuple() for position in self.nx_graph.occupied if position != source_position ],
        #     hdm = is_hadamard,
        #     min_succ_rate = 60,
        #     src_tgt_ids = (source, target),
        #     log_stats_id = log_stats_id
        # )

        viable_paths = []

        console.debug(f"Found {len(clean_paths)} clean_paths.")

        for clean_path in clean_paths:
            (viable, beams_broken_by_path, clashes) = self.is_path_viable(source, target, clean_path)
            if not viable:
                continue

            target_kind, target_position = clean_path[-1]
            console.debug(f"> Clean path [{target_kind}@{target_position}]: {clean_path}")
            coordinates_in_path = get_taken_coords(clean_path)
            target_beams = self.compute_beams(target_kind, target_position, coordinates_in_path)
            target_unobstructed_exits = len(target_beams)

            all_nodes_in_path = [p for p in clean_path]

            # if target_type == NodeType.O:
            #     target_kind = CubeKind.OOO.name.lower()
            #     all_nodes_in_path[-1] = (all_nodes_in_path[-1][0], target_kind)

            path_data = {
                "tgt_coords": target_position,
                "tgt_kind": target_kind,
                "tgt_beams": target_beams,
                "coords_in_path": coordinates_in_path,
                "all_nodes_in_path": all_nodes_in_path,
                "beams_broken_by_path": beams_broken_by_path,
                "len_of_path": len(clean_path),
                "tgt_unobstr_exit_n": target_unobstructed_exits,
            }

            viable_paths.append(PathBetweenNodes(**path_data))

        winner_path = None
        if viable_paths:
            winner_path = max(viable_paths, key = lambda path: path.weighed_value(**kwargs))

        if winner_path is None:
            console.debug("No winner")
            return None

        source_cube = self.nx_graph.get_cube(source)
        source_kind = self.nx_graph.get_cube_kind(source_cube)
        source_position = self.nx_graph.get_cube_position(source_cube)

        edge_type = self.nx_graph.get_edge_type(source, target)

        target_kind = winner_path.tgt_kind
        target_position = winner_path.tgt_coords

        # Conversion needed for the path produced by the pathfinder.
        path = self.convert_path(winner_path.all_nodes_in_path)

        console.info(f"Winner path {source_kind}@{source_position} - {target_kind}@{target_position}] w/ extras {path}")

        if not self.nx_graph.is_path_valid(source, target_kind, target_position, edge_type, path):
            console.info(f"> Path is invalid ...")
            return None

        return target_kind, target_position, path

    def find_edge_realisation(self, source, target):
        source_cube = self.nx_graph.get_cube(source)
        target_cube = self.nx_graph.get_cube(target)
        source_position = self.nx_graph.get_cube_position(source_cube)
        target_position = self.nx_graph.get_cube_position(target_cube)

        source_kind = self.nx_graph.get_cube_kind(source_cube)
        target_type = self.nx_graph.get_node_type(target)
        target_kind = self.nx_graph.get_cube_kind(target_cube)

        edge_type = self.nx_graph.get_edge_type(source, target)

        # # TODO: deal with the critical beams (cfr. graph_manager.py Lines 301-313)
        critical_beams: dict[int, tuple[int, NodeBeams]] = {}
        for node, beams in self.node_cube_beams.items():
            unrealised_edges = self.nx_graph.get_edges_unrealised(node)
            if unrealised_edges > 0:
                critical_beams[node] = (unrealised_edges, beams)

        # # Check if edge is Hadamard
        clean_paths, pathfinder_vis_data = run_pathfinder(
            src_block_info=(source_position.as_tuple(), source_kind.name.lower()),
            tgt_zx_type=target_type.name,
            init_step=3,
            taken = [position.as_tuple() for position in self.nx_graph.occupied],
            tgt_block_info = (target_position.as_tuple(), target_kind.name.lower()),
            hdm = (edge_type == EdgeType.HADAMARD),
            min_succ_rate=60,
            critical_beams=critical_beams,
            # log_stats_id = log_stats_id,
            src_tgt_ids=(source, target)
        )

        if not clean_paths:
            return None

        return self.convert_path(clean_paths[0])

    def convert_path(self, winner_path):
        # Conversion needed for the path produced by the pathfinder.
        path = []
        for coordinates, kind in winner_path[1:-1]:
            position = Coordinates.from_tuple(coordinates)
            if BlockGraphSpace.ORIGIN.get_manhattan_distance(position) % 3 == 0:
                path.append((position, CubeKind.from_string(kind)))

        return path

    def run_pathfinder(self,
            source, target,
            init_step, min_succ_rate:int = 60,
            critical_beams: dict[int, tuple[int, NodeBeams]] = {},
            log_stats_id: str = None):
        clean_paths = []
        pathfinder_vis_data = []

        source_cube = self.nx_graph.get_cube(source)
        source_position = self.nx_graph.get_cube_position(source_cube)

        taken_cc = [ position.as_tuple() for position in self.nx_graph.occupied if position != source_position ]

        target_cube = self.nx_graph.get_cube(target)
        target_type = self.nx_graph.get_node_type(target)
        target_position = None
        if self.nx_graph.is_node_realised(target):
            target_position = self.nx_graph.get_cube_position(target_cube)
            max_step = 2 * init_step
            if target_position.as_tuple() in taken_cc:
                taken_cc.remove(target_position.as_tuple())
        else:
            max_step = 9

        edge_type = self.nx_graph.get_edge_type(source, target)

        for step in range(init_step, max_step + 1, 3):
            if target_position is not None:
                tent_coords = [target_position.as_tuple()]
            else:
                tent_coords = gen_tent_tgt_coords(
                    source_position.as_tuple(), step, [ position.as_tuple() for position in self.nx_graph.occupied ]
                )

            if tent_coords:
                valid_paths, pathfinder_vis_data = pathfinder(
                    (source_position.as_tuple(), self.nx_graph.get_cube_kind(source_cube).name),
                    tent_coords,
                    target_type.name,
                    taken=taken_cc,
                    tgt_block_info=(tent_coords[0], target_type.name),
                    hdm = (edge_type == EdgeType.HADAMARD),
                    min_succ_rate=min_succ_rate,
                    critical_beams=critical_beams,
                    src_tgt_ids=(source, target),
                    log_stats_id=log_stats_id,
                )

                # A clean_path is one that doesn't pass through a taken coordinate
                for path in valid_paths.values():
                    path_checks = True
                    for node in path:
                        if node[0] in taken_cc:
                            path_checks = False
                    if path_checks:
                        clean_paths.append(path)

                if clean_paths:
                    break

            else:
                ValueError(f"tent_coords: {tent_coords}")

        return clean_paths, pathfinder_vis_data

    def compute_beams(self, cube_kind: CubeKind, cube_position: Coordinates, extra_coordinates : list[tuple[int,int,int]] = None, beam_length: int = 99) -> NodeBeams:
        if extra_coordinates is None:
            extra_coordinates = []

        if isinstance(cube_kind, str):
            cube_kind = CubeKind.from_string(cube_kind)

        if isinstance(cube_position, tuple):
            cube_position = Coordinates.from_tuple(cube_position)

        beams: NodeBeams = []

        # cube = self.nx_graph.get_cube(node)
        # cube_kind = self.nx_graph.get_cube_kind(cube)
        cube_reach = cube_kind.get_reach()
        # cube_position = self.nx_graph.get_cube_position(cube)

        for step in cube_reach.get_step_constellation():

            beam = [] # from cube_position up to beams_len steps away

            current_position = cube_position + step
            for i in range(0, beam_length):
                if current_position in self.nx_graph.occupied or current_position.as_tuple() in extra_coordinates:
                    break

                beam_crossed = False
                for node in self.node_cube_beams.keys():
                    for other in self.node_cube_beams[node]:
                        if not any([position in extra_coordinates for position in other[:9]]):
                            if current_position.as_tuple() in other:
                                beam_crossed = True
                                break

                    if beam_crossed:
                        break

                if beam_crossed:
                    break

                beam.append(current_position.as_tuple())
                current_position += step

            # Add the beam to the list if it was completely constructed
            if len(beam) == beam_length:
                beams.append(beam)

        return beams

    def prune_beams(self):
        for node in self.nx_graph.get_nodes():
            if self.nx_graph.get_edges_realised(node) >= self.nx_graph.get_degree(node):
                self.node_cube_beams[node] = []
            elif node in self.node_cube_beams:
                new_beams = []
                for beam in self.node_cube_beams[node]:
                    if all([Coordinates.from_tuple(position) not in self.nx_graph.occupied for position in beam]):
                        new_beams.append(beam)
                self.node_cube_beams[node] = new_beams