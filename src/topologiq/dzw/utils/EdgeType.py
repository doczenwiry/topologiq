from enum import Enum
import pyzx as zx


class EdgeType(Enum):
    IDENTITY = 0
    HADAMARD = 1

    @staticmethod
    def convert(edge_type: zx.EdgeType):
        if edge_type == zx.EdgeType.SIMPLE:
            return EdgeType.IDENTITY
        elif edge_type == zx.EdgeType.HADAMARD:
            return EdgeType.HADAMARD
        else:
            raise ValueError(f"Unsupported edge type: {edge_type}")

    def __str__(self):
        return self.name