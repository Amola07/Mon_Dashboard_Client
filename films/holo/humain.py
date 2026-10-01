"""Humain détaillé en hologramme, à partir du maillage CC0 de MakeHuman (data/humain.npz).

Rendu : tranches horizontales et verticales du vrai corps (lignes qui épousent les volumes), contour de silhouette
recalculé selon l'angle de caméra, cœur rouge en 3D dans la poitrine. Transparent, comme un hologramme.
"""
import math
import os

import numpy as np
import skia

from films.holo.holo import CYAN, CYAN_HI, RED, heart_2d

_D = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "humain.npz"))
V0 = _D["v"].astype(np.float64)
V0[:, 2] -= 0.1                                            # centre du torse sur z = 0
Q = _D["f"]
TRI = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
TRI = TRI[(TRI[:, 0] != TRI[:, 1]) & (TRI[:, 1] != TRI[:, 2]) & (TRI[:, 0] != TRI[:, 2])]


def _slices(axis, step, lo, hi):
    """Segments 3D de l'intersection du maillage avec les plans coord[axis] = k·step."""
    P = V0[TRI]                                            # (T, 3, 3)
    c = P[:, :, axis]
    segs = []
    for k in np.arange(lo, hi, step):
        s = c - k
        sign = s > 0
        cross = sign.any(1) & ~sign.all(1)
        if not cross.any():
            continue
        Pk, sk = P[cross], s[cross]
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            m = (sk[:, i] > 0) != (sk[:, j] > 0)
            u = sk[:, i] / np.where(m, sk[:, i] - sk[:, j], 1.0)
            pts.append((Pk[:, i] + (Pk[:, j] - Pk[:, i]) * u[:, None], m))
        a = np.where(pts[0][1][:, None], pts[0][0], pts[1][0])
        b = np.where(pts[0][1][:, None] & pts[1][1][:, None], pts[1][0], pts[2][0])
        segs.append(np.stack([a, b], 1))
    return np.concatenate(segs)


SEG_H = _slices(1, 0.022, 0.01, 1.67)                      # tranches horizontales (tous les 2,2 cm)
SEG_V = _slices(0, 0.045, -0.5, 0.5)                       # tranches verticales (tous les 4,5 cm)

# arêtes et faces voisines, pour la silhouette
_E = {}
for qi, q in enumerate(Q):
    for i in range(4):
        a, b = int(q[i]), int(q[(i + 1) % 4])
        if a == b:
            continue
        key = (min(a, b), max(a, b))
        _E.setdefault(key, []).append(qi)
EDGES = np.array([k for k, v in _E.items() if len(v) == 2])
EFACES = np.array([v for v in _E.values() if len(v) == 2])
_qv = V0[Q]
QN = np.cross(_qv[:, 2] - _qv[:, 0], _qv[:, 3] - _qv[:, 1])
QN /= np.linalg.norm(QN, axis=1, keepdims=True) + 1e-12
QC = _qv.mean(1)
HEART_POS = np.array([0.03, 1.29, 0.0])


def _xf(p, pos, yaw, scale):
    c, s = math.cos(yaw), math.sin(yaw)
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    return np.stack([x * c + z * s, y, -x * s + z * c], -1) * scale + np.asarray(pos)


def _draw_segs(fr, segs3, col, a, w, layer="c"):
    sc, z = fr.cam.project(segs3.reshape(-1, 3))
    sc = sc.reshape(-1, 2, 2)
    z = z.reshape(-1, 2)
    ok = (z > 0.05).all(1)
    sc = sc[ok]
    path = skia.Path()
    for (x0, y0), (x1, y1) in sc:
        path.moveTo(x0, y0)
        path.lineTo(x1, y1)
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                   Color=skia.Color(*[int(v) for v in col], int(255 * min(1.0, a))))
    fr.layers[layer].getCanvas().drawPath(path, p)


def human(fr, pos=(0, 0, 0), yaw=0.0, scale=1.0, a=1.0, heart=True, beat_t=0.0, reveal=1.0):
    """Dessine l'humain. reveal (0→1) : apparition de bas en haut, comme un scanner."""
    if a <= 0.004:
        return
    top = 1.7 * reveal
    sh = SEG_H[(SEG_H[:, 0, 1] <= top)]
    sv = SEG_V[(SEG_V[:, :, 1].max(1) <= top)]
    _draw_segs(fr, _xf(sh, pos, yaw, scale), CYAN, a * 0.85, 1.25)
    _draw_segs(fr, _xf(sv, pos, yaw, scale), CYAN, a * 0.45, 1.0)
    # silhouette : arêtes entre une face tournée vers la caméra et une face tournée vers l'arrière
    cpos = (fr.cam.pos - np.asarray(pos)) / scale
    c, s = math.cos(-yaw), math.sin(-yaw)
    cl = np.array([cpos[0] * c + cpos[2] * s, cpos[1], -cpos[0] * s + cpos[2] * c])
    facing = ((cl - QC) * QN).sum(1) > 0
    sil = facing[EFACES[:, 0]] != facing[EFACES[:, 1]]
    es = V0[EDGES[sil]]
    face = (es[:, :, 1].min(1) > 1.47) & (es[:, :, 2].max(1) > -0.02)   # pas de contours parasites sur le visage
    es = es[~face & (es[:, :, 1].max(1) <= top)]
    _draw_segs(fr, _xf(es, pos, yaw, scale), CYAN_HI, a, 2.0)
    if reveal < 1.0:                                       # ligne de balayage du scanner
        ring = np.array([[math.cos(t) * 0.42, top, math.sin(t) * 0.3] for t in np.linspace(0, 2 * math.pi, 64)])
        fr.poly(_xf(ring, pos, yaw, scale), CYAN_HI, a, 2.5)
    if heart and reveal > 0.8:
        beat = 1 + 0.08 * max(0.0, math.sin(beat_t * 7.5)) ** 8
        h = heart_2d() * 0.055 * beat
        for k, d in enumerate(np.linspace(-0.035, 0.035, 5)):
            sz = math.sqrt(max(0.0, 1 - (d / 0.04) ** 2))
            pts = np.stack([HEART_POS[0] + h[:, 0] * sz, HEART_POS[1] + h[:, 1] * sz, np.full(len(h), d)], 1)
            fr.poly(_xf(pts, pos, yaw, scale), RED, a, 2.2, layer="r")
