"""Ansichtssteuerung und PNG-Export für Rhino / Grasshopper."""

def _active_view():
    import Rhino

    doc = Rhino.RhinoDoc.ActiveDoc
    view = None if doc is None else doc.Views.ActiveView
    if view is None or isinstance(view, Rhino.Display.RhinoPageView):
        raise RuntimeError("Bitte eine Rhino-Modellansicht aktivieren.")
    return view


def getview(path):
    """Speichere Kamera, Projektion und Ausschnitt der aktiven Modellansicht.

    Gespeicherte Rhino-Ansichten verwenden absolute Modellkoordinaten.
    Farben und Anzeigemodus werden nicht gespeichert.
    """
    import json
    from pathlib import Path

    import Rhino

    view = _active_view()
    info = Rhino.DocObjects.ViewportInfo(view.ActiveViewport)
    try:
        data = {
            "version": 1,
            "kind": "viewport",
            "viewport": json.loads(info.ToJSON(Rhino.FileIO.SerializationOptions())),
        }
    finally:
        info.Dispose()
    destination = Path(path)
    # Erst vollständig schreiben, dann die bisherige Ansicht atomar ersetzen.
    from tempfile import NamedTemporaryFile
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=str(destination.parent),
                                suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2, allow_nan=False)
            stream.write("\n")
        temporary.replace(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return str(destination)


def setview(path, scale, origin):
    """Lade die gespeicherte Ansicht; die anfängliche Referenz folgt scale/origin.

    Nach getview() werden stattdessen die gespeicherten absoluten Koordinaten
    und der gespeicherte Ausschnitt verwendet, ohne erneutes ZoomExtents.
    """
    import json
    from pathlib import Path

    import Rhino
    import Rhino.Geometry as rg

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version") != 1 or data.get("kind") not in ("reference", "viewport"):
        raise ValueError("Unbekanntes Format in view.json.")
    view = _active_view()
    viewport = view.ActiveViewport
    if data["kind"] == "viewport":
        info = Rhino.Runtime.CommonObject.FromJSON(json.dumps(data["viewport"]))
        if not isinstance(info, Rhino.DocObjects.ViewportInfo):
            if info is not None:
                info.Dispose()
            raise ValueError("view.json enthält keine gültige Rhino-Ansicht.")
        try:
            if not viewport.SetViewProjection(info, True):
                raise RuntimeError("Die gespeicherte Ansicht konnte nicht eingestellt werden.")
        finally:
            info.Dispose()
    else:
        def point(values):
            return rg.Point3d(*(origin[i] + values[i] * scale for i in range(3)))

        target = point(data["target"])
        camera = target + rg.Vector3d(*(v * scale for v in data["camera_offset"]))
        viewport.ChangeToParallelProjection(True)
        viewport.SetCameraLocations(target, camera)
        viewport.CameraUp = rg.Vector3d(*data["up"])
        bounds = rg.BoundingBox(point(data["bounds_min"]), point(data["bounds_max"]))
        if not viewport.ZoomBoundingBox(bounds):
            raise RuntimeError("Die Referenzansicht konnte nicht eingerahmt werden.")
    view.Redraw()
    return True

def caputreview(path: str, transparent_background: bool, background_color,
                border: int, geometry, resolution: float = 300):
    """Exportiere ein PNG mit border freien Pixeln auf jeder Seite.

    path: absoluter Zielordner. Dateiname: ViewCapture_JJMMTT_HHMMSS.png.
    transparent_background: 1/True = transparent, 0/False = deckende Farbe
        aus background_color (System.Drawing.Color oder GH_Colour).
        Der Alphawert der Eingangsfarbe wird für den deckenden Hintergrund ignoriert.
    border: nichtnegative ganze Pixelzahl im fertigen Bild, unabhängig von dpi.
    Zuerst composition() aufrufen und die GH-Vorschau aktualisieren lassen;
    Export am besten in einer separaten GH-Komponente per Button auslösen.
    Andere sichtbare Rhino-/GH-Objekte vorher ausblenden: auch sie würden in
    der Aufnahme erscheinen. Die Bodenebene wird vorübergehend ausgeschaltet.
    Der Ausschnitt umfasst die zuletzt erzeugte Komposition. Blickrichtung und
    Anzeigemodus bleiben erhalten; die Ansicht wird nach dem Export restauriert.
    Die transparente Silhouette wird pixelgenau zugeschnitten, dann border
    ergänzt. Objektinterne Schatten bleiben erhalten, Bodenschatten entfallen.
    Aufnahme mit dreifacher Viewport-Pixelgröße. resolution legt die positive,
    endliche Druckauflösung in dpi fest (Standard: 300); Pixelzahl bleibt gleich.
    Jeder Aufruf exportiert; Auslösung bei Bedarf im GH-Codeblock steuern.
    Existierende Dateinamen werden nicht überschrieben.
    Rückgabe: absoluter Dateipfad.
    """

    from datetime import datetime
    import math
    from pathlib import Path

    if (isinstance(resolution, bool) or not isinstance(resolution, (int, float))
            or not math.isfinite(resolution) or resolution <= 0):
        raise ValueError("resolution muss eine positive, endliche Zahl in dpi sein.")

    import Rhino
    from System.Drawing import Bitmap, Color, Graphics, Rectangle, GraphicsUnit
    from System.Drawing.Imaging import ImageFormat, PixelFormat

    if not isinstance(transparent_background, (bool, int)) or transparent_background not in (0, 1):
        raise ValueError("transparent_background muss 0/False oder 1/True sein.")
    fill_color = Color.Transparent
    if not transparent_background:
        color = getattr(background_color, "Value", background_color)
        if not isinstance(color, Color):
            raise ValueError("background_color muss eine Farbe aus einem GH-Colour-Block sein.")
        fill_color = Color.FromArgb(255, color.R, color.G, color.B)

    if isinstance(border, bool) or not isinstance(border, (int, float)):
        raise ValueError("border muss eine nichtnegative ganze Pixelzahl sein.")
    if not 0 <= border <= 10000 or int(border) != border:
        raise ValueError("border muss eine ganze Pixelzahl zwischen 0 und 10000 sein.")
    border = int(border)
    if not geometry:
        raise RuntimeError("Vor dem Export composition() aufrufen.")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path muss ein absoluter Ordnerpfad sein.")
    folder = Path(path).expanduser()
    if not folder.is_absolute():
        raise ValueError("path muss ein absoluter Ordnerpfad sein.")
    if folder.exists() and not folder.is_dir():
        raise ValueError("path muss einen Ordner bezeichnen, keine Datei.")
    destination = folder / datetime.now().strftime("ViewCapture_%y%m%d_%H%M%S.png")
    if destination.exists():
        raise FileExistsError("Aufnahme existiert bereits; bitte erneut auslösen: "
                              + str(destination))

    doc = Rhino.RhinoDoc.ActiveDoc
    view = None if doc is None else doc.Views.ActiveView
    if view is None or isinstance(view, Rhino.Display.RhinoPageView):
        raise RuntimeError("Bitte eine Rhino-Modellansicht aktivieren.")

    settings = Rhino.Display.ViewCapture()
    settings.Width = max(1, view.ActiveViewport.Size.Width * 3)
    settings.Height = max(1, view.ActiveViewport.Size.Height * 3)
    settings.ScaleScreenItems = True
    settings.DrawAxes = False
    settings.DrawGrid = False
    settings.DrawGridAxes = False
    settings.TransparentBackground = True
    viewport = view.ActiveViewport
    saved_view = Rhino.DocObjects.ViewportInfo(viewport)
    ground = doc.GroundPlane
    saved_ground = ground.Enabled
    bitmap = None
    output = None
    try:
        bounds = Rhino.Geometry.BoundingBox.Empty
        for shape in geometry:
            bounds.Union(shape.GetBoundingBox(True))
        if not bounds.IsValid:
            raise RuntimeError("Die Komposition hat keine gültigen Geometriegrenzen.")
        bounds.Inflate(max(bounds.Diagonal.Length * 0.05, 0.001))
        if not viewport.ZoomBoundingBox(bounds):
            raise RuntimeError("Die Komposition konnte nicht vollständig eingerahmt werden.")
        ground.Enabled = False
        view.Redraw()
        bitmap = settings.CaptureToBitmap(view)
        if bitmap is None:
            raise RuntimeError("Die Rhino-Ansicht konnte nicht aufgenommen werden.")
        left, top, width, height = _capture_bounds(bitmap)
        if (left == 0 or top == 0 or left + width == bitmap.Width
                or top + height == bitmap.Height):
            raise RuntimeError("Geometrie berührt den Aufnahmerand; andere Objekte ausblenden.")
        out_width, out_height = width + 2 * border, height + 2 * border
        if out_width * out_height > 64000000:
            raise ValueError("Bild zu groß (maximal 64 Megapixel); border verkleinern.")
        output = Bitmap(out_width, out_height, PixelFormat.Format32bppArgb)
        output.SetResolution(float(resolution), float(resolution))
        graphics = Graphics.FromImage(output)
        try:
            graphics.Clear(fill_color)
            graphics.DrawImage(bitmap, Rectangle(border, border, width, height),
                               left, top, width, height, GraphicsUnit.Pixel)
        finally:
            graphics.Dispose()
        destination.parent.mkdir(parents=True, exist_ok=True)
        output.Save(str(destination), ImageFormat.Png)
    finally:
        if output is not None:
            output.Dispose()
        if bitmap is not None:
            bitmap.Dispose()
        ground.Enabled = saved_ground
        viewport.SetViewProjection(saved_view, True)
        saved_view.Dispose()
        view.Redraw()
    return str(destination)


def _capture_bounds(bitmap):
    """Grenzen aller nichttransparenten Pixel ohne langsame GetPixel-Aufrufe."""
    from System import Array, Byte, IntPtr
    from System.Drawing import Rectangle
    from System.Drawing.Imaging import ImageLockMode, PixelFormat
    from System.Runtime.InteropServices import Marshal

    width, height = bitmap.Width, bitmap.Height
    data = bitmap.LockBits(Rectangle(0, 0, width, height), ImageLockMode.ReadOnly,
                           PixelFormat.Format32bppArgb)
    left, top, right, bottom = width, height, -1, -1
    try:
        row = Array.CreateInstance(Byte, width * 4)
        for y in range(height):
            Marshal.Copy(IntPtr.Add(data.Scan0, y * data.Stride), row, 0, width * 4)
            alpha = bytes(row)[3::4]
            start = len(alpha) - len(alpha.lstrip(b"\x00"))
            if start == width:
                continue
            end = len(alpha.rstrip(b"\x00")) - 1
            left, right = min(left, start), max(right, end)
            top, bottom = min(top, y), y
    finally:
        bitmap.UnlockBits(data)
    if right < left:
        raise RuntimeError("Keine sichtbare Geometrie aufgenommen; GH-Vorschau prüfen.")
    return left, top, right - left + 1, bottom - top + 1
