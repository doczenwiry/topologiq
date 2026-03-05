from itertools import product

from topologiq.utils.coordinates import Coordinates
from topologiq.utils.beams_rays import RayBeam


def intersects(bm1: RayBeam, bm2: RayBeam):
    array1 = bm1.to_array()
    array2 = bm2.to_array()
    return not bm1.source.colinear(bm2.source) and sum(1 for p1 in array1 if p1 in array2) == 1

if __name__ == "__main__":
    steps = [
        Coordinates(+1,  0),
        Coordinates(-1,  0),
        Coordinates( 0, +1),
        Coordinates( 0, -1)
    ]

    all_beams = [RayBeam(source, direction) for source in steps for direction in steps]

    count = 0
    for beam1, beam2 in product(all_beams, all_beams):
        test1 = intersects(beam1, beam2)
        test2 = beam1.intersected_by(beam2)
        if test1 != test2:
            print(f"{beam1} x {beam2} : {test1} != {test2}")
            dlt = beam1.direction.cross(beam2.direction)
            sgm = beam2.source - beam1.source
            print(f"> Delta: {dlt}\n> Sigma: {sgm}")
            count += 1
    print(f"Erroneous cases : {count}/{len(all_beams) ** 2}\n")