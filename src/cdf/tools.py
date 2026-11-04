"""RhinoCommon-Grundkörper für die abstrakte Komposition."""

import math

import Rhino.Geometry as rg


COLOR_GROUPS = ("white", "black", "blue", "red", "yellow")


def slider_factor(value, name):
    """Bilde einen Regler von -10 bis 10 auf einen Faktor von 0.6 bis 1.4 ab."""
    if not math.isfinite(value) or not -10 <= value <= 10:
        raise ValueError(name + " muss endlich sein und zwischen -10 und 10 liegen.")
    return 1.0 + 0.04 * value


def random_direction(rng, planar=False):
    """Erzeuge einen gleichverteilten Einheitsvektor in XY oder im Raum."""
    angle = rng.uniform(0.0, 2.0 * math.pi)
    z = 0.0 if planar else rng.uniform(-1.0, 1.0)
    radius = math.sqrt(max(0.0, 1.0 - z * z))
    return radius * math.cos(angle), radius * math.sin(angle), z


def box(x, y, z, width, depth, height):
    return rg.BoundingBox(
        rg.Point3d(x, y, z),
        rg.Point3d(x + width, y + depth, z + height),
    ).ToBrep()


def sphere(x, y, z, radius):
    return rg.Sphere(rg.Point3d(x, y, z), radius).ToBrep()


def cylinder(x, y, z, radius, height):
    plane = rg.Plane(rg.Point3d(x, y, z), rg.Vector3d.ZAxis)
    return rg.Cylinder(rg.Circle(plane, radius), height).ToBrep(True, True)


def polyhedron(vertices, faces):
    mesh = rg.Mesh()
    for vertex in vertices:
        mesh.Vertices.Add(*vertex)
    for face in faces:
        mesh.Faces.AddFace(*face)
    mesh.UnifyNormals()
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh


def pyramid(x, y, z, size, height):
    r = size / 2.0
    return polyhedron(
        [(x-r, y-r, z), (x+r, y-r, z),
         (x+r, y+r, z), (x-r, y+r, z), (x, y, z+height)],
        [(3, 2, 1, 0), (0, 1, 4), (1, 2, 4),
         (2, 3, 4), (3, 0, 4)],
    )


def wedge(x, y, z, width, depth, front_height, back_height):
    return polyhedron(
        [(x, y, z), (x+width, y, z),
         (x+width, y+depth, z), (x, y+depth, z),
         (x, y, z+front_height), (x+width, y, z+front_height),
         (x+width, y+depth, z+back_height), (x, y+depth, z+back_height)],
        [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)],
    )


def revolved_profile(x, y, z, profile):
    """Drehe ein (Radius, Höhe)-Profil um die vertikale Achse."""
    points = [rg.Point3d(x + radius, y, z + height)
              for radius, height in profile]
    curve = rg.Curve.CreateInterpolatedCurve(points, 3)
    axis = rg.Line(rg.Point3d(x, y, z), rg.Point3d(x, y, z + 1))
    surface = rg.RevSurface.Create(curve, axis, 0.0, 2.0 * math.pi)
    if surface is None:
        raise RuntimeError("Das Rotationsprofil konnte nicht erzeugt werden.")
    return surface.ToBrep()


def transformed(geometry, scale, origin):
    result = geometry.Duplicate()
    result.Transform(rg.Transform.Scale(rg.Point3d.Origin, scale))
    result.Transform(rg.Transform.Translation(*origin))
    return result
