"""Éléments du film « Goutte » (Blender) : décor, goutte, caillou, pousse, vapeur, nuage, pluie, fleurs de verre.

Chaque fonction construit un objet dans la scène courante et le renvoie (ou un dict d'objets).
Utilisé par le film et par lookdev.py (images de validation de chaque élément).
"""
import math
import random

import bpy


def lin(r, g, b):
    return ((r / 255) ** 2.2, (g / 255) ** 2.2, (b / 255) ** 2.2)


def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, strength=0.0,
        alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def _delete_verts(obj, predicate):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in obj.data.vertices:
        v.select = predicate(v.co)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")


def water_material():
    m = mat("eau", lin(215, 235, 255), rough=0.0, trans=1.0, ior=1.33)
    vol = m.node_tree.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*lin(170, 215, 255), 1)
    vol.inputs["Density"].default_value = 0.2
    m.node_tree.links.new(vol.outputs["Volume"], m.node_tree.nodes["Material Output"].inputs["Volume"])
    return m


# ---------------------------------------------------------------- la goutte
def drop(location=(0, 0, 0), size=1.0, water=None):
    """Goutte avec yeux, paupières, bouches (sourire / « o »), petite main, lueur intérieure.
    L'origine est sous la goutte : l'écrasement part du sol."""
    water = water or water_material()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=128, ring_count=64)
    body = bpy.context.object
    body.name = "goutte"
    for v in body.data.vertices:
        z = v.co.z
        if z > 0:
            u = z / 0.5
            k = 1 - 0.5 * u ** 2.2          # sommet plus rond : silhouette plus mignonne
            v.co.x *= k
            v.co.y *= k
            v.co.z *= 1.0 + 0.36 * u
        v.co.z += 0.5
    body.data.materials.append(water)
    smooth(body)
    black = mat("pupille", (0.005, 0.005, 0.008), rough=0.15, coat=1.0)
    spark = mat("reflet", (1, 1, 1), emit=(1, 1, 1), strength=6)
    lid_m = mat("paupière", lin(150, 200, 245), rough=0.25, coat=1.0)
    mouth_m = mat("bouche", lin(15, 25, 45), rough=0.25, coat=1.0)
    eyes, lids = [], []
    for side in (-1, 1):
        # grands yeux (attrait « mignon ») avec deux reflets
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, segments=48, ring_count=24, location=(side * 0.16, -0.42, 0.56))
        e = smooth(bpy.context.object)
        e.data.materials.append(black)
        for r_, dx, dz in ((0.024, -0.03, 0.035), (0.011, 0.028, -0.025)):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r_, segments=16, ring_count=8,
                                                 location=(side * 0.16 + dx, -0.492, 0.56 + dz))
            s = bpy.context.object
            s.data.materials.append(spark)
            s.parent = e
            s.matrix_parent_inverse = e.matrix_world.inverted()
        e.parent = body
        eyes.append(e)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.094, segments=32, ring_count=16, location=e.location)
        lid = bpy.context.object
        _delete_verts(lid, lambda co: co.z < -0.001)
        lid.data.materials.append(lid_m)
        smooth(lid)
        lid.parent = body
        lid.rotation_euler = (math.radians(-70), 0, 0)
        lids.append(lid)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.055, minor_radius=0.013, location=(0, -0.5, 0.43),
                                     rotation=(math.pi / 2, 0, 0))
    smile = bpy.context.object
    _delete_verts(smile, lambda co: co.y > 0.004)
    smile.data.materials.append(mouth_m)
    smooth(smile).parent = body
    bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.012, location=(0, -0.5, 0.43),
                                     rotation=(math.pi / 2, 0, 0))
    ooh = smooth(bpy.context.object)
    ooh.data.materials.append(mouth_m)
    ooh.parent = body
    ooh.scale = (0, 0, 0)
    # joues roses
    blush = mat("joues", lin(255, 150, 175), rough=0.5, alpha=0.55)
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, segments=24, ring_count=12, location=(side * 0.29, -0.42, 0.46))
        ch = smooth(bpy.context.object)
        ch.scale = (1.2, 0.35, 0.7)
        ch.rotation_euler = (0, 0, side * 0.55)
        ch.data.materials.append(blush)
        ch.parent = body
    # petite main (excroissance d'eau) : repos le long du corps, levée pour la visière
    arm_c = bpy.data.curves.new("bras", "CURVE")
    arm_c.dimensions = "3D"
    arm_c.bevel_depth = 0.06
    arm_c.bevel_resolution = 6
    arm_c.use_fill_caps = True
    sp = arm_c.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, p, r in zip(sp.bezier_points, [(0.4, -0.12, 0.42), (0.52, -0.2, 0.5), (0.5, -0.24, 0.62)], (1.0, 0.8, 0.75)):
        bp.co, bp.radius = p, r
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    hand = bpy.data.objects.new("main", arm_c)
    bpy.context.collection.objects.link(hand)
    hand.data.materials.append(water)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, segments=32, ring_count=16, location=(0.5, -0.24, 0.65))
    palm = smooth(bpy.context.object)
    palm.scale = (1.0, 0.8, 0.7)
    palm.data.materials.append(water)
    palm.parent = hand
    hand.parent = body
    hand.scale = (0, 0, 0)          # bras rangé : n'apparaît que pour un geste
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 0.42))
    glow = bpy.context.object
    glow.data.energy, glow.data.color, glow.data.shadow_soft_size = 1.0, lin(160, 205, 255), 0.12
    glow.parent = body
    for ray in ("visible_camera", "visible_glossy", "visible_transmission"):
        setattr(glow, ray, False)
    body.location = location
    body.scale = (size, size, size)
    return {"body": body, "eyes": eyes, "lids": lids, "smile": smile, "ooh": ooh, "hand": hand, "glow": glow}


def hand_visor(d):
    """Pose : main levée en visière au-dessus des yeux."""
    spl = d["hand"].data.splines[0].bezier_points
    for bp, p in zip(spl, [(0.4, -0.12, 0.42), (0.46, -0.36, 0.7), (0.16, -0.49, 0.8)]):
        bp.co = p
    d["hand"].scale = (1, 1, 1)
    palm = d["hand"].children[0]
    palm.location = (0.06, -0.5, 0.8)
    palm.scale = (2.4, 1.1, 0.45)


# ---------------------------------------------------------------- désert
def sand_material():
    m = bpy.data.materials.new("sable")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(214, 156, 102), 1)
    b.inputs["Roughness"].default_value = 0.92
    wave = n.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 9.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    grain = n.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 900.0
    add = n.new("ShaderNodeMath")
    add.operation = "ADD"
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    l.new(wave.outputs["Fac"], add.inputs[0])
    l.new(grain.outputs["Fac"], add.inputs[1])
    l.new(add.outputs["Value"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def desert(sand=None):
    sand = sand or sand_material()
    bpy.ops.mesh.primitive_plane_add(size=260, location=(0, 60, -2.2))
    dunes = bpy.context.object
    m = dunes.modifiers.new("sub", "SUBSURF")
    m.subdivision_type, m.levels, m.render_levels = "SIMPLE", 8, 8
    tex = bpy.data.textures.new("dunes", "CLOUDS")
    tex.noise_scale = 7.0
    d = dunes.modifiers.new("disp", "DISPLACE")
    d.texture, d.strength = tex, 3.2
    dunes.data.materials.append(sand)
    smooth(dunes)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=128, ring_count=64, location=(0, 0, -1.4))
    crest = smooth(bpy.context.object)
    crest.scale = (9.0, 7.0, 1.4)
    crest.data.materials.append(sand)
    return dunes, crest


def sky(elevation_deg, rotation_deg=0.0, strength=0.6):
    w = bpy.data.worlds.new("ciel")
    bpy.context.scene.world = w
    w.use_nodes = True
    s = w.node_tree.nodes.new("ShaderNodeTexSky")
    s.sky_type = "MULTIPLE_SCATTERING"
    s.sun_elevation = math.radians(elevation_deg)
    s.sun_rotation = math.radians(rotation_deg)
    w.node_tree.links.new(s.outputs["Color"], w.node_tree.nodes["Background"].inputs["Color"])
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = strength
    return s


def sun(elevation_deg, rotation_deg=0.0, energy=4.0, color=(255, 236, 214)):
    e, r = math.radians(elevation_deg), math.radians(rotation_deg)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    tgt = bpy.context.object
    bpy.ops.object.light_add(type="SUN", location=(60 * math.sin(r) * math.cos(e), 60 * math.cos(r) * math.cos(e),
                                                   60 * math.sin(e)))
    s = bpy.context.object
    s.data.energy, s.data.color, s.data.angle = energy, lin(*color), math.radians(1.2)
    c = s.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    return s


# ---------------------------------------------------------------- caillou
def rock(location=(0, 0, 0), size=1.0, seed=2):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.5, subdivisions=5, location=location)
    r = smooth(bpy.context.object)
    for kind, scale_, strength in (("VORONOI", 0.3, 0.22), ("CLOUDS", 0.12, 0.05)):
        tex = bpy.data.textures.new(f"roc{seed}{kind}", kind)
        tex.noise_scale = scale_
        d = r.modifiers.new(kind, "DISPLACE")
        d.texture, d.strength = tex, strength
    r.scale = (0.8 * size, 0.65 * size, 0.5 * size)
    m = mat("roche", lin(112, 78, 60), rough=0.9)
    r.data.materials.append(m)
    return r


# ---------------------------------------------------------------- pousse
def sprout(location=(0, 0, 0), alive=0.0, size=1.0):
    """Petite pousse : alive=0 desséchée (tête basse, feuilles fanées), alive=1 vivante, droite, avec un bouton."""
    green = lin(*[int(a + (b - a) * alive) for a, b in zip((128, 112, 62), (95, 190, 90))])
    stem_m = mat("tige", green, rough=0.5, coat=0.3 * alive)
    bend = (1 - alive) * 0.9
    curve = bpy.data.curves.new("tige", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.016 * size
    curve.bevel_resolution = 4
    sp = curve.splines.new("BEZIER")
    pts = [(0, 0, 0), (0, 0, 0.28), (0.1 * bend, 0, 0.5 - 0.1 * bend), (0.28 * bend, 0, 0.62 - 0.35 * bend)]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = tuple(c * size for c in p)
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    stem = bpy.data.objects.new("tige", curve)
    bpy.context.collection.objects.link(stem)
    stem.data.materials.append(stem_m)
    stem.location = location
    leaf_m = mat("feuille", green, rough=0.45, coat=0.4 * alive)
    droop = math.radians(50 * (1 - alive) - 25 * alive)
    for side in (0, math.pi):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1 * size, segments=32, ring_count=16)
        leaf = smooth(bpy.context.object)
        for v in leaf.data.vertices:              # la base de la feuille à l'origine : elle pivote sur la tige
            v.co.x += 0.1 * size
        leaf.scale = (1.3, 0.16, 0.8)   # fine dans l'axe de la caméra : on voit la feuille de face
        leaf.rotation_euler = (0, droop, side)
        leaf.location = (location[0], location[1], location[2] + 0.36 * size)
        leaf.data.materials.append(leaf_m)
    if alive > 0.5:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06 * size, location=(location[0], location[1], location[2] + 0.66 * size))
        bud = smooth(bpy.context.object)
        bud.scale = (1, 1, 1.4)
        bud.data.materials.append(mat("bouton", lin(120, 190, 240), rough=0.1, trans=0.6, coat=1.0))
    # sol craquelé autour
    bpy.ops.mesh.primitive_circle_add(radius=0.7 * size, fill_type="NGON", location=(location[0], location[1], location[2] + 0.004))
    patch = bpy.context.object
    cm = bpy.data.materials.new("craquelé")
    cm.use_nodes = True
    n, l = cm.node_tree.nodes, cm.node_tree.links
    b = n["Principled BSDF"]
    vor = n.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 14
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*lin(90, 60, 40), 1)
    ramp.color_ramp.elements[1].position = 0.06
    ramp.color_ramp.elements[1].color = (*lin(196, 140, 92), 1)
    grad = n.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    coord = n.new("ShaderNodeTexCoord")
    l.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    l.new(coord.outputs["Object"], grad.inputs["Vector"])
    patch.scale = (1, 1, 1)
    b.inputs["Roughness"].default_value = 0.95
    mix_out = n.new("ShaderNodeMixShader")      # le craquelé se fond dans le sable sur les bords
    tr = n.new("ShaderNodeBsdfTransparent")
    l.new(grad.outputs["Fac"], mix_out.inputs["Fac"])
    l.new(tr.outputs["BSDF"], mix_out.inputs[1])
    l.new(b.outputs["BSDF"], mix_out.inputs[2])
    l.new(mix_out.outputs["Shader"], n["Material Output"].inputs["Surface"])
    patch.data.materials.append(cm)
    return stem


# ---------------------------------------------------------------- vapeur
def wisp(location=(0, 0, 0), height=0.9, turns=1.3, width=0.035, glow=0.0, seed=0):
    """Volute de vapeur : spirale qui s'affine et s'efface vers le haut."""
    rnd = random.Random(seed)
    curve = bpy.data.curves.new("volute", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = width
    curve.bevel_resolution = 6
    sp = curve.splines.new("NURBS")
    n = 12
    sp.points.add(n - 1)
    for i, p in enumerate(sp.points):
        u = i / (n - 1)
        a = u * turns * 2 * math.pi + rnd.uniform(0, 0.4)
        r = 0.06 + 0.1 * math.sin(u * math.pi)
        p.co = (r * math.cos(a), r * math.sin(a), u * height, 1)
        p.radius = 1.0 - 0.85 * u
    sp.use_endpoint_u = True
    sp.order_u = 4
    obj = bpy.data.objects.new("volute", curve)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    m = bpy.data.materials.new("vapeur")
    m.use_nodes = True
    n_, l = m.node_tree.nodes, m.node_tree.links
    em = n_.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*lin(225, 240, 255), 1)
    em.inputs["Strength"].default_value = 0.6 + glow
    tr = n_.new("ShaderNodeBsdfTransparent")
    mix = n_.new("ShaderNodeMixShader")
    grad = n_.new("ShaderNodeTexGradient")
    coord = n_.new("ShaderNodeTexCoord")
    sep = n_.new("ShaderNodeSeparateXYZ")
    mr = n_.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = height
    mr.inputs["To Min"].default_value = 0.55
    mr.inputs["To Max"].default_value = 1.0
    l.new(coord.outputs["Object"], sep.inputs["Vector"])
    l.new(sep.outputs["Z"], mr.inputs["Value"])
    l.new(mr.outputs["Result"], mix.inputs["Fac"])
    l.new(em.outputs["Emission"], mix.inputs[1])
    l.new(tr.outputs["BSDF"], mix.inputs[2])
    l.new(mix.outputs["Shader"], n_["Material Output"].inputs["Surface"])
    obj.data.materials.append(m)
    return obj


# ---------------------------------------------------------------- nuage
def cloud(location=(0, 0, 0), size=1.0, frown=0.0, seed=4):
    """Nuage en volume (boules fondues) avec les yeux de la goutte."""
    rnd = random.Random(seed)
    mb = bpy.data.metaballs.new("nuage")
    mb.resolution = 0.08
    mb.render_resolution = 0.05
    for k in range(24):
        e = mb.elements.new()
        x = rnd.uniform(-1.25, 1.25)
        e.co = (x, rnd.uniform(-0.35, 0.35), rnd.uniform(-0.15, 0.55) * (1 - abs(x) / 1.6))
        e.radius = rnd.uniform(0.5, 0.95) * (1.15 - abs(x) / 2.5)
    obj = bpy.data.objects.new("nuage", mb)
    bpy.context.collection.objects.link(obj)
    m = bpy.data.materials.new("nuage")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(250, 250, 255), 1)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Sheen Weight"].default_value = 0.5
    b.inputs["Subsurface Weight"].default_value = 0.6
    b.inputs["Subsurface Radius"].default_value = (0.8, 0.9, 1.0)
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 8.0
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    l.new(noise.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    obj.data.materials.append(m)
    obj.location = location
    obj.scale = (size, size, size)
    black = mat("pupille nuage", (0.01, 0.01, 0.015), rough=0.15, coat=1.0)
    spark = mat("reflet nuage", (1, 1, 1), emit=(1, 1, 1), strength=5)
    brow_m = mat("sourcil", lin(170, 185, 210), rough=0.6)
    for side in (-1, 1):
        ex, ey, ez = location[0] + side * 0.32 * size, location[1] - 0.95 * size, location[2] + 0.12 * size
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1 * size, location=(ex, ey, ez))
        smooth(bpy.context.object).data.materials.append(black)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03 * size, location=(ex - 0.03 * size, ey - 0.09 * size, ez + 0.04 * size))
        bpy.context.object.data.materials.append(spark)
        if frown:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.025 * size, depth=0.22 * size,
                                                location=(ex, ey - 0.02 * size, ez + 0.17 * size),
                                                rotation=(0, math.pi / 2 + side * 0.35 * frown, 0))
            smooth(bpy.context.object).data.materials.append(brow_m)
    return obj


# ---------------------------------------------------------------- pluie
def rain(area=(-4, 4, -2, 14), top=6.0, count=260, seed=5, water=None):
    rnd = random.Random(seed)
    water = water or water_material()
    drops = []
    for _ in range(count):
        x, y = rnd.uniform(area[0], area[1]), rnd.uniform(area[2], area[3])
        z = rnd.uniform(0.3, top)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, segments=12, ring_count=8, location=(x, y, z))
        d = smooth(bpy.context.object)
        d.scale = (1, 1, 3.5)
        d.data.materials.append(water)
        drops.append(d)
    return drops


# ---------------------------------------------------------------- fleur de verre
def glass_flower(location=(0, 0, 0), size=1.0, petals=6, openness=1.0, seed=0):
    rnd = random.Random(seed)
    glass = mat("pétale", lin(120, 180, 255), rough=0.05, trans=0.85, ior=1.4, coat=1.0)
    heart = mat("cœur", lin(255, 230, 150), emit=lin(255, 220, 140), strength=2.0)
    stem_m = mat("tige verte", lin(80, 170, 90), rough=0.4)
    h = 0.55 * size
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02 * size, depth=h, location=(location[0], location[1], location[2] + h / 2))
    smooth(bpy.context.object).data.materials.append(stem_m)
    top = (location[0], location[1], location[2] + h)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06 * size, location=top)
    smooth(bpy.context.object).data.materials.append(heart)
    tilt = math.radians(80 - 55 * openness)
    for k in range(petals):
        a = 2 * math.pi * k / petals + rnd.uniform(-0.1, 0.1)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1 * size, segments=32, ring_count=16)
        p = smooth(bpy.context.object)
        p.scale = (1.9, 0.9, 0.18)
        p.rotation_euler = (0, -tilt, a)
        p.location = (top[0] + math.cos(a) * 0.15 * size * math.cos(tilt), top[1] + math.sin(a) * 0.15 * size * math.cos(tilt),
                      top[2] + 0.15 * size * math.sin(tilt))
        p.data.materials.append(glass)


def ground_patch(height_fn, center=(0, 0), radius=2.5, res=60):
    """Surface invisible qui épouse le sol autour d'un point : support des grains de sable."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=res, y_subdivisions=res, size=radius * 2,
                                    location=(center[0], center[1], 0))
    patch = bpy.context.object
    for v in patch.data.vertices:
        v.co.z = height_fn(center[0] + v.co.x, center[1] + v.co.y) + 0.004
    return patch


def sand_grains(obj, count=30000, size=0.02, seed=1):
    """Grains de sable visibles (monde miniature, vue macro) répartis sur un objet."""
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=1, location=(0, 0, -50))
    grain = bpy.context.object
    grain.data.materials.append(mat("grain", lin(222, 160, 105), rough=0.85))
    mod = obj.modifiers.new("grains", "PARTICLE_SYSTEM")
    ps = mod.particle_system.settings
    ps.type = "HAIR"
    ps.count = count
    ps.use_advanced_hair = True
    ps.render_type = "OBJECT"
    ps.instance_object = grain
    ps.particle_size = size
    ps.size_random = 0.7
    ps.use_rotations = True
    ps.rotation_mode = "GLOB_X"
    ps.phase_factor_random = 2.0
    ps.use_emit_random = True
    mod.particle_system.seed = seed
    obj.show_instancer_for_render = False   # on voit les grains, pas le support
    grain.hide_render = False
    return grain
