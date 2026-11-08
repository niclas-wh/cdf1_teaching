"""Model-viewport persistence and cropped PNG export for Rhino / Grasshopper."""

def _active_view():
    import Rhino

    doc = Rhino.RhinoDoc.ActiveDoc
    view = None if doc is None else doc.Views.ActiveView
    if view is None or isinstance(view, Rhino.Display.RhinoPageView):
        raise RuntimeError("Activate a Rhino model viewport, not a layout page.")
    return view


def getview(path):
    """Save the active model viewport's camera, projection and framing to JSON.

    Saved viewports use absolute model coordinates, not coordinates relative to
    scale/origin. Colors and the display mode are not saved. Return the file path.
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
    # Finish writing the new view before atomically replacing the previous file.
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
    """Restore a saved viewport, or fit a reference-format view to scale/origin.

    A viewport written by getview() restores its absolute camera and framing
    without another zoom-to-extents. A reference-format file instead transforms
    its stored target, offset and bounds using scale/origin and fits those bounds.
    """
    import json
    from pathlib import Path

    import Rhino
    import Rhino.Geometry as rg

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version") != 1 or data.get("kind") not in ("reference", "viewport"):
        raise ValueError("Unsupported view JSON version or kind.")
    view = _active_view()
    viewport = view.ActiveViewport
    if data["kind"] == "viewport":
        info = Rhino.Runtime.CommonObject.FromJSON(json.dumps(data["viewport"]))
        if not isinstance(info, Rhino.DocObjects.ViewportInfo):
            if info is not None:
                info.Dispose()
            raise ValueError("The view JSON does not contain a valid Rhino viewport.")
        try:
            if not viewport.SetViewProjection(info, True):
                raise RuntimeError("Could not restore the saved viewport.")
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
            raise RuntimeError("Could not fit the reference view to its bounds.")
    view.Redraw()
    return True

def caputreview(path: str, transparent_background: bool, background_color,
                border: int, geometry, resolution: float = 300):
    """Export a tightly cropped PNG with a pixel border on every side.

    path: absolute output folder. Filename: ViewCapture_YYMMDD_HHMMSS.png.
    transparent_background: 1/True keeps transparency; 0/False fills an opaque
        background_color (System.Drawing.Color or a wrapped GH color).
        The supplied color's alpha is ignored for an opaque background.
    border: whole pixels from 0 to 10000 in the final image, independent of dpi.
    Run composition() and let its document objects/GH preview update first;
    preferably trigger export with a button in a separate GH component.
    Hide unrelated visible Rhino/GH objects: they would also appear in the image.
    The ground plane is temporarily disabled, so its shadows are not captured.
    Framing uses the supplied geometry, which the public wrapper takes from the
    last composition() call. View direction and display mode are retained; the
    original viewport and ground-plane state are restored after capture.
    The alpha silhouette is cropped to visible pixels, then border is added.
    Capture uses three times the viewport's width and height. resolution sets
    positive, finite print-resolution metadata in dpi (default: 300), not pixels.
    Cropping and border determine the final dimensions, limited to 64 megapixels.
    Every call exports; gate calls in GH if needed. Existing files are not replaced.
    Return the absolute output file path.
    """

    from datetime import datetime
    import math
    from pathlib import Path

    if (isinstance(resolution, bool) or not isinstance(resolution, (int, float))
            or not math.isfinite(resolution) or resolution <= 0):
        raise ValueError("resolution must be a positive, finite number in dpi.")

    import Rhino
    from System.Drawing import Bitmap, Color, Graphics, Rectangle, GraphicsUnit
    from System.Drawing.Imaging import ImageFormat, PixelFormat

    if not isinstance(transparent_background, (bool, int)) or transparent_background not in (0, 1):
        raise ValueError("transparent_background must be 0/False or 1/True.")
    fill_color = Color.Transparent
    if not transparent_background:
        color = getattr(background_color, "Value", background_color)
        if not isinstance(color, Color):
            raise ValueError("background_color must be a System.Drawing.Color or a wrapped GH color.")
        fill_color = Color.FromArgb(255, color.R, color.G, color.B)

    if isinstance(border, bool) or not isinstance(border, (int, float)):
        raise ValueError("border must be a nonnegative whole number of pixels.")
    if not 0 <= border <= 10000 or int(border) != border:
        raise ValueError("border must be a whole number of pixels between 0 and 10000.")
    border = int(border)
    if not geometry:
        raise RuntimeError("Call composition() before exporting.")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be an absolute folder path.")
    folder = Path(path).expanduser()
    if not folder.is_absolute():
        raise ValueError("path must be an absolute folder path.")
    if folder.exists() and not folder.is_dir():
        raise ValueError("path must refer to a folder, not a file.")
    destination = folder / datetime.now().strftime("ViewCapture_%y%m%d_%H%M%S.png")
    if destination.exists():
        raise FileExistsError("The capture already exists; trigger export again: "
                              + str(destination))

    doc = Rhino.RhinoDoc.ActiveDoc
    view = None if doc is None else doc.Views.ActiveView
    if view is None or isinstance(view, Rhino.Display.RhinoPageView):
        raise RuntimeError("Activate a Rhino model viewport, not a layout page.")

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
            raise RuntimeError("The composition has no valid geometry bounds.")
        bounds.Inflate(max(bounds.Diagonal.Length * 0.05, 0.001))
        if not viewport.ZoomBoundingBox(bounds):
            raise RuntimeError("Could not fit the entire composition in the viewport.")
        ground.Enabled = False
        view.Redraw()
        bitmap = settings.CaptureToBitmap(view)
        if bitmap is None:
            raise RuntimeError("Could not capture the Rhino viewport.")
        left, top, width, height = _capture_bounds(bitmap)
        if (left == 0 or top == 0 or left + width == bitmap.Width
                or top + height == bitmap.Height):
            raise RuntimeError("Geometry touches the capture border; hide unrelated objects.")
        out_width, out_height = width + 2 * border, height + 2 * border
        if out_width * out_height > 64000000:
            raise ValueError("Image exceeds the 64-megapixel limit; reduce border or viewport size.")
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
    """Return nontransparent pixel bounds without slow per-pixel GetPixel calls."""
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
        raise RuntimeError("No visible geometry captured; check Rhino object visibility and GH preview.")
    return left, top, right - left + 1, bottom - top + 1
