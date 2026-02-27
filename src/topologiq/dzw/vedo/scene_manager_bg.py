from vedo import Mesh
from vedo.plotter.runtime import Plotter

from topologiq.dzw.utils.components_zx import EdgeType
from topologiq.dzw.utils.path import Path
from topologiq.dzw.vedo.frame_manager_cumulative import CumulativeFrameManager

from topologiq.dzw.utils.components_bg import CubeId
from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.vedo.shapes_bg import BgCube, BgPipe

from logging import getLogger
console = getLogger(__name__)

class BgSceneManager:
    def __init__(self, nx_graph: AugmentedNxGraph, plotter: Plotter):
        self.__nx_graph = nx_graph
        self.__plotter = plotter

        self.__cubes = dict()
        self.__pipes = dict()

        # Prepare all the components for the BG viewport (i.e. cubes and pipes)
        self.__frame_manager = CumulativeFrameManager(self.__plotter)

        for cube in nx_graph.get_cubes():
            node = self.__nx_graph.get_node(cube)
            kind = self.__nx_graph.get_cube_kind(cube)
            position = self.__nx_graph.get_cube_position(cube)
            extra_cube = BgCube(kind, position, node, cube)
            self.__cubes[cube] = extra_cube

        for source, target in nx_graph.get_pipes():
            pipe = tuple(sorted((source, target)))
            source_kind = self.__nx_graph.get_cube_kind(source)
            target_kind = self.__nx_graph.get_cube_kind(target)
            source_position = self.__nx_graph.get_cube_position(source)
            target_position = self.__nx_graph.get_cube_position(target)
            pipe_type = self.__nx_graph.get_pipe_type(source, target)
            bg_pipe = BgPipe(source_kind, source_position, target_kind, target_position, pipe_type, source, target)
            self.__pipes[pipe] = bg_pipe

        node_realisation_order = [] #self.__nx_graph.get_node_realisation_order()
        edge_realisation_order = [] #self.__nx_graph.get_edge_realisation_order()

        if len(node_realisation_order) == 0 and len(edge_realisation_order) == 0:
            current_frame = self.__frame_manager.create_next_frame()
            self.__frame_manager.add_all_to_frame(current_frame, self.__cubes.values())
            self.__frame_manager.add_all_to_frame(current_frame, self.__pipes.values())
            console.debug(f"> Added {len(self.__cubes.values())} cubes.")
            console.debug(f"> Added {len(self.__pipes.values())} pipes.")
        else:
            placed_cubes = set()
            if len(node_realisation_order) > 0:
                root = node_realisation_order[0]
                root_cube = self.__cubes[ self.__nx_graph.get_cube(root) ]
                placed_cubes.add(root_cube)
                current_frame = self.__frame_manager.create_next_frame()
                self.__frame_manager.add_to_frame(current_frame, root_cube)

            for source, target in edge_realisation_order:
                # Add extra cubes to a new frame
                current_frame = self.__frame_manager.create_next_frame()
                previous_cube = self.__nx_graph.get_cube(source)
                for current_cube in self.__nx_graph.get_edge_realisation(source, target).get_cube_ids()[1:]:
                    pipe = tuple(sorted((previous_cube, current_cube)))
                    self.__frame_manager.add_to_frame(current_frame, self.__pipes[pipe])

                    if current_cube not in placed_cubes:
                        self.__frame_manager.add_to_frame(current_frame, self.__cubes[current_cube])
                        placed_cubes.add(current_cube)

                    previous_cube = current_cube

        # Prepare the first frame
        starting_frame = self.__frame_manager.get_frame_count() - 1
        self.__frame_manager.set_current_frame( starting_frame )
        actors = f"[actors={len(self.__plotter.actors)}]"
        console.info(f"Starting at frame {starting_frame+1}/{self.__frame_manager.get_frame_count()} {actors}")
        console.info(f"> {len(self.__cubes)} cubes, {len(self.__pipes)} pipes.")
        console.debug(f"> Actors : {self.__plotter.actors}")
        self.__frame_manager.log_frame_report()

    # def __make_subframes(self, source: CubeId, target: CubeId):
    #     subframes = []
    #     alternatives = self.__nx_graph.get_edge_alternatives(source, target)
    #     console.debug(f"Alternatives: {len(alternatives)}")
    #     if alternatives:
    #         for alternative in alternatives:
    #             previous_kind, previous_position = alternative.get_cubes()[0]
    #             current_subframe = []
    #             for current_kind, current_position in alternative.get_cubes()[1:]:
    #                 extra_cube = BgCube(current_kind, current_position)
    #                 extra_pipe = BgPipe(previous_kind, previous_position, current_kind, current_position, EdgeType.IDENTITY)
    #                 current_subframe.append(extra_cube)
    #                 current_subframe.append(extra_pipe)
    #
    #                 extra_cube.hide()
    #                 extra_pipe.hide()
    #                 self.elements.append(extra_cube)
    #                 self.elements.append(extra_pipe)
    #
    #                 previous_kind = current_kind
    #                 previous_position = current_position
    #             subframes.append(current_subframe)
    #     return subframes

    def show_cube_highlight(self, cube: CubeId):
        self.__cubes[ cube ].show_highlight()

    def hide_cube_highlight(self, cube: CubeId):
        self.__cubes[ cube ].hide_highlight()

    def show_pipe_highlight(self, source: CubeId, target: CubeId):
        pipe = tuple(sorted((source, target)))
        self.__pipes[ pipe ].show_highlight()

    def hide_pipe_highlight(self, source: CubeId, target: CubeId):
        pipe = tuple(sorted((source, target)))
        self.__pipes[ pipe ].hide_highlight()

    def on_key_press(self, event):
        if   event.keypress == "Left":
            self.__frame_manager.move_frame(count = -1)
        elif event.keypress == "Right":
            self.__frame_manager.move_frame(count = +1)
        elif event.keypress == "Home":
            self.__frame_manager.set_current_frame(0)
        elif event.keypress == "End":
            self.__frame_manager.set_current_frame(self.__frame_manager.get_frame_count() - 1)
        # elif event.keypress == "Up":
        #     self.__frame_manager.move_subframe_forward()
        # elif event.keypress == "Down":
        #     self.__frame_manager.move_subframe_backward()
        actors = f"[{len(self.__plotter.actors)}]"
        console.debug(f"> Managed elements : {actors}")

    # def on_left_click(self, event):
    #     if isinstance(event.object, BgCube):
    #         zx_node = self.__nx_graph.get_node(event.object.bg_cube)
    #         extra = f"[N{zx_node}]" if zx_node is not None else ""
    #         console.debug(f"Clicked on Cube #{event.object.bg_cube} {extra}")
    #         event.object.toggle_highlight()
    #
    #     if isinstance(event.object, BgPipe):
    #         console.debug(f"Clicked on Pipe  {event.object.bg_source}-{event.object.bg_target}")
    #         event.object.toggle_highlight()