from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph

from vedo import settings, Plotter

from topologiq.dzw.vedo.scene_manager_bg import BgSceneManager
from topologiq.dzw.vedo.scene_manager_zx import ZxSceneManager
from topologiq.dzw.vedo.shapes_zx import ZxNode, ZxEdge
from topologiq.dzw.vedo.shapes_bg import BgCube, BgPipe

import logging
console = logging.getLogger(__name__)
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)

ZX_VIEWPORT = 0
BG_VIEWPORT = 1

VIEWPORTS = [
    dict(bottomleft=(0.00, 0.75), topright=(1.00, 1.00), bg='k8'), # ZX Viewport
    dict(bottomleft=(0.00, 0.00), topright=(1.00, 0.75), bg='k6'), # BG Viewport
]

settings.enable_default_mouse_callbacks = False
settings.enable_default_keyboard_callbacks = False

class AugmentedNxGraphViewer(Plotter):
    def __init__(self, anx: AugmentedNxGraph, label: str):
        super().__init__(shape = VIEWPORTS, sharecam = False, title = f"ang-viewer [{label}]")

        self.__reset_camera()

        # Store the original AugmentedNxGraph
        self.__nx_graph = anx

        # Set the global callbacks
        self.add_callback("key press", self.__on_key_pressed)
        self.add_callback("mouse move", self.__on_mouse_move)

        # Prepare the scene manager for the ZX-graph
        self.__zx_scene_manager = ZxSceneManager(self.__nx_graph)
        # self.at(ZX_VIEWPORT).add_callback("mouse left click", self.__zx_scene_manager.on_left_click)

        # Prepare the scene manager for the BG-graph
        self.__bg_scene_manager = BgSceneManager(self.__nx_graph)
        # self.at(BG_VIEWPORT).add_callback("mouse left click", self.__bg_scene_manager.on_left_click)

        self.__selected_object = None

    def __reset_camera(self):
        # Initialise the camera for the BG Graph
        bg_camera = self.at(BG_VIEWPORT).camera
        bg_camera.SetPosition(5, 3, 3)
        bg_camera.SetFocalPoint(0, 0, 0)
        bg_camera.SetViewUp(0, 0, 1)

    def __on_key_pressed(self, event):
        # Pass the key press to the BG scene manager
        self.__bg_scene_manager.on_key_press(event)
        if event.keypress == "Escape":
            self.__reset_camera()

        # Refresh the BG viewport
        self.at(BG_VIEWPORT).show(self.__bg_scene_manager.elements)

    def __show_highlight(self, selected_object):
        if isinstance(selected_object, ZxNode):
            # Highlight the zx-node and its corresponding bg-cube
            zx_node = selected_object.zx_node
            bg_cube = self.__nx_graph.get_cube(zx_node)
            self.__zx_scene_manager.show_node_highlight(zx_node)
            self.__bg_scene_manager.show_cube_highlight(bg_cube)
        elif isinstance(selected_object, ZxEdge):
            # Highlight all the pipes of that path
            pass
        elif isinstance(selected_object, BgCube):
            # Highlight the bg-cube and its corresponding zx-node
            bg_cube = selected_object.bg_cube
            zx_node = self.__nx_graph.get_node(bg_cube)
            if zx_node is not None:
                self.__zx_scene_manager.show_node_highlight(zx_node)
            self.__bg_scene_manager.show_cube_highlight(bg_cube)

            pass
        elif isinstance(selected_object, BgPipe):
            bg_source_cube = selected_object.bg_source
            bg_target_cube = selected_object.bg_target
            self.__bg_scene_manager.show_pipe_highlight(bg_source_cube, bg_target_cube)
            self.__bg_scene_manager.show_cube_highlight(bg_source_cube)
            self.__bg_scene_manager.show_cube_highlight(bg_target_cube)
            # Show the highlighting for the entire path this pipe belongs to

    def __hide_highlight(self, selected_object):
        if isinstance(selected_object, ZxNode):
            zx_node = selected_object.zx_node
            bg_cube = self.__nx_graph.get_cube(zx_node)
            self.__zx_scene_manager.hide_node_highlight(zx_node)
            self.__bg_scene_manager.hide_cube_highlight(bg_cube)
        elif isinstance(selected_object, ZxEdge):
            pass  # Highlight all the pipes of that path
        elif isinstance(selected_object, BgCube):
            bg_cube = selected_object.bg_cube
            zx_node = self.__nx_graph.get_node(bg_cube)
            self.__bg_scene_manager.hide_cube_highlight(bg_cube)
            if zx_node is not None:
                self.__zx_scene_manager.hide_node_highlight(zx_node)
            else:
                # Hide the highlighting for the entire path this cube belongs to
                pass
        elif isinstance(selected_object, BgPipe):
            bg_source_cube = selected_object.bg_source
            bg_target_cube = selected_object.bg_target
            self.__bg_scene_manager.hide_pipe_highlight(bg_source_cube, bg_target_cube)
            self.__bg_scene_manager.hide_cube_highlight(bg_source_cube)
            self.__bg_scene_manager.hide_cube_highlight(bg_target_cube)
            # Hide the highlighting for the entire path this cube belongs to

    def __on_mouse_move(self, event):
        if event.object != self.__selected_object:
            console.debug(f"Entered new object.")

            if self.__selected_object is not None:
                self.__hide_highlight(self.__selected_object)

            self.__selected_object = event.object
            self.__show_highlight(self.__selected_object)

        self.at(ZX_VIEWPORT).show(self.__zx_scene_manager.elements)
        self.at(BG_VIEWPORT).show(self.__bg_scene_manager.elements)

    def display(self):
        self.at(ZX_VIEWPORT).show(self.__zx_scene_manager.elements)
        self.at(BG_VIEWPORT).show(self.__bg_scene_manager.elements)
        self.interactive().close()