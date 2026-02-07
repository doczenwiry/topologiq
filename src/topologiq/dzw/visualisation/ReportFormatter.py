from topologiq.dzw.utils.EdgeType import EdgeType
from topologiq.dzw.utils.NodeType import NodeType
from topologiq.dzw.ZxGraphWalker import ZxGraphWalker


class ReportFormatter:
    def __init__(self, walker: ZxGraphWalker):
        self.walker = walker

    @staticmethod
    def __flip(node_type: NodeType) -> NodeType:
        if node_type == NodeType.X:
            return NodeType.Z
        elif node_type == NodeType.Z:
            return NodeType.X
        else:
            raise ValueError(f"Flipping color not supported for node type: {node_type}")

    @staticmethod
    def infer_connecting_pipe_colors(previous_kind, step):
        current_type = previous_kind.get_type()
        current_reach = previous_kind.get_reach().value.as_tuple()
        colors = ['-', '-', '-']

        step = step.as_tuple()

        for index in range(3):
            if step[index] != 0:
                colors[index] = 'o'
            else:
                t = current_type if current_reach[index] != 0 else ReportFormatter.__flip(current_type)
                colors[index] = t.name.lower()

        return "".join(colors)


    def old_path_format(self, source, target):
        source_cube = self.walker.nx_graph.get_cube(source)
        source_kind = self.walker.nx_graph.get_cube_kind(source_cube)
        source_position = self.walker.nx_graph.get_cube_position(source_cube)
        old_format = [(source_position.as_tuple(), source_kind.name.lower())]

        previous_kind = source_kind
        previous_position = source_position
        for current_cube in self.walker.nx_graph.get_edge_realisation(source, target):
            current_kind = self.walker.nx_graph.get_cube_kind(current_cube)
            current_position = self.walker.nx_graph.get_cube_position(current_cube)
            # Infer needed pipe
            step = (current_position - previous_position).normalized()
            old_format.append(((previous_position + step).as_tuple(), ReportFormatter.infer_connecting_pipe_colors(previous_kind, step)))

            # Append current cube
            old_format.append((current_position.as_tuple(), current_kind.name))

            previous_kind = current_kind
            previous_position = current_position

        target_cube = self.walker.nx_graph.get_cube(target)
        current_kind = self.walker.nx_graph.get_cube_kind(target_cube)
        current_position = self.walker.nx_graph.get_cube_position(target_cube)

        # Infer needed pipe
        step = (current_position - previous_position).normalized()
        old_format.append(((previous_position + step).as_tuple(), ReportFormatter.infer_connecting_pipe_colors(previous_kind, step)))
        # Append current cube
        old_format.append((current_position.as_tuple(), current_kind.name.lower()))

        return str(old_format)


    def prepare_report(self, append_cube_report: bool = False):
        report = ""

        report += f"RESULT SHEET. CIRCUIT NAME: {self.walker.name}\n"
        report += "\n__________________________\n"
        report += "ORIGINAL ZX GRAPH\n"
        for node in self.walker.nx_graph.get_nodes():
            report += f"Node ID: {node}. Type: {self.walker.nx_graph.get_node_type(node).name}\n"
        report += "\n"
        for edge in self.walker.nx_graph.get_edges():
            source = min(edge)
            target = max(edge)
            edge_type = self.walker.nx_graph.get_edge_type(source, target)
            type_name = "SIMPLE" if edge_type == EdgeType.IDENTITY else "HADAMARD"
            report += f"Edge ID: ({source}, {target}). Type: {type_name}\n"
        report += "\n__________________________\n"
        report += "3D \"EDGE PATHS\" (Blocks needed to connect two original nodes)\n"
        for source, target in self.walker.edge_realisation_order:
            edge = (source, target) if source < target else (target, source)
            report += f"Edge {edge}: {self.old_path_format(source, target)}\n"
        report += "\n__________________________\n"
        report += "LATTICE SURGERY (Graph)\n"
        for node in self.walker.node_realisation_order:
            cube = self.walker.nx_graph.get_cube(node)
            report += f"Node ID: {node}. Info: ({self.walker.nx_graph.get_cube_position(cube)}, '{self.walker.nx_graph.get_cube_kind(cube).name.lower()}')\n"
        if append_cube_report:
            report += "\n__________________________\n"
            report += "CUBES (BG-Graph)\n"
            for cube in self.walker.nx_graph.get_cubes():
                node = self.walker.nx_graph.get_node(cube)
                label = str(node) if node is not None else '-'
                report += f"Cube #{cube} [ZX:{label}] : {self.walker.nx_graph.get_cube_kind(cube)}@{self.walker.nx_graph.get_cube_position(cube)}\n"

        return report


    def print_report(self, append_cube_report=False):
        print(self.prepare_report(append_cube_report = append_cube_report))


    def write_report(self, filename = None):
        if filename is None:
            filename = f"../../output/txt/old-format-{self.walker.name}.txt"

        output = open(filename, "w")
        output.write(self.prepare_report())
        output.close()