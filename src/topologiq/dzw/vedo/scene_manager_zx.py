from logging import getLogger
console = getLogger(__name__)

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.vedo.shapes_zx import ZxNode, ZxEdge


class ZxSceneManager:
    def __init__(self, nx_graph: AugmentedNxGraph):
        self.__nx_graph = nx_graph

        # Prepare all the elements for the ZX scene (i.e. nodes and edges)
        self.elements = []
        for node in self.__nx_graph.get_nodes():
            self.elements.append(
                ZxNode(node, self.__nx_graph)
            )

        for source, target in self.__nx_graph.get_edges():
            self.elements.append(
                ZxEdge(source, target, self.__nx_graph).z(-0.1)
            )

    def on_left_click(self, event):
        if isinstance(event.object, ZxNode):
            bg_cube = self.__nx_graph.get_cube(event.object.zx_node)
            extra = f"[C{bg_cube}]" if bg_cube is not None else ""
            console.debug(f"Clicked on Node #{event.object.zx_node} {extra}")
            event.object.hide_label()

        if isinstance(event.object, ZxEdge):
            console.debug(f"Clicked on Edge  {event.object.zx_source}-{event.object.zx_target}")
