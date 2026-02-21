from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph

from vedo import settings, Plotter

from topologiq.dzw.vedo.shapes_zx import ZxNode, ZxEdge
from topologiq.dzw.vedo.shapes_bg import BgCube, BgPipe

import logging
console = logging.getLogger(__name__)
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)

ZX_VIEWPORT = 1
BG_VIEWPORT = 2

SHAPES = [
    # Full window
    dict(bottomleft=(0.00, 0.00), topright=(1.00, 1.00), bg='k7'),
    # ZX Viewport
    dict(bottomleft=(0.00, 0.75), topright=(1.00, 1.00), bg='k8'),
    # BG Viewport
    dict(bottomleft=(0.00, 0.00), topright=(1.00, 0.75), bg='w'),
]

settings.enable_default_mouse_callbacks = False
settings.enable_default_keyboard_callbacks = False

class AugmentedNxGraphViewer(Plotter):
    def __init__(self, anx: AugmentedNxGraph, label: str):
        super().__init__(shape = SHAPES, sharecam = False, title = f"ang-viewer [{label}]")

        self.__reset_camera()

        # Set all the callbacks
        self.add_callback("key press", self.__on_key_pressed)
        self.at(ZX_VIEWPORT).add_callback("mouse left click", self.__on_zx_left_clicked)
        self.at(BG_VIEWPORT).add_callback("mouse left click", self.__on_bg_left_clicked)

        # Store the original AugmentedNxGraph
        self.__nx_graph = anx

        # Prepare all the components for the ZX viewport (i.e. nodes and edges)
        self.__zx_scene = []
        for node in self.__nx_graph.get_nodes():
            self.__zx_scene.append(
                ZxNode(node, self.__nx_graph)
            )

        for source, target in self.__nx_graph.get_edges():
            self.__zx_scene.append(
                ZxEdge(source, target, self.__nx_graph).z(-0.1)
            )

        # Prepare all the components for the BG viewport (i.e. cubes and pipes)
        self.__bg_scene = []
        self.__bg_frames = []

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

            self.__bg_scene.extend(current_frame)
            self.__bg_frames.append(range(0, 1))

        for source, target in anx.get_edge_realisation_order():
            current_frame = []
            current_frame_start = len(self.__bg_scene)
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
            self.__bg_scene.extend(current_frame)
            self.__bg_frames.append(range(current_frame_start, current_frame_final))

            # Keeps track of the number of frames that are accumulated into the currently displayed scene
            self.__bg_frame_count = len(self.__bg_frames) - 1

    def __reset_camera(self):
        # Initialise the camera for the BG Graph
        bg_camera = self.at(BG_VIEWPORT).camera
        bg_camera.SetPosition(5, 3, 3)
        bg_camera.SetFocalPoint(0, 0, 0)
        bg_camera.SetViewUp(0, 0, 1)

    def __add_frames_into_bg_scene(self, frame_count: int):
        count = min(frame_count, len(self.__bg_frames) - self.__bg_frame_count - 1)
        for _ in range(count):
            self.__bg_frame_count += 1
            for index in self.__bg_frames[self.__bg_frame_count]:
                self.__bg_scene[index].show()

    def __cut_frames_from_bg_scene(self, frame_count: int):
        count = min(frame_count, self.__bg_frame_count)
        for _ in range(count):
            for index in self.__bg_frames[self.__bg_frame_count]:
                self.__bg_scene[index].hide()
            self.__bg_frame_count -= 1

    def __on_key_pressed(self, event):
        console.debug(f"> Keypress : {event.keypress}")

        if   event.keypress == "Left":
            self.__cut_frames_from_bg_scene(frame_count = 1)
        elif event.keypress == "Home":
            self.__cut_frames_from_bg_scene(frame_count = self.__bg_frame_count)
        elif event.keypress == "Right":
            self.__add_frames_into_bg_scene(frame_count = 1)
        elif event.keypress == "End":
            self.__add_frames_into_bg_scene(frame_count = len(self.__bg_frames) - self.__bg_frame_count - 1)
        elif event.keypress == "Escape":
            self.__reset_camera()

        console.debug(f"> Frame {self.__bg_frame_count + 1}/{len(self.__bg_frames)}")
        console.debug(f">> Range={self.__bg_frames[self.__bg_frame_count]}")

        # Refresh the BG viewport
        self.at(BG_VIEWPORT).show(self.__bg_scene)

    def __on_zx_left_clicked(self, event):
        if isinstance(event.object, ZxNode):
            bg_cube = self.__nx_graph.get_cube(event.object.zx_node)
            extra = f"[C{bg_cube}]" if bg_cube is not None else ""
            console.debug(f"Clicked on Node #{event.object.zx_node} {extra}")
            event.object.hide_label()

        if isinstance(event.object, ZxEdge):
            console.debug(f"Clicked on Edge  {event.object.zx_source}-{event.object.zx_target}")

    def __on_bg_left_clicked(self, event):
        if isinstance(event.object, BgCube):
            zx_node = self.__nx_graph.get_node(event.object.bg_cube)
            extra = f"[N{zx_node}]" if zx_node is not None else ""
            console.debug(f"Clicked on Cube #{event.object.bg_cube} {extra}")

        if isinstance(event.object, BgPipe):
            console.debug(f"Clicked on Pipe  {event.object.bg_source}-{event.object.bg_target}")

    def display(self):
        self.at(ZX_VIEWPORT).show(self.__zx_scene)
        self.at(BG_VIEWPORT).show(self.__bg_scene)
        self.interactive().close()