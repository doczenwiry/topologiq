from logging import getLogger

from vedo import Mesh

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

        placed_cubes = set()

        for cube in nx_graph.get_cubes():
            bg_cube = BgCube(cube, anx = self.__nx_graph)
            self.__cubes[cube] = bg_cube
            self.elements.append(bg_cube)

        for source, target in nx_graph.get_pipes():
            pipe = tuple(sorted((source, target)))
            bg_pipe = BgPipe(source, target, anx = self.__nx_graph)
            self.__pipes[ pipe ] = bg_pipe
            self.elements.append(bg_pipe)

        node_realisation_order = self.__nx_graph.get_node_realisation_order()
        edge_realisation_order = self.__nx_graph.get_edge_realisation_order()

        if len(node_realisation_order) == 0 and len(edge_realisation_order) == 0:
            self.__frames.append(self.elements)
        else:
            if len(node_realisation_order) > 0:
                root = node_realisation_order[0]
                bg_cube = self.__cubes[ self.__nx_graph.get_cube(root) ]
                placed_cubes.add(root)
                self.__frames.append([bg_cube])

            for source, target in edge_realisation_order:
                current_frame: list[Mesh] = []
                # Add extra cubes to the current_frame
                previous_extra = self.__nx_graph.get_cube(source)
                current_frame.append(self.__cubes[previous_extra])
                for current_extra in self.__nx_graph.get_edge_realisation(source, target).get_cube_ids()[1:]:
                    pipe = tuple(sorted((previous_extra, current_extra)))
                    current_frame.append(self.__pipes[pipe])

                    if current_extra not in placed_cubes:
                        current_frame.append(self.__cubes[current_extra])
                        placed_cubes.add(current_extra)

                    previous_extra = current_extra

                # Add all the elements to the scene and the range of elements in the current frame
                self.__frames.append(current_frame)

        # Keeps track of the number of frames that are accumulated into the currently displayed scene
        self.__frame_index = len(self.__frames) - 1

    def __move_frame_forward(self, count: int = 1):
        frame_count = min(count, len(self.__frames) - self.__frame_index - 1)
        for frame in range(frame_count):
            for mesh in self.__frames[self.__frame_index + frame + 1]:
                mesh.show()
        self.__frame_index += frame_count

    def __move_frame_backward(self, count: int = 1):
        frame_count = min(count, self.__frame_index)
        for frame in range(frame_count):
            for mesh in self.__frames[self.__frame_index - frame]:
                mesh.hide()
        self.__frame_index -= frame_count

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

        console.debug(f"> Frame {self.__frame_index + 1}/{len(self.__frames)}")
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