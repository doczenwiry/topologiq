import networkx as nx
from sympy.geometry import Point3D, Ray3D

Coordinates = Point3D
SympyBeam = Ray3D
SympyBeams = list[SympyBeam]

CubeId = int
CubeList = list[CubeId]

NX_GRAPH_CUBE_BEAMS = "sympy-beams"

def check_path_to_beam_clashes(
    nx_g: nx.Graph,
    source: CubeId,
    target: CubeId,
    path_coordinates: list[Coordinates],
    beams_interrupted_by_path: int = 0,
    priority_cubes: CubeList | None = None,
    twin_mode: bool = False, # Twin creation should be taken care of outside this function
    ids_to_twin: tuple[CubeId] | None = None, # Shouldn't this be a CubeList or a tuple[CubeId, CubeId] ?
) -> tuple[bool, int, CubeList]:
    if priority_cubes is None: priority_cubes = []
    if ids_to_twin is None: ids_to_twin = []

    for cube in nx_g.nodes(): # CubeId
        # What is the testing of source_index against cube_index about ?
        source_index = ids_to_twin.index(source) if source in ids_to_twin else -1
        cube_index = ids_to_twin.index(cube) if cube in ids_to_twin else -1
        if source_index < cube_index:
            continue

        beams_to_check: SympyBeams = nx_g.nodes[cube][NX_GRAPH_CUBE_BEAMS]

        if beams_to_check is None:
            continue

        if twin_mode and not (cube in ids_to_twin and source_index < cube_index):
            cube_degree = sum(
                1 for c in nx_g.neighbors(cube)
                if c not in ids_to_twin or (source_index < ids_to_twin.index(c))
            )
        else:
            cube_degree = nx_g.degree[cube] # get_node_degree(nx_g, cube_id)
        cube_unrealised_edges = cube_degree - nx_g.nodes[cube]["completed"]

        if twin_mode and cube in ids_to_twin:
            if source_index > cube_index: # What about when indices are equal ?
                cube_unrealised_edges = 0

        beams_interrupted = sum(
            1 for beam in beams_to_check
            if any(beam.contains(position) for position in path_coordinates)
        )
        beams_interrupted_by_path += beams_interrupted

        # Append to priority IDs for all cubes with problems
        # Flip check if even ONE cube has problems
        src_tgt_adjust = 1 if (cube in (source, target) and source != target) else 0
        if len(beams_to_check) - beams_interrupted + src_tgt_adjust < min(cube_unrealised_edges, 1):
            priority_cubes.append(cube)

    clash = len(priority_cubes) > 0
    return clash, beams_interrupted_by_path, priority_cubes

def check_tgt_beam_clashes(
    nx_g: nx.Graph,
    source: CubeId,
    target: CubeId,
    target_beams: SympyBeams,
    target_edge_count: int
) -> bool:
    critical_interruption = False

    if len(target_beams) == 0:
        return critical_interruption

    target_beams_intersected: set[SympyBeam] = set()

    # Check target against beams of each other cube in 3D space
    for cube in nx_g.nodes():
        if cube == source or cube == target:
            continue

        # Reset trackers on every cube irrespectively
        critical_interruption = False

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
            critical_interruption = True

        target_beams_intersected.update(
            filter(
                lambda target_beam: any(bool(target_beam.intersection(beam)) for beam in cube_beams),
                target_beams
            )
        )

    if len(target_beams) - len(target_beams_intersected) < target_edge_count - 1:
        critical_interruption = True

    return critical_interruption