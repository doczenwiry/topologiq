import pyzx as zx
import networkx as nx

from topologiq.dzw.BlockGraphSpace import Coordinates, BlockGraphSpace
from topologiq.dzw.ZxGraphComponents import NodeType, EdgeType
from topologiq.dzw.BlockGraphComponents import CubeKind

# TODO: figure out what the other VertexType and EdgeType represent
# TODO: how do we deal with the last four VertexType (i.e. H_BOX, W_INPUT, W_OUTPUT, Z_BOX) ?
# TODO: do we need the last EdgeType (i.e. W_IO) ?
# TODO: how do we deal with the phase of a spider ?
# TODO: benchmarking and timing various parts
# TODO: construction of animation
class AugmentedNxGraph(nx.Graph):
    KEY_ZX_NODE = 'zx'
    KEY_ZX_EDGE = 'zx'
    KEY_NODE_TYPE = 'type'
    KEY_EDGE_TYPE = 'type'
    KEY_CUBE_KIND = 'kind'
    KEY_POSITION = 'coords'
    KEY_BEAMS = 'beams'
    KEY_NUMBER_OF_EDGES = 'number_of_edges'
    KEY_REALISED_EDGES = 'number_of_realised_edges'

    def __init__(self, zx_graph: zx.graph.base.BaseGraph):
        super().__init__()

        # Keeps track of the coordinates in 3D that are occupied by some cube
        # TODO: Replace with efficient data-structure for crowded space (Binary Space Partitioning ?)
        self.occupied: set[Coordinates] = set()
        # Keeps track of the paths (i.e. one or more pipes) in the BlockGraph that realise the edges of the ZX-graph
        self.edge_realisations: dict = {}
        # Keeps track of the order in which nodes from the ZX-graph were placed for visualisation purposes
        self.placement_order : list[int] = []

        for node in zx_graph.vertices():
            self.add_node(node)
            # None means this is an extra cube added to realise some edge.
            self.nodes[node][AugmentedNxGraph.KEY_ZX_NODE] = node
            self.nodes[node][AugmentedNxGraph.KEY_NODE_TYPE] = NodeType.convert(zx_graph.type(node))
            self.nodes[node][AugmentedNxGraph.KEY_NUMBER_OF_EDGES] = 0
            self.nodes[node][AugmentedNxGraph.KEY_REALISED_EDGES] = 0
            self.nodes[node][AugmentedNxGraph.KEY_CUBE_KIND] = None
            self.nodes[node][AugmentedNxGraph.KEY_POSITION] = None
            self.nodes[node][AugmentedNxGraph.KEY_BEAMS] = None

        for edge in zx_graph.edges():
            source = min(edge)
            target = max(edge)
            self.add_edge(source, target)
            self.edges[source, target][AugmentedNxGraph.KEY_EDGE_TYPE] = EdgeType.convert(zx_graph.edge_type(edge))
            self.edges[source, target][AugmentedNxGraph.KEY_ZX_EDGE] = edge
            self.nodes[source][AugmentedNxGraph.KEY_NUMBER_OF_EDGES] += 1
            self.nodes[target][AugmentedNxGraph.KEY_NUMBER_OF_EDGES] += 1

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        _, max_degree = max(self.degree, key=lambda entry: entry[1])
        if max_degree > 4:
            raise NotImplemented("Enforcement of no-more-than-four-legs condition not implemented.")

    def is_boundary(self, node_id: int) -> bool:
        return self.nodes[node_id][AugmentedNxGraph.KEY_NODE_TYPE] == NodeType.O

    def is_spider(self, node_id: int) -> bool:
        return self.nodes[node_id][AugmentedNxGraph.KEY_NODE_TYPE] != NodeType.O

    def get_zx_node(self, node_id: int):
        return self.nodes[node_id][AugmentedNxGraph.KEY_ZX_NODE]

    def get_zx_edge(self, source: int, target: int):
        return self.get_edge_data(source, target)[AugmentedNxGraph.KEY_ZX_EDGE]

    def get_position(self, node_id: int) -> Coordinates:
        return self.nodes[node_id][AugmentedNxGraph.KEY_POSITION]

    def get_node_type(self, node_id: int) -> NodeType:
        return self.nodes[node_id][AugmentedNxGraph.KEY_NODE_TYPE]

    def get_cube_kind(self, node_id: int) -> CubeKind:
        return self.nodes[node_id][AugmentedNxGraph.KEY_CUBE_KIND]

    def get_edge_type(self, source: int, target: int) -> EdgeType:
        return self.get_edge_data(source, target).get(AugmentedNxGraph.KEY_NODE_TYPE)

    # TODO: move consistency checking to Cube classes (recommendation from J)
    def get_candidate_adjacent(self, source: int, pipe_type: EdgeType) -> list[tuple[Coordinates, CubeKind]]:
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
        return self.get_position(node_id) is not None and self.get_cube_kind(node_id) is not None

    def realise_node(self, node_id: int, kind: CubeKind, position: Coordinates):
        """Realise the node as a cube of the given kind placed at the given coordinates."""
        if kind not in CubeKind.suitable_kinds(self.get_node_type(node_id)):
            raise Exception(f"Requested {kind} is not compatible with {self.get_node_type(node_id)}")

        if self.get_zx_node(node_id) is None:
            raise Exception(f"Node {node_id} not found in the ZX-graph.")

        # TODO: compute the beams of the new cube
        # TODO: prune the beams of other cubes

        self.place_cube(node_id, position, kind)

    def is_edge_realised(self, source: int, target: int) -> bool:
        return (source,target) in self.edge_realisations

    # Precondition: path is a sequence of (position,kind) for the extra cubes needed to connect the source to the target
    def realise_edge(self, source: int, target: int, path: list[tuple[Coordinates, CubeKind]]):
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed; cannot connect with a path.")

        if not self.is_node_realised(target):
            raise Exception(f"{target} is not placed; cannot connect with a path.")

        if self.edges[source, target] is None:
            raise Exception(f"No edge {source}-{target} found in the ZX-graph.")

        edge = (source, target)
        edge_type = self.get_edge_type(source, target)

        if self.edge_realisations[edge] is not None:
            raise Exception(f"{edge} is already realized by a path.")

        source_kind = self.get_cube_kind(source)
        target_kind = self.get_cube_kind(target)
        source_position = self.get_position(source)
        target_position = self.get_position(target)

        # Raise any Exception if the path is invalid
        CubeKind.validate_path(source_kind, source_position, target_kind, target_position, edge_type, path)

        # Representation of the path that will go into edge_realisations
        extras = []

        # Add all the extra cubes and pipes of the path to the BlockGraph
        previous: int = source
        previous_kind: CubeKind = source_kind
        for (current_position, current_kind) in path:
            # Place the current extra node and connect it to the previous node.
            current = len(self.nodes)
            self.add_node(current)
            self.place_cube(current, current_position, current_kind)
            pipe_type = CubeKind.infer_pipe_type(previous_kind, current_kind)
            self.connect_pipe(previous, current, pipe_type)

            # Extend the sequence of extra node ids
            extras.append(current)

            # Prepare for the next iteration
            previous = current
            previous_kind = current_kind

        # Make the final connection
        pipe_type = CubeKind.infer_pipe_type(previous_kind, target_kind)
        self.connect_pipe(previous, target, pipe_type)
        # Associate the path as a realisation of the edge
        self.edge_realisations[edge] = extras

        # One more edge has been realized
        self.nodes[source][AugmentedNxGraph.KEY_REALISED_EDGES] += 1
        self.nodes[target][AugmentedNxGraph.KEY_REALISED_EDGES] += 1

    def place_cube(self, node_id: int, position: Coordinates, kind: CubeKind):
        if position in self.occupied:
            raise Exception(f"Requested {position} is already occupied by another cube.")

        self.nodes[node_id][AugmentedNxGraph.KEY_CUBE_KIND] = kind
        self.nodes[node_id][AugmentedNxGraph.KEY_POSITION] = position
        self.occupied.add(position)

    def connect_pipe(self, source: int, target: int, edge_type : EdgeType):
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed and has no kind; cannot connect with a pipe.")

        if not self.is_node_realised(target):
            raise Exception(f"{target} is not placed and has no kind; cannot connect with a pipe.")

        if self.edges[source, target] is not None:
            raise Exception(f"{source} and {target} are already connected by a pipe.")

        self.add_edge(
            source,
            target,
            zx = None,
            type = edge_type,
        )