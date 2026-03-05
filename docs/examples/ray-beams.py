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

    all_positions = list(filter(lambda p : not np.array_equal(p, RayBeam.ORIGIN), [ np.array(step1) + np.array(step2) for step1, step2 in product(steps, steps) ]))
    all_beams1 = [ RayBeam(RayBeam.ORIGIN, np.array(direction)) for direction in steps ]
    all_beams2 = [ RayBeam(source, np.array(direction)) for source in all_positions for direction in steps ]

    print(f"All positions :")
    for position in all_positions:
        print(f"> Position : {position}")

    count = 0
    cases = 0
    for beam1, beam2 in product(all_beams1, all_beams2):
        test1 = beam1.intersected_by_array(beam2)
        test2 = beam1.intersected_by(beam2)
        if test1 != test2:
            print(f"{beam1} x {beam2} : {test1} != {test2}")
            direction_lineup = np.dot(beam1.direction, beam2.direction)
            sigma = beam2.source - beam1.source
            position_lineup = np.dot(sigma, beam1.direction)
            cross = np.linalg.cross(beam1.direction, beam2.direction)
            delta = np.dot(cross, cross)
            print(f"> Delta : {delta}, sigma : {sigma}")
            print(f"> Directions : {direction_lineup}")
            print(f"> Positions : {position_lineup}")
            count += 1
        cases += 1
    print(f"Erroneous intersections : {count}/{cases}\n")