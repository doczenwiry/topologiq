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

    all_positions3 = list(filter(
        lambda p: not np.array_equal(p, RayBeam.ORIGIN),
        [np.add(np.array(step1), np.array(step2), np.array(step3), dtype=np.int32) for step1, step2, step3 in product(steps, steps, steps)])
    )
    count = 0
    cases = list(product(all_beams1, all_positions3))
    total = len(cases)
    print(f"Total cases for INTERRUPTION : {total}")
    for beam1, position2 in cases:
        if beam1.interrupted_by(position2) != beam1.interrupted_by_array(position2):
            raise Exception(f"Interruption inconsistency detected.\n> {beam1} w/ {position2}")
    print(f"Erroneous INTERRUPTIONS : {count}/{total}\n")

    countP = 0
    countM = 0
    countZ = 0
    cases = list(product(all_beams2, all_beams2))
    total = len(cases)
    print(f"Total cases for INTERSECTION : {total}")
    for beam1, beam2 in cases:
        if beam1.intersected_by(beam2) != beam1.intersected_by_array(beam2):
            relative = np.dot(beam1.direction, beam2.direction)

            if   relative == -1: countM += 1
            elif relative == +1: countP += 1
            elif relative ==  0: countZ += 1
            else: raise Exception("Something went awfully wrong.")

            sigma = beam2.source - beam1.source
            cross = np.cross(beam1.direction, sigma)
            basis = beam1.direction - beam2.direction
            intra = np.all( (basis != 0) | (sigma == 0) )
            joint = np.sign(sigma) * np.sign(basis)
            pos_q = np.count_nonzero(joint < 0) == 0

            report  = f"> Relative orientation : {relative}\n"
            report += f"> Beam 1 : {beam1.to_array()}\n> Beam 2 : {beam2.to_array()}\n"
            report += f"> Sigma : {sigma}, basis : {basis}, cross : {cross}\n"
            report += f"> Intra : {intra}, joint : {joint}, pos_q : {pos_q}\n"

            raise Exception(f"INTERSECTION inconsistency detected : {beam1} / {beam2}\n{report}")
    print(f"Erroneous INTERSECTIONS : M{countM} + Z{countZ} + P{countP}/{total}\n")