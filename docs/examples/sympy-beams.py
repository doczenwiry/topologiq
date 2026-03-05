from sympy.geometry import Point3D, Ray3D

Coordinates = Point3D
Beam = Ray3D

source1 = Coordinates(0, 0, 0)
direction1 = Coordinates(1, 0, 0)
r1 = Beam(source1, source1 + direction1)

print(r1.contains(Coordinates(0, 0, 0)))

source2 = Coordinates(1, 0, -1)
direction2 = Coordinates(0, 0, 1)
r2 = Beam(source2, source2 + direction2)

print(r1.intersection(r2))

source3 = Coordinates(0, 1, 0)
direction3 = Coordinates(0, 0, 1)
r3 = Beam(source3, source3 + direction3)

print(r1.intersection(r3))

# print(r1.is_on_ray(Point3D(2, 0, 0)))

from topologiq.utils.beams_sympy import SympyBeam

source1 = Coordinates(0, 0, 0)
direction1 = Coordinates(1, 0, 0)
b1 = SympyBeam(source1, direction1)

source2 = Coordinates(0, 0, 0)
direction2 = Coordinates(1, 0, 0)
b2 = SympyBeam(source2, direction2)

print(f"Beam 1 : {b1}")
print(f"Beam 2 : {b2}")
print(f"Beam =?: {b1 == b2}")