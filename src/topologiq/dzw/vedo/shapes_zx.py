from vedo import Assembly, Disc, Line, Text3D

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.utils.components_zx import NodeId, NodeType, EdgeType

from topologiq.dzw.vedo.color_scheme import COLOR_NAMES

QUBIT_SPACING = 4.0
LAYER_SPACING = 6.0
EDGE_WIDTH = 7.5

class ZxNode(Assembly):
    def __init__(self, node: NodeId, anx: AugmentedNxGraph):
        self.zx_node = node

        node_type = anx.get_node_type(node)
        qubit = anx.get_qubit(node)
        layer = anx.get_node_layer(node)

        position = (LAYER_SPACING * layer, QUBIT_SPACING * qubit, 0)
        radius = 1.0 if node_type != NodeType.O else 0.75
        color = COLOR_NAMES[ node_type.name ]

        self.__disc = Disc(pos = position, r1 = 0.0, r2 = radius, c = color)
        self.__text = Text3D(str(node), pos = position, font = 'Calco', justify = 'centered', c = 'white')

        super().__init__( [ self.__disc, self.__text ] )

    def show_label(self):
        self.__text.alpha(1.0)

    def hide_label(self):
        self.__text.alpha(0.0)

class ZxEdge(Line):
    def __init__(self, source: NodeId, target: NodeId, anx: AugmentedNxGraph):

        self.zx_source: NodeId = source
        self.zx_target: NodeId = target

        source_qubit = anx.get_qubit(source)
        source_layer = anx.get_node_layer(source)
        target_qubit = anx.get_qubit(target)
        target_layer = anx.get_node_layer(target)
        edge_type = anx.get_edge_type(source, target)

        color = 'k' if edge_type == EdgeType.IDENTITY else 'y4'

        source_position = (LAYER_SPACING * source_layer, QUBIT_SPACING * source_qubit, 0)
        target_position = (LAYER_SPACING * target_layer, QUBIT_SPACING * target_qubit, 0)

        super().__init__(p0 = source_position, p1 = target_position, lw = EDGE_WIDTH, c = color)