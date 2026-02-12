import random
from collections import deque

import pyzx as zx
import networkx as nx

from topologiq.dzw.utils.CubeBeams import CubeBeams

from topologiq.dzw.utils.AugmentedNxGraph import AugmentedNxGraph
from topologiq.dzw.utils.Spacetime import Spacetime, Coordinates
from topologiq.dzw.utils.CubeKind import CubeKind
from topologiq.dzw.utils.NodeType import NodeType

from topologiq.dzw.SpacetimePathFinder import SpacetimePathFinder

# TODO: remove once rewrite is done
from topologiq.scripts.pathfinder import get_taken_coords
from topologiq.utils.classes import NodeBeams, PathBetweenNodes

from logging import getLogger
console = getLogger(__name__)

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
        self.node_beams : dict[int, NodeBeams] = dict()
        self.cube_beams : dict[int, CubeBeams] = dict()

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
        root_cube = self.nx_graph.realise_node(root, kind, Spacetime.ORIGIN)
        node_beams = self.compute_beams(kind, Spacetime.ORIGIN)
        cube_beams = CubeBeams(kind, Spacetime.ORIGIN, occupied = self.nx_graph.occupied)
        self.node_beams[root] = node_beams
        self.cube_beams[root_cube] = cube_beams

        self.node_realisation_order.append(root)

        queue : deque[int] = deque([root])

        # Proceed with the main loop of the BFS
        while queue:
            source: int = queue.popleft()

            for target in self.nx_graph.get_neighbours(source):
                if self.nx_graph.is_edge_realised(source, target):
                    console.info(f"Ignoring edge {source}-{target}")
                    continue

                path: list[tuple[CubeKind, Coordinates]] | None = None

                if not self.nx_graph.is_node_realised(target):
                    # First-pass edge
                    # Goal: find a path to some position where a suitable cube can be placed within some maximal MD
                    console.info(f"Processing edge {source}-{target} : Pass #1")

                    (target_kind, target_position, path) = self.find_target_realisation(source, target)

                    if target_kind is None or target_position is None:
                        raise Exception(f"> Target realisation failure : neither kind nor placement found.")

                    # Realise the target node as a cube with kind and position provided by the pathfinder
                    target_cube = self.nx_graph.realise_node(target, target_kind, target_position)
                    self.node_realisation_order.append(target)

                    # Compute the beams for the new target cube only for X and Z nodes.
                    if self.nx_graph.get_node_type(target) in [ NodeType.X, NodeType.Z ]:
                        self.node_beams[target] = self.compute_beams(target_kind, target_position)
                        self.cube_beams[target_cube] = CubeBeams(target_kind, target_position, occupied = self.nx_graph.occupied)
                        self.prune_beams_by_cube(target)

                    if path is None:
                        raise Exception(f"> Edge realisation failure : no path found.")

                    self.number_1st_pass_edges += 1
                    queue.append(target)
                elif not self.nx_graph.is_edge_realised(source, target):
                    # Second-pass edge
                    # Goal: find a path towards the position of a cube representing the target node
                    console.info(f"Processing edge {source}-{target} : Pass #2")

                    path = self.find_edge_realisation(source, target)

                    if path is None:
                        raise Exception(f"> Edge realisation failure : no path found.")

                    self.number_2nd_pass_edges += 1

                # Realise the edge using the path
                self.nx_graph.realise_edge(source, target, path)

                # Store the path that realises the current edge
                self.edge_realisation_order.append( (source,target) )

                self.prune_beams_by_path(path)

                # Incorporate the positions that are occupied by the extra cubes in the path
                for _, position in path:
                    self.nx_graph.occupied.add(position)

                self.prune_beams()

        # Prepare final BlockGraph and return it ?
        return True

    @staticmethod
    def format_beam(beam: list[tuple[int,int,int]]):
        return f"{beam[0]}-{beam[-1]},"

    @staticmethod
    def format_beams(beams: NodeBeams):
        formatted  = "["
        for beam in beams:
            formatted += ZxGraphWalker.format_beam(beam)
        formatted += "]"
        return formatted

    def is_path_viable(self,
        source, target, target_kind, target_position,
        extras: list[tuple[CubeKind, Coordinates]]
    ) -> tuple[bool, int]:

        console.debug(f"Checking validity of proposed path [{target_kind}@{target_position}]: {extras}")
        target_beams = CubeBeams(target_kind, target_position, extras = extras, occupied = self.nx_graph.occupied)
        beams_remaining = target_beams.number_available()
        edges_unrealised = self.nx_graph.get_degree(target) - 1

        if target_kind == CubeKind.OOO:
            beams_remaining, target_beams = (6, [])

        total_beams_interrupted = 0

        if beams_remaining < edges_unrealised:
            console.debug(f"Target node #{target} has {edges_unrealised} unrealised edges for {beams_remaining} beams.")
            return False, total_beams_interrupted

        egress_position = extras[0][1].as_tuple() if len(extras) > 0 else target_position.as_tuple()
        if not any([egress_position in beam for beam in self.node_beams[source]]):
            console.debug(f"Egress cube is not connected to a beam at the source node #{source}.")
            return False, total_beams_interrupted

        # Deal with the constraints on beams
        critical_interruption = False
        critical_intersection = False
        for cube, beams in self.cube_beams.items():
            node = self.nx_graph.get_node(cube)
            cube_position = self.nx_graph.get_cube_position(cube)
            edges_unrealised = self.nx_graph.get_edges_unrealised(node)

            # Determine whether the current node has too many beams interrupted by cubes from the path
            lines_of_sight = set()
            for _, position in extras:
                if cube_position.colinear(position):
                    lines_of_sight.add( cube_position.get_line_of_sight(position) )
            if cube_position.colinear(target_position):
                lines_of_sight.add( cube_position.get_line_of_sight(target_position) )

            beams_interrupted  = beams.count_interrupted(lines_of_sight)
            beams_remaining = beams.number_available() - beams_interrupted
            total_beams_interrupted += beams_interrupted
            if beams_remaining < edges_unrealised:
                console.debug(f"BRK> Node #{node} has {edges_unrealised} unrealised edges for {beams_remaining} beams.")
                critical_interruption = True

            # Determine whether the current node has too many beams intersected by those of the target cube
            if node == source or node == target:
                continue

            node_beams = self.node_beams[node]
            beams_intersected = beams.count_intersected(node_beams, target_beams)
            beams_remaining = beams.number_available() - beams_intersected
            if beams_remaining < edges_unrealised:
                console.debug(f"CLH> Node #{node} has {edges_unrealised} unrealised edges for {beams_remaining} beams.")
                critical_intersection = True

        viable = not critical_interruption and not critical_intersection
        return viable, total_beams_interrupted

    def find_target_realisation(self, source: int, target: int):
        if not self.nx_graph.is_node_realised(source):
            raise Exception(f"{source} is not placed and has no kind; cannot connect with a path.")

        if self.nx_graph.is_node_realised(target):
            raise Exception(f"{target} is already placed and has a kind.")

        proposed_paths = self.pathfinder.find_target_realisation(source, target)
        console.info(f"Pathfinder proposed {len(proposed_paths)} paths.")

        viable_paths = []
        for proposed_path in proposed_paths:
            proposed_target_kind, proposed_target_position = proposed_path[-1]
            proposed_extras = proposed_path[1:-1]
            viable, total_beams_interrupted = self.is_path_viable(
                source, target, proposed_target_kind, proposed_target_position, proposed_extras
            )
            if not viable:
                continue

            console.debug(f"> Proposed path [{proposed_target_kind}@{proposed_target_position}]: {proposed_path}")
            target_beams = CubeBeams(proposed_target_kind, proposed_target_position, extras= proposed_path, occupied = self.nx_graph.occupied)
            target_unobstructed_exits = target_beams.number_available()

            all_nodes_in_path = [p for p in proposed_path]

            path_data = {
                "tgt_coords": proposed_target_position,
                "tgt_kind": proposed_target_kind,
                "tgt_beams": target_beams,
                "coords_in_path": get_taken_coords(proposed_path),
                "all_nodes_in_path": all_nodes_in_path,
                "beams_broken_by_path": total_beams_interrupted,
                "len_of_path": len(proposed_path),
                "tgt_unobstr_exit_n": target_unobstructed_exits,
            }

            viable_paths.append(PathBetweenNodes(**path_data))

        console.debug(f"Found {len(viable_paths)} viable_paths.")

        winner_path = None
        if viable_paths:
            winner_path = max(viable_paths, key = lambda path: path.weighed_value(**kwargs))

        if winner_path is None:
            console.debug("No winner")
            return None, None, None

        source_cube = self.nx_graph.get_cube(source)
        source_kind = self.nx_graph.get_cube_kind(source_cube)
        source_position = self.nx_graph.get_cube_position(source_cube)

        edge_type = self.nx_graph.get_edge_type(source, target)

        proposed_target_kind = winner_path.tgt_kind
        if isinstance(proposed_target_kind, str):
            proposed_target_kind = CubeKind.from_string(proposed_target_kind)
        proposed_target_position = winner_path.tgt_coords

        # Conversion needed for the path produced by the pathfinder.
        proposed_path = winner_path.all_nodes_in_path[1:-1]

        console.info(f"Winner path {source_kind}@{source_position} - {proposed_target_kind}@{proposed_target_position}] w/ extras {proposed_path}")

        if not self.nx_graph.is_path_valid(source, proposed_target_kind, proposed_target_position, edge_type, proposed_path):
            console.info(f"> Path is invalid ...")
            return None, None, None

        return proposed_target_kind, proposed_target_position, proposed_path

    def find_edge_realisation(self, source, target):
        # # TODO: deal with the critical beams (cfr. graph_manager.py Lines 301-313)
        critical_beams: dict[int, tuple[int, NodeBeams]] = {}
        for node, beams in self.node_beams.items():
            unrealised_edges = self.nx_graph.get_edges_unrealised(node)
            if unrealised_edges > 0:
                critical_beams[node] = (unrealised_edges, beams)

        # TODO: take into account whether the edge has HADAMARD type
        clean_paths = self.pathfinder.find_edge_realisation(source, target, critical = critical_beams)

        if not clean_paths:
            return None

        return clean_paths[0][1:-1]

    def compute_beams(self,
        cube_kind: CubeKind, cube_position: Coordinates,
        extra_coordinates : list[tuple[int,int,int]] = None, beam_length: int = 99
    ) -> NodeBeams:
        if extra_coordinates is None:
            extra_coordinates = []

        node_beams: NodeBeams = []
        cube_reach = cube_kind.get_reach()

        console.debug(f"Computing beams [{cube_kind}@{cube_position}] : {cube_reach.get_step_constellation()}")
        console.debug(f"> Occupied : {self.nx_graph.occupied}")
        for step in cube_reach.get_step_constellation():

            beam = [] # from cube_position up to beams_len steps away

            current_position = cube_position + step
            for i in range(0, beam_length):
                if current_position in self.nx_graph.occupied or current_position.as_tuple() in extra_coordinates:
                    break

                beam_crossed = False
                for node in self.node_beams.keys():
                    for other in self.node_beams[node]:
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
                console.debug(f"> Appending beam : {ZxGraphWalker.format_beam(beam)}")
                node_beams.append(beam)

        console.debug(f"Computed Beams:")
        console.debug(f"> Node beams : {ZxGraphWalker.format_beams(node_beams)}")

        return node_beams

    def prune_beams_by_cube(self, target):
        if not self.nx_graph.is_node_realised(target):
            raise Exception(f"Node #{target} is not realised and thus has no beams.")

        target_cube = self.nx_graph.get_cube(target)
        if target_cube not in self.cube_beams:
            target_kind = self.nx_graph.get_cube_kind(target_cube)
            target_position = self.nx_graph.get_cube_position(target_cube)
            console.warning(f"Cube {target_kind}@{target_position} realising node #{target} has no beams.")
            return

        target_position = self.nx_graph.get_cube_position(target_cube)
        for cube, beams in self.cube_beams.items():
            if cube == target_cube:
                continue

            cube_position = self.nx_graph.get_cube_position(cube)
            if cube_position.colinear(target_position):
                beams.close_beam( cube_position.get_line_of_sight(target_position) )

    def prune_beams_by_path(self, path):
        for cube, beams in self.cube_beams.items():
            cube_position = self.nx_graph.get_cube_position(cube)
            for _, position in path:
                if cube_position.colinear(position):
                    beams.close_beam( cube_position.get_line_of_sight(position) )

    def prune_beams(self):
        for node in self.nx_graph.get_nodes():
            if node in self.node_beams.keys() and self.nx_graph.get_edges_realised(node) >= self.nx_graph.get_degree(node):
                self.node_beams[node] = []
            elif node in self.node_beams:
                new_node_beams = []
                for beam in self.node_beams[node]:
                    if all([Coordinates.from_tuple(position) not in self.nx_graph.occupied for position in beam]):
                        new_node_beams.append(beam)

                console.debug(f"Pruned Beams:")
                console.debug(f"> New node beams : {ZxGraphWalker.format_beams(new_node_beams)}")

                self.node_beams[node] = new_node_beams