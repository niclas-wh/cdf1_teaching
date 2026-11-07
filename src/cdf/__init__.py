"""Parametrische Referenzkomposition für Rhino 8 / Grasshopper.

    a = cdf.composition(u, v, w, x, y, z,
                        cache_id=str(ghenv.Component.InstanceGuid))

Alle Eingänge liegen zwischen -10 und 10; sechs Nullen ergeben die Referenz.
A enthält alle Geometrien. Zusätzlich werden standardmäßig bearbeitbare
Rhino-Objekte mit Material-Layern erzeugt. cdf.seed bestimmt stabile Zufallsfaktoren.
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


def composition(u=0.0, v=0.0, w=0.0, x=0.0, y=0.0, z=0.0, *,
                bake=True, cache_id="default", force=False):
    """Alle Geometrien für A; optional automatisch ins aktive Rhino-Dokument.

    Jeder Regler akzeptiert -10 bis 10; 0 behält den Referenzstand bei.
    u: Rechtsflügel mit 1/3/7 Fenstern bei -10/0/10; Balken wachsen nur nach rechts.
    v: Durchmesser von Schaft, Kugel und Ringen des linken Kugelturms.
    w: Kugelturmhöhe, mitwandernde Kugel, Ringe und Turmabschluss.
    x: Mittlerer Aufbau mit 2/5/9 Geschossen bei -10/0/10; Dach wandert mit.
    y: Farbige Quader und kleiner gelber Fußzylinder, L-Verbindungen bleiben bündig.
    z: Linker Flügel mit 1/5/13 Lamellen bei -10/0/10 und mitwachsender Grundplatte.
       Halbzylinderfaktor 0.6/1.0/1.8; positiver Bereich doppelt so stark wie bisher.

    Rasteranzahlen werden gerundet; übrige Maße verändern sich stetig.
    v/y nutzen feste Faktoren von etwa ±20–35 %; verbundene L-Teile gemeinsam.
    Schacht: Unterkante Z=26, Rückkante bündig mit der Zylinderhinterkante.
    Die blaue Abdeckung behält bei y<0 ihre Mindestgrundfläche; nur ihre Dicke
    schrumpft weiter. Dachaufbauten bleiben hinter den Schachtwänden.
    Rechte Balken behalten einen äußeren Überstand. Der blaue Fassadenstreifen
    und der linke rote Block bleiben mindestens eine Einheit unter ihrer grauen
    Nachbarfassade. Horizontale Fugen an Fensterfassaden und Säule: 0.24 Einheiten.
    cdf.seed ändert die Faktoren, nicht den Nullstand. Kamera bleibt unverändert.
    Pro GH-Komponente eine eigene cache_id nutzen.
    bake=False ist eine reine Vorschau ohne Dokumentänderungen.
    force=True verwirft manuelle Bearbeitungen der eigenen Cache-Objekte.
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
