"""Bildkomposition für Rhino 8 / Grasshopper, nach Farben gruppiert.

Alle Ausgaben enthalten ausschließlich Geometrie, keine Farben oder Materialien:
    a: weiß
    b: schwarz
    c: blau
    d: rot
    e: gelb

Grasshopper: a, b, c, d, e = cdf.composition(...).
Die sechs optionalen Regler liegen zwischen -10 und 10; 0 ist der Originalzustand.
Die Farbzuweisung erfolgt ausschließlich durch den Benutzer in Grasshopper.
Bereits manuell gebakte Altobjekte werden nicht automatisch gelöscht.
"""

from importlib import reload
from pathlib import Path

from . import tools, assignment_01, viewtools

# Grasshopper lädt beim Neuberechnen häufig nur das oberste Paket neu.
reload(tools)
reload(assignment_01)
reload(viewtools)

scale = 1.0
origin = (0.0, 0.0, 0.0)
seed = 100
_last_geometry = ()


def composition(base_plate_size=0.0, sphere_size=0.0, sphere_position=0.0,
                stair_length=0.0, grid_size=0.0, block_position=0.0):

    groups = assignment_01.create_composition(
        scale, origin, base_plate_size, sphere_size, sphere_position,
        stair_length, grid_size, block_position, seed,
    )
    global _last_geometry
    _last_geometry = tuple(shape for group in groups.values() for shape in group)
    return tuple(groups[name] for name in tools.COLOR_GROUPS)


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
