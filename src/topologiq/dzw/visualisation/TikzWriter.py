from topologiq.dzw.BlockGraphSpace import Coordinates
from topologiq.dzw.ZxGraphComponents import EdgeType
from topologiq.dzw.ZxGraphWalker import ZxGraphWalker

class TikzWriter:
    AXES = ['X', 'Y', 'Z']

    def __init__(self, walker: ZxGraphWalker):
        self.walker = walker

    @staticmethod
    def find_axis(step: Coordinates):
        step = step.as_tuple()

        for index in range(3):
            if step[index] != 0:
                return TikzWriter.AXES[index]

        return "U"

    def write_file(self, filename = None):
        if filename is None:
            filename = f"../../output/tikz/volumetric-zx-diagram-{self.walker.name}.tex"

        output = open(filename, "w")
        output.write("\\documentclass[tikz, preview, border=1pt]{standalone}\n")
        output.write("\\input{tikz-volumetric-zx-graph.tex}\n")

        output.write("\\begin{document}\n")

        output.write("\t\\ZXGraph{\n")

        for cube in self.walker.nx_graph.get_cubes():
            cube_type = self.walker.nx_graph.get_cube_kind(cube).get_type()
            cube_reach = self.walker.nx_graph.get_cube_kind(cube).get_reach().value.as_tuple()
            cube_plane = 'U'
            for index in range(3):
                if cube_reach[index] != 0:
                    cube_plane = TikzWriter.AXES[index]

            cube_position = self.walker.nx_graph.get_cube_position(cube)
            # TODO: scaling needed due to current implementation of the path-finder
            cube_position = cube_position.div(3)
            line = f"\t\t\\Node[type={cube_type}, plane={cube_plane}, identifier=N{cube}]"
            line += "{" + str(cube_position) + "}\n"
            output.write(line)

        for source_cube, target_cube in self.walker.nx_graph.get_pipes():
            source_position = self.walker.nx_graph.get_cube_position(source_cube)
            target_position = self.walker.nx_graph.get_cube_position(target_cube)

            line = f"\t\t\\Edge[axis={TikzWriter.find_axis(target_position - source_position)}]"
            line += "{N" + str(source_cube) + "}{N" + str(target_cube) + "}\n"

            output.write(line)

            # \Edge[axis=Z]{S1}{E1}
            # \Edge[axis=Z]{E1}{E2}
            # \Edge[axis=X]{E2}{E3}
            # \Edge[axis=Y]{E3}{E4}
            # \Edge[axis=Z]{E4}{E5}
            # \Edge[axis=X]{E5}{E6}
            # \Edge[axis=Z]{E6}{S2}

        output.write("\t}\n")
        output.write("\\end{document}\n")

        output.close()