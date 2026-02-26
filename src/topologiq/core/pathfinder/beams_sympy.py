import networkx as nx

from topologiq.core.graph_manager.beams_sympy import NX_GRAPH_CUBE_BEAMS
from topologiq.core.pathfinder.utils import get_manhattan
from topologiq.core.pathfinder.symbolic import check_is_exit, check_unobstructed
from topologiq.utils.beams import RayBeam

from topologiq.utils.classes import StandardCoord, Coordinates, CubeId, CubeList, CubeBeams

def check_beams_critical_intersections(
    nx_g: nx.Graph,
    source: CubeId,
    target: CubeId,
    path_coordinates: list[Coordinates],
    nxt_coords: StandardCoord,
    tgt_coords: StandardCoord,
) -> bool:

    for cube in nx_g.nodes():
        available_beams = nx_g.nodes[cube][NX_GRAPH_CUBE_BEAMS]
        if not available_beams:
            continue

        cube_beams_interrupted = sum(
            1 for beam in available_beams
            if any(beam.contains(position) for position in path_coordinates)
        )

        if cube_beams_interrupted > 0 and nxt_coords == tgt_coords and cube not in (source,target):
            for other in nx_g.nodes():
                other_beams = nx_g.nodes[other][NX_GRAPH_CUBE_BEAMS]
                other_beams_intersected = sum(
                    1 for other_beam in other_beams
                    if any( other_beam.intersects(beam) for beam in available_beams)
                )
                other_unrealised_edges = nx_g.degree[cube] - nx_g.nodes[other]["completed"]
                src_tgt_adjust = 1 if other in (source,target) else 0
                if len(other_beams) + src_tgt_adjust - other_beams_intersected < other_unrealised_edges:
                    return True

        cube_unrealised_edges = 0
        src_tgt_adjust = 1 if cube in (source,target) else 0
        out_pending = 1 if cube not in (source,target) else cube_unrealised_edges
        if len(available_beams) + src_tgt_adjust - cube_beams_interrupted < min(out_pending, 1):
            return True

    return False

# def split_critical_beams(
#     critical_beams: dict[StandardCoord, int, tuple[int, CubeBeams], tuple[int, CubeBeams]],
#     src_tgt_ids: tuple[int, int] | None,
# ) -> tuple[
#     dict[StandardCoord, int, tuple[int, CubeBeams], tuple[int, CubeBeams]],
#     dict[StandardCoord, int, tuple[int, CubeBeams], tuple[int, CubeBeams]],
# ]:
#     """Split critical beams into simple and verbose object containing different kinds of beams.
#
#     This function separates the `critical_beams` object into a quickly iterable object containing
#     coordinates of beams for nodes that needs absolutely all beams they have and a more verbose
#     dictionary containing the beams for nodes that can lose some beams.
#
#     Args:
#         critical_beams: Beams considered critical for future operations.
#         src_tgt_ids: The exact IDs of the source and target cubes.
#         max_span: the longest edge of the bounding box, equivalent to largest beam needed to clear box.
#
#     Returns:
#         unbreakable_beams: The joint beam coordinates for nodes that need all beams they currently have.
#         negotiable_beams: A minified `critical_beams` object containing beams for nodes that can lose some beams.
#
#     """
#
#     unbreakable_beams = {}
#     negotiable_beams = {}
#     for node_id, (
#         node_coords,
#         min_exit_num,
#         node_beams,
#         node_beams_short,
#     ) in critical_beams.items():
#         if node_id not in src_tgt_ids and min_exit_num == len(node_beams):
#             unbreakable_beams[node_id] = (
#                 node_coords,
#                 min_exit_num,
#                 [beam for beam in node_beams],
#                 [beam for beam in node_beams_short],
#             )
#         else:
#             negotiable_beams[node_id] = (
#                 node_coords,
#                 min_exit_num,
#                 [beam for beam in node_beams],
#                 [beam for beam in node_beams_short],
#             )
#
#     return unbreakable_beams, negotiable_beams
#
#
# def check_unbreakable_beams(
#     unbreakable_beams: dict[StandardCoord, int, tuple[int, CubeBeams], tuple[int, CubeBeams]],
#     full_path_coords: list[StandardCoord],
#     src_tgt_ids: tuple[int, int],
# ) -> bool:
#     """Check that move does not break any beams of cubes that need all their exits.
#
#     Args:
#         unbreakable_beams: The joint beam coordinates for nodes that need all beams they currently have.
#         full_path_coords: All coordinates occupied by current path.
#         src_tgt_ids: The exact IDs of the source and target cubes.
#
#     Return:
#         (bool): True if move clears all checks, False otherwise.
#         clash_coords: A list of coordinates where unbreakable beams get broken.
#
#     """
#
#     clash_coords = []
#     for node_id, (_, _, _, node_beams_short) in unbreakable_beams.items():
#         broken_beams = 0
#         for single_beam in node_beams_short:
#             clash_coords = [coord for coord in full_path_coords if single_beam.contains(coord)]
#             if clash_coords:
#                 # Reject if beam is of nodes other src and tgt
#                 if node_id not in src_tgt_ids:
#                     return False, clash_coords
#
#                 # Reject if more than one beam of src and tgt cubes is broken
#                 if broken_beams == 1:
#                     return False, clash_coords
#                 # Add to broken beams if dealing with src or tgt cube
#                 broken_beams += 1
#
#     return True, clash_coords
#
#
# def check_negotiable_beams(
#     negotiable_beams: dict[StandardCoord, int, tuple[int, CubeBeams], tuple[int, CubeBeams]],
#     full_path_coords: list[StandardCoord],
#     src_tgt_ids: tuple[int, int],
# ) -> bool:
#     """Check that move does not break any beams of cubes that need all their exits.
#
#     Args:
#         negotiable_beams: A minified `critical_beams` object containing beams for nodes that can lose some beams.
#         full_path_coords: All coordinates occupied by current path.
#         src_tgt_ids: The exact IDs of the source and target cubes.
#
#     Return:
#         (bool): True if move clears all checks, False otherwise.
#
#     """
#
#     for node_id, (
#         node_coords,
#         min_exit_num,
#         cube_beams,
#         cube_beams_short,
#     ) in negotiable_beams.items():
#         # For each beam of current cube, check if path breaks the beam
#         out_broken_beams = 0
#         for single_beam in cube_beams_short:
#             if any([single_beam.contains(coord) for coord in full_path_coords]):
#                 out_broken_beams += 1
#
#             # If beam is broken, add pre-existing beam-to-beam clashes to consider previously-used allowances
#             for other_node_id, (
#                 other_node_coords,
#                 other_min_exit_num,
#                 other_cube_beams,
#                 other_cube_beams_short,
#             ) in negotiable_beams.items():
#                 adjust = 1 if other_node_id in src_tgt_ids else 0
#                 manhattan_between = get_manhattan(node_coords, other_node_coords)
#                 intersections = [
#                     single_beam.intersects(negotiable_beam, manhattan_between)
#                     for negotiable_beam in other_cube_beams_short
#                 ]
#                 if intersections:
#                     in_broken_beams = sum(intersections) - adjust
#                     out_broken_beams += in_broken_beams
#
#                 # Flip check to false if number of broken beams exceeds tolerance
#                 if len(other_cube_beams) - in_broken_beams < (other_min_exit_num - adjust):
#                     return False
#
#         # Adjust to consider the broken beam of outgoing/incoming edge in src and tgt cubes
#         adjust = 1 if node_id in src_tgt_ids else 0
#
#         # Flip check to false if number of broken beams exceeds tolerance
#         if len(cube_beams) - out_broken_beams < (min_exit_num - adjust):
#             return False
#
#     return True