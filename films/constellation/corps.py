"""Personnages en particules animés par de la vraie capture de mouvement (base CMU, libre d'usage).

- convertir() : lit les BVH de mocap/bvh (non versionnés), calcule les positions des articulations, rééchantillonne
  à 30 im/s, met à l'échelle (1,75 m) et enregistre mocap/data/<nom>.npz (versionné, léger).
- Corps : un corps humain stylisé fait de capsules effilées autour des os (tronc elliptique, tête, mains, pieds),
  échantillonné en points une fois pour toutes, puis posé sur le squelette à chaque image.
Repère : z en haut ; le personnage regarde vers +y à l'image 0 ; yaw tourne autour de z.
Source : CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), conversion BVH de B. Hahne (cgspeed).
"""
import glob
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BVH_DIR = os.path.join(HERE, "mocap", "bvh")
DATA_DIR = os.path.join(HERE, "mocap", "data")
FPS = 30


# ------------------------------------------------------------------ lecture BVH
def _rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def read_bvh(path):
    tok = open(path).read().split()
    names, parents, offsets, chans = [], [], [], []
    stack, i = [], 0
    while tok[i] != "MOTION":
        t = tok[i]
        if t in ("ROOT", "JOINT"):
            names.append(tok[i + 1]); parents.append(stack[-1] if stack else -1); offsets.append(None); chans.append([])
            i += 2
        elif t == "End":
            names.append(names[stack[-1]] + "_end"); parents.append(stack[-1]); offsets.append(None); chans.append([])
            i += 2
        elif t == "{":
            stack.append(len(names) - 1); i += 1
        elif t == "}":
            stack.pop(); i += 1
        elif t == "OFFSET":
            offsets[stack[-1]] = np.array([float(x) for x in tok[i + 1:i + 4]]); i += 4
        elif t == "CHANNELS":
            k = int(tok[i + 1]); chans[stack[-1]] = tok[i + 2:i + 2 + k]; i += 2 + k
        else:
            i += 1
    nf = int(tok[i + 2]); dt = float(tok[i + 5])
    vals = np.array(tok[i + 6:], float).reshape(nf, -1)
    return names, np.array(parents), np.array(offsets), chans, vals, dt


def positions(names, parents, offsets, chans, vals):
    """Positions monde de toutes les articulations, (images, articulations, 3), repère BVH (y en haut)."""
    nf, nj = len(vals), len(names)
    P = np.zeros((nf, nj, 3))
    R = np.zeros((nf, nj, 3, 3))
    col = 0
    cidx = []
    for c in chans:
        cidx.append(list(range(col, col + len(c))))
        col += len(c)
    for j in range(nj):
        loc_t = np.tile(offsets[j], (nf, 1))
        loc_r = np.tile(np.eye(3), (nf, 1, 1))
        for c, k in zip(chans[j], cidx[j]):
            if c.endswith("position"):
                loc_t[:, "XYZ".index(c[0])] = vals[:, k]
            else:
                a = np.radians(vals[:, k])
                cc, ss = np.cos(a), np.sin(a)
                M = np.zeros((nf, 3, 3))
                if c[0] == "X":
                    M[:, 0, 0] = 1; M[:, 1, 1] = cc; M[:, 1, 2] = -ss; M[:, 2, 1] = ss; M[:, 2, 2] = cc
                elif c[0] == "Y":
                    M[:, 1, 1] = 1; M[:, 0, 0] = cc; M[:, 0, 2] = ss; M[:, 2, 0] = -ss; M[:, 2, 2] = cc
                else:
                    M[:, 2, 2] = 1; M[:, 0, 0] = cc; M[:, 0, 1] = -ss; M[:, 1, 0] = ss; M[:, 1, 1] = cc
                loc_r = loc_r @ M
        p = parents[j]
        if p < 0:
            P[:, j] = loc_t; R[:, j] = loc_r
        else:
            P[:, j] = P[:, p] + np.einsum("fij,fj->fi", R[:, p], loc_t)
            R[:, j] = R[:, p] @ loc_r
    return P


KEEP = ["Hips", "LowerBack", "Spine", "Spine1", "Neck", "Neck1", "Head", "Head_end",
        "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "LeftHandIndex1",
        "RightShoulder", "RightArm", "RightForeArm", "RightHand", "RightHandIndex1",
        "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "LeftToeBase_end",
        "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase", "RightToeBase_end"]


def convertir():
    os.makedirs(DATA_DIR, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(BVH_DIR, "*.bvh"))):
        names, parents, offsets, chans, vals, dt = read_bvh(path)
        P = positions(names, parents, offsets, chans, vals)
        idx = [names.index(k) for k in KEEP]
        P = P[:, idx]
        # 120 → 30 im/s
        step = max(1, int(round(1 / (dt * FPS))))
        P = P[::step]
        # repère : BVH y en haut → z en haut ; CMU regarde vers +z → nous vers +y
        P = np.stack([P[..., 0], P[..., 2], P[..., 1]], -1)
        # échelle : taille ≈ 1,75 m (tête - pieds sur la première image)
        h = P[0, KEEP.index("Head_end"), 2] - min(P[0, KEEP.index("LeftToeBase"), 2], P[0, KEEP.index("RightToeBase"), 2])
        P *= 1.75 / h
        # au sol : z mini des pieds = 0 à chaque image (en lissant)
        feet = P[:, [KEEP.index(k) for k in ("LeftToeBase", "RightToeBase", "LeftFoot", "RightFoot")], 2].min(1)
        P[..., 2] -= np.minimum(feet, feet[0])[:, None] * 0 + feet.min()
        # orientation : à l'image 0, les hanches perpendiculaires à +y (regard vers +y)
        hl, hr = P[0, KEEP.index("LeftUpLeg")], P[0, KEEP.index("RightUpLeg")]
        side = hl - hr
        fwd = np.array([-side[1], side[0]])
        ang = math.atan2(fwd[0], fwd[1])
        c, s = math.cos(ang), math.sin(ang)
        x, y = P[..., 0].copy(), P[..., 1].copy()
        P[..., 0], P[..., 1] = x * c - y * s, x * s + y * c
        if np.cross(np.r_[side[:2], 0], [0, 1, 0])[2] > 0 and (P[0, KEEP.index("LeftToeBase_end"), 1] < P[0, KEEP.index("LeftFoot"), 1]):
            P[..., 0] *= -1; P[..., 1] *= -1
        root0 = P[0, 0, :2].copy()
        P[..., :2] -= root0
        name = os.path.splitext(os.path.basename(path))[0].split("_", 2)[-1]
        np.savez_compressed(os.path.join(DATA_DIR, name + ".npz"), p=P.astype(np.float32))
        print(name, P.shape)


# ------------------------------------------------------------------ corps en particules
J = {k: i for i, k in enumerate(KEEP)}
# (articulation a, articulation b, rayon en a, rayon en b, part de points)
BONES = [("LeftUpLeg", "LeftLeg", 0.095, 0.06, 7), ("LeftLeg", "LeftFoot", 0.062, 0.042, 5),
         ("RightUpLeg", "RightLeg", 0.095, 0.06, 7), ("RightLeg", "RightFoot", 0.062, 0.042, 5),
         ("LeftFoot", "LeftToeBase_end", 0.045, 0.035, 2), ("RightFoot", "RightToeBase_end", 0.045, 0.035, 2),
         ("LeftArm", "LeftForeArm", 0.058, 0.044, 4), ("LeftForeArm", "LeftHand", 0.044, 0.032, 3.5),
         ("RightArm", "RightForeArm", 0.058, 0.044, 4), ("RightForeArm", "RightHand", 0.044, 0.032, 3.5),
         ("LeftHand", "LeftHandIndex1", 0.04, 0.03, 1.2), ("RightHand", "RightHandIndex1", 0.04, 0.03, 1.2),
         ("Neck", "Head", 0.055, 0.05, 1.2)]
# épaules et articulations : petites sphères (articulation, rayon, part)
JOINTS = [("LeftArm", 0.07, 1.2), ("RightArm", 0.07, 1.2), ("LeftLeg", 0.06, 0.6), ("RightLeg", 0.06, 0.6),
          ("LeftForeArm", 0.047, 0.4), ("RightForeArm", 0.047, 0.4)]


class Corps:
    def __init__(self, n=14000, seed=0):
        g = np.random.default_rng(seed)
        self.items = []
        tot = sum(b[4] for b in BONES) + 22 + 6 + sum(j[2] for j in JOINTS)
        # membres
        for a, b, r0, r1, w in BONES:
            m = int(n * w / tot)
            u = g.random(m)
            th = g.random(m) * 2 * np.pi
            self.items.append(("os", J[a], J[b], r0, r1, u, th))
        self.joints = []
        for jn, r, w in JOINTS:
            m = int(n * w / tot)
            v = g.normal(size=(m, 3))
            self.joints.append((J[jn], r * v / np.linalg.norm(v, axis=1, keepdims=True)))
        # tronc : section elliptique profilée (bassin, taille, poitrine, épaules) + fermetures haut et bas
        m = int(n * 22 / tot)
        self.trunk = (g.random(m), g.random(m) * 2 * np.pi)
        # tête : ellipsoïde
        m = int(n * 6 / tot)
        v = g.normal(size=(m, 3))
        self.head = v / np.linalg.norm(v, axis=1, keepdims=True)

    @staticmethod
    def _frame(d, ref):
        d = d / np.linalg.norm(d, axis=-1, keepdims=True)
        a = np.cross(d, ref)
        a /= np.linalg.norm(a, axis=-1, keepdims=True) + 1e-9
        b = np.cross(d, a)
        return d, a, b

    def points(self, P):
        """P : (articulations, 3) d'une image → nuage (n, 3)."""
        out = []
        for _, ja, jb, r0, r1, u, th in self.items:
            A, B = P[ja], P[jb]
            d = B - A
            L = np.linalg.norm(d) + 1e-9
            ref = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 * L else np.array([1.0, 0, 0])
            dd, e1, e2 = self._frame(d, ref)
            r = r0 * (1 - u) + r1 * u
            out.append(A + np.outer(u * L, dd) + np.outer(r * np.cos(th), e1) + np.outer(r * np.sin(th), e2))
        # tronc
        u, th = self.trunk
        hips, neck = P[J["Hips"]], P[J["Neck"]]
        sh = P[J["LeftArm"]] - P[J["RightArm"]]
        hp = P[J["LeftUpLeg"]] - P[J["RightUpLeg"]]
        axis = neck - hips
        L = np.linalg.norm(axis)
        dd = axis / L
        side = (sh * u[:, None] + hp * (1 - u[:, None]))
        side = side - np.outer(side @ dd, dd)
        side /= np.linalg.norm(side, axis=1, keepdims=True)
        front = np.cross(dd, side)
        uu = np.clip(u * 1.08 - 0.04, 0, 1)
        prof_w = np.interp(uu, [0, 0.15, 0.4, 0.7, 0.88, 1.0], [0.15, 0.16, 0.135, 0.165, 0.18, 0.09])
        prof_d = np.interp(uu, [0, 0.15, 0.4, 0.7, 0.88, 1.0], [0.10, 0.11, 0.095, 0.115, 0.10, 0.06])
        cap = (u < 0.04) | (u > 0.96)
        rad = np.where(cap, np.sqrt(np.random.default_rng(1).random(len(u))), 1.0)
        spine = hips + np.outer(uu * L, dd)
        out.append(spine + side * (prof_w * rad * np.cos(th))[:, None] + front * (prof_d * rad * np.sin(th))[:, None])
        for j, v in self.joints:
            out.append(P[j] + v)
        # tête
        head, top = P[J["Head"]], P[J["Head_end"]]
        c = (head + top) / 2 + np.array([0, 0, 0.02])
        hh = self.head * np.array([0.085, 0.095, 0.115])
        out.append(c + hh)
        return np.concatenate(out)


class Mouvement:
    def __init__(self, name):
        self.P = np.load(os.path.join(DATA_DIR, name + ".npz"))["p"].astype(np.float64)
        self.n = len(self.P)

    def at(self, t, loop=True, in_place=False, speed=1.0):
        f = t * FPS * speed
        f = f % (self.n - 1) if loop else min(max(f, 0), self.n - 1.001)
        i = int(f)
        k = f - i
        P = self.P[i] * (1 - k) + self.P[min(i + 1, self.n - 1)] * k
        if in_place:
            P = P.copy()
            P[:, :2] -= P[0, :2]
        return P


def pose(P, pos=(0, 0, 0), yaw=0.0):
    c, s = math.cos(yaw), math.sin(yaw)
    x, y = P[:, 0], P[:, 1]
    return np.stack([x * c - y * s, x * s + y * c, P[:, 2]], 1) + np.asarray(pos)


if __name__ == "__main__":
    convertir()
