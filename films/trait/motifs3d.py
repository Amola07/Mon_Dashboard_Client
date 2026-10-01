"""Motifs 3D du style trait lumineux : l'iris en relief (un paysage de fibres), l'empreinte en relief, l'œil en
couches, le tourbillon de formation, les tores en spirographe, la poussière.
Unités : rayon de l'iris = 1 ; plan horizontal xz, hauteur y.
"""
import functools
import math

import numpy as np

from films.trait import trait as T2


def iris_h(r):
    """Relief de l'iris : bourrelet au bord de la pupille, collerette en crête, sillons vers l'extérieur."""
    r = np.asarray(r, float)
    return (0.035 * np.exp(-((r - 0.29) / 0.025) ** 2) + 0.075 * np.exp(-((r - 0.53) / 0.05) ** 2)
            + 0.03 * np.clip(1 - (r - 0.53) / 0.5, 0, 1) * (r > 0.53) + 0.02 * (r < 0.53) * (r > 0.3)
            - 0.012 * np.exp(-((r - 0.82) / 0.015) ** 2) - 0.012 * np.exp(-((r - 0.9) / 0.015) ** 2))


def _on_iris(p, lift=0.0, arch=None):
    r = np.hypot(p[:, 0], p[:, 1])
    y = iris_h(r) + lift
    if arch is not None:
        y = y + arch * np.sin(np.linspace(0, math.pi, len(p)))
    return np.stack([p[:, 0], y, p[:, 1]], 1)


def _split(shape):
    return [shape.pts[shape.starts[i]:shape.starts[i + 1]] for i in range(len(shape))]


@functools.lru_cache(1)
def iris3d(seed=5):
    d = T2.iris_detail(seed)
    rng = np.random.default_rng(seed + 100)
    out = {}
    out["red"] = [_on_iris(l, 0.004, rng.uniform(0.0, 0.07)) for l in _split(d["red"])]
    out["blue"] = [_on_iris(l, 0.006, rng.uniform(0.0, 0.05)) for l in _split(d["blue"])]
    out["cross"] = [_on_iris(l, 0.012, rng.uniform(0.01, 0.05)) for l in _split(d["cross"])]
    for k in ("limb", "ticks", "furrows", "collar", "crypts", "pupil"):
        out[k] = [_on_iris(l, 0.002) for l in _split(d[k])]
    # paroi de la pupille : des fibres qui plongent dans le noir
    wall = []
    for a in np.linspace(0, 2 * math.pi, 140, endpoint=False):
        dd = np.linspace(0, 1, 10)
        r = 0.28 - 0.02 * dd
        wall.append(np.stack([r * np.cos(a), 0.03 - 0.35 * dd ** 1.5, r * np.sin(a)], 1))
    out["wall"] = wall
    return out


@functools.lru_cache(1)
def iris_dust(n=500, seed=8):
    rng = np.random.default_rng(seed)
    r = np.sqrt(rng.uniform(0.09, 1.3, n))
    a = rng.uniform(0, 2 * math.pi, n)
    return np.stack([r * np.cos(a), rng.uniform(0.02, 0.5, n), r * np.sin(a)], 1)


@functools.lru_cache(1)
def finger3d(seed=3):
    """Empreinte en relief : chaque crête est une petite vague ; les crêtes sont dans le plan xz."""
    sh = T2.fingerprint(seed)
    out = []
    oline = T2.finger_outline()
    path_ok = lambda p: _inside(p, oline)
    for l in _split(sh):
        m = path_ok(l)
        cur = []
        for q, ok in zip(l, m):
            if ok:
                cur.append(q)
            elif len(cur) > 1:
                out.append(np.array(cur))
                cur = []
            else:
                cur = []
        if len(cur) > 1:
            out.append(np.array(cur))
    lines = [np.stack([l[:, 0], 0.012 + 0.006 * np.sin(l[:, 0] * 40), l[:, 1]], 1) for l in out]
    outline = [np.stack([oline[:, 0] * s, np.zeros(len(oline)), oline[:, 1] * s], 1) for s in (1.0, 1.05, 1.11)]
    return lines, outline


def _inside(p, poly):
    """Point dans polygone (rayons pairs/impairs), vectorisé sur p."""
    x, y = p[:, 0][:, None], p[:, 1][:, None]
    x1, y1 = poly[:, 0][None], poly[:, 1][None]
    x2, y2 = np.roll(poly[:, 0], -1)[None], np.roll(poly[:, 1], -1)[None]
    cond = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / np.where(y2 - y1 == 0, 1e-9, y2 - y1) + x1)
    return cond.sum(1) % 2 == 1


@functools.lru_cache(1)
def eye_layers():
    """Contours de l'œil en plans successifs (profondeur = parallaxe), plan vertical xy, z vers la caméra."""
    ep = T2.eye_parts()
    out = []
    for name, z in (("sweep", 0.55), ("crease", 0.3), ("outline", 0.18)):
        sh = ep[name]
        out.append((name, [np.stack([l[:, 0], -l[:, 1], np.full(len(l), z)], 1) for l in _split(sh)]))
    return out


@functools.lru_cache(2)
def swirl3d(seed=13, n=520):
    sh = T2.swirl(seed, n)
    out = []
    for l in _split(sh):
        r = np.hypot(l[:, 0], l[:, 1])
        y = 0.12 * np.cos(r * 3.2) + 0.05 * np.sin(l[:, 0] * 5 + l[:, 1] * 3)
        out.append(np.stack([l[:, 0], y, l[:, 1]], 1))
    return out


@functools.lru_cache(2)
def network3d(seed=11):
    sh = T2.network(seed)
    return [np.stack([l[:, 0], 0.05 * np.sin(l[:, 0] * 6), l[:, 1]], 1) for l in _split(sh)]


@functools.lru_cache(4)
def torus(n=40, R=0.62, r=0.36, tilt=0.0):
    """Anneau de cercles en vrai 3D : chaque cercle du spirographe est incliné autour de l'axe du tore."""
    out = []
    th = np.linspace(0, 2 * math.pi, 90)
    for a in np.linspace(0, 2 * math.pi, n, endpoint=False):
        ca, sa = math.cos(a), math.sin(a)
        # cercle dans le plan contenant l'axe radial, incliné de `tilt` → tore « tressé »
        u = np.cos(th) * r
        v = np.sin(th) * r
        x = (R + u) * ca - v * math.sin(tilt) * sa
        z = (R + u) * sa + v * math.sin(tilt) * ca
        y = v * math.cos(tilt)
        out.append(np.stack([x, y, z], 1))
    return out


@functools.lru_cache(4)
def spirals3d(m=46, twist=2.2, wob=0.0, lift=0.0):
    sh = T2.spirals(m, twist, wob=wob)
    return [np.stack([l[:, 0], lift + 0.05 * np.sin(np.hypot(l[:, 0], l[:, 1]) * 9), l[:, 1]], 1) for l in _split(sh)]


def ring3d(r=1.0, y=0.0, n=200):
    th = np.linspace(0, 2 * math.pi, n)
    return np.stack([r * np.cos(th), np.full(n, y), r * np.sin(th)], 1)


def xf(lines, R=None, t=(0, 0, 0), s=1.0):
    """Transforme des polylignes : rotation R (3×3), échelle s, translation t."""
    R = np.eye(3) if R is None else R
    return [l @ R.T * s + np.asarray(t, float) for l in lines]


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
