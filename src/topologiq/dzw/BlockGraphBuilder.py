import random
from collections import deque

import pyzx as zx

from topologiq.dzw.AugmentedNxGraph import AugmentedNxGraph
from topologiq.dzw.BlockGraphSpace import BlockGraphSpace
from topologiq.dzw.GraphComponents import CubeKind

class BlockGraphBuilder:
    def __init__(self):
        self.name = "circuit"
        self.hide_ports = False # This really belongs in the visualization layer
        self.min_success_rate = 50

    def construct(self, pyzx_graph: zx.graph.base.BaseGraph, root: int = None):
        nx_graph = AugmentedNxGraph(pyzx_graph)

        # Prepare the root node of the construction.
        if root is None:
            root = nx_graph.pick_root()
        root_kind = random.choice(CubeKind.suitable_kinds(nx_graph.nodes[root]['type']))
        nx_graph.place_vertex(root, root_kind, BlockGraphSpace.ORIGIN)

        queue : deque[int] = deque([root])

        # Proceed with the main loop of the BFS
        while queue:
            source: int = queue.popleft()

            for target in nx_graph.neighbors(source):
                if nx_graph.is_vertex_placed(target):
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

                elif not nx_graph.is_edge_realized(source, target):
                    # Second-pass edge
                    # Path-finding to the position where the existing cube is located ?
                    source_position = nx_graph.nodes[source]['position']
                    source_kind = nx_graph.nodes[source]['kind']

                    target_position = nx_graph.nodes[target]['position']
                    target_kind = nx_graph.nodes[target]['kind']

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
        return nx_graph