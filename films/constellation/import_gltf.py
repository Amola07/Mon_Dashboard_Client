"""Convertit un personnage glTF au squelette « type Unreal » (ex. Quaternius Universal Base Characters, CC0)
au format des corps en particules (data/humain_<nom>.npz). À lancer avec le module bpy :

    python -m films.constellation.import_gltf fichier.gltf nom
"""
import sys

import bpy
import numpy as np

from films.constellation.humain import NAMES, SEG

# segment → (os de départ (tête), os d'arrivée (tête), préfixes d'os pondérés)
MAP = {"bassin": ("pelvis", "spine_03", ["root", "pelvis", "spine_01"]),
       "poitrine": ("spine_03", "neck_01", ["spine_02", "spine_03"]),
       "cou": ("neck_01", "Head", ["neck_01"]),
       "tete": ("Head", None, ["Head"])}
for s, b in (("L", "l"), ("R", "r")):
    MAP.update({f"clavicule.{s}": (f"clavicle_{b}", f"upperarm_{b}", [f"clavicle_{b}"]),
                f"bras.{s}": (f"upperarm_{b}", f"lowerarm_{b}", [f"upperarm_{b}"]),
                f"avantbras.{s}": (f"lowerarm_{b}", f"hand_{b}", [f"lowerarm_{b}"]),
                f"main.{s}": (f"hand_{b}", f"middle_01_{b}",
                              [f"hand_{b}"] + [f"{d}_0{i}_{b}" for d in ("index", "middle", "ring", "pinky", "thumb") for i in (1, 2, 3)]),
                f"cuisse.{s}": (f"thigh_{b}", f"calf_{b}", [f"thigh_{b}"]),
                f"jambe.{s}": (f"calf_{b}", f"foot_{b}", [f"calf_{b}"]),
                f"pied.{s}": (f"foot_{b}", f"ball_{b}", [f"foot_{b}"]),
                f"orteils.{s}": (f"ball_{b}", f"ball_leaf_{b}", [f"ball_{b}", f"ball_leaf_{b}"])})


def main(path, name, keep=("SuperHero", "Superhero", "Body", "body")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and any(k in o.name for k in keep)]
    Am = np.array(arm.matrix_world)
    head = {b.name: (Am @ np.r_[b.head_local, 1])[:3] for b in arm.data.bones}
    tail = {b.name: (Am @ np.r_[b.tail_local, 1])[:3] for b in arm.data.bones}
    V, F, W = [], [], []
    for o in meshes:
        Mw = np.array(o.matrix_world)
        me = o.data
        me.calc_loop_triangles()
        base = sum(len(v) for v in V)
        v = np.array([(Mw @ np.r_[p.co, 1])[:3] for p in me.vertices])
        f = np.array([t.vertices[:] for t in me.loop_triangles]) + base
        w = np.zeros((len(v), len(NAMES)))
        gname = {g.index: g.name for g in o.vertex_groups}
        seg_of = {}
        for gi, gn in gname.items():
            for sname, (_, _, bones) in MAP.items():
                if gn in bones:
                    seg_of[gi] = NAMES.index(sname)
        for i, p in enumerate(me.vertices):
            for ge in p.groups:
                if ge.group in seg_of:
                    w[i, seg_of[ge.group]] += ge.weight
        V.append(v); F.append(f); W.append(w)
    V, F, W = np.concatenate(V), np.concatenate(F), np.concatenate(W)
    W[W.sum(1) == 0, NAMES.index("poitrine")] = 1
    W /= W.sum(1, keepdims=True)
    # orientation : regard vers +y (les orteils devant les chevilles)
    rot = np.eye(3)
    if head["ball_l"][1] < head["foot_l"][1]:
        rot = np.diag([-1.0, -1.0, 1.0])
    V = V @ rot.T
    head = {k: rot @ v for k, v in head.items()}
    tail = {k: rot @ v for k, v in tail.items()}
    z0, z1 = V[:, 2].min(), V[:, 2].max()
    sc = 1.75 / (z1 - z0)
    sh = np.array([0, 0, -z0])
    V = (V + sh) * sc
    P = lambda b: (head[b] + sh) * sc
    ra, rb = [], []
    for s in NAMES:
        a, b, _ = MAP[s]
        ra.append(P(a))
        rb.append(P(b) if b else P(a) + np.array([0, 0, 0.22]))
    np.savez_compressed(f"films/constellation/data/humain_{name}.npz", v=V.astype(np.float32), f=F.astype(np.int32),
                        w=W.astype(np.float16), rest_a=np.array(ra, np.float32), rest_b=np.array(rb, np.float32),
                        side_low=(P("thigh_l") - P("thigh_r")).astype(np.float32),
                        side_up=(P("upperarm_l") - P("upperarm_r")).astype(np.float32))
    print(name, len(V), "sommets", len(F), "triangles")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
