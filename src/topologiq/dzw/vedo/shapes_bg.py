from numpy import array
from vedo import Assembly, Cube, Box, Text3D

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.utils.components_bg import CubeId, CubeKind
from topologiq.dzw.utils.components_zx import NodeId, EdgeType
from topologiq.dzw.utils.coordinates import Coordinates
from topologiq.dzw.vedo.color_scheme import COLOR_RGBS, COLOR_NAMES

BG_COLORS = {
    'U': [128, 128, 128],
    'O': [ 96,  96,  96],
    'X': [245,  39,  39],
    'Y': [ 49, 245,  39],
    'Z': [ 39,  87, 245],
}

SCALING_FACTOR = 3.0

class BgCube(Assembly):
    LARGE = 1.00
    SMALL = 0.75

    def __init__(self, anx: AugmentedNxGraph, cube: CubeId):
        kind = anx.get_cube_kind(cube)
        position = anx.get_cube_position(cube)
        position = (SCALING_FACTOR * position.x, SCALING_FACTOR * position.y, SCALING_FACTOR * position.z)

        # Initialise the cube
        self.__cube = Cube(pos = position, side = BgCube.LARGE if kind != CubeKind.OOO else BgCube.SMALL)
        # Assign colors to the six faces of the cube (i.e. +X,-X,+Y,-Y,+Z,-Z)
        self.__cube.cellcolors = array([ COLOR_RGBS[ kind.name[f // 2] ] for f in range(6) ])
        self.__cube.linecolor('k')
        self.__cube.linewidth(3)

        # Initialise the label
        node = anx.get_node(cube)
        label = str(node) if node is not None else ""
        self.__text = Text3D(label, pos = position, font = 'Calco', justify = 'centered', c = 'white')

        self.__visible = True
        self.bg_cube: CubeId = cube

        super().__init__( [ self.__cube, self.__text ] )

    def show(self):
        self.alpha(1.0)
        self.__visible = True

    def hide(self):
        self.alpha(0.0)
        self.__visible = False

class BgPipe(Box):
    LENGTH = 2.65
    DIAMETER = 0.60

    def __init__(self, source: CubeId, target: CubeId, anx : AugmentedNxGraph):
        # Determine the position where this pipe will be placed
        source_kind = anx.get_cube_kind(source)
        target_kind = anx.get_cube_kind(target)
        source_position = anx.get_cube_position(source)
        target_position = anx.get_cube_position(target)
        distance = target_position - source_position
        position = source_position + distance.div(2.0)
        position = (SCALING_FACTOR * position.x, SCALING_FACTOR * position.y, SCALING_FACTOR * position.z)
        # Compute the measurements of this pipe (i.e. length, width, height) according to its direction
        measures = [ SCALING_FACTOR * BgPipe.LENGTH if d != 0 else SCALING_FACTOR * BgPipe.DIAMETER for d in distance ]

        super().__init__(position, size = measures)

        self.__visible = True
        self.bg_source: CubeId = source
        self.bg_target: CubeId = target

        colors = []
        distance = distance.as_tuple()
        for c in range(3):
            if distance[c] == 0:
                source_color = source_kind.name[c]
                target_color = target_kind.name[c]
                if source_color != 'O' and target_color != 'O' and source_color != target_color:
                    raise Exception(f"Incompatible cubes [{source_kind}/{target_kind}] [{distance}].")
                if source_color != 'O':
                    color = source_color
                elif target_color != 'O':
                    color = target_color
                else:
                    color = 'U'
            else:
                color = 'O'
            colors.append(COLOR_RGBS[color])
            colors.append(COLOR_RGBS[color])

        self.cellcolors = colors

        self.linecolor('k')
        self.linewidth(3)
        self.scale(0.25)

    def show(self):
        self.alpha(1.0)
        self.__visible = True

    def hide(self):
        self.alpha(0.0)
        self.__visible = False
