from logging import getLogger
console = getLogger(__name__)

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.utils.components_zx import NodeId
from topologiq.dzw.vedo.shapes_zx import ZxNode, ZxEdge


class ZxSceneManager:
    def __init__(self, nx_graph: AugmentedNxGraph):
        self.__nx_graph = nx_graph

        self.__nodes = dict()
        self.__edges = dict()

        # Prepare all the elements for the ZX scene (i.e. nodes and edges)
        self.elements = []
        for node in self.__nx_graph.get_nodes():
            zx_node = ZxNode(node, self.__nx_graph)
            self.elements.append( zx_node )
            self.__nodes[ node ] = zx_node

        for source, target in self.__nx_graph.get_edges():
            zx_edge = ZxEdge(source, target, self.__nx_graph).z(-0.1)
            self.elements.append( zx_edge )
            self.__edges[ source , target ] = zx_edge

        self.__selected_object = None

    def show_node_highlight(self, node: NodeId):
        self.__nodes[ node ].show_highlight()

    def hide_node_highlight(self, node: NodeId):
        self.__nodes[ node ].hide_highlight()

    def show_edge_highlight(self, source: NodeId, target: NodeId):
        self.__edges[ source, target ].show_highlight()

    def hide_edge_highlight(self, source: NodeId, target: NodeId):
        self.__edges[ source, target ].hide_highlight()

    # def on_left_click(self, event):
    #     if isinstance(event.object, ZxNode):
    #         bg_cube = self.__nx_graph.get_cube(event.object.zx_node)
    #         extra = f"[C{bg_cube}]" if bg_cube is not None else ""
    #         console.debug(f"Clicked on Node #{event.object.zx_node} {extra}")
    #         event.object.toggle_highlight()
    #
    #     if isinstance(event.object, ZxEdge):
    #         console.debug(f"Clicked on Edge  {event.object.zx_source}-{event.object.zx_target}")