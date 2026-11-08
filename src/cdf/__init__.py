"""Parametric reference composition for Rhino 8 / Grasshopper.

    a = cdf.composition(u, v, w, x, y, z,
                        cache_id=str(ghenv.Component.InstanceGuid))

All six inputs range from -10 to 10; six zeros produce the reference layout.
The return value is a flat list of geometry. By default, editable Rhino objects
are also synchronized to material layers. cdf.seed controls stable size factors.
"""

from importlib import reload
from pathlib import Path

from . import tools, assignment_01, viewtools, layer

# Grasshopper often reloads only the top-level package when recomputing.
reload(tools)
reload(layer)
reload(assignment_01)
reload(viewtools)

scale = 1.0
origin = (0.0, 0.0, 0.0)
seed = 100
_last_geometry = ()


def composition(u=0.0, v=0.0, w=0.0, x=0.0, y=0.0, z=0.0, *,
                bake=True, cache_id="default", force=False):
    """Return all geometry and optionally synchronize it to the active Rhino document.

    Each control accepts -10 to 10; six zeros produce the reference layout.
    u: Right wing with 1/3/7 windows per row at -10/0/10; beams extend outward.
    v: Diameters of the shaft, sphere, collars and tip of the left sphere tower.
    w: Sphere-tower height; the sphere, collars and upper cap move with the shaft.
    x: Central facade with 2/5/9 storeys at -10/0/10; shelves, column and roof follow.
    y: Colored boxes and the small yellow foot cylinder; L-shaped joints stay aligned.
    z: Left wing with 1/5/13 fins and half-cylinder factors of 0.6/1.0/1.8
       at -10/0/10; the portal and platform follow the changing width.

    Counts are rounded to grid steps; other dimensions vary continuously, subject
    to clearance limits. v/y use stable per-part factors of about +/-20-35% at
    their endpoints; connected L-shaped parts share a factor and anchor.
    The shaft enclosure starts at Z=26 and ends at the column's rear edge.
    Its blue cap retains full plan coverage when y<0; only its thickness shrinks.
    Roof elements grow away from the enclosure. Right-wing beams retain an outer
    overhang. The blue facade strip and left red portal block end at least one
    unit below their adjacent facades. Horizontal facade/column joints are 0.24
    model units wide. All dimensions are defined before cdf.scale/cdf.origin.
    cdf.seed changes the size factors, not the zero-control layout.
    The camera is not changed. Use a distinct cache_id for each GH component.
    bake=False returns geometry without adding or updating Rhino document objects.
    force=True replaces this cache's objects, discarding their manual edits.
    """
    import Rhino

    doc = Rhino.RhinoDoc.ActiveDoc
    tolerance = doc.ModelAbsoluteTolerance if doc is not None else 0.001
    groups = assignment_01.create_composition(
        scale=scale, origin=origin, u=u, v=v, w=w, x=x, y=y, z=z,
        seed=seed, tolerance=tolerance,
    )
    geometry = [shape for name in tools.COLOR_GROUPS for shape in groups[name]]
    if bake:
        layer.cache_geometry(groups, cache_id, doc, force=force)
    global _last_geometry
    _last_geometry = tuple(geometry)
    return geometry


def getview():
    """Save the active Rhino model viewport to view.json beside this module."""
    return viewtools.getview(Path(__file__).resolve().with_name("view.json"))


def setview():
    """Restore view.json; only a reference-format view follows scale/origin."""
    return viewtools.setview(Path(__file__).resolve().with_name("view.json"), scale, origin)


def caputreview(path: str, transparent_background: bool = False,
                background_color=None, border: int = 0, resolution: float = 300):
    """Export a cropped PNG on every call.

    path is an absolute output folder. transparent_background accepts 1/True for
    transparency or 0/False for an opaque background_color from GH/System.Drawing.
    border adds final-image pixels on each side. resolution sets print metadata
    in dpi (default: 300), not pixel dimensions. The temporary capture disables
    the ground plane and fits the last generated geometry, then restores the view.
    """
    return viewtools.caputreview(
        path, transparent_background, background_color, border, _last_geometry,
        resolution=resolution,
    )
