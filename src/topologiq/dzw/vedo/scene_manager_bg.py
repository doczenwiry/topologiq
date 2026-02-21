from logging import getLogger
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
        self.__frames = []

        realised_nodes = set()

        current_frame_final = 0

        node_realisation_order = self.__nx_graph.get_node_realisation_order()
        if len(node_realisation_order) > 0:
            root = node_realisation_order[0]
            root_cube = self.__nx_graph.get_cube(root)
            bg_cube = BgCube(cube = root_cube, anx = self.__nx_graph)
            self.__cubes[ root_cube ] = bg_cube
            realised_nodes.add(root)

            current_frame_final += 1

            self.elements.append( bg_cube )
            self.__frames.append(range(0, 1))

        for source, target in nx_graph.get_edge_realisation_order():
            current_frame = []
            current_frame_start = len(self.elements)
            # Add extra cubes to the current_frame
            previous_extra = self.__nx_graph.get_cube(source)
            for current_extra in self.__nx_graph.get_edge_realisation(source, target):
                extra_bg_cube = BgCube(cube = current_extra, anx = self.__nx_graph)
                extra_bg_pipe = BgPipe(source = previous_extra, target = current_extra, anx=self.__nx_graph)
                # Add extra cube & pipe to current frame
                current_frame.append( extra_bg_cube )
                current_frame.append( extra_bg_pipe )
                # Save extra cube & pipe to internal dictionary
                self.__cubes[ current_extra ] = extra_bg_cube
                pipe = tuple(sorted( (previous_extra, current_extra) ))
                self.__pipes[ pipe ] = extra_bg_pipe

                previous_extra = current_extra

            target_cube = self.__nx_graph.get_cube(target)

            # Add target cube if not already placed in earlier frame
            if target not in realised_nodes:
                target_bg_cube = BgCube(cube = target_cube, anx = self.__nx_graph)
                current_frame.append( target_bg_cube )
                self.__cubes[ target_cube ] = target_bg_cube
                realised_nodes.add(target)

            # Add final pipe
            target_bg_pipe = BgPipe(source = previous_extra, target = target_cube, anx = self.__nx_graph)
            current_frame.append( target_bg_pipe )
            pipe = tuple(sorted((previous_extra, target_cube)))
            self.__pipes[ pipe ] = target_bg_pipe

            current_frame_final = current_frame_start + len(current_frame)

            # Add all the elements to the scene and the range of elements in the current frame
            self.elements.extend(current_frame)
            self.__frames.append(range(current_frame_start, current_frame_final))

            # Keeps track of the number of frames that are accumulated into the currently displayed scene
            self.__frame_index = len(self.__frames) - 1

    def __move_frame_forward(self, count: int = 1):
        frame_count = min(count, len(self.__frames) - self.__frame_index - 1)
        for frame in range(frame_count):
            for index in self.__frames[self.__frame_index + frame + 1]:
                self.elements[index].show()
        self.__frame_index += frame_count

    def __move_frame_backward(self, count: int = 1):
        frame_count = min(count, self.__frame_index)
        for frame in range(frame_count):
            for index in self.__frames[self.__frame_index - frame]:
                self.elements[index].hide()
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