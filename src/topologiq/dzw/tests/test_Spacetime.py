from unittest import TestCase

from topologiq.dzw.utils.coordinates import Coordinates
from topologiq.dzw.helpers.spacetime_helper import SpacetimeHelper

class TestSpacetime(TestCase):
    def test_get_orthogonal_plane_XY_XP_XZ(self):
        self.assertEqual(SpacetimeHelper.XZ, SpacetimeHelper.get_orthogonal_plane(SpacetimeHelper.XY, SpacetimeHelper.XP))

    def test_get_orthogonal_plane_XY_YP_YZ(self):
        self.assertEqual(SpacetimeHelper.YZ, SpacetimeHelper.get_orthogonal_plane(SpacetimeHelper.XY, SpacetimeHelper.YP))

    def test_get_orthogonal_plane_YZ_YP_XY(self):
        self.assertEqual(SpacetimeHelper.XY, SpacetimeHelper.get_orthogonal_plane(SpacetimeHelper.YZ, SpacetimeHelper.YP))

    def test_get_orthogonal_plane_YZ_ZP_XZ(self):
        self.assertEqual(SpacetimeHelper.XZ, SpacetimeHelper.get_orthogonal_plane(SpacetimeHelper.YZ, SpacetimeHelper.ZP))

    def test_get_orthogonal_plane_XZ_XP_XY(self):
        self.assertEqual(SpacetimeHelper.XY, SpacetimeHelper.get_orthogonal_plane(SpacetimeHelper.XZ, SpacetimeHelper.XP))

    def test_get_orthogonal_plane_XZ_ZP_YZ(self):
        self.assertEqual(SpacetimeHelper.YZ, SpacetimeHelper.get_orthogonal_plane(SpacetimeHelper.XZ, SpacetimeHelper.ZP))

    def test_get_constellation_ALL(self):
        expected = [step for step in SpacetimeHelper.STEPS]
        produced = SpacetimeHelper.get_constellation(SpacetimeHelper.ORIGIN)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_XY(self):
        expected = [step for step in [SpacetimeHelper.XM, SpacetimeHelper.XP, SpacetimeHelper.YM, SpacetimeHelper.YP]]
        produced = SpacetimeHelper.get_constellation(SpacetimeHelper.ORIGIN, restriction = SpacetimeHelper.XY)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_YZ(self):
        expected = [step for step in [SpacetimeHelper.ZM, SpacetimeHelper.ZP, SpacetimeHelper.YM, SpacetimeHelper.YP]]
        produced = SpacetimeHelper.get_constellation(SpacetimeHelper.ORIGIN, restriction = SpacetimeHelper.YZ)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_XZ(self):
        expected = [step for step in [SpacetimeHelper.ZM, SpacetimeHelper.ZP, SpacetimeHelper.XM, SpacetimeHelper.XP]]
        produced = SpacetimeHelper.get_constellation(SpacetimeHelper.ORIGIN, restriction = SpacetimeHelper.XZ)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_line_of_sight1(self):
        expected = Coordinates(1, 0, 0)
        produced = SpacetimeHelper.get_line_of_sight( Coordinates(0, 0, 0), Coordinates(1, 0, 0) )
        self.assertEqual(expected, produced)

    def test_get_line_of_sight2(self):
        expected = Coordinates(-1, 0, 0)
        produced = SpacetimeHelper.get_line_of_sight( Coordinates(0, 0, 0), Coordinates(-27, 0, 0) )
        self.assertEqual(expected, produced)