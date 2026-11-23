"""Sarcophyton grown from spatial spline guides, not a sinusoidal flat disk.

Grasshopper Python 3: geometry(form=..., ...) writes owned objects to Rhino;
create_geometry(...) only returns geometry. form=0: low rosette on an S-shaped
attachment ridge; 5: stout folded coral; 10: tall, nearly round shaft.

width/depth independently scale world X/Y; size controls overall scale.
radius (0..10, default 5) changes crown reach from a fixed neck, not shaft girth;
5 retains the baseline reach. stem (0..10, default 0) adds lower-shaft fullness
without moving its axis or widening the crown. edges blends the rounded, inclined
foot into a broader crown shoulder, without a horizontal flange at the ground.
lobe_density (0..10, default 5) maps to 4..20 primary lobes. lobe_strength
(0..10, default 6) retains the halved angular gain and rounded primary crests.
Primary lobes follow an arc-length reference contour with small seeded spacing
variations, rather than concentrating at particular angles of elongated forms.
z_gravity (-10..10) applies a quadratic vertical displacement across the whole
crown: positive bends down, negative bends up. Downward sag eases near the floor.
growth_shape and saddle_amp retain their formulas. fold_delay and fold_spread
are removed and fixed at their former zero values, as are soften/level/rotate.

Meridian guides bend, fan sideways, develop secondary folds and turn back at
independently curled margins. Successive transverse splines loft the resulting
ruffled sheet. Hyperbolic growth motivates the increasing fold complexity; this
is not an exact constant-curvature embedding. No mesh or external dependencies.
stage=1..9 shows the crown core, crown guides and sections, then stem guides
and sections, followed by the final loft profiles and finished surfaces (default).
Extreme folds can intersect. The basal attachment remains open.
"""
import bisect
import math
import random

ROOT = "CDF_Sarcophyton"
PALETTE = {
    "stalk": ("01_Stalk", (184, 143, 98), 0.0, 0.0),
    "crown": ("02_Crown", (222, 185, 122), 0.0, 0.0),
    "underside": ("03_Underside", (190, 150, 102), 0.0, 0.0),
    "rim": ("04_Rim", (236, 205, 147), 0.0, 0.0),
}
TAU = 2.0 * math.pi


def _color_palette(color):
    if color is None:
        return PALETTE
    # Accept a System.Drawing.Color or a wrapped Grasshopper colour.
    color = getattr(color, "Value", color)
    try:
        base = (int(color.R), int(color.G), int(color.B))
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Connect a Grasshopper Colour Swatch to color.") from exc
    if any(not 0 <= channel <= 255 for channel in base):
        raise ValueError("Color RGB channels must be between 0 and 255.")

    shades = {
        "stalk": tuple(round(channel*.82) for channel in base),
        "crown": base,
        "underside": tuple(round(channel*.86) for channel in base),
        "rim": tuple(round(channel+.30*(255-channel)) for channel in base),
    }
    return {key: (name, shades[key], shine, reflection)
            for key, (name, _, shine, reflection) in PALETTE.items()}


def _control(value, name, low=0.0, high=10.0):
    try:
        value = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(name + " must be a finite number.") from exc
    if not math.isfinite(value):
        raise ValueError(name + " must be a finite number.")
    return max(low, min(high, value))


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _blend(form, low, middle, high):
    if form <= 5.0:
        return low + (middle - low) * _smooth(form / 5.0)
    return middle + (high - middle) * _smooth((form - 5.0) / 5.0)


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _scale(a, factor):
    return tuple(x * factor for x in a)


def _subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _mix(a, b, t):
    return _add(_scale(a, 1-t), _scale(b, t))


def _unit(a):
    length = math.sqrt(_dot(a, a))
    if length < 1e-14:
        raise ValueError("Degenerate surface frame; reduce lobe_strength or curl.")
    return _scale(a, 1.0 / length)


def _periodic(values, parameter):
    index = int(math.floor(parameter))
    t = parameter - index
    p0, p1, p2, p3 = [values[(index+i) % len(values)] for i in (-1, 0, 1, 2)]
    # Periodic cubic B-spline weights keep random bend fields C2 continuous
    # and within their bounds, without overshooting at neighboring lobes.
    return ((1-t)**3*p0 + (3*t**3-6*t*t+4)*p1
            + (-3*t**3+3*t*t+3*t+1)*p2 + t**3*p3)/6.0


def growth_layout(form=5, seed=1, size=30, height=5, width=5, depth=5,
                  bulb=5, lobe_density=5, lobe_strength=6, growth_shape=6,
                  saddle_amp=4, z_gravity=3, tilt=1, curl=6,
                  thickness=4, edges=5, *, radius=5, stem=0):
    """Build a numeric guide net, with no Rhino or document dependencies.

    Controls are 0..10, except seed, size and signed z_gravity (-10..10).
    lobe_density rounds to 4..20 primary lobes with nearly equal contour spacing.
    radius scales the outward guide length by .5+.1*radius (5 is neutral).
    The neck dimensions and tissue thickness remain tied to size, not radius.
    stem=0 retains the shaft outline; increasing stem swells its lower 72%.
    width/depth scale X/Y only after all tissue and support construction.
    growth_shape shapes the hyperbolic bend-growth envelope; saddle_amp controls
    the broad core saddle and angular pitch bias. Their formulas are unchanged.
    fold_delay/fold_spread are fixed at zero, not accepted as input parameters.
    Contour sampling resolves rounded lobes; extra profiles resolve the edges
    transitions. The removed soften/level/rotate controls remain disabled.
    """
    values = locals().copy()
    c = {key: _control(value, key) for key, value in values.items()
         if key not in ("seed", "size", "z_gravity")}
    c["seed"] = _control(seed, "seed", -1000000, 1000000)
    c["size"] = _control(size, "size", .1, 1000000)
    c["z_gravity"] = _control(z_gravity, "z_gravity", -10, 10)
    rng = random.Random(c["seed"])
    c["phases"] = [rng.uniform(-math.pi, math.pi) for _ in range(3)]
    c["lobes"] = int(4 + 1.6*c["lobe_density"] + .5)
    ranges = {"reach": (.82, 1.18), "pitch": (-.35, .35),
              "roll": (-.7, .7), "twist": (-.65, .65),
              "branch": (.28, .55), "curl_start": (.57, .76),
              "curl_gain": (.72, 1.22), "phase": (-.8, .8)}
    c["variations"] = {name: [rng.uniform(*limits) for _ in range(c["lobes"])]
                       for name, limits in ranges.items()}
    c["body_scale"] = c["size"] * _blend(c["form"], 1.15, .88, 1.12)
    c["major"] = c["body_scale"] * _blend(c["form"], .55, .31, .155) * (.85+.03*c["bulb"])
    c["minor"] = c["body_scale"] * _blend(c["form"], .055, .165, .14) * (.85+.03*c["bulb"])
    c["bend"] = c["body_scale"] * _blend(c["form"], .13, .065, .008)
    c["travel"] = c["body_scale"] * _blend(c["form"], .78, .74, 1.02) * (.5+.1*c["radius"])
    c["pitch_bias"] = _blend(c["form"], .42, .18, .12)
    c["crown_z"] = c["body_scale"] * _blend(c["form"], .11, .50, 1.26) * (.55+.09*c["height"])
    c["width_scale"] = .72 + .056*c["width"]
    c["depth_scale"] = .72 + .056*c["depth"]
    c["wall"] = c["body_scale"] * (.003 + .0012*c["thickness"])
    c["samples"] = 48*c["lobes"]
    c["steps"] = 24
    c["neck"] = .24
    c["lean"] = .032*c["tilt"]
    _distribute_guides(c)
    _build_sheet(c)
    return c


def _core_point(c, u, theta):
    x = c["major"]*u*math.cos(theta)
    along = x/c["major"]
    spine = c["bend"]*(math.sin(math.pi*along)+.22*math.sin(TAU*along))
    y = spine + c["minor"]*u*math.sin(theta)*(1+.08*u*math.cos(3*theta+c["phases"][2]))
    z = c["body_scale"] * ((.012+.002*c["growth_shape"])*(1-u*u)
        + (.025+.004*c["saddle_amp"])*u*u*math.sin(2*theta+c["phases"][0]))
    return (x, y, z)


def _core_frame(c, theta):
    point = _core_point(c, 1, theta)
    radial = _unit(_subtract(point, _core_point(c, .999, theta)))
    tangent = _unit(_subtract(_core_point(c, 1, theta+.001),
                              _core_point(c, 1, theta-.001)))
    normal = _unit(_cross(radial, tangent))
    outward = _unit(_cross(tangent, normal))
    return point, radial, outward, normal


def _distribute_guides(c):
    # Measure a gently unfolded crown contour, not the thin neck or curled rim.
    # Equal theta intervals can have very different physical widths on a ridge.
    segments = max(1024, 4*c["samples"])
    reference = []
    for i in range(segments):
        point, radial, outward, _ = _core_frame(c, TAU*i/segments)
        direction = _mix(radial, outward, .84)
        reference.append(_add(point, _scale(direction, .65*c["travel"])))
    lengths = [0.0]
    for a, b in zip(reference, reference[1:]+reference[:1]):
        lengths.append(lengths[-1]+math.hypot(b[0]-a[0], b[1]-a[1]))
    if lengths[-1] <= 0:
        raise ValueError("Degenerate crown contour for primary lobe spacing.")
    c["phase_lengths"] = lengths
    c["angles"] = []
    for i in range(c["samples"]):
        distance = lengths[-1]*i/c["samples"]
        j = min(segments-1, bisect.bisect_right(lengths, distance)-1)
        t = (distance-lengths[j])/(lengths[j+1]-lengths[j])
        c["angles"].append(TAU*(j+t)/segments)
    rng = random.Random("{}:lobe_spacing".format(c["seed"]))
    c["phase_origin"] = rng.uniform(0, 1)
    # Jitter is a small fraction of one lobe, independent of the lobe count.
    c["phase_jitter"] = [rng.uniform(-.07, .07) for _ in range(c["lobes"])]


def _guide_frame(c, theta):
    _, radial, outward, normal = _core_frame(c, theta)
    lengths = c["phase_lengths"]
    a = (theta % TAU)/TAU*(len(lengths)-1)
    i = min(len(lengths)-2, int(math.floor(a)))
    distance = lengths[i]+(a-i)*(lengths[i+1]-lengths[i])
    q = c["lobes"]*distance/lengths[-1]+c["phase_origin"]
    q += _periodic(c["phase_jitter"], q)
    fields = {name: _periodic(values, q) for name, values in c["variations"].items()}
    fields.update(radial=radial, outward=outward, normal=normal, q=q)
    return fields


def _growth_direction(c, guide, s, theta):
    amplitude = c["lobe_strength"]/20.0
    lateral = .35
    k = 1.5+.14*c["growth_shape"]
    growth = (math.sinh(k*s)/math.sinh(k)) ** .55
    q = guide["q"] + (.12+.20*lateral)*guide["twist"]*s*s
    phase = guide["phase"]
    branch = _smooth((s-guide["branch"])/(.90-guide["branch"]))
    tip = _smooth((s-.76)/.24)
    crest = math.cos(TAU*q)
    flanks = (1-crest*crest)**2
    # Broaden the primary crests; higher harmonics fade out there so they
    # cannot sharpen a lobe's summit or turn it into a stack of small corners.
    primary = 1.25*crest-.25*crest**3 + .17*flanks*math.sin(2*TAU*q+phase)
    daughters = flanks*math.cos(2*TAU*q+phase+.9*s)
    wave = 1.55*growth*primary + .72*branch*growth*daughters
    wave += .24*tip*flanks*math.sin(3*TAU*q-phase)
    pitch = growth*(c["pitch_bias"]+guide["pitch"]
        + .016*c["saddle_amp"]*math.sin(2*theta+c["phases"][2])) + amplitude*wave
    curl = _smooth((s-guide["curl_start"])/(1-guide["curl_start"]))
    pitch += math.pi*c["curl"]/10.0*(.9+.7*amplitude)*guide["curl_gain"]*curl
    yaw = amplitude*lateral*(.65*growth*math.sin(TAU*q)
        + .22*branch*math.sin(2*TAU*q+phase)) + .12*guide["twist"]*growth
    roll = amplitude*growth*(guide["roll"]+.42*branch*math.sin(2*TAU*q+phase))
    radial = _unit(_mix(guide["radial"], guide["outward"], _smooth(s/.32)))
    across = _unit(_cross(guide["normal"], radial))
    normal = _unit(_cross(radial, across))
    rolled_across = _add(_scale(across, math.cos(roll)), _scale(normal, math.sin(roll)))
    rolled_normal = _add(_scale(normal, math.cos(roll)), _scale(across, -math.sin(roll)))
    # Integrating a rotating tangent permits vertical walls and true overhangs;
    # adding a height wave to a planar disk cannot produce these return folds.
    return _add(_scale(radial, math.cos(pitch)*math.cos(yaw)),
        _add(_scale(rolled_across, math.cos(pitch)*math.sin(yaw)),
             _scale(rolled_normal, math.sin(pitch))))


def _world(c, point):
    x, y, z = point
    return (x+c["lean"]*c["crown_z"], y, z+c["crown_z"]+c["lean"]*x)


def _apply_gravity(c):
    # Set clearance from the neutral shape, independent of the gravity slider.
    # The same Z shift applies to both skins and their lip; X/Y never change.
    floor = .025*c["body_scale"]
    minimum = min(p[2] for key in ("upper", "lower", "rim") for row in c[key] for p in row)
    lift = max(0.0, floor-minimum)
    c["crown_z"] += lift
    origin = c["grid"][0][0]
    distances = [[(x-origin[0])**2+(y-origin[1])**2 for x, y, _ in row]
                 for row in c["grid"]]
    radius_squared = max(value for row in distances for value in row)
    rim_floor = [min(row[i][2] for row in c["rim"]) for i in range(c["samples"])]
    shifts = []
    for j, row in enumerate(distances):
        row_shifts = []
        for i, distance_squared in enumerate(row):
            # A quadratic field bends the entire crown, including its interior,
            # instead of merely rotating or pulling the final curl rows.
            drop = .65*c["body_scale"]*c["z_gravity"]/10.0*distance_squared/radius_squared
            if drop > 0:
                bottom = min(c["upper"][j][i][2], c["lower"][j][i][2])
                if j == len(distances)-1:
                    bottom = min(bottom, rim_floor[i])
                clearance = max(0.0, bottom+lift-floor)
                drop = clearance*(-math.expm1(-drop/clearance)) if clearance > 0 else 0.0
            row_shifts.append(lift-drop)
        shifts.append(row_shifts)
    for key in ("grid", "upper", "lower"):
        c[key] = [[(x, y, z+dz) for (x, y, z), dz in zip(row, offsets)]
                  for row, offsets in zip(c[key], shifts)]
    c["rim"] = [[(x, y, z+dz) for (x, y, z), dz in zip(row, shifts[-1])]
                for row in c["rim"]]


def _build_sheet(c):
    angles = c["angles"]
    core = (0.0, .05, .14, .29, .48, .72, 1.0)
    growth = [.5*(1-math.cos(math.pi*i/c["steps"])) for i in range(c["steps"]+1)]
    c["neck_index"] = len(core)-1
    c["radii"] = [c["neck"]*u for u in core]
    c["radii"].extend(c["neck"]+(1-c["neck"])*s for s in growth[1:])
    grid = [[_core_point(c, u, theta) for theta in angles] for u in core]
    grid.extend([] for _ in growth[1:])
    for theta in angles:
        guide = _guide_frame(c, theta)
        point = _core_point(c, 1, theta)
        for i in range(1, len(growth)):
            start, end = growth[i-1], growth[i]
            direction = _growth_direction(c, guide, (start+end)/2, theta)
            point = _add(point, _scale(direction, c["travel"]*guide["reach"]*(end-start)))
            grid[c["neck_index"]+i].append(point)
    c["grid"] = [[_world(c, point) for point in row] for row in grid]
    normals, outward = _sheet_frames(c["grid"])
    c["upper"] = [[_add(p, _scale(n, c["wall"]/2)) for p, n in zip(row, field)]
                  for row, field in zip(c["grid"], normals)]
    c["lower"] = [[_add(p, _scale(n, -c["wall"]/2)) for p, n in zip(row, field)]
                  for row, field in zip(c["grid"], normals)]
    c["rim"] = [c["upper"][-1]]
    for i in range(1, 6):
        phi = math.pi*i/6
        c["rim"].append([_add(p, _add(_scale(n, math.cos(phi)*c["wall"]/2),
            _scale(d, math.sin(phi)*c["wall"]/2)))
            for p, n, d in zip(c["grid"][-1], normals[-1], outward)])
    c["rim"].append(c["lower"][-1])
    _apply_gravity(c)
    _support_grid(c, angles, growth)
    # Apply axis scales last, including shoulders, offsets and foot. Neither
    # slider changes Z, the other horizontal axis or the gravity clearance.
    for key in ("grid", "upper", "lower", "rim", "support", "underside_profiles"):
        c[key] = [[(x*c["width_scale"], y*c["depth_scale"], z)
                   for x, y, z in row] for row in c[key]]


def _sheet_frames(grid):
    normals = [[] for _ in grid]
    outward = []
    for j in range(1, len(grid)):
        row = grid[j]
        for i, point in enumerate(row):
            if j == len(grid)-1:
                radial = _unit(_subtract(point, grid[j-1][i]))
            else:
                radial = _unit(_subtract(grid[j+1][i], grid[j-1][i]))
            angular = _unit(_subtract(row[(i+1) % len(row)], row[(i-1) % len(row)]))
            normal = _unit(_cross(radial, angular))
            normals[j].append(normal)
            if j == len(grid)-1:
                outward.append(_unit(_cross(angular, normal)))
    center = _unit(tuple(sum(p[axis] for p in normals[1]) for axis in range(3)))
    normals[0] = [center for _ in grid[0]]
    return normals, outward


def _grid_point(c, grid, r, theta):
    r = max(0.0, min(1.0, r))
    j = max(0, min(len(c["radii"])-2, bisect.bisect_right(c["radii"], r)-1))
    t = (r-c["radii"][j])/(c["radii"][j+1]-c["radii"][j])
    theta %= TAU
    i = max(0, bisect.bisect_right(c["angles"], theta)-1)
    following = (i+1) % c["samples"]
    end = c["angles"][following] if following else TAU
    u = (theta-c["angles"][i])/(end-c["angles"][i])
    return _mix(_mix(grid[j][i], grid[j][following], u),
                _mix(grid[j+1][i], grid[j+1][following], u), t)


def _skin(c, r, theta, side):
    return _grid_point(c, c["upper"] if side > 0 else c["lower"], r, theta)


def _ring(rg, points):
    points = [rg.Point3d(*p) for p in points]
    if len(points) < 4 or any(not point.IsValid for point in points):
        raise ValueError("A Sarcophyton ring needs at least four valid points.")
    # Rhino permits a repeated endpoint for periodic interpolation. Uniform
    # knots preserve the shared reference-contour sampling of adjacent rings.
    if points[-1].DistanceTo(points[0]) != 0.0:
        points.append(points[0])
    failures = []
    for style in (rg.CurveKnotStyle.UniformPeriodic, rg.CurveKnotStyle.ChordPeriodic):
        curve = rg.Curve.CreateInterpolatedCurve(
            points, 3, style, rg.Vector3d.Unset, rg.Vector3d.Unset)
        if curve is None:
            failures.append("{}: no curve returned".format(style))
            continue
        if curve.IsValid and curve.IsClosed and curve.IsPeriodic:
            return curve
        failures.append("{}: valid={}, closed={}, periodic={}".format(
            style, curve.IsValid, curve.IsClosed, curve.IsPeriodic))
        curve.Dispose()
    raise RuntimeError("Could not interpolate a periodic Sarcophyton ring "
                       "({} points). {}".format(len(points)-1, "; ".join(failures)))


def _loft(rg, curves, label, start=None):
    shapes = rg.Brep.CreateFromLoft(curves,
        rg.Point3d.Unset if start is None else rg.Point3d(*start),
        rg.Point3d.Unset, rg.LoftType.Normal, False)
    if not shapes or any(shape is None or not shape.IsValid for shape in shapes):
        raise RuntimeError("Sarcophyton loft failed: " + label)
    return list(shapes)


def _shaft_point(c, t, theta):
    """Unscaled shaft, before its foot and shoulder are replaced by blends."""
    attachment = _skin(c, c["neck"], theta, -1)
    x, y, _ = _core_point(c, 1, theta)
    foot = (x*(1.10+.015*c["bulb"]), y*(1.18+.02*c["bulb"]), 0)
    center = (c["lean"]*c["crown_z"], 0, 0)
    top = _subtract(attachment, center)
    outline = _mix(foot, top, _smooth(t))
    waist = 1-_blend(c["form"], .08, .17, .25)*math.sin(math.pi*t)**2
    fullness = 1+.75*c["stem"]/10.0*(1-_smooth(t/.72))
    # Swell around the existing shaft axis, leaving the neck and shoulder
    # attachment unchanged; stem=0 is exactly the unmodified shaft formula.
    return (outline[0]*waist*fullness+center[0]*t*t,
            outline[1]*waist*fullness, attachment[2]*t)


def _shaft_tangent(c, t, theta):
    lo, hi = max(0.0, t-.0001), min(1.0, t+.0001)
    return _scale(_subtract(_shaft_point(c, hi, theta), _shaft_point(c, lo, theta)),
                  1.0/(hi-lo))


def _transition(start, end, incoming, outgoing, t):
    # Quintic Bezier with zero endpoint curvature, not a circular fillet.
    points = [start, _add(start, incoming), _add(start, _scale(incoming, 2)),
              _subtract(end, _scale(outgoing, 2)), _subtract(end, outgoing), end]
    while len(points) > 1:
        points = [_mix(a, b, t) for a, b in zip(points, points[1:])]
    return points[0]


def _support_grid(c, angles, growth):
    amount = _smooth(c["edges"]/10.0)
    shoulder_r = c["neck"]+(1-c["neck"])*.28*amount
    c["underside_profiles"] = [[_skin(c, shoulder_r+(1-shoulder_r)*s, a, -1)
                                 for a in angles] for s in growth]
    if amount == 0:
        c["support"] = [[_shaft_point(c, i/12.0, a) for a in angles]
                        for i in range(13)]
        return
    foot_samples = (0.0, .15, .35, .60, .82, 1.0)
    shaft_samples, shoulder_samples = 12, 10
    c["support"] = [[] for _ in range(len(foot_samples)+shaft_samples+shoulder_samples)]
    for i, theta in enumerate(angles):
        attachment = _skin(c, c["neck"], theta, -1)
        foot_height = amount*min(.12*attachment[2], .065*c["body_scale"])
        shoulder_height = amount*min(.42*attachment[2], .30*c["body_scale"])
        bottom_t, top_t = foot_height/attachment[2], 1-shoulder_height/attachment[2]
        foot = _shaft_point(c, 0, theta)
        angular = _subtract(_shaft_point(c, 0, theta+.001),
                            _shaft_point(c, 0, theta-.001))
        outward = _unit((angular[1], -angular[0], 0))
        basal_minor = c["minor"]*(1+.75*c["stem"]/10.0)
        foot_width = min(.024*c["body_scale"]*amount, .22*basal_minor*amount, .60*foot_height)
        foot_width *= .94+.06*math.cos(3*theta+c["phases"][0])
        toe = _add(foot, _scale(outward, foot_width))
        bottom = _shaft_point(c, bottom_t, theta)
        # A taller and wider blend rounds the foot more generously, but its
        # initial tangent still rises instead of forming a horizontal flange.
        foot_in = _add(_scale(outward, -.24*foot_width), (0, 0, foot_height/5.0))
        foot_out = _scale(_shaft_tangent(c, bottom_t, theta), bottom_t/5.0)
        points = [_transition(toe, bottom, foot_in, foot_out, t) for t in foot_samples]
        points.extend(_shaft_point(c, bottom_t+(top_t-bottom_t)*j/shaft_samples, theta)
                      for j in range(1, shaft_samples+1))
        top = points[-1]
        target = c["underside_profiles"][0][i]
        direction = _unit(_subtract(_skin(c, shoulder_r+.0001, theta, -1),
                                    _skin(c, shoulder_r-.0001, theta, -1)))
        shoulder_in = _scale(_unit(_shaft_tangent(c, top_t, theta)), .30*shoulder_height)
        chord = _subtract(target, top)
        shoulder_out = _scale(direction, .24*math.sqrt(_dot(chord, chord)))
        points.extend(_transition(top, target, shoulder_in, shoulder_out,
                                  j/float(shoulder_samples))
                      for j in range(1, shoulder_samples+1))
        for row, point in zip(c["support"], points):
            row.append(point)


def _stage_number(value):
    message = "stage must be an integer from 1 to 9."
    if isinstance(value, bool):
        raise ValueError(message)
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(message) from exc
    if number not in range(1, 10):
        raise ValueError(message)
    return int(number)


def _growth_guides(rg, rows, count):
    curves = []
    for j in range(count):
        column = j*len(rows[0])//count
        points = [rg.Point3d(*row[column]) for row in rows]
        curve = rg.Curve.CreateInterpolatedCurve(points, 3, rg.CurveKnotStyle.Chord)
        if curve is None or not curve.IsValid:
            raise RuntimeError("Could not interpolate a Sarcophyton growth guide.")
        curves.append(curve)
    return curves


def _construction_curves(rg, c, stage, groups):
    grid = c["grid"]
    neck = c["neck_index"]
    crown_rows = grid[1:neck+1] if stage <= 2 else grid[1:]
    groups["crown"] = [_ring(rg, row) for row in crown_rows]
    if stage in (2, 3):
        groups["crown"].extend(_growth_guides(rg, grid[neck:], 2*c["lobes"]))
    if stage in (5, 6):
        groups["stalk"].extend(_growth_guides(rg, c["support"], 8))
    if stage in (6, 7):
        groups["stalk"].extend(_ring(rg, row) for row in c["support"])


def create_geometry(form=5, seed=1, size=30, height=5, width=5, depth=5,
                    bulb=5, lobe_density=5, lobe_strength=6, growth_shape=6,
                    saddle_amp=4, z_gravity=3, tilt=1, curl=6,
                    thickness=4, edges=5, stage=9, *, radius=5, stem=0):
    """Return one construction stage from the same guide net.

    1: crown core rings; 2: core rings and crown guides; 3: crown guides
    and full crown mid-surface sections; 4: crown sections only.
    5–7 retain the crown sections and add, respectively, stem guides,
    stem guides and sections, and stem sections only.
    8: exact loft profiles (shared rings once); 9: surface lofts only.
    The lower loft spans the foot to the crown rim.
    The basal foot stays open; extreme parameters can cause self-intersections.
    """
    stage = _stage_number(stage)
    c = growth_layout(form=form, seed=seed, size=size, height=height,
        width=width, depth=depth, bulb=bulb, lobe_density=lobe_density,
        lobe_strength=lobe_strength, growth_shape=growth_shape,
        saddle_amp=saddle_amp, z_gravity=z_gravity,
        tilt=tilt, curl=curl, thickness=thickness, edges=edges, radius=radius, stem=stem)
    import Rhino.Geometry as rg

    groups = {key: [] for key in PALETTE}
    if stage <= 7:
        _construction_curves(rg, c, stage, groups)
        return groups

    upper = [_ring(rg, row) for row in c["upper"][1:]]
    lower = [_ring(rg, row) for row in c["underside_profiles"]]
    stalk = [_ring(rg, row) for row in c["support"][:-1]] + [lower[0]]
    lip = [upper[-1]]+[_ring(rg, row) for row in c["rim"][1:-1]]+[lower[-1]]
    if stage == 8:
        groups.update(stalk=stalk[:-1], crown=upper, underside=lower, rim=lip[1:-1])
        return groups
    # Isolate the central pole so it cannot flatten the many outer return folds.
    groups["crown"] = _loft(rg, upper[:2], "central crown", start=c["upper"][0][0])
    groups["crown"].extend(_loft(rg, upper[1:], "folded crown"))
    groups["stalk"] = _loft(rg, stalk+lower[1:], "foot, shaft, shoulder and underside")
    groups["rim"] = _loft(rg, lip, "rolled rim")
    return groups


def geometry(form=5, seed=1, size=30, height=5, width=5, depth=5,
             bulb=5, lobe_density=5, lobe_strength=6, growth_shape=6,
             saddle_amp=4, z_gravity=3, tilt=1, curl=6,
             thickness=4, edges=5, stage=9, *, radius=5, stem=0,
             cache_id="assignment02_1_2", force=False, color=None):
    """GH entry point: synchronize owned Rhino objects and return preview groups.

    Use named arguments and cache_id=str(ghenv.Component.InstanceGuid).
    Connect a Colour Swatch to color (item access, Colour type hint). The crown
    uses its RGB value; the other layers use lighter or darker shades. Alpha
    is ignored. If color is omitted, the original palette remains in use.
    Remove fold_delay/fold_spread from the GH call; both are now fixed at zero,
    as are the previously removed soften/level/rotate controls.
    Add radius (0..10, default 5) and stem (0..10, default 0) as keyword inputs.
    radius changes crown reach, not the neck/shaft dimensions or tissue thickness.
    stem increases lower-shaft fullness around its existing axis, fading to zero
    before the neck. At 0 its gain is exactly one. size still scales everything.
    edges (0..10) controls the enlarged foot rounding and broader upper shoulders.
    lobe_strength uses the halved angular gain, with rounded primary crests
    and smoother random bend fields. lobe_density maps 0..10 to 4..20 primary
    lobes with bounded, seeded spacing variation along the reference contour. curl
    controls return folds; z_gravity (-10..10) bends the crown in world Z,
    downward for positive values, upward for negative values. Only downward
    motion is limited softly by ground clearance. No collision-free guarantee.
    width/depth independently scale world X/Y, with 5 neutral for both.
    Use an integer GH slider stage=1..9 (default 9). Stages 1..8 show only
    construction curves; stage 9 lofts the profiles from stage 8 into surfaces.
    This module never overwrites the other coral's layers or cached objects.
    """
    import Rhino
    from . import layer

    doc = Rhino.RhinoDoc.ActiveDoc
    if doc is None:
        raise RuntimeError("An active Rhino document is required.")
    palette = _color_palette(color)
    groups = create_geometry(form=form, seed=seed, size=size, height=height,
        width=width, depth=depth, bulb=bulb, lobe_density=lobe_density,
        lobe_strength=lobe_strength, growth_shape=growth_shape,
        saddle_amp=saddle_amp, z_gravity=z_gravity,
        tilt=tilt, curl=curl, thickness=thickness, edges=edges,
        stage=stage, radius=radius, stem=stem)
    layer.ensure_layers(palette=palette, root=ROOT)
    layer.cache_geometry(groups, cache_id, force=force, palette=palette, root=ROOT)
    doc.Views.Redraw()
    return groups
