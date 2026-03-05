from topologiq.utils.coordinates import Coordinates

class RayBeam:
    def __init__(self, source: Coordinates, direction: Coordinates):
        if len(direction) != 1 and direction.non_zeroes() == 1:
            raise Exception(f"Beam direction must be a unit step.")

        self.source = source
        self.direction = direction

    def interrupted_by(self, that):
        # compute the t = (p - s) / d must be the same for all components
        # or, say d = (1, 0, 0), then p and s must have equal y&z and p.x > s.x
        pass

    def intersected_by(self, that):
        delta = self.direction.cross(that.direction)

        if delta == 0:
            return False

        sigma = that.source - self.source
        t1 = sigma.cross(self.direction) / delta
        t2 = sigma.cross(that.direction) / delta
        return t1 >= 1 and t2 >= 1

    def to_array(self, length: int = 10):
        return [ self.source + i * self.direction for i in range(1, length+1) ]

    def __str__(self):
        return f"@{self.source}->{self.direction}"

    def __repr__(self):
        return str(self)