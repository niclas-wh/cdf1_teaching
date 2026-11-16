# Computational Design and Fabrication 1 (CDF1)

Beginner-friendly computational design with Python in **Rhino 8 / Grasshopper**.
Use **Python 3 Script** components and add this repository's `src` folder to
Rhino's Python module search paths.

## Assignment 01: Grasshopper blocks

Open [assignment-01.gh](assignments/01/assignment-01.gh). The **geometry** block
creates the architectural composition; the **view** block saves/restores the
camera and exports PNG images. Input and output names are case-sensitive.

### Block: geometry

[assignment_01.composition()](src/cdf/assignment_01.py) creates a composition with
arched facades, a sphere tower, fins and colored volumes. All six sliders accept
**-10 to 10**, with **0** producing the reference layout.

| Input | Effect | Values at -10 / 0 / 10 |
| --- | --- | --- |
| `u` | Right-wing length and window count | 1 / 3 / 7 windows per row |
| `v` | Diameters of the sphere tower's parts | Smaller / reference / larger; approximately Â±20â€“35% per part |
| `w` | Sphere-tower height | Nominal factor 0.6 / 1.0 / 1.4 |
| `x` | Central facade height and storey count | 2 / 5 / 9 storeys |
| `y` | Size of colored boxes and the yellow foot cylinder | Smaller / reference / larger; approximately Â±20â€“35%, subject to connection limits |
| `z` | Left-wing fins and half-cylinders | 1 / 5 / 13 fins; half-cylinder factor 0.6 / 1.0 / 1.8 |

Counts change in discrete steps; other dimensions vary continuously.

| Output | Content |
| --- | --- |
| `a` | One flat list of Breps for further use in GH |
| `out` | Python messages and errors |

```python
from cdf import assignment_01

a = assignment_01.composition(u=u, v=v, w=w, x=x, y=y, z=z)
```

The function also creates editable Rhino objects on five material layers under
`CDF_Composition`: ivory, anthracite, ultramarine, vermilion and yellow. Disable
GH preview for this block and downstream geometry when displaying these Rhino
objects. Use **Rendered** or **Raytraced** for material appearance.

Optional module settings, assigned before the function call:

| Setting | Meaning | Default |
| --- | --- | --- |
| `assignment_01.scale` | Positive global scale factor | `1.0` |
| `assignment_01.origin` | Global translation `(x, y, z)` | `(0.0, 0.0, 0.0)` |
| `assignment_01.seed` | Reproducible size variation for `v` and `y` | `100` |

### Block: view

[viewtools](src/cdf/viewtools.py) provides three commands:

| Function | Action | Return value |
| --- | --- | --- |
| `getview()` | Save the active model viewport's camera, projection and framing to [view.json](src/cdf/view.json) | Saved file path |
| `setview()` | Restore the saved view | `True` on success |
| `caputreview(...)` | Export the current view as a cropped PNG, framed around the last generated composition | PNG file path |

| Input | Type / meaning |
| --- | --- |
| `s_view` | Button: save view |
| `r_view` | Button: restore view |
| `c_path` | Text: absolute export folder, e.g. `C:\Users\your_username\Pictures\CDF` |
| `c_export` | Button: export PNG |
| `c_back` | Boolean: `True` for transparent background, `False` for an opaque background |
| `c_color` | GH color: background color when `c_back=False` |
| `c_res` | Positive number: print resolution in dpi, e.g. `300` |
| `c_border` | Integer: border width in pixels, from `0` to `10000` |

| Output | Content |
| --- | --- |
| `out` | Saved view/PNG file paths, Python messages and errors |

```python
from cdf import viewtools

if s_view:
    print(viewtools.getview())

if r_view:
    viewtools.setview()

if c_export:
    print(viewtools.caputreview(
        c_path=c_path,
        c_back=c_back,
        c_color=c_color,
        c_res=c_res,
        c_border=c_border,
    ))
```

Connect **resolution (dpi)** to `c_res` and **border width (px)** to `c_border`.
Use a Rhino model viewport, not a layout. Export fits the entire visible Rhino
scene with ZoomExtents, independent of Assignment 1 or 2 and of the selection.
Hidden objects and layers remain hidden; GH preview contributes to framing when
its display conduit supplies extents. Let document/preview updates finish before
exporting. No call to `composition()` is required.

PNG files are named `ViewCapture_YYMMDD_HHMMSS.png`; existing files are not
overwritten. Capture uses three times the viewport's pixel dimensions, crops the
visible silhouette and adds `c_border`. `c_res` changes print-resolution metadata,
not pixel dimensions. The original camera and ground-plane state are restored
after export; ground-plane shadows are not captured.

## Assignment 02.1: folded coral

[assignment_02_1.py](src/cdf/assignment_02_1.py) creates a leaf-like coral as
open, folded Breps, growing from a spline guide rooted at `(0, 0, 0)` toward +z.
The narrow foot is centered on the origin. There is no wall thickness or polyp
texture, and the leaves are not closed solids. Strong curling can cause leaves
to overlap; a global self-intersection-free solid is not guaranteed.

Use the existing Python 3 geometry component with item inputs:

```python
from cdf import assignment_02_1
assignment_02_1.geometry(q, r, s, t,
                       cache_id=str(ghenv.Component.InstanceGuid))
ghenv.Component.Hidden = True
```

| Input | Meaning |
| --- | --- |
| `q` | Seed, 1–10; fractional values produce reproducible variations |
| `r` | Steps, 1–10; number of growth intervals, rounded half upward |
| `s` | Step Height, 1–10 model units; first interval height |
| `t` | Curl, 1–10; increasing fold strength and frequency |

Later interval heights are `s * 0.7**i`. The first interval forms the unbranched
trunk and fan; each later interval doubles the number of leaf branches. Steps=10
has 512 leaf ends and 1023 loft sections, so high settings can take longer.
Each child starts on an exact half of its parent's upper profile. As intervals
shrink, folds become more closely spaced in height. Defaults are Seed=1,
Steps=6, Step Height=3.5, Curl=4.1. Finite controls are clamped to 1–10;
non-numeric and non-finite inputs raise an error. Inputs `u` through `p` are
currently unused and must not be passed to this function.

Breps automatically synchronize to `CDF_Coral::01_Coral`, muted peach
RGB `(224, 174, 145)`, using the existing component-owned layer cache. Recomputing
does not accumulate duplicates or replace other components' objects. Pass a
unique `cache_id` per component; `force=True` restores manually deleted cached
objects. `geometry()` returns `None`; `create_geometry()` returns the Brep group
without baking. Use Rendered display to see the layer material.

## Assignment 2: planar pattern tiles

Use a Python 3 Grasshopper component with item inputs `q, r, s, t, u, v, w, x, y, z, p`:

```python
from cdf import assignment_02
assignment_02.geometry(q, r, s, t, u, v, w, x, y, z, p,
                      cache_id=str(ghenv.Component.InstanceGuid))
ghenv.Component.Hidden = True
```

No cache switch or geometry output is needed: curves are always synchronized to
Rhino, without duplicate GH preview. Existing owned pipes are replaced on the
first run. Other components' objects are untouched.

| Input | Meaning |
| --- | --- |
| `q` | Size: 1–20 gives 1×1 to 20×20 tiles |
| `r` | Tile size: 1–10 maps to 5–50 model units |
| `s` | Border print width: input / 10 mm |
| `t` | Pattern print width: input / 10 mm |
| `u` | Curvature: 0–10; zero uses exact quarter circles |
| `v` | Curve seed: 0–10, fractional values supported |
| `w, x, y, z` | Patterns 1–14 for rows 1–4, repeated vertically |
| `p` | Pattern distinction: dark blue/red if true, both black otherwise |
Size and pattern selections round to the nearest integer (halves upward) and
clamp to their ranges. Widths accept **any positive finite number**, including
values below 1 or above 10. Zero/negative widths are rejected. PlotWeight is a
physical print width, not a model-space thickness. PrintDisplay is enabled on
each call. Very thick strokes may visually overlap although centerlines do not.

The square field is centered at the origin; all curves lie at Z=0. Row 1 is at
+Y; words repeat left to right and the final repetition is truncated. B and R
refer only to the two tile orientations, not to display colors:

| Pattern | Repeated word |
| --- | --- |
| 1 | B |
| 2 | R |
| 3 | BR |
| 4 | RB |
| 5 | BBR |
| 6 | RRB |
| 7 | BBRR |
| 8 | RRBB |
| 9 | BBBR |
| 10 | RBBB |
| 11 | BBBRR |
| 12 | RRBBB |
| 13 | BBBRRR |
| 14 | RRRBBB |

Blue connects west–south and north–east; red connects west–north and south–east.
Curves meet at edge midpoints with perpendicular tangents. At zero curvature,
exact quarter circles are used. Positive curvature uses degree-five Bezier
splines with two fixed endpoints and four inner control points. The two tangent
handles lie on the edge normals, independently spaced between one eighth and
one quarter tile width from their edges. The two free points have a minimum
separation of 0.25 + 0.20 × normalized curvature tile widths (0.25–0.45).
Thus their required separation grows with line curve, although individual random
samples need not change monotonically. The entire control polygon must be
non-self-intersecting, including nonadjacent touches/overlaps.
The other two points are sampled inside
the area between the two reference quarter circles: each free point must be
at least half a tile width from both relevant opposite corners. This condition
is checked after curvature blending as well. Points and curves may cross the
tile diagonal. Inflections are allowed again; this rule constrains the free
control points, not the entire curve relative to the reference circles.
Each pair is checked for self-intersections and mutual intersections
(including touches/overlaps). Conflicting deformations are deterministically
reduced; persistent conflicts fall back to the two reference quarter circles.
Convex-hull containment keeps all curves inside their tile.
Curvature blends a circle-like Bezier reference toward the random controls.
Only the zero setting is exactly circular. Curve seed gives reproducible local
randomness. Shared borders are emitted only once.

Three layers are always used: `CDF_Tiles::01_TileBorders` (black),
`CDF_Tiles::02_BlueTiles` and `CDF_Tiles::03_RedTiles`. Pattern distinction toggles
the form layers between black and dark blue (0,0,139) / dark red (139,0,0).
Existing owned curves are migrated on recompute; unrelated objects are untouched.
The shared `layer.cache_geometry` accepts optional `plot_weights` in millimeters
per geometry group. Assignment 1 retains its existing cache behavior.
Width/color changes refresh owned objects; unchanged inputs preserve manual edits.
Use `force=True` to rebuild unchanged owned objects.
Run regression tests with `python -m unittest discover -s tests`.
Actual spline/intersection operations, PrintDisplay and PNG stroke rendering
must additionally be checked inside Rhino 8.

