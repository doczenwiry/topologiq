from networkx.algorithms.isomorphism.matchhelpers import categorical_doc

from topologiq.dzw.BlockGraphComponents import CubeKind
from topologiq.dzw.BlockGraphSpace import Step, Coordinates, BlockGraphSpace
from topologiq.dzw.ZxGraphComponents import NodeType, EdgeType


class SpacetimeHelper:
    @staticmethod
    def infer_pipe_type(source: CubeKind, target: CubeKind) -> EdgeType:
        source_type = source.get_type()
        target_type = target.get_type()
        source_reach = source.get_reach()
        target_reach = target.get_reach()

        if source_type in [ NodeType.Y ] or target_type in [ NodeType.Y ]:
            raise NotImplemented("Cannot infer type of pipe w.r.t Y nodes for now.")

        same_type = source_type == target_type
        same_reach = source_reach == target_reach

        return EdgeType.IDENTITY if same_type == same_reach else EdgeType.HADAMARD

    @staticmethod
    def get_candidate_constellation(
        origin_kind: CubeKind,
        origin_position: Coordinates = BlockGraphSpace.ORIGIN,
        pipe_type: EdgeType = EdgeType.IDENTITY,
        candidate_types: list[NodeType] = None
    ) -> list[tuple[Coordinates, CubeKind]]:
        constellation = []

        origin_type = origin_kind.get_type()
        origin_reach = origin_kind.get_reach()

        for step in BlockGraphSpace.STEPS:
            if not origin_reach.contains(step):
                continue

            candidate_position = origin_position + step
            orthogonal_plane = BlockGraphSpace.get_orthogonal_plane(origin_reach, step.value)

            if not candidate_types or origin_type in candidate_types:
                # A cube can always have an adjacent cube of the same color connected by
                # - IDENTITY pipe in the same plane
                # - HADAMARD pipe in the plane orthogonal along the step
                candidate_plane = origin_reach if pipe_type == EdgeType.IDENTITY else orthogonal_plane
                constellation.append((candidate_position, CubeKind.convert(origin_type, candidate_plane)))

            if not candidate_types or NodeType.flip(origin_type) in candidate_types:
                # A cube can always have an adjacent cube of the other color connected by
                # - IDENTITY pipe in the plane orthogonal along the step
                # - HADAMARD pipe in the same plane
                candidate_plane = orthogonal_plane if pipe_type == EdgeType.IDENTITY else origin_reach
                constellation.append((candidate_position, CubeKind.convert(NodeType.flip(origin_type), candidate_plane)))

            if not candidate_types or NodeType.O in candidate_types:
                # A cube can always have an adjacent cube of kind OOO (both IDENTITY and HADAMARD pipes are possible)
                constellation.append( (candidate_position, CubeKind.OOO) )

            if not candidate_types or NodeType.Y in candidate_types:
                # A cube can always have an adjacent cube of kind OOO (both IDENTITY and HADAMARD pipes are possible)
                constellation.append( (candidate_position, CubeKind.YYY) )

        return constellation