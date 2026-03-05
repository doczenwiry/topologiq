from itertools import product

from topologiq.utils.beams_rays import RayBeam, Coordinates

import numpy as np

# # Manhattan-collinearity
# def colinear(v1: Coordinates, v2: Coordinates):
#     return sum(1 for i in range(3) if v1[i] == v2[i]) == 2
#
# def interrupts(position: Coordinates, beam: RayBeam):
#     return any(np.array_equal(pos, position) for pos in beam.to_array())
#
# def intersects(bm1: RayBeam, bm2: RayBeam):
#     array1 = bm1.to_array()
#     array2 = bm2.to_array()
#     return not colinear(bm1.source, bm2.source) and sum(1 for p1 in array1 if any(np.array_equal(p1, p2) for p2 in array2)) == 1

if __name__ == "__main__":
    steps = [
        (+1,  0,  0),
        (-1,  0,  0),
        ( 0, +1,  0),
        ( 0, -1,  0),
        ( 0,  0, +1),
        ( 0,  0, -1),
    ]

    all_positions = [ np.array(position) for position in steps ]
    all_beams = [ RayBeam(source, direction) for source in steps for direction in steps]

    count = 0
    cases = 0
    for beam, position in product(all_beams, all_positions):
        test1 = beam.interrupted_by_array(position)
        test2 = beam.interrupted_by(position)
        if test1 != test2:
            print(f"{beam} x {position} : {test1} != {test2}")
            print(f"> RelaP : {position - beam.source}")
            print(f"> BeamD : {beam.direction}")
            print(f"> Cross : {np.linalg.cross(position - beam.source, beam.direction)}")
            signs = 0
            agreement = 0
            for i in range(3):
                print(f"> i:{i} : [{beam.source[i]},{position[i]}]")
                if beam.source[i] == position[i]:
                    agreement += 1
                    print(f">> i:{i} : [{beam.source[i]},{position[i]}]")
                elif np.sign(beam.direction[i]) == np.sign(position[i]):
                    signs += 1
                    print(f">> i:{i} : [{np.sign(beam.source[i])},{np.sign(position[i])}]")
            print(f"> Agreements : {agreement} vs {signs} [{np.sign(-1)}/{np.sign(-2)}]")
            count += 1
        cases += 1
    print(f"Erroneous interruptions : {count}/{cases}\n")

    count = 0
    cases = 0
    for beam1, beam2 in product(all_beams, all_beams):
        test1 = beam1.intersected_by_array(beam2)
        test2 = beam1.intersected_by(beam2)
        if test1 != test2:
            print(f"{beam1} x {beam2} : {test1} != {test2}")
            count += 1
        cases += 1
    print(f"Erroneous intersections : {count}/{cases}\n")