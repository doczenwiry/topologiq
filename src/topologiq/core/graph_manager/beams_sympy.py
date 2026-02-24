import networkx as nx

from topologiq.core.pathfinder.symbolic import check_is_exit, check_unobstructed
from topologiq.utils.classes import StandardCoord, Coordinates, CubeId, CubeList, SympyBeam, SympyBeams, CubeBeams

NX_GRAPH_CUBE_BEAMS = "beams_sympy"

def check_beams_critical_interruptions(
    nx_g: nx.Graph,
    source: CubeId,
    target: CubeId,
    path_coordinates: list[Coordinates],
    priority_cubes: CubeList | None = None,
    twin_mode: bool = False, # Twin creation should be taken care of outside this function
    ids_to_twin: list[CubeId] | None = None, # What does the order of those represent ?
) -> tuple[bool, int, CubeList]:
    if priority_cubes is None: priority_cubes = []
    if ids_to_twin is None: ids_to_twin = []

    beams_interrupted_by_path = 0

    for cube in nx_g.nodes(): # CubeId
        cube_beams: SympyBeams = nx_g.nodes[cube][NX_GRAPH_CUBE_BEAMS]

        if cube_beams is None:
            continue

        # What is the testing of source_index against cube_index about ?
        source_index = ids_to_twin.index(source) if source in ids_to_twin else -1
        cube_index = ids_to_twin.index(cube) if cube in ids_to_twin else -1
        if source_index < cube_index:
            continue

        if twin_mode and ids_to_twin and nx_g.neighbors(cube):
            cube_degree = sum(
                1 for c in nx_g.neighbors(cube)
                if c not in ids_to_twin or (source_index < ids_to_twin.index(c))
            )
        else:
            cube_degree = nx_g.degree[cube]
        cube_unrealised_edges = cube_degree - nx_g.nodes[cube]["completed"]

        if twin_mode and cube in ids_to_twin:
            if source_index > cube_index: # What about when indices are equal ?
                cube_unrealised_edges = 0

        beams_interrupted = sum(
            1 for beam in cube_beams
            if any(beam.contains(position) for position in path_coordinates)
        )

        beams_interrupted_by_path += beams_interrupted

        # Append to priority IDs for all cubes with problems
        # Flip check if even ONE cube has problems
        src_tgt_adjust = 1 if (cube in (source, target) and source != target) else 0
        if len(cube_beams) - beams_interrupted + src_tgt_adjust < min(cube_unrealised_edges, 1):
            priority_cubes.append(cube)

    critical_interruptions = len(priority_cubes) > 0
    return critical_interruptions, beams_interrupted_by_path, priority_cubes

def check_beams_critical_intersections(
    nx_g: nx.Graph,
    source: CubeId,
    target: CubeId,
    target_beams: SympyBeams = None,
) -> int:
    if target_beams is None: target_beams = []

    target_edge_count = nx_g.nodes[target]["completed"]
    cubes_with_critical_intersections = 0

    if len(target_beams) == 0:
        return cubes_with_critical_intersections

    target_beams_intersected: set[SympyBeam] = set()

    # Check target against beams of each other cube in 3D space
    for cube in nx_g.nodes():
        if cube == source or cube == target:
            continue

        # Count intersections with beams of other cubes
        cube_beams: SympyBeams = nx_g.nodes[cube][NX_GRAPH_CUBE_BEAMS]
        if not cube_beams:
            continue

        cube_number_of_edges = nx_g.degree[cube]
        cube_realised_edges = nx_g.nodes[cube]["completed"]
        cube_unrealised_edges = cube_number_of_edges - cube_realised_edges
        cube_beams_remaining = sum(
            1 for beam in cube_beams
            if all( not bool(beam.intersection(target_beam)) for target_beam in target_beams)
        )

        if cube_beams_remaining < cube_unrealised_edges:
            cubes_with_critical_intersections += 1

        target_beams_intersected.update(
            filter(
                lambda target_beam: any(bool(target_beam.intersection(beam)) for beam in cube_beams),
                target_beams
            )
        )

    if len(target_beams) - len(target_beams_intersected) < target_edge_count - 1:
        cubes_with_critical_intersections += 1

    return cubes_with_critical_intersections

def compute_beams(
    source: StandardCoord,
    source_kind: str | None,
    taken: list[StandardCoord],
    coords_in_path: list[StandardCoord],
) -> tuple[int, SympyBeams]:
    cube_beams: SympyBeams = []

    diffs = [
        (1, 0, 0),
        (-1, 0, 0),
        (0, 1, 0),
        (0, -1, 0),
        (0, 0, 1),
        (0, 0, -1),
    ]

    for d in diffs:
        tgt_c = (
            source[0] + d[0],
            source[1] + d[1],
            source[2] + d[2],
        )

        if check_is_exit(source, source_kind, tgt_c):
            is_unobstr, single_beam, single_beam_short = check_unobstructed(source, tgt_c, taken)
            if is_unobstr and not any([single_beam.contains(coord) for coord in coords_in_path]):
                cube_beams.append(make_beam(source, d))

    return len(cube_beams), cube_beams


def make_beam(source: StandardCoord, direction: StandardCoord):
    source_position = Coordinates(source[0], source[1], source[2])
    beam_direction = Coordinates(direction[0], direction[1], direction[2])
    start_position = source_position + beam_direction
    return SympyBeam(start_position, start_position + beam_direction)

def validate_all_beams(nx_g: nx.Graph, label: str = ""):
    for cube in nx_g.nodes():
        old_beams: CubeBeams = nx_g.nodes[cube]["beams"]
        new_beams: SympyBeams = nx_g.nodes[cube][NX_GRAPH_CUBE_BEAMS]
        validate_beams(cube, old_beams, new_beams, label = label)

def validate_beams(cube: CubeId, old_beams: CubeBeams, new_beams: SympyBeams, label: str = ""):
    if old_beams is None: old_beams = []
    if new_beams is None: new_beams = []

    conv_beams = []
    for obeam in old_beams:
        two_points = obeam.to_array(3)
        source = Coordinates(two_points[1][0], two_points[1][1], two_points[1][2])
        direction = Coordinates(two_points[2][0], two_points[2][1], two_points[2][2])
        conv_beams.append(SympyBeam(source, direction))
    if conv_beams != new_beams:
        new_string = str(new_beams)
        old_string = ""
        for obeam in old_beams:
            old_string += str(obeam.to_array(3))
        raise Exception(f"[{label}] Beam representation mismatch for cube #{cube}:\n>> {new_string}\n>> {old_string}")