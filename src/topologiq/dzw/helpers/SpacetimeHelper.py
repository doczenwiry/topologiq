from topologiq.dzw.utils.CubeKind import CubeKind
from topologiq.dzw.utils.Spacetime import Coordinates, Spacetime
from topologiq.dzw.utils.EdgeType import EdgeType
from topologiq.dzw.utils.NodeType import NodeType

from logging import getLogger
console = getLogger(__name__)

class SpacetimeHelper:
    @staticmethod
    def infer_pipe_type(source: CubeKind, target: CubeKind) -> set[EdgeType]:
        source_type = source.get_type()
        target_type = target.get_type()
        source_reach = source.get_reach()
        target_reach = target.get_reach()

        if source_type in [ NodeType.O , NodeType.Y ] or target_type in [ NodeType.O , NodeType.Y ]:
            return { EdgeType.IDENTITY , EdgeType.HADAMARD }

        same_type = source_type == target_type
        same_reach = source_reach == target_reach

        return { EdgeType.IDENTITY } if same_type == same_reach else { EdgeType.HADAMARD }

    @staticmethod
    def get_candidate_constellation(
        origin_kind: CubeKind,
        origin_position: Coordinates = Spacetime.ORIGIN,
        pipe_type: EdgeType = EdgeType.IDENTITY
    ) -> list[tuple[CubeKind, Coordinates]]:
        constellation = []

        origin_reach = origin_kind.get_reach()

        for step in origin_reach.get_step_constellation():
            candidate_position = origin_position + step

            for node_type in [ NodeType.X, NodeType.Z ]:
                for node_reach in Spacetime.PLANES:
                    if node_reach.contains(step):
                        candidate_kind = CubeKind.convert(node_type, node_reach)
                        if pipe_type in SpacetimeHelper.infer_pipe_type(candidate_kind, origin_kind):
                            constellation.append( (candidate_kind, candidate_position) )

            # A cube can always have an adjacent cube of kind OOO (both IDENTITY and HADAMARD pipes are possible)
            constellation.append( (CubeKind.OOO, candidate_position) )

            # A cube can always have an adjacent cube of kind OOO (both IDENTITY and HADAMARD pipes are possible)
            constellation.append( (CubeKind.YYY, candidate_position) )

        console.debug(f"Constellation of {len(constellation)} points.")
        for kind, position in constellation:
            console.debug(f"> {kind}@{position}")

        return constellation