"""

Intro to project ...


Setup
=====

In order to use this library, ...


Main concepts
=============

Describe typical classes found in project

.. autoclass:: SampleClassName
   :members:


"""

from . import tools, assignment_01

nx = 10
ny = 10
spacing = 12.0

diameter_min = 4.0
diameter_max = 10.0
height_min = 5.0
height_max = 30.0

jitter = 0.3
seed = 100

def cylinders():
    """Erzeuge die Geometrie mit den aktuellen Einstellungen dieses Moduls."""
    cells = tools.randomized_grid(
        nx, ny, spacing, diameter_min, diameter_max,
        height_min, height_max, jitter, seed,
    )
    return assignment_01.create_cylinders(cells)

a = cylinders()
b = []
c = []
