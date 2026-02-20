from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph

from vedo import Plotter
from topologiq.dzw.visualisation.components_vedo import BgCube, BgPipe

import logging
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)

class AugmentedNxGraphViewer(Plotter):
    def __init__(self, anx: AugmentedNxGraph, label: str):
        super().__init__(title = f"ang-viewer [{label}]")
        self.camera.SetPosition(5, 3, 3)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 0, 1)

        self.__scene = []
        for cube in anx.get_cubes():
            kind = anx.get_cube_kind(cube)
            position = anx.get_cube_position(cube)
            self.__scene.append(
                BgCube(kind, position)
            )

        for source, target in anx.get_pipes():
            source_kind = anx.get_cube_kind(source)
            source_position = anx.get_cube_position(source)
            target_kind = anx.get_cube_kind(target)
            target_position = anx.get_cube_position(target)
            pipe_type = anx.get_pipe_type(source, target)
            self.__scene.append(
                BgPipe(source_kind, source_position, target_kind, target_position, pipe_type)
            )

    def display(self):
        self.show(self.__scene, axes=0)
        self.render()
        self.interactive().close()