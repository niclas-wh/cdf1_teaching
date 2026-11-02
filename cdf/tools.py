"""Rhino-unabhängige Raster- und Zufallsfunktionen.

Der Zufallsgenerator wird pro Aufruf mit seed initialisiert, damit eine
Neuberechnung durch den Watcher dieselbe Zufallsverteilung liefert.
"""

import random


def randomized_grid(nx, ny, spacing, diameter_min, diameter_max,
                    height_min, height_max, jitter, seed):
    """Liefere (x, y, Durchmesser, Höhe) je Rasterzelle."""
    if not isinstance(nx, int) or not isinstance(ny, int) or nx < 1 or ny < 1:
        raise ValueError("nx und ny müssen positive ganze Zahlen sein.")
    if spacing <= 0:
        raise ValueError("spacing muss größer als 0 sein.")
    if not 0 < diameter_min <= diameter_max:
        raise ValueError("Erforderlich: 0 < diameter_min <= diameter_max.")
    if not 0 < height_min <= height_max:
        raise ValueError("Erforderlich: 0 < height_min <= height_max.")
    if not 0 <= jitter <= 1:
        raise ValueError("jitter muss zwischen 0 und 1 liegen.")

    rng = random.Random(seed)
    offset_x = (nx - 1) * spacing / 2.0
    offset_y = (ny - 1) * spacing / 2.0
    max_shift = spacing * jitter
    cells = []

    for i in range(nx):
        for j in range(ny):
            x = i * spacing - offset_x + rng.uniform(-max_shift, max_shift)
            y = j * spacing - offset_y + rng.uniform(-max_shift, max_shift)
            diameter = rng.uniform(diameter_min, diameter_max)
            height = rng.uniform(height_min, height_max)
            cells.append((x, y, diameter, height))

    return cells
