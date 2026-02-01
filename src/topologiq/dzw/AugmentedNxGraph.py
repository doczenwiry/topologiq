import pyzx as zx
import networkx as nx

from topologiq.dzw.BlockGraphSpace import Coordinates, BlockGraphSpace, Plane
from topologiq.dzw.ZxGraphComponents import NodeType, EdgeType
from topologiq.dzw.BlockGraphComponents import CubeKind
from topologiq.utils.utils_pathfinder import check_exits

# TODO: figure out what the other VertexType and EdgeType represent
# TODO: how do we deal with the last four VertexType (i.e. H_BOX, W_INPUT, W_OUTPUT, Z_BOX) ?
# TODO: do we need the last EdgeType (i.e. W_IO) ?
# TODO: how do we deal with the phase of a spider ?
# TODO: benchmarking and timing various parts
# TODO: construction of animation
class AugmentedNxGraph(nx.Graph):

    KEY_ZX_NODE = 'zx'
    KEY_ZX_EDGE = 'zx'
    KEY_NODE_TYPE = 'node_type'
    KEY_EDGE_TYPE = 'edge_type'
    KEY_CUBE_KIND = 'cube_kind'
    KEY_POSITION = 'position'
    KEY_BEAMS = 'beams'
    KEY_NUMBER_OF_EDGES = 'number_of_edges'
    KEY_REALISED_EDGES = 'number_of_realised_edges'

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
            self.add_node(node)
            # None means this is an extra cube added to realise some edge.
            self.nodes[node][AugmentedNxGraph.KEY_ZX_NODE] = node
            self.nodes[node][AugmentedNxGraph.KEY_NODE_TYPE] = NodeType.convert(zx_graph.type(node))
            self.nodes[node][AugmentedNxGraph.KEY_NUMBER_OF_EDGES] = 0
            self.nodes[node][AugmentedNxGraph.KEY_REALISED_EDGES] = 0
            self.nodes[node][AugmentedNxGraph.KEY_CUBE_KIND] = None
            self.nodes[node][AugmentedNxGraph.KEY_POSITION] = None
            self.nodes[node][AugmentedNxGraph.KEY_BEAMS] = None

            self.nodes[node][AugmentedNxGraph.KEY_OLD_NODE_TYPE] = zx_graph.type(node).name
            self.nodes[node][AugmentedNxGraph.KEY_OLD_CUBE_KIND] = None
            self.nodes[node][AugmentedNxGraph.KEY_OLD_COMPLETED] = 0
            self.nodes[node][AugmentedNxGraph.KEY_OLD_COORDINATES] = None

        for edge in zx_graph.edges():
            source = min(edge)
            target = max(edge)
            self.add_edge(source, target)
            self.edges[source, target][AugmentedNxGraph.KEY_EDGE_TYPE] = EdgeType.convert(zx_graph.edge_type(edge))
            self.edges[source, target][AugmentedNxGraph.KEY_OLD_EDGE_TYPE] = zx_graph.edge_type(edge).name
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
        return self.get_edge_data(source, target).get(AugmentedNxGraph.KEY_EDGE_TYPE)

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
        # self.nodes[node_id][AugmentedNxGraph.KEY_BEAMS] = node_beams

        self.place_cube(node_id, position, kind)

    def is_edge_realised(self, source: int, target: int) -> bool:
        return (source,target) in self.edge_realisations

    def is_path_valid(self, source: int, target: int, path: list[tuple[Coordinates, CubeKind]]) -> bool:
            is_hadamard_path = False

            previous_kind: CubeKind = self.get_cube_kind(source)
            previous_plane: Plane = self.get_cube_kind().get_plane()
            previous_position: Coordinates = self.get_position(source)

            for (current_position, current_kind) in path:
                current_plane = current_kind.get_plane()

                # Check that the step taken lies in both planes of successive cubes
                step_taken = current_position - previous_position
                if not previous_plane.contains(step_taken) or not current_plane.contains(step_taken):
                    return False

                # Check that the current_position is not already occupied
                if current_position in self.occupied:
                    return False

                # Update the type of the path based on the type of the pipe
                if CubeKind.infer_pipe_type(previous_kind, current_kind) == EdgeType.HADAMARD:
                    is_hadamard_path = not is_hadamard_path

                previous_position = current_position
                previous_kind = current_kind
                previous_plane = current_plane

            target_position = self.get_position(target)
            target_kind = self.get_cube_kind(target)

            # Check that the step taken lies in both planes of successive cubes
            step_taken = target_position - previous_position
            if not previous_plane.contains(step_taken) or not target_kind.get_plane().contains(step_taken):
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

        if self.edges[source, target] is None:
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
            current = len(self.nodes)
            self.add_node(current)
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
        self.nodes[source][AugmentedNxGraph.KEY_REALISED_EDGES] += 1
        self.nodes[target][AugmentedNxGraph.KEY_REALISED_EDGES] += 1

        return True

    def place_cube(self, node_id: int, position: Coordinates, kind: CubeKind):
        if position in self.occupied:
            raise Exception(f"Requested {position} is already occupied by another cube.")

        self.nodes[node_id][AugmentedNxGraph.KEY_CUBE_KIND] = kind
        self.nodes[node_id][AugmentedNxGraph.KEY_POSITION] = position

        self.nodes[node_id][AugmentedNxGraph.KEY_OLD_COORDINATES] = position.as_tuple()
        self.nodes[node_id][AugmentedNxGraph.KEY_OLD_CUBE_KIND] = kind.name.lower()

        self.occupied.add(position)
        self.old_taken.add(position.as_tuple())

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