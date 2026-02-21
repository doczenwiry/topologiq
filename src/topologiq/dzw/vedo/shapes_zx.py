from vedo import Assembly, Disc, Line, Text3D, Box

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.utils.components_zx import NodeId, NodeType, EdgeType
from topologiq.dzw.utils.coordinates import Coordinates

from topologiq.dzw.vedo.color_scheme import COLOR_NAMES

QUBIT_SPACING = 6.0
LAYER_SPACING = 6.0

class ZxNode(Assembly):
    def __init__(self, node: NodeId, anx: AugmentedNxGraph):
        self.zx_node = node

        node_type = anx.get_node_type(node)
        qubit = anx.get_qubit(node)
        layer = anx.get_node_layer(node)

        disc_position = (LAYER_SPACING * layer, QUBIT_SPACING * qubit, 0.00)
        text_position = (LAYER_SPACING * layer, QUBIT_SPACING * qubit, 0.05)
        radius = 1.0 if node_type != NodeType.O else 0.75
        color = COLOR_NAMES[ node_type.name ]

        self.__disc = Disc(pos = disc_position, r1 = 0.0, r2 = radius, c = color)
        self.__disc_highlight = Disc(pos = text_position, r1 = 0.8 * radius, r2 = radius - 0.05, c = COLOR_NAMES[ 'highlighted' ])
        self.__text = Text3D(str(node), pos = text_position, font = 'Calco', justify = 'centered', c = 'white')

        super().__init__( [ self.__disc, self.__disc_highlight, self.__text ] )

        self.__highlighted = False
        self.__disc_highlight.alpha(0.0)

    def toggle_highlight(self):
        self.__highlighted = not self.__highlighted
        if self.__highlighted:
            self.__disc_highlight.alpha(1.0)
        else:
            self.__disc_highlight.alpha(0.0)

    def show_highlight(self): self.__disc_highlight.alpha(1.0)
    def hide_highlight(self): self.__disc_highlight.alpha(0.0)

    def show_label(self): self.__text.alpha(1.0)
    def hide_label(self): self.__text.alpha(0.0)

# Replace line with a Box
class ZxEdge(Box):
    LENGTH = 3.00
    DIAMETER = 0.50

    def __init__(self, source: NodeId, target: NodeId, anx: AugmentedNxGraph):

        self.zx_source: NodeId = source
        self.zx_target: NodeId = target

        source_qubit = anx.get_qubit(source)
        source_layer = anx.get_node_layer(source)
        target_qubit = anx.get_qubit(target)
        target_layer = anx.get_node_layer(target)
        edge_type = anx.get_edge_type(source, target)

        color = 'k' if edge_type == EdgeType.IDENTITY else 'y4'

        source_position = Coordinates(LAYER_SPACING * source_layer, QUBIT_SPACING * source_qubit, 0)
        target_position = Coordinates(LAYER_SPACING * target_layer, QUBIT_SPACING * target_qubit, 0)

        distances = target_position - source_position
        position = source_position + distances / 2.0
        # Compute the measurements of this pipe (i.e. length, width, height) according to its direction
        measures = [ ZxEdge.LENGTH if d != 0 else ZxEdge.DIAMETER for d in distances ]

        super().__init__(pos = position.as_tuple(), size = measures, c = color)

    def show_highlight(self):
        self.linecolor('k5')
        self.linewidth(6)

    def hide_highlight(self):
        self.linecolor('k')
        self.linewidth(3)
