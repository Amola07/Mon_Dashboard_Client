"""Éclat — « Gravité » : film muet de 2 minutes en 2D (fond noir, traits blancs, lumière).

    python -m films.stick.gravite sortie.mp4 [--debut s] [--fin s] [--pas N] [--images n1,n2,...]

Tout le film est décrit ici : lieux (planètes, lune, trou noir), trajet d'Éclat, poses, caméra, effets et son.
"""
import argparse
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import skia

from . import hero as HERO

W, H, FPS = 1080, 1920, 60
DURATION = 120.0
LINE = (236, 240, 248)
CYAN = HERO.CYAN
VIOLET = (170, 90, 255)
GOLD = (255, 200, 90)
S = 0.55                                        # taille d'Éclat (≈ 165 unités de haut)


def col(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def pen(c, w, a=255, glow=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if glow:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        p.setBlendMode(skia.BlendMode.kPlus)
    return p


def brush(c, a=255, glow=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if glow:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        p.setBlendMode(skia.BlendMode.kPlus)
    return p


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    if isinstance(a, tuple):
        return tuple(x + (y - x) * u for x, y in zip(a, b))
    return a + (b - a) * u


def keys_at(keys, t, ease=smooth):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(v0, v1, ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0)
    return keys[-1][1]


# ---------------------------------------------------------------- lieux
P0 = dict(c=(0.0, 0.0), r=140)                   # la petite planète de départ
P1 = dict(c=(760.0, -950.0), r=230)
P2 = dict(c=(-650.0, -1900.0), r=180)
MOON_ORBIT = (380.0, 0.55)                      # rayon, vitesse angulaire (rad/s) autour de P1
MOON_R = 60
BH = (150.0, -3350.0)
BH_AWAKE = (60.0, 64.0)
BH_COLLAPSE = (95.0, 98.0)


def moon_pos(t):
    a = -2.2 + MOON_ORBIT[1] * t
    return (P1["c"][0] + math.cos(a) * MOON_ORBIT[0], P1["c"][1] + math.sin(a) * MOON_ORBIT[0]), a


def p2_center(t):
    """La troisième planète est entraînée vers le trou noir, puis relâchée quand il s'effondre."""
    u = smooth((t - 68) / 14) * (1 - smooth((t - 96) / 8))
    return lerp(P2["c"], (BH[0] - 520, BH[1] + 420), u * 0.55)


def bh_strength(t):
    return smooth((t - BH_AWAKE[0]) / (BH_AWAKE[1] - BH_AWAKE[0])) * (1 - smooth((t - BH_COLLAPSE[0]) / (BH_COLLAPSE[1] - BH_COLLAPSE[0])))


def surface(planet_c, r, ang):
    """Point de la surface et rotation d'Éclat debout dessus (la tête vers l'extérieur)."""
    return (planet_c[0] + math.cos(ang) * r, planet_c[1] + math.sin(ang) * r), math.degrees(ang) + 90


# ---------------------------------------------------------------- trajet d'Éclat
UP = -math.pi / 2


def arc(p0, p1, t, t0, t1, height):
    """Trajectoire courbe entre deux points (bosse perpendiculaire), vitesse adoucie."""
    u = (t - t0) / (t1 - t0)
    u = u * u * (3 - 2 * u) * 0.6 + u * 0.4
    x, y = lerp(p0, p1, u)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy) or 1
    k = 4 * height * u * (1 - u)
    return (x - dy / n * k, y + dx / n * k), math.degrees(math.atan2(dy, dx)) + 90


def hero_state(t):
    """Renvoie position des pieds, rotation (degrés), pose, sens, traînée (bool), vent de cape."""
    wind, trail = 0.9, False
    walk = "marche1" if int(t * 4) % 2 == 0 else "marche2"
    if t < 1.2:                                                    # chute depuis le haut
        u = t / 1.2
        return (0.0, -140 - 900 * (1 - u * u)), 0.0, "saut", 1, False, 1.8
    if t < 3.0:
        pose = "atterrit" if t < 1.6 else ("salut" if 2.0 < t < 2.8 else "debout")
        pos, rot = surface(P0["c"], P0["r"], UP)
        return pos, rot, pose, 1, False, wind
    if t < 7.0:                                                    # tour de la planète à pied
        ang = UP + 2 * math.pi * smooth((t - 3.0) / 4.0)
        pos, rot = surface(P0["c"], P0["r"], ang)
        return pos, rot, walk, 1, False, 1.1
    if t < 8.0:
        pos, rot = surface(P0["c"], P0["r"], UP)
        return pos, rot, "debout", 1, False, wind
    if t < 9.5:                                                    # petit saut
        u = (t - 8.0) / 1.5
        pos, rot = surface(P0["c"], P0["r"], UP)
        return (pos[0], pos[1] - 4 * 150 * u * (1 - u)), rot, "saut" if 0.1 < u < 0.9 else "atterrit", 1, True, 1.2
    if t < 10.5:
        pos, rot = surface(P0["c"], P0["r"], UP)
        return pos, rot, "reflexion", 1, False, wind
    if t < 11.5:                                                   # grand saut : monte jusqu'à l'orbite
        u = smooth((t - 10.5) / 1.0)
        pos, rot = surface(P0["c"], lerp(P0["r"], 320, u), UP + 0.6 * u)
        return pos, rot, "saut", 1, True, 1.6
    if t < 20.0:                                                   # en orbite autour de P0
        ang = UP + 0.6 + (t - 11.5) * (2 * math.pi / 5.0)
        pos, rot = surface(P0["c"], 320, ang)
        return pos, rot + 90, "vol", 1, True, 1.7
    orbit_exit = surface(P0["c"], 320, UP + 0.6 + 8.5 * (2 * math.pi / 5.0))[0]
    land1, rot1 = surface(P1["c"], P1["r"], math.radians(215))
    if t < 23.5:                                                   # vers la grande planète
        if t < 21.0:
            ang = UP + 0.6 + (t - 11.5) * (2 * math.pi / 5.0)
            pos, rot = surface(P0["c"], 320, ang)
            return pos, rot + 90, "vol", 1, True, 1.7
        pos, rot = arc(orbit_exit, land1, t, 21.0, 23.5, 260)
        return pos, rot, "vol", 1, True, 1.8
    if t < 28.0:
        pose = "atterrit" if t < 24.0 else ("salut" if 25 < t < 26.5 else "debout")
        return land1, rot1, pose, 1, False, wind
    mp, ma = moon_pos(t)
    if t < 30.4:                                                   # vise la lune… la rate
        target = moon_pos(30.2)[0]
        pos, rot = arc(land1, (target[0] - 180, target[1] + 40), t, 28.0, 30.4, 140)
        return pos, rot, "vol", 1, True, 1.6
    if t < 33.0:                                                   # percuté : tournoie et retombe
        miss = moon_pos(30.2)[0]
        u = smooth((t - 30.4) / 2.6)
        start = (miss[0] - 180, miss[1] + 40)
        pos = lerp(start, land1, u)
        return pos, 720 * u + rot1 * u, "saut", 1, True, 1.2
    if t < 36.0:
        return land1, rot1, "reflexion", 1, False, wind
    if t < 38.5:                                                   # saute au bon moment : atterrit sur la lune
        dest = surface(moon_pos(38.5)[0], MOON_R, moon_pos(38.5)[1])[0]
        pos, rot = arc(land1, dest, t, 36.0, 38.5, 200)
        return pos, rot, "vol", 1, True, 1.7
    if t < 42.0:                                                   # surfe sur la lune
        pos, rot = surface(mp, MOON_R, ma)
        return pos, rot, "salut" if int(t) % 2 else "debout", 1, False, 1.3
    land2, rot2 = surface(P2["c"], P2["r"], math.radians(20))
    if t < 47.0:                                                   # fronde vers la troisième planète
        start = surface(moon_pos(42.0)[0], MOON_R, moon_pos(42.0)[1])[0]
        pos, rot = arc(start, land2, t, 42.0, 47.0, -700)
        return pos, rot, "vol", 1, True, 1.9
    p2c = p2_center(t)
    if t < 60.0:
        pose = "atterrit" if t < 47.5 else ("marche1" if 48.5 < t < 49 else ("marche2" if 49 < t < 49.5 else "reflexion" if t > 52 else "debout"))
        pos, rot = surface(p2c, P2["r"], math.radians(20))
        return pos, rot, pose, 1, False, wind
    if t < 80.0:                                                   # le trou noir aspire : il court en sens inverse
        bh_dir = math.atan2(BH[1] - p2c[1], BH[0] - p2c[0])
        ang = math.radians(20) + 0.25 * smooth((t - 66) / 6) * math.sin((t - 66) * 1.3)
        pos, rot = surface(p2c, P2["r"], ang if t < 70 else bh_dir + math.pi + 0.15 * math.sin(t * 3))
        pose = "debout" if t < 66 else walk
        return pos, rot, pose, 1, False, 1.0 + 1.5 * bh_strength(t)
    rope_a = (BH[0] - 900, BH[1] + 900)
    rope_b = (BH[0] + 700, BH[1] + 1000)
    hang = lerp(rope_a, rope_b, 0.42)
    if t < 82.0:                                                   # aspiré, se rattrape à une ligne d'orbite
        start = surface(p2_center(80), P2["r"], math.atan2(BH[1] - p2_center(80)[1], BH[0] - p2_center(80)[0]) + math.pi)[0]
        pos, rot = arc(start, (hang[0], hang[1] + 165 * S * 1.9), t, 80.0, 82.0, 120)
        return pos, rot, "saut", 1, True, 2.2
    if t < 86.5:
        sway = 12 * math.sin(t * 2.2)
        return (hang[0] + sway * 0.3, hang[1] + 165 * S * 1.9), -180 + sway, "accroche", 1, False, 2.4
    if t < 95.0:                                                   # plonge, frôle le trou noir, s'échappe
        u = (t - 86.5) / 8.5
        d0 = math.hypot(hang[0] - BH[0], hang[1] - BH[1])
        ang0 = math.atan2(hang[1] - BH[1], hang[0] - BH[0])
        r = 230 + (d0 - 230) * (1 - u / 0.5) ** 2 if u < 0.5 else 230 + 7000 * (u - 0.5) ** 2
        ang = ang0 + 4.6 * smooth(u)
        pos = (BH[0] + math.cos(ang) * r, BH[1] + math.sin(ang) * r)
        return pos, math.degrees(ang) + 180, "vol", 1, True, 2.4
    esc = hero_state(94.999)[0]
    home, rot0 = surface(P0["c"], P0["r"], UP)
    if t < 110.0:                                                  # retour sur la petite planète
        pos, rot = arc(esc, home, t, 95.0, 110.0, 900)
        return pos, rot if t < 108.5 else rot0, "vol" if t < 108.8 else "atterrit", 1, True, 1.6
    if t < 116.0:
        return home, rot0, "debout" if t < 113 else ("salut" if t < 115 else "saut"), 1, False, wind
    u = min(1.0, (t - 116.0) / 1.6)                                # saute hors de l'écran : boucle
    return (home[0], home[1] - 1100 * u * u), 0.0, "saut", 1, True, 1.8


# ---------------------------------------------------------------- caméra : (centre, zoom, rotation)
def camera(t):
    pos, rot, *_ = hero_state(t)
    follow = [
        (0.0, (0.0, -420.0), 1.25, 0.0), (1.2, (0.0, -150.0), 1.45, 0.0), (3.0, (0.0, -80.0), 1.45, 0.0),
        (7.0, (0.0, -80.0), 1.45, 0.0), (10.5, (0.0, -140.0), 1.3, 0.0), (15.0, (0.0, -60.0), 0.9, 0.0),
        (19.0, (300.0, -700.0), 0.57, 0.0), (22.0, (500.0, -800.0), 0.74, 0.0), (26.0, None, 0.8, 0.0),
        (30.0, None, 0.81, 0.0), (36.0, None, 0.84, 0.0), (42.0, None, 0.94, 0.0), (46.0, None, 0.61, 0.0),
        (52.0, None, 0.94, 0.0), (58.0, ((-650 + 150) / 2, (-1900 - 3350) / 2 + 200), 0.34, 0.0),
        (66.0, None, 0.57, 0.0), (80.0, None, 0.61, 0.0), (86.0, None, 0.68, 0.0), (90.0, None, 0.46, 0.0),
        (95.0, (150.0, -3350.0), 0.41, 0.0), (99.0, (150.0, -3100.0), 0.38, 0.0), (104.0, None, 0.54, 0.0),
        (110.0, (0.0, -120.0), 1.2, 0.0), (116.0, (0.0, -150.0), 1.3, 0.0), (120.0, (0.0, -420.0), 1.25, 0.0),
    ]
    prev = None
    for (t0, c0, z0, r0), (t1, c1, z1, r1) in zip(follow, follow[1:]):
        if t0 <= t <= t1:
            u = smooth((t - t0) / (t1 - t0))
            a = c0 if c0 is not None else (pos[0], pos[1] - 120)
            b = c1 if c1 is not None else (pos[0], pos[1] - 120)
            center, zoom = lerp(a, b, u), lerp(z0, z1, u)
            break
    else:
        center, zoom = (pos[0], pos[1]), 1.0
    angle = 0.0
    if 3.0 <= t <= 7.2:                                            # la caméra tourne avec lui autour de la planète
        angle = -(360 * smooth((t - 3.0) / 4.0))
        center = lerp(center, P0["c"], smooth((t - 3.0) / 0.5) * (1 - smooth((t - 6.6) / 0.5)))
    shake = 7 * bh_strength(t) * (1 if 60 < t < 95 else 0)
    center = (center[0] + shake * math.sin(t * 37), center[1] + shake * math.cos(t * 29))
    return center, zoom, angle


# ---------------------------------------------------------------- dessin
class World:
    def __init__(self):
        r = np.random.default_rng(3)
        n = 700
        self.stars = np.column_stack([r.uniform(-4000, 4000, n), r.uniform(-6000, 2000, n), r.power(4, n) * 2.4 + 0.5,
                                      r.uniform(0, 6.28, n), r.uniform(0.2, 0.7, n)])     # x, y, taille, phase, profondeur
        m = 260
        self.swirl = np.column_stack([r.uniform(250, 1600, m), r.uniform(0, 6.28, m), r.uniform(1, 3.2, m)])
        self.trail = []

    def to_screen(self, cam, p, depth=1.0):
        (cx, cy), zoom, ang = cam
        x, y = (p[0] - cx) * zoom * depth, (p[1] - cy) * zoom * depth
        a = math.radians(ang)
        return (W / 2 + x * math.cos(a) - y * math.sin(a), H / 2 + x * math.sin(a) + y * math.cos(a))


def warp(p, t):
    """Déformation de l'espace-temps autour du trou noir : les points glissent vers lui."""
    k = bh_strength(t)
    if k <= 0:
        return p
    dx, dy = BH[0] - p[0], BH[1] - p[1]
    d = math.hypot(dx, dy) + 1e-6
    pull = min(d * 0.8, 260000 * k / (d + 250))
    return (p[0] + dx / d * pull, p[1] + dy / d * pull)


def draw_frame(c, world, t):
    cam = camera(t)
    c.clear(skia.ColorBLACK)
    (cx, cy), zoom, ang = cam
    k_bh = bh_strength(t)
    # étoiles de fond (parallaxe) ; aspirées en spirale quand le trou noir est éveillé
    for x, y, s, ph, depth in world.stars:
        p = warp((x, y), t) if k_bh > 0 else (x, y)
        sx, sy = world.to_screen(cam, (cx + (p[0] - cx) * depth, cy + (p[1] - cy) * depth))
        if -20 < sx < W + 20 and -20 < sy < H + 20:
            a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(ph + t * 1.1))
            c.drawCircle(sx, sy, s * (0.6 + 0.4 * zoom), brush(LINE, 200 * a))
    c.save()
    c.translate(W / 2, H / 2)
    c.rotate(ang)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)
    lw = 1 / zoom                                                  # épaisseur de trait constante à l'écran
    # grille de l'espace-temps
    grid_a = max(smooth((t - 52) / 4) * (1 - smooth((t - 104) / 5)), 0.0)
    if grid_a > 0.01:
        step = 220
        x0, x1, y0, y1 = BH[0] - 2600, BH[0] + 2600, BH[1] - 2400, BH[1] + 3600
        for gx in np.arange(x0, x1 + 1, step):
            pts = [warp((gx, gy), t) for gy in np.arange(y0, y1 + 1, 60)]
            path = skia.Path()
            path.moveTo(*pts[0])
            for q in pts[1:]:
                path.lineTo(*q)
            c.drawPath(path, pen((120, 110, 220), 1.6 * lw, 90 * grid_a))
        for gy in np.arange(y0, y1 + 1, step):
            pts = [warp((gx, gy), t) for gx in np.arange(x0, x1 + 1, 60)]
            path = skia.Path()
            path.moveTo(*pts[0])
            for q in pts[1:]:
                path.lineTo(*q)
            c.drawPath(path, pen((120, 110, 220), 1.6 * lw, 90 * grid_a))
    # orbites
    orbit_a = smooth((t - 11.5) / 1.5)
    if orbit_a > 0:
        drawn = min(1.0, (t - 11.5) / 5.0)
        path = skia.Path()
        path.addArc(skia.Rect.MakeLTRB(-320, -320, 320, 320), math.degrees(UP + 0.6), 360 * drawn)
        c.drawPath(path, pen(LINE, 2.2 * lw, 170 * orbit_a))
    reveal = smooth((t - 15.5) / 3)
    if reveal > 0:
        c.drawCircle(*P1["c"], MOON_ORBIT[0], pen(LINE, 2.0 * lw, 130 * reveal))
    # trou noir
    if k_bh > 0.01 or BH_COLLAPSE[0] <= t < BH_COLLAPSE[1] + 3:
        r = 95 * k_bh
        for i, (rr, a0, s) in enumerate(world.swirl):              # étoiles qui tombent en spirale
            rad = rr * (1 - ((t * 0.08 + i * 0.013) % 1.0)) * k_bh + r
            a = a0 + t * 900 / (rad + 60)
            c.drawCircle(BH[0] + math.cos(a) * rad, BH[1] + math.sin(a) * rad * 0.55, s * lw * 1.4,
                         brush((200, 180, 255), 220 * k_bh))
        c.drawCircle(*BH, r * 3.2, brush(VIOLET, 60 * k_bh, glow=r * 1.6))
        ring = skia.Rect.MakeLTRB(BH[0] - r * 2.4, BH[1] - r * 0.8, BH[0] + r * 2.4, BH[1] + r * 0.8)
        c.drawOval(ring, pen(VIOLET, 14 * lw + r * 0.12, 200 * k_bh, glow=r * 0.25))
        c.drawOval(ring, pen((230, 200, 255), 3 * lw, 230 * k_bh))
        c.drawCircle(*BH, r, brush((0, 0, 0)))
        c.drawCircle(*BH, r * 1.08, pen((240, 230, 255), 2.2 * lw, 220 * k_bh))
    # effondrement → nouvelle étoile
    if t >= BH_COLLAPSE[0]:
        flash = smooth((t - BH_COLLAPSE[1] + 0.4) / 0.5) * (1 - smooth((t - BH_COLLAPSE[1] - 0.4) / 2.0))
        born = smooth((t - BH_COLLAPSE[1]) / 2.0)
        if flash > 0:
            c.drawCircle(*BH, 700 * flash, brush((255, 240, 210), 160 * flash, glow=220))
        if born > 0:
            c.drawCircle(*BH, 150 * born, brush(GOLD, 120 * born, glow=90))
            for k in range(12):
                a = 2 * math.pi * k / 12 + t * 0.2
                c.drawLine(BH[0] + math.cos(a) * 60 * born, BH[1] + math.sin(a) * 60 * born,
                           BH[0] + math.cos(a) * 150 * born, BH[1] + math.sin(a) * 150 * born, pen(GOLD, 5 * lw, 230 * born))
            c.drawCircle(*BH, 42 * born, brush((255, 240, 200)))
    # planètes
    planets = [(P0["c"], P0["r"], 1.0), (P1["c"], P1["r"], reveal), (p2_center(t), P2["r"], reveal)]
    mp, _ = moon_pos(t)
    planets.append((mp, MOON_R, reveal))
    glow_land = 1 - smooth((t - 1.2) / 1.0) if t > 1.2 else 0.0
    for (pc, pr, a) in planets:
        if a <= 0.01:
            continue
        c.drawCircle(*pc, pr, brush((6, 6, 10), 255 * a))
        extra = glow_land if pc == P0["c"] else 0.0
        c.drawCircle(*pc, pr, pen(LINE, (3.2 + 4 * extra) * lw, 240 * a, glow=0))
        c.drawCircle(*pc, pr, pen(CYAN if extra else LINE, 10 * lw, (60 + 180 * extra) * a, glow=8 * lw + 20 * extra))
        for j in range(3):                                          # petits points de repère sur le contour
            q = (pc[0] + math.cos(j * 2.1 + 0.4) * pr, pc[1] + math.sin(j * 2.1 + 0.4) * pr)
            c.drawCircle(*q, 6 * lw, brush((0, 0, 0), 255 * a))
            c.drawCircle(*q, 6 * lw, pen(LINE, 2 * lw, 255 * a))
    # corde : ligne d'orbite à laquelle il s'accroche
    if 78 < t < 90:
        a = smooth((t - 78) / 1.0) * (1 - smooth((t - 88) / 2))
        ra, rb = (BH[0] - 900, BH[1] + 900), (BH[0] + 700, BH[1] + 1000)
        sag = 60 + 40 * math.sin(t * 2.2) if t < 86.5 else 0
        path = skia.Path()
        path.moveTo(*ra)
        mid = lerp(ra, rb, 0.42)
        path.quadTo(mid[0], mid[1] + sag * 2, *rb)
        c.drawPath(path, pen(LINE, 3 * lw, 220 * a))
        for q in (ra, rb):
            c.drawCircle(*q, 8 * lw, pen(LINE, 2.5 * lw, 255 * a))
    # prévisions de trajectoire en pointillés
    for t_show, t_jump, fn in ((20.0, 21.0, lambda u: hero_state(21.0 + 2.5 * u)[0]),
                               (34.0, 36.0, lambda u: hero_state(36.0 + 2.5 * u)[0])):
        if t_show < t < t_jump + 0.2:
            a = smooth((t - t_show) / 0.5)
            for k in range(18):
                q = fn(k / 17)
                c.drawCircle(*q, 5 * lw, brush(CYAN, 170 * a))
    # traînée
    pos, rot, pose, facing, trail, wind = hero_state(t)
    world.trail.append((pos, trail))
    world.trail = world.trail[-90:]
    for i, (q, on) in enumerate(world.trail[:-1]):
        if on and i % 3 == 0:
            a = (i + 1) / len(world.trail)
            c.drawCircle(*q, (2 + 4 * a) * lw, brush(CYAN, 200 * a))
    if 87 < t < 95:                                                 # traînée de lumière pendant la fronde
        pts = [hero_state(t - k * 0.03)[0] for k in range(40)]
        path = skia.Path()
        path.moveTo(*pts[0])
        for q in pts[1:]:
            path.lineTo(*q)
        c.drawPath(path, pen(CYAN, 22 * lw, 140, glow=18 * lw))
        c.drawPath(path, pen((220, 250, 255), 5 * lw, 230))
    # flèche g
    if 7.0 < t < 10.6:
        a = smooth((t - 7.0) / 0.4) * (1 - smooth((t - 10.1) / 0.4))
        tip = (0, -35)
        base = (0, -125)
        c.drawLine(*base, *tip, pen(GOLD, 5 * lw, 255 * a))
        head = skia.Path()
        head.moveTo(tip[0], tip[1] + 6)
        head.lineTo(tip[0] - 14, tip[1] - 16)
        head.lineTo(tip[0] + 14, tip[1] - 16)
        head.close()
        c.drawPath(head, brush(GOLD, 255 * a))
        font = skia.Font(skia.Typeface("DejaVu Serif", skia.FontStyle.Italic()), 44)
        c.drawString("g", 18, -70, font, brush(GOLD, 255 * a))
    # Éclat
    c.save()
    c.translate(*pos)
    c.rotate(rot)
    HERO.draw(c, 0, 0, S, pose, t=t, cape="violet", wind=wind, facing=facing)
    c.restore()
    c.restore()


# ---------------------------------------------------------------- son
def soundtrack(path, duration):
    from satisfying.engine import PROGRESSIONS, Sound
    import wave
    SR = 48000
    sections = [(0, 20, "ré", 0, "cristal", 0.45), (20, 52, "ré", 1, "kalimba", 0.5), (52, 60, "ré", 4, "cristal", 0.6),
                (60, 86.5, "la", 2, "piano doux", 0.75), (87, 105, "ré", 1, "cristal", 0.8), (105, 120, "ré", 4, "cristal", 0.55)]
    cues = [(1.2, 2, 1.0), (7.0, 7, 0.6), (9.4, 4, 0.5), (11.5, 5, 0.5), (12, 7, 0.5), (12.5, 9, 0.5), (13, 10, 0.6),
            (23.5, 3, 0.8), (30.4, 0, 1.0), (38.5, 7, 0.7), (47.0, 4, 0.8), (64, 0, 1.0), (82, 1, 0.9),
            (87.0, 5, 0.9), (87.3, 7, 0.9), (87.6, 9, 0.9), (87.9, 12, 1.0), (98, 7, 0.8), (98.4, 9, 0.8), (98.8, 12, 0.9),
            (108.8, 2, 0.9), (113, 7, 0.5), (116, 9, 0.5)]
    arps = [(12.5, 19.5, 0.25), (21, 52, 0.4), (64, 86, 0.2), (88, 104, 0.25)]
    n = int(duration * SR)
    mix = np.zeros((n, 2))
    for i, (t0, t1, key, prog, timbre, pad) in enumerate(sections):
        snd = Sound(np.random.default_rng(20 + i), key=key, timbre=timbre, prog=PROGRESSIONS[prog])
        snd.bar = 4.0
        for t, step, vel in cues:
            if t0 <= t < t1:
                snd.hit(t, vel, step=step)
        for a0, a1, gap in arps:
            tt = max(a0, t0)
            while tt < min(a1, t1):
                snd.hit(tt, 0.4)
                tt += gap
        if i == 0:
            fr = int(duration * 60)
            def env(keys):
                return [keys_at(keys, k / 60, ease=lambda u: u) for k in range(fr)]
            snd.bed("vent", env([(0, 0.9), (1.2, 1.0), (1.3, 0.1), (10.4, 0.1), (10.8, 0.8), (11.6, 0.2), (20.8, 0.2),
                                 (21.3, 0.8), (23.5, 0.2), (80, 0.3), (86.5, 0.3), (88, 1.0), (95, 0.4), (115.8, 0.2),
                                 (117.5, 1.0), (120, 0.9)]), 1.0)
            snd.bed("océan", env([(0, 0), (60, 0), (64, 1.0), (94, 1.0), (97, 0), (120, 0)]), 1.4)   # grondement
        wav = Path(path).with_name(f"g{i}.wav")
        snd.render(duration, wav, pad_level=pad)
        with wave.open(str(wav)) as w:
            part = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float).reshape(-1, 2)[:n] / 32767
        tt = np.arange(len(part)) / SR
        fade = 1.2
        e = np.clip((tt - (t0 - fade)) / fade, 0, 1) * np.clip(((t1 + fade) - tt) / fade, 0, 1)
        if i == 0:
            e = np.clip(((t1 + fade) - tt) / fade, 0, 1)
        if i == len(sections) - 1:
            e = np.clip((tt - (t0 - fade)) / fade, 0, 1)
        if t0 == 87:                                               # une seconde de silence avant la fronde
            e *= np.clip((tt - 87.0) / 0.05, 0, 1)
        mix[:len(part)] += part * e[:, None] / max(1e-9, np.abs(part).max())
    mix /= max(1e-9, np.abs(mix).max() / 0.9)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--debut", type=float, default=0.0)
    ap.add_argument("--fin", type=float, default=DURATION)
    ap.add_argument("--pas", type=int, default=1, help="une image sur N (brouillon)")
    ap.add_argument("--images", default=None, help="instants (s) à rendre en PNG, séparés par des virgules")
    a = ap.parse_args()
    world = World()
    surf = skia.Surface(W, H)
    if a.images:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for s in a.images.split(","):
            t = float(s)
            world.trail = [(hero_state(max(0, t - k / FPS))[0], hero_state(max(0, t - k / FPS))[4]) for k in range(90, 0, -1)]
            draw_frame(surf.getCanvas(), world, t)
            surf.makeImageSnapshot().save(str(out / f"t{t:06.1f}.png"), skia.kPNG)
        return
    fps = FPS / a.pas
    with tempfile.TemporaryDirectory() as tmp:
        video = Path(tmp) / "v.mp4"
        ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                               "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                               "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps), str(video)], stdin=subprocess.PIPE)
        f = int(a.debut * FPS)
        while f < int(a.fin * FPS):
            draw_frame(surf.getCanvas(), world, f / FPS)
            ff.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
            f += a.pas
        ff.stdin.close()
        ff.wait()
        audio = Path(tmp) / "a.wav"
        soundtrack(audio, DURATION)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-ss", str(a.debut),
                        "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", a.out], check=True)
    print(a.out)


if __name__ == "__main__":
    main()
