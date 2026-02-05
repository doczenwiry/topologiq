from enum import Enum

from topologiq.dzw.ZxGraphComponents import NodeType, EdgeType
from topologiq.dzw.BlockGraphSpace import Reach, BlockGraphSpace, Coordinates, Step


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

    def get_candidate_constellation(self, pipe_type : EdgeType = EdgeType.IDENTITY)\
            -> list[ tuple[Step, 'CubeKind'] ]:
        constellation = []

        source_type = self.get_type()
        source_reach = self.get_reach()

        for step in BlockGraphSpace.STEPS:
            if source_reach.contains(step):
                orthogonal_plane = BlockGraphSpace.get_orthogonal_plane(source_reach, step)
                # A cube can always have an adjacent cube of the same color connected by
                # - IDENTITY pipe in the same plane
                # - HADAMARD pipe in the plane orthogonal along the step
                candidate_plane = source_reach if pipe_type == EdgeType.IDENTITY else orthogonal_plane
                constellation.append( (step , CubeKind.convert(source_type, candidate_plane)) )
                # A cube can always have an adjacent cube of the other color connected by
                # - IDENTITY pipe in the plane orthogonal along the step
                # - HADAMARD pipe in the same plane
                candidate_plane = orthogonal_plane if pipe_type == EdgeType.IDENTITY else source_reach
                constellation.append( (step , CubeKind.convert(NodeType.flip(source_type), candidate_plane)) )

        return constellation

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
        elif self == CubeKind.OOO:
            return Reach.XYZ
        else: # self.name == CubeKind.YYY
            raise ValueError(f"Not applicable to cube kind {self.name}")

    @staticmethod
    def infer_pipe_type(source: 'CubeKind', target: 'CubeKind') -> EdgeType:
        source_type = source.get_type()
        target_type = target.get_type()
        source_reach = source.get_reach()
        target_reach = target.get_reach()

        if source_type in [ NodeType.Y ] or target_type in [ NodeType.Y ]:
            raise NotImplemented("Cannot infer type of pipe w.r.t Y nodes for now.")

        same_type = source_type == target_type
        same_reach = source_reach == target_reach

        return EdgeType.IDENTITY if same_type == same_reach else EdgeType.HADAMARD

    def __str__(self):
        return self.name