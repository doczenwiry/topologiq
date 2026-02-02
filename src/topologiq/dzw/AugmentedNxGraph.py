import pyzx as zx
import networkx as nx

from topologiq.dzw.BlockGraphSpace import Coordinates, Reach, Step
from topologiq.dzw.ZxGraphComponents import NodeType, EdgeType
from topologiq.dzw.BlockGraphComponents import CubeKind
from topologiq.utils.utils_pathfinder import check_exits

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

    KEY_BG_CUBE_KIND = 'bg_cube_kind'
    KEY_BG_CUBE_POSITION = 'bg_cube_position'
    KEY_OLD_BEAMS = 'beams'

    # These are here only for compatibility with the current implementation of graph_manager and pathfinder.
    # TODO: remove when rewrite is complete
    OLD_LENGTH_OF_BEAMS = 99
    KEY_OLD_CUBE_KIND = 'kind'
    KEY_OLD_NODE_TYPE = 'type'
    KEY_OLD_EDGE_TYPE = 'type'
    KEY_OLD_COMPLETED = 'completed'
    KEY_OLD_COORDINATES = 'coords'

    def __init__(self, zx_graph: zx.graph.base.BaseGraph):
        super().__init__()

        # Original implementation
        self.__nx_graph = nx.Graph()
        # Separate ZX-graph and BG-graph
        self.__zx_graph = nx.Graph()
        self.__bg_graph = nx.Graph()

        # Keeps track of the coordinates in 3D that are occupied by some cube
        # TODO: Replace with efficient data-structure for crowded space (Binary Space Partitioning ?)
        self.occupied: set[Coordinates] = set()
        # TODO: remove old_taken rewrite is complete
        self.old_taken: set[tuple[int,int,int]] = set()
        # Keeps track of the paths (i.e. one or more pipes) in the BlockGraph that realise the edges of the ZX-graph
        self.edge_realisations: dict = {}
        # Keeps track of the order in which nodes from the ZX-graph were placed for visualisation purposes
        self.placement_order : list[int] = []

        for node in zx_graph.vertices():
            self.__zx_graph.add_node(node)
            self.__zx_graph.nodes[node][AugmentedNxGraph.KEY_ZX_NODE_TYPE] = NodeType.convert(zx_graph.type(node))
            self.__zx_graph.nodes[node][AugmentedNxGraph.KEY_ZX_EDGES_REALISED] = 0
            self.__zx_graph.nodes[node][AugmentedNxGraph.KEY_ZX_BG_CUBE] = None

            self.__nx_graph.add_node(node)
            self.__nx_graph.nodes[node][AugmentedNxGraph.KEY_OLD_BEAMS] = None
            self.__nx_graph.nodes[node][AugmentedNxGraph.KEY_OLD_NODE_TYPE] = zx_graph.type(node).name
            self.__nx_graph.nodes[node][AugmentedNxGraph.KEY_OLD_CUBE_KIND] = None
            self.__nx_graph.nodes[node][AugmentedNxGraph.KEY_OLD_COMPLETED] = 0
            self.__nx_graph.nodes[node][AugmentedNxGraph.KEY_OLD_COORDINATES] = None

        for edge in zx_graph.edges():
            source = min(edge)
            target = max(edge)
            self.__nx_graph.add_edge(source, target)
            self.__nx_graph.get_edge_data(source, target)[AugmentedNxGraph.KEY_OLD_EDGE_TYPE] = zx_graph.edge_type(edge).name

            self.__zx_graph.add_edge(source, target)
            self.__zx_graph.get_edge_data(source, target)[AugmentedNxGraph.KEY_ZX_EDGE_TYPE] = EdgeType.convert(zx_graph.edge_type(edge))

        self.__next_cube_id = self.__zx_graph.number_of_nodes()

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        _, max_degree = max(self.__nx_graph.degree, key=lambda entry: entry[1])
        if max_degree > 4:
            raise NotImplemented("Enforcement of no-more-than-four-legs condition not implemented.")

    def get_nodes(self):
        return self.__nx_graph.nodes()

    def number_of_nodes(self) -> int:
        return self.__nx_graph.number_of_nodes()

    def get_edges(self):
        return self.__nx_graph.edges()

    def number_of_edges(self) -> int:
        return self.__nx_graph.number_of_edges()

    # TODO: remove once encapsulation is complete
    def get_nx_graph(self):
        return self.__nx_graph

    def get_neighbours(self, node_id: int):
        return self.__nx_graph.neighbors(node_id)

    def get_degrees(self):
        return self.__nx_graph.degree

    def is_boundary(self, node_id: int) -> bool:
        return self.get_node_type(node_id) == NodeType.O

    def is_spider(self, node_id: int) -> bool:
        return self.get_node_type(node_id) != NodeType.O

    def get_cube(self, node_id: int):
        return self.__zx_graph.nodes[node_id][AugmentedNxGraph.KEY_ZX_BG_CUBE]

    def get_position(self, node_id: int) -> Coordinates:
        return Coordinates.from_tuple(self.__nx_graph.nodes[node_id][AugmentedNxGraph.KEY_OLD_COORDINATES])

    def set_position(self, node_id: int, position: Coordinates):
        self.__zx_graph.nodes[node_id][AugmentedNxGraph.KEY_BG_CUBE_POSITION] = position
        self.__nx_graph.nodes[node_id][AugmentedNxGraph.KEY_OLD_COORDINATES] = position.as_tuple()

    def get_node_type(self, node_id: int) -> NodeType:
        return self.__zx_graph.nodes[node_id][AugmentedNxGraph.KEY_ZX_NODE_TYPE]

    def set_node_type(self, node_id: int, node_type: NodeType):
        self.__zx_graph.nodes[node_id][AugmentedNxGraph.KEY_ZX_NODE_TYPE] = node_type
        self.__nx_graph.nodes[node_id][AugmentedNxGraph.KEY_OLD_NODE_TYPE] = node_type.name

    def get_cube_kind(self, node_id: int) -> CubeKind:
        return CubeKind.from_string(self.__nx_graph.nodes[node_id][AugmentedNxGraph.KEY_OLD_CUBE_KIND])

    def get_edge_type(self, source: int, target: int) -> EdgeType:
        return self.__zx_graph.get_edge_data(source, target).get(AugmentedNxGraph.KEY_ZX_EDGE_TYPE)

    # TODO: move consistency checking to Cube classes (recommendation from J)
    def get_candidate_adjacent(self, source: int, pipe_type: EdgeType) -> list[tuple[Step, CubeKind]]:
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed and thus has no kind. Cannot determine its adjacent candidates.")

        if self.get_node_type(source) not in [NodeType.X, NodeType.Z]:
            raise NotImplemented(f"NodeType {self.get_node_type(source)} not supported.")

        source_kind = self.get_cube_kind(source)

        return source_kind.get_candidate_constellation(pipe_type)

    # TODO: provide number of unobstructed ports, number of legs, information to check the beams
    def get_unobstructed_ports(self, node_id: int) -> int:
        return 0

    def is_node_realised(self, node_id: int) -> bool:
        has_position = self.__nx_graph.nodes[node_id][AugmentedNxGraph.KEY_OLD_COORDINATES] is not None
        has_cubekind = self.__nx_graph.nodes[node_id][AugmentedNxGraph.KEY_OLD_CUBE_KIND] is not None
        return has_position and has_cubekind

    def realise_node(self, node_id: int, kind: CubeKind, position: Coordinates):
        """Realise the node as a cube of the given kind placed at the given coordinates."""
        if kind not in CubeKind.suitable_kinds(self.get_node_type(node_id)):
            raise Exception(f"Requested {kind} is not compatible with {self.get_node_type(node_id)}")

        if not self.__zx_graph.has_node(node_id):
            raise Exception(f"Node #{node_id} not found in the ZX-graph.")

        # TODO: compute the beams of the new cube
        # TODO: prune the beams of other cubes
        # # Compute beams
        # _, node_beams = check_exits(
        #     position.as_tuple(),
        #     kind.name,
        #     list(self.old_taken),
        #     # [position.as_tuple()],
        #     [],
        #     self,
        #     AugmentedNxGraph.OLD_LENGTH_OF_BEAMS,
        # )
        # self.nx_graph.nodes[node_id][AugmentedNxGraph.KEY_BEAMS] = node_beams

        self.place_cube(node_id, position, kind)

    def is_edge_realised(self, source: int, target: int) -> bool:
        edge = (source, target) if source < target else (target, source)
        return edge in self.edge_realisations

    def is_path_valid(self, source: int, target: int, path: list[tuple[Coordinates, CubeKind]]) -> bool:
            is_hadamard_path = False

            previous_kind: CubeKind = self.get_cube_kind(source)
            previous_reach: Reach = previous_kind.get_reach()
            previous_position: Coordinates = self.get_position(source)

            for (current_position, current_kind) in path:
                current_reach = current_kind.get_reach()

                # Check that the step taken lies in both planes of successive cubes
                step_taken = current_position - previous_position
                if not previous_reach.contains(step_taken) or not current_reach.contains(step_taken):
                    return False

                # Check that the current_position is not already occupied
                if current_position in self.occupied:
                    return False

                # Update the type of the path based on the type of the pipe
                if CubeKind.infer_pipe_type(previous_kind, current_kind) == EdgeType.HADAMARD:
                    is_hadamard_path = not is_hadamard_path

                previous_position = current_position
                previous_kind = current_kind
                previous_reach = current_reach

            target_kind = self.get_cube_kind(target)
            target_reach = target_kind.get_reach()
            target_position = self.get_position(target)

            # Check that the step taken lies in both planes of successive cubes
            step_taken = target_position - previous_position
            if not previous_reach.contains(step_taken) or not target_reach.contains(step_taken):
                return False

            # Update the type of the path based on the type of the pipe
            if CubeKind.infer_pipe_type(previous_kind, target_kind) == EdgeType.HADAMARD:
                is_hadamard_path = not is_hadamard_path

            return is_hadamard_path != (self.get_edge_type(source, target) == EdgeType.HADAMARD)

    # Precondition: path is a sequence of (position,kind) for the extra cubes needed to connect the source to the target
    def realise_edge(self, source: int, target: int, path: list[tuple[Coordinates, CubeKind]]):
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed; cannot connect with a path.")

        if not self.is_node_realised(target):
            raise Exception(f"{target} is not placed; cannot connect with a path.")

        if self.__nx_graph.edges[source, target] is None:
            raise Exception(f"No edge {source}-{target} found in the ZX-graph.")

        if self.is_edge_realised(source, target):
            raise Exception(f"{source}-{target} is already realized by a path.")

        # Check path validity w.r.t. CubeKinds
        # Check path does not place an extra cube at some occupied position
        if not self.is_path_valid(source, target, path):
            return False

        # Representation of the path that will go into edge_realisations
        extras = []

        # Add all the extra cubes and pipes of the path to the BlockGraph
        previous: int = source
        previous_kind: CubeKind = self.get_cube_kind(source)
        for (current_position, current_kind) in path:
            current = len(self.__nx_graph.nodes)
            self.__nx_graph.add_node(current)
            # Place the current extra node and connect it to the previous node.
            self.place_cube(current, current_position, current_kind)
            pipe_type = CubeKind.infer_pipe_type(previous_kind, current_kind)
            self.connect_pipe(previous, current, pipe_type)

            # Extend the sequence of extra node ids
            extras.append(current)

            # Prepare for the next iteration
            previous = current
            previous_kind = current_kind

        # Make the final connection
        pipe_type = CubeKind.infer_pipe_type(previous_kind, self.get_cube_kind(target))
        self.connect_pipe(previous, target, pipe_type)
        # Associate the path as a realisation of the edge
        edge = (source, target) if source < target else (target, source)
        self.edge_realisations[edge] = extras

        # One more edge has been realised
        self.__nx_graph.nodes[source][AugmentedNxGraph.KEY_OLD_COMPLETED] += 1
        self.__nx_graph.nodes[target][AugmentedNxGraph.KEY_OLD_COMPLETED] += 1

        return True

    def place_cube(self, node_id: int, position: Coordinates, kind: CubeKind):
        if position in self.occupied:
            raise Exception(f"Requested {position} is already occupied by another cube.")

        # self.__bg_graph.add_node(cube_id)
        # self.__bg_graph.nodes[cube_id][AugmentedNxGraph.KEY_BG_CUBE_KIND] = kind
        # self.__bg_graph.nodes[cube_id][AugmentedNxGraph.KEY_BG_CUBE_POSITION] = position

        self.__nx_graph.nodes[node_id][AugmentedNxGraph.KEY_OLD_COORDINATES] = position.as_tuple()
        self.__nx_graph.nodes[node_id][AugmentedNxGraph.KEY_OLD_CUBE_KIND] = kind.name.lower()

        self.occupied.add(position)
        self.old_taken.add(position.as_tuple())

    def connect_pipe(self, source: int, target: int, edge_type : EdgeType):
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed and has no kind; cannot connect with a pipe.")

        if not self.is_node_realised(target):
            raise Exception(f"{target} is not placed and has no kind; cannot connect with a pipe.")

        if self.__nx_graph.edges[source, target] is not None:
            raise Exception(f"{source} and {target} are already connected by a pipe.")

        self.__nx_graph.add_edge(source, target)
        self.__nx_graph.get_edge_data(target, source)[AugmentedNxGraph.KEY_OLD_EDGE_TYPE] = edge_type