import random
import pyzx as zx
import networkx as nx

from topologiq.dzw.GraphComponents import NodeType, EdgeType, CubeKind
from topologiq.dzw.BlockGraphSpace import Coordinates, BlockGraphSpace

# TODO: figure out what the other VertexType and EdgeType represent
# TODO: how do we deal with the last four VertexType (i.e. H_BOX, W_INPUT, W_OUTPUT, Z_BOX) ?
# TODO: do we need the last EdgeType (i.e. W_IO) ?
# TODO: how do we deal with the phase of a spider ?
# TODO: benchmarking and timing various parts
# TODO: construction of animation
class AugmentedNxGraph(nx.Graph):
    KEY_TYPE = 'type'
    KEY_KIND = 'kind'
    KEY_POSITION = 'coords'

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
            self.add_node(
                node,
                # The node identifier from the ZX-graph
                # None means this is an extra cube added to realise some edge.
                zx = node,
                # NodeType : X, Y, Z or O
                type = NodeType.convert(zx_graph.type(node)),
                number_of_legs = 0,
                # Attributes of the cube that realises this node
                kind = None,     # CubeKind
                position = None, # 3D coordinates
                beams = None,    # Orientation of the I/O ports
                # Keeping track of how many legs of this node are realised in the BlockGraph
                number_of_realized_legs = 0
            )

        for edge in zx_graph.edges():
            source = min(edge)
            target = max(edge)
            self.add_edge(
                u_of_edge = source,
                v_of_edge = target,
                # EdgeType : IDENTITY or HADAMARD
                type = EdgeType.convert(zx_graph.edge_type(edge)),
                # The edge from the ZX-graph.
                # None means this is an extra pipe of a path that realizes some edge from the ZX-graph.
                zx = edge
            )
            self.nodes[source]['number_of_legs'] += 1
            self.nodes[target]['number_of_legs'] += 1

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        _, max_degree = max(self.degree, key=lambda entry: entry[1])
        if max_degree > 4:
            raise NotImplemented("Enforcement of no-more-than-four-legs condition not implemented.")

    def is_boundary(self, node_id: int) -> bool:
        return self.nodes[node_id][AugmentedNxGraph.KEY_TYPE] == NodeType.O

    def is_spider(self, node_id: int) -> bool:
        return self.nodes[node_id][AugmentedNxGraph.KEY_TYPE] != NodeType.O

    def get_position(self, node_id: int) -> Coordinates:
        return self.nodes[node_id][AugmentedNxGraph.KEY_POSITION]

    def get_node_type(self, node_id: int) -> NodeType:
        return self.nodes[node_id][AugmentedNxGraph.KEY_TYPE]

    def get_node_kind(self, node_id: int) -> CubeKind:
        return self.nodes[node_id][AugmentedNxGraph.KEY_KIND]

    def get_edge_type(self, source: int, target: int) -> EdgeType:
        return self.get_edge_data(source, target).get(AugmentedNxGraph.KEY_TYPE)

    def get_candidate_adjacent(self, source: int, pipe_type: EdgeType) -> list[tuple[Coordinates, CubeKind]]:
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed and thus has no kind. Cannot determine its adjacent candidates.")

        if self.get_node_type(source) not in [NodeType.X, NodeType.Z]:
            raise NotImplemented(f"NodeType {self.get_node_type(source)} not supported.")

        source_position = self.nodes[source][AugmentedNxGraph.KEY_POSITION]
        source_type = self.nodes[source][AugmentedNxGraph.KEY_TYPE]
        source_kind = self.nodes[source][AugmentedNxGraph.KEY_KIND]
        source_plane = source_kind.get_plane()
        candidates_adjacent = []
        for step in BlockGraphSpace.STEPS:
            # A cube can only have an adjacent cube that lies in the same plane
            if source_plane.contains(step):
                candidate_coordinates = source_position + step.value
                # A cube can only have an adjacent cube at a position that is not occupied by another cube
                if candidate_coordinates not in self.occupied:
                    orthogonal_plane = BlockGraphSpace.get_orthogonal_plane(source_plane, step)
                    # A cube can always have an adjacent cube of the same color connected by
                    # - IDENTITY pipe in the same plane
                    # - HADAMARD pipe in the plane orthogonal along the step
                    if pipe_type == EdgeType.IDENTITY:
                        candidate_kind = source_kind
                    else:
                        candidate_kind = CubeKind.convert(source_type, orthogonal_plane)
                    candidates_adjacent.append( (candidate_coordinates , candidate_kind) )
                    # A cube can always have an adjacent cube of the other color connected by
                    # - IDENTITY pipe in the plane orthogonal along the step
                    # - HADAMARD pipe in the same plane
                    if pipe_type == EdgeType.IDENTITY:
                        candidate_kind = CubeKind.convert(NodeType.flip(source_type), orthogonal_plane)
                    else:
                        candidate_kind = CubeKind.convert(NodeType.flip(source_type), source_plane)
                    candidates_adjacent.append( (candidate_coordinates , candidate_kind) )

        return candidates_adjacent

    # TODO: provide number of unobstructed ports, number of legs, information to check the beams
    def get_unobstructed_ports(self, node_id: int) -> int:
        return 0

    def is_node_realised(self, node_id: int) -> bool:
        return self.nodes[node_id][AugmentedNxGraph.KEY_POSITION] is not None and self.nodes[node_id][AugmentedNxGraph.KEY_KIND] is not None

    def realise_node(self, node_id: int, kind: CubeKind, position: Coordinates):
        """Realise the node as a cube of the given kind placed at the given coordinates."""
        if kind not in CubeKind.suitable_kinds(self.nodes[node_id][AugmentedNxGraph.KEY_TYPE]):
            raise Exception(f"Requested {kind} is not compatible with {self.nodes[node_id][AugmentedNxGraph.KEY_TYPE]}")

        if self.nodes[node_id]['zx'] is None:
            raise Exception(f"Node {node_id} not found in the ZX-graph.")

        # TODO: compute the beams of the new cube
        # TODO: prune the beams of other cubes

        self.place_cube(node_id, position, kind)

    def is_edge_realised(self, source: int, target: int) -> bool:
        return (source,target) in self.edge_realisations

    @staticmethod
    def adjacent_consistent(position1: Coordinates, kind1: CubeKind, position2: Coordinates, kind2: CubeKind) -> bool:
        md_consistent = position1.get_manhattan_distance(position2) == 1
        # TODO: compute kind-to-kind-consistency along the step between the two positions
        kk_consistent = True # kind1.compatible(kind2, position1 - position2)
        return md_consistent and kk_consistent

    # Precondition: path is a sequence of (position,kind) for the extra cubes needed to connect the source to the target
    def realise_edge(self, source: int, target: int, path: list[tuple[Coordinates, CubeKind]]):
        if not self.is_node_realised(source):
            raise Exception(f"{source} is not placed; cannot connect with a path.")

        if not self.is_node_realised(target):
            raise Exception(f"{target} is not placed; cannot connect with a path.")

        if self.edges[source, target] is None:
            raise Exception(f"No edge {source}-{target} found in the ZX-graph.")

        edge = (source, target)

        if self.edge_realisations[edge] is not None:
            raise Exception(f"{edge} is already realized by a path.")

        # TODO: check that the path type is consistent with the edge type which it realizes (parity of Hadamard-pipes ?)

        self.nodes[source]['number_of_realized_legs'] += 1
        self.nodes[target]['number_of_realized_legs'] += 1

        source_position = self.nodes[source][AugmentedNxGraph.KEY_POSITION]
        target_position = self.nodes[target][AugmentedNxGraph.KEY_POSITION]
        source_kind = self.nodes[source][AugmentedNxGraph.KEY_KIND]
        target_kind = self.nodes[target][AugmentedNxGraph.KEY_KIND]

        # This will serve as the representation for the path that will go into edge_realisations
        extra_ids = []

        # Add all the extra cubes and pipes of the path to the BlockGraph
        previous_id: int = source
        previous_kind: CubeKind = source_kind
        previous_position: Coordinates = source_position
        for (current_position, current_kind) in path:
            # Check for consistency between the current extra node and the previous node
            # Adjacent cubes must be within Manhattan Distance of 1 and have compatible kinds
            if not AugmentedNxGraph.adjacent_consistent(current_position, current_kind, previous_position, previous_kind):
                raise Exception(f"Successive cubes in the path must have a Manhattan Distance of 1 and compatible kinds [{previous_kind}@{previous_position} vs. {current_kind}@{current_position}].")

            # Place the current extra node and connect it to the previous node.
            current_id = len(self.nodes)
            self.add_node(current_id)
            self.place_cube(current_id, current_position, current_kind)
            self.connect_pipe(previous_id, current_id, EdgeType.IDENTITY)

            # Extend the sequence of extra node ids
            extra_ids.append(current_id)

            # Prepare for the next iteration
            previous_id = current_id
            previous_position = current_position
            previous_kind = current_kind

        # Check for consistency between the previous node and the target
        if not AugmentedNxGraph.adjacent_consistent(target_position, target_kind, previous_position, previous_kind):
            raise Exception(f"Successive cubes in the path must have a Manhattan Distance of 1 and compatible kinds [{previous_kind}@{previous_position} vs. {target_kind}@{target_position}].")

        # Make the final connection
        self.connect_pipe(previous_id, target, EdgeType.IDENTITY)
        # Associate the path as a realisation of the edge
        self.edge_realisations[edge] = extra_ids

    def place_cube(self, node_id: int, position: Coordinates, kind: CubeKind):
        if position in self.occupied:
            raise Exception(f"Requested {position} is already occupied by another cube.")

        self.nodes[node_id][AugmentedNxGraph.KEY_KIND] = kind
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