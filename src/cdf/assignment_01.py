"""Abstrakte räumliche Komposition nach der Bildvorlage, ohne Schriftzüge."""

import math
import random

from . import tools


def create_composition(scale=1.0, origin=(0.0, 0.0, 0.0),
                       base_plate_size=0.0, sphere_size=0.0, sphere_position=0.0,
                       stair_length=0.0, grid_size=0.0, block_position=0.0,
                       seed=100):
    """Liefere Geometrielisten nach Farbgruppen, ohne Materialzuweisung.

    Z zeigt nach oben; die Vorderseite liegt in negativer Y-Richtung.
    Die Komposition ist für eine Perspektive von (220, -330, 240) ausgelegt.
    Alle Objekte bleiben ungebakt, damit Neuberechnungen nichts duplizieren.
    """
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale muss positiv und endlich sein.")
    if len(origin) != 3 or not all(math.isfinite(v) for v in origin):
        raise ValueError("origin muss drei endliche Koordinaten enthalten.")

    plate_factor = tools.slider_factor(base_plate_size, "base_plate_size")
    sphere_factor = tools.slider_factor(sphere_size, "sphere_size")
    stair_factor = tools.slider_factor(stair_length, "stair_length")
    grid_factor = tools.slider_factor(grid_size, "grid_size")
    tools.slider_factor(sphere_position, "sphere_position")
    tools.slider_factor(block_position, "block_position")
    if not isinstance(seed, int):
        raise ValueError("seed muss eine ganze Zahl sein.")

    # Getrennte Zufallsströme halten Kugel- und Quaderrichtungen unabhängig.
    sphere_rng = random.Random("spheres:{}".format(seed))
    block_rng = random.Random("blocks:{}".format(seed))
    groups = {name: [] for name in tools.COLOR_GROUPS}

    def add(shape, color, name):
        if shape is None:
            raise RuntimeError("Geometrie fehlt: " + name)
        if scale != 1.0 or tuple(origin) != (0.0, 0.0, 0.0):
            shape = tools.transformed(shape, scale, origin)
        groups[color].append(shape)

    def block(x, y, z, w, d, h, color, name, movable=True):
        if color != "white":
            dx, dy, _ = tools.random_direction(block_rng, planar=True)
            if movable:
                x += dx * block_position
                y += dy * block_position
        add(tools.box(x, y, z, w, d, h), color, name)

    def ball(x, y, z, radius):
        dx, dy, dz = tools.random_direction(sphere_rng)
        return tools.sphere(x + dx * sphere_position,
                            y + dy * sphere_position,
                            z + dz * sphere_position, radius * sphere_factor)

    block(-48 * plate_factor, 4 - 38 * plate_factor, 0,
          96 * plate_factor, 76 * plate_factor, 4, "white", "Sockelplatte")
    add(tools.wedge(-26, -18, 4, 53, 45, 20, 42), "blue", "Blauer Keil")
    block(-5, -26, 4, 13, 12, 21, "black", "Schwarzer Vorderblock")
    block(-35, -31, 8, 24, 24, 19, "red", "Roter Rippenkörper", movable=False)
    for i in range(10):
        block(-35, -31 + i * 2.4, 27, 24, 1.25, 2.0,
              "red", "Rote Rippe {:02d}".format(i + 1), movable=False)

    for i in range(12):
        block(18, 4.4 + (-26.4 + i * 2.2) * stair_factor,
              44.3 + (-20.3 + i * 1.7) * stair_factor,
              20, 2.2 * stair_factor, 1.6 * stair_factor,
              "white", "Rechte Treppenstufe {:02d}".format(i + 1))
    block(18, 2, 44, 21, 12, 3, "yellow", "Gelbes Podest")
    block(18, 12, 44, 21, 1.6, 10, "yellow", "Gelbe Rückwand")
    block(37.4, 2, 44, 1.6, 10, 10, "yellow", "Gelbe Seitenwand")
    add(ball(28, 7, 51, 3.0), "blue", "Blaue Podestkugel")
    add(ball(34, 9, 54, 4.2), "blue", "Blaue Podestkugel groß")
    add(ball(24, -12, 36, 4.7), "blue", "Blaue Treppenkugel")

    for i in range(30):
        block(-72, 20 + (-56 + i * 1.9) * stair_factor,
              56.75 + (-48.75 + i * 1.65) * stair_factor,
              20, 0.9 * stair_factor, 0.9 * stair_factor,
              "white", "Schwebende Sprosse {:02d}".format(i + 1))

    add(tools.cylinder(-15, -3, 35, 3.5, 29), "red", "Rote Säule")
    add(ball(-11, -1, 72, 10), "yellow", "Zentrale gelbe Kugel")

    # Zwei versetzte Schichten bilden das durchlässige räumliche Würfelraster.
    for layer in range(2):
        for row in range(10):
            for col in range(10):
                x = -28 + col * 3.65 + layer * 1.5
                y = 11 + layer * 3.65
                z = 61 + row * 3.65
                block(-9.925 + (x + 9.925) * grid_factor, y,
                      78.325 + (z - 78.325) * grid_factor,
                      1.8 * grid_factor, 1.8, 1.8 * grid_factor, "white",
                      "Raster {}-{}-{}".format(layer, row, col))

    for i in range(10):
        block(15, 17, 54 + i * 3.65, 3.5, 3.5, 3.35,
              "red", "Roter Stapel {:02d}".format(i + 1))
    add(tools.pyramid(16.75, 18.75, 92, 5.5, 5), "red", "Rote Stapelspitze")

    block(8, 22, 93, 24, 15, 20, "black", "Oberer schwarzer Würfel")
    block(-17, 22, 111, 49, 12, 9, "blue", "Oberer blauer Querbalken")
    block(-17, 22, 105, 9, 12, 15, "blue", "Blaues Balkenende")
    block(-7, 19, 104, 9, 12, 42, "black", "Schwarzer Turm")
    block(-7, 19, 104, 24, 12, 8, "black", "Schwarzer Turmfuß")
    add(tools.pyramid(-2.5, 25, 146, 27, 23), "yellow", "Gelbe Pyramide")

    add(tools.revolved_profile(20, 27, 113, [
        (0, 0), (3.4, 0), (4.5, 0.8), (4.6, 3),
        (4.6, 8), (4.2, 10), (2.4, 12), (1.7, 13),
    ]), "white", "Weiße Flasche")
    add(tools.cylinder(20, 27, 126, 1.7, 2.2), "yellow", "Flaschenhals")
    add(tools.cylinder(20, 27, 128.2, 2.6, 1.0), "yellow", "Flaschenverschluss")

    # Außenwand, runder Rand und Innenwand ergeben einen offenen Hohlkörper.
    add(tools.revolved_profile(-36, 26, 91, [
        (0, -16), (7, -15), (13, -11), (17, -4), (18, 4),
        (16, 12), (12, 16), (9, 16.5), (8.5, 15.7),
        (11, 14), (14, 10), (15, 4), (14, -3),
        (10, -9), (5, -12), (0, -12.5),
    ]), "white", "Weißer offener Hohlkörper")

    block(-67, 22, 91, 19, 19, 19, "yellow", "Schwebender gelber Würfel")
    add(ball(-67, 30, 145, 10), "red", "Schwebende rote Kugel")
    add(ball(12, 37, 152, 10), "white", "Obere weiße Kugel")
    add(ball(45, 26, 65, 10), "yellow", "Rechte gelbe Kugel")
    add(ball(62, -2, 9, 10), "yellow", "Untere gelbe Kugel")
    return groups
