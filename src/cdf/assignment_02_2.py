"""Centered planar Truchet tiles, synchronized to Rhino with print widths.

Grasshopper Python inputs: six numeric controls, the algorithm slider (1–10),
three colour swatches (tlc, lc, bc), three Boolean toggles (bt, ft, pt),
and the contrast and transparency sliders (c and x, each 0–10)::

    from cdf import assignment_02_2
    assignment_02_2.geometry(
        size, tile_size, tile_linewidth, line_linewidth, line_curve, seed,
        algorithm=algorithm, tile_line_color=tlc, line_color=lc, background_color=bc,
        background=bt, fill_patterns=ft, pattern_distinction=pt, contrast=c,
        transparency=x,
        cache_id=str(ghenv.Component.InstanceGuid),
    )
    ghenv.Component.Hidden = True

With bt and ft enabled and pt off, connected motif regions receive seeded
lighter/darker variants of bc, ignoring internal tile borders. At contrast 0
all variants equal bc; otherwise shades span the former 25–75% levels.
With pt on, tile borders are black, the fill darkens the blue/red motif colour
by at most 25%, and ft is ignored. Transparency applies only to fills: 0 is
opaque, 10 omits fills.
"""
import math
import random

ROOT = "CDF_Tiles"


def _number(value):
    value = float(getattr(value, "Value", value))
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


def _orientation_runs(algorithm, seed):
    color = "B"
    if algorithm == 10:
        rng = random.Random("tile layout:{}".format(seed))
        while True:
            yield color, rng.randint(1, 5)
            color = "R" if color == "B" else "B"

    lengths = (1, 1, 2, 3, 5) if algorithm == 9 else range(1, 6)
    while True:
        for length in lengths:
            if algorithm == 6:
                yield "B", 1
                yield "R", length
            elif algorithm == 7:
                yield "B", length
                yield "R", length
            else:
                yield color, length
                color = "R" if color == "B" else "B"


def tile_layout(count, algorithm=1, *, curve_seed=0):
    """Return (col, row, orientation) tiles, starting at the top left.

    Algorithms: 1 checkerboard, 2 vertical stripes, 3 horizontal stripes,
    4 diagonal bands, 5 square rings, 6 single blue tiles alternating with
    growing red runs, 7 paired lengths, 8 increasing lengths, 9 Fibonacci
    lengths, and 10 seeded random lengths. Runs are at most five tiles long
    and continue across row breaks.
    Floats round to the nearest integer, with halves rounded up.
    """
    algorithm = _integer(algorithm, 10)
    if algorithm >= 6:
        runs = _orientation_runs(algorithm, _control(curve_seed, 0, 10))
        layout = []
        remaining = 0
        for row in range(count):
            for col in range(count):
                if remaining == 0:
                    color, remaining = next(runs)
                layout.append((col, row, color))
                remaining -= 1
        return layout

    layout = []
    for row in range(count):
        for col in range(count):
            if algorithm == 1:
                red = (row + col) % 2 == 1
            elif algorithm == 2:
                red = col % 2 == 1
            elif algorithm == 3:
                red = row % 2 == 1
            elif algorithm == 4:
                red = (row + col) % 4 >= 2
            else:
                depth = min(row, col, count - 1 - row, count - 1 - col)
                red = depth % 2 == 1
            layout.append((col, row, "R" if red else "B"))
    return layout


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


def _rgb(color, default):
    if color is None:
        return default
    color = getattr(color, "Value", color)
    return int(color.R), int(color.G), int(color.B)


_SHADE_STEPS = 20
_SHADE_PREFIX = "fill_shade_"


def _shade(rgb, amount):
    target = 255 if amount > 0 else 0
    return tuple(round(channel + (target - channel) * abs(amount)) for channel in rgb)


def _palette(distinction, background, tile_line_color, line_color, background_color,
             groups, contrast):
    border = (0, 0, 0) if distinction else _rgb(tile_line_color, (0, 0, 0))
    if distinction:
        blue, red = (0, 82, 147), (192, 0, 0)
    else:
        blue = red = _rgb(line_color, (0, 0, 0))
    palette = {
        "tiles": ("01_TileBorders", border, 0.0, 0.0),
        "blue": ("02_BlueTiles", blue, 0.0, 0.0),
        "red": ("03_RedTiles", red, 0.0, 0.0),
    }
    if background:
        if distinction:
            palette["fill_blue"] = ("04_BlueBackground", _shade(blue, -contrast / 4), 0.0, 0.0)
            palette["fill_red"] = ("05_RedBackground", _shade(red, -contrast / 4), 0.0, 0.0)
        else:
            base = _rgb(background_color, (240, 240, 240))
            if "fill" in groups:
                palette["fill"] = ("06_Background", base, 0.0, 0.0)
            for key in groups:
                if key.startswith(_SHADE_PREFIX):
                    level = int(key[len(_SHADE_PREFIX):])
                    shade_level = 0.25 + 0.5 * level / _SHADE_STEPS
                    amount = (shade_level - 0.5) * contrast
                    palette[key] = ("{}_PatternFill".format(100 + level), _shade(base, amount), 0.0, 0.0)
    return palette


def _pattern_fills(rg, groups, half, tolerance, pattern_index, seed):
    from System import Array

    plane = rg.Plane.WorldXY
    frame = rg.Rectangle3d(plane, rg.Point3d(-half, -half, 0),
                           rg.Point3d(half, half, 0)).ToNurbsCurve()
    # Join the motifs across tile edges; only the outer frame bounds the regions.
    paths = rg.Curve.JoinCurves(Array[rg.Curve](groups["blue"] + groups["red"]), tolerance)
    if not paths:
        raise RuntimeError("Could not join the tile motif curves.")
    regions = rg.Curve.CreateBooleanRegions(Array[rg.Curve]([frame] + list(paths)),
                                           plane, False, tolerance)
    if regions is None:
        raise RuntimeError("Could not find the enclosed motif regions.")
    try:
        count = regions.RegionCount
        if count != len(paths) + 1:
            raise RuntimeError("Could not resolve all enclosed motif regions.")
        rng = random.Random("pattern fills:{}".format(seed))
        for start in range(0, count, _SHADE_STEPS + 1):
            batch = min(_SHADE_STEPS + 1, count - start)
            levels = ([round(i * _SHADE_STEPS / (batch - 1)) for i in range(batch)]
                      if batch > 1 else [rng.randrange(_SHADE_STEPS + 1)])
            rng.shuffle(levels)
            for index, level in enumerate(levels, start):
                loops = list(regions.RegionCurves(index))
                if not loops:
                    raise RuntimeError("Could not read a motif region boundary.")
                hatch = rg.Hatch.Create(plane, loops[0], Array[rg.Curve](loops[1:]),
                                        pattern_index, 0.0, 1.0)
                if hatch is None or not hatch.IsValid:
                    raise RuntimeError("Could not fill an enclosed motif region.")
                groups.setdefault(_SHADE_PREFIX + str(level), []).append(hatch)
    finally:
        regions.Dispose()


def create_geometry(size=1, tile_size=1, line_curve=0, algorithm=1, *, curve_seed=0,
                    fill_pattern_index=None, pattern_distinction=False, fill_patterns=False):
    """Return planar curves and optional solid fills without modifying the document."""
    import Rhino.Geometry as rg

    count = _integer(size, 20)
    layout = tile_layout(count, algorithm, curve_seed=curve_seed)
    side = _control(tile_size, 1, 10) * 5
    strength = _control(line_curve, 0, 10) / 10
    seed = _control(curve_seed, 0, 10)
    half = count * side / 2
    groups = {"tiles": [], "blue": [], "red": []}
    region_fills = fill_pattern_index is not None and fill_patterns and not pattern_distinction
    tile_fills = fill_pattern_index is not None and not region_fills
    if tile_fills:
        for key in ("fill_blue", "fill_red") if pattern_distinction else ("fill",):
            groups[key] = []
    for i in range(count + 1):
        p = -half + i * side
        groups["tiles"].extend((
            rg.LineCurve(rg.Point3d(p, -half, 0), rg.Point3d(p, half, 0)),
            rg.LineCurve(rg.Point3d(-half, p, 0), rg.Point3d(half, p, 0))))
    for col, row, form in layout:
        corners = ((0, 0, 1, 1), (1, 1, -1, -1)) if form == "B" else (
            (0, 1, 1, -1), (1, 0, -1, 1))
        x, y = -half + col * side, half - (row + 1) * side
        color_key = "blue" if form == "B" else "red"
        curves = _tile_curves(rg, corners, strength, seed, row, col)
        for curve in curves:
            curve.Transform(rg.Transform.Scale(rg.Point3d.Origin, side))
            curve.Transform(rg.Transform.Translation(x, y, 0))
        groups[color_key].extend(curves)
        if tile_fills:
            boundary = rg.Rectangle3d(rg.Plane.WorldXY, rg.Point3d(x, y, 0),
                                      rg.Point3d(x + side, y + side, 0)).ToNurbsCurve()
            fills = rg.Hatch.Create(boundary, fill_pattern_index, 0.0, 1.0, side * 1e-6)
            if fills is None or len(fills) != 1:
                raise RuntimeError("Could not create a solid tile background.")
            key = "fill_" + color_key if pattern_distinction else "fill"
            groups[key].append(fills[0])
    if region_fills:
        _pattern_fills(rg, groups, half, side * 1e-6, fill_pattern_index, seed)
    return groups


def _solid_pattern_index(doc):
    import Rhino

    solid = Rhino.DocObjects.HatchPattern.Defaults.Solid
    existing = doc.HatchPatterns.FindName(solid.Name)
    if existing is not None:
        return existing.Index
    index = doc.HatchPatterns.Add(solid)
    if index < 0:
        raise RuntimeError("Could not add the solid hatch pattern.")
    return index


def geometry(q=1, r=1, s=1, t=1, u=0, v=0, algorithm=1, p=False, *,
             tile_line_color=None, line_color=None, background_color=None,
             background=False, pattern_distinction=None, fill_patterns=False, contrast=4,
             transparency=0, cache_id="assignment02", force=False):
    """Synchronize tile curves and optional fills in Rhino; returns None.

    q/r set field and tile size, s/t set print widths, u/v set curvature and seed.
    p is the legacy name for pattern_distinction. Transparency ranges from
    0 (opaque fills) to 10 (no fills), without affecting the curves.
    """
    import Rhino
    from . import layer

    doc = Rhino.RhinoDoc.ActiveDoc
    if doc is None:
        raise RuntimeError("No active Rhino document is available.")
    distinction = p if pattern_distinction is None else pattern_distinction
    distinction = bool(getattr(distinction, "Value", distinction))
    transparency = _control(transparency, 0, 10)
    background = bool(getattr(background, "Value", background)) and transparency < 10
    fill_patterns = bool(getattr(fill_patterns, "Value", fill_patterns))
    contrast = _control(contrast, 0, 10) / 10
    tile_weight, line_weight = _weight(s), _weight(t)
    fill_index = _solid_pattern_index(doc) if background else None
    groups = create_geometry(q, r, u, algorithm=algorithm, curve_seed=v,
                             fill_pattern_index=fill_index, pattern_distinction=distinction,
                             fill_patterns=fill_patterns)
    palette = _palette(distinction, background, tile_line_color, line_color, background_color,
                       groups, contrast)
    if background and transparency > 0:
        alpha = max(1, round(255 * (1 - transparency / 10)))
        for key, (name, rgb, shine, reflection) in palette.items():
            if key.startswith("fill"):
                palette[key] = (name, (alpha, *rgb), shine, reflection)
    weights = {key: line_weight if key in ("blue", "red") else tile_weight for key in palette}
    ids = layer.cache_geometry(groups, cache_id, doc=doc, force=force, palette=palette,
                               root=ROOT, plot_weights=weights)
    if background:
        # Keep the coplanar fills behind the tile grid and motif curves.
        for object_id in ids:
            obj = doc.Objects.FindId(object_id)
            if isinstance(obj, Rhino.DocObjects.HatchObject) and obj.Attributes.DisplayOrder != -1:
                attributes = obj.Attributes.Duplicate()
                attributes.DisplayOrder = -1
                if not doc.Objects.ModifyAttributes(object_id, attributes, True):
                    raise RuntimeError("Could not set the tile background draw order.")
    Rhino.RhinoApp.RunScript("_PrintDisplay _State=_On _Enter", False)
    doc.Views.Redraw()


