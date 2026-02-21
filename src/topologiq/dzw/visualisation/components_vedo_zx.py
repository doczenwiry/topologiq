from vedo import Disc, Line

from topologiq.dzw.utils.coordinates import Coordinates
from topologiq.dzw.utils.components_zx import NodeId, NodeType, EdgeType

ZX_COLORS = {
    NodeType.X : 'r4',
    NodeType.Y : 'g4',
    NodeType.Z : 'b4',
    NodeType.O : 'k2'
}

QUBIT_SPACING = 4.0
LAYER_SPACING = 6.0
EDGE_WIDTH = 7.5

class ZxNode(Disc):
    def __init__(self, node: NodeId, qubit: int, layer: int, node_type: NodeType):
        self.zx_node = node

        position = (LAYER_SPACING * layer, QUBIT_SPACING * qubit, 0)

        radius = 1.0 if node_type != NodeType.O else 0.75
        color = ZX_COLORS[node_type]

        super().__init__(pos=position, r1 = 0.0, r2 = radius, c = color)

class ZxEdge(Line):
    def __init__(self,
        source: NodeId, source_qubit: int, source_layer: int,
        target: NodeId, target_qubit: int, target_layer: int,
        edge_type: EdgeType
    ):

        self.zx_source: NodeId = source
        self.zx_target: NodeId = target

        color = 'k' if edge_type == EdgeType.IDENTITY else 'y4'

        source_position = (LAYER_SPACING * source_layer, QUBIT_SPACING * source_qubit, 0)
        target_position = (LAYER_SPACING * target_layer, QUBIT_SPACING * target_qubit, 0)

        super().__init__(p0 = source_position, p1 = target_position, lw = EDGE_WIDTH, c = color)