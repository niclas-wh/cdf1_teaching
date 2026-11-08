# Computational Design and Fabrication 1 (CDF1)

## Welcome

Welcome to **Computational Design and Fabrication**, a platform dedicated to beginner-friendly creative coding tutorials and exercises for computational design and fabrication in architecture.


<!-- ## Session Blocks 

Title | Description | Slides | Session material | Assignment 
----- | ----------- | ------ | ---------------- | ---------- -->
<!-- **01a Python Basics** | Quick start on Python | [Python Basics](https://github.com/computationaldesignandfabrication/cdf1_teaching/blob/main/sessions-slides/Session%2001%20Python%20Basics.pdf) | [Session 01a](https://classroom.github.com/a/0gVDlBH0) |[Assignment 01a](https://classroom.github.com/a/gEZq-xda)
**01b Rhino Basics** | Quick start on Rhino | [Rhino Basics](https://github.com/computationaldesignandfabrication/cdf1_teaching/blob/main/sessions-slides/Session%2001%20Rhino%20Basics.pdf) |  |
**02 Geometry 2D** | 2D geometry  | [Geometry 2D](https://github.com/computationaldesignandfabrication/cdf1_teaching/blob/main/sessions-slides/Session%2002%20Geometry%202D.pdf) | [Session 02](https://classroom.github.com/a/tBISN_ul) | [Assignment 02](https://classroom.github.com/a/FkT2TYiD)
**03 Basic Geometry 3D** | 3D primitive geometry  | [Geometry 3D](https://github.com/computationaldesignandfabrication/cdf1_teaching/blob/main/sessions-slides/Session%2003%20Basic%20Geometry%203D.pdf) | [Session 03](https://classroom.github.com/a/331M5qJj) | [Assignment 03](https://classroom.github.com/a/piywCTG7)
**04 Meshses** | Meshes and mesh operations | [Meshes](https://github.com/computationaldesignandfabrication/cdf1_teaching/blob/main/sessions-slides/Session%2004%20Meshes.pdf) |  [Session 04](https://classroom.github.com/assignment-invitations/380e9596c1d28ade12d9917156004a25/status) | [Assignment 04](https://classroom.github.com/assignment-invitations/6641726eccea3b9db9017547b04649f2/status)
**05 Integrated Representations** | Integrated design and fabrication representations | [Integrated Representation](https://github.com/computationaldesignandfabrication/cdf1_teaching/blob/main/sessions-slides/Session%2005%20Integrated%20Representations.pdf) | [Session 05](https://classroom.github.com/a/J5fiLqqq) |
**06 Design Algorithms** | Generative methods for creating form and structure | [Design Algorithms](https://github.com/computationaldesignandfabrication/cdf1_teaching/blob/main/sessions-slides/Session%2006%20Design%20Algorithms.pdf) | [Session 06](https://classroom.github.com/a/5SiJajj8) |
**07 Structural Form Finding** | Geometric form finding for compression-only structures | [Structural Form Finding]() | [Session 07]() | -->


## Requirements

* Rhino 8 / Grasshopper
* [Github Desktop](https://desktop.github.com/)
* [Visual Studio Code](https://code.visualstudio.com/)

## Installation

### Cloning the CDF Repository to your workstation

1. Create a **workspace** folder in File Explorer:

    `C:\Users\your_username\workspace`

2. Open **GitHub Desktop** and click **Current Repository** (top left), then **Add > Clone Repository...**.

3. Select the **URL** tab and paste:

    `https://github.com/computationaldesignandfabrication/cdf1_teaching.git`

4. Set the **Local Path** (bottom) so it looks like:

    `C:\Users\your_username\workspace\cdf1_teaching`

5. Click **Clone**.

### Setting up your GitHub Copilot account

1. Create a free [GitHub account](https://github.com/signup) if you do not have one yet.

2. As a TUM student, you are eligible for free **GitHub Pro** and **GitHub Copilot Pro**. Request them by following the [TUM GitHub guide](https://collab.dvb.bayern/spaces/TUMsoftware/pages/2662964764/GitHub) (TUM login required).

### Setting up VS Code and extensions

1. Install the extensions. Open the Extensions panel (`Ctrl+Shift+X`), search for each one and click **Install**:
    * **Python** (by Microsoft): syntax highlighting and code help for Python files.
    * **GitHub Copilot** (by GitHub): the AI assistant. This also installs **GitHub Copilot Chat**.

2. Log in to your Copilot account:
    * Click the Copilot icon in the VS Code status bar (bottom right) or the account icon (bottom left) and choose **Sign in with GitHub**.
    * Sign in with your GitHub account in the browser and authorize VS Code.

3. Check that it works: open the Copilot Chat panel (`Ctrl+Alt+I`) and send a short message. If you get an answer, you are ready.

### Setting up Rhino/Grasshopper

This tells Rhino's Python where to find the CDF code, so you can `import` it in Grasshopper.

1. Open **Rhino 8** and start **Grasshopper** (type `Grasshopper` in the Rhino command line).

2. Add a **Python 3 Script** component to the canvas. The first time, wait for it to finish loading.

3. Double-click the component to open the script editor.

4. In the editor's top bar, go to **Tools > Options**.

5. Open the **Python 3** tab.

6. Under **Module search paths**, click **+** and add the path to the `src` folder of your cloned repository:

    `C:\Users\your_username\workspace\cdf1_teaching\src`

7. Click **Save**.

8. Check that it works: in the component, run `import cdf` (or one of the CDF modules). If there is no error, the path is set up correctly.


**Done! Now you can go to VS Code, Rhino, or Grasshopper to run the example files of CDF.**

---

# Assignment 01

## Parametric composition: Rhino layers and editable geometry

The [composition generator](src/cdf/assignment_01.py) approximates an architectural
reference using arched facades, circular recesses, fins, a sphere tower and primary
colors. It is not a dimensionally accurate reconstruction; hidden backs are inferred.

Z points up. The central facade faces **-Y**. The right wing is rotated **+90 degrees**
around `(28, -3)` and then offset as an assembly, so its windows face **+X** and its
length extends along **+Y**. Its horizontal fins sit on the short end face. To see
both facades, view the composition from the **positive-X/negative-Y side**.
`composition()` does not change the camera. `cdf.scale` and `cdf.origin` apply global
scale and translation after the local rotations and assembly offsets.

### Controls

[composition()](src/cdf/__init__.py) accepts six controls in the inclusive range
**-10 to 10**. Six zeros produce the current reference layout. Nonfinite or
out-of-range values raise an error.

| Control | Effect | Values at -10 / 0 / 10 |
| --- | --- | --- |
| `u` | Right-wing length, both window rows, backing, beams and tapered roof ribs | 1 / 3 / 7 windows per row |
| `v` | Different diameter factors for the left sphere tower's shaft, sphere, collars and red tip | Approximately -20-35% / unchanged / +20-35% per part |
| `w` | Sphere-tower height; sphere, collars and top cap move with the shaft | Nominal height factor 0.6 / 1.0 / 1.4 |
| `x` | Central facade height, shelf count, black enclosure, segmented column and roof elements | 2 / 5 / 9 storeys |
| `y` | Colored boxes and the small yellow foot cylinder; connected blue L-shaped parts share their transform | Approximately -20-35% / unchanged / +20-35%, subject to connection limits |
| `z` | Left-wing fins, portal, half-cylinders, chimney and growing black platform | 1 / 5 / 13 fins; half-cylinder factor 0.6 / 1.0 / 1.8 |

Window, storey and fin counts change in rounded grid steps, not continuously.
Half steps round away from the reference count. Each sign uses its own range
between zero and its endpoint. The central storey pitch stays at 9 model units;
the right-wing rectangular and arched windows retain pitches of 10.5 and 10 units.
Other dimensions vary continuously, with clearance and connection limits applied.

The size factors for `v` and `y` are reproducible for each part key and `cdf.seed`
(default: `100`), independent of the current window/storey counts. Changing the
seed does not change the zero-control layout. Only the left sphere tower responds
to `v` and `w`; the central light-colored column responds to `x` instead.

The generator maintains these connections:

- Right-wing beams keep their inner ends fixed. `u` changes only their length
  outward; `y` changes their cross-section and outer overhang.
- Connected blue L-shaped parts use a shared factor and anchor. The blue facade
  strip and left red portal block end at least 1 unit below their adjacent facades.
- The shaft enclosure starts at the central facade's underside, `Z=26`, and ends
  at the central column's rear edge. Its blue cap always covers the full footprint,
  even when `y` is negative; thickness can still shrink.
- Roof blocks grow away from the shaft. The red eye block is 26 units high at
  zero controls, with its opening center 17 units above its base.
- Right-window outer chamfers reach the facade plane; their straight outer sections
  are embedded in the wall. The left portal has a fixed 2-unit width allowance.
- Horizontal joints in both stacked window facades and the segmented column are
  0.24 units wide. All listed dimensions are before global scaling/translation.

### Grasshopper integration

Use Python 3 in Rhino 8. Update the embedded code in
[assignment-01.gh](assignments/assignment-01.gh) in the Grasshopper script editor;
the Python package does not rewrite the GH file.

1. Keep the existing AutoReloader, path monitoring and view/capture buttons.
2. Connect six sliders with a range of -10 to 10 and a default of 0. After importing
   or reloading `cdf`, forward the inputs to the composition call. For inputs named
   `U` through `Z`, use:

   ```python
   a = cdf.composition(
       u=U, v=V, w=W, x=X, y=Y, z=Z,
       cache_id=str(ghenv.Component.InstanceGuid),
   )
   ```

   If the component inputs use lowercase names, use those names on the right-hand
   side instead. Match `a` to the actual output name, such as `A` if capitalized.
   The return value is **one flat list of Breps**, not five separate color outputs.
3. With the default `bake=True`, **disable preview** for this Python component and
   downstream preview components. Otherwise GH preview may cover the cached Rhino
   objects' material colors. The geometry output remains available for further use.
4. Recompute. Editable objects are synchronized into five material layers under
   `CDF_Composition`; no separate Bake or Content Cache component is required.
5. Use **Rendered** or **Raytraced** for material appearance. Shaded uses layer
   colors but does not produce the same lighting/material response. Choose a view
   from the positive-X/negative-Y side and save it with `cdf.getview()` when ready.

### Layers and materials

The [layer manager](src/cdf/layer.py) assigns both object color and render material
**by layer**, using these labels and RGB values:

| Layer under `CDF_Composition` | RGB |
| --- | --- |
| `01_Ivory` | `(226, 212, 192)` |
| `02_Anthracite` | `(37, 38, 36)` |
| `03_Ultramarine` | `(6, 38, 145)` |
| `04_Vermilion` | `(228, 12, 18)` |
| `05_SunYellow` | `(255, 190, 5)` |

Render-material names use the root and child label, for example
`CDF_Composition_03_Ultramarine`. Blue, red and yellow have zero shine and
reflectivity, with a black specular color. Ivory and anthracite retain their
configured low shine/reflectivity. Document-controlled layer properties apply
immediately; material changes are committed through the material table.

On updating an older document, the layer manager can identify an existing
composition root through cache-owned objects and reuse uniquely numbered child
layers. These layers and their matching CDF materials are renamed in place rather
than creating a second layer tree. Ambiguous candidates raise an error instead of
renaming an arbitrary tree. Unrelated layers are not renamed.

**The English labels change the palette fingerprint. The next recompute refreshes
owned geometry, so preserve any manual variants before recomputing.** Ownership
and cache metadata keys remain unchanged.

### Cache behavior and limitations

- Cache state belongs to the active **Rhino document**, not the Grasshopper document.
  The returned geometry list alone carries no Rhino layer/material attributes.
- Identical generated geometry and palette inputs do not create duplicates, even
  after module reload. Manual object edits, layer changes and deletions remain
  while those inputs stay unchanged.
- The returned geometry is always the generated geometry, not manually edited
  cache objects. PNG framing also uses the last generated geometry's bounds.
- Changes to generated geometry, global scale/origin or the palette replace only
  objects marked with the same `cache_id`; their manual edits are lost. To preserve
  a variant, copy its objects and remove the `cdf.composition.owner` user text from
  the copies before recomputing. Unmarked objects are never automatically deleted.
- `force=True` explicitly replaces the cache even when inputs have not changed,
  including after manual deletion. Remove it after the reset. Locked/reference
  cache objects prevent replacement and raise an error.
- Use a distinct `cache_id` per GH component, for example its `InstanceGuid`.
  Omitting it uses `default`, so multiple callers would share the same cache.
- Save the Rhino document as `.3dm` to retain objects, layers, materials and cache
  state. Removing the GH component does not remove cached Rhino objects.
- `bake=False` returns geometry without adding/updating document objects; existing
  cached objects remain. Enable GH preview separately if a preview-only workflow
  is desired; the output list itself does not contain layer/material attributes.

### Saved views and PNG export

[viewtools.py](src/cdf/viewtools.py) provides the existing public view helpers:

- `cdf.getview()` saves the active model viewport's camera, projection and framing
  to [view.json](src/cdf/view.json), replacing the file atomically. Saved viewports
  use absolute model coordinates, not coordinates relative to `scale`/`origin`.
  Colors and display mode are not saved.
- `cdf.setview()` restores that saved viewport without another zoom-to-extents.
  It also supports a reference-format JSON file, whose camera/bounds are transformed
  by `scale`/`origin`. Layout pages are not supported by these helpers.
- `cdf.caputreview(...)` exports on every call. The historical function spelling
  is retained for compatibility. Gate it with a button rather than calling it on
  every slider update, and let the composition/document preview update first.

Example capture call, after generating the composition:

```python
if capture:
    image_path = cdf.caputreview(
        r"C:\Users\your_username\Pictures\CDF",
        transparent_background=True,
        border=32,
        resolution=300,
    )
```

For an opaque background, use `transparent_background=False` and provide
`background_color` from a GH color input or `System.Drawing.Color`. Its alpha is
ignored. `path` must be an absolute output folder. Files are named
`ViewCapture_YYMMDD_HHMMSS.png`; existing files are not overwritten.

Capture temporarily fits the last generated composition, disables the ground
plane and captures at three times the viewport width and height. It retains the
view direction/display mode and restores the original viewport/ground-plane state
afterwards. The alpha silhouette is cropped to visible pixels, then `border`
adds 0-10000 whole pixels per side. `resolution` sets positive, finite dpi metadata
(default: 300), **not pixel dimensions**. Final images are limited to 64 megapixels.
Hide unrelated visible Rhino/GH objects before capture: they would appear too.
Ground-plane shadows are not captured.

### Validation scope

These modules require RhinoCommon and the Rhino/.NET runtime; they are not a
standalone CPython geometry application. This checkout does not include the
previously described automated composition/cache test suite.

When evaluating geometry in Rhino, compare the chosen view with the reference and
exercise zero controls, slider endpoints, combined controls, cache recomputation
and view/export buttons. Visual agreement and Rhino solid/Boolean behavior cannot
be established from Python syntax checks alone.
