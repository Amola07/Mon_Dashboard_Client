"""Extraction Mixamo → numpy (à lancer avec le module bpy) : maillage, poids de peau, matrices d'os par image.

    python -m films.holo.mixamo.export perso.fbx anim1.fbx anim2.fbx … sortie_dossier

Repère de sortie : mètres, Y vers le haut, personnage tourné vers +Z (même convention que films.holo).
"""
import os
import sys

import bpy
import numpy as np

AX = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)   # Blender (Z haut) → nous (Y haut)


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
    return arm, [o for o in bpy.data.objects if o.type == "MESH"]


def mat(m):
    return AX @ np.array(m, float)


def export_character(path, out):
    arm, meshes = load(path)
    bones = [b.name for b in arm.data.bones]
    bidx = {n: i for i, n in enumerate(bones)}
    verts, tris, wi, ww, part = [], [], [], [], []
    off = 0
    for ob in meshes:
        me = ob.data
        mw = mat(ob.matrix_world)
        co = np.array([v.co[:] for v in me.vertices], float)
        co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
        verts.append(co)
        part.append(np.full(len(co), 1 if "joint" in ob.name.lower() else 0, np.int8))
        me.calc_loop_triangles()
        tris.append(np.array([t.vertices[:] for t in me.loop_triangles]) + off)
        names = [g.name for g in ob.vertex_groups]
        for v in me.vertices:
            gs = sorted(((g.weight, bidx.get(names[g.group], -1)) for g in v.groups if names[g.group] in bidx),
                        reverse=True)[:4]
            gs += [(0.0, 0)] * (4 - len(gs))
            s = sum(w for w, _ in gs) or 1.0
            wi.append([b for _, b in gs])
            ww.append([w / s for w, _ in gs])
        off += len(co)
    rest = np.array([mat(arm.matrix_world @ b.matrix_local) for b in arm.data.bones])
    heads = np.array([(mat(arm.matrix_world) @ np.r_[b.head_local[:], 1])[:3] for b in arm.data.bones])
    tails = np.array([(mat(arm.matrix_world) @ np.r_[b.tail_local[:], 1])[:3] for b in arm.data.bones])
    parents = np.array([bidx[b.parent.name] if b.parent else -1 for b in arm.data.bones])
    np.savez_compressed(out, v=np.concatenate(verts).astype(np.float32), t=np.concatenate(tris).astype(np.int32),
                        wi=np.array(wi, np.int16), ww=np.array(ww, np.float32), bones=np.array(bones),
                        rest=rest.astype(np.float32), heads=heads.astype(np.float32),
                        tails=tails.astype(np.float32), parents=parents, part=np.concatenate(part))
    return bones, rest


def export_anim(path, bones, rest, out):
    arm, _ = load(path)
    act = arm.animation_data.action
    f0, f1 = (int(round(x)) for x in act.frame_range)
    inv_rest = np.linalg.inv(rest)
    mats = []
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        m = []
        for i, n in enumerate(bones):
            pb = arm.pose.bones.get(n)
            g = mat(arm.matrix_world @ pb.matrix) if pb else rest[i]
            m.append(g @ inv_rest[i])                       # matrice de peau : repos → pose
        mats.append(m)
    np.savez_compressed(out, m=np.array(mats, np.float32), fps=bpy.context.scene.render.fps)
    return f1 - f0 + 1


if __name__ == "__main__":
    *files, outdir = sys.argv[1:]
    os.makedirs(outdir, exist_ok=True)
    bones, rest = export_character(files[0], os.path.join(outdir, "perso.npz"))
    for f in files[1:]:
        name = os.path.splitext(os.path.basename(f))[0].split("-", 1)[-1].lower()
        n = export_anim(f, bones, rest, os.path.join(outdir, name + ".npz"))
        print(name, n, "images")
