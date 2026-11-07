"""Referenzkomposition für Rhino 8 / Grasshopper.

    a = cdf.composition(cache_id=str(ghenv.Component.InstanceGuid))

A enthält alle Geometrien. Zusätzlich werden standardmäßig bearbeitbare
Rhino-Objekte mit Material-Layern erzeugt. Die sechs Regler sind reserviert.
"""

from importlib import reload
from pathlib import Path

from . import tools, assignment_01, viewtools, layer

# Grasshopper lädt beim Neuberechnen häufig nur das oberste Paket neu.
reload(tools)
reload(layer)
reload(assignment_01)
reload(viewtools)

scale = 1.0
origin = (0.0, 0.0, 0.0)
seed = 100
_last_geometry = ()


def composition(base_plate_size=0.0, sphere_size=0.0, sphere_position=0.0,
                stair_length=0.0, grid_size=0.0, block_position=0.0, *,
                bake=True, cache_id="default", force=False):
    """Alle Geometrien für A; optional automatisch ins aktive Rhino-Dokument.

    U bis Z bleiben wirkungslos. Pro GH-Komponente eine eigene cache_id nutzen.
    bake=False ist eine reine Vorschau ohne Dokumentänderungen.
    force=True verwirft manuelle Bearbeitungen der eigenen Cache-Objekte.
    """
    import Rhino

    doc = Rhino.RhinoDoc.ActiveDoc
    tolerance = doc.ModelAbsoluteTolerance if doc is not None else 0.001
    groups = assignment_01.create_composition(
        scale, origin, base_plate_size, sphere_size, sphere_position,
        stair_length, grid_size, block_position, seed, tolerance=tolerance,
    )
    geometry = [shape for name in tools.COLOR_GROUPS for shape in groups[name]]
    if bake:
        layer.cache_geometry(groups, cache_id, doc, force=force)
    global _last_geometry
    _last_geometry = tuple(geometry)
    return geometry


def getview():
    """Speichere die aktuelle Rhino-Ansicht in view.json neben diesem Modul."""
    return viewtools.getview(Path(__file__).resolve().with_name("view.json"))


def setview():
    """Stelle die in view.json gespeicherte Rhino-Ansicht ein."""
    return viewtools.setview(Path(__file__).resolve().with_name("view.json"), scale, origin)


def caputreview(path: str, transparent_background: bool = False,
                background_color=None, border: int = 0, resolution: float = 300):
    """Exportiere bei jedem Aufruf: 1 = transparent, 0 = deckende GH-Farbe.

    path ist der Zielordner; border ist der freie Pixelrand auf jeder Seite.
    resolution legt die Druckauflösung in dpi fest (Standard: 300), nicht die Pixelzahl.
    """
    return viewtools.caputreview(
        path, transparent_background, background_color, border, _last_geometry,
        resolution=resolution,
    )
