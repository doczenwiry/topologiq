from enum import Enum
import functools

from topologiq.dzw.utils.NodeType import NodeType
from topologiq.dzw.utils.Spacetime import Reach, Coordinates

class CubeKind(Enum):
    OOO = 0
    XZZ = 1
    ZXZ = 2
    ZZX = 3
    ZXX = 4
    XZX = 5
    XXZ = 6
    YYY = 7

    @staticmethod
    def suitable_kinds(node_type: NodeType):
        if   node_type == NodeType.X:
            return [CubeKind.XZZ, CubeKind.ZXZ, CubeKind.ZZX]
        elif node_type == NodeType.Y:
            return [CubeKind.YYY]
        elif node_type == NodeType.Z:
            return [CubeKind.ZXX, CubeKind.XZX, CubeKind.XXZ]
        elif node_type == NodeType.O:
            return [CubeKind.OOO]
        else:
            raise Exception(f"{node_type} has no representation as a cube of any kind.")

    @staticmethod
    def convert(node_type: NodeType, node_reach: Reach):
        if node_type == NodeType.X:
            if node_reach == Reach.XY:
                return CubeKind.ZZX
            elif node_reach == Reach.XZ:
                return CubeKind.ZXZ
            else:
                return CubeKind.XZZ
        elif node_type == NodeType.Z:
            if node_reach == Reach.XY:
                return CubeKind.XXZ
            elif node_reach == Reach.XZ:
                return CubeKind.XZX
            else:
                return CubeKind.ZXX
        elif node_type == NodeType.Y:
            return CubeKind.YYY
        else: # node_type == NodeType.O:
            return CubeKind.OOO

    def get_type(self) -> NodeType:
        if   self == CubeKind.XZZ or self == CubeKind.ZXZ or self == CubeKind.ZZX:
            return NodeType.X
        elif self == CubeKind.ZXX or self == CubeKind.XZX or self == CubeKind.XXZ:
            return NodeType.Z
        elif self == CubeKind.YYY:
            return NodeType.Y
        else: # self == CubeKind.OOO
            return NodeType.O

    # TODO: a CubeKind.YYY has Reach.XYZ and single port ?
    def get_reach(self) -> Reach:
        if self == CubeKind.XZZ or self == CubeKind.ZXX:
            return Reach.YZ
        elif self == CubeKind.ZXZ or self == CubeKind.XZX:
            return Reach.XZ
        elif self == CubeKind.ZZX or self == CubeKind.XXZ:
            return Reach.XY
        elif self == CubeKind.OOO or self == CubeKind.YYY:
            return Reach.XYZ
        else:
            raise ValueError(f"Not applicable to cube kind {self.name}")

    @functools.total_ordering
    def __lt__(self, other):
        return self.value.__lt__(other.value)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.name