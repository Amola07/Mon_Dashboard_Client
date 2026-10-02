"""Les 33 plans de l'épisode 12 en Blender (hologramme néon, sans personnages).
Chaque fonction construit la scène, la caméra et l'animation pour n images à 30 im/s."""
import math
import random

import bpy
from mathutils import Vector

from . import neon as N
from .neon import BLUE, BLUE_HI, RED, ORANGE, GOLD, COPPER

# (plan, début, fin) dans la voix d'origine — identique à montage.py
TIMES = {"01": (0.00, 3.10), "02": (3.10, 6.10), "03": (6.10, 9.30), "04": (9.30, 14.10), "05": (14.10, 18.10),
         "06": (18.10, 20.40), "07": (20.40, 24.60), "08": (24.60, 29.30), "09": (29.30, 32.90), "10": (32.90, 37.70),
         "11": (37.70, 42.00), "12": (42.00, 46.40), "13": (46.40, 49.20), "14": (49.20, 53.60), "15": (53.60, 57.30),
         "16": (57.30, 61.40), "17": (61.40, 65.70), "18": (65.70, 68.40), "19": (68.40, 72.80), "20": (72.80, 74.60),
         "21": (74.60, 79.00), "22": (79.00, 83.20), "23": (83.20, 88.20), "24": (88.20, 90.70), "25": (90.70, 94.00),
         "26": (94.00, 99.90), "27": (99.90, 103.10), "28": (103.10, 107.00), "29": (107.00, 110.00),
         "30": (110.00, 114.70), "31": (114.70, 117.60), "32": (117.60, 120.80), "33": (120.80, 125.23)}
PLANS = {}


def plan(num):
    def deco(f):
        PLANS[num] = f
        return f
    return deco


def rain(n_rays, x, y, z_top, z_bot, frames, length, mat, seed=5, fall=40):
    """Pluie de muons : segments fins qui tombent en boucle."""
    rnd = random.Random(seed)
    for i in range(n_rays):
        px, py = rnd.uniform(*x), rnd.uniform(*y)
        o = N.line([(0, 0, 0), (0, 0, length)], length * 0.004, mat)
        off = rnd.randint(0, fall)
        k = -off
        while k < frames + fall:
            o.location = (px, py, z_top)
            o.keyframe_insert("location", frame=k)
            o.location = (px, py, z_bot)
            o.keyframe_insert("location", frame=k + fall)
            k += fall + rnd.randint(0, 8)
        for fc in _fcurves(o):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def _fcurves(o):
    ad = o.animation_data
    if ad is None or ad.action is None:
        return []
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += list(cb.fcurves)
    return out


# ---------------------------------------------------------------- 01 — particules venues de l'espace
@plan("01")
def p01(n):
    R = 60.0
    earth = N.sphere((0, 0, -R), R, N.glass(tint=(0.002, 0.006, 0.02), rough=0.3), seg=96)
    # limbe lumineux : sphère légèrement plus grande, émission en fresnel
    m = bpy.data.materials.new("limbe"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.08
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*BLUE, 1)
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "POWER"; mul.inputs[1].default_value = 3.0
    s = nt.nodes.new("ShaderNodeMath"); s.operation = "MULTIPLY"; s.inputs[1].default_value = 25.0
    t = nt.nodes.new("ShaderNodeBsdfTransparent"); ad = nt.nodes.new("ShaderNodeAddShader"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(lw.outputs["Facing"], mul.inputs[0]); nt.links.new(mul.outputs[0], s.inputs[0]); nt.links.new(s.outputs[0], e.inputs[1])
    nt.links.new(e.outputs[0], ad.inputs[0]); nt.links.new(t.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], o.inputs[0])
    N.sphere((0, 0, -R), R * 1.012, m, seg=96)
    # le Nil : ligne de lumières sur la surface, du sud (Assouan) au delta
    nile = N.emit(BLUE_HI, 6)
    pts = []
    for i in range(40):
        u = i / 39
        yy = -9 + 16 * u + 0.6 * math.sin(u * 7)
        xx = 0.5 * math.sin(u * 4)
        zz = math.sqrt(R * R - xx * xx - yy * yy) - R + 0.03
        pts.append((xx, yy, zz))
    N.line(pts, 0.06, nile)
    city = N.emit((1.0, 0.75, 0.45), 8)
    for (xx, yy) in ((0.2, 6.5), (-0.6, 7.6), (0.9, 7.9), (0.3, -8.5)):
        N.sphere((xx, yy, math.sqrt(R * R - xx * xx - yy * yy) - R + 0.05), 0.15, city, seg=8)
    N.stars(700, 3000)
    rain(70, (-8, 8), (-6, 10), 40, -1, n, 3.0, N.emit(BLUE_HI, 9), fall=24)
    cam, tgt = N.camera(30, (0, -40, 22), (0, 4, 6))
    N.keys(cam, "location", [(1, (0, -40, 22)), (n, (0, -26, 12))])
    N.keys(tgt, "location", [(1, (0, 4, 8)), (n, (0, 3, 0))])


# ---------------------------------------------------------------- 02 — à travers la Grande Pyramide
@plan("02")
def p02(n):
    gl = N.glass()
    solid, edges, courses = N.pyramid(glass_mat=gl, courses=40)
    N.key_alpha(gl, [(1, 1.0), (int(n * 0.35), 1.0), (int(n * 0.85), 0.12)])
    im = N.emit(BLUE_HI, 0)
    N.interior(mat=im, r=0.5)
    N.key_strength(im, [(1, 0), (int(n * 0.4), 0), (int(n * 0.9), 6)])
    N.ground()
    N.stars(600, 3000)
    rain(90, (-110, 110), (-110, 110), 420, -30, n, 30, N.emit(BLUE_HI, 9), fall=26)
    cam, tgt = N.camera(28, (260, -330, 10), (0, 0, 55))
    N.keys(cam, "location", [(1, (260, -330, 10)), (n, (235, -300, 14))])


# ---------------------------------------------------------------- 03 — la carte des muons révèle une anomalie
@plan("03")
def p03(n):
    root = N.empty("holo", (0, 0, 0), (math.radians(90), 0, 0))     # coupe affichée face caméra (y→x, z→z)
    edge = N.emit(BLUE, 6)
    a, h = N.HALF, N.HEIGHT
    tri = N.line([(-a, 0, 0), (0, 0, h), (a, 0, 0)], 0.6, edge, cyclic=True)
    dim = N.emit(BLUE, 0.5)
    for k in range(1, 40):
        z = h * k / 40
        s = a * (1 - z / h)
        N.line([(-s, 0, z), (s, 0, z)], 0.25, dim)
    inside = N.emit(BLUE_HI, 3)
    gg0, gg1 = N.GG0, N.GG1
    N.line([(gg0.y, -0.5, gg0.z), (gg1.y, -0.5, gg1.z)], 0.9, inside)
    N.line([(8, -0.5, 43), (13.2, -0.5, 43), (13.2, -0.5, 48.8), (8, -0.5, 48.8)], 0.5, inside, cyclic=True)
    N.line([(-2.9, -0.5, 21.7), (2.9, -0.5, 21.7), (2.9, -0.5, 25.5), (0, -0.5, 27.9), (-2.9, -0.5, 25.5)], 0.5, inside, cyclic=True)
    red = N.emit(RED, 0)
    v0, v1 = N.VOID0, N.VOID1
    N.line([(v0.y, -1, v0.z), (v1.y, -1, v1.z)], 2.6, red)
    N.key_strength(red, [(1, 0), (int(n * 0.25), 0), (int(n * 0.7), 9)])
    # barre de balayage qui monte
    scan = N.line([(-a, -0.8, 0), (a, -0.8, 0)], 0.5, N.emit(BLUE_HI, 8))
    N.keys(scan, "location", [(1, (0, 0, 0)), (int(n * 0.6), (0, 0, h))])
    # plaque de détecteur sous la coupe
    det = N.emit(BLUE, 2)
    for i in range(-6, 7):
        N.line([(i * 6, -12, -14), (i * 6, 12, -14)], 0.3, det)
        N.line([(-36, i * 2, -14), (36, i * 2, -14)], 0.3, det)
    cam, tgt = N.camera(35, (40, -330, 60), (0, 0, 55))
    N.keys(cam, "location", [(1, (40, -330, 60)), (n, (20, -230, 52))])
    N.keys(tgt, "location", [(1, (0, 0, 55)), (n, (-6, 0, 44))])


# ---------------------------------------------------------------- 04 — un vide de 30 m au cœur de la pyramide
@plan("04")
def p04(n):
    gl = N.glass()
    N.key_alpha(gl, [(1, 0.15)])
    N.pyramid(glass_mat=gl, courses=0)
    N.interior(mat=N.emit(BLUE_HI, 5), r=0.35)
    red = N.emit(RED, 9)
    v = N.line([N.VOID0, N.VOID1], 2.2, red)
    N.draw(v, int(n * 0.1), int(n * 0.55))
    N.light(((N.VOID0 + N.VOID1) / 2) + Vector((3, 0, 0)), (1, 0.1, 0.05), 0)
    N.stars(400, 3000)
    cam, tgt = N.camera(30, (330, -40, 60), (0, -4, 50))
    N.keys(cam, "location", [(1, (330, -40, 60)), (int(n * 0.45), (330, -40, 60)), (n, (120, -14, 46))])
    N.keys(tgt, "location", [(1, (0, -4, 50)), (n, (0, -12, 44))])


# ---------------------------------------------------------------- 05 — personne ne l'a jamais ouvert
@plan("05")
def p05(n):
    N.blocks_wall(-6, 6, -3, 5, 0.0, bw=1.6, bh=1.0, edge=N.emit(BLUE, 0.5), face=N.glass(tint=(0.03, 0.04, 0.06), rough=0.55), seed=4)
    redl = N.emit(RED, 0)
    seam = N.line([(1.2, -0.01, 0.95), (2.6, -0.01, 0.95)], 0.02, redl)
    N.key_strength(redl, [(1, 2.5), (int(n * 0.55), 2.5), (int(n * 0.65), 9), (int(n * 0.75), 3), (n, 5)])
    rl = N.light((1.9, 0.6, 0.9), (1, 0.05, 0.03), 0)
    rl.data.keyframe_insert("energy", frame=1)
    rl.data.energy = 6; rl.data.keyframe_insert("energy", frame=int(n * 0.65))
    sp = N.spot((-5, -4, 1.6), (0.75, 0.85, 1.0), 900, angle_deg=14)
    tg = N.empty("visee", (-4, 0, 1.2))
    c = sp.constraints.new("TRACK_TO"); c.target = tg; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    N.keys(tg, "location", [(1, (-4.5, 0, 1.4)), (int(n * 0.6), (1.9, 0, 1.0)), (n, (1.9, 0, 0.95))])
    cam, tgt = N.camera(32, (-3, -7, 1.5), (0, 0, 1.0))
    N.keys(cam, "location", [(1, (-3, -7, 1.5)), (n, (0.8, -4.5, 1.2))])
    N.keys(tgt, "location", [(1, (-1.5, 0, 1.1)), (n, (1.9, 0, 0.95))])


# ---------------------------------------------------------------- pyramides de Gizeh (décor commun)
def giza(courses=40, gl=None):
    out = N.pyramid(glass_mat=gl or N.glass(), courses=courses)
    for (cx, cy, half, h, ang) in ((-180.0, 330.0, 107.5, 136.4, 0.0), (-310.0, 640.0, 51.5, 65.0, 0.0)):
        g = N.empty("p", (cx, cy, 0))
        a = half
        V = [(-a, -a, 0), (a, -a, 0), (a, a, 0), (-a, a, 0), (0, 0, h)]
        N.mesh(V, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)], N.glass(), g)
        em = N.emit(BLUE, 3)
        for i in range(4):
            N.line([V[i], V[4]], 0.3, em, g)
        N.line(V[:4], 0.3, em, g, cyclic=True)
    return out


# ---------------------------------------------------------------- 06 — tu crois qu'on connaît tout ?
@plan("06")
def p06(n):
    giza()
    N.ground(grid=40, extent=900)
    N.stars(900, 3000)
    cam, tgt = N.camera(24, (150, -300, 4), (0, 0, 70))
    N.keys(cam, "location", [(1, (150, -300, 4)), (n, (140, -280, 40))])
    N.keys(tgt, "location", [(1, (-10, 20, 75)), (n, (-10, 20, 85))])


# ---------------------------------------------------------------- 07 — 4 500 ans : le revêtement d'origine réapparaît
@plan("07")
def p07(n):
    solid, edges, courses = giza(courses=60)
    cmats = {c.data.materials[0] for c in courses}
    for m in cmats:
        N.key_strength(m, [(1, 1.0), (int(n * 0.2), 1.0), (int(n * 0.8), 0.05)])
    a, h = N.HALF + 0.3, N.HEIGHT + 0.3
    casing = N.reveal_emit((0.55, 0.7, 1.0), 0.07, "Z", "revetement")
    V = [(-a, -a, 0), (a, -a, 0), (a, a, 0), (-a, a, 0), (0, 0, h)]
    N.mesh(V, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], casing, name="revetement")
    N.key_reveal(casing, [(1, -1), (int(n * 0.15), -1), (int(n * 0.8), h - 9)])
    gold = N.emit(GOLD, 0)
    t = 9.0
    s = N.HALF * t / N.HEIGHT + 0.4
    cap = [(-s, -s, h - t), (s, -s, h - t), (s, s, h - t), (-s, s, h - t), (0, 0, h + 0.2)]
    N.mesh(cap, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], gold, name="pyramidion")
    N.key_strength(gold, [(1, 0), (int(n * 0.75), 0), (int(n * 0.9), 25)])
    N.light((40, -40, h + 10), (1, 0.7, 0.3), 0)
    N.ground(grid=40, extent=900)
    N.stars(900, 3000)
    cam, tgt = N.camera(26, (140, -280, 40), (-10, 20, 85))
    N.keys(cam, "location", [(1, (140, -280, 40)), (n, (120, -250, 50))])
    N.keys(tgt, "location", [(1, (-20, 40, 80)), (n, (0, 0, 95))])


# ---------------------------------------------------------------- 08 — 2,3 millions de blocs, 20 ans de chantier
@plan("08")
def p08(n):
    layers = 30
    edge = N.emit(BLUE, 4)
    face = N.glass()
    a, h = N.HALF, N.HEIGHT
    built0, built1 = 9, 21
    for k in range(layers):
        z0, z1 = h * k / layers * 0.85, h * (k + 1) / layers * 0.85
        s = a * (1 - z0 / h)
        b = N.box(-s, s, -s, s, z0, z1, face)
        lines = [N.line([(-s, -s, z1), (s, -s, z1), (s, s, z1), (-s, s, z1)], 0.3, edge, cyclic=True),
                 N.line([(-s, -s, z0), (-s, -s, z1)], 0.3, edge), N.line([(s, -s, z0), (s, -s, z1)], 0.3, edge),
                 N.line([(s, s, z0), (s, s, z1)], 0.3, edge), N.line([(-s, s, z0), (-s, s, z1)], 0.3, edge)]
        if k >= built1:
            for o in [b] + lines:
                o.hide_render = True
        elif k >= built0:
            f = 1 + int((k - built0 + 1) / (built1 - built0) * (n - 8))
            for o in [b] + lines:
                N.visible(o, [(1, False), (f, True)])
    # rampe de chantier contre la face sud-est
    rm = N.emit(ORANGE, 1.2)
    N.line([(a + 40, -160, 0), (a - 5, -60, 40)], 0.6, rm)
    N.line([(a + 52, -160, 0), (a + 7, -60, 40)], 0.6, rm)
    # blocs en attente et Nil au loin
    bm = N.emit(BLUE, 1.5)
    rnd = random.Random(2)
    for i in range(60):
        x, y = rnd.uniform(160, 320), rnd.uniform(-320, -140)
        N.outline_box(x, x + 3, y, y + 3, 0, 2.5, 0.12, bm)
    N.line([(-2000, -900, 0.5), (2000, -1100, 0.5)], 3, N.emit(BLUE_HI, 4))
    N.line([(-3000, 2500, 0), (3000, 2500, 0)], 12, N.emit(ORANGE, 6))      # dernière lueur à l'horizon
    N.ground(grid=20, extent=700)
    N.stars(400, 3000, zmin=0.25)
    cam, tgt = N.camera(22, (300, -300, 150), (20, -20, 30))
    N.keys(cam, "location", [(1, (300, -300, 150)), (n, (370, -170, 140))])


# ---------------------------------------------------------------- 09 — un bloc toutes les deux minutes, jour et nuit
@plan("09")
def p09(n):
    face = N.glass()
    edge = N.emit(BLUE, 6)
    grp = N.empty("traineau")
    N.box(-0.65, 0.65, -0.75, 0.75, 0.25, 1.25, face, grp)
    N.outline_box(-0.65, 0.65, -0.75, 0.75, 0.25, 1.25, 0.02, edge, grp)
    wood = N.emit(BLUE, 3)
    for x in (-0.5, 0.5):
        N.line([(x, -1.0, 0.05), (x, 1.0, 0.05), (x, 1.25, 0.25)], 0.04, wood, grp)
        N.line([(x, -1.0, 0.05), (x, -1.0, 0.25)], 0.03, wood, grp)
    for y in (-0.6, 0.0, 0.6):
        N.line([(-0.5, y, 0.22), (0.5, y, 0.22)], 0.03, wood, grp)
    rope = N.emit(BLUE_HI, 3)
    for x in (-0.4, -0.15, 0.15, 0.4):
        N.line([(x, 1.2, 0.3), (x * 3, 12, 1.1)], 0.015, rope, grp)
    N.keys(grp, "location", [(1, (0, -1.2, 0)), (n, (0, 1.2, 0))])
    water = N.emit((0.3, 0.85, 1.0), 1.2)
    wl = N.line([(0, -6, 0.01), (0, 14, 0.01)], 0.5, water)
    wl.scale = (1, 1, 0.05)
    N.draw(wl, 1, n, 0.3, 1.0)
    N.ground(400, grid=2, extent=30)
    sun_m = N.emit(ORANGE, 8)
    sun = N.sphere((0, 300, 30), 14, sun_m)
    N.keys(sun, "location", [(1, (40, 300, 30)), (n, (70, 300, -20))])
    moon_m = N.emit((0.75, 0.85, 1.0), 0)
    N.sphere((-60, 300, 90), 8, moon_m)
    N.key_strength(moon_m, [(1, 0), (int(n * 0.5), 0), (n, 6)])
    N.key_strength(sun_m, [(1, 8), (int(n * 0.8), 0)])
    for x in (-3, 3):
        N.flame((x, 3, 2.2), 2.0, energy=0)
    for o in [ob for ob in bpy.data.objects if ob.type == "LIGHT"]:
        o.data.energy = 0; o.data.keyframe_insert("energy", frame=int(n * 0.5))
        o.data.energy = 140; o.data.keyframe_insert("energy", frame=int(n * 0.8))
    st = N.stars(600, 1500, zmin=0.1)
    cam, tgt = N.camera(24, (-3.6, -3.0, 1.0), (0, 0.5, 0.7))
    N.keys(cam, "location", [(1, (-3.6, -3.0, 1.0)), (n, (-3.4, -1.2, 1.1))])
    N.keys(tgt, "location", [(1, (0, -0.5, 0.7)), (n, (0, 1.5, 0.7))])


# ---------------------------------------------------------------- 10 — à plus de 100 m de haut
@plan("10")
def p10(n):
    zt = 118.0
    a, h = N.HALF, N.HEIGHT
    s = a * (1 - zt / h)
    gl = N.glass()
    V = [(-a, -a, 0), (a, -a, 0), (a, a, 0), (-a, a, 0), (-s, -s, zt), (s, -s, zt), (s, s, zt), (-s, s, zt)]
    N.mesh(V, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)], gl)
    e = N.emit(BLUE, 6)
    for i in range(4):
        N.line([V[i], V[i + 4]], 0.3, e)
    N.line(V[4:], 0.25, e, cyclic=True)
    cm = N.emit(BLUE, 0.9)
    for k in range(1, 36):
        z = zt * k / 36
        ss = a * (1 - z / h) + 0.05
        N.line([(-ss, -ss, z), (ss, -ss, z), (ss, ss, z), (-ss, ss, z)], 0.1, cm, cyclic=True)
    # petits blocs posés sur la plate-forme et un bloc qui se soulève au bord
    bm = N.emit(BLUE_HI, 4)
    for (x, y) in ((-6, -4), (-3, 3), (2, -6), (5, 4)):
        N.box(x, x + 1.4, y, y + 1.4, zt, zt + 1.0, gl)
        N.outline_box(x, x + 1.4, y, y + 1.4, zt, zt + 1.0, 0.03, bm)
    lift = N.empty("bloc")
    N.box(-0.7, 0.7, -0.7, 0.7, 0, 1.0, gl, lift)
    N.outline_box(-0.7, 0.7, -0.7, 0.7, 0, 1.0, 0.035, N.emit(BLUE_HI, 8), lift)
    N.keys(lift, "location", [(1, (0, -s + 0.4, zt - 0.9)), (int(n * 0.35), (0, -s + 0.6, zt + 0.05))])
    lev = N.emit(ORANGE, 3)
    for x in (-0.5, 0.5):
        N.line([(x, -s - 1.2, zt - 1.6), (x, -s + 1.5, zt + 0.2)], 0.05, lev)
    N.flame((-2.5, -s + 1.0, zt + 1.2), 3.0)
    N.ground(grid=40, extent=900)
    N.stars(800, 3000)
    cam, tgt = N.camera(24, (6, -s - 6, zt + 3), (0, -s + 1, zt))
    N.keys(cam, "location", [(1, (9, -s - 9, zt + 4)), (int(n * 0.35), (9, -s - 10, zt + 4)), (n, (160, -330, 150))])
    N.keys(tgt, "location", [(1, (0, -s + 1, zt)), (int(n * 0.35), (0, -s + 1, zt)), (n, (0, 0, 70))])


# ---------------------------------------------------------------- Grande Galerie (plans 11 et 30)
SLOPE = math.radians(26.3)
GL = 47.0


def gallery():
    root = N.empty("galerie", (0, 0, 0), (SLOPE, 0, 0))
    blue, dim, slot = N.emit(BLUE, 5.0), N.emit((0.05, 0.22, 1.0), 0.45), N.emit((0.05, 0.2, 1.0), 0.25)
    g = N.glass(rough=0.12)
    N.box(-0.52, 0.52, 0, GL, -0.1, 0, g, root)
    for s in (-1, 1):
        N.box(s * 0.52, s * 1.03, 0, GL, -0.1, 0.6, g, root)
        for x in (0.52, 1.03):
            N.line([(s * x, 0, 0.6), (s * x, GL, 0.6)], 0.008, blue, root)
        N.line([(s * 0.52, 0, 0.0), (s * 0.52, GL, 0.0)], 0.006, dim, root)
        y = 1.0
        while y < GL - 1:
            N.box(s * 0.62, s * 0.92, y, y + 0.2, 0.595, 0.605, slot, root)
            y += 1.75
    courses = [(0.6, 2.9, 1.03)] + [(2.9 + 0.8 * k, 2.9 + 0.8 * (k + 1), 1.03 - 0.076 * (k + 1)) for k in range(7)]
    for s in (-1, 1):
        for i, (z0, z1, xx) in enumerate(courses):
            N.box(s * xx, s * (xx + 0.6), 0, GL, z0, z1, g, root)
            N.line([(s * xx, 0, z1), (s * xx, GL, z1)], 0.009, blue, root)
            N.line([(s * xx, 0, z0), (s * xx, GL, z0)], 0.006, dim, root)
            y = 0.4 + 0.75 * (i % 2)
            while y < GL:
                N.line([(s * xx, y, z0), (s * xx, y, z1)], 0.004, dim, root)
                y += 1.5
    top = courses[-1][1]
    N.box(-0.6, 0.6, 0, GL, top, top + 0.3, g, root)
    N.box(-1.03, 1.03, GL - 1.6, GL, -0.1, 0.9, g, root)
    N.line([(-1.03, GL - 1.6, 0.9), (1.03, GL - 1.6, 0.9)], 0.01, blue, root)
    N.box(-1.03, -0.525, GL, GL + 0.5, 0.9, top, g, root)
    N.box(0.525, 1.03, GL, GL + 0.5, 0.9, top, g, root)
    N.box(-0.525, 0.525, GL, GL + 0.5, 2.0, top, g, root)
    N.box(-0.525, 0.525, GL + 0.45, GL + 0.5, 0.9, 2.0, N.emit((0, 0, 0), 0), root)
    N.line([(-0.525, GL, 0.9), (-0.525, GL, 2.0), (0.525, GL, 2.0), (0.525, GL, 0.9)], 0.012, blue, root)
    N.box(-0.82, -0.68, GL - 0.67, GL - 0.53, 0.9, 0.95, g, root)
    N.flame((-0.75, GL - 0.6, 0.98), 1.0, root, energy=200)
    return root, top


@plan("11")
def p11(n):
    root, top = gallery()
    cam, tgt = N.camera(17, (0, 0, 0), (0, 0, 0))
    cam.parent = root; tgt.parent = root
    tgt.location = (0, GL + 0.5, 4.2)
    N.keys(cam, "location", [(1, (-0.05, 22.0, 1.75)), (n, (0.04, 37.5, 1.95))])


# ---------------------------------------------------------------- chambre du roi (plans 12, 15)
KW, KD, KH = 10.47, 5.23, 5.84          # est-ouest, nord-sud, hauteur


def kings_chamber(beam_gold=None):
    g = N.glass(tint=(0.012, 0.004, 0.006), rough=0.1, name="granit")
    edge, dim = N.emit(BLUE, 4), N.emit(BLUE, 0.6)
    x0, x1, y0, y1 = -KW / 2, KW / 2, -KD / 2, KD / 2
    N.box(x0 - 1, x1 + 1, y0 - 1, y1 + 1, -0.5, 0, g)                       # sol
    N.box(x0 - 1, x0, y0, y1, 0, KH, g); N.box(x1, x1 + 1, y0, y1, 0, KH, g)
    N.box(x0, x1, y0 - 1, y0, 0, KH, g); N.box(x0, x1, y1, y1 + 1, 0, KH, g)
    for (p, u) in (((x0, y0), (1, 0)), ((x1, y0), (0, 1)), ((x1, y1), (-1, 0)), ((x0, y1), (0, -1))):
        pass
    N.line([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], 0.02, edge, cyclic=True)
    N.line([(x0, y0, KH), (x1, y0, KH), (x1, y1, KH), (x0, y1, KH)], 0.02, edge, cyclic=True)
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        N.line([(x, y, 0), (x, y, KH)], 0.02, edge)
    # joints verticaux des blocs de granit
    rnd = random.Random(8)
    for k in range(1, 5):
        z0, z1 = KH * (k - 1) / 5, KH * k / 5
        x = x0 + rnd.uniform(0.5, 1.5)
        while x < x1 - 0.3:
            N.line([(x, y1 - 0.01, z0), (x, y1 - 0.01, z1)], 0.006, dim)
            N.line([(x, y0 + 0.01, z0), (x, y0 + 0.01, z1)], 0.006, dim)
            x += rnd.uniform(1.4, 2.6)
        y = y0 + rnd.uniform(0.6, 1.4)
        while y < y1 - 0.3:
            N.line([(x0 + 0.01, y, z0), (x0 + 0.01, y, z1)], 0.006, dim)
            N.line([(x1 - 0.01, y, z0), (x1 - 0.01, y, z1)], 0.006, dim)
            y += rnd.uniform(1.2, 2.2)
    # cinq assises de granit sur les murs
    for k in range(1, 5):
        z = KH * k / 5
        N.line([(x0, y0 + 0.01, z), (x1, y0 + 0.01, z), (x1 - 0.01, y1, z), (x0 + 0.01, y1, z)], 0.008, dim)
    # neuf poutres du plafond, posées nord-sud
    beams = []
    w = KW / 9
    for i in range(9):
        bx = x0 + i * w
        mat = beam_gold if (beam_gold is not None and i == 4) else edge
        N.box(bx + 0.01, bx + w - 0.01, y0 - 1, y1 + 1, KH, KH + 1.6, g)
        beams.append(N.line([(bx, y0, KH - 0.005), (bx, y1, KH - 0.005)], 0.018, mat))
        beams.append(N.line([(bx + w, y0, KH - 0.005), (bx + w, y1, KH - 0.005)], 0.018, mat))
    # porte nord-est vers l'antichambre
    N.line([(x1 - 1.6, y0 + 0.01, 0), (x1 - 1.6, y0 + 0.01, 1.11), (x1 - 0.55, y0 + 0.01, 1.11), (x1 - 0.55, y0 + 0.01, 0)], 0.02, edge)
    return g, edge


def sarcophagus(loc=(0, 0, 0), edge=None, parent=None):
    g = N.glass(tint=(0.012, 0.004, 0.006), rough=0.1, name="granit_s")
    edge = edge or N.emit(BLUE_HI, 6)
    grp = N.empty("sarcophage", loc)
    if parent is not None:
        grp.parent = parent
    L, W, H, t = 2.28, 0.98, 1.05, 0.15
    N.box(-L / 2, L / 2, -W / 2, W / 2, 0, t, g, grp)
    for (a0, a1, b0, b1) in ((-L / 2, L / 2, -W / 2, -W / 2 + t), (-L / 2, L / 2, W / 2 - t, W / 2),
                             (-L / 2, -L / 2 + t, -W / 2, W / 2), (L / 2 - t, L / 2, -W / 2, W / 2)):
        N.box(a0, a1, b0, b1, 0, H, g, grp)
    lines = N.outline_box(-L / 2, L / 2, -W / 2, W / 2, 0, H, 0.012, edge, grp)
    lines.append(N.line([(-L / 2 + t, -W / 2 + t, H), (L / 2 - t, -W / 2 + t, H), (L / 2 - t, W / 2 - t, H),
                         (-L / 2 + t, W / 2 - t, H)], 0.008, edge, grp, cyclic=True))
    return grp, lines


@plan("12")
def p12(n):
    gold = N.emit(BLUE, 4)
    kings_chamber(beam_gold=gold)
    gs = N.strength_socket(gold)
    # la poutre centrale passe du bleu à l'or
    col = next(nd for nd in gold.node_tree.nodes if nd.type == "EMISSION").inputs[0]
    col.default_value = (*BLUE, 1); col.keyframe_insert("default_value", frame=int(n * 0.45))
    col.default_value = (*GOLD, 1); col.keyframe_insert("default_value", frame=int(n * 0.7))
    N.key_strength(gold, [(int(n * 0.45), 4), (int(n * 0.7), 12)])
    N.flame((-4.6, 2.0, 0.1), 2.0, energy=260, frames=n)
    sp = N.spot((-4.6, 2.0, 0.6), (1.0, 0.55, 0.2), 0, angle_deg=25)
    tg = N.empty("t", (-4, 0, KH))
    c = sp.constraints.new("TRACK_TO"); c.target = tg; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    sp.data.keyframe_insert("energy", frame=1); sp.data.energy = 1500; sp.data.keyframe_insert("energy", frame=10)
    N.keys(tg, "location", [(1, (-4.5, 0, KH)), (n, (4.5, 0, KH))])
    cam, tgt = N.camera(14, (-3.8, -1.6, 0.6), (-2.0, 0.0, KH))
    N.keys(tgt, "location", [(1, (-2.5, 0.3, KH * 0.6)), (n, (2.5, 0.2, KH))])


# ---------------------------------------------------------------- 13 — une poutre de granit descend le Nil
@plan("13")
def p13(n):
    water = N.glass(tint=(0.002, 0.006, 0.016), rough=0.04, name="eau")
    N.ground(6000, 0, water)
    bank = N.emit(BLUE, 3)
    for y in (-40, 40):
        N.line([(-3000, y, 0.3), (3000, y, 0.3)], 0.25, bank)
    rnd = random.Random(9)
    palm = N.emit(BLUE, 2.5)
    for i in range(70):
        x = rnd.uniform(-600, 600); y = rnd.choice((-1, 1)) * rnd.uniform(46, 120); h = rnd.uniform(8, 14)
        lean = rnd.uniform(-1.5, 1.5)
        N.line([(x, y, 0), (x + lean, y, h)], 0.12, palm)
        for k in range(7):
            ang = k / 7 * 2 * math.pi
            N.line([(x + lean, y, h), (x + lean + 3.2 * math.cos(ang), y + 3.2 * math.sin(ang), h - 1.6)], 0.06, palm)
    boat = N.empty("barge")
    hull = N.emit(BLUE_HI, 5)
    L, W = 30.0, 9.0
    pts = [(-L / 2, 0, 2.2), (-L / 2 + 4, -W / 2, 1.2), (L / 2 - 4, -W / 2, 1.2), (L / 2, 0, 2.2), (L / 2 - 4, W / 2, 1.2), (-L / 2 + 4, W / 2, 1.2)]
    N.line(pts, 0.1, hull, boat, cyclic=True)
    N.line([(-L / 2 + 4, -W / 2, 1.2), (-L / 2 + 5, -W / 2 + 1, -0.2), (L / 2 - 5, -W / 2 + 1, -0.2), (L / 2 - 4, -W / 2, 1.2)], 0.06, hull, boat)
    N.line([(-L / 2 + 4, W / 2, 1.2), (-L / 2 + 5, W / 2 - 1, -0.2), (L / 2 - 5, W / 2 - 1, -0.2), (L / 2 - 4, W / 2, 1.2)], 0.06, hull, boat)
    N.mesh([(p[0], p[1], 1.0) for p in pts], [tuple(range(6))], N.glass(), boat)
    for i in range(-5, 6):
        N.line([(i * 2.2, -W / 2, 1.2), (i * 2.2 - 1.2, -W / 2 - 3.5, -0.2)], 0.05, palm, boat)
        N.line([(i * 2.2, W / 2, 1.2), (i * 2.2 - 1.2, W / 2 + 3.5, -0.2)], 0.05, palm, boat)
    gr = N.glass(tint=(0.02, 0.004, 0.004), rough=0.1, name="granit")
    N.box(-4.0, 4.0, -0.75, 0.75, 1.2, 3.0, gr, boat)
    N.outline_box(-4.0, 4.0, -0.75, 0.75, 1.2, 3.0, 0.06, N.emit(COPPER, 8), boat)
    N.keys(boat, "location", [(1, (-25, 0, 0)), (n, (5, 0, 0))])
    N.line([(-6000, 3000, 0), (6000, 3000, 0)], 40, N.emit(ORANGE, 5))
    N.stars(500, 4000, zmin=0.2)
    cam, tgt = N.camera(26, (-28, -24, 6), (-22, 0, 2))
    N.keys(cam, "location", [(1, (-28, -24, 6)), (n, (0, -22, 6))])
    N.keys(tgt, "location", [(1, (-24, 0, 2)), (n, (4, 0, 2))])


# ---------------------------------------------------------------- 14 — hissées à 40 m, sans poulie ni roue
@plan("14")
def p14(n):
    ang = math.radians(18)
    root = N.empty("rampe", (0, 0, 0), (ang, 0, 0))
    g = N.glass()
    N.box(-5, 5, -40, 80, -2, 0, g, root)
    side = N.emit(ORANGE, 1.4)
    for x in (-5, 5):
        N.line([(x, -40, 0), (x, 80, 0)], 0.06, side, root)
    k = -40
    while k < 80:
        N.line([(-5, k, 0.01), (5, k, 0.01)], 0.015, N.emit(BLUE, 0.4), root)
        k += 2.5
    sled = N.empty("traineau"); sled.parent = root
    gr = N.glass(tint=(0.02, 0.004, 0.004), rough=0.1, name="granit")
    N.box(-1.0, 1.0, -4.0, 4.0, 0.35, 2.1, gr, sled)
    N.outline_box(-1.0, 1.0, -4.0, 4.0, 0.35, 2.1, 0.04, N.emit(COPPER, 8), sled)
    wood = N.emit(BLUE, 4)
    for x in (-0.8, 0.8):
        N.line([(x, -4.4, 0.05), (x, 4.4, 0.05), (x, 4.9, 0.4)], 0.07, wood, sled)
    rope = N.emit(BLUE_HI, 1.0)
    for i in range(12):
        x = -0.9 + i * 1.8 / 11
        N.line([(x, 4.6, 0.4), (x * 3.5, 60, 1.2)], 0.02, rope, sled)
    N.keys(sled, "location", [(1, (0, 0, 0)), (int(n * 0.3), (0, 0.15, 0)), (int(n * 0.55), (0, 0.15, 0)), (n, (0, 0.9, 0))])
    # pyramide en construction à côté
    edge = N.emit(BLUE, 3)
    for kk in range(10):
        z0 = kk * 4.5 - 2
        s = 60 - kk * 4
        N.box(-s - 70, s - 70, -30, 60, z0, z0 + 4.5, g)
        N.line([(-s - 70 + 2 * s, -30, z0 + 4.5), (-s - 70 + 2 * s, 60, z0 + 4.5)], 0.06, edge)
    for y in range(-30, 80, 15):
        N.flame((6.5, y * math.cos(ang), y * math.sin(ang) + 1.4), 3.0, energy=220, frames=n)
    N.ground(3000, -15)
    N.stars(700, 3000)
    cam, tgt = N.camera(24, (16, -14, 3), (0, 3, 2))
    N.keys(cam, "location", [(1, (16, -14, 3)), (n, (14, -10, 6))])
    N.keys(tgt, "location", [(1, (0, 2, 2)), (n, (0, 6, 4))])


# ---------------------------------------------------------------- 15 — un sarcophage
@plan("15")
def p15(n):
    kings_chamber()
    sarcophagus((-KW / 2 + 1.8, 0, 0))
    N.flame((-1.0, 1.9, 0.1), 2.0, energy=200, frames=n)
    sp = N.spot((-1.0, 1.9, 1.5), (1.0, 0.55, 0.2), 1200, angle_deg=30)
    N.aim(sp, (-KW / 2 + 1.8, 0, 0.6))
    cam, tgt = N.camera(28, (3.0, -1.8, 1.7), (-KW / 2 + 1.8, 0, 0.6))
    N.keys(cam, "location", [(1, (3.0, -1.8, 1.7)), (n, (-0.5, -1.0, 1.5))])


# ---------------------------------------------------------------- 16 — trop large pour les couloirs
@plan("16")
def p16(n):
    blue = N.emit(BLUE, 5)
    x0, x1, y0, y1 = -KW / 2, KW / 2, -KD / 2, KD / 2
    N.outline_box(x0, x1, y0, y1, 0, KH, 0.025, blue)
    # couloir ascendant (1,05 m de large, 1,2 m de haut) qui arrive par le nord
    cor = N.emit(BLUE_HI, 5)
    cx = x1 - 1.1
    N.outline_box(cx - 0.525, cx + 0.525, y0 - 9, y0, 0, 1.2, 0.02, cor)
    N.box(x0, x1, y0 - 0.02, y0, 0, KH, N.glass())
    hole = N.box(cx - 0.525, cx + 0.525, y0 - 0.05, y0 + 0.03, 0, 1.2, N.emit((0, 0, 0), 0))
    s_edge = N.emit(BLUE_HI, 6)
    grp, lines = sarcophagus((x0 + 2.2, 0, 0), s_edge)
    red = N.emit(RED, 0)
    _, rl = sarcophagus((0, 0, 0), red, grp)
    for o in [ob for ob in grp.children if ob.type == "MESH"]:
        pass
    N.keys(grp, "location", [(1, (x0 + 2.2, 0, 0)), (int(n * 0.3), (cx, 0.2, 0))])
    N.keys(grp, "rotation_euler", [(1, (0, 0, 0)), (int(n * 0.3), (0, 0, math.radians(90)))])
    N.keys(grp, "location", [(int(n * 0.3), (cx, 0.2, 0)), (int(n * 0.6), (cx, y0 + 1.0, 0))])
    N.key_strength(red, [(1, 0), (int(n * 0.58), 0), (int(n * 0.66), 12)])
    N.key_strength(s_edge, [(int(n * 0.58), 6), (int(n * 0.66), 0.5)])
    N.stars(300, 400)
    cam, tgt = N.camera(24, (x1 + 2.5, y0 - 5.5, 3.6), (cx - 1.2, y0 + 0.8, 0.4))


# ---------------------------------------------------------------- 17 — posé pendant la construction, puis muré
@plan("17")
def p17(n):
    g = N.glass(tint=(0.012, 0.004, 0.006), rough=0.1, name="granit")
    edge = N.emit(BLUE, 4)
    N.box(-12, 12, -10, 10, -1, 0, N.glass())
    N.line([(-12, -10, 0), (12, -10, 0), (12, 10, 0), (-12, 10, 0)], 0.04, N.emit(BLUE, 2), cyclic=True)
    sarcophagus((-KW / 2 + 1.8, 0, 0))
    x0, x1, y0, y1 = -KW / 2, KW / 2, -KD / 2, KD / 2
    walls = [(x0 - 1, x0, y0 - 1, y1 + 1), (x1, x1 + 1, y0 - 1, y1 + 1), (x0, x1, y0 - 1, y0), (x0, x1, y1, y1 + 1)]
    f0, f1 = int(n * 0.2), int(n * 0.75)
    for i, (a0, a1, b0, b1) in enumerate(walls):
        w = N.empty("mur", (0, 0, 0))
        N.box(a0, a1, b0, b1, 0, KH, g, w)
        for k in range(1, 6):
            z = KH * k / 5
            N.line([(a0, b0 - 0.01, z), (a1, b0 - 0.01, z)], 0.015, N.emit(BLUE, 0.8), w)
        N.outline_box(a0, a1, b0, b1, 0, KH, 0.02, edge, w)
        N.keys(w, "scale", [(1, (1, 1, 0.001)), (f0 + i * 3, (1, 1, 0.001)), (f1, (1, 1, 1))])
    roof = N.empty("toit", (0, 0, 30))
    for i in range(9):
        bx = x0 + i * KW / 9
        N.box(bx, bx + KW / 9 - 0.02, y0 - 1, y1 + 1, KH, KH + 1.6, g, roof)
        N.outline_box(bx, bx + KW / 9 - 0.02, y0 - 1, y1 + 1, KH, KH + 1.6, 0.015, edge, roof)
    N.keys(roof, "location", [(1, (0, 0, 30)), (f1 - 4, (0, 0, 30)), (n - 4, (0, 0, 0))])
    N.flame((-3.0, 2.0, 0.1), 2.0, energy=180, frames=n)
    N.stars(700, 2000)
    cam, tgt = N.camera(22, (12, -14, 13), (-2, 0, 1.5))
    N.keys(cam, "location", [(1, (12, -14, 13)), (n, (10, -12, 10))])


# ---------------------------------------------------------------- 18 — le corps du pharaon ? jamais retrouvé
@plan("18")
def p18(n):
    grp, _ = sarcophagus((0, 0, 0))
    gold = N.emit(GOLD, 9)
    # silhouette du cercueil momiforme (vue de dessus) : tête ronde, épaules, pieds
    pts = []
    prof = [(-0.95, 0.10), (-0.9, 0.16), (-0.75, 0.2), (-0.45, 0.22), (-0.1, 0.24), (0.15, 0.26), (0.3, 0.24),
            (0.42, 0.18), (0.48, 0.2), (0.62, 0.22), (0.78, 0.19), (0.88, 0.12), (0.92, 0.0)]
    for x, w in prof:
        pts.append((x, -w, 0.5))
    for x, w in reversed(prof[:-1]):
        pts.append((x, w, 0.5))
    mum = N.line(pts, 0.012, gold, cyclic=True)
    N.line([(0.62, -0.1, 0.5), (0.62, 0.1, 0.5)], 0.008, gold)
    N.line([(0.3, -0.24, 0.5), (-0.1, 0.0, 0.5), (0.3, 0.24, 0.5)], 0.008, gold)
    N.key_strength(gold, [(1, 9), (int(n * 0.3), 9), (int(n * 0.9), 0)])
    dust = N.emit(GOLD, 6)
    rnd = random.Random(4)
    for i in range(40):
        x, y = rnd.uniform(-0.9, 0.9), rnd.uniform(-0.22, 0.22)
        s = N.sphere((x, y, 0.5), 0.006, dust, seg=6)
        N.keys(s, "location", [(int(n * 0.3), (x, y, 0.5)), (n, (x + rnd.uniform(-0.3, 0.3), y + rnd.uniform(-0.3, 0.3), 0.5 + rnd.uniform(0.6, 1.4)))])
    N.key_strength(dust, [(1, 0), (int(n * 0.3), 0), (int(n * 0.5), 6), (n, 0)])
    N.flame((1.6, 0.9, 0.0), 1.5, energy=80, frames=n)
    cam, tgt = N.camera(30, (0.6, -2.0, 3.4), (0, 0, 0.4))
    N.keys(cam, "location", [(1, (0.6, -2.0, 3.4)), (n, (0.4, -1.5, 3.0))])


# ---------------------------------------------------------------- chambre de la reine et conduits (19-23)
QW, QD = 5.23, 5.75
SH = math.radians(39.6)


def queens_chamber():
    g = N.glass()
    edge, dim = N.emit(BLUE, 4), N.emit(BLUE, 0.6)
    x0, x1, y0, y1 = -QW / 2, QW / 2, -QD / 2, QD / 2
    wall_h, peak = 4.7, 6.2
    N.box(x0 - 1, x1 + 1, y0 - 1, y1 + 1, -0.5, 0, g)
    for (a0, a1, b0, b1) in ((x0 - 1, x0, y0, y1), (x1, x1 + 1, y0, y1)):
        N.box(a0, a1, b0, b1, 0, wall_h, g)
    # pignons nord et sud, troués par l'ouverture des conduits
    for yy, d in ((y0, -1), (y1, 1)):
        verts = [(x0, yy, 0), (x1, yy, 0), (x1, yy, wall_h), (0, yy, peak), (x0, yy, wall_h)]
        N.mesh(verts, [(0, 1, 2, 3, 4)], g)
        N.line(verts, 0.02, edge, cyclic=True)
    # toit à deux pentes
    for s in (-1, 1):
        N.mesh([(s * QW / 2, y0, wall_h), (0, y0, peak), (0, y1, peak), (s * QW / 2, y1, wall_h)], [(0, 1, 2, 3)], g)
        k = 0
        while k <= QD:
            N.line([(s * QW / 2, y0 + k, wall_h), (0, y0 + k, peak)], 0.01, dim)
            k += 1.15
    N.line([(0, y0, peak), (0, y1, peak)], 0.02, edge)
    for xx in (x0, x1):
        N.line([(xx, y0, 0), (xx, y1, 0)], 0.02, edge)
        N.line([(xx, y0, wall_h), (xx, y1, wall_h)], 0.02, edge)
    # niche en encorbellement dans le mur est
    nm = N.emit(BLUE_HI, 3)
    steps = [(1.57, 0, 1.6), (1.3, 1.6, 2.4), (1.04, 2.4, 3.1), (0.78, 3.1, 3.8), (0.52, 3.8, 4.5)]
    for w, z0, z1 in steps:
        N.line([(x1 - 0.01, -w / 2, z0), (x1 - 0.01, -w / 2, z1), (x1 - 0.01, w / 2, z1), (x1 - 0.01, w / 2, z0)], 0.012, nm)
    # ouvertures des conduits (20 × 20 cm) sur les murs nord et sud
    holes = []
    for yy in (y0, y1):
        holes.append(N.rect((-0.1, yy + (0.01 if yy < 0 else -0.01), 1.4), (0.2, 0, 0), (0, 0, 0.2), 0.006, N.emit(BLUE_HI, 8)))
        N.box(-0.1, 0.1, yy - 0.02, yy + 0.02, 1.4, 1.6, N.emit((0, 0, 0), 0))
    return holes


def shaft(parent, length=60.0, door_at=None):
    """Conduit de 20 × 20 cm montant à 39,6° (dans le repère du parent : y le long du conduit)."""
    g = N.glass(rough=0.2)
    dim = N.emit(BLUE, 0.9)
    s = 0.1
    for (a0, a1, b0, b1) in ((-s - 0.3, s + 0.3, -s - 0.3, -s), (-s - 0.3, s + 0.3, s, s + 0.3), (-s - 0.3, -s, -s, s), (s, s + 0.3, -s, s)):
        N.box(a0, a1, 0, length, b0, b1, g, parent)
    for (x, z) in ((-s, -s), (s, -s), (s, s), (-s, s)):
        N.line([(x, 0, z), (x, length, z)], 0.0025, N.emit(BLUE, 2.5), parent)
    y = 0.6
    while y < length:
        N.line([(-s, y, -s), (s, y, -s), (s, y, s), (-s, y, s)], 0.0015, dim, parent, cyclic=True)
        y += 1.3


@plan("19")
def p19(n):
    holes = queens_chamber()
    sp = N.spot((0.8, 0.5, 1.6), (0.8, 0.88, 1.0), 300, angle_deg=12)
    tg = N.empty("t", (2.0, 0, 3.0))
    c = sp.constraints.new("TRACK_TO"); c.target = tg; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    N.keys(tg, "location", [(1, (QW / 2, 0, 2.5)), (int(n * 0.45), (0, QD / 2, 1.5))])
    cam, tgt = N.camera(16, (-1.6, -2.4, 1.7), (0.5, 0.0, 2.6))
    N.keys(cam, "location", [(1, (-1.6, -2.4, 1.7)), (int(n * 0.45), (-1.2, -2.2, 1.6)), (n, (0, 1.3, 1.5))])
    N.keys(tgt, "location", [(1, (0.8, 0.5, 2.6)), (int(n * 0.45), (0, QD / 2, 1.5)), (n, (0, QD / 2, 1.5))])


@plan("20")
def p20(n):
    queens_chamber()
    root = N.empty("conduit", (0, QD / 2, 1.5), (SH, 0, 0))
    shaft(root, 25)
    N.light((0, QD / 2 - 0.6, 1.9), (0.8, 0.88, 1.0), 4)
    cam, tgt = N.camera(20, (0, QD / 2 - 1.0, 1.5), (0, QD / 2 + 3, 1.5 + 3 * math.tan(SH)))
    N.keys(cam, "location", [(1, (0, QD / 2 - 0.9, 1.5)), (n, (0, QD / 2 + 0.6, 1.5 + 0.6 * math.tan(SH) * 0.95))])
    N.keys(tgt, "location", [(1, (0, QD / 2 + 3, 1.5 + 0.5)), (n, (0, QD / 2 + 4, 1.5 + 4 * math.tan(SH)))])


def robot(parent, lights=True):
    """Upuaut-2 (1993) : petit engin à chenilles plaquées au sol et au plafond, deux phares, câble."""
    body = N.emit(BLUE_HI, 6)
    g = N.glass()
    rb = N.empty("robot"); rb.parent = parent
    N.box(-0.07, 0.07, -0.19, 0.19, -0.05, 0.05, g, rb)
    N.outline_box(-0.07, 0.07, -0.19, 0.19, -0.05, 0.05, 0.003, body, rb)
    tr = N.emit(BLUE, 4)
    for z in (-0.085, 0.085):
        for x in (-0.06, 0.06):
            N.line([(x, -0.2, z), (x, 0.2, z)], 0.012, tr, rb)
    for y in (-0.2, 0.2):
        N.line([(-0.06, y, -0.085), (-0.06, y, 0.085)], 0.004, tr, rb)
        N.line([(0.06, y, -0.085), (0.06, y, 0.085)], 0.004, tr, rb)
    hl = N.emit((0.9, 0.95, 1.0), 25)
    for x in (-0.035, 0.035):
        N.sphere((x, 0.195, 0.0), 0.012, hl, rb, seg=8)
    if lights:
        s = N.spot((0, 0.21, 0), (0.85, 0.9, 1.0), 6, angle_deg=55, parent=rb)
        s.rotation_euler = (math.radians(-90), 0, 0)
    N.line([(0, -0.19, -0.07), (0, -30, -0.07)], 0.002, N.emit(BLUE, 0.8), rb)
    return rb


@plan("21")
def p21(n):
    root = N.empty("conduit", (0, 0, 0), (SH, 0, 0))
    shaft(root, 40)
    rb = robot(root)
    N.keys(rb, "location", [(1, (0, 1.0, -0.005)), (n, (0, 7.5, -0.005))])
    cam, tgt = N.camera(24, (0, 0, 0), (0, 0, 0))
    cam.parent = root; tgt.parent = root
    cam.location = (0.03, 0.15, 0.06)
    N.keys(tgt, "location", [(1, (0, 2.0, 0.0)), (n, (0, 8.0, 0.0))])


def slab(parent, y, hole=False):
    lime = N.glass(tint=(0.01, 0.012, 0.018), rough=0.3, name="dalle")
    if hole:
        r = 0.012
        for (a0, a1, b0, b1) in ((-0.1, -r, -0.1, 0.1), (r, 0.1, -0.1, 0.1), (-r, r, -0.1, -r), (-r, r, r, 0.1)):
            N.box(a0, a1, y, y + 0.06, b0, b1, lime, parent)
    else:
        N.box(-0.1, 0.1, y, y + 0.06, -0.1, 0.1, lime, parent)
    N.rect((-0.1, y - 0.001, -0.1), (0.2, 0, 0), (0, 0, 0.2), 0.002, N.emit(BLUE_HI, 4), parent)
    cu = N.emit(COPPER, 10)
    for x in (-0.05, 0.05):
        N.line([(x, y, 0.035), (x, y - 0.012, 0.035), (x, y - 0.012, 0.02)], 0.0022, cu, parent)
    return lime


@plan("22")
def p22(n):
    root = N.empty("conduit", (0, 0, 0), (SH, 0, 0))
    shaft(root, 10)
    slab(root, 6.0)
    hl = N.spot((0, 0, 0), (0.85, 0.9, 1.0), 2, angle_deg=50)
    cam, tgt = N.camera(28, (0, 0, 0), (0, 0, 0))
    cam.parent = root; tgt.parent = root; hl.parent = root
    hl.rotation_euler = (math.radians(-90), 0, 0)
    tgt.location = (0, 6.0, 0.0)
    N.keys(cam, "location", [(1, (0, 4.6, 0.0)), (n, (0, 5.72, 0.0))])
    N.keys(hl, "location", [(1, (0, 4.6, 0.0)), (n, (0, 5.72, 0.0))])
    hl.data.keyframe_insert("energy", frame=1); hl.data.energy = 5; hl.data.keyframe_insert("energy", frame=n)


@plan("23")
def p23(n):
    root = N.empty("conduit", (0, 0, 0), (SH, 0, 0))
    shaft(root, 10)
    full = N.empty("pleine"); full.parent = root
    slab(full, 6.0)
    holed = N.empty("percee"); holed.parent = root
    slab(holed, 6.0, hole=True)
    ring = N.line([(0.012 * math.cos(a), 5.999, 0.012 * math.sin(a)) for a in [i / 12 * 2 * math.pi for i in range(12)]], 0.0012, N.emit(BLUE_HI, 10), root, cyclic=True)
    fh = int(n * 0.35)
    for o in full.children_recursive:
        N.visible(o, [(1, True), (fh, False)])
    for o in list(holed.children_recursive) + [ring]:
        N.visible(o, [(1, False), (fh, True)])
    # seconde dalle, brute, 20 cm derrière
    s2 = N.glass(tint=(0.01, 0.012, 0.018), rough=0.4, name="dalle2")
    N.box(-0.1, 0.1, 6.26, 6.32, -0.1, 0.1, s2, root)
    N.rect((-0.1, 6.259, -0.1), (0.2, 0, 0), (0, 0, 0.2), 0.0015, N.emit(BLUE, 2), root)
    red = N.emit(RED, 2.5)
    N.line([(-0.06, 6.259, -0.07), (-0.02, 6.259, 0.02), (0.03, 6.259, -0.01), (0.07, 6.259, 0.06)], 0.0015, red, root)
    N.light((0, 6.2, 0), (0.85, 0.9, 1.0), 0.15, root)
    drill = N.line([(0, 0, 0), (0, 0.5, 0)], 0.0025, N.emit(BLUE, 2), root)
    N.keys(drill, "location", [(1, (0, 5.35, 0)), (fh, (0, 5.55, 0)), (fh + 10, (0, 5.2, 0))])
    hl = N.spot((0, 0, 0), (0.85, 0.9, 1.0), 4, angle_deg=40, parent=root)
    hl.rotation_euler = (math.radians(-90), 0, 0)
    cam, tgt = N.camera(30, (0, 0, 0), (0, 0, 0))
    cam.parent = root; tgt.parent = root
    tgt.location = (0, 6.5, 0)
    N.keys(cam, "location", [(1, (0.03, 5.62, 0.035)), (fh + 6, (0.0, 5.75, 0.0)), (n, (0.0, 6.03, 0.0))])
    N.keys(hl, "location", [(1, (0.03, 5.62, 0.035)), (fh + 6, (0.0, 5.75, 0.0)), (n, (0.0, 6.03, 0.0))])


# ---------------------------------------------------------------- face nord et couloir caché (24-27)
FACE = math.radians(51.84)


def north_face():
    """Face nord autour de l'entrée : repère local x = largeur, y = vers l'intérieur, z = le long de la pente."""
    root = N.empty("face", (0, 0, 0), (-(math.pi / 2 - FACE), 0, 0))
    g = N.glass()
    dim = N.emit(BLUE, 0.7)
    N.box(-25, 25, 0, 6, -10, 40, g, root)
    rnd = random.Random(11)
    z = -10.0
    while z < 40:
        h = rnd.uniform(0.9, 1.4)
        N.line([(-25, -0.01, z), (25, -0.01, z)], 0.02, dim, root)
        x = -25 + rnd.uniform(0, 1.5)
        while x < 25:
            if not (-4.5 < x < 4.5 and 0 < z < 12):
                N.line([(x, -0.01, z), (x, -0.01, z + h)], 0.015, dim, root)
            x += rnd.uniform(1.2, 2.4)
        z += h
    chev = N.emit(BLUE_HI, 6)
    big = N.glass(tint=(0.006, 0.01, 0.02), rough=0.15, name="chevrons")
    for (w, z0, t) in ((4.2, 2.0, 1.6), (4.2, 5.2, 1.6)):
        for s in (-1, 1):
            p0, p1 = Vector((0, -0.3, z0 + 3.4)), Vector((s * w, -0.3, z0))
            d = p1 - p0
            n_ = Vector((-d.z, 0, d.x)).normalized() * t * s * -1
            verts = [p0, p1, p1 + n_, p0 + n_]
            N.mesh([v + Vector((0, -0.4, 0)) for v in verts] + [v + Vector((0, 1.5, 0)) for v in verts],
                   [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], big, root)
            N.line([v + Vector((0, -0.42, 0)) for v in verts], 0.03, chev, root, cyclic=True)
    N.line([(-0.55, -0.01, -1.0), (-0.55, -0.01, 0.2), (0.55, -0.01, 0.2), (0.55, -0.01, -1.0)], 0.03, chev, root)
    return root


@plan("24")
def p24(n):
    root = north_face()
    N.stars(700, 2000)
    N.ground(3000, -20)
    for x in (-2.5, 2.5):
        N.flame((x, -1.2, -0.6), 2.0, root, energy=0)
    cam, tgt = N.camera(24, (0, 0, 0), (0, 0, 0))
    cam.parent = root; tgt.parent = root
    N.keys(cam, "location", [(1, (0, -14, -6)), (n, (0, -10, 4))])
    N.keys(tgt, "location", [(1, (0, 0, 2)), (n, (0, 0, 7))])
    spl = N.spot((0, 0, 0), (0.8, 0.88, 1.0), 2500, angle_deg=22, parent=root)
    N.keys(spl, "location", [(1, (-3, -6, -4)), (n, (2, -6, 2))])
    spl.rotation_euler = (math.radians(-80), 0, 0)


def joint_wall(gap, golden=False):
    """Deux énormes blocs de calcaire séparés par un joint étroit (axe y = profondeur du joint)."""
    g = N.glass(tint=(0.02, 0.026, 0.04), rough=0.5, name="calcaire")
    edge, dim = N.emit(BLUE_HI, 4), N.emit(BLUE, 0.45)
    N.box(-4, -gap / 2, 0, 3, -3, 3, g)
    N.box(gap / 2, 4, 0, 3, -3, 3, g)
    N.box(-gap / 2, gap / 2, 2.6, 3, -3, 3, N.emit((0, 0, 0), 0))
    for x in (-gap / 2, gap / 2):
        N.line([(x, -0.002, -3), (x, -0.002, 3)], 0.004, edge)
    for (x0, x1, z) in ((-4, -gap / 2, -1.2), (-4, -gap / 2, 1.05), (gap / 2, 4, -0.6), (gap / 2, 4, 1.6)):
        N.line([(x0, -0.002, z), (x1, -0.002, z)], 0.004, dim)
    for (x, z0, z1) in ((-2.2, -1.2, 1.05), (2.4, -0.6, 1.6), (-3.1, 1.05, 3), (1.3, -3, -0.6)):
        N.line([(x, -0.002, z0), (x, -0.002, z1)], 0.004, dim)
    return edge


@plan("25")
def p25(n):
    joint_wall(0.03)
    cable = N.line([(0.6, -1.6, -1.1), (0.25, -0.8, -0.45), (0.05, -0.25, -0.06), (0.0, -0.05, 0.0), (0, 0.0, 0), (0, 1.2, 0)], 0.006, N.emit(BLUE, 1.5))
    N.keys(cable, "location", [(1, (0, -0.7, 0)), (n, (0, 0.0, 0))])
    tip = N.sphere((0, 0, 0), 0.008, N.emit((0.9, 0.95, 1.0), 30), seg=8)
    tl = N.light((0, 0, 0), (0.85, 0.9, 1.0), 0.6)
    for o in (tip, tl):
        N.keys(o, "location", [(1, (0, 0.5, 0)), (n, (0, 1.2, 0))])
    hl = N.spot((1.2, -2.5, 0.8), (0.85, 0.9, 1.0), 300, angle_deg=25)
    N.aim(hl, (0, 0, 0))
    cam, tgt = N.camera(30, (0.9, -2.4, 0.5), (0, 0.1, 0))
    N.keys(cam, "location", [(1, (0.9, -2.4, 0.5)), (n, (0.45, -1.3, 0.25))])

def hidden_corridor():
    g = N.glass(tint=(0.006, 0.01, 0.02), rough=0.25, name="calcaire")
    edge, dim = N.emit(BLUE, 4), N.emit(BLUE, 0.7)
    W, L, wall = 2.1, 9.0, 1.3
    N.box(-W / 2 - 1, W / 2 + 1, 0, L, -0.5, 0, g)
    for s in (-1, 1):
        N.box(s * W / 2, s * (W / 2 + 1), 0, L, 0, wall, g)
        N.line([(s * W / 2, 0, 0), (s * W / 2, L, 0)], 0.01, edge)
        N.line([(s * W / 2, 0, wall), (s * W / 2, L, wall)], 0.01, edge)
    # plafond en chevrons : paires de poutres inclinées
    y = 0.0
    while y < L:
        for s in (-1, 1):
            N.mesh([(s * W / 2, y, wall), (0, y, wall + 1.3), (0, y + 1.1, wall + 1.3), (s * W / 2, y + 1.1, wall)], [(0, 1, 2, 3)], g)
            N.line([(s * W / 2, y, wall), (0, y, wall + 1.3)], 0.008, dim)
        y += 1.15
    N.line([(0, 0, wall + 1.3), (0, L, wall + 1.3)], 0.01, edge)
    end = N.box(-W / 2, W / 2, L, L + 0.5, 0, wall + 1.3, g)
    N.line([(-W / 2, L - 0.01, 0), (-W / 2, L - 0.01, wall), (0, L - 0.01, wall + 1.3), (W / 2, L - 0.01, wall), (W / 2, L - 0.01, 0)], 0.012, edge)
    return L, wall


def dust(n, box_, count, mat, frames, toward=None, seed=3):
    rnd = random.Random(seed)
    (x0, x1), (y0, y1), (z0, z1) = box_
    for i in range(count):
        p = Vector((rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(z0, z1)))
        s = N.sphere(p, 0.006, mat, seg=6)
        q = Vector(toward) + Vector((rnd.uniform(-0.1, 0.1), 0, rnd.uniform(0, 0.03))) if toward else p + Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), rnd.uniform(-0.05, 0.1)))
        N.keys(s, "location", [(1, p), (frames, p.lerp(q, 0.85 if toward else 1.0))])


@plan("26")
def p26(n):
    L, wall = hidden_corridor()
    ring = N.light((0, 0, 0), (0.9, 0.95, 1.0), 25)
    cam, tgt = N.camera(18, (0, 0.3, 1.0), (0, 9, 1.1))
    N.keys(cam, "location", [(1, (0.05, 0.2, 1.0)), (n, (0.0, 5.5, 1.05))])
    N.keys(ring, "location", [(1, (0.05, 0.3, 1.1)), (n, (0.0, 5.6, 1.15))])
    dust(n, ((-0.9, 0.9), (1, 7), (0.2, 2.0)), 25, N.emit((0.8, 0.85, 1.0), 3), n)


@plan("27")
def p27(n):
    L, wall = hidden_corridor()
    gap = N.box(0.15, 0.55, L - 0.02, L + 0.02, 0.0, 0.035, N.emit((0, 0, 0), 0))
    N.line([(0.15, L - 0.025, 0.035), (0.55, L - 0.025, 0.035)], 0.003, N.emit(BLUE_HI, 4))
    ring = N.light((0, 0, 0), (0.9, 0.95, 1.0), 6)
    cam, tgt = N.camera(24, (0, 5.5, 1.05), (0.2, 9, 0.6))
    N.keys(cam, "location", [(1, (0.0, 5.5, 1.05)), (n, (0.15, 7.6, 0.6))])
    N.keys(ring, "location", [(1, (0.0, 5.3, 1.25)), (n, (0.1, 7.2, 0.9))])
    N.keys(tgt, "location", [(1, (0.0, 9, 1.0)), (n, (0.35, 9, 0.05))])
    dust(n, ((-0.3, 0.9), (7.6, 8.8), (0.05, 0.6)), 30, N.emit((0.8, 0.85, 1.0), 4), n, toward=(0.35, L, 0.02))


# ---------------------------------------------------------------- 28 — le vide au-dessus de la galerie
@plan("28")
def p28(n):
    gl = N.glass()
    N.key_alpha(gl, [(1, 0.15)])
    N.pyramid(glass_mat=gl, courses=0)
    N.interior(mat=N.emit(BLUE, 2.5), r=0.3)
    gg = N.emit(BLUE_HI, 9)
    g = N.line([N.GG0 + Vector((0, 0, 4.3)), N.GG1 + Vector((0, 0, 4.3))], 2.4, gg)
    N.draw(g, 1, int(n * 0.45))
    red = N.emit(RED, 4)
    N.line([N.VOID0, N.VOID1], 2.2, red)
    N.key_strength(red, [(1, 4), (int(n * 0.45), 4), (int(n * 0.75), 14)])
    N.stars(400, 3000)
    cam, tgt = N.camera(32, (0, 0, 0), (0, -12, 40))
    piv = N.empty("pivot", (0, -12, 40))
    cam.parent = piv
    cam.location = (125, 0, 12)
    N.keys(piv, "rotation_euler", [(1, (0, 0, math.radians(-12))), (n, (0, 0, math.radians(22)))])


# ---------------------------------------------------------------- 29 — ils savent où il est, ils connaissent sa taille
@plan("29")
def p29(n):
    piv = N.empty("modele", (0, 0, 1.2))
    sc = 0.01
    piv.scale = (sc, sc, sc)
    gl = N.glass()
    N.key_alpha(gl, [(1, 0.2)])
    N.pyramid(piv, courses=20, glass_mat=gl, r_edge=0.6, r_course=0.2)
    N.interior(piv, N.emit(BLUE_HI, 5), r=0.5)
    N.void(piv, N.emit(RED, 10), radius=2.4)
    N.keys(piv, "rotation_euler", [(1, (0, 0, math.radians(-40))), (n, (0, 0, math.radians(25)))])
    ring = N.emit(BLUE, 5)
    for r in (1.4, 1.6):
        N.line([(r * math.cos(a), r * math.sin(a), 0.7) for a in [i / 64 * 2 * math.pi for i in range(64)]], 0.008, ring, cyclic=True)
    N.mesh([(1.6 * math.cos(a), 1.6 * math.sin(a), 0.69) for a in [i / 64 * 2 * math.pi for i in range(64)]], [tuple(range(64))], N.glass())
    rays = N.emit(BLUE, 0.6)
    for i in range(24):
        a = i / 24 * 2 * math.pi
        N.line([(1.4 * math.cos(a), 1.4 * math.sin(a), 0.7), (0.8 * math.cos(a), 0.8 * math.sin(a), 1.2)], 0.002, rays)
    N.ground(60, 0)
    cam, tgt = N.camera(35, (0, -4.6, 2.4), (0, 0, 1.6))
    N.keys(cam, "location", [(1, (0.6, -4.8, 2.5)), (n, (0.2, -3.6, 2.2))])


# ---------------------------------------------------------------- 30 — personne n'y est jamais entré
@plan("30")
def p30(n):
    root, top = gallery()
    redm = N.emit(RED, 0)
    for k in range(6):
        N.line([(-0.5, 12 + k * 3, top + 0.31), (0.5, 12 + k * 3, top + 0.31)], 0.01, redm, root)
    N.key_strength(redm, [(1, 0), (int(n * 0.5), 0), (int(n * 0.85), 6)])
    sp = N.spot((0, 0, 0), (0.8, 0.88, 1.0), 900, angle_deg=10, parent=root)
    sp.location = (0.1, 10.0, 1.6)
    tg = N.empty("t"); tg.parent = root
    c = sp.constraints.new("TRACK_TO"); c.target = tg; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    N.keys(tg, "location", [(1, (0.9, 13, 1.5)), (int(n * 0.6), (0, 14.5, top))])
    cam, tgt = N.camera(16, (0, 0, 0), (0, 0, 0))
    cam.parent = root; tgt.parent = root
    N.keys(cam, "location", [(1, (0, 9.0, 1.7)), (int(n * 0.45), (0, 9.5, 2.5)), (n, (0, 13.0, top - 0.2))])
    N.keys(tgt, "location", [(1, (0, 15, 4.5)), (int(n * 0.45), (0, 14.0, top)), (n, (0, 14.0, top + 1))])


# ---------------------------------------------------------------- 31 — fermée depuis l'époque des pharaons
@plan("31")
def p31(n):
    N.blocks_wall(-4, 4, 0, 4, 0.0, bw=1.4, bh=1.0, edge=N.emit(BLUE, 0.8), seed=6)
    # ouverture à combler
    N.box(-0.7, 0.7, -0.01, 1.02, 1.0, 2.0, N.emit((0, 0, 0), 0))
    blk = N.empty("bloc")
    g = N.glass()
    N.box(-0.7, 0.7, 0, 1.0, 1.0, 2.0, g, blk)
    N.outline_box(-0.7, 0.7, 0, 1.0, 1.0, 2.0, 0.012, N.emit(BLUE_HI, 6), blk)
    N.keys(blk, "location", [(1, (0, -0.95, 0)), (int(n * 0.55), (0, -0.0, 0))])
    f, l, m = N.flame((-1.8, -1.2, 1.1), 2.5, energy=260, frames=n)
    N.key_strength(m, [(int(n * 0.6), 40), (int(n * 0.85), 0)])
    l.data.energy = 260; l.data.keyframe_insert("energy", frame=int(n * 0.6))
    l.data.energy = 0; l.data.keyframe_insert("energy", frame=int(n * 0.85))
    cam, tgt = N.camera(28, (1.8, -4.5, 1.7), (0, 0, 1.5))
    N.keys(cam, "location", [(1, (1.8, -4.5, 1.7)), (n, (1.2, -3.6, 1.6))])


# ---------------------------------------------------------------- 32 — le monument le plus étudié de la planète
@plan("32")
def p32(n):
    giza(courses=30)
    N.ground(30000)
    rnd = random.Random(21)
    city = N.emit((1.0, 0.72, 0.42), 6)
    city2 = N.emit((1.0, 0.6, 0.3), 0.8)
    verts, faces = [], []
    for i in range(6000):
        ang = rnd.uniform(math.radians(20), math.radians(160))
        d = 900 + rnd.expovariate(1 / 2500)
        x, y = d * math.cos(ang), d * math.sin(ang) - 300
        s = rnd.uniform(1.5, 4)
        b = len(verts)
        verts += [(x - s, y - s, 0.5), (x + s, y - s, 0.5), (x + s, y + s, 0.5), (x - s, y + s, 0.5)]
        faces.append((b, b + 1, b + 2, b + 3))
    N.mesh(verts, faces, city, name="ville")
    for i in range(30):
        ang = rnd.uniform(math.radians(25), math.radians(155))
        N.line([(900 * math.cos(ang), 900 * math.sin(ang) - 300, 0.6), (9000 * math.cos(ang), 9000 * math.sin(ang) - 300, 0.6)], 1.2, city2)
    N.stars(500, 20000, zmin=0.15)
    cam, tgt = N.camera(28, (0, -420, 120), (0, 300, 60))
    N.keys(cam, "location", [(1, (60, -380, 110)), (n, (120, -900, 420))])
    N.keys(tgt, "location", [(1, (0, 200, 60)), (n, (0, 600, 20))])


# ---------------------------------------------------------------- 33 — là où personne ne devait jamais regarder
@plan("33")
def p33(n):
    edge = joint_wall(0.05)
    gold = N.emit(GOLD, 0)
    N.sphere((0, 2.4, 0.1), 0.015, gold, seg=8)
    N.key_strength(gold, [(1, 0), (int(n * 0.3), 6), (int(n * 0.5), 25), (int(n * 0.6), 4), (int(n * 0.7), 18), (n, 0)])
    gl_ = N.light((0, 2.3, 0.1), (1, 0.7, 0.3), 0)
    gl_.data.keyframe_insert("energy", frame=1); gl_.data.energy = 2.0; gl_.data.keyframe_insert("energy", frame=int(n * 0.5))
    gl_.data.energy = 0; gl_.data.keyframe_insert("energy", frame=n)
    f, l, m = N.flame((-1.4, -1.2, -0.9), 2.0, energy=90, frames=n)
    N.key_strength(edge, [(1, 4), (int(n * 0.75), 4), (n, 0)])
    N.key_strength(m, [(int(n * 0.75), 40), (n, 0)])
    l.data.energy = 90; l.data.keyframe_insert("energy", frame=int(n * 0.75)); l.data.energy = 0; l.data.keyframe_insert("energy", frame=n)
    cam, tgt = N.camera(32, (0.7, -3.0, 0.5), (0, 0.5, 0))
    N.keys(cam, "location", [(1, (0.7, -3.0, 0.5)), (n, (0.0, -0.02, 0.05))])
    N.keys(tgt, "location", [(1, (0, 0.5, 0)), (n, (0, 2.4, 0.1))])
