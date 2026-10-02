"""Épisode 12 complet en style « Constellation » (particules), calé sur la voix d'origine.

    python -m films.episodes.ep12_pyramide.constellation_ep output/ep12_constellation.mp4 [--from T --to T] [--still t1,t2]
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import skia

from films import montage_ia as MI
from films.constellation import corps as CO
from films.constellation import formes as F
from films.constellation import humain as HU
from films.constellation import moteur as M
from films.episodes.ep12_pyramide import constellation_v2 as V2
from films.episodes.ep12_pyramide.montage import SEG

HERE = os.path.dirname(os.path.abspath(__file__))
END = 125.23
g = np.random.default_rng(42)
BODY = {m: HU.Humain(12000, seed=i, modele=m) for i, m in enumerate(("qt_male", "qt_female", "mh"))}
MOV = {}


def mov(name):
    if name not in MOV:
        MOV[name] = CO.Mouvement(name)
    return MOV[name]


def person(fr, body, motion, t, pos, yaw, f0=0, alpha=0.18, col=M.BLUE_HI, loop=True, speed=1.0, in_place=True,
           shear=None, scale=1.0, warm=8):
    mv = mov(motion)
    P = mv.at(f0 / 30 + t * speed, loop=loop, in_place=in_place)
    if not in_place:
        P = P - [mv.P[int(f0), 0, 0], mv.P[int(f0), 0, 1], 0]
    c, s = math.cos(yaw), math.sin(yaw)
    Q = (P * scale) @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T + pos
    if shear is not None:
        Q[:, 2] += (Q - pos) @ shear
    pts = BODY[body].points(Q)
    if shear is not None:
        pts[:, 2] += (pts - pos) @ shear * 0
    fr.points(pts, col, alpha, warm_near=warm)
    return Q


def flame(fr, p, t, k=1.0, n=1200, seed=0, rays=False):
    rr = np.random.default_rng(seed + int(t * 30))
    pts = np.asarray(p) + rr.normal(0, 1, (n, 3)) * [0.06 * k, 0.06 * k, 0.15 * k] + [0, 0, 0.1 * k]
    fr.points(pts, M.ORANGE, 0.6 * (1 + 0.25 * math.sin(t * 23 + seed)), size=1.3)
    if rays:
        fr.rays(p, 0.35, 0.25)


def cam(keys, tl, ap=((0, 4.0),), fog=None, size=2.2):
    pos = M.keyed(tl, [(k[0], k[1]) for k in keys])
    tgt = M.keyed(tl, [(k[0], k[2]) for k in keys])
    fov = float(M.keyed(tl, [(k[0], k[3]) for k in keys]))
    d = float(np.linalg.norm(tgt - pos))
    fn, ff = fog if fog else (1e9, 2e9)
    return M.look_at(pos, tgt, fov), M.Lens(focus=d, aperture=float(M.keyed(tl, list(ap))), fog_near=fn, fog_far=ff, size=size)


def fin(fr, t, exposure=2.6, trail=None):
    return fr.finish(exposure=exposure, bloom=1.0, seed=int(t * 30), trail=trail)


# ================================================================== décors partagés
CHAMBER, CH_I, CH_BEAM = F.kings_chamber(260_000, seed=3)
SARC = F.sarcophagus(30_000, seed=4)
GAL = F.gallery(260_000, seed=5)
CORR = F.gable_corridor(160_000, seed=6)
CHEV, CHEV_I = F.chevrons(220_000, seed=7)
MAP, MAP_I, MAP_R = F.egypt_map(160_000, seed=8)
CASING = F.pyramid_surface(260_000, seed=9, course_frac=0.0)
PYR, PYR_I = V2.PYR, V2.PYR_I
_cx = g.random(70_000)
CITY = np.stack([g.uniform(-2500, 9000, 70_000), -g.uniform(1500, 16000, 70_000) * (0.4 + 0.6 * _cx), g.normal(0, 1, 70_000)], 1)
CITY_A = (g.uniform(0.3, 1.0, 70_000) * np.exp(-np.abs(CITY[:, 1]) / 12000)).astype(np.float32)
SHAFT = F.tube(120_000, (0, 0, 0), (0, 60, 0), 0.2, 0.2, seed=10)
SLAB = F.box_surface(14_000, -0.1, 0.1, 0, 0.06, -0.1, 0.1, seed=11, edge=0.5)
ROBOT = np.concatenate([F.box_surface(6000, -0.07, 0.07, -0.19, 0.19, -0.05, 0.05, seed=12, edge=0.6),
                        F.polyline([(-0.06, -0.2, -0.085), (-0.06, 0.2, -0.085)], 800), F.polyline([(0.06, -0.2, -0.085), (0.06, 0.2, -0.085)], 800),
                        F.polyline([(-0.06, -0.2, 0.085), (-0.06, 0.2, 0.085)], 800), F.polyline([(0.06, -0.2, 0.085), (0.06, 0.2, 0.085)], 800)])


def cone(apex, direction, length, angle, n, seed=0):
    """Faisceau de lumière (phares, lampe) en particules faibles."""
    rr = np.random.default_rng(seed)
    d = np.asarray(direction, float); d /= np.linalg.norm(d)
    a = np.cross(d, [0, 0, 1.0]); a = a if np.linalg.norm(a) > 1e-3 else np.cross(d, [1.0, 0, 0]); a /= np.linalg.norm(a)
    b = np.cross(d, a)
    u = rr.random(n) ** 0.7 * length
    r = np.sqrt(rr.random(n)) * np.tan(angle) * u
    th = rr.random(n) * 2 * np.pi
    P = apex + np.outer(u, d) + np.outer(r * np.cos(th), a) + np.outer(r * np.sin(th), b)
    return P, (1 - u / length).astype(np.float32)


# ================================================================== scènes (t = temps de la voix ; tl = temps local)
def s_void_close(t, tl):            # 14,1 → 18,1 : personne ne l'a jamais ouvert
    c = (V2.F.VOID0 + V2.F.VOID1) / 2
    cm, ln = cam([(0, c + [70, -30, 6], c, 36), (4.0, c + [52, 18, 10], c, 34)], tl, ((0, 14.0),))
    fr = M.Frame(cm, ln)
    R = 6.5
    for base, D, DIR, alpha, col in ((V2.VOL, V2.DV, V2.DIRV, 0.45, M.BLUE), (V2.INT, V2.DI, V2.DIRI, 0.5, M.BLUE_HI)):
        nd = np.sqrt(D * D + R * R)
        Q = base + DIR * (nd - D)[:, None]
        w = np.exp(-((nd - R) / 2.2) ** 2)[:, None].astype(np.float32) * (0.85 + 0.15 * math.sin(tl * 5))
        fr.points(M.flow(Q, tl, 0.25, 0.2), col[None, :] * (1 - w) + M.RED[None, :] * w, alpha * (1 + 2.5 * w[:, 0]))
    fr.rays(c, 0.25, 0.3)
    V2.add_dust(fr, cm, tl, 0.3)
    return fin(fr, t)


def s_rewind(t, tl):                # 18,1 → 24,6 : tu crois qu'on connaît tout ? 4 500 ans
    cm, ln = cam([(0, (70, 470, 25), (0, 0, 75), 40), (6.5, (50, 380, 70), (0, 0, 78), 38)], tl, ((0, 3.0),),
                 fog=(900, 6000))
    fr = M.Frame(cm, ln)
    k = float(M.keyed(tl, [(0, 0.0), (2.4, 0.0), (5.0, 1.0)]))
    V2.base_scene(fr, t, 0.35, 0.18)
    fr.points(V2.STARS, M.WHITE, V2.STAR_A * 0.7 * k)
    fr.points(CITY, M.ORANGE * 0.9 + 0.1, CITY_A * 1.6 * (1 - k))
    fr.points(PYR, M.BLUE[None, :] * PYR_I[:, None], 0.42 * (1 - 0.6 * k) * V2.sparkle(t))
    zc = float(M.keyed(tl, [(0, -1), (2.4, -1), (5.4, 147)]))
    m = CASING[:, 2] < zc
    if m.any():
        fr.points(CASING[m], np.array([0.75, 0.82, 1.0], np.float32), 0.085)
    if tl > 5.0:
        top = CASING[CASING[:, 2] > 137.5]
        fr.points(top, M.GOLD, 3.0 * min(1.0, (tl - 5.0) / 0.6))
        fr.rays((0, 0, 145), 0.4 * min(1.0, (tl - 5.0) / 0.6), 0.3)
    return fin(fr, t)


def s_summit(t, tl):                # 32,9 → 37,7 : personne n'a jamais retrouvé comment… 100 m
    zt = 120.0
    s = F.HALF * (1 - zt / F.HEIGHT)
    edge = np.array([0, -s + 1.5, zt])
    cm, ln = cam([(0, edge + [7, -9, 3], edge + [0, 0, 1], 44), (1.4, edge + [8, -11, 4], edge + [0, 0, 1], 44),
                  (4.8, (230, -460, 210), (0, -40, 90), 40)], tl, ((0, 12.0), (1.6, 10.0), (4.8, 3.0)))
    fr = M.Frame(cm, ln)
    V2.base_scene(fr, t, 0.3, 0.12)
    m = PYR[:, 2] <= zt
    fr.points(PYR[m], M.BLUE[None, :] * PYR_I[m, None], 0.4, warm_near=40)
    fr.points(F.platform(40_000, zt, seed=1), M.BLUE, 0.12)
    blk = F.box_surface(5000, -0.7, 0.7, -0.6, 0.6, 0, 1.0, seed=2, edge=0.6) + edge + [0, -0.6, zt * 0 + min(0.6, tl * 0.15)]
    fr.points(blk, M.BLUE_HI, 0.5)
    for i, (dx, mo) in enumerate(((-1.2, "pousser_lourd"), (1.2, "pousser_appui"), (0, "soulever"))):
        person(fr, ("qt_male", "mh", "qt_female")[i], mo, tl, edge + [dx, 1.4, 0], math.pi * 1.5, f0=40 + 20 * i)
    flame(fr, edge + [-2.6, 1.0, 2.0], tl, 1.5, rays=True)
    V2.add_dust(fr, cm, tl, 0.25)
    return fin(fr, t)


def s_gallery(t, tl):               # 37,7 → 42,0 : la chambre du roi, en haut de la Grande Galerie
    d = (V2.F.GG1 - V2.F.GG0)
    up = np.array([0, 0, 1.0])
    p0, p1 = V2.F.GG0 + d * 0.35 + up * 1.8, V2.F.GG0 + d * 0.78 + up * 2.0
    look = V2.F.GG1 + up * 3.5 + d / np.linalg.norm(d) * 2
    cm, ln = cam([(0, p0, look, 70), (4.3, p1, look, 66)], tl, ((0, 6.0),))
    fr = M.Frame(cm, ln)
    fr.points(M.flow(GAL, tl, 0.02, 0.5), M.BLUE_HI, 0.5, warm_near=6)
    door = V2.F.GG1 + up * 1.0
    fr.points(F.polyline([door + [-0.5, 0, 0], door + [-0.5, 0, 1.1], door + [0.5, 0, 1.1], door + [0.5, 0, 0]], 3000), M.BLUE_HI, 1.5)
    flame(fr, V2.F.GG1 + up * 0.95 + [-0.8, -0.3, 0], tl, 1.0, rays=True)
    return fin(fr, t)


def s_ceiling(t, tl):               # 42,0 → 46,4 : poutres de granit jusqu'à 80 tonnes
    cm, ln = cam([(0, (-3.8, -1.9, 0.7), (-2.0, 0.2, 3.2), 74), (4.4, (-3.5, -1.8, 0.8), (2.4, 0.2, 5.8), 74)], tl, ((0, 4.0),))
    fr = M.Frame(cm, ln)
    gold = float(M.keyed(tl, [(0, 0.0), (2.0, 0.0), (2.8, 1.0)]))
    col = np.where((CH_BEAM == 4)[:, None], M.BLUE_HI * (1 - gold) + M.GOLD * gold, M.BLUE_HI)
    fr.points(CHAMBER, col, 0.32 * CH_I * np.where(CH_BEAM == 4, 1 + 2.5 * gold, 1.0), warm_near=5)
    flame(fr, (-4.6, 2.0, 0.25), tl, 1.6, rays=True)
    V2.add_dust(fr, cm, tl, 0.2)
    return fin(fr, t)


MAP_W = np.stack([(MAP[:, 0] - 31) * 10, (MAP[:, 1] - 27) * 10, MAP[:, 2]], 1)
_n = MAP_R == 1
NILE_PTS = MAP_W[_n]
NILE_LAT = MAP[_n, 1]


def s_map(t, tl):                   # 46,4 → 49,2 : venues d'une carrière à 800 km
    cm, ln = cam([(0, (4, -62, 48), (1, -2, 0), 40), (2.8, (2, -48, 40), (1, 3, 0), 40)], tl, ((0, 3.0),))
    fr = M.Frame(cm, ln)
    fr.points(MAP_W, M.BLUE[None, :] * MAP_I[:, None], 1.4)
    lat = float(M.keyed(tl, [(0, 24.05), (0.3, 24.05), (2.4, 30.0)]))
    m = (NILE_LAT > 24.05) & (NILE_LAT < lat) & (np.abs(NILE_PTS[:, 0] - 0.0) < 40)
    fr.points(NILE_PTS[m], M.GOLD, 2.5)
    for (lon, la, c) in ((32.9, 24.09, M.ORANGE), (31.13, 29.98, M.GOLD)):
        P = np.array([(lon - 31) * 10, (la - 27) * 10, 0.3]) + np.random.default_rng(1).normal(0, 0.25, (1500, 3))
        fr.points(P, c, 1.5 * (1 if c is M.ORANGE or tl > 2.2 else 0.15))
    head = NILE_PTS[m][np.argmax(NILE_LAT[m])] if m.any() else None
    if head is not None:
        fr.rays(head, 0.3, 0.2)
    return fin(fr, t)


def s_ramp(t, tl):                  # 49,2 → 53,6 : hissées à 40 m, sans poulie, sans roue
    sl = math.radians(16)
    d = np.array([0, math.cos(sl), math.sin(sl)])
    base = np.array([0, 0, 0.0])
    adv = 0.35 * tl
    beam_c = base + d * (adv + 0.0)
    rampP = F.along(F.box_surface(80_000, -6, 6, 0, 1, -0.4, 0.0, seed=3, edge=0.7), base - d * 30, base + d * 60)
    fr_keys = [(0, (6.5, 3.0, 2.6), (0, 9.5, 3.4), 50), (4.4, (6.0, 5.0, 3.2), (0, 11.5, 4.2), 50)]
    cm, ln = cam(fr_keys, tl, ((0, 10.0),))
    fr = M.Frame(cm, ln)
    fr.points(rampP, M.ORANGE * 0.5 + 0.05, 0.25)
    gr = F.box_surface(14_000, -0.8, 0.8, -4, 4, 0.3, 1.6, seed=4, edge=0.6)
    Rx = np.array([[1, 0, 0], [0, math.cos(sl), -math.sin(sl)], [0, math.sin(sl), math.cos(sl)]])
    fr.points(gr @ Rx.T + beam_c, np.array([1.0, 0.45, 0.35], np.float32), 0.6)
    wall = F.wall_blocks(90_000, -25, 25, 0, 30, 0, 1.2, 2.0, seed=5)[0]
    fr.points(np.stack([np.full(len(wall), -9.0), wall[:, 0] + 15, wall[:, 2]], 1), M.BLUE, 0.22)
    for k in range(8):
        side, dist = 0.8 * (k % 2 * 2 - 1), 6.0 + 1.6 * (k // 2)
        pos = beam_c + d * dist + [side, 0, 0]
        Q = person(fr, ("qt_male", "mh", "qt_male", "qt_female")[k % 4], ("trainer_lourd_1", "tirer_lourd", "trainer_lourd_2")[k % 3],
                   tl, pos, math.pi / 2, f0=120 + 9 * k, in_place=True, alpha=0.17)
        hand = (Q[CO.J["LeftHand"]] + Q[CO.J["RightHand"]]) / 2
        fr.points(F.polyline([beam_c + d * 4.2 + [side * 0.4, 0, 0.9], hand], 500, seed=k), M.GOLD, 0.5)
    for y in (2, 12, 22):
        flame(fr, base + d * y + [7, 0, 2.6], tl, 1.4, seed=y)
    V2.add_dust(fr, cm, tl, 0.3)
    return fin(fr, t)


SARC_POS = np.array([-5.235 + 1.6, 0.0, 0.0])


def s_sarc(t, tl):                  # 53,6 → 57,3 : un sarcophage
    cm, ln = cam([(0, (3.2, -2.0, 1.8), SARC_POS + [0, 0, 0.6], 50), (3.7, (0.2, -1.3, 1.6), SARC_POS + [0, 0, 0.5], 46)], tl, ((0, 8.0),))
    fr = M.Frame(cm, ln)
    fr.points(CHAMBER, M.BLUE_HI, 0.22 * CH_I, warm_near=4)
    fr.points(SARC + SARC_POS, M.BLUE_HI, 0.8, warm_near=4)
    flame(fr, (-1.2, 2.0, 0.2), tl, 1.4, rays=True)
    V2.add_dust(fr, cm, tl, 0.25)
    return fin(fr, t)


def s_toowide(t, tl):               # 57,3 → 61,4 : vide, sans couvercle, trop large pour les couloirs
    cx, y0 = 5.235 - 1.1, -2.615
    cor = F.tube(30_000, (cx, y0, 0.6), (cx, y0 - 10, 0.6), 1.05, 1.2, seed=1)
    cm, ln = cam([(0, (8.5, -9, 7), (0, -0.5, 0), 40), (4.1, (8, -8, 6), (2.5, -1.5, 0.3), 38)], tl, ((0, 3.0),))
    fr = M.Frame(cm, ln)
    fr.points(CHAMBER, M.BLUE, 0.12 * CH_I)
    fr.points(cor, M.BLUE_HI, 0.5)
    k1 = float(M.ease_io(tl / 1.4))
    k2 = float(M.ease_io((tl - 1.4) / 1.3))
    ang = math.pi / 2 * k1
    pos = SARC_POS * (1 - k1) + np.array([cx, 0.3, 0]) * k1 + np.array([0, (y0 + 1.0 - 0.3) * k2, 0])
    c, s = math.cos(ang), math.sin(ang)
    Q = SARC @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T + pos
    red = float(M.keyed(tl, [(0, 0), (2.6, 0), (3.0, 1)]))
    fr.points(Q, M.BLUE_HI * (1 - red) + M.RED * red, 0.8 * (1 + red))
    return fin(fr, t)


def s_walls(t, tl):                 # 61,4 → 65,7 : posé pendant la construction, puis tout bâti autour
    cm, ln = cam([(0, (11, -12, 9), (-1.5, 0, 1.5), 40), (4.3, (9, -10, 7), (-1.5, 0, 2.5), 40)], tl, ((0, 3.0),))
    fr = M.Frame(cm, ln)
    fr.points(V2.STARS, M.WHITE, V2.STAR_A * 0.6)
    fr.points(F.platform(40_000, 0.0, half=14, height=1e9), M.BLUE, 0.1)
    fr.points(SARC + SARC_POS, M.BLUE_HI, 0.8)
    zc = float(M.keyed(tl, [(0, -1), (0.8, -1), (3.2, 5.8)]))
    walls = (CH_BEAM == -1) | (CHAMBER[:, 2] < 5.8)
    m = walls & (CHAMBER[:, 2] < zc)
    fr.points(CHAMBER[m], M.BLUE_HI, 0.3 * CH_I[m])
    drop = float(M.keyed(tl, [(0, 30), (3.2, 30), (4.0, 0)]))
    b = CH_BEAM >= 0
    fr.points(CHAMBER[b] + [0, 0, drop], M.BLUE_HI, 0.3 * CH_I[b] * (1 if tl > 3.2 else 0))
    if tl < 1.5:
        for i, x in enumerate((-2.0, 0.5)):
            person(fr, ("qt_male", "mh")[i], "pousser_caisse", tl, (x, 1.6, 0), -math.pi / 2, f0=60, alpha=0.18 * (1 - tl / 1.5))
    flame(fr, (-3.0, 2.0, 0.1), tl, 1.4)
    return fin(fr, t)


LYING = None


def s_pharaoh(t, tl):               # 65,7 → 68,4 : le corps du pharaon ? jamais retrouvé
    global LYING
    if LYING is None:
        best = None                                        # la pose debout la plus droite et compacte
        for name in ("marche_neutre", "marche_militaire", "lampe_torche", "effraye"):
            mv = mov(name)
            for f in range(0, mv.n, 3):
                Pf = mv.P[f]
                spread = np.ptp(Pf[:, 0]) + np.ptp(Pf[:, 1])
                if best is None or spread < best[0]:
                    best = (spread, Pf - [Pf[0, 0], Pf[0, 1], 0])
        P = best[1]
        pts = BODY["qt_male"].points(P)
        pts = pts[:, [2, 0, 1]]                            # couché : la tête vers +x, le visage vers le haut
        pts = pts - (pts.min(0) + pts.max(0)) / 2
        LYING = pts * (2.0 / np.ptp(pts[:, 0]))
    cm, ln = cam([(0, SARC_POS + [0.4, -1.8, 3.0], SARC_POS + [0, 0, 0.5], 40), (2.7, SARC_POS + [0.3, -1.4, 2.5], SARC_POS + [0, 0, 0.5], 40)], tl, ((0, 6.0),))
    fr = M.Frame(cm, ln)
    fr.points(SARC + SARC_POS, M.BLUE_HI, 0.7)
    k = float(M.keyed(tl, [(0, 0.0), (0.7, 0.0), (2.6, 1.0)]))
    rr = np.random.default_rng(3)
    drift = rr.normal(0, 1, LYING.shape) * [0.3, 0.3, 0.2] + [0, 0, 1.5]
    pts = LYING + SARC_POS + [0, 0, 0.55] + drift * k ** 1.5
    fr.points(pts, M.GOLD, 0.7 * (1 - k) + 0.03)
    fr.rays(SARC_POS + [0, 0, 0.8], 0.3 * (1 - k), 0.25)
    return fin(fr, t)


def s_shafts(t, tl):                # 68,4 → 74,6 : deux conduits minuscules… 20 cm
    if tl < 3.4:
        cm, ln = cam([(0, (260, -60, 50), (0, 0, 35), 34), (3.4, (120, -20, 32), (0, 0, 30), 30)], tl, ((0, 4.0),))
        fr = M.Frame(cm, ln)
        fr.points(V2.INT, M.BLUE, 0.25)
        fr.points(V2.PYR, M.BLUE[None, :] * V2.PYR_I[:, None], 0.06)
        k = float(M.keyed(tl, [(0, 0.0), (0.6, 0.0), (2.4, 1.0)]))
        for sgn in (-1, 1):
            a = np.array([0, sgn * 2.9, 22.6])
            b = a + np.array([0, sgn * 46.0, 38.6]) * k
            fr.points(F.polyline([a, b], 6000, 0.1, seed=sgn + 2), M.GOLD, 1.6)
        fr.points(F.box_surface(8000, -2.6, 2.6, -2.9, 2.9, 21.7, 26, seed=5), M.BLUE_HI, 0.8)
        return fin(fr, t)
    u = tl - 3.4
    wall, wi = F.wall_blocks(70_000, -3, 3, 0, 4.5, 0.0, 0.9, 1.4, seed=6)
    hole = np.array([0, 0, 1.5])
    keep = ~((np.abs(wall[:, 0]) < 0.1) & (np.abs(wall[:, 2] - 1.6) < 0.1))
    cm, ln = cam([(0, (2.2, -3.2, 1.6), (-0.15, -0.3, 1.3), 46), (3.2, (1.5, -2.4, 1.6), (-0.1, -0.2, 1.4), 46)], u, ((0, 6.0),))
    fr = M.Frame(cm, ln)
    fr.points(wall[keep], M.BLUE_HI, 0.3 * wi[keep], warm_near=3)
    sq = F.polyline([(-0.1, -0.01, 1.5), (0.1, -0.01, 1.5), (0.1, -0.01, 1.7), (-0.1, -0.01, 1.7), (-0.1, -0.01, 1.5)], 2000)
    fr.points(sq, M.GOLD, 2.0)
    person(fr, "mh", "epier", u, (-0.15, -0.75, 0), 0.0, f0=10, alpha=0.22, warm=3)
    flame(fr, (1.4, -1.2, 0.3), u, 1.0, rays=True)
    return fin(fr, t)


def s_robot(t, tl):                 # 74,6 → 79,0 : en 1993, un robot s'y glisse
    y = 2.0 + 1.3 * tl
    cm, ln = cam([(0, (0.03, y - 0.65, 0.06), (0, y + 0.1, 0), 60)], tl, ((0, 2.5),))
    fr = M.Frame(cm, ln)
    fr.points(SHAFT, M.BLUE_HI, 0.35, warm_near=1.5)
    fr.points(ROBOT + [0, y, 0], M.WHITE, 0.6, warm_near=1)
    P, A = cone((0, y + 0.2, 0), (0, 1, 0), 4.0, 0.35, 6000, seed=int(tl * 30))
    fr.points(P, M.WHITE, A * 0.08)
    for x in (-0.035, 0.035):
        fr.points(np.array([[x, y + 0.2, 0]]) + np.random.default_rng(1).normal(0, 0.004, (200, 3)), M.WHITE, 2.0)
    fr.points(F.polyline([(0, y - 0.2, -0.07), (0, 0, -0.07)], 3000), M.BLUE, 0.5)
    return fin(fr, t)


def s_door(t, tl, drill=False):     # 79,0 → 83,2 : une petite porte de pierre, deux poignées de cuivre
    y = float(M.keyed(tl, [(0, 58.6), (4.2, 59.7)])) if not drill else float(M.keyed(tl, [(0, 59.62), (1.4, 59.72), (5.0, 60.03)]))
    cm, ln = cam([(0, (0, y, 0), (0, 61, 0), 62)], tl, ((0, 3.0),))
    fr = M.Frame(cm, ln)
    fr.points(SHAFT, M.BLUE_HI, 0.3, warm_near=1)
    slab = SLAB + [0, 60.0, 0]
    if drill and tl > 1.3:
        slab = slab[np.hypot(slab[:, 0], slab[:, 2]) > 0.014]
        ring = np.array([[0.012 * math.cos(a), 59.999, 0.012 * math.sin(a)] for a in np.linspace(0, 2 * math.pi, 400)])
        fr.points(ring, M.WHITE, 1.2)
        s2 = F.box_surface(14_000, -0.1, 0.1, 60.26, 60.32, -0.1, 0.1, seed=3, edge=0.4)
        fr.points(s2, np.array([1.0, 0.4, 0.35], np.float32), 0.6 * min(1, (tl - 1.3) / 1.5))
    fr.points(slab, M.BLUE_HI, 0.7, warm_near=1)
    for x in (-0.05, 0.05):
        pin = F.polyline([(x, 60.0, 0.035), (x, 59.988, 0.035), (x, 59.988, 0.02)], 300)
        fr.points(pin, M.ORANGE, 2.5)
    if drill and tl < 1.6:
        fr.points(F.polyline([(0, 59.5, 0), (0, 60.0 + 0.002 * tl, 0)], 1500), M.WHITE, 0.8)
    P, A = cone((0, y + 0.02, -0.02), (0, 1, 0), 1.5, 0.5, 5000, seed=int(tl * 30))
    fr.points(P, M.WHITE, A * 0.06)
    return fin(fr, t)


FACE_ROT = math.radians(90 - 51.84)


def face_to_world(P):
    c, s = math.cos(FACE_ROT), math.sin(FACE_ROT)
    return np.stack([P[:, 0], P[:, 1] * c - P[:, 2] * s, P[:, 1] * s + P[:, 2] * c], 1)


CHEV_W = face_to_world(CHEV)


def s_north(t, tl):                 # 88,2 → 94,0 : en 2023, une caméra dans une fissure de la face nord
    jt = face_to_world(np.array([[0.0, -0.3, 8.6]]))[0]
    plat = face_to_world(np.array([[0.0, -1.5, -0.9]]))[0]
    mid = (plat + jt) / 2 + [0, 0, -0.5]
    cm, ln = cam([(0, plat + [5, -9, 0.5], mid, 44), (2.6, plat + [3.8, -7, 1.5], mid, 42),
                  (5.8, jt + [1.4, -3.2, -0.6], jt, 40)], tl, ((0, 4.0), (5.8, 8.0)))
    fr = M.Frame(cm, ln)
    fr.points(V2.STARS, M.WHITE, V2.STAR_A * 0.5)
    fr.points(CHEV_W, M.BLUE_HI, 0.35 * CHEV_I, warm_near=6)
    Q1 = person(fr, "qt_male", "lampe_torche", tl, plat + [-0.8, 0, 0], math.pi / 2, f0=20)
    person(fr, "qt_female", "epier", tl, plat + [0.9, 0, 0], math.pi / 2, f0=5)
    hand = Q1[CO.J["RightHand"]]
    k = float(M.keyed(tl, [(0, 0.0), (2.6, 0.0), (5.4, 1.0)]))
    tip = hand * (1 - k) + jt * k
    fr.points(F.polyline([hand, (hand + tip) / 2 + [0, 0, -0.5], tip], 2500, seed=2), M.BLUE, 0.6)
    fr.points(tip + np.random.default_rng(0).normal(0, 0.01, (300, 3)), M.WHITE, 3.0)
    fr.rays(tip, 0.3, 0.2)
    return fin(fr, t)


def s_corridor(t, tl, end=False):   # 94,0 → 99,9 couloir caché ; 99,9 → 103,1 il ne mène nulle part
    if not end:
        y = float(M.keyed(tl, [(0, 0.3), (5.9, 5.5)]))
        cm, ln = cam([(0, (0.05, y, 1.0), (0, y + 6, 1.1), 74)], tl, ((0, 4.0),))
    else:
        y = float(M.keyed(tl, [(0, 5.5), (3.2, 7.5)]))
        cm, ln = cam([(0, (0.05, y, 1.0), (0.25, 9, 0.5), 66), (3.2, (0.15, y, 0.6), (0.35, 9, 0.05), 60)], tl, ((0, 5.0),))
    fr = M.Frame(cm, ln)
    near = np.linalg.norm(CORR - cm["pos"], axis=1)
    fr.points(CORR, M.BLUE_HI, 0.35 * (0.4 + 1.6 * np.exp(-near / 2.5)), warm_near=3)
    endw, ei = F.wall_blocks(20_000, -1.05, 1.05, 0, 2.6, 9.0, 0.65, 0.9, seed=4)
    endw = endw[~((endw[:, 0] > 0.15) & (endw[:, 0] < 0.55) & (endw[:, 2] < 0.04))]
    fr.points(endw, M.BLUE_HI, 0.35 * (0.4 + 1.6 * np.exp(-np.linalg.norm(endw - cm["pos"], axis=1) / 2.5)))
    rr = np.random.default_rng(5)
    dust = rr.uniform([-0.9, 1, 0.1], [0.9, 8.8, 2.2], (300, 3))
    if end:
        k = float(M.ease_io(tl / 3.2))
        dust = dust * (1 - k * 0.8) + np.array([0.35, 9.0, 0.02]) * k * 0.8
        fr.points(F.polyline([(0.15, 9.02, 0.01), (0.55, 9.02, 0.01)], 800), M.RED, 2.0 * k)
    fr.points(M.flow(dust, tl, 0.05, 2.0), M.WHITE, 0.6)
    return fin(fr, t)


def s_orbit(t, tl):                 # 103,1 → 108,7 : le grand vide, juste au-dessus de la galerie
    c = np.array([0, -12.0, 42.0])
    a = math.radians(-20 + 9 * tl)
    pos = c + np.array([170 * math.cos(a), 170 * math.sin(a), 30])
    cm, ln = cam([(0, pos, c, 34)], 0, ((0, 4.0),))
    fr = M.Frame(cm, ln)
    fr.points(V2.PYR, M.BLUE[None, :] * V2.PYR_I[:, None], 0.08)
    fr.points(V2.INT, M.BLUE, 0.3)
    k = float(M.keyed(tl, [(0, 0.0), (0.4, 0.0), (2.4, 1.0)]))
    gm = (V2.INT[:, 2] > 20) & (V2.INT[:, 2] < 52) & (V2.INT[:, 1] < 6) & (V2.INT[:, 1] > -38)
    fr.points(V2.INT[gm], M.BLUE_HI, 0.9 * k)
    R = 6.5
    nd = np.sqrt(V2.DV ** 2 + R * R)
    Q = V2.VOL + V2.DIRV * (nd - V2.DV)[:, None]
    w = np.exp(-((nd - R) / 2.2) ** 2).astype(np.float32)
    fr.points(Q[w > 0.2], M.RED, 0.5 * w[w > 0.2] * (1 + float(M.keyed(tl, [(0, 0), (2.4, 0), (4.0, 1.5)]))))
    fr.rays((V2.F.VOID0 + V2.F.VOID1) / 2, 0.2, 0.3)
    return fin(fr, t)


HOLO = None


def s_holo(t, tl):                  # 108,7 → 114,7 : ils connaissent sa taille… personne n'y est entré
    global HOLO
    sc = 0.0062
    ctr = np.array([0, 0, 0.95])
    if HOLO is None:
        HOLO = (V2.PYR[::3] * sc, V2.INT * sc)
    a = math.radians(-35 + 8 * tl)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    cm, ln = cam([(0, (0.5, -4.0, 1.9), ctr + [0, 0, 0.25], 50), (6.0, (-0.5, -3.3, 1.7), ctr + [0, 0, 0.25], 50)], tl, ((0, 5.0),))
    fr = M.Frame(cm, ln)
    fr.points(HOLO[0] @ Rz.T + ctr, M.BLUE, 0.35)
    fr.points(HOLO[1] @ Rz.T + ctr, M.BLUE_HI, 0.25)
    vc = ((V2.F.VOID0 + V2.F.VOID1) / 2 * sc) @ Rz.T + ctr
    vv = F.polyline([V2.F.VOID0 * sc, V2.F.VOID1 * sc], 3000, 0.02) @ Rz.T + ctr
    fr.points(vv, M.RED, 1.6)
    ring = np.array([[0.95 * math.cos(b), 0.95 * math.sin(b), 0.9] for b in np.linspace(0, 2 * math.pi, 3000)])
    fr.points(ring, M.BLUE_HI, 0.8)
    for i, (mo, ang) in enumerate((("penseur", 200), ("montrer_du_doigt", 320), ("taper_clavier", 80))):
        b = math.radians(ang)
        person(fr, ("qt_male", "qt_female", "mh")[i], mo, tl, (1.35 * math.cos(b), 1.35 * math.sin(b), 0), b + math.pi / 2 + math.pi / 2,
               f0=30 * i, alpha=0.16, warm=5)
    for i, ts in enumerate((1.5, 2.9, 3.8)):      # caméra, robot, humain : trois sondes s'arrêtent net au bord du vide
        if tl > ts - 1.0:
            k = min(1.0, (tl - ts + 1.0) / 1.0)
            start = vc + np.array([math.cos(i * 2.1), math.sin(i * 2.1), 0.4]) * 0.7
            p = start * (1 - k) + (vc + (start - vc) * 0.1) * k
            col = M.WHITE if tl < ts else M.RED
            fr.points(p + np.random.default_rng(i).normal(0, 0.008, (300, 3)), col, 2.5 * (1 if tl < ts + 0.5 else max(0, 1 - (tl - ts - 0.5))))
    fr.rays(vc, 0.25, 0.25)
    return fin(fr, t)


def s_seal(t, tl):                  # 114,7 → 117,6 : une chambre, fermée depuis l'époque des pharaons
    wall, wi = F.wall_blocks(110_000, -4, 4, 0, 4, 0.0, 1.0, 1.4, seed=9)
    hole = (np.abs(wall[:, 0]) < 0.7) & (wall[:, 2] > 1.0) & (wall[:, 2] < 2.0)
    cm, ln = cam([(0, (2.2, -4.6, 1.8), (0, 0, 1.5), 46), (2.9, (1.4, -3.4, 1.6), (0, 0, 1.5), 46)], tl, ((0, 6.0),))
    fr = M.Frame(cm, ln)
    fr.points(wall[~hole], M.BLUE_HI, 0.3 * wi[~hole], warm_near=4)
    k = float(M.keyed(tl, [(0, 0.0), (1.8, 1.0)]))
    blk = F.box_surface(9000, -0.7, 0.7, 0, 1.0, 1.0, 2.0, seed=1, edge=0.6) + [0, -0.95 * (1 - k), 0]
    fr.points(blk, M.BLUE_HI, 0.6)
    if tl < 2.0:
        for i, x in enumerate((-0.45, 0.45)):
            person(fr, ("qt_male", "mh")[i], "pousser_caisse", tl, (x, -1.6 + 0.9 * k, 0), math.pi / 2, f0=80, alpha=0.18 * (1 - max(0, tl - 1.6) / 0.4), warm=4)
    out = float(M.keyed(tl, [(0, 1.0), (1.9, 1.0), (2.6, 0.0)]))
    if out > 0:
        rr = np.random.default_rng(int(tl * 30))
        fl = np.array([-1.8, -1.2, 1.2]) + rr.normal(0, 1, (int(1200 * out) + 1, 3)) * [0.08, 0.08, 0.2 * out]
        fr.points(fl, M.ORANGE, 0.6 * out)
    return fin(fr, t, exposure=2.6 * (0.35 + 0.65 * out))


def s_pullback(t, tl):              # 117,6 → 120,8 : au cœur du monument le plus étudié de la planète
    cm, ln = cam([(0, (160, -330, 120), (0, 0, 60), 40), (3.2, (900, -4200, 2600), (0, -2500, 0), 50)], tl, ((0, 3.0),),
                 fog=(3000, 30000))
    fr = M.Frame(cm, ln)
    V2.base_scene(fr, t, 0.3, 0.15)
    fr.points(V2.PYR, M.BLUE[None, :] * V2.PYR_I[:, None], 0.4)
    fr.points(CITY, M.ORANGE * 0.9 + 0.1, CITY_A * 2.0)
    vc = (V2.F.VOID0 + V2.F.VOID1) / 2
    fr.points(vc + np.random.default_rng(0).normal(0, 2.0, (800, 3)), M.RED, 1.5)
    return fin(fr, t)


def s_final(t, tl):                 # 120,8 → 125,2 : qu'est-ce qu'ils ont voulu cacher…
    vc = (V2.F.VOID0 + V2.F.VOID1) / 2
    cm, ln = cam([(0, (260, -300, 90), vc, 36), (2.2, (60, -60, 50), vc, 36), (4.0, vc + [9, -3, 1], vc, 40)], tl, ((0, 4.0), (4.0, 22.0)))
    fr = M.Frame(cm, ln)
    fade = float(M.keyed(tl, [(0, 1.0), (3.4, 1.0), (4.4, 0.0)]))
    fr.points(V2.PYR, M.BLUE[None, :] * V2.PYR_I[:, None], 0.25 * fade)
    R = 6.5
    nd = np.sqrt(V2.DV ** 2 + R * R)
    Q = V2.VOL + V2.DIRV * (nd - V2.DV)[:, None]
    w = np.exp(-((nd - R) / 2.2) ** 2).astype(np.float32)
    col = M.BLUE[None, :] * (1 - w[:, None]) + M.RED[None, :] * w[:, None]
    pulse = 1 + 0.6 * max(0, math.sin(tl * 3.0))
    fr.points(Q, col, 0.3 * (1 + 4.0 * w * pulse) * np.where(w > 0.3, max(fade, 0.6 * (1 - max(0, tl - 4.0) * 4)), fade))
    fr.rays(vc, 0.5 * max(fade, 0.5), 0.35)
    return fin(fr, t)


SCENES = [(0.0, 14.1, lambda t, tl: V2.frame_A(t)), (14.1, 18.1, s_void_close), (18.1, 24.6, s_rewind),
          (24.6, 32.9, lambda t, tl: V2.frame_B(tl)), (32.9, 37.7, s_summit), (37.7, 42.0, s_gallery),
          (42.0, 46.4, s_ceiling), (46.4, 49.2, s_map), (49.2, 53.6, s_ramp), (53.6, 57.3, s_sarc),
          (57.3, 61.4, s_toowide), (61.4, 65.7, s_walls), (65.7, 68.4, s_pharaoh), (68.4, 74.6, s_shafts),
          (74.6, 79.0, s_robot), (79.0, 83.2, s_door), (83.2, 88.2, lambda t, tl: s_door(t, tl, drill=True)),
          (88.2, 94.0, s_north), (94.0, 99.9, s_corridor), (99.9, 103.1, lambda t, tl: s_corridor(t, tl, end=True)),
          (103.1, 108.7, s_orbit), (108.7, 114.7, s_holo), (114.7, 117.6, s_seal), (117.6, 120.8, s_pullback),
          (120.8, END, s_final)]
XF = 0.2                                     # fondu enchaîné entre deux scènes (s)


def frame(t):
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b or i == len(SCENES) - 1:
            img = fn(t, t - a)
            if i > 0 and t - a < XF:
                pa, pb, pfn = SCENES[i - 1]
                prev = pfn(t, t - pa)
                k = (t - a) / XF
                img = (img.astype(np.float32) * k + prev.astype(np.float32) * (1 - k)).astype(np.uint8)
            return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep12_constellation.mp4"
    if "--still" in sys.argv:
        import cv2
        ts = [float(x) for x in sys.argv[sys.argv.index("--still") + 1].split(",")]
        cv2.imwrite(out, cv2.cvtColor(np.hstack([frame(t)[::2, ::2] for t in ts]), cv2.COLOR_RGB2BGR))
        return
    t0 = float(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 0.0
    t1 = float(sys.argv[sys.argv.index("--to") + 1]) if "--to" in sys.argv else END
    subs = MI.groups([(txt, a - t0, b - t0) for txt, a, b in SEG if t0 <= a < t1])
    tmp = tempfile.mkdtemp()
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{M.W}x{M.H}",
                            "-r", str(M.FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", f"{tmp}/v.mp4"],
                           stdin=subprocess.PIPE)
    n = int(round((t1 - t0) * M.FPS))
    for i in range(n):
        t = t0 + i / M.FPS
        rgb = frame(t)
        arr = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
        MI.draw_sub(skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType).getCanvas(), t - t0, subs)
        enc.stdin.write(arr.tobytes())
        if i % 150 == 0:
            print(f"{t:.1f} s", flush=True)
    enc.stdin.close()
    enc.wait()
    voice = MI.load_voice(os.path.join(HERE, "audio", "voix.mp3"))[int(t0 * MI.SR): int(t1 * MI.SR)]
    MI.soundtrack(f"{tmp}/a.wav", voice, t1 - t0)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "libx264",
                    "-crf", "23", "-preset", "slow", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    main()
