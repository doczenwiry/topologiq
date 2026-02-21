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

        # Prepare the scene manager for the ZX-graph
        self.__zx_scene_manager = ZxSceneManager(self.__nx_graph)
        self.at(ZX_VIEWPORT).add_callback("mouse left click", self.__zx_scene_manager.on_left_click)

        # Prepare the scene manager for the BG-graph
        self.__bg_scene_manager = BgSceneManager(self.__nx_graph)
        self.at(BG_VIEWPORT).add_callback("mouse left click", self.__bg_scene_manager.on_left_click)

    def __reset_camera(self):
        # Initialise the camera for the BG Graph
        bg_camera = self.at(BG_VIEWPORT).camera
        bg_camera.SetPosition(5, 3, 3)
        bg_camera.SetFocalPoint(0, 0, 0)
        bg_camera.SetViewUp(0, 0, 1)

    def __on_key_pressed(self, event):
        console.debug(f"> Keypress : {event.keypress}")

        self.__bg_scene_manager.on_key_press(event)
        if event.keypress == "Escape":
            self.__reset_camera()

        # Refresh the BG viewport
        self.at(BG_VIEWPORT).show(self.__bg_scene_manager.elements)

    def display(self):
        self.at(ZX_VIEWPORT).show(self.__zx_scene_manager.elements)
        self.at(BG_VIEWPORT).show(self.__bg_scene_manager.elements)
        self.interactive().close()