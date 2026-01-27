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
    def __init__(self, pyzx_graph: zx.graph.base.BaseGraph):
        super().__init__()

        # Keeps track of the coordinates in 3D that are occupied by some cube
        # TODO: Replace with efficient data-structure for crowded space (Binary Space Partitioning ?)
        self.occupied: set[Coordinates] = set()
        # Keeps track of the paths (i.e. one or more pipes) in the BlockGraph that realise the edges of the ZX-graph
        self.edge_realizations: dict = {}
        # Keeps track of the order in which nodes from the ZX-graph were placed for visualisation purposes
        self.placement_order : list[int] = []

        for vertex in pyzx_graph.vertices():
            self.add_node(
                vertex,
                # The vertex identifier from the ZX-graph
                # None means this is an extra cube added to realise some edge.
                zx = vertex,
                # NodeType : X, Y, Z or O
                type = NodeType.convert(pyzx_graph.type(vertex)),
                # Attributes of the cube that realises this vertex
                kind = None,     # CubeKind
                position = None, # 3D coordinates
                beams = None     # Orientation of the I/O ports
            )

        for edge in pyzx_graph.edges():
            source = min(edge)
            target = max(edge)
            self.add_edge(
                u_of_edge = source,
                v_of_edge = target,
                # EdgeType : IDENTITY or HADAMARD
                type = EdgeType.convert(pyzx_graph.edge_type(edge)),
                # The edge from the ZX-graph.
                # None means this is an extra pipe of a path that realizes some edge from the ZX-graph.
                zx = edge
            )

        # TODO: split any spider with more than 4 edges (cfr. graph_manager.py; prep_3d_g)
        # TODO: does the choice of how to split such spiders affect the minimal achievable volume ?
        _, max_degree = max(self.degree, key=lambda entry: entry[1])
        if max_degree > 4:
            raise NotImplemented("Enforcement of no-more-than-four-legs condition not implemented.")

    def is_boundary(self, v: int) -> bool:
        return self.nodes[v]['type'] == NodeType.O

    def is_spider(self, v: int) -> bool:
        return self.nodes[v]['type'] != NodeType.O

    # find_first_id(..)
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

        if self.number_of_nodes() == 0:
            raise nx.exception.NodeNotFound("Graph is empty.")

        # n.b. entries of self.degree are of tuples of the form (id, degree)
        if central_spider:
            (_, max_degree) = max(self.degree, key=lambda entry: entry[1])
            candidates = [v for v in self.nodes if self.is_spider(v) and self.degree[v] == max_degree]
        else:
            candidates = [v for v in self.nodes if self.is_spider(v)]

        return min(candidates) if deterministic else random.choice(candidates)

    def get_candidate_adjacent(self, source: int) -> list[tuple[Coordinates, CubeKind]]:
        if not self.is_vertex_placed(source):
            raise ValueError(f"{source} is not placed and thus has no kind. Cannot determine its adjacent candidates.")

        source_position = self.nodes[source]['position']
        source_type = self.nodes[source]['type']
        source_kind = self.nodes[source]['kind']
        source_plane = source_kind.get_plane()
        candidates_adjacent = []
        for step in BlockGraphSpace.STEPS:
            # A cube can only have an adjacent cube that lies in the same plane
            if source_plane.contains(step):
                candidate_coordinates = source_position + step.value
                # A cube can only have an adjacent cube at a position that is not occupied by another cube
                if candidate_coordinates not in self.occupied:
                    # A cube can always have an adjacent cube of the same kind
                    candidates_adjacent.append( ( candidate_coordinates, source_kind) )
                    # A cube can always have an adjacent cube of the other color lying in a plane
                    # that is orthogonal to its own plane along the step
                    candidate_type = NodeType.flip(source_type)
                    candidate_plane = BlockGraphSpace.get_orthogonal_plane(source_plane, step)
                    candidate_kind = CubeKind.convert(candidate_type, candidate_plane)
                    candidates_adjacent.append( (candidate_coordinates, candidate_kind) )
        return candidates_adjacent

    # TODO: provide number of unobstructed ports, number of legs, information to check the beams
    def get_unobstructed_ports(self, v: int) -> int:
        return 0

    def is_vertex_placed(self, v: int) -> bool:
        return self.nodes[v]['coordinates'] is not None and self.nodes[v]['kind'] is not None

    def place_vertex(self, v: int, kind: CubeKind, position: Coordinates):
        """Realize the vertex as a cube of the given kind placed at the given coordinates."""
        if position in self.occupied:
            raise Exception(f"Requested {position} is already occupied by another cube.")

        if kind not in CubeKind.suitable_kinds(self.nodes[v]['type']):
            raise Exception(f"Requested {kind} is not compatible with {self.nodes[v]['type']}")

        if self.nodes[v]['zx'] is not None:
            self.placement_order.append(v)

        self.nodes[v]['kind'] = kind
        self.nodes[v]['position'] = position

        # TODO: compute the beams of the new cube
        # TODO: prune the beams of other cubes

        self.occupied.add(position)

    def is_edge_realized(self, source: int, target: int) -> bool:
        return (source,target) in self.edge_realizations

    def connect_pipe(self, source: int, target: int):
        if not self.is_vertex_placed(source):
            raise ValueError(f"{source} is not placed. Cannot connect with a pipe.")

        if not self.is_vertex_placed(target):
            raise ValueError(f"{target} is not placed. Cannot connect with a pipe.")

