from unittest import TestCase

from topologiq.dzw.utils.CubeKind import CubeKind
from topologiq.dzw.utils.Spacetime import Step, Spacetime, Coordinates
from topologiq.dzw.utils.ZxGraphComponents import EdgeType
from topologiq.dzw.helpers.SpacetimeHelper import SpacetimeHelper

class TestSpacetimeHelper(TestCase):
    def test_infer_pipe_type1(self):
        produced = SpacetimeHelper.infer_pipe_type(CubeKind.XZZ, CubeKind.XZZ)
        expected = EdgeType.IDENTITY
        self.assertEqual(produced, expected)

    def test_infer_pipe_type2(self):
        produced = SpacetimeHelper.infer_pipe_type(CubeKind.XZZ, CubeKind.ZXZ)
        expected = EdgeType.HADAMARD
        self.assertEqual(produced, expected)

    def test_infer_pipe_type3(self):
        produced = SpacetimeHelper.infer_pipe_type(CubeKind.XZZ, CubeKind.ZXX)
        expected = EdgeType.HADAMARD
        self.assertEqual(produced, expected)

    def test_infer_pipe_type4(self):
        produced = SpacetimeHelper.infer_pipe_type(CubeKind.XZZ, CubeKind.XZX)
        expected = EdgeType.IDENTITY
        self.assertEqual(produced, expected)

    def test_get_constellation(self):
        produced = sorted(SpacetimeHelper.get_candidate_constellation(
            origin_kind = CubeKind.XZZ, origin_position = Spacetime.ORIGIN, pipe_type = EdgeType.IDENTITY)
        )
        specification = {
            CubeKind.XZZ: [Step.YM, Step.YP, Step.ZM, Step.ZP],
            CubeKind.XZX: [Step.ZM, Step.ZP],
            CubeKind.XXZ: [Step.YM, Step.YP],
            CubeKind.OOO: [Step.YM, Step.YP, Step.ZM, Step.ZP],
            CubeKind.YYY: [Step.YM, Step.YP, Step.ZM, Step.ZP],
        }

        expected : list[tuple[CubeKind, Coordinates]] = []
        for kind, positions in specification.items():
            for position in positions:
                expected.append( (kind, position.value) )
        expected = sorted(expected)

        self.assertEqual(produced, expected)

    def test_bgc1(self):
        set1 = { CubeKind.XZZ }
        set2 = { CubeKind.XZZ }
        self.assertEqual(set1, set2)

    def test_bgc2(self):
        set1 = {(CubeKind.XZZ, Spacetime.ORIGIN)}
        self.assertTrue((CubeKind.XZZ, Spacetime.ORIGIN) in set1)
