from itertools import product

from topologiq.utils.beams_rays import RayBeam, Coordinates

import numpy as np

def manhattan_distance(array: np.ndarray) -> int:
    return 0

if __name__ == "__main__":
    steps = [
        (+1,  0,  0),
        (-1,  0,  0),
        ( 0, +1,  0),
        ( 0, -1,  0),
        ( 0,  0, +1),
        ( 0,  0, -1),
    ]

    all_positions = list(filter(
        lambda p : not np.array_equal(p, RayBeam.ORIGIN),
        [ np.add(np.array(step1), np.array(step2), dtype = np.int32) for step1, step2 in product(steps, steps) ])
    )
    all_beams1 = [ RayBeam(RayBeam.ORIGIN, np.array(direction, dtype = np.int32)) for direction in steps ]
    all_beams2 = [ RayBeam(source, np.array(direction, dtype = np.int32)) for source in all_positions for direction in steps ]

    countP = 0
    countM = 0
    countZ = 0
    cases = list(product(all_beams2, all_beams2))
    total = len(cases)
    print(f"Total cases: {total}")
    for beam1, beam2 in cases:
        try:
            beam1.intersected_by(beam2)
        except Exception as e:
            dot = np.dot(beam1.direction, beam2.direction)
            if   dot == -1: countM += 1
            elif dot == +1: countP += 1
            elif dot ==  0: countZ += 1
            else: raise Exception("Something went awfully wrong.")
            raise e
        # cases += 1
    print(f"Erroneous intersections : M{countM} + Z{countZ} + P{countP}/{total}\n")