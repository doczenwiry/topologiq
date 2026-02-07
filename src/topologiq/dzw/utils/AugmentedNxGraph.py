import logging
from collections import deque
from logging import getLogger

console = getLogger(__name__)
console.setLevel(logging.CRITICAL + 10)

import pyzx as zx
import networkx as nx

from topologiq.dzw.utils.Spacetime import Coordinates, Reach, Step
from topologiq.dzw.utils.EdgeType import EdgeType
from topologiq.dzw.utils.NodeType import NodeType
from topologiq.dzw.utils.CubeKind import CubeKind

from topologiq.dzw.helpers.SpacetimeHelper import SpacetimeHelper


# TODO: figure out what the other VertexType and EdgeType represent
# TODO: how do we deal with the last four VertexType (i.e. H_BOX, W_INPUT, W_OUTPUT, Z_BOX) ?
# TODO: do we need the last EdgeType (i.e. W_IO) ?
# TODO: how do we deal with the phase of a spider ?
# TODO: benchmarking and timing various parts
# TODO: construction of animation
class AugmentedNxGraph:
    KEY_ZX_NODE_TYPE = 'zx_node_type'
    KEY_ZX_EDGE_TYPE = 'zx_edge_type'
    KEY_ZX_EDGES_REALISED = 'zx_edges_realised'
    KEY_ZX_BG_CUBE = 'zx_bg_cube'
    KEY_ZX_BG_PATH = 'zx_bg_path'

    KEY_BG_ZX_NODE   = 'bg_zx_node'
    KEY_BG_CUBE_KIND = 'bg_cube_kind'
    KEY_BG_CUBE_POSITION = 'bg_cube_position'
    KEY_BG_PIPE_TYPE = 'bg_pipe_type'
    KEY_BG_CUBE_BEAMS = 'bg_cube_beams'

    def __init__(self, zx_graph: zx.graph.base.BaseGraph):
        super().__init__()

        # Separate ZX-graph and BG-graph
        self.__zx_graph = nx.Graph()
        self.__bg_graph = nx.Graph()

        # Keeps track of the coordinates in 3D that are occupied by some cube
        # TODO: Replace with efficient data-structure for crowded space (Binary Space Partitioning ?)
        self.occupied: set[Coordinates] = set()

        for node in zx_graph.vertices():
            self.__zx_graph.add_node(node)
            self.__zx_graph.nodes[node][AugmentedNxGraph.KEY_ZX_NODE_TYPE] = NodeType.convert(zx_graph.type(node))
            self.__zx_graph.nodes[node][AugmentedNxGraph.KEY_ZX_EDGES_REALISED] = 0
            self.__zx_graph.nodes[node][AugmentedNxGraph.KEY_ZX_BG_CUBE] = None

        for edge in zx_graph.edges():
            source = min(edge)
            target = max(edge)
            self.__zx_graph.add_edge(source, target)
            self.__zx_graph.get_edge_data(source, target)[AugmentedNxGraph.KEY_ZX_EDGE_TYPE] = EdgeType.convert(zx_graph.edge_type(edge))
            self.__zx_graph.get_edge_data(source, target)[AugmentedNxGraph.KEY_ZX_BG_PATH] = None

        self.__next_cube_id = self.__zx_graph.number_of_nodes()

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        _, max_degree = max(self.__zx_graph.degree, key=lambda entry: entry[1])
        if max_degree > 4:
            raise NotImplemented("Enforcement of no-more-than-four-legs condition not implemented.")

    def get_next_cube_id(self) -> int:
        cube_id = self.__next_cube_id
        self.__next_cube_id += 1
        return cube_id

    def get_nodes(self):
        return self.__zx_graph.nodes()

    def number_of_nodes(self) -> int:
        return self.__zx_graph.number_of_nodes()

    def get_edges(self):
        return self.__zx_graph.edges()

    def number_of_edges(self) -> int:
        return self.__zx_graph.number_of_edges()

    def get_cubes(self):
        return self.__bg_graph.nodes()

    def number_of_cubes(self) -> int:
        return self.__bg_graph.number_of_nodes()

    def get_pipes(self):
        return self.__bg_graph.edges()

    def number_of_pipes(self) -> int:
        return self.__bg_graph.number_of_edges()

    def get_edges_realised(self, node_id: int):
        return self.__zx_graph.nodes[node_id].get(AugmentedNxGraph.KEY_ZX_EDGES_REALISED)

    def get_edges_unrealised(self, node_id: int):
        return self.get_degree(node_id) - self.get_edges_realised(node_id)

    def get_neighbours(self, node_id: int):
        return self.__zx_graph.neighbors(node_id)

    def get_bg_neighbours(self, cube: int):
        return self.__bg_graph.neighbors(cube)

    def get_degree(self, node_id: int):
        return self.__zx_graph.degree[node_id]

    def is_boundary(self, node_id: int) -> bool:
        return self.get_node_type(node_id) == NodeType.O

    def is_spider(self, node_id: int) -> bool:
        return self.get_node_type(node_id) != NodeType.O

    def get_cube(self, node_id: int):
        return self.__zx_graph.nodes[node_id][AugmentedNxGraph.KEY_ZX_BG_CUBE]

    def get_node(self, cube_id: int):
        return self.__bg_graph.nodes[cube_id][AugmentedNxGraph.KEY_BG_ZX_NODE]

    def get_node_type(self, node_id: int) -> NodeType:
        return self.__zx_graph.nodes[node_id][AugmentedNxGraph.KEY_ZX_NODE_TYPE]

    def get_cube_position(self, cube_id: int) -> Coordinates:
        return self.__bg_graph.nodes[cube_id][AugmentedNxGraph.KEY_BG_CUBE_POSITION]

    def get_cube_kind(self, cube_id: int) -> CubeKind:
        return self.__bg_graph.nodes[cube_id][AugmentedNxGraph.KEY_BG_CUBE_KIND]

    def get_pipe_type(self, source_cube: int, target_cube: int):
        return self.__bg_graph.get_edge_data(source_cube, target_cube).get(AugmentedNxGraph.KEY_BG_PIPE_TYPE)

    def get_edge_type(self, source: int, target: int) -> EdgeType:
        return self.__zx_graph.get_edge_data(source, target).get(AugmentedNxGraph.KEY_ZX_EDGE_TYPE)

    def get_edge_realisation(self, source: int, target: int):
        return self.__zx_graph.get_edge_data(source, target).get(AugmentedNxGraph.KEY_ZX_BG_PATH)

    def is_node_realised(self, node_id: int) -> bool:
        return self.__zx_graph.nodes[node_id][AugmentedNxGraph.KEY_ZX_BG_CUBE] is not None

    def realise_node(self, node_id: int, kind: CubeKind, position: Coordinates):
        """Realise the node as a cube of the given kind placed at the given coordinates."""
        if kind not in CubeKind.suitable_kinds(self.get_node_type(node_id)):
            raise Exception(f"Requested {kind} is not compatible with {self.get_node_type(node_id)}")

        if not self.__zx_graph.has_node(node_id):
            raise Exception(f"Node #{node_id} not found in the ZX-graph.")

        cube_id = self.get_next_cube_id()
        console.info(f"Realising node #{node_id} [{self.get_node_type(node_id)}] as cube #{cube_id} [{kind}@{position}]")

        self.__bg_graph.add_node(cube_id)

        self.__bg_graph.nodes[cube_id][AugmentedNxGraph.KEY_BG_ZX_NODE] = node_id
        self.__zx_graph.nodes[node_id][AugmentedNxGraph.KEY_ZX_BG_CUBE] = cube_id

        self.place_cube(cube_id, position, kind)

    def find_realising_cubes(self, node: int) -> set[int]:
        if not self.is_node_realised(node):
            raise Exception(f"Node #{node} is not realised by any cube.")

        node_type = self.get_node_type(node)
        queue: deque[int] = deque([ self.get_cube(node) ])
        realising: set[int] = set()

        # TODO: explore within the BlockGraph
        while queue:
            current = queue.popleft()

            for successor in self.get_bg_neighbours(current):
                successor_type = self.get_node_type(successor)
                pipe_type = self.get_pipe_type(current, successor)
                if successor_type == node_type and pipe_type == EdgeType.IDENTITY and successor not in realising:
                    queue.append(successor)
                    realising.add(successor)

        return realising

    def is_path_valid(self, source: int, target_kind: CubeKind, target_position: Coordinates,
                      edge_type: EdgeType, extras: list[tuple[Coordinates, CubeKind]]) -> bool:
            is_hadamard_path = False

            source_cube = self.get_cube(source)
            previous_kind: CubeKind = self.get_cube_kind(source_cube)
            previous_reach: Reach = previous_kind.get_reach()
            previous_position: Coordinates = self.get_cube_position(source_cube)

            extra_positions = set()

            console.info(f"Checking path validity:")
            console.info(f"> From source : {source_cube} [{previous_kind}@{previous_position}]")
            console.info(f"> Towards target : {target_kind}@{target_position}")
            console.info(f"> With extras : {extras}")

            for (current_position, current_kind) in extras:
                current_reach = current_kind.get_reach()

                # Check that the cube type is either X or Z (Y and boundaries must be leaves)
                if current_kind.get_type() not in [NodeType.X, NodeType.Z]:
                    console.debug(f"> Current kind : {current_kind.get_type()}")
                    return False

                # Check that the step taken lies in both reaches of successive cubes
                step_taken = current_position - previous_position
                if not previous_reach.contains(step_taken) or not current_reach.contains(step_taken):
                    console.debug(f"> Previous reach contains step : {previous_reach.contains(step_taken)}")
                    console.debug(f"> Current reach contains step : {current_reach.contains(step_taken)}")
                    return False

                # Check that the current_position is not already occupied
                if current_position in self.occupied:
                    console.debug(f"> Current position is already occupied : {current_kind}@{current_position}")
                    return False

                # Check that the current_position is not already occupied by an extra cube
                if current_position in extra_positions:
                    console.debug(f"> Current position is already in path : {current_kind}@{current_position}")
                    return False
                extra_positions.add(current_position)

                # Update the type of the path based on the type of the pipe
                if SpacetimeHelper.infer_pipe_type(previous_kind, current_kind) == EdgeType.HADAMARD:
                    is_hadamard_path = not is_hadamard_path

                previous_position = current_position
                previous_kind = current_kind
                previous_reach = current_reach

            # target_kind = self.get_cube_kind(target)
            target_reach = target_kind.get_reach()
            # target_position = self.get_position(target)

            # Check that the step taken lies in both reaches of successive cubes
            step_taken = target_position - previous_position
            if not previous_reach.contains(step_taken) or not target_reach.contains(step_taken):
                console.debug(f"> Proposed path has successive cubes not within reach of each other.")
                return False

            # Update the type of the path based on the type of the pipe
            if SpacetimeHelper.infer_pipe_type(previous_kind, target_kind) == EdgeType.HADAMARD:
                is_hadamard_path = not is_hadamard_path

            if is_hadamard_path != (edge_type == EdgeType.HADAMARD):
                console.debug(f"> Proposed path is Hadamard-inconsistent with its purported edge.")

            return is_hadamard_path == (edge_type == EdgeType.HADAMARD)

    def is_edge_realised(self, source: int, target: int) -> bool:
        return self.__zx_graph.get_edge_data(source, target)[AugmentedNxGraph.KEY_ZX_BG_PATH] is not None

    # Precondition: path is a sequence of (position,kind) for the extra cubes needed to connect the source to the target
    def realise_edge(self, source: int, target: int, path: list[tuple[Coordinates, CubeKind]]):
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed; cannot connect with a path.")

        if not self.is_node_realised(target):
            raise Exception(f"{target} is not placed; cannot connect with a path.")

        if not self.__zx_graph.has_edge(source, target):
            raise Exception(f"No edge {source}-{target} found in the ZX-graph.")

        if self.is_edge_realised(source, target):
            raise Exception(f"{source}-{target} is already realized by a path.")

        source_cube = self.get_cube(source)
        target_cube = self.get_cube(target)

        # Reject path if it is invalid.
        if not self.is_path_valid(source, self.get_cube_kind(target_cube), self.get_cube_position(target_cube), self.get_edge_type(source, target), path):
            raise Exception(f"Proposed path to realise edge {source}-{target} is invalid.")

        if not path:
            sequence = "[]"
        else:
            sequence = ""
            for position, kind in path:
                sequence += f"{kind}@{position}"
        console.info(f"Realising edge {source}-{target} [type={self.get_edge_type(source,target)}] with extra cubes : {sequence}")

        # Representation of the path that will go into edge_realisations
        extras = []

        # Add all the extra cubes and pipes of the path to the BlockGraph
        previous_cube: int = source_cube
        previous_kind: CubeKind = self.get_cube_kind(source_cube)
        for (current_position, current_kind) in path:
            current_cube = self.get_next_cube_id() #len(self.__nx_graph.nodes)
            self.__bg_graph.add_node(current_cube)
            console.debug(f"> Adding cube #{current_cube} [{current_kind}@{current_position}].")
            self.__bg_graph.nodes[current_cube][AugmentedNxGraph.KEY_BG_ZX_NODE] = None
            # Place the current extra node and connect it to the previous node.
            self.place_cube(current_cube, current_position, current_kind)
            self.connect_pipe(previous_cube, current_cube, SpacetimeHelper.infer_pipe_type(previous_kind, current_kind))

            # Extend the sequence of extra node ids
            extras.append(current_cube)

            # Prepare for the next iteration
            previous_cube = current_cube
            previous_kind = current_kind

        # Make the final connection
        target_cube = self.get_cube(target)
        target_kind = self.get_cube_kind(target_cube)
        self.connect_pipe(previous_cube, target_cube, SpacetimeHelper.infer_pipe_type(previous_kind, target_kind))

        # Associate the path as a realisation of the edge
        self.__zx_graph.get_edge_data(source, target)[AugmentedNxGraph.KEY_ZX_BG_PATH] = extras

        # One more edge has been realised
        self.__zx_graph.nodes[source][AugmentedNxGraph.KEY_ZX_EDGES_REALISED] += 1
        self.__zx_graph.nodes[target][AugmentedNxGraph.KEY_ZX_EDGES_REALISED] += 1

    def place_cube(self, cube_id: int, position: Coordinates, kind: CubeKind):
        if position in self.occupied:
            raise Exception(f"Proposed {position} is already occupied by another cube.")

        self.__bg_graph.nodes[cube_id][AugmentedNxGraph.KEY_BG_CUBE_KIND] = kind
        self.__bg_graph.nodes[cube_id][AugmentedNxGraph.KEY_BG_CUBE_POSITION] = position

        self.occupied.add(position)

    def connect_pipe(self, source_cube: int, target_cube: int, pipe_type : EdgeType):
        if not self.__bg_graph.has_node(source_cube):
            raise Exception(f"Cube #{source_cube} not found in the BG-graph.")

        if not self.__bg_graph.has_node(target_cube):
            raise Exception(f"Cube #{target_cube} not found in the BG-graph.")

        if self.__bg_graph.has_edge(source_cube, target_cube):
            raise Exception(f"Cubes #{source_cube} and #{target_cube} are already connected by a pipe.")

        source_position = self.get_cube_position(source_cube)
        target_position = self.get_cube_position(target_cube)
        # TODO: replace 3 with 1 once the pathfinder has been rewritten
        if source_position.get_manhattan_distance(target_position) != 3:
            raise Exception(f"Cubes #{source_cube}@{source_position} and #{target_cube}@{target_position} are not at adjacent positions.")

        self.__bg_graph.add_edge(source_cube, target_cube)
        self.__bg_graph.get_edge_data(source_cube, target_cube)[AugmentedNxGraph.KEY_BG_PIPE_TYPE] = pipe_type