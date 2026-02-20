from unittest import TestCase

from topologiq.dzw.utils.coordinates import Coordinates
from topologiq.dzw.helpers.spacetime import Spacetime

class TestSpacetime(TestCase):
    def test_get_orthogonal_plane_XY_XP_XZ(self):
        self.assertEqual(Spacetime.XZ, Spacetime.get_orthogonal_plane(Spacetime.XY, Spacetime.XP))

    def test_get_orthogonal_plane_XY_YP_YZ(self):
        self.assertEqual(Spacetime.YZ, Spacetime.get_orthogonal_plane(Spacetime.XY, Spacetime.YP))

    def test_get_orthogonal_plane_YZ_YP_XY(self):
        self.assertEqual(Spacetime.XY, Spacetime.get_orthogonal_plane(Spacetime.YZ, Spacetime.YP))

    def test_get_orthogonal_plane_YZ_ZP_XZ(self):
        self.assertEqual(Spacetime.XZ, Spacetime.get_orthogonal_plane(Spacetime.YZ, Spacetime.ZP))

    def test_get_orthogonal_plane_XZ_XP_XY(self):
        self.assertEqual(Spacetime.XY, Spacetime.get_orthogonal_plane(Spacetime.XZ, Spacetime.XP))

    def test_get_orthogonal_plane_XZ_ZP_YZ(self):
        self.assertEqual(Spacetime.YZ, Spacetime.get_orthogonal_plane(Spacetime.XZ, Spacetime.ZP))

    def test_get_constellation_ALL(self):
        expected = [step for step in Spacetime.STEPS]
        produced = Spacetime.get_constellation(Spacetime.ORIGIN)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_XY(self):
        expected = [step for step in [Spacetime.XM, Spacetime.XP, Spacetime.YM, Spacetime.YP]]
        produced = Spacetime.get_constellation(Spacetime.ORIGIN, restriction = Spacetime.XY)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_YZ(self):
        expected = [step for step in [Spacetime.ZM, Spacetime.ZP, Spacetime.YM, Spacetime.YP]]
        produced = Spacetime.get_constellation(Spacetime.ORIGIN, restriction = Spacetime.YZ)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_XZ(self):
        expected = [step for step in [Spacetime.ZM, Spacetime.ZP, Spacetime.XM, Spacetime.XP]]
        produced = Spacetime.get_constellation(Spacetime.ORIGIN, restriction = Spacetime.XZ)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_line_of_sight1(self):
        expected = Coordinates(1, 0, 0)
        produced = Spacetime.get_direction(Coordinates(0, 0, 0), Coordinates(1, 0, 0))
        self.assertEqual(expected, produced)

    def test_get_line_of_sight2(self):
        expected = Coordinates(-1, 0, 0)
        produced = Spacetime.get_direction(Coordinates(0, 0, 0), Coordinates(-27, 0, 0))
        self.assertEqual(expected, produced)