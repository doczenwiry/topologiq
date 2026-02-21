from numpy import array
from vedo import Cube, Box

from topologiq.dzw.utils.components_bg import CubeId, CubeKind
from topologiq.dzw.utils.components_zx import NodeId, EdgeType
from topologiq.dzw.utils.coordinates import Coordinates

BG_COLORS = {
    'U': [128, 128, 128],
    'O': [ 96,  96,  96],
    'X': [245,  39,  39],
    'Y': [ 49, 245,  39],
    'Z': [ 39,  87, 245],
}

class BgCube(Cube):
    LARGE = 1.00
    SMALL = 0.75

    def __init__(self, cube: CubeId, kind: CubeKind, position: Coordinates):
        super().__init__(position.as_tuple(), side = BgCube.LARGE if kind != CubeKind.OOO else BgCube.SMALL)

        self.bg_cube: CubeId = cube

        # Assigning colors to faces
        self.cellcolors = array([ BG_COLORS[ kind.name[f // 2] ] for f in range(6) ])

        # Draw black lines along the edges of this cube
        super().linecolor('k')
        super().linewidth(3)

        # Scale everything down by 1/4
        super().scale(0.25)

class BgPipe(Box):
    LENGTH = 3.00
    DIAMETER = 0.60

    def __init__(self,
        source: CubeId, source_kind: CubeKind, source_position: Coordinates,
        target: CubeId, target_kind: CubeKind, target_position: Coordinates,
        pipe_type: EdgeType
    ):
        # Determine the position where this pipe will be placed
        distance = target_position - source_position
        position = source_position + distance.div(2.0)
        # Compute the measurements of this pipe (i.e. length, width, height) according to its direction
        measures = [ BgPipe.LENGTH if d != 0 else BgPipe.DIAMETER for d in distance ]

        super().__init__(position.as_tuple(), size = measures)

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
            colors.append(BG_COLORS[color])
            colors.append(BG_COLORS[color])

        self.cellcolors = colors

        super().linecolor('k')
        super().linewidth(3)
        super().scale(0.25)