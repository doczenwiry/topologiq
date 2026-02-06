from unittest import TestCase

from topologiq.dzw.utils.Spacetime import Spacetime, Step, Reach


class TestSpacetime(TestCase):
    def test_get_orthogonal_plane_XY_XP_XZ(self):
        self.assertEqual(Reach.XZ, Spacetime.get_orthogonal_plane(Reach.XY, Step.XP.value))

    def test_get_orthogonal_plane_XY_YP_YZ(self):
        self.assertEqual(Reach.YZ, Spacetime.get_orthogonal_plane(Reach.XY, Step.YP.value))

    def test_get_orthogonal_plane_YZ_YP_XY(self):
        self.assertEqual(Reach.XY, Spacetime.get_orthogonal_plane(Reach.YZ, Step.YP.value))

    def test_get_orthogonal_plane_YZ_ZP_XZ(self):
        self.assertEqual(Reach.XZ, Spacetime.get_orthogonal_plane(Reach.YZ, Step.ZP.value))

    def test_get_orthogonal_plane_XZ_XP_XY(self):
        self.assertEqual(Reach.XY, Spacetime.get_orthogonal_plane(Reach.XZ, Step.XP.value))

    def test_get_orthogonal_plane_XZ_ZP_YZ(self):
        self.assertEqual(Reach.YZ, Spacetime.get_orthogonal_plane(Reach.XZ, Step.ZP.value))

    def test_get_constellation_ALL(self):
        expected = [step.value for step in Spacetime.STEPS]
        produced = Spacetime.get_constellation(Spacetime.ORIGIN)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_XY(self):
        expected = [ step.value for step in [ Step.XM, Step.XP, Step.YM, Step.YP ]]
        produced = Spacetime.get_constellation(Spacetime.ORIGIN, restriction = Reach.XY)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_YZ(self):
        expected = [ step.value for step in [ Step.ZM, Step.ZP, Step.YM, Step.YP ]]
        produced = Spacetime.get_constellation(Spacetime.ORIGIN, restriction = Reach.YZ)
        self.assertEqual(sorted(expected), sorted(produced))

    def test_get_constellation_XZ(self):
        expected = [ step.value for step in [ Step.ZM, Step.ZP, Step.XM, Step.XP ]]
        produced = Spacetime.get_constellation(Spacetime.ORIGIN, restriction = Reach.XZ)
        self.assertEqual(sorted(expected), sorted(produced))
