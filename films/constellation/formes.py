"""Nuages de points : formes de base et Grande Pyramide (dimensions réelles, y = nord→sud, z = haut)."""
import math

import numpy as np

HALF, HEIGHT = 115.0, 146.6
GG0, GG1 = np.array([0, -37.0, 21.7]), np.array([0, 5.0, 42.9])
VOID0, VOID1 = np.array([0, -27.0, 36.0]), np.array([0, 3.0, 51.0])


def rng(seed):
    return np.random.default_rng(seed)


def sphere(n, R, center=(0, 0, 0), seed=0, lines=0.45):
    """Sphère : une partie des points sur méridiens et parallèles (lecture « globe »), le reste uniforme."""
    g = rng(seed)
    m = int(n * lines)
    u = g.random(n - m) * 2 - 1
    th = g.random(n - m) * 2 * math.pi
    pts = [np.stack([np.sqrt(1 - u * u) * np.cos(th), np.sqrt(1 - u * u) * np.sin(th), u], 1)]
    k = g.integers(0, 2, m)
    lat = np.where(k == 0, np.round(g.uniform(-80, 80, m) / 10) * 10, g.uniform(-89, 89, m))
    lon = np.where(k == 1, np.round(g.uniform(0, 360, m) / 15) * 15, g.uniform(0, 360, m))
    la, lo = np.radians(lat), np.radians(lon)
    pts.append(np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], 1))
    P = np.concatenate(pts) * R + np.asarray(center)
    return P


def polyline(pts, n, jitter=0.0, seed=0):
    pts = np.asarray(pts, np.float64)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.r_[0, np.cumsum(seg)]
    s = np.sort(rng(seed).random(n)) * cum[-1]
    i = np.clip(np.searchsorted(cum, s) - 1, 0, len(seg) - 1)
    k = ((s - cum[i]) / np.maximum(seg[i], 1e-9))[:, None]
    P = pts[i] * (1 - k) + pts[i + 1] * k
    if jitter:
        P += rng(seed + 1).standard_normal(P.shape) * jitter
    return P


def pyramid_surface(n, seed=0, courses=60, course_frac=0.55):
    """Faces de la pyramide ; une partie des points se range sur les assises (lignes horizontales)."""
    g = rng(seed)
    # échantillonnage uniforme sur l'aire : z suit une densité ∝ (1 - z/h)
    v = g.random(n)
    z = HEIGHT * (1 - np.sqrt(1 - v))
    m = g.random(n) < course_frac
    z[m] = np.round(z[m] / HEIGHT * courses) / courses * HEIGHT + g.normal(0, 0.15, m.sum())
    z = np.clip(z, 0, HEIGHT)
    s = HALF * (1 - z / HEIGHT)
    face = g.integers(0, 4, n)
    w = g.uniform(-1, 1, n) * s
    x = np.where(face == 0, w, np.where(face == 1, s, np.where(face == 2, -w, -s)))
    y = np.where(face == 0, -s, np.where(face == 1, w, np.where(face == 2, s, -w)))
    P = np.stack([x, y, z], 1)
    # arêtes plus denses
    e = g.random(n) < 0.08
    t = g.random(e.sum())
    corner = g.integers(0, 4, e.sum())
    cxy = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], float)[corner] * HALF
    P[e, 0] = cxy[:, 0] * (1 - t)
    P[e, 1] = cxy[:, 1] * (1 - t)
    P[e, 2] = HEIGHT * t
    return P


def pyramid_volume(n, seed=0):
    g = rng(seed)
    v = g.random(n)
    z = HEIGHT * (1 - np.cbrt(1 - v))
    s = HALF * (1 - z / HEIGHT)
    x = g.uniform(-1, 1, n) * s
    y = g.uniform(-1, 1, n) * s
    return np.stack([x, y, z], 1)


def interior(n, seed=0):
    """Couloirs et chambres connus, en lignes de points."""
    ent = (0, -HALF + 17.0 * HALF / HEIGHT, 17.0)
    L = [
        [ent, (0, -6.0, -30.0)],
        [(0, -72.0, 2.0), tuple(GG0)],
        [tuple(GG0), (0, -2.9, 21.7)],
        [(0, -2.9, 21.7), (0, 2.9, 21.7), (0, 2.9, 25.5), (0, 0, 27.9), (0, -2.9, 25.5), (0, -2.9, 21.7)],
        [tuple(GG0), tuple(GG1), tuple(GG1 + [0, 0, 8.6]), tuple(GG0 + [0, 0, 8.6]), tuple(GG0)],
        [tuple(GG1), (0, 8.0, 42.9)],
        [(0, 8.0, 43.0), (0, 13.2, 43.0), (0, 13.2, 48.8), (0, 8.0, 48.8), (0, 8.0, 43.0)],
        [(0, -6, -30), (0, 8, -30), (0, 8, -26), (0, -6, -26), (0, -6, -30)],
    ]
    lens = np.array([sum(np.linalg.norm(np.subtract(a, b)) for a, b in zip(l, l[1:])) for l in L])
    counts = np.maximum(50, (n * lens / lens.sum()).astype(int))
    pts = [polyline(l, c, 0.15, seed + i) for i, (l, c) in enumerate(zip(L, counts))]
    # épaisseur en x pour donner du volume aux couloirs
    P = np.concatenate(pts)
    P[:, 0] += rng(seed + 9).uniform(-0.8, 0.8, len(P))
    return P


def capsule_dist(P, a=VOID0, b=VOID1):
    """Distance de chaque point au segment ab, et direction de sortie."""
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    c = a + t[:, None] * ab
    d = P - c
    dist = np.linalg.norm(d, axis=1)
    dirn = d / np.maximum(dist, 1e-6)[:, None]
    return dist, dirn, c
