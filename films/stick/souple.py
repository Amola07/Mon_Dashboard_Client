"""Membres souples d'Éclat : la logique du mouvement « rubber hose ».

Un bras, une jambe ou la colonne n'est pas une suite de segments raides articulés par un angle : c'est un tube
souple de longueur fixe. Ici chacun est une chaîne de points simulée (intégration de Verlet) :

  • elle est accrochée au corps par sa racine (épaule, bassin) ;
  • des « muscles » élastiques la tirent vers la forme voulue par la pose — un arc de cercle de longueur fixe,
    d'autant plus courbé que la main (ou le pied) est proche de la racine : il n'y a pas de coude ;
  • ces muscles sont plus forts près de la racine que vers l'extrémité : le mouvement part du centre et se
    propage jusqu'aux mains comme une vague (chevauchement d'action), l'extrémité suit en dernier, dépasse
    un peu puis revient (accompagnement) ;
  • la gravité fait légèrement pendre ce qui est libre ; un appui (pied posé, main qui tient un objet) reste
    fixé exactement là où il est ;
  • la colonne est elle-même une chaîne : les épaules suivent le bassin avec un léger retard, et le buste
    respire quand le personnage est immobile.
"""
import math

import numpy as np

from . import corps as K

N_LIMB = 8
N_SPINE = 6
SUB = 2                                                         # sous-pas de simulation par image


def _arc_table():
    th = np.linspace(1e-4, 1.92 * np.pi, 4000)
    ratio = np.sin(th / 2) / (th / 2)
    return ratio[::-1].copy(), th[::-1].copy()


RATIO, THETA = _arc_table()


def arc_points(S, H, L, side, n):
    """n points sur l'arc de cercle de longueur L allant de S à H, bombé du côté du point `side`."""
    S = np.asarray(S, float)
    H = np.asarray(H, float)
    d = H - S
    c = float(np.hypot(*d))
    t = np.linspace(0.0, 1.0, n)
    if c < 1e-6:
        return np.repeat(S[None], n, axis=0)
    if c >= L * 0.999:                                          # tendu (ou étiré) : ligne droite
        return S + np.outer(t, d)
    th = float(np.interp(c / L, RATIO, THETA))
    u = d / c
    nrm = np.array([-u[1], u[0]])
    M = (S + H) / 2
    if np.dot(nrm, np.asarray(side, float) - M) < 0:
        nrm = -nrm
    R = L / th
    C = M - nrm * R * math.cos(th / 2)
    a0 = math.atan2(S[1] - C[1], S[0] - C[0])
    sgn = 1.0
    e = C + R * np.array([math.cos(a0 + th), math.sin(a0 + th)])
    if np.hypot(*(e - H)) > 1.0:
        sgn = -1.0
    ang = a0 + sgn * th * t
    return C + R * np.stack([np.cos(ang), np.sin(ang)], axis=1)


def bezier_points(P0, C, P1, n):
    t = np.linspace(0.0, 1.0, n)[:, None]
    P0, C, P1 = (np.asarray(x, float) for x in (P0, C, P1))
    return (1 - t) ** 2 * P0 + 2 * (1 - t) * t * C + t ** 2 * P1


class Chain:
    def __init__(self, pts, length):
        self.p = np.array(pts, float)
        self.q = self.p.copy()
        self.rest = length / (len(pts) - 1)

    def step(self, root, target, k, grav, damp, pin=None, iters=8, stiff=0.9, bend=0.06):
        v = (self.p - self.q) * damp
        new = self.p + v + k[:, None] * (target - self.p) + grav
        new[0] = root
        if pin is not None:
            new[-1] = pin
        for _ in range(iters):
            seg = new[1:] - new[:-1]
            ln = np.maximum(np.hypot(seg[:, 0], seg[:, 1]), 1e-6)
            corr = seg * (((ln - self.rest) / ln) * 0.5 * stiff)[:, None]
            new[:-1] += corr
            new[1:] -= corr
            new[1:-1] += bend * ((new[:-2] + new[2:]) / 2 - new[1:-1])
            new[0] = root
            if pin is not None:
                new[-1] = pin
        self.q, self.p = self.p, new
        return new


def _near_wall(q, room, tol):
    return min(room - abs(q[0]), room - abs(q[1])) < tol


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
    return float(np.hypot(*(a + t * ab - p)))


def simulate(show, Y, X, room, G):
    """Y : articulations lissées (N, 13, 2) ; renvoie, par image, les chaînes (colonne, bras, jambes)."""
    N = len(Y)
    frames = show.frames
    ARM_L = K.UPPER + K.FORE
    LEG_L = K.THIGH + K.SHIN
    spine = Chain(np.linspace(Y[0][0], Y[0][2], N_SPINE), K.SPINE)
    arms = [Chain(np.linspace(Y[0][3], Y[0][10 + 2 * i], N_LIMB), ARM_L) for i in range(2)]
    legs = [Chain(np.linspace(Y[0][0], Y[0][6 + 2 * i], N_LIMB), LEG_L) for i in range(2)]
    k_spine = np.linspace(0.55, 0.35, N_SPINE)
    k_arm = np.linspace(0.55, 0.30, N_LIMB)
    k_leg = np.linspace(0.60, 0.38, N_LIMB)
    k_pinned = np.linspace(0.45, 0.35, N_LIMB)
    out = []
    for f in range(N):
        fr = frames[f]
        t = f / 60.0
        g = np.asarray(fr["g"], float)
        gm = min(2.5, float(np.hypot(*g)) / G)
        gdir = g / max(1e-6, float(np.hypot(*g)))
        prev = Y[f - 1] if f else Y[f]
        arrows = [(np.asarray(c, float), np.asarray(c, float) + np.array([math.cos(math.radians(ph)), math.sin(math.radians(ph))]) * L / 2,
                   np.asarray(c, float) - np.array([math.cos(math.radians(ph)), math.sin(math.radians(ph))]) * L / 2)
                  for c, ph, L in fr["arrows"]]
        stones = [(np.asarray(p, float), r) for p, r, _, _ in fr["stones"]]

        def contact(tip, tip_prev, hand):
            speed = float(np.hypot(*(tip - tip_prev)))
            if _near_wall(tip, room, 6.0) and speed < 2.5:
                return True
            if hand:
                for c, a, b in arrows:
                    if _seg_dist(tip, a, b) < 14:
                        return True
                for p, r in stones:
                    if float(np.hypot(*(tip - p))) < r + 12:
                        return True
            return False
        pel, chest, neck = Y[f][0], Y[f][1], Y[f][2]
        # quand tout le corps tourne vite (roulade, culbute), les muscles se raidissent : sans ça les membres
        # traîneraient derrière comme des nouilles et la silhouette deviendrait illisible
        d0, d1 = prev[2] - prev[0], neck - pel
        spin = abs(math.atan2(d0[0] * d1[1] - d0[1] * d1[0], d0[0] * d1[0] + d0[1] * d1[1]))
        firm = min(1.0, spin / 0.08) * 0.35
        # colonne : de la pose (courbe par le buste), + respiration
        mid = (pel + neck) / 2
        tgt_sp = bezier_points(pel, 2 * chest - mid, neck, N_SPINE)          # passe par le milieu du dos (courbe en C)
        up = (neck - pel) / max(1e-6, float(np.hypot(*(neck - pel))))
        breath = 0.0 * math.sin(2 * math.pi * 0.32 * t)            # tenues vraiment immobiles
        tgt_sp[1:] += up * breath * np.linspace(0, 1, N_SPINE)[1:, None]
        spine.rest = K.SPINE * fr["pose"].st / (N_SPINE - 1)     # le buste s'étire / s'écrase
        for s in range(SUB):
            a = (s + 1) / SUB
            root = prev[0] + (pel - prev[0]) * a
            sp = spine.step(root, tgt_sp, k_spine + firm, gdir * 0.01 * gm, 0.8)
        spn = spine.p
        sh_idx = K.SHOULDER / K.SPINE * (N_SPINE - 1)
        i0 = int(sh_idx)
        shoulder = spn[i0] + (spn[min(i0 + 1, N_SPINE - 1)] - spn[i0]) * (sh_idx - i0)
        arm_pts = []
        for i in range(2):
            hand, elbow = Y[f][10 + 2 * i], Y[f][9 + 2 * i]
            pinned = contact(hand, prev[10 + 2 * i], True)
            La = min(1.3 * ARM_L, max(ARM_L, float(np.hypot(*(hand - shoulder)))))   # bras élastique
            arms[i].rest = La / (N_LIMB - 1)
            tgt = arc_points(shoulder, hand, La, elbow, N_LIMB)
            # un bras levé volontairement (contre la gravité, ou tendu en apesanteur) est tenu par les muscles ;
            # un bras qui pend reste mou
            reach = hand - shoulder
            rn = max(1e-6, float(np.hypot(*reach)))
            effort = max(0.0, float(np.dot(reach / rn, -gdir))) if gm > 0.05 else min(1.0, rn / ARM_L)
            k = k_pinned if pinned else k_arm + np.linspace(0.0, 0.26, N_LIMB) * effort + firm
            grav = 0.0 if pinned else gdir * 0.015 * gm
            for s in range(SUB):
                arms[i].step(shoulder, tgt, k, grav, 0.82, pin=hand if pinned else None)
            arm_pts.append(arms[i].p.copy())
        leg_pts = []
        for i in range(2):
            foot, knee = Y[f][6 + 2 * i], Y[f][5 + 2 * i]
            pinned = contact(foot, prev[6 + 2 * i], False)
            Ll = min(1.25 * LEG_L, max(LEG_L, float(np.hypot(*(foot - pel)))))   # jambe élastique
            legs[i].rest = Ll / (N_LIMB - 1)
            tgt = arc_points(pel, foot, Ll, knee, N_LIMB)
            k = k_pinned if pinned else k_leg + firm
            grav = 0.0 if pinned else gdir * 0.012 * gm
            for s in range(SUB):
                legs[i].step(pel, tgt, k, grav, 0.8, pin=foot if pinned else None)
            leg_pts.append(legs[i].p.copy())
        out.append(dict(spine=spn.copy(), shoulder=shoulder.copy(), arms=arm_pts, legs=leg_pts))
    return out
