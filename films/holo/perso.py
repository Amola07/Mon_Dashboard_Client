"""Personnage Mixamo (ex. X Bot) en hologramme, animé par les vraies animations Mixamo.

Données (non versionnées, régénérées par films.holo.mixamo.export) : perso.npz + une .npz par animation.
Rendu : anneaux perpendiculaires à l'os de chaque membre + méridiens, lignes avant vives / arrière estompées,
contour de silhouette, voile lumineux, cœur 3D attaché à la poitrine. Pas de visage (X Bot n'en a pas).
"""
import math
import os

import numpy as np
import skia

from films.holo.holo import CYAN, CYAN_HI, RED
from films.holo import humain as HU

DATA = os.environ.get("MIXAMO_DATA", "/tmp/claude-0/-home-user-Mon-Dashboard-Client/074a8d09-4de2-5e84-a06b-0cddbabdcc79/"
                                     "scratchpad/mixamo")


class Perso:
    def __init__(self, folder=DATA):
        d = np.load(os.path.join(folder, "perso.npz"))
        self.V = d["v"].astype(np.float64)
        self.T = d["t"].astype(np.int64)
        self.wi = d["wi"].astype(np.int64)
        self.ww = d["ww"].astype(np.float64)
        self.bones = [str(b) for b in d["bones"]]
        self.heads, self.tails = d["heads"].astype(np.float64), d["tails"].astype(np.float64)
        part = d["part"] if "part" in d else np.zeros(len(self.V), np.int8)
        self.tpart = part[self.T[:, 0]]                    # 0 = surface, 1 = sphères d'articulation internes
        self.folder = folder
        self.anims = {}
        self._build()

    # -------------------------------------------------------------------------------------------- précalculs
    def _build(self, step=0.022):
        V, T = self.V, self.T
        dom = self.wi[T[:, 0], 0]                          # os dominant du triangle
        refs = []
        for b in np.unique(dom):
            for jpart in (0, 1):
                self._bone_refs(refs, b, np.where((dom == b) & (self.tpart == jpart))[0], step, jpart)
        refs = [r for r in refs if r is not None]
        self._finish(refs)

    def _bone_refs(self, refs, b, tri, step, jpart):
        V, T = self.V, self.T
        if not len(tri):
            return
        ax = self.tails[b] - self.heads[b]
        n = np.linalg.norm(ax)
        if n < 1e-4:
            return
        ax /= n
        e1 = np.cross(ax, [0, 0, 1.0] if abs(ax[2]) < 0.9 else [1.0, 0, 0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(ax, e1)
        P = V[T[tri]] - self.heads[b]
        for kind, c, levels in (("ring", P @ ax, None),
                                ("mer", None, [e1, e2, (e1 + e2) / 1.414, (e1 - e2) / 1.414])):
            if kind == "ring":
                for k in np.arange(math.floor(c.min() / step), math.ceil(c.max() / step) + 1) * step:
                    refs.append(self._cut(tri, c - k, 2 if jpart else 0))
            else:
                if not jpart:
                    for nrm in levels:
                        refs.append(self._cut(tri, P @ nrm, 1))

    def _finish(self, refs):
        T = self.T
        self.ref_idx = np.concatenate([r[0] for r in refs])
        self.ref_u = np.concatenate([r[1] for r in refs])
        self.ref_tri = np.concatenate([r[2] for r in refs])
        self.ref_kind = np.concatenate([r[3] for r in refs])
        e = {}
        for ti, t in enumerate(T):
            for i in range(3):
                a, b = int(t[i]), int(t[(i + 1) % 3])
                e.setdefault((min(a, b), max(a, b)), []).append(ti)
        self.edges = np.array([k for k, v in e.items() if len(v) == 2])
        self.efaces = np.array([v for v in e.values() if len(v) == 2])
        self.ejoint = self.tpart[self.efaces[:, 0]] == 1
        sp = self.bones.index("mixamorig:Spine2")
        chest = self.V[(np.abs(self.V[:, 1] - self.heads[sp][1] - 0.06) < 0.02) & (np.abs(self.V[:, 0]) < 0.06)]
        self.heart_pos = np.array([0.035, self.heads[sp][1] + 0.06, chest[:, 2].max() - 0.07 if len(chest) else 0.05])
        self.heart_bone = sp

    def _cut(self, tri, s, kind):
        sign = s > 0
        cross = sign.any(1) & ~sign.all(1)
        if not cross.any():
            return None
        T, sk = self.T[tri[cross]], s[cross]
        e = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            m = (sk[:, i] > 0) != (sk[:, j] > 0)
            u = sk[:, i] / np.where(m, sk[:, i] - sk[:, j], 1.0)
            e.append((T[:, i], T[:, j], u, m))
        ma, mb = e[0][3], e[0][3] & e[1][3]
        a_ = [np.where(ma, e[0][k], e[1][k]) for k in range(3)]
        b_ = [np.where(mb, e[1][k], e[2][k]) for k in range(3)]
        idx = np.stack([a_[0], a_[1], b_[0], b_[1]], 1).astype(np.int64)
        return idx, np.stack([a_[2], b_[2]], 1), tri[cross], np.full(len(idx), kind)

    # -------------------------------------------------------------------------------------------- animation
    def anim(self, name):
        if name not in self.anims:
            d = np.load(os.path.join(self.folder, name + ".npz"))
            self.anims[name] = d["m"].astype(np.float64)
        return self.anims[name]

    def mats(self, name, t, loop=True, fps=30.0):
        m = self.anim(name)
        f = t * fps
        n = len(m)
        if loop:
            f %= n
            i0 = int(f)
            i1 = (i0 + 1) % n
        else:
            f = min(max(f, 0.0), n - 1.001)
            i0 = int(f)
            i1 = i0 + 1
        u = f - int(f)
        return m[i0] * (1 - u) + m[i1] * u

    def skin(self, M):
        Vh = np.c_[self.V, np.ones(len(self.V))]
        out = np.zeros_like(self.V)
        for k in range(4):
            Mk = M[self.wi[:, k]]
            out += self.ww[:, k, None] * np.einsum("nij,nj->ni", Mk, Vh)[:, :3]
        return out

    # -------------------------------------------------------------------------------------------- dessin
    def draw(self, fr, M, pos=(0, 0, 0), yaw=0.0, a=1.0, t=0.0, beat_t=0.0, heart=True, reveal=1.0):
        V = self.skin(M)
        top = (V[:, 1].max() + 0.05) * reveal
        xf = lambda p: HU._xf(p, pos, yaw, 1.0)
        cl = HU._cam_local(fr, pos, yaw, 1.0)
        tp = V[self.T]
        tn = np.cross(tp[:, 1] - tp[:, 0], tp[:, 2] - tp[:, 0])
        tn /= np.linalg.norm(tn, axis=1, keepdims=True) + 1e-12
        tc = tp.mean(1)
        cc = fr.layers["c"].getCanvas()
        ok = (tc[:, 1] <= top) & (self.tpart == 0)
        pts, z = fr.cam.project(xf(tp[ok].reshape(-1, 3)))
        if len(z) and (z > 0.05).all():                    # voile lumineux
            cc.drawVertices(skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode,
                                                   [skia.Point(float(x), float(y)) for x, y in pts]),
                            skia.Paint(AntiAlias=True, Color=skia.Color(70, 150, 255, int(6 * a)),
                                       BlendMode=skia.BlendMode.kPlus))
        A = V[self.ref_idx[:, 0]] + (V[self.ref_idx[:, 1]] - V[self.ref_idx[:, 0]]) * self.ref_u[:, :1]
        B = V[self.ref_idx[:, 2]] + (V[self.ref_idx[:, 3]] - V[self.ref_idx[:, 2]]) * self.ref_u[:, 1:]
        segs = np.stack([A, B], 1)
        keep = segs[:, :, 1].max(1) <= top
        mid = segs.mean(1)
        front = ((cl - mid) * tn[self.ref_tri]).sum(1) > 0
        yb = (t * 0.32) % 2.4 - 0.2
        for kind, base_a, w in ((0, 0.9, 1.3), (1, 0.55, 1.0), (2, 0.3, 1.0)):
            k = keep & (self.ref_kind == kind)
            cc.drawPath(HU._segs_path(fr, xf(segs[k & front])), HU._paint(CYAN, a * base_a, w))
            cc.drawPath(HU._segs_path(fr, xf(segs[k & ~front])), HU._paint(CYAN, a * base_a * 0.22, w * 0.8))
            band = k & front & (np.abs(mid[:, 1] - yb) < 0.022)
            if band.any():
                cc.drawPath(HU._segs_path(fr, xf(segs[band])), HU._paint(CYAN_HI, a * 0.55, w + 0.3))
        facing = ((cl - tc) * tn).sum(1) > 0                # silhouette
        sil = facing[self.efaces[:, 0]] != facing[self.efaces[:, 1]]
        for jm, al, w in ((False, 1.0, 2.0), (True, 0.3, 1.2)):           # articulations : contour discret
            es = V[self.edges[sil & (self.ejoint == jm)]]
            es = es[es[:, :, 1].max(1) <= top]
            cc.drawPath(HU._segs_path(fr, xf(es)), HU._paint(CYAN_HI, a * al, w))
        if reveal < 1.0:
            from films.holo.holo import circle
            fr.poly(xf(circle((0, top, 0), 0.5, (0, 1, 0), 96)), CYAN_HI, a, 2.6)
        if heart and reveal > 0.85:
            Mh = M[self.heart_bone]
            hx = lambda q: q @ Mh[:3, :3].T + Mh[:3, 3]
            ph = (beat_t * 1.2) % 1.0
            beat = 1 + 0.1 * math.exp(-((ph - 0.05) / 0.04) ** 2) + 0.06 * math.exp(-((ph - 0.22) / 0.04) ** 2)
            hp = xf(hx(self.heart_pos[None]))[0]
            sc_, z_ = fr.cam.project(hp[None])
            rc = fr.layers["r"].getCanvas()
            if z_[0] > 0.05:
                rr = fr.cam.focal / z_[0] * 0.16
                rc.drawCircle(*sc_[0], rr, skia.Paint(AntiAlias=True, Color=skia.Color(255, 50, 70, int(26 * a * beat)),
                                                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle,
                                                                                          rr * 0.5)))
            for sg, al, w in ((HU.HEART_SEGS, 1.0, 1.6), (HU.HEART_SEGS_V, 0.45, 1.1)):
                p3 = hx((self.heart_pos + sg * beat).reshape(-1, 3)).reshape(-1, 2, 3)
                rc.drawPath(HU._segs_path(fr, xf(p3)), HU._paint(RED, a * al, w))
        return V
