from logging import getLogger
console = getLogger(__name__)

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.vedo.shapes_bg import BgCube, BgPipe


class BgSceneManager:
    def __init__(self, nx_graph: AugmentedNxGraph):
        self.__nx_graph = nx_graph

        # Prepare all the components for the BG viewport (i.e. cubes and pipes)
        self.elements = []
        self.__frames = []

        realised_nodes = set()

        current_frame_final = 0

        node_realisation_order = self.__nx_graph.get_node_realisation_order()
        if len(node_realisation_order) > 0:
            root = node_realisation_order[0]
            root_cube = self.__nx_graph.get_cube(root)
            current_frame = [
                BgCube(cube = root_cube, anx = self.__nx_graph)
            ]
            realised_nodes.add(root)

            current_frame_final += 1

            self.elements.extend(current_frame)
            self.__frames.append(range(0, 1))

        for source, target in nx_graph.get_edge_realisation_order():
            current_frame = []
            current_frame_start = len(self.elements)
            # Add extra cubes to the current_frame
            previous_extra = self.__nx_graph.get_cube(source)
            for current_extra in self.__nx_graph.get_edge_realisation(source, target):
                current_frame.append(
                    BgCube(cube = current_extra, anx = self.__nx_graph)
                )

                # Add extra pipe
                current_frame.append(
                    BgPipe(source = previous_extra, target = current_extra, anx = self.__nx_graph)
                )

                previous_extra = current_extra

            # Add final pipe
            target_cube = self.__nx_graph.get_cube(target)
            current_frame.append(
                BgPipe(source = previous_extra, target = target_cube, anx = self.__nx_graph)
            )

            # Add target if not already placed in earlier frame
            if target not in realised_nodes:
                current_frame.append(
                    BgCube(cube = target_cube, anx = self.__nx_graph)
                )
                realised_nodes.add(target)

            current_frame_final = current_frame_start + len(current_frame)

            # Add all the elements to the scene and the range of elements in the current frame
            self.elements.extend(current_frame)
            self.__frames.append(range(current_frame_start, current_frame_final))

            # Keeps track of the number of frames that are accumulated into the currently displayed scene
            self.__frame_count = len(self.__frames) - 1

    def add_frames(self, count: int = 1):
        frame_count = min(count, len(self.__frames) - self.__frame_count - 1)
        for _ in range(frame_count):
            self.__frame_count += 1
            for index in self.__frames[self.__frame_count]:
                self.elements[index].show()

    def cut_frames(self, count: int = 1):
        frame_count = min(count, self.__frame_count)
        for _ in range(frame_count):
            for index in self.__frames[self.__frame_count]:
                self.elements[index].hide()
            self.__frame_count -= 1

    def on_key_press(self, event):
        if   event.keypress == "Left":
            self.cut_frames()
        elif event.keypress == "Home":
            self.cut_frames(count = self.__frame_count)
        elif event.keypress == "Right":
            self.add_frames()
        elif event.keypress == "End":
            self.add_frames(count =len(self.__frames) - self.__frame_count - 1)

        console.debug(f"> Frame {self.__frame_count + 1}/{len(self.__frames)}")
        console.debug(f">> Range={self.__frames[self.__frame_count]}")

    def on_left_click(self, event):
        if isinstance(event.object, BgCube):
            zx_node = self.__nx_graph.get_node(event.object.bg_cube)
            extra = f"[N{zx_node}]" if zx_node is not None else ""
            console.debug(f"Clicked on Cube #{event.object.bg_cube} {extra}")

        if isinstance(event.object, BgPipe):
            console.debug(f"Clicked on Pipe  {event.object.bg_source}-{event.object.bg_target}")