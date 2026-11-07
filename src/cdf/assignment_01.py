"""Architektonische Bauhaus-Komposition nach der Referenzansicht von Bild 4."""

import math

from . import tools


def create_composition(scale=1.0, origin=(0.0, 0.0, 0.0),
                       base_plate_size=0.0, sphere_size=0.0, sphere_position=0.0,
                       stair_length=0.0, grid_size=0.0, block_position=0.0,
                       seed=100, *, tolerance=0.001):
    """Feste Referenzgeometrie, nach Materialien gruppiert.

    Z ist oben, die Hauptfassade liegt in negativer Y-Richtung. Der rechte
    Flügel knickt am Zylinderturm um 90° in die positive Y-Richtung ab;
    seine Fenster zeigen nach +X. Die Referenzansicht liegt auf der +X/-Y-Seite.
    Die Zwischenplatten liegen in einer schwarzen Rück-/Seitenwand hinter
    der Hauptfassade, der rechte Flügel vor dem seitlich versetzten Zylinderturm.
    Seine Stirnlamellen enden an der Fensterfassade, der Bogenblock reicht
    bis zur rückwärtigen Flügelebene. Links sind Lochplattenflügel, Kugelturm
    und Gewölbeflügel separat nach vorn und links gestaffelt; Lamellen und
    Gewölbe schließen an Wand und Trägerplatte an. Dachaufbauten reichen
    nach unten hinter die Fassade; blaue Abschlüsse sitzen ohne Anschlussfuge.
    Bogen- und Rundöffnungen sind flache Nischen mit dunklen Rückflächen.
    Baugruppenversätze werden vor scale/origin in Modell-Einheiten angewendet.
    Die sechs bisherigen Regler und seed sind reserviert und wirkungslos.
    Maße sind Modell-Einheiten; Rückseiten sind aus dem Einzelbild angenähert.
    Die Kamera wird nicht verändert.
    """
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale muss positiv und endlich sein.")
    if len(origin) != 3 or not all(math.isfinite(v) for v in origin):
        raise ValueError("origin muss drei endliche Koordinaten enthalten.")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance muss positiv und endlich sein.")
    tol = tolerance / scale
    groups = {name: [] for name in tools.COLOR_GROUPS}
    right_wing = False
    assembly_offset = (0.0, 0.0, 0.0)
    wing_pivot = (28.0, -3.0, 0.0)
    tower_x, tower_y, tower_radius = 31.0, -1.0, 5.5
    tower_top, roof_base = 71.0, 68.0

    def add(shape, color):
        if shape is None or not shape.IsValid or not shape.IsSolid:
            raise RuntimeError("Ungültiger Volumenkörper in Farbgruppe " + color)
        if right_wing:
            shape = tools.rotated_z(shape, math.pi / 2, wing_pivot)
        placed_origin = tuple(base + scale * delta
                              for base, delta in zip(origin, assembly_offset))
        groups[color].append(tools.transformed(shape, scale, placed_origin))

    def block(x, y, z, w, d, h, color="white"):
        add(tools.box(x, y, z, w, d, h), color)

    def column(x, y, z, r, h, color="white"):
        add(tools.cylinder(x, y, z, r, h), color)

    def arch_wall(x, y, z, w, d, h, centers, radius, spring=0.0,
                  color="white"):
        recess = 1.6
        cutters = [tools.arch_prism(cx, y - 1, z + 1.4, radius, recess + 1,
                                    spring, tol) for cx in centers]
        add(tools.difference(tools.box(x, y, z, w, d, h), cutters, tol), color)
        # Die Rückfläche sitzt in der Wand, damit keine Durchblicke entstehen.
        block(x + 0.3, y + recess - 0.1, z + 0.3, w - 0.6, 0.2, h - 0.6, "black")

    # Mittlere, fünfgeschossige Fassade mit zehn Halbkreisbögen.
    for row in range(5):
        arch_wall(-15, -12, 26 + row * 9, 28, 7, 8.94,
                  (-8, 5.5), 4.5)
    block(-20, -11.8, 23, 5, 8, 46, "blue")
    block(-20, -12, 22, 19, 13, 4, "blue")
    block(-1, -5, 19, tower_x + 1, 18, 7, "red")
    block(13, -5, 26, tower_x - 13, 14, 9, "red")
    # L-förmiger Hintergrund; die Platten stoßen innen an beide schwarzen Wände.
    shelf_left, shelf_front, shelf_back, backing = 8.0, -1.0, 10.0, 0.4
    block(shelf_left, shelf_front, 35, backing, shelf_back - shelf_front, 37, "black")
    block(shelf_left + backing, shelf_back - backing, 35,
          tower_x - 0.2 - shelf_left - backing, backing, 37, "black")
    for z in (35, 44, 53, 62):
        block(shelf_left + backing, shelf_front, z,
              tower_x - shelf_left - backing, shelf_back - backing - shelf_front, 1.1)
    block(shelf_left, tower_y - 6, tower_top,
          tower_x + tower_radius - shelf_left, shelf_back - (tower_y - 6), 5, "blue")
    for z, height in ((11, 14.94), (26, 13.94), (40, 12.94),
                      (53, 10.94), (64, tower_top - 64)):
        column(tower_x, tower_y, z, tower_radius, height)

    # Lochplattenflügel und gelber Fuß bleiben als Baugruppe verbunden.
    assembly_offset = (0.0, -4.0, 0.0)
    for row in range(3):
        z = 29 + row * 11
        body = tools.box(-32, -10, z, 12, 6, 10.94)
        cutter = tools.cylinder_y(-26, -11, z + 5.5, 3.1, 2.6)
        add(tools.difference(body, [cutter], tol), "white")
        block(-31.7, -8.5, z + 0.3, 11.4, 0.2, 10.3, "black")
    block(-32, -3, 14, 8, 10, 21, "yellow")

    assembly_offset = (-10.0, -5.0, 0.0)
    column(-28, 1, 40, 4.7, 59, "blue")
    add(tools.sphere(-28, 1, 76, 10), "yellow")
    column(-28, 1, 89.5, 5.2, 3.5)
    column(-28, 1, 99, 7.8, 3.8)
    column(-28, 1, 102.8, 3.3, 3.5, "red")
    assembly_offset = (0.0, 0.0, 0.0)
    block(-17, 2, roof_base, 9, 9, 80 - roof_base, "red")

    # Gemeinsamer Versatz: Rot hinter die Seitenwand, Gelb hinter die Rückwand.
    assembly_offset = (shelf_left - 12, shelf_back - 8, 0.0)
    body = tools.box(-3, 0, roof_base, 15, 7, 91 - roof_base)
    add(tools.difference(body, [tools.cylinder_y(4.5, -1, 81.5, 4.8, 2.6)], tol), "red")
    block(-2.7, 1.5, roof_base + 0.3, 14.4, 0.2,
          90.7 - (roof_base + 0.3), "black")
    block(10, 8, roof_base, 6, 9, 98 - roof_base, "yellow")

    # Gemeinsame Anschlussflächen vermeiden Überlappungen und schwebende Bauteile.
    assembly_offset = (-1.0, -13.0, 0.0)
    platform_z, platform_front, platform_back = 29.0, -10.0, 10.0
    platform_top = platform_z + 2.4
    portal_front, portal_back = -6.0, 2.0
    portal_top = platform_top + 17.0
    block(-63, platform_front, platform_z, 32,
          platform_back - platform_front, platform_top - platform_z, "black")
    arch_wall(-50, portal_front, platform_top, 19, portal_back - portal_front,
              portal_top - platform_top, (-42,), 5, 5)
    block(-41, -1, portal_top, 7, portal_back + 1, 62 - portal_top, "red")
    add(tools.arch_prism(-56, -4, platform_top, 6, portal_back + 4,
                         tolerance=tol), "white")

    # Gewölbe mit Fuß bis zur Platte; der Kamin sitzt in einer echten Aussparung.
    chimney_x, chimney_y, chimney_radius, chimney_top = -48.0, 6.0, 3.1, 56.0
    chimney_height = chimney_top - platform_top
    vault = tools.arch_prism(-46, portal_back, platform_top, 9,
                             platform_back - portal_back, 39 - platform_top, tol)
    chimney_cut = tools.cylinder(chimney_x, chimney_y, platform_top - 1,
                                 chimney_radius, chimney_height + 2)
    add(tools.difference(vault, [chimney_cut], tol), "black")
    column(chimney_x, chimney_y, platform_top, chimney_radius, chimney_height)

    lower_half = tools.arch_prism(-49, -4, 0, 6, 9, tolerance=tol)
    import Rhino.Geometry as rg
    lower_half.Transform(rg.Transform.Rotation(math.pi, rg.Vector3d.YAxis,
                                               rg.Point3d(-49, -4, 0)))
    lower_half.Transform(rg.Transform.Translation(0, 0, platform_z))
    add(lower_half, "white")
    for i in range(5):
        block(-40 + i * 2, platform_front, platform_top, 0.9,
              portal_front - platform_front, portal_top - platform_top)
    column(-37, -3, 20, 3.4, platform_z - 20)

    # Nach der Drehung als Ganzes vorziehen; die Stirnlamellen liegen vor dem Turm.
    right_wing = True
    assembly_offset = (tower_x - wing_pivot[0] + 15.0,
                       tower_y - wing_pivot[1], 0.0)
    wing_start, wing_front, wing_back = 33.0, -4.0, 12.0
    window_centers = (39, 49.5, 60)
    frame_width, frame_height, frame_wall = 7.4, 9.5, 1.6
    frame_z = 21
    opening_width = frame_width - 2 * frame_wall
    opening_height = frame_height - 2 * frame_wall
    cutters = [tools.box(cx - opening_width / 2, -7, frame_z + frame_wall,
                         opening_width, 4.6, opening_height)
               for cx in window_centers]
    add(tools.difference(tools.box(wing_start, wing_front, 18, 35,
                                   wing_back - wing_front, 17), cutters, tol), "white")
    block(33.3, -2.5, 18.3, 34.4, 0.2, 16.4, "black")
    for x in window_centers:
        add(tools.chamfered_frame(x - frame_width / 2, -6, frame_z,
                                  frame_width, frame_height, 2.5, frame_wall,
                                  chamfer=0.8, tolerance=tol, inner_chamfer=0.2), "white")
    block(29, -5, 35, 40, 18, 3, "black")
    arch_wall(32, -2, 38, 34, wing_back + 2, 11, (39, 49, 59), 3.5)
    block(30, -3, 49, 35, wing_back + 3, 4.5, "blue")
    for i in range(5):
        block(33 + i * 6, 3, 53.5, 3, 12, 16 - i * 1.5)
    for i in range(5):
        block(31.4, wing_front, 23 + i * 2.7, wing_start - 31.4,
              7.8 - wing_front, 1.2)
    block(29, -2, 15, 16, 14, 3, "blue")
    block(29, -2, 18, 3, 9, 5, "blue")
    block(65, 6, 38, 4, 6, 7, "black")
    right_wing = False
    assembly_offset = (0.0, 0.0, 0.0)
    column(15, 0, 12, 2.7, 8, "yellow")
    return groups
