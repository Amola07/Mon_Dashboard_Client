"""Corps humain réaliste en particules : maillage de base MakeHuman (CC0), animé par la capture CMU.

Le maillage MakeHuman est découpé en segments (bassin, poitrine, cou, tête, clavicules, bras, avant-bras, mains,
cuisses, jambes, pieds, orteils) d'après les poids de peau de son squelette. À chaque image, chaque segment suit
l'os CMU correspondant (direction de l'os + orientation du corps), et les points se mélangent selon les poids.

    python -m films.constellation.humain DOSSIER_MAKEHUMAN   # construit data/humain_mh.npz depuis base.obj,
                                                             # default.mhskel, default_weights.mhw (CC0)
Source : MakeHuman (makehumancommunity.org), maillage et squelette sous licence CC0.
"""
import json
import os
import sys

import numpy as np

from films.constellation import corps as K

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "humain_mh.npz")
DATA = os.path.join(HERE, "data")

# segment : (os CMU début, os CMU fin, côté de référence, os MakeHuman (tête, queue) pour le repos, os MH pondérés)
SEG = {
    "bassin": ("Hips", "Spine", "bas", ("root", "head"), ("spine03", "head"),
               ["root", "spine05", "spine04", "pelvis.L", "pelvis.R", "special01"]),
    "poitrine": ("Spine", "Neck", "haut", ("spine03", "head"), ("neck01", "head"),
                 ["spine03", "spine02", "spine01", "breast.L", "breast.R"]),
    "cou": ("Neck", "Head", "haut", ("neck01", "head"), ("head", "head"), ["neck01", "neck02", "neck03"]),
    "tete": ("Head", "Head_end", "haut", ("head", "head"), ("head", "tail"), None),
}
for s, S in (("L", "Left"), ("R", "Right")):
    SEG.update({
        f"clavicule.{s}": (f"{S}Shoulder", f"{S}Arm", "haut", (f"clavicle.{s}", "head"), (f"upperarm01.{s}", "head"),
                           [f"clavicle.{s}", f"shoulder01.{s}"]),
        f"bras.{s}": (f"{S}Arm", f"{S}ForeArm", "haut", (f"upperarm01.{s}", "head"), (f"lowerarm01.{s}", "head"),
                      [f"upperarm01.{s}", f"upperarm02.{s}"]),
        f"avantbras.{s}": (f"{S}ForeArm", f"{S}Hand", "haut", (f"lowerarm01.{s}", "head"), (f"wrist.{s}", "head"),
                           [f"lowerarm01.{s}", f"lowerarm02.{s}"]),
        f"main.{s}": (f"{S}Hand", f"{S}HandIndex1", "haut", (f"wrist.{s}", "head"), (f"finger3-1.{s}", "head"),
                      [f"wrist.{s}", "metacarpal", "finger"]),
        f"cuisse.{s}": (f"{S}UpLeg", f"{S}Leg", "bas", (f"upperleg01.{s}", "head"), (f"lowerleg01.{s}", "head"),
                        [f"upperleg01.{s}", f"upperleg02.{s}"]),
        f"jambe.{s}": (f"{S}Leg", f"{S}Foot", "bas", (f"lowerleg01.{s}", "head"), (f"foot.{s}", "head"),
                       [f"lowerleg01.{s}", f"lowerleg02.{s}"]),
        f"pied.{s}": (f"{S}Foot", f"{S}ToeBase", "bas", (f"foot.{s}", "head"), (f"toe3-1.{s}", "head"), [f"foot.{s}"]),
        f"orteils.{s}": (f"{S}ToeBase", f"{S}ToeBase_end", "bas", (f"toe3-1.{s}", "head"), (f"toe3-3.{s}", "tail"),
                         ["toe"]),
    })
NAMES = list(SEG)
PARENT = {"bassin": None, "poitrine": "bassin", "cou": "poitrine", "tete": "cou"}
for _s in ("L", "R"):
    PARENT.update({f"clavicule.{_s}": "poitrine", f"bras.{_s}": f"clavicule.{_s}", f"avantbras.{_s}": f"bras.{_s}",
                   f"main.{_s}": f"avantbras.{_s}", f"cuisse.{_s}": "bassin", f"jambe.{_s}": f"cuisse.{_s}",
                   f"pied.{_s}": f"jambe.{_s}", f"orteils.{_s}": f"pied.{_s}"})
TOPO = ["bassin", "poitrine", "cou", "tete"] + [f"{p}.{_s}" for _s in ("L", "R") for p in
                                              ("clavicule", "bras", "avantbras", "main", "cuisse", "jambe", "pied", "orteils")]


def _segment_of(bone):
    side = bone[-1] if bone[-2:] in (".L", ".R") else None
    for name, (_, _, _, _, _, bones) in SEG.items():
        if bones is None:
            continue
        if name.endswith((".L", ".R")) and side != name[-1]:
            continue
        for b in bones:
            if bone == b or (not b.endswith((".L", ".R")) and "." not in b and bone.startswith(b) and
                             b in ("metacarpal", "finger", "toe")):
                return name
    return "tete"                                  # visage, yeux, mâchoire, langue…


def build(folder):
    V, faces, group = [], [], None
    for line in open(os.path.join(folder, "base.obj")):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("g "):
            group = line.split()[1]
        elif line.startswith("f ") and group == "body":
            idx = [int(t.split("/")[0]) - 1 for t in line.split()[1:]]
            for k in range(1, len(idx) - 1):
                faces.append((idx[0], idx[k], idx[k + 1]))
    V = np.array(V)
    faces = np.array(faces)
    sk = json.load(open(os.path.join(folder, "default.mhskel")))
    joint = {k: V[v].mean(0) for k, v in sk["joints"].items()}

    def bone_pt(b, end):
        return joint[sk["bones"][b][end]]
    # repère : MakeHuman y en haut, regard vers +z → nous z en haut, regard vers +y (rotation propre)
    M = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float)
    used = np.unique(faces)
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    Vb = V[used] @ M.T
    faces = remap[faces]
    rest = {}
    for name, (_, _, _, a, b, _) in SEG.items():
        rest[name] = (bone_pt(*a) @ M.T, bone_pt(*b) @ M.T)
    rest_side_low = (bone_pt("upperleg01.L", "head") - bone_pt("upperleg01.R", "head")) @ M.T
    rest_side_up = (bone_pt("upperarm01.L", "head") - bone_pt("upperarm01.R", "head")) @ M.T
    # échelle 1,75 m, pieds au sol
    zmin, zmax = Vb[:, 2].min(), Vb[:, 2].max()
    sc = 1.75 / (zmax - zmin)
    shift = np.array([0, 0, -zmin])
    Vb = (Vb + shift) * sc
    rest = {k: ((a + shift) * sc, (b + shift) * sc) for k, (a, b) in rest.items()}
    # poids par segment
    W = np.zeros((len(V), len(NAMES)))
    wj = json.load(open(os.path.join(folder, "default_weights.mhw")))["weights"]
    for bone, lst in wj.items():
        s = NAMES.index(_segment_of(bone))
        for v, w in lst:
            W[v, s] += w
    W = W[used]
    tot = W.sum(1, keepdims=True)
    W[tot[:, 0] == 0, NAMES.index("poitrine")] = 1
    W /= W.sum(1, keepdims=True)
    np.savez_compressed(OUT, v=Vb.astype(np.float32), f=faces.astype(np.int32), w=W.astype(np.float16),
                        rest_a=np.array([rest[k][0] for k in NAMES], np.float32),
                        rest_b=np.array([rest[k][1] for k in NAMES], np.float32),
                        side_low=rest_side_low.astype(np.float32), side_up=rest_side_up.astype(np.float32))
    print(len(Vb), "sommets,", len(faces), "triangles ->", OUT)


def _frames(d, side):
    d = d / (np.linalg.norm(d, axis=-1, keepdims=True) + 1e-9)
    s = side - d * (side * d).sum(-1, keepdims=True)
    s = s / (np.linalg.norm(s, axis=-1, keepdims=True) + 1e-9)
    return np.stack([d, s, np.cross(d, s)], -1)              # colonnes : d, s, d×s


class Humain:
    def __init__(self, n=30000, seed=0, modele="mh"):
        d = np.load(os.path.join(DATA, f"humain_{modele}.npz"))
        V, Fc, W = d["v"].astype(np.float64), d["f"], d["w"].astype(np.float64)
        A, B, C = V[Fc[:, 0]], V[Fc[:, 1]], V[Fc[:, 2]]
        area = np.linalg.norm(np.cross(B - A, C - A), axis=1)
        g = np.random.default_rng(seed)
        tri = g.choice(len(Fc), n, p=area / area.sum())
        r1, r2 = g.random(n), g.random(n)
        s = np.sqrt(r1)
        bc = np.stack([1 - s, s * (1 - r2), s * r2], 1)
        self.rest = (V[Fc[tri]] * bc[:, :, None]).sum(1)
        self.w = (W[Fc[tri]] * bc[:, :, None]).sum(1)
        self.rest_a, self.rest_b = d["rest_a"].astype(np.float64), d["rest_b"].astype(np.float64)
        sides = np.array([d["side_low"] if SEG[k][2] == "bas" else d["side_up"] for k in NAMES], np.float64)
        self.F0 = _frames(self.rest_b - self.rest_a, sides)
        self.ia = [K.J[SEG[k][0]] for k in NAMES]
        self.ib = [K.J[SEG[k][1]] for k in NAMES]
        self.low = np.array([SEG[k][2] == "bas" for k in NAMES])
        self.order = [NAMES.index(k) for k in TOPO]
        self.hips_rest = self.rest_a[NAMES.index("bassin")]
        fk = [NAMES.index(k) for k in NAMES if k.startswith(("pied", "orteils"))]
        self.feet = self.w[:, fk].sum(1) > 0.5

    def points(self, P):
        """P : articulations CMU (28, 3) d'une image → nuage (n, 3).
        Les directions des os viennent de la capture ; les longueurs et points d'attache restent ceux du modèle
        (chaîne parent → enfant), donc le corps ne se déchire pas quand ses proportions diffèrent de la capture."""
        a, b = P[self.ia], P[self.ib]
        sl = P[K.J["LeftUpLeg"]] - P[K.J["RightUpLeg"]]
        su = P[K.J["LeftArm"]] - P[K.J["RightArm"]]
        side = np.where(self.low[:, None], sl, su)
        F1 = _frames(b - a, side)
        R = F1 @ np.transpose(self.F0, (0, 2, 1))           # (S, 3, 3)
        head = np.zeros((len(NAMES), 3))
        for k in self.order:
            p = PARENT[NAMES[k]]
            if p is None:
                head[k] = P[K.J["Hips"]] + (self.rest_a[k] - self.hips_rest)
            else:
                j = NAMES.index(p)
                head[k] = head[j] + R[j] @ (self.rest_a[k] - self.rest_a[j])
        out = np.zeros_like(self.rest)
        for k in range(len(NAMES)):
            wk = self.w[:, k]
            m = wk > 1e-3
            if not m.any():
                continue
            out[m] += ((self.rest[m] - self.rest_a[k]) @ R[k].T + head[k]) * wk[m, None]
        # pieds au sol comme dans la capture
        foot_cmu = P[[K.J["LeftToeBase"], K.J["RightToeBase"], K.J["LeftFoot"], K.J["RightFoot"]], 2].min()
        out[:, 2] += foot_cmu - self.foot_rest_gap(out)
        return out

    def foot_rest_gap(self, out):
        return np.percentile(out[self.feet, 2], 1) if self.feet.any() else 0.0

if __name__ == "__main__":
    build(sys.argv[1])
