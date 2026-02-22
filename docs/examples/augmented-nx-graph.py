import pyzx as zx

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.zx_graph_walker import ZxGraphWalker
from topologiq.dzw.utils.components_bg import CubeKind
from topologiq.dzw.utils.components_zx import NodeType
from topologiq.dzw.visualisation.report_formatter import ReportFormatter
from topologiq.dzw.visualisation.tikz_writer import TikzWriter

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.INFO)
logging.getLogger('topologiq.dzw').setLevel(logging.INFO)
logging.getLogger('topologiq.dzw.ZxGraphWalker').setLevel(logging.DEBUG)
logging.getLogger('topologiq.dzw.utils').setLevel(logging.DEBUG)
logging.getLogger('topologiq.dzw.helpers').setLevel(logging.CRITICAL)
logging.getLogger('topologiq.dzw.visualisation').setLevel(logging.CRITICAL)

from jsonpickle import encode, decode
ANG_PATH = "../../assets/ang/"
def ang_write(ang: AugmentedNxGraph, label: str):
    with open(ANG_PATH + label + ".json", "w") as f:
        f.write(encode(ang, indent=2, keys = True, unpicklable=True))

def ang_read(label: str):
    return decode(open(ANG_PATH + label + ".json").read(), keys = True)

if __name__ == '__main__':
    circuit = zx.Circuit(8, name = "ghz8")
    circuit.add_gate("H", 0)
    circuit.add_gate("CNOT", 0, 4)
    circuit.add_gate("CNOT", 0, 2)
    circuit.add_gate("CNOT", 4, 6)
    circuit.add_gate("CNOT", 0, 1)
    circuit.add_gate("CNOT", 2, 3)
    circuit.add_gate("CNOT", 4, 5)
    circuit.add_gate("CNOT", 6, 7)
    zx_input = circuit.to_graph()
    zx.draw(zx_input, labels = True)

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

    # formatter = ReportFormatter(walker.nx_graph, label = circuit.name)
    # formatter.print_report(append_cube_report = True)
    # formatter.write_report()

    ang_write(walker.nx_graph, label = circuit.name)

    TikzWriter.STYLE = 'zx'
    TikzWriter.ROTATION_X = 60
    TikzWriter.ROTATION_Z = 118
    tikz_writer = TikzWriter(walker.nx_graph, label = circuit.name)
    tikz_writer.write_file()