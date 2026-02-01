from enum import Enum

from topologiq.dzw.ZxGraphComponents import NodeType, EdgeType
from topologiq.dzw.BlockGraphSpace import Plane, BlockGraphSpace, Coordinates, Step


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
        plane1 = kind1.get_plane()
        plane2 = kind2.get_plane()
        # TODO: compute kind-to-kind-consistency along the step between the two positions
        kk_consistent = True  # kind1.compatible(kind2, position1 - position2)
        return md_consistent and kk_consistent

    def get_candidate_constellation(self, pipe_type : EdgeType = EdgeType.IDENTITY)\
            -> list[ tuple[Step, 'CubeKind'] ]:
        constellation = []

        source_type = self.get_type()
        source_plane = self.get_plane()

        for step in BlockGraphSpace.STEPS:
            if source_plane.contains(step):
                orthogonal_plane = BlockGraphSpace.get_orthogonal_plane(source_plane, step)
                # A cube can always have an adjacent cube of the same color connected by
                # - IDENTITY pipe in the same plane
                # - HADAMARD pipe in the plane orthogonal along the step
                candidate_plane = source_plane if pipe_type == EdgeType.IDENTITY else orthogonal_plane
                constellation.append( (step , CubeKind.convert(source_type, candidate_plane)) )
                # A cube can always have an adjacent cube of the other color connected by
                # - IDENTITY pipe in the plane orthogonal along the step
                # - HADAMARD pipe in the same plane
                candidate_plane = orthogonal_plane if pipe_type == EdgeType.IDENTITY else source_plane
                constellation.append( (step , CubeKind.convert(NodeType.flip(source_type), candidate_plane)) )

        return constellation

    @staticmethod
    def convert(node_type: NodeType, node_plane: Plane):
        if node_type == NodeType.X:
            if node_plane == Plane.XY:
                return CubeKind.ZZX
            elif node_plane == Plane.XZ:
                return CubeKind.ZXZ
            else:
                return CubeKind.XZZ
        elif node_type == NodeType.Z:
            if node_plane == Plane.XY:
                return CubeKind.XXZ
            elif node_plane == Plane.XZ:
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

    def get_plane(self) -> Plane:
        if self == CubeKind.XZZ or self == CubeKind.ZXX:
            return Plane.YZ
        elif self == CubeKind.ZXZ or self == CubeKind.XZX:
            return Plane.XZ
        elif self == CubeKind.ZZX or self == CubeKind.XXZ:
            return Plane.XY
        else: # self.name == CubeKind.OOO or self.name == CubeKind.YYY
            raise ValueError(f"Not applicable to cube kind {self.value}")

    @staticmethod
    def infer_pipe_type(source: 'CubeKind', target: 'CubeKind') -> EdgeType:
        source_type = source.get_type()
        target_type = target.get_type()
        source_plane = source.get_plane()
        target_plane = target.get_plane()

        if source_type not in [ NodeType.X, NodeType.Z ] or target_type not in [ NodeType.X, NodeType.Z ]:
            raise NotImplemented("Can only infer type of pipe between X and Z nodes for now.")

        same_type = source_type == target_type
        same_plane = source_plane == target_plane

        return EdgeType.IDENTITY if same_type == same_plane else EdgeType.HADAMARD

    @staticmethod
    def validate_path(source_kind: 'CubeKind', source_position: Coordinates,
                      target_kind: 'CubeKind', target_position: Coordinates,
                      edge_type : EdgeType, path: list[tuple[Coordinates, 'CubeKind']]):

        is_hadamard_path = False
        previous_kind: CubeKind = source_kind
        previous_plane: Plane = source_kind.get_plane()
        previous_position: Coordinates = source_position
        for (current_position, current_kind) in path:
            # Check that the step taken lies in both planes of successive cubes
            step_taken = current_position - previous_position
            current_plane = current_kind.get_plane()
            if not previous_plane.contains(step_taken) or not current_plane.contains(step_taken):
                raise Exception(f"Step taken must lie in the plane of both successive cubes [{previous_kind}@{previous_position} vs. {current_kind}@{current_position}].")

            # Update the type of the path based on the type of the pipe
            if CubeKind.infer_pipe_type(previous_kind, current_kind) == EdgeType.HADAMARD:
                is_hadamard_path = not is_hadamard_path

            previous_position = current_position
            previous_kind = current_kind
            previous_plane = current_plane

        # Check that the step taken lies in both planes of successive cubes
        step_taken = target_position - previous_position
        if not previous_plane.contains(step_taken) or not target_kind.get_plane().contains(step_taken):
            raise Exception(f"Step taken must lie in the plane of both successive cubes [{previous_kind}@{previous_position} vs. {target_kind}@{target_position}].")

        # Update the type of the path based on the type of the pipe
        if CubeKind.infer_pipe_type(previous_kind, target_kind) == EdgeType.HADAMARD:
            is_hadamard_path = not is_hadamard_path

        if is_hadamard_path != (edge_type == EdgeType.HADAMARD):
            raise Exception(f"Path type must match edge type [Hadamard-inconsistency].")

    def __str__(self):
        return self.name