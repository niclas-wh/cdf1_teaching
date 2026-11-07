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

## Bildkomposition: Rhino-Layer und bearbeitbare Geometrie

Die [Geometrie](src/cdf/assignment_01.py) nähert die architektonische Bildvorlage
räumlich an: Bogenfassaden, runde Öffnungen, Lamellen, Turm mit Kugel und
Primärfarben. Z zeigt nach oben, die Hauptfassade liegt in negativer Y-Richtung.
Der rechte Flügel knickt am Zylinderturm bei `(28, -3)` um 90° in die **negative
Y-Richtung** ab: Unterbau, Fenster mit umlaufenden inneren und äußeren 45°-Fasen,
Bogenreihe, blaue Balken und Dachrippen werden gemeinsam gedreht. Die horizontalen
Lamellen sitzen auf der kurzen Stirnseite und verdecken keines der drei Fenster.
Die RGB-Farben bleiben unverändert; Rot, Blau und Gelb sind nun matt (kein Glanz,
keine Reflexion, schwarze Glanzlichtfarbe). Elfenbein und Anthrazit bleiben unverändert.
Maße und nicht sichtbare Rückseiten sind angenähert, keine maßhaltige Rekonstruktion.
Die Hauptausdehnung beträgt etwa 110 Modell-Einheiten. `cdf.scale` und
`cdf.origin` steuern bei Bedarf Größe und Position. Die Flügeldrehung erfolgt vor
Skalierung und Verschiebung, sodass der Anschluss am Turm erhalten bleibt.

### Vorhandenen AutoReloader-Block anpassen

Der eingebettete Code in [assignment-01.gh](assignments/assignment-01.gh) muss im
Grasshopper-Skripteditor angepasst werden; die GH-Datei wird nicht automatisch
umgeschrieben. Python 3 in Rhino 8 verwenden.

1. Auto-Reload, Pfadüberwachung und alle Aufrufe von `getview()`, `setview()` und
   `caputreview()` beibehalten. [viewtools.py](src/cdf/viewtools.py) bleibt unverändert.
2. Die bisherige Zuweisung des Ergebnisses von `cdf.composition(...)` durch diese
   Zeile ersetzen (nach Import/Reload von `cdf`, vor Ansichts-/Capture-Aufrufen):

   ```python
   a = cdf.composition(cache_id=str(ghenv.Component.InstanceGuid))
   ```

   Der Ausgang im Screenshot heißt `a`. Falls er tatsächlich `A` heißt, muss auch
   die Python-Variable `A` heißen. Nicht mehr `a, b, c, d, e = ...` verwenden:
   Der Rückgabewert ist jetzt eine flache Liste aller Breps, nicht fünf Farbgruppen.
   U bis Z bleiben angeschlossen, werden aber vorerst nicht ausgewertet. Auch ein
   alter Aufruf mit sechs Positionsargumenten akzeptiert sie weiterhin wirkungslos.
3. Die **Vorschau dieses Python-Blocks ausschalten** (Rechtsklick → Preview aus).
   Auch nachgeschaltete Vorschau-Komponenten ausschalten, damit die GH-Vorschau
   nicht die Materialfarben der gecachten Rhino-Objekte überlagert. A bleibt als
   Geometrieausgabe für weitere GH-Verarbeitung verfügbar.
4. Einmal neu berechnen. Es entstehen fünf Unterlayer unter `CDF_Bildkomposition`:
   Elfenbein, Anthrazit, Ultramarin, Zinnoberrot und Sonnengelb. Die
   [Layerverwaltung](src/cdf/layer.py) weist Layerfarben und Render-Materialien zu;
   jedes Objekt verwendet Farbe und Material **vom Layer**. Layeränderungen sind
   in Rhino 8 sofort wirksam; das veraltete `Layer.CommitChanges()` wird nicht benutzt.
   In Rhino lassen sich
   die Objekte sofort auswählen, verschieben und bearbeiten; zusätzliches Bake
   oder eine Content-Cache-Komponente ist nicht nötig.
5. Zum Betrachten **Rendered/Gerendert** oder **Raytraced** verwenden. Shaded zeigt
   Layerfarben, aber nicht dieselbe Materialwirkung. Für die geknickte Komposition
   aus **negativer X- und negativer Y-Richtung** schauen. Eine parallele Ansicht aus
   ungefähr `(-180, -300, 160)` auf `(0, -10, 56)` ist ein geeigneter Ausgangspunkt;
   anschließend auf die Komposition zoomen und mit dem vorhandenen Button speichern.
   Bei anderem `scale`/`origin` diese Koordinaten entsprechend mittransformieren.
   Die Kamera wird durch `composition()` absichtlich nicht verändert.
   Die bestehende `view.json` wird nicht überschrieben, bis `getview()` aufgerufen wird.
   Licht, Schatten und Bildausschnitt müssen für die Vorlage in Rhino abgestimmt werden.

### Cache-Verhalten und Grenzen

- Der Cache liegt im aktiven **Rhino-Dokument**, nicht im Grasshopper-Dokument.
  Eine Geometrieliste an A allein enthält keine Rhino-Layer oder Materialattribute.
  Die direkte Rhino-Ausgabe ist deshalb ein zusätzlicher, absichtlicher Seiteneffekt.
- Identische Geometrie erzeugt keine Duplikate, auch nach Modul-Reload. Manuelle
  Bearbeitungen, Layerwechsel und Löschungen bleiben bei unveränderter Eingabe erhalten.
  A enthält trotzdem die ursprüngliche generierte Geometrie, nicht die nachträglich
  bearbeiteten Rhino-Objekte. Der Bildexport verwendet deren ursprüngliche Grenzen.
- Änderungen an Geometrie, Maßstab, Ursprung oder Materialdefinition ersetzen nur
  die für dieselbe `cache_id` markierten Objekte. Manuelle Änderungen dieser Objekte
  gehen dann verloren. Für dauerhafte eigene Varianten vorher kopieren und bei den
  Kopien den Benutzertext `cdf.composition.owner` entfernen.
- `cdf.composition(cache_id=..., force=True)` erzeugt den ursprünglichen Zustand
  ausdrücklich neu, auch nach manuellem Löschen. Danach `force=True` wieder entfernen.
  Gesperrte Cache-Objekte verhindern eine Ersetzung mit einer Fehlermeldung.
- Mehrere GH-Blöcke benötigen unterschiedliche IDs; `InstanceGuid` liefert diese.
  Ohne explizite ID wird `default` benutzt und mehrere Aufrufer teilen einen Cache.
- Die Rhino-Datei als `.3dm` speichern: Objekte, Layer, Materialien und Cache-Zustand
  werden dort gespeichert. Entfernen des GH-Blocks löscht die Rhino-Objekte nicht.
  Manuell gebakte Altgeometrie ohne Cache-Markierung wird niemals automatisch gelöscht.
- `cdf.composition(bake=False)` liefert nur Geometrie an A, ohne Dokumentänderungen;
  bereits gecachte Objekte bleiben bestehen. Layer und Farben sind dann nicht in A.
- Die bestehenden ViewTools bleiben vollständig erhalten. Vor einer Aufnahme erst
  die Komposition berechnen lassen. Andere sichtbare Objekte ausblenden; Kamera und
  Export funktionieren weiterhin über die bisherigen Buttons.

### Validierung

Die Cache-Vertragstests benötigen nur die Python-Standardbibliothek:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Der zusätzliche RhinoCommon-Geometrietest wird außerhalb Rhino übersprungen.
Für einen echten Volumenkörper-/Boolean-Test in Rhinos Python-3-Skripteditor:

```python
import sys
import unittest
sys.path.insert(0, r"C:\Users\your_username\workspace\cdf1_teaching\tests")
from test_composition import GeometryTests
suite = unittest.defaultTestLoader.loadTestsFromTestCase(GeometryTests)
unittest.TextTestRunner(verbosity=2).run(suite)
```

Anschließend im GH-Block Neuberechnung, manuelle Objektbearbeitung, erneute
Neuberechnung und `force=True` prüfen. Die visuelle Übereinstimmung muss in Rhino
beurteilt werden; die Tests ersetzen keinen Vergleich mit der Bildvorlage.
