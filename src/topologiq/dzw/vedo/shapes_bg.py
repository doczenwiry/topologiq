from numpy import array
from vedo import Assembly, Cube, Box, Text3D

from topologiq.dzw.helpers.spacetime import Spacetime
from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.utils.components_bg import CubeId, CubeKind
from topologiq.dzw.utils.components_zx import NodeId, EdgeType
from topologiq.dzw.utils.coordinates import Coordinates
from topologiq.dzw.vedo.color_scheme import COLOR_RGBS

GLOBAL_SPACING_FACTOR = 3.0

def cross(vector1: Coordinates, vector2: Coordinates):
    return Coordinates(vector1.y * vector2.z - vector1.z * vector2.y, vector1.z * vector2.x + vector1.x * vector2.z, vector1.x * vector2.y)

class BgCube(Assembly):
    LARGE_CUBE = 1.00
    LARGE_TEXT = 0.50
    FACTOR_SMALLER = 0.75
    SMALL_CUBE = LARGE_CUBE * FACTOR_SMALLER
    SMALL_TEXT = LARGE_TEXT * FACTOR_SMALLER

    def __init__(self, anx: AugmentedNxGraph, cube: CubeId):
        kind = anx.get_cube_kind(cube)
        position = GLOBAL_SPACING_FACTOR * anx.get_cube_position(cube)

        # Initialise the cube
        self.__cube = Cube(pos = position, side = BgCube.LARGE_CUBE if kind != CubeKind.OOO else BgCube.SMALL_CUBE)
        # Assign colors to the six faces of the cube (i.e. +X,-X,+Y,-Y,+Z,-Z)
        self.__cube.cellcolors = array([ COLOR_RGBS[ kind.name[f // 2] ] for f in range(6) ])
        self.__cube.linecolor('k')
        self.__cube.linewidth(3)

        # Initialise the label
        node = anx.get_node(cube)
        label = str(node) if node is not None else ""
        text_size = BgCube.LARGE_TEXT if kind != CubeKind.OOO else BgCube.SMALL_TEXT
        step_scale = 0.55 if kind != CubeKind.OOO else 0.55 * BgCube.FACTOR_SMALLER

        self.__texts = []
        for direction in Spacetime.STEPS:
            face_center = (position + step_scale * direction).as_tuple()
            text = Text3D(txt = label, pos = face_center, s = text_size, font ='Roboto', justify ='centered', c ='white')
            # Rotate the text to line it up with its face
            rotation_axis = cross(Spacetime.ZP, direction).as_tuple()
            text.rotate(angle = 90.0, axis = rotation_axis, point = face_center)
            # Rotate the text to
            if   direction == Spacetime.XP: rotation_angle =  90.0
            elif direction == Spacetime.XM: rotation_angle = -90.0
            elif direction == Spacetime.YP: rotation_angle = 180.0
            else: # direction in [Spacetime.YM, Spacetime.ZP, Spacetime.ZM]
                rotation_angle = 0.0

            text.rotate(angle = rotation_angle, axis = direction.as_tuple(), point = face_center)
            self.__texts.append(text)

        self.__highlighted = False
        self.__visible = True
        self.bg_cube: CubeId = cube

        super().__init__(self.__cube, self.__texts)

    def show_highlight(self):
        self.__cube.linecolor('k5')
        self.__cube.linewidth(6)

    def hide_highlight(self):
        self.__cube.linecolor('k')
        self.__cube.linewidth(3)

    def toggle_visible(self):
        self.__visible = not self.__visible
        if self.__visible:
            self.alpha(1.0)
        else:
            self.alpha(0.0)

class BgPipe(Box):
    LENGTH = GLOBAL_SPACING_FACTOR * 0.205
    DIAMETER = 0.25

    def __init__(self, source: CubeId, target: CubeId, anx : AugmentedNxGraph):
        # Determine the position where this pipe will be placed
        source_kind = anx.get_cube_kind(source)
        source_position = anx.get_cube_position(source)
        target_kind = anx.get_cube_kind(target)
        target_position = anx.get_cube_position(target)
        distances = target_position - source_position
        position = GLOBAL_SPACING_FACTOR * (source_position + distances.div(2.0))
        # Compute the measurements of this pipe (i.e. length, width, height) according to its direction
        measures = [
            GLOBAL_SPACING_FACTOR * (BgPipe.LENGTH if d != 0 else BgPipe.DIAMETER)
            for d in distances
        ]

        super().__init__(position, size = measures)

        self.bg_source: CubeId = source
        self.bg_target: CubeId = target

        colors = []
        distances = distances.as_tuple()
        for c in range(3):
            if distances[c] == 0:
                source_color = source_kind.name[c]
                target_color = target_kind.name[c]
                if source_color != 'O' and target_color != 'O' and source_color != target_color:
                    raise Exception(f"Incompatible cubes [{source_kind}/{target_kind}] [{distances}].")
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

        self.__visible = True
        self.__highlighted = False

    def show_highlight(self):
        self.linecolor('k5')
        self.linewidth(6)

    def hide_highlight(self):
        self.linecolor('k')
        self.linewidth(3)

    def show(self):
        self.alpha(1.0)
        self.__visible = True

    def hide(self):
        self.alpha(0.0)
        self.__visible = False