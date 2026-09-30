"""« L'Orbe rentre à la maison » : un seul plan continu, de l'univers observable jusqu'à la France (≈ 61 s, sans voix).

L'échelle est pilotée par L(t) = log10(distance de la caméra à sa cible, en mètres). Chaque étage (toile cosmique,
Voie lactée, voisinage solaire, système solaire, Terre) est décrit dans ses propres unités et n'est visible que sur
sa plage de L ; les passages se font quand l'étage suivant n'est encore qu'un point au centre de l'image.

    python -m films.episodes.univers.retour sortie.mp4          # rendu parallèle (4 processus)
"""
import math
import os
import subprocess
import sys
import tempfile
import wave
from multiprocessing import Pool

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep01_triangle.ep01 import P, ease, text_c
from films.persos.orbe import Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
F = 1150.0
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "tex")

# ------------------------------------------------------------------------------------------------ l'échelle
KEYS = [(0, 26.3), (2.5, 25.0), (6, 24.2), (9, 23.3), (12.5, 22.3), (15, 21.4), (18, 20.9), (20.5, 20.2),
        (22.5, 19.2), (26, 17.2), (29, 16.3), (32, 15.2), (35, 13.4), (38, 12.2), (41, 11.1), (44, 9.9), (47, 9.0),
        (51, 7.8), (55, 6.7), (58, 6.45), (61.5, 6.4)]
DUR = 61.5


def L_at(t):
    for (t0, l0), (t1, l1) in zip(KEYS, KEYS[1:]):
        if t <= t1:
            u = max(0.0, (t - t0) / (t1 - t0))
            v = 0.5 * u + 0.5 * (u * u * (3 - 2 * u))
            return l0 + (l1 - l0) * v
    return KEYS[-1][1]


_TT = np.arange(0, DUR + 1, 1 / FPS)
_SPEED = np.array([-(L_at(t + 0.02) - L_at(t - 0.02)) / 0.04 for t in _TT])
_SCROLL = np.cumsum(_SPEED) / FPS


def speed_at(t):
    return float(np.interp(t, _TT, _SPEED))


def scroll_at(t):
    return float(np.interp(t, _TT, _SCROLL))


def band(L, hi_in, hi_full, lo_full, lo_out):
    """Visibilité d'un étage : 0 au-dessus de hi_in, 1 entre hi_full et lo_full, 0 sous lo_out (L décroît)."""
    a = ease((hi_in - L) / (hi_in - hi_full)) if L > hi_full else 1.0
    b = ease((L - lo_out) / (lo_full - lo_out)) if L < lo_full else 1.0
    return a * b


def roll_at(t):
    return 0.10 * math.sin(t * 0.21) + 0.004 * t


# ------------------------------------------------------------------------------------------------ outils de rendu
def splat(buf, x, y, val):
    ix, iy = x.astype(np.int32), y.astype(np.int32)
    m = (ix >= 0) & (ix < buf.shape[1]) & (iy >= 0) & (iy < buf.shape[0])
    for ch in range(val.shape[1]):
        np.add.at(buf[:, :, ch], (iy[m], ix[m]), val[m, ch])


def to_screen(x, y, z, t):
    r = roll_at(t)
    cr, sr = math.cos(r), math.sin(r)
    X, Y = x * cr - y * sr, x * sr + y * cr
    return W / 2 + F * X / z, H / 2 - F * Y / z


def render_points(img, diff, pts, lum, col, D, k, t, a_sharp, a_diff, cap=2.5):
    """Points 3D (cible à l'origine, caméra en (0, 0, -D)) ; luminosité ∝ 1/z² (brillance de surface constante)."""
    if a_sharp <= 0.003 and a_diff <= 0.003:
        return
    z = pts[:, 2] + D
    m = z > 1e-9
    z = z[m]
    sx, sy = to_screen(pts[m, 0], pts[m, 1], z, t)
    b = lum[m] * k / z ** 2
    val = col[m] * b[:, None]
    if a_sharp > 0.003:
        splat(img, sx, sy, np.minimum(val, cap) * 0.35 * a_sharp)
    if a_diff > 0.003:
        far = (b < 25)[:, None]
        splat(diff, sx / 8, sy / 8, val * far / 64 * 0.65 * a_diff)


def basis_from(fwd, up_hint):
    fwd = fwd / np.linalg.norm(fwd)
    right = np.cross(up_hint, fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    return np.stack([right, up, fwd])


# ------------------------------------------------------------------------------------------------ A. toile cosmique
UA = 1e24
K_WEB, K_MW = 900.0, 0.45
rng = np.random.default_rng(21)


def make_web():
    nodes = np.concatenate([[[0, 0, 0]], rng.normal(0, 1, (70, 3))])
    nodes[1:] *= (40 * rng.random((70, 1)) ** (1 / 3)) / np.linalg.norm(nodes[1:], axis=1, keepdims=True)
    pts = []
    for i, a in enumerate(nodes):
        d = np.linalg.norm(nodes - a, axis=1)
        for j in np.argsort(d)[1:4]:
            b = nodes[j]
            n = int(d[j] * 90)
            u = rng.random(n)[:, None]
            pts.append(a + (b - a) * u + rng.normal(0, 0.35, (n, 3)))
        pts.append(a + rng.normal(0, 0.55, (900, 3)))
    p = np.concatenate(pts)
    p = p[np.linalg.norm(p, axis=1) > 0.06]
    if len(p) > 170000:
        p = p[rng.choice(len(p), 170000, replace=False)]
    col = np.where(rng.random((len(p), 1)) < 0.5, [1.0, 0.86, 0.68], [0.78, 0.84, 1.0])
    return p, rng.lognormal(0, 0.8, len(p)), col


WEB, WEB_LUM, WEB_COL = make_web()


# ------------------------------------------------------------------------------------------------ B. la Voie lactée
UB = 5e20


def make_galaxy(n_disk, n_bulge, n_dust, seed):
    g = np.random.default_rng(seed)
    r = g.gamma(2.0, 0.17, n_disk)
    arm = g.integers(0, 2, n_disk)
    th = arm * math.pi + np.log(r + 0.05) / math.tan(math.radians(14)) + g.normal(0, 0.32, n_disk)
    x, z = r * np.cos(th), r * np.sin(th)
    y = g.normal(0, 0.012 + 0.01 * np.exp(-r / 0.2), n_disk)
    warm = np.clip(1 - r / 0.9, 0, 1)[:, None]
    col = warm * np.array([1.0, 0.82, 0.6]) + (1 - warm) * np.array([0.72, 0.8, 1.0])
    pink = g.random(n_disk) < 0.012
    col[pink] = [1.0, 0.45, 0.7]
    lum = g.lognormal(0, 0.7, n_disk) * (1 + 4 * pink)
    b = g.normal(0, 1, (n_bulge, 3)) * np.array([0.11, 0.07, 0.11])
    pts = np.concatenate([np.stack([x, y, z], 1), b])
    cols = np.concatenate([col, np.tile([1.0, 0.8, 0.55], (n_bulge, 1))])
    lums = np.concatenate([lum, g.lognormal(0, 0.5, n_bulge) * 1.4])
    rd = g.gamma(2.2, 0.17, n_dust)
    armd = g.integers(0, 2, n_dust)
    thd = armd * math.pi + np.log(rd + 0.05) / math.tan(math.radians(14)) - 0.35 + g.normal(0, 0.22, n_dust)
    dust = np.stack([rd * np.cos(thd), g.normal(0, 0.008, n_dust), rd * np.sin(thd)], 1)
    return pts, cols, lums, dust


MW, MW_COL, MW_LUM, MW_DUST = make_galaxy(110000, 24000, 28000, 7)
_ths = math.log(0.55) / math.tan(math.radians(14)) + 0.55                  # le Soleil, entre deux bras
SUN_G = np.array([0.5 * math.cos(_ths), 0.0, 0.5 * math.sin(_ths)])
_out = SUN_G / np.linalg.norm(SUN_G)
_c, _s = math.cos(math.radians(-70)), math.sin(math.radians(-70))
_hor = np.array([_out[0] * _c - _out[2] * _s, 0, _out[0] * _s + _out[2] * _c])
_U = np.array([_hor[0] * math.cos(0.5), math.sin(0.5), _hor[2] * math.cos(0.5)])   # 29° au-dessus du disque
RB = basis_from(-_U, np.array([0.0, 1.0, 0.0]))
MW_V = (MW - SUN_G) @ RB.T
MW_DUST_V = (MW_DUST - SUN_G) @ RB.T
MW_CENTER_V = (-SUN_G) @ RB.T
AND, AND_COL, AND_LUM, _ = make_galaxy(50000, 12000, 10, 3)
_ta = 1.1
_RA = np.array([[1, 0, 0], [0, math.cos(_ta), -math.sin(_ta)], [0, math.sin(_ta), math.cos(_ta)]])
AND_V = np.concatenate([(AND * 1.3) @ _RA.T + np.array([-12.0, 9.0, 25.0]),          # Andromède
                        (AND[::3] * 0.45) @ _RA.T[::-1] + np.array([9.0, -7.0, 18.0])])  # galaxie du Triangle
AND_LUM = np.concatenate([AND_LUM, AND_LUM[::3]]) * 5.0                            # plus loin : on les éclaire
AND_COL = np.concatenate([AND_COL, AND_COL[::3]])

# ------------------------------------------------------------------------------------------------ C. le voisinage
UC = 9.461e15


def make_neigh(n=32000):
    p = rng.normal(0, 1, (n, 3))
    p *= (300 * rng.random((n, 1)) ** (1 / 3)) / np.linalg.norm(p, axis=1, keepdims=True)
    p = p[np.linalg.norm(p, axis=1) > 2.5]
    kinds = np.array([[1.0, 0.68, 0.5], [1.0, 0.84, 0.64], [1.0, 0.95, 0.86], [0.8, 0.88, 1.0]])
    col = kinds[rng.choice(4, len(p), p=[0.55, 0.2, 0.15, 0.1])]
    return p, rng.lognormal(-0.3, 1.0, len(p)), col


NB, NB_LUM, NB_COL = make_neigh()
ALPHA_CEN = np.array([2.0, 1.0, -3.7])
NAMED = [(ALPHA_CEN, 3.0, np.array([1.0, 0.93, 0.8])), (np.array([-5.0, 3.0, -6.1]), 6.0, np.array([0.85, 0.9, 1.0]))]
NB = np.concatenate([NB, [n[0] for n in NAMED]])
NB_LUM = np.concatenate([NB_LUM, [n[1] for n in NAMED]])
NB_COL = np.concatenate([NB_COL, [n[2] for n in NAMED]])

# ------------------------------------------------------------------------------------------------ D. le système solaire
UD = 1.496e11
PLANETS = [("Mercure", 0.39, 1.3, (190, 180, 170)), ("Vénus", 0.72, 3.2, (240, 210, 160)),
           ("Terre", 1.0, 3.4, (90, 160, 255)), ("Mars", 1.52, 1.8, (230, 120, 80)),
           ("Jupiter", 5.2, 38, (225, 190, 150)), ("Saturne", 9.5, 32, (230, 210, 160)),
           ("Uranus", 19.2, 14, (160, 225, 235)), ("Neptune", 30.1, 14, (110, 150, 255))]
_pa = {"Mercure": 2.2, "Vénus": 4.0, "Terre": 0.0, "Mars": 1.1, "Jupiter": 2.6, "Saturne": 5.0, "Uranus": 3.5,
       "Neptune": 0.9}
_a = np.array([-0.5, 0.0, 1.0]) / math.hypot(0.5, 1.0)
_UD = np.array([_a[0] * math.cos(math.radians(30)), math.sin(math.radians(30)), _a[2] * math.cos(math.radians(30))])
RD = basis_from(-_UD, np.array([0.0, 1.0, 0.0]))
EARTH_D = np.array([1.0, 0.0, 0.0])
SUN_DIR_VIEW = (np.array([-1.0, 0.0, 0.0]) @ RD.T)
SUN_DIR_VIEW /= np.linalg.norm(SUN_DIR_VIEW)


def to_view_D(p):
    return (p - EARTH_D) @ RD.T


_th = rng.uniform(0, 2 * math.pi, 5000)
_r = rng.uniform(2.2, 3.3, 5000)
BELT = to_view_D(np.stack([_r * np.cos(_th), rng.normal(0, 0.05, 5000), _r * np.sin(_th)], 1))
_th = rng.uniform(0, 2 * math.pi, 7000)
_r = rng.uniform(30, 50, 7000)
KUIPER = to_view_D(np.stack([_r * np.cos(_th), rng.normal(0, 1.5, 7000), _r * np.sin(_th)], 1))
ORBITS = []
for name, a_, _, _ in PLANETS:
    u = np.linspace(0, 2 * math.pi, 361)
    ORBITS.append(to_view_D(np.stack([a_ * np.cos(u), 0 * u, a_ * np.sin(u)], 1)))
PLANET_V = {n: to_view_D(np.array([a_ * math.cos(_pa[n]), 0, a_ * math.sin(_pa[n])])) for n, a_, _, _ in PLANETS}
SUN_V = to_view_D(np.zeros(3))

# ------------------------------------------------------------------------------------------------ E. la Terre
RE = 6.371e6
FR_LAT, FR_LON = 46.6, 2.4
MOON_V = np.array([-38.0, 26.0, 40.0])


def _load(name, channel=None):
    im = skia.Image.open(os.path.join(TEX, name))
    a = im.convert(colorType=skia.ColorType.kRGBA_8888_ColorType).toarray()
    a = a.astype(np.float32) / 255
    return a[:, :, channel] if channel is not None else a[:, :, :3]


_TEXC = {}


def textures():
    if not _TEXC:
        _TEXC["day"] = _load("2_no_clouds_4k.jpg")
        _TEXC["cloud"] = _load("fair_clouds_4k.png", channel=3)       # nuages : couche alpha
        _TEXC["water"] = _load("water_4k.png", channel=0)
    return _TEXC


def sample(tex, lat, lon):
    """Échantillonnage bilinéaire d'une carte équirectangulaire (degrés)."""
    h, w = tex.shape[:2]
    u = (lon + 180.0) / 360.0 * w - 0.5
    v = (90.0 - lat) / 180.0 * h - 0.5
    x0 = np.floor(u).astype(np.int32)
    y0 = np.clip(np.floor(v).astype(np.int32), 0, h - 2)
    fx, fy = (u - x0), np.clip(v - y0, 0, 1)
    x0 %= w
    x1 = (x0 + 1) % w
    if tex.ndim == 3:
        fx, fy = fx[:, None], fy[:, None]
    a = tex[y0, x0] * (1 - fx) + tex[y0, x1] * fx
    b = tex[y0 + 1, x0] * (1 - fx) + tex[y0 + 1, x1] * fx
    return a * (1 - fy) + b * fy


def earth_matrix(lon_c, lat_c):
    la, lo = math.radians(lat_c), math.radians(lon_c)
    f = np.array([math.cos(la) * math.cos(lo), math.sin(la), math.cos(la) * math.sin(lo)])
    vz = -f
    n = np.array([0.0, 1.0, 0.0])
    vy = n - np.dot(n, vz) * vz
    vy /= np.linalg.norm(vy)
    vx = np.cross(vz, vy)
    return np.stack([vx, vy, vz])


def render_earth(c, t, dc, a):
    """Lancer de rayons sur la sphère terrestre (demi-résolution), avec nuages, reflets, atmosphère et nuit."""
    if a <= 0.003:
        return
    tx = textures()
    hw, hh, fh = W // 2, H // 2, F / 2
    rad_px = fh * math.tan(math.asin(min(0.9999, 1 / dc))) * 1.12 + 6
    x0, x1 = int(max(0, hw / 2 - rad_px)), int(min(hw, hw / 2 + rad_px + 1))
    y0, y1 = int(max(0, hh / 2 - rad_px)), int(min(hh, hh / 2 + rad_px + 1))
    if x1 <= x0 or y1 <= y0:
        return
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    r = roll_at(t)
    X, Y = (xs + 0.5 - hw / 2) / fh, -(ys + 0.5 - hh / 2) / fh
    cr, sr = math.cos(-r), math.sin(-r)
    X, Y = X * cr - Y * sr, X * sr + Y * cr
    d = np.stack([X, Y, np.ones_like(X)], -1)
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    bq = -dc * d[..., 2]
    disc = bq * bq - (dc * dc - 1)
    hit = disc > 0
    out = np.zeros(d.shape[:2] + (4,), np.float32)
    prog = ease((9.6 - L_at(t)) / 2.8)
    M = earth_matrix(FR_LON + 55 * (1 - prog), FR_LAT - 8 * (1 - prog))
    sun = SUN_DIR_VIEW
    if hit.any():
        dd = d[hit]
        tt = -bq[hit] - np.sqrt(disc[hit])
        p = np.array([0, 0, -dc], np.float32) + tt[:, None] * dd
        q = p @ M                                                          # coordonnées terrestres
        lat = np.degrees(np.arcsin(np.clip(q[:, 1], -1, 1)))
        lon = np.degrees(np.arctan2(q[:, 2], q[:, 0]))
        day = sample(tx["day"], lat, lon)
        cl = sample(tx["cloud"], lat, lon)[:, None]
        wat = sample(tx["water"], lat, lon)[:, None]
        ndl = p @ sun
        lit = np.clip(ndl * 1.25 + 0.12, 0, 1)[:, None] ** 0.9
        hv = sun[None, :] - dd
        hv /= np.linalg.norm(hv, axis=1, keepdims=True)
        spec = wat * np.clip((p * hv).sum(1), 0, 1)[:, None] ** 70 * 0.9 * lit
        col = day * (0.03 + 0.97 * lit) + spec * np.array([1.0, 0.95, 0.85])
        col = col * (1 - cl * 0.92) + cl * np.array([1.0, 1.0, 1.0]) * (0.02 + 0.98 * lit)
        rim = (1 - np.clip(-(dd * p).sum(1), 0, 1))[:, None] ** 3
        col += rim * np.array([0.3, 0.55, 1.0]) * 0.75 * np.clip(ndl + 0.35, 0, 1)[:, None]
        col += (1 - lit) * np.array([0.006, 0.01, 0.03])
        out[hit, :3] = col
        out[hit, 3] = 1
    miss = ~hit
    h = np.sqrt(np.maximum(0, dc * dc - bq[miss] ** 2))
    front = bq[miss] < 0
    o = np.array([0, 0, -dc], np.float32)
    cp = o + (-bq[miss])[:, None] * d[miss]                                 # point le plus proche du centre
    side = np.clip((cp @ sun) / np.maximum(h, 1e-6) + 0.4, 0, 1)
    glow = np.exp(-np.maximum(0, h - 1) / 0.022) * front * side
    out[miss, :3] = np.array([0.35, 0.6, 1.0]) * glow[:, None]
    out[miss, 3] = np.clip(glow, 0, 1)
    rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    rgba[..., :3] = np.clip(1 - np.exp(-out[..., :3] * 1.6), 0, 1) * 255 * out[..., 3:4].clip(0, 1) ** 0
    rgba[..., :3] = (np.clip(out[..., :3], 0, 1) * 255).astype(np.uint8)
    rgba[..., 3] = (np.clip(out[..., 3], 0, 1) * 255 * a).astype(np.uint8)
    rgba[..., :3] = (rgba[..., :3].astype(np.float32) * (rgba[..., 3:4] / 255.0)).astype(np.uint8)   # prémultiplié
    img = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.ColorType.kRGBA_8888_ColorType,
                               alphaType=skia.AlphaType.kPremul_AlphaType)
    c.drawImageRect(img, skia.Rect(x0 * 2, y0 * 2, x1 * 2, y1 * 2), skia.SamplingOptions(skia.FilterMode.kLinear))


def draw_moon(c, t, dc, a):
    if a <= 0.003:
        return
    z = MOON_V[2] + dc
    if z <= 0.1:
        return
    sx, sy = to_screen(np.array([MOON_V[0]]), np.array([MOON_V[1]]), np.array([z]), t)
    r = max(2.5, F * 0.273 / z)
    sun2 = SUN_DIR_VIEW[:2] / (np.linalg.norm(SUN_DIR_VIEW[:2]) + 1e-9)
    cx, cy = float(sx[0]), float(sy[0])
    sh = skia.GradientShader.MakeRadial(skia.Point(cx + sun2[0] * r * 0.5, cy - sun2[1] * r * 0.5), r * 1.4,
                                        [E1.rgb((235, 232, 225), 255 * a), E1.rgb((150, 148, 145), 255 * a),
                                         E1.rgb((20, 20, 24), 255 * a)], [0.0, 0.55, 1.0])
    c.drawCircle(cx, cy, r, P(shader=sh))
    if r > 6:
        text_c(c, "Lune", cx, cy - r - 24, 32, (220, 220, 230), 255 * a * min(1, (r - 6) / 10), shadow=False)


# ------------------------------------------------------------------------------------------------ fond et vitesse lumière
SKY_DIR = rng.normal(0, 1, (6000, 3))
SKY_DIR /= np.linalg.norm(SKY_DIR, axis=1, keepdims=True)
SKY_DIR = SKY_DIR[SKY_DIR[:, 2] > 0.2]
SKY_LUM = rng.lognormal(-0.8, 0.8, len(SKY_DIR))
SKY_COL = np.where(rng.random((len(SKY_DIR), 1)) < 0.3, [1.0, 0.85, 0.7], [0.85, 0.9, 1.0])
NEAR = rng.uniform(-1, 1, (2600, 3)) * np.array([60, 60, 100]) + np.array([0, 0, 100])


def draw_warp(c, t):
    s = speed_at(t)
    a = min(1.0, max(0.0, (s - 0.33) / 0.45))
    if a <= 0.01:
        return
    sc = scroll_at(t) * 60
    zz = (NEAR[:, 2] - sc) % 200 + 0.5
    ln = min(40.0, s * 7)
    z1 = zz + ln
    r = roll_at(t)
    cr, sr = math.cos(r), math.sin(r)
    for i in range(len(NEAR)):
        z = zz[i]
        if z < 2:
            continue
        x, y = NEAR[i, 0], NEAR[i, 1]
        X, Y = x * cr - y * sr, x * sr + y * cr
        ax, ay = W / 2 + F * X / z, H / 2 - F * Y / z
        if not (-80 < ax < W + 80 and -80 < ay < H + 80):
            continue
        bx, by = W / 2 + F * X / z1[i], H / 2 - F * Y / z1[i]
        c.drawLine(bx, by, ax, ay, P((215, 225, 255), 255 * a * min(1.0, 40 / z), stroke=1.4 if z > 25 else 2.4))


# ------------------------------------------------------------------------------------------------ système solaire (vectoriel)
def draw_solar(c, t, Dau, a):
    if a <= 0.003:
        return
    r = roll_at(t)
    cr, sr = math.cos(r), math.sin(r)

    def scr(p):
        z = p[..., 2] + Dau
        X, Y = p[..., 0] * cr - p[..., 1] * sr, p[..., 0] * sr + p[..., 1] * cr
        return W / 2 + F * X / np.maximum(z, 1e-9), H / 2 - F * Y / np.maximum(z, 1e-9), z

    for orb in ORBITS:
        sx, sy, z = scr(orb)
        path = skia.Path()
        pen = False
        for i in range(len(orb)):
            ok = z[i] > Dau * 0.02 and abs(sx[i]) < 6000 and abs(sy[i]) < 8000
            if ok and pen:
                path.lineTo(float(sx[i]), float(sy[i]))
            elif ok:
                path.moveTo(float(sx[i]), float(sy[i]))
            pen = ok
        c.drawPath(path, P((110, 255, 170), 90 * a, blur=4, stroke=5))
        c.drawPath(path, P((140, 255, 190), 170 * a, stroke=2))
    # le Soleil
    sx, sy, z = scr(SUN_V)
    if z > 0:
        rs = max(10.0, F * 0.00465 / z)
        c.drawCircle(float(sx), float(sy), rs * 7, P((255, 200, 120), 70 * a, blur=rs * 3))
        c.drawCircle(float(sx), float(sy), rs * 2.2, P((255, 230, 170), 200 * a, blur=rs))
        c.drawCircle(float(sx), float(sy), rs, P((255, 250, 235), 255 * a))
    for name, a_, size, col in PLANETS:
        if name == "Terre":
            continue
        p = PLANET_V[name]
        sx, sy, z = scr(p)
        if z <= 0:
            continue
        rp = max(2.2, F * size * 4.26e-5 / z * 1.0)
        c.drawCircle(float(sx), float(sy), rp * 2.5, P(col, 60 * a, blur=rp))
        c.drawCircle(float(sx), float(sy), rp, P(col, 255 * a))
        vis = min(1.0, max(0.0, (Dau / a_ - 0.8) / 2)) * min(1.0, max(0.0, (40 * a_ - Dau) / (20 * a_)))
        if vis > 0.02:
            text_c(c, name, float(sx), float(sy) - rp - 16, 28, (220, 235, 255), 220 * a * vis, shadow=False)
    # la Terre, point bleu (tant que la sphère n'est pas encore visible)
    sx, sy, z = scr(np.zeros(3))
    k = min(1.0, max(0.0, (L_at(t) - 9.9) / 0.5))
    c.drawCircle(float(sx), float(sy), 9, P((90, 160, 255), 110 * a * k, blur=6))
    c.drawCircle(float(sx), float(sy), 3.5, P((150, 200, 255), 255 * a * k))


# ------------------------------------------------------------------------------------------------ image complète
LABELS = [(26.4, 24.6, "L'univers observable : 93 milliards d'années-lumière"),
          (24.4, 23.4, "Superamas de la Vierge : 110 millions d'années-lumière"),
          (23.2, 22.1, "Groupe local : 10 millions d'années-lumière"),
          (21.8, 20.45, "La Voie lactée : 100 000 années-lumière"),
          (20.3, 19.3, "Le Soleil : à 26 000 années-lumière du centre"),
          (17.0, 15.9, "Alpha du Centaure : 4,2 années-lumière"),
          (14.2, 12.8, "Le système solaire : 9 milliards de km"),
          (12.6, 11.4, "La Terre et le Soleil : 150 millions de km"),
          (9.7, 8.5, "La Terre et la Lune : 384 400 km"),
          (8.3, 7.1, "La Terre : 12 742 km")]
ORBE_EXPR = [(0, "surpris"), (6, "neutre"), (15, "joie"), (22, "reflechit"), (28, "surpris"), (33, "neutre"),
             (38, "joie"), (46, "surpris"), (53, "amour")]
T_HOME = 55.3


def frame(c, t):
    Lg = L_at(t)
    D = 10 ** Lg
    img = np.zeros((H, W, 3), np.float32)
    diff = np.zeros((H // 8, W // 8, 3), np.float32)
    # ciel lointain
    z = SKY_DIR[:, 2]
    sx, sy = to_screen(SKY_DIR[:, 0], SKY_DIR[:, 1], z, t)
    sky_a = 1 - 0.8 * band(Lg, 23.6, 23.0, 5, 4)                              # la toile cosmique le remplace
    splat(img, sx, sy, SKY_COL * SKY_LUM[:, None] * 0.5 * sky_a)
    # A. toile cosmique
    aA = band(Lg, 30, 29, 23.3, 22.8)
    render_points(img, diff, WEB, WEB_LUM, WEB_COL, D / UA, K_WEB, t, aA, aA)
    # B. Voie lactée (+ Andromède) ; sa lueur diffuse reste en fond jusqu'au système solaire
    aBs = band(Lg, 23.4, 22.9, 19.4, 18.9)
    aBd = band(Lg, 23.4, 22.9, 13.0, 12.0)
    render_points(img, diff, MW_V, MW_LUM, MW_COL, D / UB, K_MW, t, aBs, aBd)
    render_points(img, diff, AND_V, AND_LUM, AND_COL, D / UB, K_MW, t, aBs * band(Lg, 23.4, 22.9, 21.0, 20.4),
                  aBd * band(Lg, 23.4, 22.9, 21.0, 20.4))
    dsm = None
    if aBs > 0.003:
        dsm = np.zeros((H // 4, W // 4, 1), np.float32)
        z = MW_DUST_V[:, 2] + D / UB
        m = z > 1e-6
        x4, y4 = to_screen(MW_DUST_V[m, 0], MW_DUST_V[m, 1], z[m], t)
        splat(dsm, x4 / 4, y4 / 4, (13.0 / z[m] ** 2 / 16 * aBs)[:, None])
    # C. voisinage solaire
    aC = band(Lg, 19.6, 19.1, 15.8, 15.2)
    render_points(img, diff, NB, NB_LUM, NB_COL, D / UC, 0.004, t, aC, aC * 0.5, cap=4.0)
    # D. ceintures (points) du système solaire
    aD = band(Lg, 15.2, 14.6, 10.6, 10.0)
    if aD > 0.003:
        for pts, v in ((BELT, 0.25), (KUIPER, 0.18)):
            zz = pts[:, 2] + D / UD
            m = zz > 1e-6
            bx, by = to_screen(pts[m, 0], pts[m, 1], zz[m], t)
            splat(img, bx, by, np.tile([0.8, 0.75, 0.7], (int(m.sum()), 1)) * v * aD)
    # composition lumineuse
    if dsm is not None:
        d8 = (np.minimum(dsm[:, :, 0], 1.0) * 255).astype(np.uint8)
        dimg = skia.Image.fromarray(np.ascontiguousarray(np.stack([d8, d8, d8, np.full_like(d8, 255)], -1)),
                                    colorType=skia.ColorType.kRGBA_8888_ColorType)
        ds = skia.Surface(W, H)
        ds.getCanvas().clear(skia.ColorBLACK)
        ds.getCanvas().drawImageRect(dimg, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear),
                                     skia.Paint(ImageFilter=skia.ImageFilters.Blur(10, 10)))
        dust = ds.makeImageSnapshot().toarray()[:, :, :1].astype(np.float32) / 255 * 3.2
        img = img * np.exp(-dust * 2.2) + dust * np.array([0.5, 0.26, 0.1], np.float32) * 0.6
    dfa = np.zeros((H // 8, W // 8, 4), np.uint8)
    dfa[..., :3] = np.clip(diff / 4, 0, 1) * 255
    dfa[..., 3] = 255
    dfi = skia.Image.fromarray(dfa, colorType=skia.ColorType.kRGBA_8888_ColorType)
    ds2 = skia.Surface(W, H)
    ds2.getCanvas().clear(skia.ColorBLACK)
    ds2.getCanvas().drawImageRect(dfi, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear),
                                  skia.Paint(ImageFilter=skia.ImageFilters.Blur(22, 22)))
    img = img + ds2.makeImageSnapshot().toarray()[:, :, :3].astype(np.float32) / 255 * 4
    expo = 1.6
    tone = 1 - np.exp(-img * expo)
    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., :3] = np.clip(tone * 255, 0, 255)
    rgba[..., 3] = 255
    simg = skia.Image.fromarray(rgba, colorType=skia.ColorType.kRGBA_8888_ColorType)
    c.clear(skia.Color(3, 3, 8))
    c.drawImage(simg, 0, 0)
    for sig, al in ((14, 0.75), (60, 0.5)):
        g = skia.Paint(ImageFilter=skia.ImageFilters.Blur(sig, sig), BlendMode=skia.BlendMode.kPlus)
        g.setAlphaf(al)
        c.drawImage(simg, 0, 0, skia.SamplingOptions(), g)
    # C. le Soleil au centre (étoile de plus en plus brillante), puis le système solaire
    if 19.3 > Lg > 14.0:
        k = band(Lg, 19.3, 18.2, 14.8, 14.0)
        rs = 3 + 16 * ease((18.5 - Lg) / 3.5)
        c.drawCircle(W / 2, H / 2, rs * 6, P((255, 210, 140), 90 * k, blur=rs * 2.5))
        c.drawCircle(W / 2, H / 2, rs, P((255, 248, 230), 255 * k))
        if Lg < 17.6:
            text_c(c, "le Soleil", W / 2, H / 2 - rs * 2 - 40, 34, (255, 225, 170),
                   255 * k * band(Lg, 17.6, 17.2, 15.6, 15.0), shadow=False)
    if aC > 0.05 and 17.2 > Lg > 15.9:                                     # étiquette sur Alpha du Centaure
        zc = ALPHA_CEN[2] + D / UC
        if zc > 0.2:
            ax, ay = to_screen(np.array([ALPHA_CEN[0]]), np.array([ALPHA_CEN[1]]), np.array([zc]), t)
            ax, ay = float(ax[0]), float(ay[0])
            if 0 < ax < W and 0 < ay < H:
                k = band(Lg, 17.2, 16.9, 16.2, 15.9)
                c.drawCircle(ax, ay, 34, P((255, 225, 170), 200 * k, stroke=2.5))
                text_c(c, "Alpha du Centaure", ax, ay - 50, 30, (255, 225, 170), 255 * k, shadow=False)
    if 23.0 > Lg > 21.3:                                                    # étiquette sur Andromède
        k = band(Lg, 23.0, 22.7, 21.7, 21.3)
        za = 25.0 + D / UB
        ax, ay = to_screen(np.array([-12.0]), np.array([9.0]), np.array([za]), t)
        ax, ay = float(ax[0]), float(ay[0])
        if 0 < ax < W and 0 < ay < H:
            c.drawCircle(ax, ay, 40, P((200, 210, 255), 170 * k, stroke=2))
            text_c(c, "Andromède", ax, ay - 56, 30, (200, 210, 255), 255 * k, shadow=False)
    if 20.4 > Lg > 19.2:                                                    # « le Soleil est ici » dans la galaxie
        k = band(Lg, 20.4, 20.1, 19.6, 19.2)
        rr = 26 + 6 * math.sin(t * 5)
        c.drawCircle(W / 2, H / 2, rr, P((255, 225, 170), 230 * k, stroke=3))
    draw_solar(c, t, D / UD, aD)
    # E. la Terre et la Lune
    aE = band(Lg, 10.4, 9.9, -5, -6)
    dc = 1 + D / RE
    if aE > 0.003:
        draw_moon(c, t, dc, aE * band(Lg, 10.4, 9.9, 7.6, 7.2))
        render_earth(c, t, dc, aE)
    draw_warp(c, t)
    # « Tu es ici »
    if t > T_HOME:
        k = ease((t - T_HOME) / 0.6)
        for i in range(2):
            ph = ((t - T_HOME) * 0.8 + i * 0.5) % 1.0
            c.drawCircle(W / 2, H / 2, 20 + 70 * ph, P((255, 90, 120), 220 * k * (1 - ph), stroke=4))
        c.drawCircle(W / 2, H / 2, 11, P((255, 90, 120), 255 * k))
        text_c(c, "Tu es ici.", W / 2, H / 2 - 110, 64, (255, 255, 255), 255 * k)
    # l'Orbe
    expr = [e for t0, e in ORBE_EXPR if t >= t0][-1]
    e = Etat(expr=expr, age=t - [t0 for t0, e_ in ORBE_EXPR if t >= t0][-1], humeur_mix=1.0)
    e.regard = (0.0, -0.6)
    e.cligne = (t % 3.1) < 0.12
    c.save()
    c.translate(540 + 14 * math.sin(t * 1.7), 1470 + 10 * math.sin(t * 2.3))
    c.scale(0.4, 0.4)
    draw_orbe(c, t, e)
    c.restore()
    # textes
    text_c(c, "« L'univers, c'est pas si grand »", 540, 250, 50, (255, 255, 255), 255)
    for hi, lo, s in LABELS:
        k = band(Lg, hi, hi - 0.25, lo + 0.25, lo)
        if k > 0.01:
            text_c(c, s, 540, 1700, 36 if len(s) < 44 else 32, (235, 225, 200), 255 * k)


# ------------------------------------------------------------------------------------------------ son et rendu
def soundtrack(path):
    sr = E1.SR
    n = int(DUR * sr)
    y = E1.music(DUR) * 1.4
    fx = np.zeros(n)

    def add(t0, s_, g=1.0):
        i = int(t0 * sr)
        m = min(n - i, len(s_))
        if m > 0:
            fx[i:i + m] += s_[:m] * g

    add(0.0, E1.swish(3.0, 0.3))
    add(0.1, E1.swell(0.25))
    prev = 0.0
    for t in np.arange(0.5, DUR, 0.25):                                     # un souffle à chaque accélération
        s = speed_at(t)
        if s > 0.45 and t - prev > 2.0:
            add(t, E1.swish(1.6, 0.18))
            prev = t
    for t0 in (12.5, 20.5, 26.5, 34.0, 41.5, 47.5, 51.5):                   # révélations
        add(t0, E1.swell(0.16))
    add(T_HOME, E1.sparkle(0.16))
    add(T_HOME + 0.2, E1.ding(784, 0.14))
    out_ = y + E1.soften(fx, 6)
    fade = np.minimum(1, np.minimum(np.arange(n) / (0.3 * sr), (n - np.arange(n)) / (1.2 * sr)))
    out_ = np.tanh(out_ * fade * 1.4) / np.tanh(1.4)
    st = np.stack([out_, out_], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def render_chunk(args):
    f0, f1, path = args
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", path],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(f0, f1):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
        if (f - f0) % 60 == 0:
            print(f"[{f0}-{f1}] {f}", flush=True)
    ff.stdin.close()
    ff.wait()
    return path


def render(out_path, procs=4):
    tmp = tempfile.mkdtemp()
    n = int(DUR * FPS)
    cuts = [n * i // (procs * 3) for i in range(procs * 3 + 1)]
    jobs = [(cuts[i], cuts[i + 1], f"{tmp}/part{i:02d}.mp4") for i in range(len(cuts) - 1)]
    with Pool(procs) as pool:
        parts = pool.map(render_chunk, jobs, chunksize=1)
    with open(f"{tmp}/list.txt", "w") as fl:
        fl.writelines(f"file '{p}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy",
                    f"{tmp}/v.mp4"], check=True)
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy", "-c:a",
                    "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/univers_retour.mp4")
