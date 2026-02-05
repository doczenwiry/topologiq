import pyzx as zx

from topologiq.dzw.ZxGraphWalker import ZxGraphWalker
from topologiq.dzw.BlockGraphComponents import CubeKind, NodeType

if __name__ == '__main__':
    circuit_name = "cnot"
    c = zx.Circuit(2)
    c.add_gate("CNOT", 1, 0)
    # c.add_gate("CNOT", 1, 0)
    # c.add_gate("CNOT", 0, 1)
    zx_input = c.to_graph()

    walker = ZxGraphWalker(zx_input, circuit_name)
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

    root = 3  # builder.pick_root()
    kind = CubeKind.suitable_kinds(nx_graph.get_node_type(root))[0]

    kwargs: dict[str, tuple[int, int] | int] = {
        "weights": (-1, -1),
        "length_of_beams": 99,
    }

    walker.construct( root_choice = (root,kind) )

    walker.print_report(append_cube_report = True)
    walker.write_report("../../output/txt/cnot-ang-bis.txt")