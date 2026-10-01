"""Bonhomme bâton 2D à partir du rig « 2D StickMan Rig v2 » (Blend Swap n° 79370, licence CC BY 3.0).

Géométrie des segments et proportions extraites du .blend (stickman_rig.npz) ; la pose est calculée ici :
cinématique inverse à deux os pour les bras et les jambes, marche avec pieds posés au sol.
Coordonnées du bonhomme : x vers la droite, y vers le haut, hanches en (0, 0), hauteur ≈ 2,3.
"""
import math
import os

import numpy as np

_D = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stickman_rig.npz"))
BONES = [str(b) for b in _D["bones"]]
HEAD0 = {b: _D["heads"][i] for i, b in enumerate(BONES)}
TAIL0 = {b: _D["tails"][i] for i, b in enumerate(BONES)}
PARTS = {b: (_D[f"{b}__v"], _D[f"{b}__t"]) for b in BONES if f"{b}__v" in _D and b != "head_bone"}
ANG0 = {b: math.atan2(*(TAIL0[b] - HEAD0[b])[::-1]) for b in BONES}
LEN = {b: float(np.linalg.norm(TAIL0[b] - HEAD0[b])) for b in BONES}
HEAD_R = 0.2                                               # tête : un cercle lisse, sans visage


def _ik(root, target, l1, l2, bend):
    """Deux os : renvoie le coude/genou (bend = +1 ou −1 choisit le côté de pliure)."""
    d = np.asarray(target, float) - root
    dist = min(np.linalg.norm(d), l1 + l2 - 1e-4)
    dist = max(dist, abs(l1 - l2) + 1e-4)
    base = math.atan2(d[1], d[0])
    a = math.acos(max(-1, min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist))))
    ang = base + bend * a
    return root + l1 * np.array([math.cos(ang), math.sin(ang)])


def pose(hip=(0, 0), lean=0.0, neck=0.0, hands=None, feet=None, foot_ang=(0.0, 0.0), facing=1):
    """Pose complète → {os: (nouvelle tête, nouvel angle)}.

    lean / neck : inclinaison (radians, + = vers l'avant) ; hands / feet : cibles (x, y) relatives aux hanches.
    """
    hip = np.asarray(hip, float)
    P = {}
    up = math.pi / 2 - lean * facing
    belly_t = hip + LEN["belly_bone"] * np.array([math.cos(up), math.sin(up)])
    chest_t = belly_t + LEN["chest_bone"] * np.array([math.cos(up), math.sin(up)])
    nk = up - neck * facing
    neck_t = chest_t + LEN["neck"] * np.array([math.cos(nk), math.sin(nk)])
    P["belly_bone"] = (hip, up)
    P["chest_bone"] = (belly_t, up)
    P["neck"] = (chest_t, nk)
    P["_head"] = neck_t + HEAD_R * 0.85 * np.array([math.cos(nk), math.sin(nk)])
    hands = hands or {"l": (0.12 * facing, -0.16), "r": (-0.06 * facing, -0.16)}
    for s in ("l", "r"):
        tgt = hip + np.asarray(hands[s], float)
        el = _ik(chest_t, tgt, LEN[f"{s}_arm_bone"], LEN[f"{s}_forearm_bone"], -facing)
        P[f"{s}_arm_bone"] = (chest_t, math.atan2(*(el - chest_t)[::-1]))
        P[f"{s}_forearm_bone"] = (el, math.atan2(*(tgt - el)[::-1]))
    feet = feet or {"l": (0.12 * facing, -1.1), "r": (-0.1 * facing, -1.1)}
    for k, s in enumerate(("l", "r")):
        tgt = hip + np.asarray(feet[s], float)
        kn = _ik(hip, tgt, LEN[f"{s}_thigh_bone"], LEN[f"{s}_leg_bone"], facing)
        P[f"{s}_thigh_bone"] = (hip, math.atan2(*(kn - hip)[::-1]))
        P[f"{s}_leg_bone"] = (kn, math.atan2(*(tgt - kn)[::-1]))
        fa = foot_ang[k] if facing > 0 else math.pi - foot_ang[k]
        P[f"{s}_foot"] = (tgt, fa)
    P["_facing"] = facing
    return P


def triangles(P):
    """Triangles 2D (N, 3, 2) du corps posé, plus (centre, rayon) de la tête."""
    out = []
    for b, (v, t) in PARTS.items():
        if b not in P:
            continue
        h, a = P[b]
        a0 = ANG0[b]
        if b.endswith("_foot") and P["_facing"] < 0:
            a0 = ANG0[b]
        d = a - a0
        c, s_ = math.cos(d), math.sin(d)
        rel = v - HEAD0[b]
        if b.endswith("_foot") and P["_facing"] < 0:
            rel = rel * np.array([1, -1])                  # pied retourné quand il regarde à gauche
        w = np.stack([rel[:, 0] * c - rel[:, 1] * s_, rel[:, 0] * s_ + rel[:, 1] * c], 1) + h
        out.append(w[t])
    return np.concatenate(out), (P["_head"], HEAD_R)


# ------------------------------------------------------------------------------------------------ marche
def walk_feet(dist, stride=0.5, lift=0.14, stance=0.5, facing=1):
    """Cibles des pieds (relatives aux hanches) pour une distance parcourue `dist` : pieds posés pendant l'appui."""
    feet, angs = {}, []
    for s, off in (("l", 0.0), ("r", 0.5)):
        u = (dist / (2 * stride) + off) % 1.0
        if u < stance:                                     # appui : le pied recule à la vitesse des hanches
            rel = stride * (0.5 - u / stance)
            y = -1.1
            ang = 0.0
        else:                                              # balancement : le pied passe devant, en l'air
            v = (u - stance) / (1 - stance)
            rel = stride * (-0.5 + v)
            y = -1.1 + lift * math.sin(math.pi * v)
            ang = 0.35 * math.sin(math.pi * v)
        feet[s] = (facing * (rel + 0.05), y)
        angs.append(ang)
    return feet, tuple(angs)


def walk_hands(dist, facing=1, stride=0.5):
    ph = math.pi * dist / stride
    return {"l": (facing * (0.04 - 0.2 * math.sin(ph)), -0.14 + 0.05 * abs(math.sin(ph))),
            "r": (facing * (0.04 + 0.2 * math.sin(ph)), -0.14 + 0.05 * abs(math.sin(ph)))}
