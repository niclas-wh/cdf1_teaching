"""RhinoCommon primitives, control mappings and transforms for the composition."""

import math
import random

import Rhino.Geometry as rg


COLOR_GROUPS = ("white", "black", "blue", "red", "yellow")


def slider_value(value, name):
    """Convert a control value to a finite float in the inclusive range [-10, 10]."""
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(name + " must be a number between -10 and 10.") from error
    if not math.isfinite(value) or not -10 <= value <= 10:
        raise ValueError(name + " must be finite and between -10 and 10.")
    return value


def slider_factor(value, name):
    """Map [-10, 10] linearly to a size factor of [0.6, 1.4], with 0 mapping to 1."""
    return 1.0 + 0.04 * slider_value(value, name)


def raster_count(value, name, reference, minimum, maximum):
    """Round to grid counts: -10 = minimum, 0 = reference, 10 = maximum.

    Each sign uses its own span between the reference and the corresponding
    endpoint. Half steps are rounded away from the reference count.
    """
    value = slider_value(value, name)
    span = maximum - reference if value >= 0 else reference - minimum
    steps = int(math.floor(abs(value) * span / 10.0 + 0.5))
    return reference + steps if value >= 0 else reference - steps


def varied_factor(value, seed, key):
    """Return a seed/key-stable factor; +/-10 produces a +/-20-35% size change."""
    value = slider_value(value, str(key))
    rng = random.Random("{}:{}".format(seed, key))
    return 1.0 + value * rng.uniform(0.02, 0.035)


def random_direction(rng, planar=False):
    """Sample a uniform unit direction in the XY plane or in three dimensions."""
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
    """Interpolate (radius, height) samples and revolve them around a vertical axis."""
    points = [rg.Point3d(x + radius, y, z + height)
              for radius, height in profile]
    curve = rg.Curve.CreateInterpolatedCurve(points, 3)
    axis = rg.Line(rg.Point3d(x, y, z), rg.Point3d(x, y, z + 1))
    surface = rg.RevSurface.Create(curve, axis, 0.0, 2.0 * math.pi)
    if surface is None:
        raise RuntimeError("Could not create the revolved profile.")
    return surface.ToBrep()


def arch_prism(x, y, z, radius, depth, spring_height=0.0, tolerance=0.001):
    """Create a capped XZ arch extruded along +Y; zero spring height gives a half-disc."""
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
        raise RuntimeError("Arch extrusion failed.")
    result = surface.ToBrep().CapPlanarHoles(tolerance)
    if result is None or not result.IsSolid:
        raise RuntimeError("Could not cap the arch solid.")
    return result


def cylinder_y(x, y, z, radius, depth):
    plane = rg.Plane(rg.Point3d(x, y, z), rg.Vector3d.YAxis)
    return rg.Cylinder(rg.Circle(plane, radius), depth).ToBrep(True, True)


def difference(body, cutters, tolerance=0.001):
    """Subtract cutters, raising on failure instead of silently returning an uncut wall."""
    pieces = [body]
    for cutter in cutters:
        next_pieces = []
        for piece in pieces:
            result = rg.Brep.CreateBooleanDifference(piece, cutter, tolerance)
            if not result:
                raise RuntimeError("Boolean subtraction failed.")
            next_pieces.extend(result)
        pieces = next_pieces
    if len(pieces) != 1 or not pieces[0].IsValid or not pieces[0].IsSolid:
        raise RuntimeError("Subtraction did not produce a single valid solid.")
    return pieces[0]


def chamfered_frame(x, y, z, width, height, depth, wall,
                    chamfer=0.45, tolerance=0.001, *, inner_chamfer=None):
    """Create a rectangular solid frame with continuous inner/outer 45-degree chamfers.

    The front lies at y and the back at y + depth. Outer and inner chamfers
    are independent, with a flat front band between them. inner_chamfer=None
    uses the outer chamfer width. Consistently ordered rectangular rings form
    planar, mitered faces without relying on tolerance-sensitive edge fillets.
    Embed the straight outer section behind the facade to expose only the bevel.
    """
    if inner_chamfer is None:
        inner_chamfer = chamfer
    values = (x, y, z, width, height, depth, wall, chamfer, inner_chamfer, tolerance)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Frame dimensions must be finite.")
    if (min(width, height, depth, wall, chamfer, inner_chamfer, tolerance) <= 0
            or 2 * wall >= min(width, height)
            or chamfer + inner_chamfer >= wall
            or max(chamfer, inner_chamfer) >= depth):
        raise ValueError("The frame needs an opening, a remaining front band and sufficient chamfer depth.")

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
                raise RuntimeError("Could not create a frame face.")
            faces.append(face)
    joined = rg.Brep.JoinBreps(faces, tolerance)
    if not joined or len(joined) != 1 or not joined[0].IsValid or not joined[0].IsSolid:
        raise RuntimeError("Could not join the chamfered frame into a closed solid.")
    result = joined[0]
    if result.SolidOrientation == rg.BrepSolidOrientation.Inward:
        result.Flip()
    return result


def rotated_z(geometry, angle, center):
    result = geometry.Duplicate()
    rotation = rg.Transform.Rotation(angle, rg.Vector3d.ZAxis, rg.Point3d(*center))
    if not result.Transform(rotation):
        raise RuntimeError("Could not rotate the building wing.")
    return result


def transformed(geometry, scale, origin):
    result = geometry.Duplicate()
    result.Transform(rg.Transform.Scale(rg.Point3d.Origin, scale))
    result.Transform(rg.Transform.Translation(*origin))
    return result
