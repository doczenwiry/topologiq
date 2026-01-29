import random
from collections import deque

import pyzx as zx
import networkx as nx

from topologiq.dzw.AugmentedNxGraph import AugmentedNxGraph
from topologiq.dzw.BlockGraphSpace import BlockGraphSpace
from topologiq.dzw.BlockGraphComponents import CubeKind
from topologiq.scripts.graph_manager import run_pathfinder

class BlockGraphBuilder:
    def __init__(self, pyzx_graph: zx.graph.base.BaseGraph):
        self.name = "circuit"
        self.hide_ports = False # This really belongs in the visualisation layer
        self.min_success_rate = 50
        self.nx_graph = AugmentedNxGraph(pyzx_graph)

    # find_first_id(..)
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
        if central_spider:
            (_, max_degree) = max(self.nx_graph.degree, key=lambda entry: entry[1])
            candidates = [node_id for node_id in self.nx_graph.nodes() if self.nx_graph.is_spider(node_id) and self.nx_graph.degree[node_id] == max_degree]
        else:
            candidates = [node_id for node_id in self.nx_graph.nodes() if self.nx_graph.is_spider(node_id)]

        return min(candidates) if deterministic else random.choice(candidates)

    def construct(self, root: int = None):
        # Prepare the root node of the construction.
        if root is None:
            root = self.pick_root()
        root_kind = random.choice(CubeKind.suitable_kinds(self.nx_graph.nodes[root]['type']))
        self.nx_graph.realise_node(root, root_kind, BlockGraphSpace.ORIGIN)

        queue : deque[int] = deque([root])

        # Proceed with the main loop of the BFS
        while queue:
            source: int = queue.popleft()

            for target in self.nx_graph.neighbors(source):
                if self.nx_graph.is_node_realised(target):
                    # First-pass edge
                    # Path-finding to a position where a suitable cube can be placed ?
                    queue.append(target)

                    # Try placing target in 3D space and connect it to the source.
                    # cfr. graph_manager.py; place_nxt_block(..) with step in [3, 6, 9]

                    # if edge_success:
                    #   number_1st_pass_edges += 1
                    # else:
                    #   create_animation(..) for partial BlockGraph

                    # if step >= 9:
                    #   reporting(..)
                    #   raise ValueError(f"ERROR with edge {source} -> {target}")

                    raise NotImplemented("First-pass edge processing.")

                elif not self.nx_graph.is_edge_realised(source, target):
                    # Second-pass edge
                    # Path-finding to the position where the existing cube is located ?
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

        # Prepare final BlockGraph and return it ?
        return True

    def place_nxt_block(self, source: int, target: int, init_step: int = 3):
        if not self.nx_graph.is_node_realised(source):
            raise Exception(f"{source} is not placed and has no kind; cannot connect with a path.")

        if self.nx_graph.is_node_realised(target):
            raise Exception(f"{target} is already placed and has a kind.")

        source_position = self.nx_graph.get_position(source)
        source_kind = self.nx_graph.get_cube_kind(source)
        target_type = self.nx_graph.get_node_type(target)
        edge_type = self.nx_graph.get_edge_type(source, target)

        taken_coords_c = list(self.nx_graph.occupied)
        if source_position in taken_coords_c:
            taken_coords_c.remove(source_position)

        clean_paths, pathfinder_vis_data = run_pathfinder(
            (source_position.as_tuple(), source_kind.name),

        )

        raise NotImplemented("Placement of next block not implemented.")