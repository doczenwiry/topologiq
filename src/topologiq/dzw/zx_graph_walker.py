import random
from collections import deque

import pyzx as zx
import networkx as nx

from topologiq.dzw.utils.CubeBeams import CubeBeams

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.helpers.spacetime_helper import SpacetimeHelper, Coordinates
from topologiq.dzw.utils.components_zx import NodeId, NodeType
from topologiq.dzw.utils.components_bg import CubeId, CubeKind
from topologiq.dzw.utils.path import Path

from topologiq.dzw.spacetime_pathfinder import SpacetimePathFinder

# TODO: remove once rewrite is done
from topologiq.utils.classes import NodeBeams

from logging import getLogger
console = getLogger(__name__)

kwargs: dict[str, tuple[int, int] | int] = {
    "weights": (-1, -1),
    "length_of_beams": 99,
}

# graph_manager.py
class ZxGraphWalker:
    def __init__(self, pyzx_graph: zx.graph.base.BaseGraph):
        self.hide_ports = False # This really belongs in the visualisation layer
        self.min_success_rate = 50
        self.nx_graph = AugmentedNxGraph(pyzx_graph)
        self.pathfinder = SpacetimePathFinder(self.nx_graph)
        self.number_1st_pass_edges = 0
        self.number_2nd_pass_edges = 0
        self.node_beams : dict[NodeId, NodeBeams] = dict()
        self.cube_beams : dict[CubeId, CubeBeams] = dict()

    def pick_root(self, central_spider: bool = True, deterministic: bool = False) -> NodeId:
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

    def construct(self, root_choice: tuple[NodeId, CubeKind] = None):
        # Prepare the root node of the construction.
        if root_choice is None:
            root = self.pick_root()
            kind = random.choice(CubeKind.suitable_kinds(self.nx_graph.get_node_type(root)))
        else:
            (root, kind) = root_choice
        root_cube = self.nx_graph.realise_node(root, kind, SpacetimeHelper.ORIGIN)
        self.node_beams[root] = self.compute_beams(kind, SpacetimeHelper.ORIGIN)
        self.cube_beams[root] = CubeBeams(kind, SpacetimeHelper.ORIGIN, occupied = self.nx_graph.occupied)

        console.info(f"Root node #{root} realised as cube #{root_cube} [{kind}@{SpacetimeHelper.ORIGIN}]")

        queue : deque[NodeId] = deque([root])

        # Proceed with the main loop of the BFS
        while queue:
            current_node: NodeId = queue.popleft()

            for neighbour_node in self.nx_graph.get_node_neighbours(current_node):
                if self.nx_graph.is_edge_realised(current_node, neighbour_node):
                    console.info(f"Ignoring edge {current_node}-{neighbour_node}")
                    continue

                proposed_path: Path | None = None

                if not self.nx_graph.is_node_realised(neighbour_node):
                    # First-pass edge
                    # Goal: find a path to some position where a suitable cube can be placed within some maximal MD
                    console.info(f"Processing edge {current_node}-{neighbour_node} : Pass #1")

                    proposed_path = self.find_target_realisation(current_node, neighbour_node)

                    if proposed_path is None:
                        raise Exception(f"> Target realisation failure : neither kind nor placement found.")

                    proposed_kind = proposed_path.get_target_kind()
                    proposed_position = proposed_path.get_target_position()

                    # Realise the target node as a cube with kind and position provided by the pathfinder
                    target_cube = self.nx_graph.realise_node(neighbour_node, proposed_kind, proposed_position)
                    proposed_path.set_target_cube(target_cube)

                    self.prune_beams_by_cube(neighbour_node)
                    self.prune_beams()

                    console.info(f"Realised node #{neighbour_node} as cube #{target_cube} [{proposed_kind}@{proposed_position}]")

                    # Compute the beams for the new target cube only for X and Z nodes.
                    if self.nx_graph.get_node_type(neighbour_node) in [ NodeType.X, NodeType.Z ]:
                        self.node_beams[neighbour_node] = self.compute_beams(proposed_kind, proposed_position)
                        self.cube_beams[neighbour_node] = CubeBeams(proposed_kind, proposed_position, occupied = self.nx_graph.occupied)

                    self.number_1st_pass_edges += 1
                    queue.append(neighbour_node)
                elif not self.nx_graph.is_edge_realised(current_node, neighbour_node):
                    # Second-pass edge
                    # Goal: find a path towards the position of a cube representing the target node
                    console.info(f"Processing edge {current_node}-{neighbour_node} : Pass #2")

                    proposed_path = self.find_edge_realisation(current_node, neighbour_node)

                    if proposed_path is None:
                        raise Exception(f"> Edge realisation failure : no path found.")

                    self.number_2nd_pass_edges += 1

                # Realise the edge using the path
                self.nx_graph.realise_edge(current_node, neighbour_node, proposed_path)

                self.prune_beams_by_path(proposed_path.get_extra_cubes())

                # Incorporate the positions that are occupied by the extra cubes in the path
                for _, position in proposed_path.get_extra_cubes():
                    self.nx_graph.occupied.add(position)

                self.prune_beams()

        console.info(f"Construction completed.")

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
        source: NodeId, target: NodeId, target_kind: CubeKind, target_position: Coordinates,
        extras: list[tuple[CubeKind, Coordinates]]
    ) -> tuple[bool, int]:

        console.debug(f"Checking validity of proposed path [{target_kind}@{target_position}]: {extras}")
        target_beams = CubeBeams(target_kind, target_position, extras = extras, occupied = self.nx_graph.occupied)
        beams_remaining = target_beams.number_available()
        edges_unrealised = self.nx_graph.get_degree(target) - 1

        if target_kind == CubeKind.OOO:
            beams_remaining, target_beams = (6, [])
            old_extras = [position.as_tuple() for _, position in extras]
            old_target_beams = self.compute_beams(target_kind, target_position, old_extras)
        else:
            old_target_beams = []

        total_beams_interrupted = 0

        if beams_remaining < edges_unrealised:
            console.debug(f"> Target node #{target} has {edges_unrealised} unrealised edges for {beams_remaining} beams.")
            return False, total_beams_interrupted

        egress_position = extras[0][1].as_tuple() if len(extras) > 0 else target_position.as_tuple()
        if not any([egress_position in beam for beam in self.node_beams[source]]):
            console.debug(f"> Egress cube is not connected to a beam at the source node #{source}. [beams={ZxGraphWalker.format_beams(self.node_beams[source])}]")
            return False, total_beams_interrupted

        # Deal with the constraints on beams
        critical_interruption = False
        critical_intersection = False
        for node, beams in self.cube_beams.items():
            if node == source or node == target:
                continue

            cube = self.nx_graph.get_cube(node)
            cube_position = self.nx_graph.get_cube_position(cube)
            edges_unrealised = self.nx_graph.get_edges_unrealised(node)

            # Determine whether the current cube has too many beams interrupted by cubes from the path
            lines_of_sight = set()
            for _, position in extras:
                if cube_position.colinear(position):
                    lines_of_sight.add( SpacetimeHelper.get_line_of_sight(cube_position, position) )
            if cube_position.colinear(target_position):
                lines_of_sight.add( SpacetimeHelper.get_line_of_sight(cube_position, target_position) )

            beams_interrupted  = beams.count_interrupted(lines_of_sight)
            beams_remaining = beams.number_available() - beams_interrupted
            console.debug(f"> Interrupting {beams_interrupted} beams of node #{node} [{beams}]")
            console.debug(f">> Node beams : {self.node_beams[node]}")
            total_beams_interrupted += beams_interrupted
            if beams_remaining < edges_unrealised:
                console.debug(f"BRK> Node #{node} has {edges_unrealised} unrealised edges for {beams_remaining} beams.")
                critical_interruption = True

            # Determine whether the current cube has too many beams intersected by those of the target cube
            old_node_beams = self.node_beams[node]
            beams_intersected = beams.old_count_intersected(old_node_beams, old_target_beams)
            beams_remaining = beams.number_available() - beams_intersected
            if beams_remaining < edges_unrealised:
                console.debug(f"CLH> Node #{node} has {edges_unrealised} unrealised edges for {beams_remaining} beams.")
                critical_intersection = True

        viable = not critical_interruption and not critical_intersection
        return viable, total_beams_interrupted

    def find_target_realisation(self, source: NodeId, target: NodeId):
        if not self.nx_graph.is_node_realised(source):
            raise Exception(f"{source} is not placed and has no kind; cannot connect with a path.")

        if self.nx_graph.is_node_realised(target):
            raise Exception(f"{target} is already placed and has a kind.")

        edge_type = self.nx_graph.get_edge_type(source, target)
        proposed_paths = self.pathfinder.find_target_realisation(source, target)
        console.info(f"Pathfinder proposed {len(proposed_paths)} paths.")

        viable_paths = []
        for proposed_path in proposed_paths:
            console.debug(f"> Proposed target : {proposed_path.get_target_kind()}@{proposed_path.get_target_position()}")
            console.debug(f"> Proposed cubes : {proposed_path.get_cubes()}")
            proposed_kind, proposed_position = proposed_path.get_cubes()[-1]
            proposed_extras = proposed_path.get_cubes()[1:-1]
            viable_path, total_beams_interrupted = self.is_path_viable(
                source, target, proposed_kind, proposed_position, proposed_extras
            )

            if viable_path:
                console.debug(f"> Viable path [{proposed_kind}@{proposed_position}]: {proposed_extras}")
                proposed_path.set_cube_beams(CubeBeams(
                    proposed_kind, proposed_position, extras = proposed_extras, occupied = self.nx_graph.occupied
                ))
                proposed_path.set_total_beams_interrupted(total_beams_interrupted)
                viable_paths.append(proposed_path)

        console.debug(f"Found {len(viable_paths)} viable_paths.")

        winner_path : Path | None = None
        if viable_paths:
            winner_path = max(viable_paths, key = lambda p: p.weight())

        for vp in viable_paths:
            console.debug(f"> Path weight [{vp}] : {vp.weight()}")

        if winner_path is None:
            console.debug("No winner")

        source_cube = self.nx_graph.get_cube(source)
        source_kind = self.nx_graph.get_cube_kind(source_cube)
        source_position = self.nx_graph.get_cube_position(source_cube)

        console.info(f"Winner path {source_kind}@{source_position}")
        console.info(f"> Proposed target : {winner_path.get_target_kind()}@{winner_path.get_target_position()}")
        console.info(f"> Proposed cubes  : {winner_path.get_cubes()}")
        console.info(f"> Proposed pipes  : {winner_path.get_pipes()}")

        return winner_path

    def find_edge_realisation(self, source: NodeId, target: NodeId) -> Path | None:
        proposed_paths = self.pathfinder.find_edge_realisation(source, target, node_beams = self.node_beams)

        console.info(f"Pathfinder proposed {len(proposed_paths)} paths.")

        if not proposed_paths:
            return None

        for proposed_path in proposed_paths:
            console.debug(f"> Proposed path {proposed_path}")

        return proposed_paths[0]

    def compute_beams(self,
        cube_kind: CubeKind, cube_position: Coordinates,
        extra_coordinates : list[tuple[int,int,int]] = None, beam_length: int = 99
    ) -> NodeBeams:
        if extra_coordinates is None:
            extra_coordinates = []

        node_beams: NodeBeams = []
        cube_reach = cube_kind.get_reach()

        console.debug(f"Computing beams [{cube_kind}@{cube_position}] : {SpacetimeHelper.get_step_constellation(cube_reach)}")
        console.debug(f"> Occupied : {self.nx_graph.occupied}")
        for step in SpacetimeHelper.get_step_constellation(cube_reach):

            beam = [] # from cube_position up to beams_len steps away

            current_position = cube_position + step
            for i in range(0, beam_length):
                if current_position in self.nx_graph.occupied or current_position.as_tuple() in extra_coordinates:
                    console.debug(f"> Current position {current_position} already occupied.")
                    break

                beam_crossed = False
                for node, beams in self.node_beams.items():
                    for other in beams:
                        if not any([position in extra_coordinates for position in other]):
                            if current_position.as_tuple() in other:
                                console.debug(f"> Current position {current_position} in other #{node} : {other}.")
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
            else:
                console.debug(f"> Ignoring beam for step {step}")

        console.debug(f"Computed Beams:")
        console.debug(f"> Node beams : {ZxGraphWalker.format_beams(node_beams)}")

        return node_beams

    def prune_beams_by_cube(self, target):
        if not self.nx_graph.is_node_realised(target):
            raise Exception(f"Node #{target} is not realised and thus has no beams.")

        target_cube = self.nx_graph.get_cube(target)
        target_position = self.nx_graph.get_cube_position(target_cube)

        for node, beams in self.cube_beams.items():
            cube = self.nx_graph.get_cube(node)
            if cube == target_cube:
                continue

            console.debug(f"> Pruning beams of node #{node} by target #{target}")

            cube_position = self.nx_graph.get_cube_position(cube)
            if cube_position.colinear(target_position):
                los = SpacetimeHelper.get_line_of_sight(cube_position, target_position)
                console.debug(f">> Cube @{cube_position} colinear with {target_position} : {los}")
                beams.close_beam( los )

    def prune_beams_by_path(self, path):
        for node, beams in self.cube_beams.items():
            cube = self.nx_graph.get_cube(node)
            cube_position = self.nx_graph.get_cube_position(cube)
            for _, position in path:
                if cube_position.colinear(position):
                    beams.close_beam( SpacetimeHelper.get_line_of_sight(cube_position, position) )

    def prune_beams(self):
        for node, beams in self.node_beams.items():
            if self.nx_graph.get_edges_realised(node) >= self.nx_graph.get_degree(node):
                self.node_beams[node] = []
            else:
                console.debug(f"Pruning beams of node #{node}:")
                console.debug(f"> Old node beams : {ZxGraphWalker.format_beams(beams)}")
                new_node_beams = []
                for beam in beams:
                    if all([Coordinates.from_tuple(position) not in self.nx_graph.occupied for position in beam]):
                        new_node_beams.append(beam)

                console.debug(f"> New node beams : {ZxGraphWalker.format_beams(new_node_beams)}")

                self.node_beams[node] = new_node_beams