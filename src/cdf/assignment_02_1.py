"""Folded leaf coral for Rhino 8 / Grasshopper Python 3.

    from cdf import assignment_02_1
    assignment_02_1.geometry(q, r, s, t,
        cache_id=str(ghenv.Component.InstanceGuid))
    ghenv.Component.Hidden = True

Open Brep leaves, not solids. Only q (seed), r (steps), s (first interval
height), and t (curl) are used. All controls accept values from 1 to 10.
"""
import math
import random

ROOT = "CDF_Coral"
PALETTE = {"coral": ("01_Coral", (224, 174, 145), 0.0, 0.0)}


def _control(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Coral controls must be finite numbers.") from exc
    if not math.isfinite(number):
        raise ValueError("Coral controls must be finite numbers.")
    return max(1.0, min(10.0, number))


def growth_layout(seed=1, steps=6, step_height=3.5, curl=4.1):
    """Return deterministic breadth-first section data without importing Rhino.

    Parent indices refer to this list; side identifies the inherited half-profile.
    A single section is the trunk, followed by two children per section.
    """
    seed, steps, height, curl = map(_control, (seed, steps, step_height, curl))
    count = int(math.floor(steps + 0.5))
    rng = random.Random(seed)
    sections = []
    parents = [None]
    bottom = 0.0
    for level in range(count):
        interval = height * 0.7 ** level
        children = []
        for position, parent in enumerate(parents):
            sections.append({
                "parent": parent, "side": position % 2,
                "level": level, "bottom": bottom, "top": bottom + interval,
                "height": interval, "curl": curl / 10.0,
                "angle": rng.uniform(-0.65, 0.65),
                "phase": rng.uniform(-math.pi, math.pi),
                "lean": rng.uniform(-0.25, 0.25),
            })
            children.extend([len(sections) - 1] * 2)
        parents = children
        bottom += interval
    return sections


def _profile(rg, points):
    curve = rg.Curve.CreateInterpolatedCurve(points, 3)
    if curve is None or not curve.IsValid:
        raise RuntimeError("Could not construct a coral spline profile.")
    return curve


def _section(rg, lower, section, tolerance, guide=None):
    """Loft from the exact inherited boundary; keep all profiles horizontal."""
    samples = 32
    domain = lower.Domain
    base = [lower.PointAt(domain.T0 + (domain.T1 - domain.T0) * i / samples)
            for i in range(samples + 1)]
    center = base[samples // 2]
    dx, dy = base[-1].X - base[0].X, base[-1].Y - base[0].Y
    width = math.hypot(dx, dy)
    if width <= tolerance:
        raise RuntimeError("Coral profile is smaller than the document tolerance.")
    ux, uy = dx / width, dy / width
    angle = section["angle"]
    vx = ux * math.cos(angle) - uy * math.sin(angle)
    vy = ux * math.sin(angle) + uy * math.cos(angle)
    height = section["height"]
    level = section["level"]
    # The initial narrow ribbon opens into a fan; children inherit half a fan.
    target_width = height * 2.4 if level == 0 else width * 1.5
    side = -1 if section["side"] == 0 else 1
    spread = 0 if level == 0 else side * height * 0.55
    drift = section["lean"] * height
    for reduction in (1.0, 0.5, 0.0):
        profiles = [lower]
        for row in range(1, 5):
            t = row / 4.0
            blend = t * t * (3 - 2 * t)
            axis = guide.PointAtNormalizedLength(t) if guide is not None else center
            points = []
            for i, start in enumerate(base):
                u = i / samples
                across = (u - 0.5) * target_width
                wave = math.sin(u * math.tau * (1.5 + section["curl"] * 2.5)
                                + section["phase"])
                fold = reduction * section["curl"] * height * 0.48 * wave
                target_x = axis.X + vx * (across + spread) - vy * (fold + drift)
                target_y = axis.Y + vy * (across + spread) + vx * (fold + drift)
                points.append(rg.Point3d(
                    start.X + blend * (target_x - start.X),
                    start.Y + blend * (target_y - start.Y),
                    section["bottom"] + t * height))
            profiles.append(_profile(rg, points))
        breps = rg.Brep.CreateFromLoft(profiles, rg.Point3d.Unset,
                                       rg.Point3d.Unset, rg.LoftType.Normal, False)
        if breps and all(brep is not None and brep.IsValid for brep in breps):
            return list(breps), profiles[-1]
    raise RuntimeError("Could not loft coral section at level {}.".format(level + 1))


def create_geometry(seed=1, steps=6, step_height=3.5, curl=4.1):
    """Build open Breps without modifying the Rhino document.

    The trunk guide starts at the origin; its foot profile is centered there.
    Shared split boundaries connect leaves; no solid union is attempted.
    """
    import Rhino
    import Rhino.Geometry as rg

    layout = growth_layout(seed, steps, step_height, curl)
    doc = Rhino.RhinoDoc.ActiveDoc
    tolerance = doc.ModelAbsoluteTolerance if doc is not None else 0.001
    height = layout[0]["height"]
    guide = _profile(rg, [rg.Point3d(0, 0, 0),
                          rg.Point3d(height * 0.015, 0, height / 3),
                          rg.Point3d(-height * 0.015, 0, height * 2 / 3),
                          rg.Point3d(0, 0, height)])
    foot = guide.PointAtStart
    lower = _profile(rg, [rg.Point3d(foot.X + height * 0.12 * (i / 4 - 0.5),
                                    foot.Y, foot.Z) for i in range(5)])
    tops = []
    shapes = []
    for index, section in enumerate(layout):
        parent = section["parent"]
        if parent is not None:
            boundary = tops[parent]
            middle = (boundary.Domain.T0 + boundary.Domain.T1) / 2
            halves = boundary.Split(middle)
            if halves is None or len(halves) != 2:
                raise RuntimeError("Could not split coral boundary for section {}.".format(index))
            lower = halves[section["side"]]
        breps, upper = _section(rg, lower, section, tolerance,
                                guide=guide if parent is None else None)
        shapes.extend(breps)
        tops.append(upper)
    return {"coral": shapes}


def geometry(q=1, r=6, s=3.5, t=4.1, *, cache_id="assignment02_1", force=False):
    """Synchronize coral Breps to a muted peach Rhino layer; return None."""
    import Rhino
    from . import layer

    groups = create_geometry(q, r, s, t)
    layer.cache_geometry(groups, cache_id, force=force, palette=PALETTE, root=ROOT)
    Rhino.RhinoDoc.ActiveDoc.Views.Redraw()
