"""Humain détaillé en hologramme, à partir du maillage CC0 de MakeHuman (data/humain.npz).

Finitions :
  - tête lissée (aucun trait de visage : ni nez, ni bouche, ni yeux, ni oreilles) ;
  - tranches horizontales / verticales qui épousent les volumes ; lignes avant vives, lignes arrière estompées ;
  - contour de silhouette recalculé selon la caméra ; voile lumineux très léger dans le corps ;
  - bande de balayage qui parcourt le corps ; cœur 3D rouge qui bat et éclaire la poitrine ;
  - socle de projection (anneaux, faisceau) et particules qui montent.
"""
import math
import os

import numpy as np
import skia

from films.holo.holo import CYAN, CYAN_HI, RED, W, H, circle

_D = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "humain.npz"))
V0 = _D["v"].astype(np.float64)
V0[:, 2] -= 0.1                                            # centre du torse sur z = 0
Q = _D["f"]

# ------------------------------------------------------------------------------------------------ tête sans visage
# on retire la tête d'origine (au-dessus du cou) et on la remplace par un ovoïde lisse, sans aucun trait
Q = Q[~(V0[Q].mean(1)[:, 1] > 1.41)]                       # le corps s'arrête à la base du cou
# cou + tête : une seule surface lisse (anneaux elliptiques), raccordée à la base du cou, sans aucun trait
_PROF = np.array([  # y, demi-largeur, demi-profondeur, centre en profondeur
    (1.395, 0.072, 0.075, -0.050), (1.430, 0.055, 0.063, -0.043), (1.470, 0.052, 0.060, -0.040),
    (1.495, 0.060, 0.072, -0.028), (1.512, 0.068, 0.085, -0.022), (1.540, 0.074, 0.094, -0.030),
    (1.580, 0.080, 0.098, -0.040), (1.620, 0.082, 0.098, -0.045), (1.650, 0.072, 0.088, -0.050),
    (1.668, 0.050, 0.060, -0.052), (1.678, 0.022, 0.028, -0.052), (1.682, 0.0, 0.0, -0.052)])
_ys = np.linspace(_PROF[0, 0], _PROF[-1, 0], 46)
_cols_ = [np.interp(_ys, _PROF[:, 0], _PROF[:, k]) for k in (1, 2, 3)]
_ker = np.array([1, 2, 3, 2, 1], float) / 9
_cols_ = [np.concatenate([c_[:2], np.convolve(c_, _ker, "valid"), c_[-2:]]) for c_ in _cols_]
_nv = 44
_hv = []
for y, rx, rz, zc in zip(_ys, *_cols_):
    for j in range(_nv):
        ph = 2 * math.pi * j / _nv
        _hv.append(np.array([rx * math.cos(ph), y, zc + rz * math.sin(ph)]))
_nu = len(_ys) - 1
_off = len(V0)
V0 = np.concatenate([V0, np.array(_hv)])
_hq = [[_off + i * _nv + j, _off + i * _nv + (j + 1) % _nv, _off + (i + 1) * _nv + (j + 1) % _nv,
        _off + (i + 1) * _nv + j] for i in range(_nu) for j in range(_nv)]
Q = np.concatenate([Q, np.array(_hq, Q.dtype)])

TRI = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
TRI = TRI[(TRI[:, 0] != TRI[:, 1]) & (TRI[:, 1] != TRI[:, 2]) & (TRI[:, 0] != TRI[:, 2])]
_tp = V0[TRI]
TN = np.cross(_tp[:, 1] - _tp[:, 0], _tp[:, 2] - _tp[:, 0])
TN /= np.linalg.norm(TN, axis=1, keepdims=True) + 1e-12
TC = _tp.mean(1)


def _slices(axis, step, lo, hi, V=None, T=None, N=None):
    """Segments de l'intersection maillage / plans, avec la normale du triangle d'origine."""
    V = V0 if V is None else V
    T = TRI if T is None else T
    N = TN if N is None else N
    P = V[T]
    c = P[:, :, axis]
    segs, nrm = [], []
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
        nrm.append(N[cross])
    return np.concatenate(segs), np.concatenate(nrm)


def _slice_refs(axis, step, lo, hi):
    """Comme _slices, mais chaque extrémité est mémorisée comme (sommet i, sommet j, u) : les tranches restent
    collées au corps quand il se déforme (marche)."""
    P = V0[TRI]
    c = P[:, :, axis]
    out = []
    for k in np.arange(lo, hi, step):
        s_ = c - k
        sign = s_ > 0
        cross = np.where(sign.any(1) & ~sign.all(1))[0]
        if not len(cross):
            continue
        T, sk = TRI[cross], s_[cross]
        e = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            m = (sk[:, i] > 0) != (sk[:, j] > 0)
            u = sk[:, i] / np.where(m, sk[:, i] - sk[:, j], 1.0)
            e.append((T[:, i], T[:, j], u, m))
        ma = e[0][3]
        mb = e[0][3] & e[1][3]
        a_ = [np.where(ma, e[0][k_], e[1][k_]) for k_ in range(3)]
        b_ = [np.where(mb, e[1][k_], e[2][k_]) for k_ in range(3)]
        out.append(np.stack([a_[0], a_[1], b_[0], b_[1]], 1).astype(np.int64))
        out[-1] = (out[-1], np.stack([a_[2], b_[2]], 1), cross)
    idx = np.concatenate([o[0] for o in out])
    uu = np.concatenate([o[1] for o in out])
    tri = np.concatenate([o[2] for o in out])
    return idx, uu, tri


def _segs_from(V, ref):
    idx, uu, _ = ref
    a = V[idx[:, 0]] + (V[idx[:, 1]] - V[idx[:, 0]]) * uu[:, :1]
    b = V[idx[:, 2]] + (V[idx[:, 3]] - V[idx[:, 2]]) * uu[:, 1:]
    return np.stack([a, b], 1)


REF_H = _slice_refs(1, 0.02, 0.01, 1.71)
REF_V = _slice_refs(0, 0.04, -0.5, 0.5)
SEG_H, NRM_H = _segs_from(V0, REF_H), TN[REF_H[2]]
SEG_V, NRM_V = _segs_from(V0, REF_V), TN[REF_V[2]]

# ------------------------------------------------------------------------------------------------ squelette (marche)
_R = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "rig.npz"))
BONES = [str(n) for n in _R["names"]]
PARENT = _R["parent"]
PIVOT = _R["piv"]
_nb = _D["v"].shape[0]
WEIGHTS = np.zeros((len(V0), len(BONES)))
WEIGHTS[:_nb] = _R["w"]
WEIGHTS[_nb:, BONES.index("neck01")] = 1.0                 # la tête lisse suit le cou


def rot(axis, deg):
    a = math.radians(deg)
    c, s_ = math.cos(a), math.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])
    if axis == "y":
        return np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])
    return np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])


def skin(rots, root_t=(0, 0, 0)):
    """rots : {os: matrice 3×3 (axes du repos)}. Renvoie (sommets déformés, transformations 4×4 par os)."""
    G = []
    for b, name in enumerate(BONES):
        Rb = rots.get(name, np.eye(3))
        L = np.eye(4)
        L[:3, :3] = Rb
        L[:3, 3] = PIVOT[b] - Rb @ PIVOT[b]
        if PARENT[b] < 0:
            T = np.eye(4)
            T[:3, 3] = root_t
            G.append(T @ L)
        else:
            G.append(G[PARENT[b]] @ L)
    G = np.array(G)
    Vd = np.zeros_like(V0)
    for b in range(len(BONES)):
        w = WEIGHTS[:, b]
        m = w > 1e-4
        if m.any():
            Vd[m] += w[m, None] * (V0[m] @ G[b, :3, :3].T + G[b, :3, 3])
    return Vd, G

_E = {}
for qi, q in enumerate(Q):
    for i in range(4):
        a, b = int(q[i]), int(q[(i + 1) % 4])
        if a != b:
            _E.setdefault((min(a, b), max(a, b)), []).append(qi)
EDGES = np.array([k for k, v in _E.items() if len(v) == 2])
EFACES = np.array([v for v in _E.values() if len(v) == 2])
_qv = V0[Q]
QN = np.cross(_qv[:, 2] - _qv[:, 0], _qv[:, 3] - _qv[:, 1])
QN /= np.linalg.norm(QN, axis=1, keepdims=True) + 1e-12
QC = _qv.mean(1)
HEART_POS = np.array([0.025, 1.3, 0.01])


# cœur 3D : surface paramétrique maillée, puis tranchée comme le corps (cohérent sous tous les angles)
def _heart_mesh(nu=26, nv=48):
    vs = []
    for u in np.linspace(0.0, math.pi, nu + 1):
        for v in np.linspace(0, 2 * math.pi, nv, endpoint=False):
            x = math.sin(u) * (15 * math.sin(v) - 4 * math.sin(3 * v))
            depth = 8 * math.cos(u)
            yv = math.sin(u) * (15 * math.cos(v) - 5 * math.cos(2 * v) - 2 * math.cos(3 * v) - math.cos(v))
            vs.append((x / 16 * 0.055, yv / 16 * 0.055, depth / 16 * 0.055))
    vs = np.array(vs)
    tris = []
    for i in range(nu):
        for j in range(nv):
            a_, b_ = i * nv + j, i * nv + (j + 1) % nv
            c_, d_ = (i + 1) * nv + (j + 1) % nv, (i + 1) * nv + j
            tris += [(a_, b_, c_), (a_, c_, d_)]
    tris = np.array(tris)
    p_ = vs[tris]
    n_ = np.cross(p_[:, 1] - p_[:, 0], p_[:, 2] - p_[:, 0])
    n_ /= np.linalg.norm(n_, axis=1, keepdims=True) + 1e-12
    return vs, tris, n_


_HV, _HT, _HN = _heart_mesh()
HEART_SEGS, _ = _slices(1, 0.0075, -0.07, 0.07, _HV, _HT, _HN)
HEART_SEGS_V, _ = _slices(0, 0.014, -0.07, 0.07, _HV, _HT, _HN)
_g = np.random.default_rng(5)
MOTES = np.stack([_g.uniform(0, 2 * math.pi, 140), _g.uniform(0.1, 0.62, 140), _g.uniform(0, 1, 140),
                  _g.uniform(0.6, 1.4, 140)], 1)


def _xf(p, pos, yaw, scale):
    c, s = math.cos(yaw), math.sin(yaw)
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    return np.stack([x * c + z * s, y, -x * s + z * c], -1) * scale + np.asarray(pos)


def _paint(col, a, w):
    return skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                      Color=skia.Color(*[int(v) for v in col], int(255 * max(0.0, min(1.0, a)))))


def _segs_path(fr, segs3):
    sc, z = fr.cam.project(segs3.reshape(-1, 3))
    sc = sc.reshape(-1, 2, 2)
    ok = (z.reshape(-1, 2) > 0.05).all(1)
    path = skia.Path()
    for (x0, y0), (x1, y1) in sc[ok]:
        path.moveTo(x0, y0)
        path.lineTo(x1, y1)
    return path


def _cam_local(fr, pos, yaw, scale):
    cpos = (fr.cam.pos - np.asarray(pos)) / scale
    c, s = math.cos(-yaw), math.sin(-yaw)
    return np.array([cpos[0] * c + cpos[2] * s, cpos[1], -cpos[0] * s + cpos[2] * c])


def pedestal(fr, t, pos=(0, 0, 0), scale=1.0, a=1.0):
    """Socle de projection : anneaux au sol, graduations qui tournent, faisceau vertical."""
    px, py, pz = pos
    for r, al, w in ((0.42, 0.9, 2.4), (0.55, 0.55, 1.6), (0.7, 0.3, 1.2)):
        fr.poly(circle((px, py + 0.002, pz), r * scale, (0, 1, 0), 96), CYAN_HI if r < 0.5 else CYAN, a * al, w)
    for k in range(36):
        th = t * 0.35 + k * 2 * math.pi / 36
        r0, r1 = 0.45 * scale, (0.5 if k % 3 else 0.53) * scale
        fr.poly([(px + r0 * math.cos(th), py, pz + r0 * math.sin(th)), (px + r1 * math.cos(th), py,
                                                                          pz + r1 * math.sin(th))], CYAN, a * 0.6, 1.4)
    c = fr.layers["c"].getCanvas()                         # faisceau : cône vaporeux
    base, _ = fr.cam.project(np.array([[px, py, pz], [px, py + 1.8 * scale, pz]]))
    (bx, by), (tx, ty) = base
    half = abs(fr.cam.project(np.array([[px + 0.42 * scale, py, pz]]))[0][0, 0] - bx)
    sh = skia.GradientShader.MakeLinear([skia.Point(bx, by), skia.Point(tx, ty)],
                                        [skia.Color(90, 170, 255, int(46 * a)), skia.Color(90, 170, 255, int(14 * a)),
                                         skia.Color(90, 170, 255, 0)], [0.0, 0.45, 1.0])
    p = skia.Path()
    p.moveTo(bx - half, by)
    p.cubicTo(bx - half * 0.9, (by + ty) / 2, tx - half * 0.5, ty + 80, tx - half * 0.45, ty)
    p.lineTo(tx + half * 0.45, ty)
    p.cubicTo(tx + half * 0.5, ty + 80, bx + half * 0.9, (by + ty) / 2, bx + half, by)
    p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh,
                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, half * 0.25)))


def motes(fr, t, pos=(0, 0, 0), scale=1.0, a=1.0):
    px, py, pz = pos
    pts = []
    for th, r, ph, sp in MOTES:
        h = ((ph + t * 0.06 * sp) % 1.0) * 1.9
        pts.append((px + r * math.cos(th + t * 0.1) * scale, py + h * scale, pz + r * math.sin(th + t * 0.1) * scale,
                    math.sin(math.pi * h / 1.9)))
    pts = np.array(pts)
    sc, z = fr.cam.project(pts[:, :3])
    c = fr.layers["c"].getCanvas()
    for (x, y), zz, k in zip(sc, z, pts[:, 3]):
        if zz > 0.1:
            c.drawCircle(x, y, 1.6, skia.Paint(AntiAlias=True, Color=skia.Color(190, 230, 255, int(170 * a * k))))


def human(fr, pos=(0, 0, 0), yaw=0.0, scale=1.0, a=1.0, heart=True, beat_t=0.0, reveal=1.0, t=0.0, scan=True,
          pose=None):
    """Dessine l'humain. reveal (0→1) : apparition de bas en haut, comme un scanner."""
    if a <= 0.004:
        return
    top = 1.75 * reveal
    cl = _cam_local(fr, pos, yaw, scale)
    if pose is None:
        V, G = V0, None
        tc, segsets = TC, ((SEG_H, NRM_H, 0.9, 1.3), (SEG_V, NRM_V, 0.5, 1.0))
        qn, qc = QN, QC
    else:
        V, G = pose
        tp = V[TRI]
        tn = np.cross(tp[:, 1] - tp[:, 0], tp[:, 2] - tp[:, 0])
        tn /= np.linalg.norm(tn, axis=1, keepdims=True) + 1e-12
        tc = tp.mean(1)
        segsets = ((_segs_from(V, REF_H), tn[REF_H[2]], 0.9, 1.3), (_segs_from(V, REF_V), tn[REF_V[2]], 0.5, 1.0))
        qv = V[Q]
        qn = np.cross(qv[:, 2] - qv[:, 0], qv[:, 3] - qv[:, 1])
        qn /= np.linalg.norm(qn, axis=1, keepdims=True) + 1e-12
        qc = qv.mean(1)
    cc = fr.layers["c"].getCanvas()
    # voile lumineux : triangles projetés, très transparents
    tri_ok = tc[:, 1] <= top
    pts, z = fr.cam.project(_xf(V[TRI[tri_ok]].reshape(-1, 3), pos, yaw, scale))
    if len(z) and (z > 0.05).all():
        verts = skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode,
                                       [skia.Point(float(x), float(y)) for x, y in pts])
        cc.drawVertices(verts, skia.Paint(AntiAlias=True, Color=skia.Color(70, 150, 255, int(7 * a)),
                                          BlendMode=skia.BlendMode.kPlus))
    # tranches : avant vives, arrière estompées
    yb = (t * 0.32) % 2.2 - 0.2                            # bande de balayage
    for segs, nrm, base_a, w in segsets:
        keep = segs[:, :, 1].max(1) <= top
        s, n = segs[keep], nrm[keep]
        mid = s.mean(1)
        front = ((cl - mid) * n).sum(1) > 0
        cc.drawPath(_segs_path(fr, _xf(s[front], pos, yaw, scale)), _paint(CYAN, a * base_a, w))
        cc.drawPath(_segs_path(fr, _xf(s[~front], pos, yaw, scale)), _paint(CYAN, a * base_a * 0.22, w * 0.8))
        if scan:
            band = np.abs(mid[:, 1] - yb) < 0.022
            if band.any():
                cc.drawPath(_segs_path(fr, _xf(s[band & front], pos, yaw, scale)), _paint(CYAN_HI, a * 0.55, w + 0.3))
    # silhouette
    facing = ((cl - qc) * qn).sum(1) > 0
    sil = facing[EFACES[:, 0]] != facing[EFACES[:, 1]]
    es = V[EDGES[sil]]
    es = es[es[:, :, 1].max(1) <= top]
    cc.drawPath(_segs_path(fr, _xf(es, pos, yaw, scale)), _paint(CYAN_HI, a, 2.1))
    if reveal < 1.0:                                       # anneau du scanner pendant l'apparition
        ring = circle((0, top, 0), 0.45, (0, 1, 0), 96)
        fr.poly(_xf(ring, pos, yaw, scale), CYAN_HI, a, 2.6)
    if heart and reveal > 0.85:
        ph = (beat_t * 1.2) % 1.0                          # « boum-boum »
        beat = 1 + 0.1 * math.exp(-((ph - 0.05) / 0.04) ** 2) + 0.06 * math.exp(-((ph - 0.22) / 0.04) ** 2)
        if G is not None:                                  # le cœur suit la poitrine
            Gc = G[BONES.index("spine02")]
            hxf = lambda q_: q_ @ Gc[:3, :3].T + Gc[:3, 3]
        else:
            hxf = lambda q_: q_
        hp = _xf(hxf(HEART_POS[None]), pos, yaw, scale)[0]
        sc_, z_ = fr.cam.project(hp[None])
        if z_[0] > 0.05:                                   # lueur rouge sur la poitrine
            rr = fr.cam.focal / z_[0] * 0.16 * scale
            fr.layers["r"].getCanvas().drawCircle(*sc_[0], rr, skia.Paint(
                AntiAlias=True, Color=skia.Color(255, 50, 70, int(26 * a * beat)),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, rr * 0.5)))
        rc = fr.layers["r"].getCanvas()
        for segs, al, w in ((HEART_SEGS, 1.0, 1.6), (HEART_SEGS_V, 0.45, 1.1)):
            pts3 = hxf((HEART_POS + segs * beat).reshape(-1, 3)).reshape(-1, 2, 3)
            rc.drawPath(_segs_path(fr, _xf(pts3, pos, yaw, scale)), _paint(RED, a * al, w))
