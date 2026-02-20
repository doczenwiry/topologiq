from unittest import TestCase

from topologiq.dzw.utils.components_bg import CubeKind
from topologiq.dzw.helpers.spacetime_helper import SpacetimeHelper, Coordinates
from topologiq.dzw.utils.components_zx import EdgeType
from topologiq.dzw.helpers.blockgraph_helper import BlockGraphHelper

class TestSpacetimeHelper(TestCase):
    def test_infer_pipe_type1(self):
        produced = BlockGraphHelper.infer_pipe_type(CubeKind.XZZ, CubeKind.XZZ)
        expected = { EdgeType.IDENTITY }
        self.assertIn(expected, produced)

    def test_infer_pipe_type2(self):
        produced = BlockGraphHelper.infer_pipe_type(CubeKind.XZZ, CubeKind.ZXZ)
        expected = { EdgeType.HADAMARD }
        self.assertEqual(expected, produced)

    def test_infer_pipe_type3(self):
        produced = BlockGraphHelper.infer_pipe_type(CubeKind.XZZ, CubeKind.ZXX)
        expected = { EdgeType.HADAMARD }
        self.assertEqual(expected, produced)

    def test_infer_pipe_type4(self):
        produced = BlockGraphHelper.infer_pipe_type(CubeKind.XZZ, CubeKind.XZX)
        expected = { EdgeType.IDENTITY }
        self.assertEqual(expected, produced)

    def test_get_constellation(self):
        produced = sorted(BlockGraphHelper.get_candidate_constellation(
            origin_kind = CubeKind.XZZ, origin_position = SpacetimeHelper.ORIGIN, pipe_type = EdgeType.IDENTITY)
        )
        specification = {
            CubeKind.XZZ: [SpacetimeHelper.YM, SpacetimeHelper.YP, SpacetimeHelper.ZM, SpacetimeHelper.ZP],
            CubeKind.XZX: [SpacetimeHelper.ZM, SpacetimeHelper.ZP],
            CubeKind.XXZ: [SpacetimeHelper.YM, SpacetimeHelper.YP],
            CubeKind.OOO: [SpacetimeHelper.YM, SpacetimeHelper.YP, SpacetimeHelper.ZM, SpacetimeHelper.ZP],
            CubeKind.YYY: [SpacetimeHelper.YM, SpacetimeHelper.YP, SpacetimeHelper.ZM, SpacetimeHelper.ZP],
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
        set1 = {(CubeKind.XZZ, SpacetimeHelper.ORIGIN)}
        self.assertTrue((CubeKind.XZZ, SpacetimeHelper.ORIGIN) in set1)
