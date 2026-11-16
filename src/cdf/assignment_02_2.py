"""Centered planar Truchet tiles, synchronized to Rhino with print widths.

GH inputs q..z plus p, no geometry preview output required::

    from cdf import assignment_02
    assignment_02.geometry(q, r, s, t, u, v, w, x, y, z, p,
        cache_id=str(ghenv.Component.InstanceGuid))
    ghenv.Component.Hidden = True
"""
import math
import random

ROOT = "CDF_Tiles"
PATTERNS = ("B", "R", "BR", "RB", "BBR", "RRB", "BBRR", "RRBB",
            "BBBR", "RBBB", "BBBRR", "RRBBB", "BBBRRR", "RRRBBB")


def _number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Controls must be finite numbers.")
    return value


def _control(value, low, high):
    return max(low, min(high, _number(value)))


def _integer(value, high):
    return int(math.floor(_control(value, 1, high) + 0.5))


def _weight(value):
    value = _number(value)
    if value <= 0:
        raise ValueError("Line widths must be positive.")
    return value / 10


def tile_layout(count, patterns):
    """Rows run top to bottom; repeat and truncate each selected word."""
    words = [PATTERNS[_integer(p, 14) - 1] for p in patterns]
    if len(words) != 4:
        raise ValueError("Exactly four row patterns are required.")
    return [(col, row, words[row % 4][col % len(words[row % 4])])
            for row in range(count) for col in range(count)]


def _simple_polygon(points):
    """Reject crossings, touches and overlaps of nonadjacent control edges."""
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

    for i in range(len(points) - 1):
        a, b = points[i:i+2]
        for j in range(i + 2, len(points) - 1):
            c, d = points[j:j+2]
            if (max(a[0], b[0]) < min(c[0], d[0]) or
                    max(c[0], d[0]) < min(a[0], b[0]) or
                    max(a[1], b[1]) < min(c[1], d[1]) or
                    max(c[1], d[1]) < min(a[1], b[1])):
                continue
            if cross(a, b, c)*cross(a, b, d) <= 0 and cross(c, d, a)*cross(c, d, b) <= 0:
                return False
    return True


def _control_points(cx, cy, sx, sy, strength, rng):
    """Bound handles, separate inner points and keep the control polygon simple."""
    reference = [(0.5, 0), (0.5, 0.16), (0.49, 0.30),
                 (0.30, 0.49), (0.16, 0.5), (0, 0.5)]
    minimum = 0.25 + 0.20 * strength
    h1, h2 = rng.uniform(0.125, 0.25), rng.uniform(0.125, 0.25)
    for _ in range(200):
        target = [(0.5, 0), (0.5, h1),
                  (rng.uniform(0.001, 0.999), rng.uniform(0.001, 0.999)),
                  (rng.uniform(0.001, 0.999), rng.uniform(0.001, 0.999)),
                  (h2, 0.5), (0, 0.5)]
        points = [(a[0]*(1-strength) + b[0]*strength,
                   a[1]*(1-strength) + b[1]*strength) for a, b in zip(reference, target)]
        if any(x*x+y*y < 0.25 or (1-x)**2+(1-y)**2 < 0.25 for x,y in points[2:4]):
            continue
        if math.dist(points[2], points[3]) < minimum:
            continue
        if _simple_polygon(points):
            break
    else:
        # A deterministic valid polygon when rejection sampling is exhausted.
        separation = minimum / math.sqrt(2) + 0.01
        points = [(0.5, 0), (0.5, 0.16*(1-strength)+h1*strength),
                  (0.5+separation/2, 0.5-separation/2),
                  (0.5-separation/2, 0.5+separation/2),
                  (0.16*(1-strength)+h2*strength, 0.5), (0, 0.5)]
    return [(cx + sx*x, cy + sy*y, 0) for x,y in points]

def _corner_curve(rg, cx, cy, sx, sy, strength, rng):
    if strength == 0:
        return rg.Arc(rg.Point3d(cx + sx * 0.5, cy, 0),
                      rg.Point3d(cx + sx * math.sqrt(0.125), cy + sy * math.sqrt(0.125), 0),
                      rg.Point3d(cx, cy + sy * 0.5, 0)).ToNurbsCurve()
    points = _control_points(cx, cy, sx, sy, strength, rng)
    return rg.NurbsCurve.Create(False, 5, [rg.Point3d(*point) for point in points])


def _tile_curves(rg, corners, strength, seed, row, col):
    """Reduce conflicting deformations, retaining the same random controls."""
    for attempt in range(13):
        amount = strength * 0.75 ** attempt if attempt < 12 else 0
        curves = [_corner_curve(rg, *corner, amount,
                               random.Random("{}:{}:{}:{}".format(seed, row, col, index)))
                  for index, corner in enumerate(corners)]
        if amount == 0:
            return curves
        if any(curve is None or not curve.IsValid for curve in curves):
            continue
        intersection = rg.Intersect.Intersection
        if any(intersection.CurveSelf(curve, 1e-8).Count for curve in curves):
            continue
        if not intersection.CurveCurve(curves[0], curves[1], 1e-8, 1e-8).Count:
            return curves


def _palette(distinction):
    return {
        "tiles": ("01_TileBorders", (0, 0, 0), 0.0, 0.0),
        "blue": ("02_BlueTiles", (0, 82, 147) if distinction else (0, 0, 0), 0.0, 0.0),
        "red": ("03_RedTiles", (192, 0, 0) if distinction else (0, 0, 0), 0.0, 0.0),
    }

def create_geometry(size=1, tile_size=1, line_curve=0,
                    pattern1=1, pattern2=2, pattern3=3, pattern4=4, *, curve_seed=0):
    """Return planar curves in three permanent groups without modifying the document."""
    import Rhino.Geometry as rg

    count = _integer(size, 20)
    side = _control(tile_size, 1, 10) * 5
    strength = _control(line_curve, 0, 10) / 10
    seed = _control(curve_seed, 0, 10)
    half = count * side / 2
    groups = {"tiles": [], "blue": [], "red": []}
    for i in range(count + 1):
        p = -half + i * side
        groups["tiles"].extend((
            rg.LineCurve(rg.Point3d(p, -half, 0), rg.Point3d(p, half, 0)),
            rg.LineCurve(rg.Point3d(-half, p, 0), rg.Point3d(half, p, 0))))
    for col, row, form in tile_layout(count, (pattern1, pattern2, pattern3, pattern4)):
        corners = ((0, 0, 1, 1), (1, 1, -1, -1)) if form == "B" else (
            (0, 1, 1, -1), (1, 0, -1, 1))
        curves = _tile_curves(rg, corners, strength, seed, row, col)
        for curve in curves:
            curve.Transform(rg.Transform.Scale(rg.Point3d.Origin, side))
            curve.Transform(rg.Transform.Translation(-half + col * side,
                                                     half - (row + 1) * side, 0))
        groups["blue" if form == "B" else "red"].extend(curves)
    return groups


def geometry(q=1, r=1, s=1, t=1, u=0, v=0, w=1, x=2, y=3, z=4, p=False, *,
             cache_id="assignment02", force=False):
    """q=size, r=tile size, s/t=print widths, u=curvature, v=curve seed,
    w/x/y/z=row patterns, p=pattern distinction. Always returns None.
    """
    import Rhino
    from . import layer

    weights = {"tiles": _weight(s), "blue": _weight(t), "red": _weight(t)}
    groups = create_geometry(q, r, u, w, x, y, z, curve_seed=v)
    layer.cache_geometry(groups, cache_id, force=force, palette=_palette(p),
                         root=ROOT, plot_weights=weights)
    Rhino.RhinoApp.RunScript("_PrintDisplay _State=_On _Enter", False)
    Rhino.RhinoDoc.ActiveDoc.Views.Redraw()


