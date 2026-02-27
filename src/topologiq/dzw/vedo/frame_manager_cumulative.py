from typing import Iterable
from vedo import Mesh
from vedo.plotter.runtime import Plotter

from logging import getLogger
console = getLogger(__name__)

FrameIndex = int

class CumulativeFrameManager:
    def __init__(self, plotter: Plotter):
        self.__plotter = plotter
        self.__frames: list[list[list[Mesh]]] = []
        self.__frame_index = 0
        self.__frame_total = 0
        self.__subframe_index = 0

    def log_frame_report(self):
        console.debug(f"Cumulative Frame Manager report")
        for f in range(len(self.__frames)):
            console.debug(f"> Frame {f+1}/{len(self.__frames)} : {len(self.__frames[f][0])}")

    def get_frame_count(self):
        return len(self.__frames)

    def create_next_frame(self) -> FrameIndex:
        self.__frames.append( [] )
        frame_index = self.__frame_total
        self.__frames[frame_index].append([])
        self.__frame_total += 1
        return frame_index

    def add_to_frame(self, frame_index, mesh: Mesh, subframe_index: int = 0):
        self.__frames[frame_index][subframe_index].append(mesh)

    def add_all_to_frame(self, frame_index, meshes: Iterable[Mesh], subframe_index: int = 0):
        self.__frames[frame_index][subframe_index].extend(meshes)

    def create_next_subframe(self, frame_index: int) -> FrameIndex:
        self.__frames[frame_index].append( [] )
        return len(self.__frames[frame_index]) - 1

    def set_current_frame(self, frame_index: int, subframe_index: int = 0):
        console.debug(f"Setting current frame to #{frame_index}")
        self.__plotter.clear()
        for f in range(frame_index + 1):
            self.__plotter.show(self.__frames[f][0])
        self.__frame_index = frame_index

    def move_frame(self, count: int = 0):
        if count < 0:
            self.__move_frame_backward(abs(count))
        elif count > 0:
            self.__move_frame_forward(count)

        subframe_notice = f"[SF:{self.__subframe_index + 1}/{len(self.__frames[self.__frame_index - 1])}]"
        console.debug(f"> Frame {self.__frame_index + 1}/{len(self.__frames)} {subframe_notice}")

    def __move_frame_forward(self, count: int = 1):
        frame_count = min(count, self.__frame_total - self.__frame_index - 1)
        console.debug(f"> Forward frame : {frame_count}")
        for frame in range(frame_count):
            self.__plotter.show(self.__frames[self.__frame_index + frame - 1][0])
        self.__frame_index += frame_count

    def __move_frame_backward(self, count: int = 1):
        frame_count = min(count, self.__frame_index)
        console.debug(f"> Backward frame : {frame_count}")
        for frame in range(frame_count):
            for mesh in self.__frames[self.__frame_index - frame][0]:
                self.__plotter.remove( mesh )
        self.__frame_index -= frame_count

    # def __reset_subframe(self):
    #     current_subframe = self.__frames[self.__frame_index][self.__subframe_index]
    #     for mesh in current_subframe[self.__subframe_index]:
    #         mesh.hide()
    #     self.__subframe_index = 0
    #     for mesh in current_subframe[self.__subframe_index]:
    #         mesh.show()
    #
    # def __move_subframe_forward(self):
    #     current_subframes = self.__subframes[self.__frame_index]
    #     console.debug(f"Forward subframe: {self.__subframe_index + 1} [{len(current_subframes)}]")
    #     if self.__subframe_index < len(current_subframes) - 1:
    #         for mesh in current_subframes[self.__subframe_index]:
    #             mesh.hide()
    #         self.__subframe_index += 1
    #         for mesh in current_subframes[self.__subframe_index]:
    #             mesh.show()
    #
    # def __move_subframe_backward(self):
    #     current_subframes = self.__subframes[self.__frame_index]
    #     console.debug(f"Backward subframe: {self.__subframe_index - 1} [{len(current_subframes)}]")
    #     if self.__subframe_index > 0:
    #         for mesh in current_subframes[self.__subframe_index]:
    #             mesh.hide()
    #         self.__subframe_index -= 1
    #         for mesh in current_subframes[self.__subframe_index]:
    #             mesh.show()