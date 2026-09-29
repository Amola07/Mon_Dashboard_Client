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
S = 0.68                                        # taille d'Éclat (≈ 250 unités des mains aux pieds)


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
MOON_ORBIT = (560.0, (2 * math.pi + math.radians(14)) / 8.1)   # rayon, vitesse angulaire (rad/s) autour de P1
MOON_PHASE = math.radians(241) - MOON_ORBIT[1] * 30.4           # un tour complet entre le « bonk » et l'atterrissage
MOON_R = 60
BH = (150.0, -3350.0)
BH_AWAKE = (60.0, 64.0)
BH_COLLAPSE = (95.0, 98.0)


def moon_pos(t):
    a = MOON_PHASE + MOON_ORBIT[1] * t
    return (P1["c"][0] + math.cos(a) * MOON_ORBIT[0], P1["c"][1] + math.sin(a) * MOON_ORBIT[0]), a


def p2_center(t):
    """La troisième planète est entraînée vers le trou noir, puis relâchée quand il s'effondre."""
    u = smooth((t - 68) / 14) * (1 - smooth((t - 96) / 8))
    return lerp(P2["c"], (BH[0] - 520, BH[1] + 420), u * 0.3)


def bh_strength(t):
    return smooth((t - BH_AWAKE[0]) / (BH_AWAKE[1] - BH_AWAKE[0])) * (1 - smooth((t - BH_COLLAPSE[0]) / (BH_COLLAPSE[1] - BH_COLLAPSE[0])))


def surface(planet_c, r, ang):
    """Point de la surface et rotation d'Éclat debout dessus (la tête vers l'extérieur)."""
    return (planet_c[0] + math.cos(ang) * r, planet_c[1] + math.sin(ang) * r), math.degrees(ang) + 90


# ---------------------------------------------------------------- outils de trajectoire
UP = -math.pi / 2


def unit(a):
    return (math.cos(a), math.sin(a))


def vadd(*vs):
    return (sum(v[0] for v in vs), sum(v[1] for v in vs))


def vmul(v, k):
    return (v[0] * k, v[1] * k)


def rotate(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def hermite(p0, v0, p1, v1, t, t0, t1):
    """Courbe d'Hermite : part de p0 à la vitesse v0, arrive en p1 à la vitesse v1 (vitesses continues)."""
    T = t1 - t0
    u = min(max((t - t0) / T, 0.0), 1.0)
    u2, u3 = u * u, u * u * u
    h = (2 * u3 - 3 * u2 + 1, (u3 - 2 * u2 + u) * T, -2 * u3 + 3 * u2, (u3 - u2) * T)
    d = ((6 * u2 - 6 * u) / T, 3 * u2 - 4 * u + 1, (-6 * u2 + 6 * u) / T, 3 * u2 - 2 * u)
    pos = tuple(h[0] * a + h[1] * b + h[2] * c + h[3] * e for a, b, c, e in zip(p0, v0, p1, v1))
    vel = tuple(d[0] * a + d[1] * b + d[2] * c + d[3] * e for a, b, c, e in zip(p0, v0, p1, v1))
    return pos, vel


def turn(a, b, u):
    """De l'angle a vers l'angle b (degrés) par le plus court chemin."""
    return a + ((b - a + 180) % 360 - 180) * u


def fly_rot(vel):
    """En vol (pose « vol », corps presque à l'horizontale), la tête file dans le sens du mouvement."""
    return math.degrees(math.atan2(vel[1], vel[0])) + 10


# ---------------------------------------------------------------- repères du trajet
HOME, ROT0 = surface(P0["c"], P0["r"], UP)
LAND1, ROT1 = surface(P1["c"], P1["r"], math.radians(215))
N1 = unit(math.radians(215))                                    # normale (vers l'extérieur) au point d'atterrissage
ORBIT_R, ORBIT_W = 320.0, 2 * math.pi / 5.0
EXIT_A = UP + 0.6 + 9.5 * ORBIT_W
BONK = 30.4
P2_A = math.radians(20)                                         # là où il s'assoit (le trou noir est dans l'axe)
LAND2_A = math.radians(55)
R_ROPE = 900.0                                                  # ligne d'orbite autour du trou noir
SPIRAL = (86.5, 95.0)
LANDINGS = [1.2, 9.5, 23.5, 33.0, 38.5, 47.0, 108.8]
TAKEOFFS = [8.0, 10.5, 28.0, 36.0, 43.6, 80.0, 116.0]


def orbit(t):
    a = UP + 0.6 + (t - 11.5) * ORBIT_W
    return surface(P0["c"], ORBIT_R, a)[0], vmul(unit(a + math.pi / 2), ORBIT_R * ORBIT_W), a


def moon_ride(t):
    """Debout sur le haut de la lune (point le plus éloigné de la grande planète)."""
    mp, a = moon_pos(t)
    pos, rot = surface(mp, MOON_R, a)
    return pos, rot, vmul(unit(a + math.pi / 2), (MOON_ORBIT[0] + MOON_R) * MOON_ORBIT[1]), a


def moon_bonk():
    mp, a = moon_pos(BONK)
    tau = unit(a + math.pi / 2)                                 # sens de déplacement de la lune
    return vadd(mp, vmul(tau, MOON_R + 45)), tau


def p2_vel(t):
    a, b = p2_center(t - 0.01), p2_center(t + 0.01)
    return ((b[0] - a[0]) / 0.02, (b[1] - a[1]) / 0.02)


def p2_spin(t):
    """Rotation de la troisième planète sous ses pieds quand il court (tapis roulant)."""
    def integ(x):                                              # intégrale de smooth(x)
        if x <= 0:
            return 0.0
        return x ** 3 - x ** 4 / 2 if x < 1 else x - 0.5
    if t <= 80:
        return -2.2 * integ(t - 64.5)
    return -2.2 * (integ(80 - 64.5) + (1 - math.exp(-(t - 80) * 1.5)) / 1.5)


def takeoff_p2():
    pos = surface(p2_center(80.0), P2["r"], P2_A)[0]
    return pos


PHI_H = math.atan2(takeoff_p2()[1] - BH[1], takeoff_p2()[0] - BH[0]) - 0.04
HANG_HANDS = None


def hang(t):
    """Suspendu à la ligne d'orbite par les mains, le corps tiré vers le trou noir."""
    global HANG_HANDS
    if HANG_HANDS is None:
        J = HERO.skeleton("accroche", S, 1, False)
        HANG_HANDS = ((J["arms"][0][2][0] + J["arms"][1][2][0]) / 2, (J["arms"][0][2][1] + J["arms"][1][2][1]) / 2)
    dt = max(0.0, t - 82.0)
    sag = 80 * (1 - math.exp(-3 * dt) * math.cos(6 * dt))
    sway = 10 * math.sin(2.2 * dt) * (1 - math.exp(-2 * dt))
    rot = math.degrees(PHI_H) + 90 + sway
    grip = vadd(BH, vmul(unit(PHI_H), R_ROPE - sag))
    return vadd(grip, vmul(rotate(HANG_HANDS, rot), -1)), rot, sag


def _spiral_table():
    start = hang(SPIRAL[0])[0]
    d0 = math.hypot(start[0] - BH[0], start[1] - BH[1])
    a0 = math.atan2(start[1] - BH[1], start[0] - BH[0])
    up_, rp, r_end, sweep = 0.45, 260.0, 1400.0, math.radians(300)
    u = np.linspace(0, 1, 4001)
    r = np.where(u < up_, rp + (d0 - rp) * np.cos(np.pi / 2 * np.minimum(u / up_, 1)) ** 2,
                 rp + (r_end - rp) * np.array([smooth(x) for x in (u - up_) / (1 - up_)]))
    w = r ** -1.5 * np.array([smooth(x / 0.25) for x in u])
    f = np.concatenate([[0], np.cumsum((w[1:] + w[:-1]) / 2)])
    return u, r, a0 + sweep * f / f[-1]


SPIRAL_TAB = None


def spiral(t):
    """Lâche la corde, plonge vers le trou noir, le frôle à pleine vitesse (fronde) et s'échappe."""
    global SPIRAL_TAB
    if SPIRAL_TAB is None:
        SPIRAL_TAB = _spiral_table()
    uu, rr, aa = SPIRAL_TAB

    def at(tt):
        u = min(max((tt - SPIRAL[0]) / (SPIRAL[1] - SPIRAL[0]), 0.0), 1.0)
        r, a = np.interp(u, uu, rr), np.interp(u, uu, aa)
        return (BH[0] + math.cos(a) * r, BH[1] + math.sin(a) * r)
    p0, p1 = at(t - 0.002), at(t + 0.002)
    return at(t), ((p1[0] - p0[0]) / 0.004, (p1[1] - p0[1]) / 0.004)


# ---------------------------------------------------------------- poses animées (évaluées à l'instant courant)
def waving(tt):
    p = dict(HERO.POSES["salut"])
    p["arm_r"] = (118 + 16 * math.sin(tt * 13), 38 + 22 * math.sin(tt * 13))
    return p


def walking(t0, t1, cycles, amp=1.0):
    def f(tt):
        u = min(max((tt - t0) / (t1 - t0), 0.0), 1.0)
        return HERO.walk(2 * math.pi * cycles * smooth(u), amp * min(1.0, 5.4 * u * (1 - u)))
    return f


def running(tt):
    return HERO.run(2 * math.pi * 2.0 * tt, smooth((tt - 64.2) / 0.5))


def trembling(tt):
    p = HERO.blend(HERO.POSES["debout"], HERO.POSES["surpris"], 0.55)
    p["lean"] = -8 + 2.5 * math.sin(tt * 47)
    p["head"] = -6 + 2 * math.sin(tt * 39)
    return p


def surfing(tt):
    p = HERO.blend(HERO.POSES["etire"], HERO.POSES["triomphe"], 0.5 + 0.5 * math.sin(tt * 2.5))
    p["lean"] = 10 * math.sin(tt * 2.5)
    p["leg_l"], p["leg_r"] = (-22, 30), (22, -30)
    return p


def kicking(tt):
    p = dict(HERO.POSES["accroche"])
    k = 1 - smooth((tt - 84.2) / 0.6)                          # panique, puis se calme quand il a l'idée
    p["leg_l"] = (8 + 30 * k * math.sin(tt * 11), 6 + 25 * k * math.sin(tt * 11 + 1))
    p["leg_r"] = (-8 - 30 * k * math.sin(tt * 11 + 2), -6 - 25 * k * math.sin(tt * 11 + 3))
    return p


def sit(t0, t1, up=False):
    """S'assoit (ou se relève) en douceur."""
    def f(tt):
        u = smooth((tt - t0) / (t1 - t0))
        a, b = (HERO.POSES["assis"], HERO.POSES["debout"]) if up else (HERO.POSES["debout"], HERO.POSES["assis"])
        return HERO.blend(a, b, u)
    return f


def pre(t, t_jump, base):
    """Anticipation : s'accroupit dans les 0,3 s avant un saut."""
    return "accroupi" if t_jump - 0.3 <= t < t_jump else base


# ---------------------------------------------------------------- trajet d'Éclat
def flight(t, t0, t1, p0, v0, p1, v1, rot0=None, rot1=None, wind=1.7, mid="vol", end="saut"):
    pos, vel = hermite(p0, v0, p1, v1, t, t0, t1)
    rot = fly_rot(vel)
    if rot0 is not None:
        rot = turn(rot0, rot, smooth((t - t0) / 0.4))
    if rot1 is not None:
        rot = turn(rot1, rot, smooth((t1 - t) / 0.45))
    pose = "saut" if t - t0 < 0.25 else (end if t1 - t < 0.4 else mid)
    return pos, rot, pose, 1, True, True, wind


def hero_state(t):
    """(pieds, rotation en degrés, pose, sens, en l'air, traînée, vent de cape) à l'instant t du récit."""
    wind = 0.9
    if t < 1.2:                                                    # chute depuis le haut de l'écran
        u = t / 1.2
        return (0.0, -140 - 900 * (1 - u * u)), 8 * math.sin(t * 9), "panique" if t < 0.95 else "saut", 1, True, False, 1.8
    if t < 3.0:
        pose = "atterrit" if t < 1.5 else (waving if 2.1 < t < 2.8 else "debout")
        return HOME, ROT0, pose, 1, False, False, wind
    if t < 7.0:                                                    # tour de la planète à pied
        u = smooth((t - 3.0) / 4.0)
        pos, rot = surface(P0["c"], P0["r"], UP + 2 * math.pi * u)
        return pos, rot, walking(3.0, 7.0, 6.0), 1, False, False, 1.1
    if t < 8.0:
        return HOME, ROT0, pre(t, 8.0, "debout"), 1, False, False, wind
    if t < 9.5:                                                    # petit saut
        u = (t - 8.0) / 1.5
        return (HOME[0], HOME[1] - 600 * u * (1 - u)), ROT0, "saut", 1, True, True, 1.2
    if t < 10.5:
        return HOME, ROT0, pre(t, 10.5, "atterrit" if t < 9.8 else "reflexion"), 1, False, False, wind
    if t < 11.5:                                                   # grand saut qui le met en orbite
        u = t - 10.5
        a = UP + 0.5434 * u * u + 0.0566 * u ** 3
        pos, rot = surface(P0["c"], 140 + 180 * (1 - (1 - u) ** 2), a)
        return pos, rot + 10 * smooth(u), HERO.blend(HERO.POSES["saut"], HERO.POSES["vol"], smooth(u / 0.9)), 1, True, True, 1.6
    if t < 21.0:                                                   # en orbite autour de la petite planète
        pos, vel, a = orbit(t)
        return pos, fly_rot(vel), "vol", 1, True, True, 1.7
    if t < 23.5:                                                   # vers la grande planète
        p0, v0, _ = orbit(21.0)
        return flight(t, 21.0, 23.5, p0, v0, LAND1, vmul(N1, -330), rot1=ROT1, wind=1.8)
    if t < 28.0:
        pose = "atterrit" if t < 23.8 else (waving if 24.6 < t < 26.2 else "debout")
        return LAND1, ROT1, pre(t, 28.0, pose), 1, False, False, wind
    miss, tau = moon_bonk()
    v_miss = (-60.0, 380.0)
    if t < BONK:                                                   # vise la lune… qui arrive par derrière
        return flight(t, 28.0, BONK, LAND1, vmul(N1, 480), miss, v_miss, rot0=ROT1, wind=1.6, end="vol")
    if t < 33.0:                                                   # BONK : projeté, tournoie, retombe
        u = (t - BONK) / 2.6
        kick = vadd(vmul(tau, 600), vmul(unit(moon_pos(BONK)[1]), 800))  # projeté vers l'avant et vers l'extérieur
        pos, _ = hermite(miss, kick, LAND1, vmul(N1, -260), t, BONK, 33.0)
        rb = fly_rot(v_miss)
        total = ((ROT1 - rb + 180) % 360 - 180) + 720
        pose = "panique" if t < 32.5 else "saut"
        return pos, rb + total * (1 - (1 - u) ** 3), pose, 1, True, True, 1.2
    if t < 36.0:
        pose = "atterrit" if t < 33.3 else ("tete" if t < 34.3 else "reflexion")
        return LAND1, ROT1, pre(t, 36.0, pose), 1, False, False, wind
    if t < 38.5:                                                   # saute au bon moment : atterrit sur la lune
        dest, rot_d, vel_d, a = moon_ride(38.5)
        return flight(t, 36.0, 38.5, LAND1, vmul(N1, 450), dest, vadd(vel_d, vmul(unit(a), -250)), ROT1, rot_d)
    if t < 43.6:                                                   # surfe sur la lune, bras écartés
        pos, rot, _, _ = moon_ride(t)
        return pos, rot, pre(t, 43.6, "atterrit" if t < 38.8 else surfing), 1, False, False, 1.3
    land2, rot2 = surface(P2["c"], P2["r"], LAND2_A)
    if t < 47.0:                                                   # s'élance de la lune vers la troisième planète
        p0, r0, v_r, a = moon_ride(43.6)
        return flight(t, 43.6, 47.0, p0, vadd(v_r, vmul(unit(a), 420)), land2, vmul(unit(LAND2_A), -300), r0, rot2, 1.9)
    if t < 80.0:
        p2c = p2_center(t)
        if t < 47.4:
            ang, pose, facing = LAND2_A, "atterrit", 1
        elif t < 49.6:                                             # quelques pas vers le haut de la planète
            ang = LAND2_A + (P2_A - LAND2_A) * smooth((t - 47.4) / 2.2)
            pose, facing = walking(47.4, 49.6, 1.5, 0.75), -1
        else:
            ang, facing = P2_A, (-1 if t < 64.2 else 1)
            if t < 51.5:
                pose = "debout"
            elif t < 60.0:
                pose = sit(51.5, 52.2)
            elif t < 61.3:
                pose = "surpris"
            elif t < 64.2:
                pose = trembling
            else:
                pose = running
        pos, rot = surface(p2c, P2["r"], ang)
        return pos, rot, pre(t, 80.0, pose), facing, False, False, 1.0 + 1.6 * bh_strength(t)
    if t < 82.0:                                                   # saute, aspiré, se rattrape à la ligne d'orbite
        p0 = takeoff_p2()
        p1, r1, _ = hang(82.0)
        v1 = vmul(unit(PHI_H + math.pi), 320)
        return flight(t, 80.0, 82.0, p0, vadd(p2_vel(80.0), vmul(unit(P2_A), 380)), p1, v1,
                      math.degrees(P2_A) + 90, r1, 2.2, mid="panique", end="accroche")
    if t < SPIRAL[0]:
        pos, rot, _ = hang(t)
        return pos, rot, kicking, 1, True, False, 2.4
    if t < SPIRAL[1]:                                              # lâche prise… et la fronde
        pos, vel = spiral(t)
        r_h = hang(SPIRAL[0])[1]
        speed = math.hypot(*vel)
        rot = turn(r_h, fly_rot(vel) if speed > 1 else r_h, smooth((t - SPIRAL[0]) / 1.0))
        return pos, rot, "etire" if t < 87.0 else "vol", 1, True, True, 2.4
    if t < 108.8:                                                  # retour vers la petite planète
        p0, v0 = spiral(SPIRAL[1])
        return flight(t, SPIRAL[1], 108.8, p0, v0, HOME, (200.0, 300.0), rot1=ROT0, wind=1.6,
                      mid="triomphe" if t < 98.0 else "vol")
    if t < 116.0:
        if t < 109.2:
            pose = "atterrit"
        elif t < 113.0:
            pose = sit(109.2, 109.9)
        elif t < 114.0:
            pose = sit(113.0, 113.5, up=True)
        elif t < 115.4:
            pose = waving
        else:
            pose = "debout"
        return HOME, ROT0, pre(t, 116.0, pose), 1, False, False, wind
    tau_ = t - 116.0                                               # saute hors de l'écran : la vidéo boucle
    return (HOME[0], HOME[1] - (500 * tau_ + 300 * tau_ * tau_)), ROT0, "saut", 1, True, True, 1.8


def pose_of(spec, t):
    return spec(t) if callable(spec) else HERO.as_pose(spec)


def smoothed_hero(t):
    """Pose, hauteur de hanche et rotation lissées sur les 0,4 s précédentes : aucune cassure entre deux poses.
    Les cycles (marche, course…) sont évalués à l'instant courant pour garder toute leur amplitude."""
    pos, rot, spec, facing, air, trail, wind = hero_state(t)
    acc, lift, drot, wsum = None, 0.0, 0.0, 0.0
    for k in range(24):
        _, r_k, spec_k, _, air_k, *_ = hero_state(max(0.0, t - k / 60))
        pd = pose_of(spec_k, t)
        w = math.exp(-k / 6)
        if acc is None:
            acc = {key: (tuple(v * w for v in val) if isinstance(val, tuple) else val * w) for key, val in pd.items()}
        else:
            for key, val in pd.items():
                acc[key] = tuple(a + v * w for a, v in zip(acc[key], val)) if isinstance(val, tuple) else acc[key] + val * w
        lift += HERO.lift_of(pd, S, not air_k) * w
        drot += ((r_k - rot + 180) % 360 - 180) * w
        wsum += w
    pose = {key: (tuple(v / wsum for v in val) if isinstance(val, tuple) else val / wsum) for key, val in acc.items()}
    return pos, rot + drot / wsum, pose, facing, air, trail, wind, lift / wsum


# ---------------------------------------------------------------- jeu d'acteur : expressions, symboles, regard
EXPR = [(0, "peur"), (1.2, "surpris"), (1.9, "joie"), (3.0, "curieux"), (5.2, "joie"), (7.0, "curieux"),
        (7.7, "decide"), (8.0, "joie"), (9.5, "surpris"), (9.9, "curieux"), (10.2, "decide"), (11.5, "joie"),
        (16.0, "surpris"), (17.6, "joie"), (20.0, "decide"), (23.5, "joie"), (26.2, "curieux"), (27.5, "decide"),
        (29.8, "surpris"), (BONK, "etourdi"), (34.3, "colere"), (35.1, "decide"), (38.5, "joie"), (43.3, "decide"),
        (43.8, "joie"), (49.6, "curieux"), (51.5, "fier"), (55.0, "neutre"), (60.0, "surpris"), (61.3, "peur"),
        (84.4, "decide"), (88.5, "decide"), (90.3, "joie"), (92.0, "fier"), (95.0, "joie"), (97.6, "surpris"),
        (99.5, "joie"), (108.8, "joie"), (109.5, "fier"), (113.0, "neutre"), (114.0, "clin"), (115.4, "decide"),
        (116.0, "joie")]
EMOTES = [(1.2, 1.9, "!"), (7.2, 7.7, "?"), (9.7, 10.1, "?"), (10.1, 10.5, "!"), (12.0, 13.2, "eclats"),
          (16.2, 17.4, "!"), (26.4, 27.4, "?"), (29.9, BONK, "!"), (BONK + 0.05, 34.2, "etoiles"), (35.0, 35.6, "!"),
          (38.6, 39.8, "eclats"), (60.2, 61.2, "!"), (61.3, 80.0, "sueur"), (84.4, 85.2, "!"), (90.4, 92.0, "eclats"),
          (97.8, 98.8, "!"), (109.5, 110.8, "eclats")]
LOOK = [(0, (0, 0.8)), (1.9, (0, 0)), (7.1, (0.2, 0.9)), (8.0, (0, 0)), (9.7, (0, -0.8)), (10.2, (0, 0)),
        (16.0, (0.6, -0.6)), (17.6, (0, 0)), (26.4, (0.7, -0.5)), (27.4, (0, 0)), (34.4, (0.6, -0.6)), (35.6, (0, 0)),
        (51.5, (0.3, -0.9)), (60.0, (0.3, -0.9)), (61.3, (0.6, -0.3)), (64.2, (-0.9, -0.2)), (80.0, (0, 0)),
        (82.0, (0, -0.9)), (84.4, (0, 0.9)), (86.5, (0, 0)), (113.0, (0, 0)), (114.0, (0, 0))]


def acting(t):
    expr = EXPR[0][1]
    for t0, name in EXPR:
        if t >= t0:
            expr = name
    emote = None
    for t0, t1, kind in EMOTES:
        if t0 <= t < t1:
            emote = (kind, t - t0)
    return expr, emote, keys_at(LOOK, t)


def squash_at(t):
    """Étirement juste avant l'impact, écrasement élastique à l'atterrissage, étirement au décollage."""
    sx = sy = 1.0
    for tl in LANDINGS:
        dt = t - tl
        if -0.18 < dt < 0:
            k = 1 + dt / 0.18
            sy, sx = 1 + 0.12 * k, 1 - 0.06 * k
        elif 0 <= dt < 0.7:
            k = math.exp(-dt * 7) * math.cos(dt * 17)
            sy, sx = 1 - 0.3 * k, 1 + 0.22 * k
    for to in TAKEOFFS:
        dt = t - to
        if 0 <= dt < 0.3:
            k = 1 - dt / 0.3
            sy, sx = 1 + 0.2 * k, 1 - 0.1 * k
    return sx, sy


# ---------------------------------------------------------------- temps : ralenti au passage près du trou noir
SLOW = (89.2, 92.4, 0.72)                                       # début, fin, force (vitesse mini = 1 - force)
CATCH = (92.4, 97.4)                                            # le récit rattrape son retard


def story_time(t):
    def g(x, L):
        return x / 2 - L / (4 * math.pi) * math.sin(2 * math.pi * x / L)
    s0, s1, a = SLOW
    L1, L2 = s1 - s0, CATCH[1] - CATCH[0]
    if t < s0 or t >= CATCH[1]:
        return t
    if t < s1:
        return t - a * g(t - s0, L1)
    return t - a * L1 / 2 + (a * L1 / L2) * g(t - CATCH[0], L2)


# ---------------------------------------------------------------- caméra : (centre, zoom, rotation)
def body_offset(t):
    """Décalage vers le centre du corps (orientation moyennée : pas de tangage quand il tournoie)."""
    x = y = wsum = 0.0
    for k in range(10):
        _, r_k, *_ = hero_state(max(0.0, t - k * 0.05))
        w = math.exp(-k / 4)
        u = unit(math.radians(r_k - 90))
        x, y, wsum = x + u[0] * w, y + u[1] * w, wsum + w
    return (110 * x / wsum, 110 * y / wsum)


FOLLOW = [
    (0.0, (0.0, -420.0), 1.25), (1.2, (0.0, -150.0), 1.5), (3.0, (0.0, -80.0), 1.5), (7.0, (0.0, -80.0), 1.5),
    (10.5, (0.0, -140.0), 1.35), (15.0, (0.0, -60.0), 0.95), (19.0, (300.0, -700.0), 0.65),
    (22.0, (500.0, -800.0), 0.9), (26.0, None, 1.05), (30.0, None, 1.0), (36.0, None, 0.95), (43.6, None, 1.0),
    (46.2, None, 0.75), (52.0, None, 1.2), (58.0, ((-650 + 150) / 2, (-1900 - 3350) / 2 + 200), 0.36),
    (66.0, None, 0.8), (80.0, None, 0.78), (84.0, None, 0.95), (87.0, None, 0.9), (89.5, None, 0.62),
    (92.0, None, 0.5), (95.0, (150.0, -3350.0), 0.45), (99.0, (150.0, -3100.0), 0.42), (104.0, None, 0.7),
    (110.0, (0.0, -120.0), 1.35), (116.0, (0.0, -150.0), 1.4), (120.0, (0.0, -420.0), 1.25),
]


def camera(t):
    pos = hero_state(t)[0]
    off = body_offset(t)
    here = (pos[0] + off[0], pos[1] + off[1])
    center, zoom = here, 1.0
    for (t0, c0, z0), (t1, c1, z1) in zip(FOLLOW, FOLLOW[1:]):
        if t0 <= t <= t1:
            u = smooth((t - t0) / (t1 - t0))
            center, zoom = lerp(c0 or here, c1 or here, u), lerp(z0, z1, u)
            break
    angle = 0.0
    if 3.0 <= t <= 7.2:                                            # la caméra tourne avec lui autour de la planète
        angle = -(360 * smooth((t - 3.0) / 4.0))
        center = lerp(center, P0["c"], smooth((t - 3.0) / 0.5) * (1 - smooth((t - 6.6) / 0.5)))
    shake = 7 * bh_strength(t) * (1 if 60 < t < 95 else 0)
    for ti, amp in [(tl, 16) for tl in LANDINGS] + [(BONK, 34), (BH_COLLAPSE[1], 40)]:
        dt = t - ti
        if 0 <= dt < 0.6:
            shake += amp * math.exp(-dt * 9)
    center = (center[0] + shake * math.sin(t * 37) / zoom, center[1] + shake * math.cos(t * 29) / zoom)
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


def ring(c, center, radius, color, width, alpha, glow=0.0):
    if alpha > 1 and radius > 0:
        if glow:
            c.drawCircle(*center, radius, pen(color, width * 3, alpha * 0.5, glow=glow))
        c.drawCircle(*center, radius, pen(color, width, alpha))


def draw_impacts(c, t, lw):
    """Poussière, étincelles et éclair au contact du sol."""
    for tl in LANDINGS:
        dt = t - tl
        if not 0 <= dt < 0.8:
            continue
        pos, rot, *_ = hero_state(tl)
        e = 1 - (1 - dt / 0.8) ** 3
        fade = 1 - dt / 0.8
        c.save()
        c.translate(*pos)
        c.rotate(rot)
        c.drawCircle(0, 0, 70 + 60 * e, brush(CYAN, 150 * fade * fade, glow=40))
        c.drawOval(skia.Rect.MakeLTRB(-60 - 260 * e, -10 - 22 * e, 60 + 260 * e, 10 + 22 * e),
                   pen(LINE, 3 * lw, 210 * fade))
        for i in range(10):
            a = math.radians(-172 + i * 18 + 5 * math.sin(i * 7.3))
            r0, r1 = 40 + 170 * e, 40 + 170 * e + 50 * fade
            c.drawLine(math.cos(a) * r0, math.sin(a) * r0 * 0.7, math.cos(a) * r1, math.sin(a) * r1 * 0.7,
                       pen((255, 240, 200) if i % 2 else CYAN, 3.2 * lw, 255 * fade))
        c.restore()
    dt = t - BONK                                                  # le choc avec la lune
    if 0 <= dt < 1.0:
        miss, tau = moon_bonk()
        p = vadd(miss, vmul(tau, -30))
        fade = 1 - dt
        c.drawCircle(*p, 60 + 260 * dt, brush((255, 240, 210), 200 * fade ** 2, glow=60))
        for i in range(14):
            a = i * 2 * math.pi / 14 + 0.2
            r0, r1 = 30 + 300 * dt, 30 + 300 * dt + 90 * fade
            c.drawLine(p[0] + math.cos(a) * r0, p[1] + math.sin(a) * r0, p[0] + math.cos(a) * r1,
                       p[1] + math.sin(a) * r1, pen(GOLD if i % 2 else LINE, 4 * lw, 255 * fade))


def draw_rope(c, t, lw, hands):
    """Ligne d'orbite autour du trou noir : il s'y accroche comme à une corde (elle passe par ses mains)."""
    if not 76.0 < t < 90.0:
        return
    a = smooth((t - 76.0) / 1.5) * (1 - smooth((t - 88.0) / 2.0))
    drawn = smooth((t - 76.0) / 2.5)
    if t < SPIRAL[0] and t >= 82.0 and hands is not None:
        rho = math.hypot(hands[0] - BH[0], hands[1] - BH[1])
        phi = math.atan2(hands[1] - BH[1], hands[0] - BH[0])
        dent = rho - R_ROPE
    elif t >= SPIRAL[0]:
        dt = t - SPIRAL[0]
        phi, dent = PHI_H, -hang(SPIRAL[0])[2] * math.exp(-4 * dt) * math.cos(10 * dt)
    else:
        phi, dent = PHI_H, 0.0
    n = 240
    path = skia.Path()
    for i in range(n + 1):
        psi = PHI_H + math.pi * drawn * (2 * i / n - 1)
        d = (psi - phi + math.pi) % (2 * math.pi) - math.pi
        r = R_ROPE + dent * math.exp(-(d / 0.28) ** 2)
        q = (BH[0] + math.cos(psi) * r, BH[1] + math.sin(psi) * r)
        path.moveTo(*q) if i == 0 else path.lineTo(*q)
    c.drawPath(path, pen((200, 190, 255), 9 * lw, 110 * a, glow=8 * lw))
    c.drawPath(path, pen(LINE, 3 * lw, 235 * a))
    for i in range(12):                                            # points réguliers, comme les sommets du style
        psi = PHI_H + math.pi * drawn * (2 * (i + 0.5) / 12 - 1)
        d = (psi - phi + math.pi) % (2 * math.pi) - math.pi
        r = R_ROPE + dent * math.exp(-(d / 0.28) ** 2)
        q = (BH[0] + math.cos(psi) * r, BH[1] + math.sin(psi) * r)
        c.drawCircle(*q, 7 * lw, brush((0, 0, 0), 255 * a))
        c.drawCircle(*q, 7 * lw, pen(LINE, 2.2 * lw, 255 * a))


def draw_speed_lines(c, t, lw):
    p1 = hero_state(t)[0]
    p0 = hero_state(max(0.0, t - 1 / 60))[0]
    vel = ((p1[0] - p0[0]) * 60, (p1[1] - p0[1]) * 60)
    speed = math.hypot(*vel)
    if speed < 520:
        return
    a = min(1.0, (speed - 520) / 700)
    d = (vel[0] / speed, vel[1] / speed)
    n = (-d[1], d[0])
    rng = np.random.default_rng(int(t * 24))
    center = vadd(p1, vmul(d, 60))
    for _ in range(11):
        off, back = rng.uniform(-1, 1) * 150, rng.uniform(60, 320)
        length = rng.uniform(0.08, 0.2) * min(speed, 2600)
        s = vadd(center, vmul(d, -back), vmul(n, off))
        e = vadd(s, vmul(d, -length))
        c.drawLine(*s, *e, pen(LINE, 2.6 * lw, 190 * a))


def draw_frame(c, world, t):
    """Une image, à l'instant t du récit."""
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
        path.addArc(skia.Rect.MakeLTRB(-ORBIT_R, -ORBIT_R, ORBIT_R, ORBIT_R), math.degrees(UP + 0.6), 360 * drawn)
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
        ring_r = skia.Rect.MakeLTRB(BH[0] - r * 2.4, BH[1] - r * 0.8, BH[0] + r * 2.4, BH[1] + r * 0.8)
        c.drawOval(ring_r, pen(VIOLET, 14 * lw + r * 0.12, 200 * k_bh, glow=r * 0.25))
        c.drawOval(ring_r, pen((230, 200, 255), 3 * lw, 230 * k_bh))
        c.drawCircle(*BH, r, brush((0, 0, 0)))
        c.drawCircle(*BH, r * 1.08, pen((240, 230, 255), 2.2 * lw, 220 * k_bh))
    dt = t - 60.4                                                  # réveil : une onde violette
    if 0 <= dt < 2.0:
        ring(c, BH, 120 + 1600 * (1 - (1 - dt / 2) ** 2), VIOLET, 6 * lw, 230 * (1 - dt / 2), glow=20 * lw)
    # effondrement → onde de choc → nouvelle étoile
    if t >= BH_COLLAPSE[0]:
        flash = smooth((t - BH_COLLAPSE[1] + 0.4) / 0.5) * (1 - smooth((t - BH_COLLAPSE[1] - 0.4) / 2.0))
        born = smooth((t - BH_COLLAPSE[1]) / 2.0)
        if flash > 0:                                              # éclair : cœur blanc, halo chaud qui s'estompe
            R = 200 + 900 * flash
            glow = skia.Paint(AntiAlias=True)
            glow.setShader(skia.GradientShader.MakeRadial(
                skia.Point(*BH), R, [col((255, 255, 255), 250 * flash), col((255, 226, 170), 120 * flash),
                                     col((255, 200, 120), 0)], [0.0, 0.22, 1.0]))
            glow.setBlendMode(skia.BlendMode.kPlus)
            c.drawCircle(*BH, R, glow)
        dt = t - BH_COLLAPSE[1]
        if 0 <= dt < 2.6:
            e = 1 - (1 - dt / 2.6) ** 2
            ring(c, BH, 80 + 3600 * e, (255, 236, 200), 10 * lw, 255 * (1 - dt / 2.6), glow=30 * lw)
            ring(c, BH, 60 + 2600 * e, GOLD, 4 * lw, 200 * (1 - dt / 2.6))
        if born > 0:
            c.drawCircle(*BH, 150 * born, brush(GOLD, 120 * born, glow=90))
            for k in range(12):
                a = 2 * math.pi * k / 12 + t * 0.2
                c.drawLine(BH[0] + math.cos(a) * 60 * born, BH[1] + math.sin(a) * 60 * born,
                           BH[0] + math.cos(a) * 150 * born, BH[1] + math.sin(a) * 150 * born, pen(GOLD, 5 * lw, 230 * born))
            c.drawCircle(*BH, 42 * born, brush((255, 240, 200)))
    # planètes (points de repère sur le contour ; la troisième tourne sous ses pieds quand il court)
    mp, _ = moon_pos(t)
    planets = [(P0["c"], P0["r"], 1.0, 0.0), (P1["c"], P1["r"], reveal, 0.0), (p2_center(t), P2["r"], reveal, p2_spin(t)),
               (mp, MOON_R, reveal, 0.0)]
    glow_land = 1 - smooth((t - 1.2) / 1.0) if t > 1.2 else 0.0
    for (pc, pr, a, spin) in planets:
        if a <= 0.01:
            continue
        c.drawCircle(*pc, pr, brush((6, 6, 10), 255 * a))
        extra = glow_land if pc == P0["c"] else 0.0
        c.drawCircle(*pc, pr, pen(LINE, (3.2 + 4 * extra) * lw, 240 * a, glow=0))
        c.drawCircle(*pc, pr, pen(CYAN if extra else LINE, 10 * lw, (60 + 180 * extra) * a, glow=8 * lw + 20 * extra))
        for j in range(3 if pr > 100 else 2):
            q = (pc[0] + math.cos(j * 2.1 + 0.4 + spin) * pr, pc[1] + math.sin(j * 2.1 + 0.4 + spin) * pr)
            c.drawCircle(*q, 6 * lw, brush((0, 0, 0), 255 * a))
            c.drawCircle(*q, 6 * lw, pen(LINE, 2 * lw, 255 * a))
    # prévisions de trajectoire en pointillés
    for t_show, t_jump, t_end in ((20.0, 21.0, 23.5), (34.4, 36.0, 38.5)):
        if t_show < t < t_jump + 0.3:
            a = smooth((t - t_show) / 0.5) * (1 - smooth((t - t_jump) / 0.3))
            for k in range(18):
                q = hero_state(t_jump + (t_end - t_jump) * k / 17)[0]
                c.drawCircle(*q, 5 * lw, brush(CYAN, 170 * a))
    # Éclat : état lissé, squelette, mains (pour la corde)
    pos, rot, pose, facing, air, trail, wind, lift = smoothed_hero(t)
    sq = squash_at(t)
    J = HERO.skeleton(pose, S, facing, True, lift)
    hm = ((J["arms"][0][2][0] + J["arms"][1][2][0]) / 2 * sq[0], (J["arms"][0][2][1] + J["arms"][1][2][1]) / 2 * sq[1])
    draw_rope(c, t, lw, vadd(pos, rotate(hm, rot)))
    # traînée
    world.trail.append((pos, trail))
    world.trail = world.trail[-90:]
    for i, (q, on) in enumerate(world.trail[:-1]):
        if on and i % 3 == 0:
            a = (i + 1) / len(world.trail)
            c.drawCircle(*q, (2 + 4 * a) * lw, brush(CYAN, 200 * a))
    if SPIRAL[0] + 0.5 < t < SPIRAL[1]:                              # traînée de lumière pendant la fronde
        a = smooth((t - SPIRAL[0] - 0.5) / 0.6)
        pts = [hero_state(max(SPIRAL[0], t - k * 0.03))[0] for k in range(40)]
        path = skia.Path()
        path.moveTo(*pts[0])
        for q in pts[1:]:
            path.lineTo(*q)
        c.drawPath(path, pen(CYAN, 22 * lw, 140 * a, glow=18 * lw))
        c.drawPath(path, pen((220, 250, 255), 5 * lw, 230 * a))
    draw_speed_lines(c, t, lw)
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
    expr, emote, look = acting(t)
    c.save()
    c.translate(*pos)
    c.rotate(rot)
    HERO.draw(c, 0, 0, S, pose, t=t, cape="violet", wind=wind, facing=facing, expr=expr, look=look,
              squash=sq, emote=emote, lift=lift)
    c.restore()
    draw_impacts(c, t, lw)
    c.restore()


# ---------------------------------------------------------------- son
def soundtrack(path, duration):
    from satisfying.engine import PROGRESSIONS, Sound
    import wave
    SR = 48000
    # (début, fin, tonalité, progression, timbre, nappe) ; silence entre 85,3 et 89,6 : il lâche la corde et plonge
    sections = [(0, 20, "ré", 0, "cristal", 0.45), (20, 52, "ré", 1, "kalimba", 0.5), (52, 60, "ré", 4, "cristal", 0.6),
                (60, 85.3, "la", 2, "piano doux", 0.75), (89.6, 105, "ré", 1, "cristal", 0.8), (105, 120, "ré", 4, "cristal", 0.55)]
    cues = [(1.2, 2, 1.0), (7.0, 7, 0.6), (9.5, 4, 0.6), (11.5, 5, 0.5), (12, 7, 0.5), (12.5, 9, 0.5), (13, 10, 0.6),
            (23.5, 3, 0.8), (30.4, 0, 1.0), (33.0, 2, 0.7), (38.5, 7, 0.7), (43.6, 9, 0.6), (47.0, 4, 0.8), (60.4, 0, 0.9), (64, 0, 1.0),
            (80, 3, 0.8), (82, 1, 0.9), (84.4, 7, 0.6),
            (89.6, 5, 0.8), (89.9, 7, 0.85), (90.2, 9, 0.9), (90.8, 12, 1.0), (98, 7, 0.8), (98.4, 9, 0.8), (98.8, 12, 0.9),
            (108.8, 2, 0.9), (113, 7, 0.5), (116, 9, 0.5)]
    arps = [(12.5, 19.5, 0.25), (21, 52, 0.4), (64, 85, 0.2), (91.2, 104, 0.25)]
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
                                 (21.3, 0.8), (23.5, 0.2), (80, 0.3), (85, 0.5), (86.5, 0.6), (88.5, 0.9), (90.8, 1.0),
                                 (93, 0.5), (95, 0.4), (115.8, 0.2), (117.5, 1.0), (120, 0.9)]), 1.0)
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
        if t0 == 89.6:                                             # la musique éclate d'un coup au passage de la fronde
            e *= np.clip((tt - 89.6) / 0.05, 0, 1)
        mix[:len(part)] += part * e[:, None] / max(1e-9, np.abs(part).max())
    mix /= max(1e-9, np.abs(mix).max() / 0.9)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def render_video(debut, fin, pas, path):
    """Rend [debut, fin[ (temps du film) en vidéo muette."""
    world = World()
    surf = skia.Surface(W, H)
    fps = FPS / pas
    f = int(round(debut * FPS))
    world.trail = [(hero_state(story_time(max(0, (f - k) / FPS)))[0], hero_state(story_time(max(0, (f - k) / FPS)))[5])
                   for k in range(90, 0, -1)] if f > 0 else []
    ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps), str(path)], stdin=subprocess.PIPE)
    while f < int(round(fin * FPS)):
        draw_frame(surf.getCanvas(), world, story_time(f / FPS))
        ff.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
        f += pas
    ff.stdin.close()
    ff.wait()
    return str(path)


def _render_part(args):
    return render_video(*args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--debut", type=float, default=0.0)
    ap.add_argument("--fin", type=float, default=DURATION)
    ap.add_argument("--pas", type=int, default=1, help="une image sur N (brouillon)")
    ap.add_argument("--morceaux", type=int, default=1, help="nombre de morceaux rendus en parallèle")
    ap.add_argument("--images", default=None, help="instants (s) à rendre en PNG, séparés par des virgules")
    a = ap.parse_args()
    if a.images:
        world = World()
        surf = skia.Surface(W, H)
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for s in a.images.split(","):
            t = float(s)
            world.trail = [(hero_state(story_time(max(0, t - k / FPS)))[0], hero_state(story_time(max(0, t - k / FPS)))[5])
                           for k in range(90, 0, -1)]
            draw_frame(surf.getCanvas(), world, story_time(t))
            surf.makeImageSnapshot().save(str(out / f"t{t:06.1f}.png"), skia.kPNG)
        return
    with tempfile.TemporaryDirectory() as tmp:
        n = max(1, a.morceaux)
        frames = int(round(a.debut * FPS)), int(round(a.fin * FPS))
        cuts = [frames[0] + (frames[1] - frames[0]) * i // n for i in range(n + 1)]
        cuts = [c - (c - frames[0]) % a.pas for c in cuts[:-1]] + [cuts[-1]]
        parts = [(cuts[i] / FPS, cuts[i + 1] / FPS, a.pas, Path(tmp) / f"v{i}.mp4") for i in range(n)]
        if n == 1:
            render_video(*parts[0])
        else:
            import multiprocessing as mp
            with mp.get_context("fork").Pool(n) as pool:
                pool.map(_render_part, parts)
        video = Path(tmp) / "v.mp4"
        lst = Path(tmp) / "liste.txt"
        lst.write_text("".join(f"file '{p[3]}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(video)], check=True)
        audio = Path(tmp) / "a.wav"
        soundtrack(audio, DURATION)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-ss", str(a.debut),
                        "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", a.out], check=True)
    print(a.out)


if __name__ == "__main__":
    main()
