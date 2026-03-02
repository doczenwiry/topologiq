from itertools import product

from topologiq.utils.coordinates import Coordinates

class Beam:
    def __init__(self, source: Coordinates, direction: Coordinates):
        if len(direction) != 1 and direction.non_zeroes() == 1:
            raise Exception(f"Beam direction must be a unit step.")

        self.source = source
        self.direction = direction

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

def intersects(beam1: Beam, beam2: Beam):
    array1 = beam1.to_array()
    array2 = beam2.to_array()
    return not beam1.source.colinear(beam2.source) and sum(1 for p1 in array1 if p1 in array2) == 1

if __name__ == "__main__":
    steps = [
        Coordinates(+1,  0),
        Coordinates(-1,  0),
        Coordinates( 0, +1),
        Coordinates( 0, -1)
    ]

    all_beams = [ Beam(source, direction) for source in steps for direction in steps ]

    count = 0
    for beam1 in all_beams:
        for beam2 in all_beams:
            test1 = intersects(beam1, beam2)
            test2 = beam1.intersected_by(beam2)
            if test1 != test2:
                print(f"{beam1} x {beam2} : {test1} != {test2}")
                delta = beam1.direction.cross(beam2.direction)
                sigma = beam2.source - beam1.source
                print(f"> Delta: {delta}\n> Sigma: {sigma}")
                pt1 = beam1.direction.cross(sigma)
                pt2 = beam2.direction.cross(sigma)
                print(f"> pt1: {pt1}, pt2: {pt2}")
                if delta != 0:
                    t1 = pt1 / delta
                    t2 = pt2 / delta
                    print(f"> PTS: {t1}, {t2} [{t1 >= 1}/{t2 >= 1}]")
                count += 1
    print(f"Erroneous cases : {count}/{len(all_beams) ** 2}\n")