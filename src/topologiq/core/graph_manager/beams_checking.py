import networkx as nx

from topologiq.core.pathfinder.symbolic import check_is_exit, check_unobstructed
from topologiq.utils.beams_rays import RayBeam
from topologiq.utils.classes import StandardCoord, Coordinates, CubeId, CubeList, CubeBeams

#TODO: SymPy seems to be quite slow due to its symbolic nature; replace with a numerical alternative (SciPy or NumPy)
NX_GRAPH_CUBE_BEAMS = "beams_rays"

def check_beams_critical_interruptions(
    nx_g: nx.Graph,
    source: CubeId,
    target: CubeId,
    path_coordinates: list[Coordinates],
    twin_mode: bool = False, # Twin creation should be taken care of outside this function
    ids_to_twin: list[CubeId] | None = None, # What does the order of those represent ?
) -> tuple[bool, int, CubeList]:
    """Identify the cubes which suffer from critical interruptions caused by a proposed path.

    In normal circumstances, a beam extends from a side of the cube where a connection is allowed into infinity.
    A beam that does not extend to infinity due to the presence of some cube is said to be interrupted.
    When there are less uninterrupted beams for a cube than its unrealised edges, it is said to have suffered critical interruptions.

    Args:
        nx_g: A nx_graph initially like the input ZX graph but with 3D-amicable structure, updated regularly.
        source: the ID of the cube that is the source of the proposed path
        target: the ID of the cube that is the target of the proposed path
        path_coordinates: the coordinates taken up by the proposed path
        twin_mode: ??
        ids_to_twin: ??

    Returns:
        critical_interruptions: whether the path has caused at least one cube to suffer from critical interruptions
        total_interrupted_beams: the total number of beams interrupted by the proposed path
        cubes_with_critical_interruptions: the IDs of the cubes that have suffered critical interruptions
    """

    if ids_to_twin is None: ids_to_twin = []

    cubes_with_critical_interruptions = []
    total_beams_interrupted_by_path = 0

    for cube in nx_g.nodes(): # CubeId
        cube_beams: list[RayBeam] = nx_g.nodes[cube][NX_GRAPH_CUBE_BEAMS]

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

        cube_beams_interrupted = sum(
            1 for beam in cube_beams
            if any(beam.interrupted_by(position) for position in path_coordinates)
        )

        total_beams_interrupted_by_path += cube_beams_interrupted

        src_tgt_adjust = 1 if (cube in (source, target) and source != target) else 0
        if len(cube_beams) - cube_beams_interrupted + src_tgt_adjust < cube_unrealised_edges:
            cubes_with_critical_interruptions.append(cube)

    critical_interruptions = len(cubes_with_critical_interruptions) > 0
    return critical_interruptions, total_beams_interrupted_by_path, cubes_with_critical_interruptions

def check_beams_critical_intersections(
    nx_g: nx.Graph,
    source: CubeId,
    target: CubeId,
    target_beams: list[RayBeam] = None,
) -> int:
    if target_beams is None: target_beams = []

    target_edges_unrealised = nx_g.degree[target] - nx_g.nodes[target]["completed"]
    cubes_with_critical_intersections = 0

    if len(target_beams) == 0:
        return cubes_with_critical_intersections

    target_beams_intersected: set[RayBeam] = set()

    # Check target against beams of each other cube in 3D space
    for cube in nx_g.nodes():
        if cube == source or cube == target:
            continue

        # Count intersections with beams of other cubes
        cube_beams: list[RayBeam] = nx_g.nodes[cube][NX_GRAPH_CUBE_BEAMS]
        if not cube_beams:
            continue

        cube_number_of_edges = nx_g.degree[cube]
        cube_realised_edges = nx_g.nodes[cube]["completed"]
        cube_unrealised_edges = cube_number_of_edges - cube_realised_edges
        cube_beams_remaining = sum(
            1 for beam in cube_beams
            if all(not beam.intersected_by(target_beam) for target_beam in target_beams)
        )

        if cube_beams_remaining < cube_unrealised_edges:
            cubes_with_critical_intersections += 1

        target_beams_intersected.update(
            filter(
                lambda target_beam: any(target_beam.intersected_by(beam) for beam in cube_beams),
                target_beams
            )
        )

    if len(target_beams) - len(target_beams_intersected) < target_edges_unrealised - 1:
        cubes_with_critical_intersections += 1

    return cubes_with_critical_intersections

def compute_beams(
    source: StandardCoord,
    source_kind: str | None,
    taken: list[StandardCoord],
    coords_in_path: list[StandardCoord],
) -> list[RayBeam]:
    cube_beams: list[RayBeam] = []

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
                cube_beams.append(RayBeam(source, d))

    return cube_beams


# def make_beam(source: StandardCoord, direction: StandardCoord):
#     source_position = Coordinates(source[0], source[1], source[2])
#     beam_direction = Coordinates(direction[0], direction[1], direction[2])
#     start_position = source_position + beam_direction
#     return Beam(start_position, start_position + beam_direction)

def validate_all_beams(nx_g: nx.Graph, label: str = ""):
    for cube in nx_g.nodes():
        old_beams: CubeBeams = nx_g.nodes[cube]["beams"]
        new_beams: list[RayBeam] = nx_g.nodes[cube][NX_GRAPH_CUBE_BEAMS]
        validate_beams(cube, old_beams, new_beams, label = label)

def validate_beams(cube: CubeId, old_beams: CubeBeams, new_beams: list[RayBeam], label: str = ""):
    if old_beams is None: old_beams = []
    if new_beams is None: new_beams = []

    conv_beams = []
    for obeam in old_beams:
        two_points = obeam.to_array(3)
        source = two_points[0]
        direction = (two_points[1][0] - source[0], two_points[1][1] - source[1], two_points[1][2] - source[2])
        conv_beams.append(RayBeam(source, direction))
    if conv_beams != new_beams:
        new_string = str(new_beams)
        old_string = ""
        cnv_string = str(conv_beams)
        for obeam in old_beams:
            points = obeam.to_array(3)
            old_string += f" @{points[0]}->{points[1]}"
        raise Exception(f"[{label}] Beam representation mismatch for cube #{cube}:\n>> {new_string}\n>>{old_string}\n>> {cnv_string}")