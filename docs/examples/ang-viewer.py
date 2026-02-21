import pyzx as zx

from topologiq.dzw.utils.augmented_nx_graph import AugmentedNxGraph
from topologiq.dzw.vedo.ang_viewer import AugmentedNxGraphViewer

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('utils').setLevel(logging.INFO)
logging.getLogger('helpers').setLevel(logging.CRITICAL)
logging.getLogger('visualisation').setLevel(logging.DEBUG)

from jsonpickle import encode, decode
ANG_PATH = "../../assets/ang/"
def ang_write(ang: AugmentedNxGraph, label: str):
    with open(ANG_PATH + label + ".json", "w") as f:
        f.write(encode(ang, indent=2, keys = True, unpicklable=True))

def ang_read(label: str):
    return decode(open(ANG_PATH + label + ".json").read(), keys = True)

if __name__ == '__main__':
    circuit = zx.Circuit(2)
    circuit.add_gate("CNOT", 0, 1)
    circuit.add_gate("CNOT", 1, 0)
    circuit.add_gate("CNOT", 1, 0)
    zx_input = circuit.to_graph()
    # zx.draw(zx_input, labels = True)

    name = "three-cnots"
    anx: AugmentedNxGraph = ang_read(label = name)

    viewer = AugmentedNxGraphViewer(anx, label = name)
    viewer.display()