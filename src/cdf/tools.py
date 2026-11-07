"""RhinoCommon-Grundkörper für die abstrakte Komposition."""

import math
import random

import Rhino.Geometry as rg


COLOR_GROUPS = ("white", "black", "blue", "red", "yellow")


def slider_value(value, name):
    """Akzeptiere nur endliche numerische Reglerwerte von -10 bis 10."""
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(name + " muss eine Zahl zwischen -10 und 10 sein.") from error
    if not math.isfinite(value) or not -10 <= value <= 10:
        raise ValueError(name + " muss endlich sein und zwischen -10 und 10 liegen.")
    return value


def slider_factor(value, name):
    """Bilde einen Regler von -10 bis 10 auf einen Faktor von 0.6 bis 1.4 ab."""
    return 1.0 + 0.04 * slider_value(value, name)


def raster_count(value, name, reference, minimum, maximum):
    """Runde auf Rasterstufen: -10 = Minimum, 0 = Referenz, 10 = Maximum.

    Positive und negative Werte verteilen sich separat auf ihren Teilbereich.
    Halbe Rasterstufen werden von der Referenz weg gerundet.
    """
    value = slider_value(value, name)
    span = maximum - reference if value >= 0 else reference - minimum
    steps = int(math.floor(abs(value) * span / 10.0 + 0.5))
    return reference + steps if value >= 0 else reference - steps


def varied_factor(value, seed, key):
    """Stabile bauteilbezogene Größenvariation; ±10 ergibt etwa ±20–35 %."""
    value = slider_value(value, str(key))
    rng = random.Random("{}:{}".format(seed, key))
    return 1.0 + value * rng.uniform(0.02, 0.035)


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


def arch_prism(x, y, z, radius, depth, spring_height=0.0, tolerance=0.001):
    """Geschlossener Bogenkörper in XZ, extrudiert in positive Y-Richtung."""
    left = rg.Point3d(x - radius, y, z + spring_height)
    right = rg.Point3d(x + radius, y, z + spring_height)
    top = rg.Point3d(x, y, z + spring_height + radius)
    outline = rg.PolyCurve()
    if spring_height > 0:
        bottom_left = rg.Point3d(x - radius, y, z)
        bottom_right = rg.Point3d(x + radius, y, z)
        outline.Append(rg.LineCurve(bottom_left, bottom_right))
        outline.Append(rg.LineCurve(bottom_right, right))
    else:
        outline.Append(rg.LineCurve(left, right))
    outline.Append(rg.ArcCurve(rg.Arc(right, top, left)))
    if spring_height > 0:
        outline.Append(rg.LineCurve(left, bottom_left))
    surface = rg.Surface.CreateExtrusion(outline, rg.Vector3d(0, depth, 0))
    if surface is None:
        raise RuntimeError("Bogenextrusion fehlgeschlagen.")
    result = surface.ToBrep().CapPlanarHoles(tolerance)
    if result is None or not result.IsSolid:
        raise RuntimeError("Bogenkörper konnte nicht geschlossen werden.")
    return result


def cylinder_y(x, y, z, radius, depth):
    plane = rg.Plane(rg.Point3d(x, y, z), rg.Vector3d.YAxis)
    return rg.Cylinder(rg.Circle(plane, radius), depth).ToBrep(True, True)


def difference(body, cutters, tolerance=0.001):
    """Boolesche Ausschnitte; Fehler nicht als geschlossene Wand verschweigen."""
    pieces = [body]
    for cutter in cutters:
        next_pieces = []
        for piece in pieces:
            result = rg.Brep.CreateBooleanDifference(piece, cutter, tolerance)
            if not result:
                raise RuntimeError("Boolescher Ausschnitt fehlgeschlagen.")
            next_pieces.extend(result)
        pieces = next_pieces
    if len(pieces) != 1 or not pieces[0].IsValid or not pieces[0].IsSolid:
        raise RuntimeError("Ausschnitt ergibt keinen einzelnen gültigen Volumenkörper.")
    return pieces[0]


def chamfered_frame(x, y, z, width, height, depth, wall,
                    chamfer=0.45, tolerance=0.001, *, inner_chamfer=None):
    """Rechteckiger Volumenrahmen mit umlaufender innerer/äußerer 45°-Fase.

    Die Vorderseite liegt bei y, die Rückseite bei y + depth. Außen- und
    Innenfase sind unabhängig; dazwischen bleibt eine ebene Stirnfläche.
    inner_chamfer=None übernimmt die Außenfase wie bei bisherigen Aufrufen.
    Identisch geordnete Rechteckkonturen ergeben ebene, auf Gehrung
    zusammentreffende Flächen ohne toleranzabhängigen Kanten-Fillet.
    """
    if inner_chamfer is None:
        inner_chamfer = chamfer
    values = (x, y, z, width, height, depth, wall, chamfer, inner_chamfer, tolerance)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Rahmenmaße müssen endlich sein.")
    if (min(width, height, depth, wall, chamfer, inner_chamfer, tolerance) <= 0
            or 2 * wall >= min(width, height)
            or chamfer + inner_chamfer >= wall
            or max(chamfer, inner_chamfer) >= depth):
        raise ValueError("Rahmen benötigt eine Öffnung, Restwand und ausreichende Fasentiefe.")

    def rectangle(inset, at_y):
        return [rg.Point3d(x + inset, at_y, z + inset),
                rg.Point3d(x + width - inset, at_y, z + inset),
                rg.Point3d(x + width - inset, at_y, z + height - inset),
                rg.Point3d(x + inset, at_y, z + height - inset)]

    rings = [rectangle(0, y + depth), rectangle(0, y + chamfer),
             rectangle(chamfer, y), rectangle(wall - inner_chamfer, y),
             rectangle(wall, y + inner_chamfer), rectangle(wall, y + depth)]
    faces = []
    for ring, following in zip(rings, rings[1:] + rings[:1]):
        for i in range(4):
            j = (i + 1) % 4
            face = rg.Brep.CreateFromCornerPoints(ring[i], ring[j],
                                                  following[j], following[i], tolerance)
            if face is None:
                raise RuntimeError("Eine Fasenfläche konnte nicht erzeugt werden.")
            faces.append(face)
    joined = rg.Brep.JoinBreps(faces, tolerance)
    if not joined or len(joined) != 1 or not joined[0].IsValid or not joined[0].IsSolid:
        raise RuntimeError("Der gefaste Rahmen konnte nicht geschlossen werden.")
    result = joined[0]
    if result.SolidOrientation == rg.BrepSolidOrientation.Inward:
        result.Flip()
    return result


def rotated_z(geometry, angle, center):
    result = geometry.Duplicate()
    rotation = rg.Transform.Rotation(angle, rg.Vector3d.ZAxis, rg.Point3d(*center))
    if not result.Transform(rotation):
        raise RuntimeError("Gebäudeflügel konnte nicht gedreht werden.")
    return result


def transformed(geometry, scale, origin):
    result = geometry.Duplicate()
    result.Transform(rg.Transform.Scale(rg.Point3d.Origin, scale))
    result.Transform(rg.Transform.Translation(*origin))
    return result
