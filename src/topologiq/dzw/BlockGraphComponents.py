from enum import Enum

from topologiq.dzw.ZxGraphComponents import NodeType
from topologiq.dzw.BlockGraphSpace import Reach, Coordinates

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
    def from_string(kind: str):
        if kind == "xzz":
            return CubeKind.XZZ
        elif kind == "zxz":
            return CubeKind.ZXZ
        elif kind == "zzx":
            return CubeKind.ZZX
        elif kind == "zxx":
            return CubeKind.ZXX
        elif kind == "xzx":
            return CubeKind.XZX
        elif kind == "xxz":
            return CubeKind.XXZ
        elif kind == "yyy":
            return CubeKind.YYY
        elif kind == "ooo":
            return CubeKind.OOO
        else:
            raise NotImplementedError(f"Unknown cube kind {kind}")

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
    def compatible_adjacent(kind1: 'CubeKind', kind2: 'CubeKind', step: Coordinates) -> bool:
        md_consistent = step.dot(step) == 1
        reach1 = kind1.get_reach()
        reach2 = kind2.get_reach()
        # TODO: compute kind-to-kind-consistency along the step between the two positions
        kk_consistent = True  # kind1.compatible(kind2, position1 - position2)
        return md_consistent and kk_consistent

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

    def __str__(self):
        return self.name