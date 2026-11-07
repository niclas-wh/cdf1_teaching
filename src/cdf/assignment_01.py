"""Architektonische Bauhaus-Komposition nach der Referenzansicht von Bild 4."""

import math

from . import tools


def create_composition(scale=1.0, origin=(0.0, 0.0, 0.0),
                       u=0.0, v=0.0, w=0.0, x=0.0, y=0.0, z=0.0,
                       seed=100, *, tolerance=0.001):
    """Parametrische Komposition, nach Materialien gruppiert.

    Alle Regler akzeptieren -10 bis 10; sechs Nullen ergeben den Referenzstand.
    u: 1–7 Fenster pro rechter Reihe; blaue Balken wachsen nur nach rechts.
    v: unterschiedliche, reproduzierbare Durchmesserfaktoren am Kugelturm.
    w: Höhenfaktor 0.6–1.4 am Kugelturm, mit geführten Ringen und Kugel.
    x: 2–9 mittlere Geschosse (Referenz 5), mit Platten, Säule und Aufbauten.
    y: farbige Quader und gelber Fußzylinder; L-Teile teilen Faktor und Anker.
    z: 1–13 linke Lamellen (Referenz 5), Halbzylinder und mitwachsende Platte.

    u, x und die Lamellenanzahl werden auf die nächste Rasterstufe gerundet.
    v und y verändern Maße bei ±10 um etwa ±20–35 %, stabil je seed/Bauteil.
    Der Schacht endet unten bei Z=26 und hinten an der Zylinderhinterkante.
    Die blaue Abdeckung behält auch bei y<0 ihre Mindestgrundfläche.
    Dachaufbauten wachsen vom Schacht weg. Rechte Balken behalten ihren
    inneren Anschlag und einen positiven Überstand. Blauer Fassadenstreifen
    und roter Portalblock enden mindestens eine Einheit unter ihrer Fassade,
    auch bei verändertem y. Im Nullstand ist der Augenblock 26 hoch,
    sein Auge liegt 17.0 über der Basis. Der linke Portalbogen erhält unabhängig
    von z zwei Einheiten zusätzliche Breite. Die Außenfasen der rechten Rahmen
    enden auf der Fassadenebene, gerade Rahmenabschnitte liegen in der Wand.
    Horizontale Fugen an Fensterfassaden und segmentierter Säule sind 0.24 breit;
    Geschossraster sowie Säulenfuß und -kopf bleiben unverändert.
    Linke Halbzylinderfaktoren bei z=-10/0/10: 0.6/1.0/1.8.
    Der positive z-Bereich wirkt doppelt so stark; negative Werte bleiben gleich.
    Z ist oben; die Hauptfassade zeigt nach -Y, der Rechtsflügel nach +X.
    Rotation und Baugruppenversätze erfolgen vor scale/origin.
    Kamera, Layer und Materialfarben werden hier nicht verändert.
    """
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale muss positiv und endlich sein.")
    if len(origin) != 3 or not all(math.isfinite(v) for v in origin):
        raise ValueError("origin muss drei endliche Koordinaten enthalten.")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance muss positiv und endlich sein.")
    controls = {name: tools.slider_value(value, name)
                for name, value in zip("uvwxyz", (u, v, w, x, y, z))}
    window_count = tools.raster_count(controls["u"], "u", 3, 1, 7)
    storey_count = tools.raster_count(controls["x"], "x", 5, 2, 9)
    fin_count = tools.raster_count(controls["z"], "z", 5, 1, 13)
    wing_extension = (window_count - 3) * 10.5
    middle_rise = (storey_count - 5) * 9.0
    left_extension = (fin_count - 5) * 2.0
    half_factor = tools.slider_factor(controls["z"], "z") + 0.04 * max(0.0, controls["z"])
    height_factor = tools.slider_factor(controls["w"], "w")
    joint_gap, top_reveal = 0.24, 1.0
    tol = tolerance / scale
    groups = {name: [] for name in tools.COLOR_GROUPS}
    right_wing = False
    assembly_offset = (0.0, 0.0, 0.0)
    wing_pivot = (28.0, -3.0, 0.0)
    tower_x, tower_y, tower_radius = 31.0, -1.0, 5.5
    tower_top, roof_base = 71.0 + middle_rise, 68.0 + middle_rise

    def resize_factor(key):
        return tools.varied_factor(controls["y"], seed, "block:" + key)

    def height_below(bottom, height, key, anchor_z, ceiling):
        # Die Grenze gilt nach der y-Skalierung, deshalb vorher invers umrechnen.
        limit = anchor_z + (ceiling - anchor_z) / resize_factor(key) - bottom
        return min(height, limit)

    def add(shape, color, *, resize_key=None, anchor=None):
        if resize_key is not None and controls["y"] != 0:
            factor = resize_factor(resize_key)
            shape = tools.transformed(shape, factor,
                                      tuple(c * (1.0 - factor) for c in anchor))
        if shape is None or not shape.IsValid or not shape.IsSolid:
            raise RuntimeError("Ungültiger Volumenkörper in Farbgruppe " + color)
        if right_wing:
            shape = tools.rotated_z(shape, math.pi / 2, wing_pivot)
        placed_origin = tuple(base + scale * delta
                              for base, delta in zip(origin, assembly_offset))
        groups[color].append(tools.transformed(shape, scale, placed_origin))

    def block(bx, by, bz, width, depth, height, color="white", *, key=None, anchor=None):
        if anchor is None:
            anchor = (bx + width / 2.0, by + depth / 2.0, bz)
        add(tools.box(bx, by, bz, width, depth, height), color,
            resize_key=key if color in ("blue", "red", "yellow") else None,
            anchor=anchor)

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

    # Fenster- und Plattenraster bleiben bei neun Einheiten je Geschoss.
    facade_bottom = 26.0
    facade_top = facade_bottom + storey_count * 9 - joint_gap
    for row in range(storey_count):
        arch_wall(-15, -12, facade_bottom + row * 9, 28, 7, 9 - joint_gap,
                  (-8, 5.5), 4.5)
    # Beide Schenkel teilen Faktor und Anker; nur die obere Länge wird begrenzt.
    middle_l_anchor = (-15, -5.5, 26)
    spine_height = height_below(23, 46 + middle_rise, "middle-base",
                                middle_l_anchor[2], facade_top - top_reveal)
    block(-20, -11.8, 23, 5, 8, spine_height, "blue",
          key="middle-base", anchor=middle_l_anchor)
    block(-20, -12, 22, 19, 13, 4, "blue",
          key="middle-base", anchor=middle_l_anchor)
    block(-1, -5, 19, tower_x + 1, 18, 7, "red",
          key="middle-plinth", anchor=(15, 4, 26))
    block(13, -5, 26, tower_x - 13, 14, 9, "red", key="middle-panel")
    # Schacht und Platten enden an der Fassadenunterkante und Zylinderhinterkante.
    shelf_left, shelf_front, backing = 8.0, -1.0, 0.4
    shelf_back = tower_y + tower_radius
    shaft_bottom = facade_bottom
    shaft_height = 72.0 + middle_rise - shaft_bottom
    block(shelf_left, shelf_front, shaft_bottom, backing,
          shelf_back - shelf_front, shaft_height, "black")
    block(shelf_left + backing, shelf_back - backing, shaft_bottom,
          tower_x - 0.2 - shelf_left - backing, backing, shaft_height, "black")
    for row in range(storey_count - 1):
        block(shelf_left + backing, shelf_front, 35 + row * 9,
              tower_x - shelf_left - backing, shelf_back - backing - shelf_front, 1.1)
    # Die Grundfläche darf nicht unter die Schacht-/Zylinderkontur schrumpfen.
    cap_factor = resize_factor("middle-cap")
    cap_plan_factor = max(1.0, cap_factor)
    cap_left = tower_x + (shelf_left - tower_x) * cap_plan_factor
    cap_front = tower_y - 6 * cap_plan_factor
    block(cap_left, cap_front, tower_top,
          (tower_x + tower_radius - shelf_left) * cap_plan_factor,
          (shelf_back - (tower_y - 6)) * cap_plan_factor, 5 * cap_factor, "blue")
    column_factor = (tower_top - 11) / 60.0
    column_levels = (11, 26, 40, 53, 64, 71)
    for base_z, next_z in zip(column_levels, column_levels[1:]):
        gap = joint_gap if next_z < column_levels[-1] else 0.0
        column(tower_x, tower_y, 11 + (base_z - 11) * column_factor,
               tower_radius, (next_z - base_z) * column_factor - gap)

    # Lochplattenflügel und gelber Fuß bleiben als Baugruppe verbunden.
    assembly_offset = (0.0, -4.0, 0.0)
    round_row_height = 11 - joint_gap
    round_facade_top = 29 + 3 * 11 - joint_gap
    for row in range(3):
        z = 29 + row * 11
        body = tools.box(-32, -10, z, 12, 6, round_row_height)
        cutter = tools.cylinder_y(-26, -11, z + 5.5, 3.1, 2.6)
        add(tools.difference(body, [cutter], tol), "white")
        block(-31.7, -8.5, z + 0.3, 11.4, 0.2, round_row_height - 0.6, "black")
    block(-32, -3, 14, 8, 10, 21, "yellow",
          key="left-foot", anchor=(-28, 2, 35))

    assembly_offset = (-10.0, -5.0, 0.0)

    def round_radius(radius, key):
        return radius * tools.varied_factor(controls["v"], seed, "tower:" + key)

    shaft_radius = round_radius(4.7, "shaft")
    sphere_radius = round_radius(10, "sphere")
    collar_radius = max(round_radius(5.2, "collar"), shaft_radius * 1.06)
    sphere_z = 40 + 36 * height_factor
    # Mindestabstände halten die Ringe auch bei großem v und kleinem w frei.
    collar_z = max(40 + 49.5 * height_factor, sphere_z + sphere_radius + 0.5)
    cap_z = max(40 + 59 * height_factor, collar_z + 4.0)
    column(-28, 1, 40, shaft_radius, cap_z - 40, "blue")
    add(tools.sphere(-28, 1, sphere_z, sphere_radius), "yellow")
    column(-28, 1, collar_z, collar_radius, 3.5)
    column(-28, 1, cap_z, round_radius(7.8, "cap"), 3.8)
    column(-28, 1, cap_z + 3.8, round_radius(3.3, "tip"), 3.5, "red")
    assembly_offset = (0.0, 0.0, 0.0)
    block(-17, 2, roof_base, 9, 9, 12, "red", key="roof-small")

    # Dachpositionen bleiben trotz verkürzter Schachttiefe erhalten.
    # Schachtseitige Kanten sind fest; Mehrgröße wächst samt Auge nach hinten.
    assembly_offset = (shelf_left - 12, 2.0, 0.0)
    eye_anchor = (12, 3.5, roof_base)
    eye_height, eye_center_z = 26.0, roof_base + 17.0
    body = tools.box(-3, 0, roof_base, 15, 7, eye_height)
    eye_cutter = tools.cylinder_y(4.5, -1, eye_center_z, 4.8, 2.6)
    add(tools.difference(body, [eye_cutter], tol), "red",
        resize_key="roof-eye", anchor=eye_anchor)
    add(tools.box(-2.7, 1.5, roof_base + 0.3, 14.4, 0.2, eye_height - 0.6), "black",
        resize_key="roof-eye", anchor=eye_anchor)
    block(10, 8, roof_base, 6, 9, 30, "yellow",
          key="roof-yellow", anchor=(13, 8, roof_base))

    # Der rechte Anschluss bleibt fest; zusätzliche Lamellen wachsen nach links.
    assembly_offset = (-1.0, -13.0, 0.0)
    platform_z, platform_front = 29.0, -10.0
    platform_top = platform_z + 2.4
    portal_front, portal_back = -6.0, 2.0
    portal_top = platform_top + 17.0
    portal_extra_width = 2.0
    portal_left = -50 - left_extension - portal_extra_width
    portal_width = 19 + left_extension + portal_extra_width
    half_radius, half_depth = 6 * half_factor, 6 * half_factor
    vault_radius, vault_depth = 9 * half_factor, 8 * half_factor
    platform_left = portal_left - 2 * half_radius - 1
    platform_back = max(10.0, portal_back + vault_depth)
    block(platform_left, platform_front, platform_z, -31 - platform_left,
          platform_back - platform_front, platform_top - platform_z, "black")
    portal_radius = min(5.0 + portal_extra_width / 2.0, (portal_width - 4) / 2.0)
    portal_center = portal_left + min(8.0, portal_width / 2.0)
    arch_wall(portal_left, portal_front, platform_top, portal_width,
              portal_back - portal_front, portal_top - platform_top,
              (portal_center,), portal_radius, 5)
    portal_block_height = height_below(portal_top, 62 - portal_top, "left-portal",
                                       portal_top, round_facade_top - top_reveal)
    block(-41, -1, portal_top, 7, portal_back + 1, portal_block_height, "red",
          key="left-portal")
    add(tools.arch_prism(portal_left - half_radius, portal_back - half_depth,
                         platform_top, half_radius, half_depth, tolerance=tol), "white")

    # Kamin und Aussparung folgen dem veränderlichen Gewölbe gemeinsam.
    chimney_x = -48 - left_extension
    chimney_y = portal_back + vault_depth / 2.0
    chimney_radius = 3.1 * half_factor
    chimney_top = 56 + vault_radius - 9
    chimney_height = chimney_top - platform_top
    vault = tools.arch_prism(-46 - left_extension, portal_back, platform_top,
                             vault_radius, vault_depth, 39 - platform_top, tol)
    chimney_cut = tools.cylinder(chimney_x, chimney_y, platform_top - 1,
                                 chimney_radius, chimney_height + 2)
    add(tools.difference(vault, [chimney_cut], tol), "black")
    column(chimney_x, chimney_y, platform_top, chimney_radius, chimney_height)

    lower_x = min(-49 - left_extension, -37 - 3.4 - half_radius - 1)
    lower_depth = 9 * half_factor
    lower_y = 0.5 - lower_depth / 2.0
    lower_half = tools.arch_prism(lower_x, lower_y, 0, half_radius,
                                  lower_depth, tolerance=tol)
    import Rhino.Geometry as rg
    lower_half.Transform(rg.Transform.Rotation(math.pi, rg.Vector3d.YAxis,
                                               rg.Point3d(lower_x, lower_y, 0)))
    lower_half.Transform(rg.Transform.Translation(0, 0, platform_z))
    add(lower_half, "white")
    for i in range(fin_count):
        block(-40 - left_extension + i * 2, platform_front, platform_top, 0.9,
              portal_front - platform_front, portal_top - platform_top)
    column(-37, -3, 20, 3.4, platform_z - 20)

    # Nach der Drehung als Ganzes vorziehen; die Stirnlamellen liegen vor dem Turm.
    right_wing = True
    assembly_offset = (tower_x - wing_pivot[0] + 15.0,
                       tower_y - wing_pivot[1], 0.0)
    wing_start, wing_front, wing_back = 33.0, -4.0, 12.0
    wing_width = 35 + wing_extension
    window_centers = tuple(39 + i * 10.5 for i in range(window_count))
    arch_centers = tuple(39 + i * 10 for i in range(window_count))
    frame_width, frame_height, frame_wall = 7.4, 9.5, 1.6
    frame_z = 21
    # Außenfase bis zur Fassadenebene; der gerade Abschnitt liegt in der Wand.
    frame_chamfer, frame_embed = 0.8, 0.5
    frame_front = wing_front - frame_chamfer
    frame_depth = frame_chamfer + frame_embed
    opening_width = frame_width - 2 * frame_wall
    opening_height = frame_height - 2 * frame_wall
    cutters = [tools.box(cx - opening_width / 2, -7, frame_z + frame_wall,
                         opening_width, 4.6, opening_height)
               for cx in window_centers]
    add(tools.difference(tools.box(wing_start, wing_front, 18, wing_width,
                                   wing_back - wing_front, 17), cutters, tol), "white")
    block(33.3, -2.5, 18.3, wing_width - 0.6, 0.2, 16.4, "black")
    for cx in window_centers:
        add(tools.chamfered_frame(cx - frame_width / 2, frame_front, frame_z,
                                  frame_width, frame_height, frame_depth, frame_wall,
                                  chamfer=frame_chamfer, tolerance=tol,
                                  inner_chamfer=0.2), "white")
    block(29, -5, 35, 40 + wing_extension, 18, 3, "black")
    arch_wall(32, -2, 38, 34 + wing_extension, wing_back + 2, 11,
              arch_centers, 3.5)
    # u ändert nur das äußere Ende; y skaliert Querschnitt und Überstand.
    beam_overhang = 2.0
    lintel_factor = resize_factor("right-lintel")
    arch_end = 32 + 34 + wing_extension
    lintel_width = (arch_end - 30) / lintel_factor + beam_overhang
    block(30, -3, 49, lintel_width, wing_back + 3, 4.5, "blue",
          key="right-lintel", anchor=(30, 4.5, 49))
    roof_count = max(1, int(math.floor((32 + wing_extension) / 6.0)))
    for i in range(roof_count):
        rib_height = 16 - i * 1.5 if i < 5 else 10 * 0.85 ** (i - 4)
        block(33 + i * 6, 3, 53.5, 3, 12, rib_height)
    for i in range(5):
        block(31.4, wing_front, 23 + i * 2.7, wing_start - 31.4,
              7.8 - wing_front, 1.2)
    right_l_anchor = (29, 5, 18)
    right_l_factor = resize_factor("right-base")
    wing_end = wing_start + wing_width
    foot_width = (wing_end - 29) / right_l_factor + beam_overhang
    block(29, -2, 15, foot_width, 14, 3, "blue",
          key="right-base", anchor=right_l_anchor)
    block(29, -2, 18, 3, 9, 5, "blue",
          key="right-base", anchor=right_l_anchor)
    block(65 + wing_extension, 6, 38, 4, 6, 7, "black")
    right_wing = False
    assembly_offset = (0.0, 0.0, 0.0)
    # Mit y skalieren und die Oberkante an der Unterseite des roten Sockels führen.
    foot_factor = resize_factor("middle-foot")
    foot_top = 27 - 7 * resize_factor("middle-plinth")
    column(15, 0, foot_top - 8 * foot_factor, 2.7 * foot_factor,
           8 * foot_factor, "yellow")
    return groups
