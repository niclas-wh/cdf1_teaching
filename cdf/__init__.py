from . import geometry, tools


# Längen in Rhino-Modelleinheiten
nx = 10
ny = 10
spacing = 12.0

diameter_min = 2.0
diameter_max = 10.0
height_min = 5.0
height_max = 30.0

jitter = 0.3
seed = 100

def run():
    """Erzeuge die Geometrie mit den aktuellen Einstellungen dieses Moduls."""
    cells = tools.randomized_grid(
        nx, ny, spacing, diameter_min, diameter_max,
        height_min, height_max, jitter, seed,
    )
    return geometry.create_cylinders(cells)


cylinders = run()
a = cylinders
