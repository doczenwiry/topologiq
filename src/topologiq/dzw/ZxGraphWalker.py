import random
from collections import deque

import pyzx as zx
import networkx as nx

from topologiq.dzw.AugmentedNxGraph import AugmentedNxGraph
from topologiq.dzw.BlockGraphSpace import BlockGraphSpace, Coordinates
from topologiq.dzw.BlockGraphComponents import CubeKind
from topologiq.dzw.ZxGraphComponents import EdgeType, NodeType

# TODO: remove once rewrite is done
from topologiq.scripts.graph_manager import run_pathfinder
from topologiq.scripts.pathfinder import pathfinder, get_taken_coords
from topologiq.utils.utils_greedy_bfs import gen_tent_tgt_coords
from topologiq.utils.classes import NodeBeams, PathBetweenNodes

kwargs: dict[str, tuple[int, int] | int] = {
            "weights": (-1, -1),
            "length_of_beams": 99,
}

# graph_manager.py
class ZxGraphWalker:
    def __init__(self, pyzx_graph: zx.graph.base.BaseGraph, circuit_name: str = "circuit"):
        self.name = circuit_name
        self.hide_ports = False # This really belongs in the visualisation layer
        self.min_success_rate = 50
        self.nx_graph = AugmentedNxGraph(pyzx_graph)
        self.number_1st_pass_edges = 0
        self.number_2nd_pass_edges = 0
        self.node_placement_order = []
        self.node_cube_beams = dict()

    def pick_root(self, central_spider: bool = True, deterministic: bool = False) -> int:
        """Pick the spider that will serve as the root of the construction.

        Args:
            deterministic (bool, optional):
                True  => return the candidate spider with the lowest ID
                False => return a random candidate spider
            central_spider (bool, optional):
                True  => candidates are all spiders with maximal degree
                False => candidates are all spiders

        Returns:
            ID of the spider that has been selected as the root
        """

        if self.nx_graph.number_of_nodes() == 0:
            raise nx.exception.NodeNotFound("Graph is empty.")

        # n.b. entries of self.degree are tuples of the form (node_id, degree)
        # TODO: shouldn't we ignore boundaries when computing degree ?
        if central_spider:
            (_, max_degree) = max(self.nx_graph.get_degrees(), key=lambda entry: entry[1])
            candidates = [node_id for node_id in self.nx_graph.get_nodes() if self.nx_graph.is_spider(node_id) and self.nx_graph.get_degrees()[node_id] == max_degree]
        else:
            candidates = [node_id for node_id in self.nx_graph.get_nodes() if self.nx_graph.is_spider(node_id)]

        return min(candidates) if deterministic else random.choice(candidates)

    def construct(self, root: int = None):
        # Prepare the root node of the construction.
        if root is None:
            root = self.pick_root()
        root_kind = CubeKind.suitable_kinds(self.nx_graph.get_node_type(root))[0]
        #root_kind = random.choice(CubeKind.suitable_kinds(self.nx_graph.get_node_type(root)))
        self.nx_graph.realise_node(root, root_kind, BlockGraphSpace.ORIGIN)

        queue : deque[int] = deque([root])

        # Proceed with the main loop of the BFS
        while queue:
            source: int = queue.popleft()
            self.node_placement_order.append(source)

            for target in self.nx_graph.get_neighbours(source):
                if not self.nx_graph.is_node_realised(target):
                    # First-pass edge
                    # Goal: find a path to some position where a suitable cube can be placed within some maximal MD
                    queue.append(target)

                    successful = False
                    step = 3
                    while step <= 9 and not successful:
                        successful = self.place_nxt_block(source, target, init_step = step)
                        step += 3

                    if not successful:
                        # TODO: reporting(..) and animation(..)
                        raise Exception(f"Edge realisation failure [{source}-{target}]")

                    self.number_1st_pass_edges += 1

                elif not self.nx_graph.is_edge_realised(source, target):
                    # Second-pass edge
                    # Goal: find a path towards the position of a cube representing the target node
                    source_position = self.nx_graph.get_position(source)
                    source_kind = self.nx_graph.get_cube_kind(source)

                    target_position = self.nx_graph.get_position(target)
                    target_kind = self.nx_graph.get_cube_kind(target)

                    # TODO: deal with the critical beams (cfr. graph_manager.py Lines 301-313)

                    # Check if edge is Hadamard
                    # Call pathfinder for second-pass
                    # clean_paths, vis_data = run_pathfinder(
                    #       source_coords, source_kind,
                    #       target_type, target_coords, target_kind,
                    #       edge_type == HADAMARD ?,
                    #       init_step=3)
                    # update edge_realizations with clean_paths[0]
                    # TODO: a path can just be a list of (coordinates, kind)

                    # TODO: reporting

                    # if clean_paths:
                    #   number_2nd_pass_edges += 1
                    #   n.b. only consider clean_paths[0]
                    #   associate clean_paths[0] to edge in edge_realizations
                    #   update AugmentedNxGraph with new cubes and pipes from clean_paths[0]
                    #   update Beams ? Should be done as part
                    # else:
                    #   create_animation(..) and report failure
                    #   raise ValueError(f"ERROR. Path between fixed cubes {src_id} -> {tgt_id}")

                    raise NotImplemented("Second-pass edge processing.")

                self.prune_beams()

        # Prepare final BlockGraph and return it ?
        return True

    # TODO: the BgPathFinder should provide a function to find a path towards some position where a suitable cube can be placed
    def place_nxt_block(self, source: int, target: int, init_step: int = 3, log_stats_id = None):
        if not self.nx_graph.is_node_realised(source):
            raise Exception(f"{source} is not placed and has no kind; cannot connect with a path.")

        if self.nx_graph.is_node_realised(target):
            raise Exception(f"{target} is already placed and has a kind.")

        source_position = self.nx_graph.get_position(source)
        source_kind = self.nx_graph.get_cube_kind(source)

        target_type = self.nx_graph.get_node_type(target)
        edge_type = self.nx_graph.get_edge_type(source, target)
        is_hadamard = edge_type == EdgeType.HADAMARD

        # For compatibility with the current implementation of the pathfinder
        taken_coordinates = [ position.as_tuple() for position in self.nx_graph.occupied if position != source_position ]

        # clean_paths, pathfinder_vis_data = self.run_pathfinder(source, target, init_step)

        clean_paths, pathfinder_vis_data = run_pathfinder(
            (source_position.as_tuple(), source_kind.name.lower()),
            target_type.name,
            init_step,
            taken_coordinates,
            hdm=is_hadamard,
            min_succ_rate=60,
            src_tgt_ids=(source, target),
            log_stats_id=log_stats_id,
        )

        viable_paths = []
        target_degree = self.nx_graph.get_degrees()[target]

        print(f"Found {len(clean_paths)} clean_paths.")

        for clean_path in clean_paths:
            target_position, target_kind = clean_path[-1]
            print(f"> Clean path [{target_kind}@{target_position}]: {clean_path}")
            coordinates_in_path = get_taken_coords(clean_path)
            target_beams = self.compute_beams(CubeKind.from_string(target_kind), Coordinates.from_tuple(target_position), coordinates_in_path)
            target_unobstructed_exits = len(target_beams)

            if target_type == NodeType.O:
                target_unobstructed_exits, target_beams = (6, [])

            source_beams = self.node_cube_beams[source]

            if not (target_unobstructed_exits >= target_degree - 1 and any([clean_path[1][0] in beam for beam in source_beams])):
                continue

            critical_broken = False
            beams_broken_by_path = 0
            for node in self.nx_graph.get_nodes():
                if node not in self.node_cube_beams:
                    continue

                node_beams = self.node_cube_beams[node]
                broken = len(list(filter(lambda beam : any([ c in coordinates_in_path for c in beam[:7]]), node_beams)))
                beams_broken_by_path += broken
                adjust_for_source_node = 1 if node == source else 0
                node_degree = self.nx_graph.get_degrees()[node]
                edges_realised = self.nx_graph.get_edges_realised(node)
                remaining_edges = node_degree - edges_realised
                if (len(node_beams) - broken + adjust_for_source_node) < remaining_edges:
                    print(f"> Broken for {node} [L:{len(node_beams)},B:{broken},A:{adjust_for_source_node},R:{remaining_edges}]")
                    critical_broken = True

            critical_clash = False
            for node in self.nx_graph.get_nodes():
                if node == source or node == target or node not in self.node_cube_beams:
                    continue

                node_beams = self.node_cube_beams[node]
                clashes = 0 # This is inside the following loop in the original code ...
                for node_beam in node_beams:
                    clashes += len(list(filter(lambda target_beam : sum([(c in node_beam[:9]) for c in target_beam[:9]]) > len(target_beams) - target_degree, target_beams)))
                node_degree = self.nx_graph.get_degrees()[node]
                edges_realised = self.nx_graph.get_edges_realised(node)
                remaining_edges = node_degree - edges_realised
                if len(node_beams) - clashes < remaining_edges:
                    print(f"> Clash with {node}")
                    critical_clash = True

            if not critical_broken and not critical_clash:
                all_nodes_in_path = [p for p in clean_path]

                if target_type == NodeType.O:
                    target_kind = CubeKind.OOO.name.lower()
                    all_nodes_in_path[-1] = (all_nodes_in_path[-1][0], target_kind)

                path_data = {
                    "tgt_coords": target_position,
                    "tgt_kind": target_kind,
                    "tgt_beams": target_beams,
                    "coords_in_path": coordinates_in_path,
                    "all_nodes_in_path": all_nodes_in_path,
                    "beams_broken_by_path": beams_broken_by_path,
                    "len_of_path": len(clean_path),
                    "tgt_unobstr_exit_n": target_unobstructed_exits,
                }

                viable_paths.append(PathBetweenNodes(**path_data))

        winner_path = None
        if viable_paths:
            winner_path = max(viable_paths, key=lambda path: path.weighed_value(**kwargs))

        if winner_path is None:
            print("No winner")
            return False

        target_kind = CubeKind.from_string(winner_path.tgt_kind)
        target_position = Coordinates.from_tuple(winner_path.tgt_coords)

        path = []
        for coordinates, kind in winner_path.all_nodes_in_path[:-1]:
            if kind.count('o') != 1:
                path.append( (Coordinates.from_tuple(coordinates), CubeKind.from_string(kind)) )

        if not self.nx_graph.is_path_valid(source, target_kind, target_position, edge_type, path):
            return False

        self.nx_graph.realise_node(target, target_kind, target_position)

        self.nx_graph.realise_edge(source, target, path)

        # Compute the beams for the newly placed target cube.
        self.node_cube_beams[target] = self.compute_beams(target_kind, target_position)

        # Store the edge realisation path
        edge = (source, target) if source < target else (target, source)
        edge_type = self.nx_graph.get_edge_type(source, target)
        self.nx_graph.edge_realisations[edge] = {
            "src_tgt_ids": edge,
            "path_coordinates": winner_path.coords_in_path,
            "path_nodes": winner_path.all_nodes_in_path,
            "edge_type": edge_type,
        }

        # Incorporate the now occupied positions
        coordinates_in_path = get_taken_coords(winner_path.all_nodes_in_path)
        for taken in coordinates_in_path:
            self.nx_graph.occupied.add(Coordinates.from_tuple(taken))

        return True

    @staticmethod
    def kind_to_zx_type(kind: str) -> str:
        if kind == "ooo":
            zx_t = "BOUNDARY"
        elif "o" in kind:
            zx_t = "HADAMARD" if "h" in kind else "SIMPLE"
        else:
            zx_t = min(set(kind), key=lambda c: kind.count(c)).capitalize()
        return zx_t

    def run_pathfinder(self,
            source, target,
            init_step, min_succ_rate:int = 60,
            critical_beams: dict[int, tuple[int, NodeBeams]] = {},
            log_stats_id: str = None):
        clean_paths = []
        pathfinder_vis_data = []

        source_position = self.nx_graph.get_position(source)

        taken_cc = [ position.as_tuple() for position in self.nx_graph.occupied if position != source_position ]

        target_type = self.nx_graph.get_node_type(target)
        target_position = None
        if self.nx_graph.is_node_realised(target):
            target_position = self.nx_graph.get_position(target)
            max_step = 2 * init_step
            if target_position.as_tuple() in taken_cc:
                taken_cc.remove(target_position.as_tuple())
        else:
            max_step = 9

        edge_type = self.nx_graph.get_edge_type(source, target)

        for step in range(init_step, max_step + 1, 3):
            if target_position is not None:
                tent_coords = [target_position.as_tuple()]
            else:
                tent_coords = gen_tent_tgt_coords(
                    source_position.as_tuple(), step, [ position.as_tuple() for position in self.nx_graph.occupied ]
                )

            if tent_coords:
                valid_paths, pathfinder_vis_data = pathfinder(
                    (source_position.as_tuple(), self.nx_graph.get_cube_kind(source).name),
                    tent_coords,
                    target_type.name,
                    taken=taken_cc,
                    tgt_block_info=(tent_coords[0], target_type.name),
                    hdm = (edge_type == EdgeType.HADAMARD),
                    min_succ_rate=min_succ_rate,
                    critical_beams=critical_beams,
                    src_tgt_ids=(source, target),
                    log_stats_id=log_stats_id,
                )

                # A clean_path is one that doesn't pass through a taken coordinate
                for path in valid_paths.values():
                    path_checks = True
                    for node in path:
                        if node[0] in taken_cc:
                            path_checks = False
                    if path_checks:
                        clean_paths.append(path)

                if clean_paths:
                    break

            else:
                ValueError(f"tent_coords: {tent_coords}")

        return clean_paths, pathfinder_vis_data

    def compute_beams(self, cube_kind: CubeKind, cube_position: Coordinates,
                      extra_coordinates : list[tuple[int,int,int]] = None, beam_length: int = 99) -> NodeBeams:
        if extra_coordinates is None:
            extra_coordinates = []

        beams: NodeBeams = []

        cube_reach = cube_kind.get_reach()

        for step in BlockGraphSpace.STEPS:
            if not cube_reach.contains(step):
                continue

            beam = [] # from cube_position up to beams_len steps away

            current_position = cube_position + step.value
            for i in range(0, beam_length):
                if current_position in self.nx_graph.occupied or current_position.as_tuple() in extra_coordinates:
                    break

                beam_crossed = False
                for node in self.nx_graph.get_nodes():
                    if node not in self.node_cube_beams:
                        continue

                    for other in self.node_cube_beams[node]:
                        if not any([position in extra_coordinates for position in other[:9]]):
                            if current_position.as_tuple() in other:
                                beam_crossed = True
                                break
                    if beam_crossed:
                        break

                if beam_crossed:
                    break

                beam.append(current_position.as_tuple())
                current_position += step.value

            # Add the beam to the list if it was completely constructed
            if len(beam) == beam_length:
                beams.append(beam)

        return beams

    def prune_beams(self):
        for node in self.nx_graph.get_nodes():
            if self.nx_graph.get_edges_realised(node) >= self.nx_graph.get_degrees()[node]:
                self.node_cube_beams[node] = []
            elif node in self.node_cube_beams:
                new_beams = []
                for beam in self.node_cube_beams[node]:
                    if all([Coordinates.from_tuple(position) not in self.nx_graph.occupied for position in beam]):
                        new_beams.append(beam)
                self.node_cube_beams[node] = new_beams

    def prepare_report(self):
        report = ""

        report += f"RESULT SHEET. CIRCUIT NAME: {self.name}\n"
        report += "\n__________________________\n"
        report += "ORIGINAL ZX GRAPH\n"
        for node in self.nx_graph.get_nodes():
            report += f"Node ID: {node}. Type: {self.nx_graph.get_node_type(node).name}\n"
        report += "\n"
        for edge in self.nx_graph.get_edges():
            source = min(edge)
            target = max(edge)
            edge_type = self.nx_graph.get_edge_type(source, target)
            type_name = "SIMPLE" if edge_type == EdgeType.IDENTITY else "HADAMARD"
            report += f"Edge ID: ({source}, {target}). Type: {type_name}\n"
        report += "\n__________________________\n"
        report += "3D \"EDGE PATHS\" (Blocks needed to connect two original nodes)\n"
        for edge, data in self.nx_graph.edge_realisations.items():
            report += f"Edge {edge}: {data['path_nodes']}\n"
        report += "\n__________________________\n"
        report += "LATTICE SURGERY (Graph)\n"
        for node in self.node_placement_order:
            report += f"Node ID: {node}. Info: ({self.nx_graph.get_position(node)}, '{self.nx_graph.get_cube_kind(node).name.lower()}')\n"

        return report

    def print_report(self):
        print(self.prepare_report())

    def write_report(self, filename = "ang.txt"):
        output = open(filename, "w")
        output.write(self.prepare_report())
        output.close()