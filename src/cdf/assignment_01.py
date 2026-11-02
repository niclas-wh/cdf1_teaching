import Rhino.Geometry as rg


def create_cylinders(cells):
    """Erzeuge Breps aus (x, y, Durchmesser, Höhe) in Modelleinheiten."""
    cylinders = []
    for x, y, diameter, height in cells:
        if diameter <= 0 or height <= 0:
            raise ValueError("Durchmesser und Höhe müssen größer als 0 sein.")

        base = rg.Point3d(x, y, 0)
        plane = rg.Plane(base, rg.Vector3d.ZAxis)
        circle = rg.Circle(plane, diameter / 2.0)
        cylinder = rg.Cylinder(circle, height)
        brep = cylinder.ToBrep(True, True)
        if brep is None:
            raise RuntimeError("Ein Zylinder konnte nicht erzeugt werden.")
        cylinders.append(brep)

    return cylinders
