import pyzx as zx

from topologiq.dzw.ZxGraphWalker import ZxGraphWalker
from topologiq.dzw.utils.CubeKind import CubeKind
from topologiq.dzw.utils.components_zx import NodeType
from topologiq.dzw.visualisation.ReportFormatter import ReportFormatter
from topologiq.dzw.visualisation.TikzWriter import TikzWriter

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('topologiq.dzw').setLevel(logging.INFO)
logging.getLogger('topologiq.dzw.ZxGraphWalker').setLevel(logging.DEBUG)
logging.getLogger('topologiq.dzw.utils').setLevel(logging.DEBUG)
logging.getLogger('topologiq.dzw.helpers').setLevel(logging.CRITICAL)
logging.getLogger('topologiq.dzw.visualisation').setLevel(logging.CRITICAL)

if __name__ == '__main__':
    c = zx.Circuit(2)
    c.add_gate("H", 0)
    c.add_gate("CNOT", 0, 1)
    c.add_gate("CNOT", 1, 0)
    c.add_gate("CNOT", 1, 0)
    zx_input = c.to_graph()
    # zx.draw(zx_input)

    walker = ZxGraphWalker(zx_input)
    nx_graph = walker.nx_graph

    print(f"Z-Spiders:", end=" ")
    for node in nx_graph.get_nodes():
        node_type = nx_graph.get_node_type(node)
        if node_type == NodeType.Z:
            print(f"{node}", end=" ")
    print("")

    print(f"X-Spiders:", end=" ")
    for node in nx_graph.get_nodes():
        node_type = nx_graph.get_node_type(node)
        if node_type == NodeType.X:
            print(f"{node}", end=" ")
    print("")

    print(f"Boundaries:", end=" ")
    for node in nx_graph.get_nodes():
        node_type = nx_graph.get_node_type(node)
        if node_type == NodeType.O:
            print(f"{node}", end=" ")
    print("")

    root = 3
    kind = CubeKind.suitable_kinds(nx_graph.get_node_type(root))[0]

    walker.construct( root_choice = (root,kind) )

    formatter = ReportFormatter(walker.nx_graph, label = "3cnots")
    formatter.print_report(append_cube_report = True)
    formatter.write_report()

    TikzWriter.STYLE = 'zx'
    TikzWriter.ROTATION_X = 60
    TikzWriter.ROTATION_Z = 118
    tikz_writer = TikzWriter(walker.nx_graph, label ="3cnots")
    tikz_writer.write_file()