from logging import getLogger

from vedo import Mesh

from topologiq.dzw.utils.components_zx import EdgeType
from topologiq.dzw.utils.path import Path

console = getLogger(__name__)

from topologiq.dzw.utils.components_bg import CubeId
from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.vedo.shapes_bg import BgCube, BgPipe


class BgSceneManager:
    def __init__(self, nx_graph: AugmentedNxGraph):
        self.__nx_graph = nx_graph

        self.__cubes = dict()
        self.__pipes = dict()

        # Prepare all the components for the BG viewport (i.e. cubes and pipes)
        self.elements = []
        self.__frames: list[list[Mesh]] = []
        self.__subframes: list[list[list[Mesh]]] = []

        for cube in nx_graph.get_cubes():
            node = self.__nx_graph.get_node(cube)
            kind = self.__nx_graph.get_cube_kind(cube)
            position = self.__nx_graph.get_cube_position(cube)
            extra_cube = BgCube(kind, position, node, cube)
            self.__cubes[cube] = extra_cube
            self.elements.append(extra_cube)

        for source, target in nx_graph.get_pipes():
            pipe = tuple(sorted((source, target)))
            source_kind = self.__nx_graph.get_cube_kind(source)
            target_kind = self.__nx_graph.get_cube_kind(target)
            source_position = self.__nx_graph.get_cube_position(source)
            target_position = self.__nx_graph.get_cube_position(target)
            pipe_type = self.__nx_graph.get_pipe_type(source, target)
            bg_pipe = BgPipe(source_kind, source_position, target_kind, target_position, pipe_type, source, target)
            self.__pipes[pipe] = bg_pipe
            self.elements.append(bg_pipe)

        node_realisation_order = self.__nx_graph.get_node_realisation_order()
        edge_realisation_order = self.__nx_graph.get_edge_realisation_order()

        if len(node_realisation_order) == 0 and len(edge_realisation_order) == 0:
            self.__frames.append(self.elements)
        else:
            placed_cubes = set()
            if len(node_realisation_order) > 0:
                root = node_realisation_order[0]
                extra_cube = self.__cubes[ self.__nx_graph.get_cube(root) ]
                placed_cubes.add(root)
                self.__frames.append([extra_cube])

            for source, target in edge_realisation_order:
                # Add all the elements to the scene and the range of elements in the current frame
                current_frame = self.__make_frame(source, target, placed_cubes)
                self.__frames.append( current_frame )
                subframes = [ current_frame ]
                subframes.extend(self.__make_subframes(source, target))
                console.debug(f"Subframes: {len(subframes)}")
                # current_subframes.extend( subframes )
                self.__subframes.append( subframes )

                # alternatives = self.__nx_graph.get_edge_alternatives(source, target)
                # if alternatives:
                #     subframes = [ current_frame ]
                #     for alternative in alternatives:
                #         current_subframe = self.__make_subframe(alternative)
                #         subframes.append(current_subframe)
                #     self.__subframes.append(subframes)

        # Keeps track of the number of frames that are accumulated into the currently displayed scene
        self.__frame_index = len(self.__frames) - 1
        self.__subframe_index = 0

    def __make_frame(self, source: CubeId, target: CubeId, placed_cubes: set[CubeId]):
        frame = []
        # Add extra cubes to the current_frame
        previous_cube = self.__nx_graph.get_cube(source)
        for current_cube in self.__nx_graph.get_edge_realisation(source, target).get_cube_ids()[1:]:
            pipe = tuple(sorted((previous_cube, current_cube)))
            frame.append(self.__pipes[pipe])

            if current_cube not in placed_cubes:
                frame.append(self.__cubes[current_cube])
                placed_cubes.add(current_cube)

            previous_cube = current_cube
        return frame

    def __make_subframes(self, source: CubeId, target: CubeId):
        subframes = []
        alternatives = self.__nx_graph.get_edge_alternatives(source, target)
        console.debug(f"Alternatives: {len(alternatives)}")
        if alternatives:
            for alternative in alternatives:
                previous_kind, previous_position = alternative.get_cubes()[0]
                current_subframe = []
                for current_kind, current_position in alternative.get_cubes()[1:]:
                    extra_cube = BgCube(current_kind, current_position)
                    extra_pipe = BgPipe(previous_kind, previous_position, current_kind, current_position, EdgeType.IDENTITY)
                    current_subframe.append(extra_cube)
                    current_subframe.append(extra_pipe)

                    previous_kind = current_kind
                    previous_position = current_position
                subframes.append(current_subframe)
        return subframes

    def __move_frame_forward(self, count: int = 1):
        frame_count = min(count, len(self.__frames) - self.__frame_index - 1)
        for frame in range(frame_count):
            for mesh in self.__frames[self.__frame_index + frame + 1]:
                mesh.show()
        self.__frame_index += frame_count
        self.__subframe_index = 0

    def __move_frame_backward(self, count: int = 1):
        frame_count = min(count, self.__frame_index)
        for frame in range(frame_count):
            for mesh in self.__frames[self.__frame_index - frame]:
                mesh.hide()
        self.__frame_index -= frame_count
        self.__subframe_index = 0

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
            self.__move_frame_backward()
        elif event.keypress == "Home":
            self.__move_frame_backward(count = self.__frame_index)
        elif event.keypress == "Right":
            self.__move_frame_forward()
        elif event.keypress == "End":
            self.__move_frame_forward(count =len(self.__frames) - self.__frame_index - 1)

        if len(self.__subframes) > 0:
            subframe_notice = f"[SF:{self.__subframe_index + 1}/{len(self.__subframes[self.__subframe_index])}]"
        else:
            subframe_notice = "[SF:0/0]"
        console.debug(f"> Frame {self.__frame_index + 1}/{len(self.__frames)} {subframe_notice}")
        console.debug(f">> Range={self.__frames[self.__frame_index]}")

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