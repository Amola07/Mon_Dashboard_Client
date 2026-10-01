"""Vol à travers les étoiles : des milliers d'étoiles en vrais points 3D, la caméra accélère, le flou de
mouvement les étire en traits (comme l'ouverture de la vidéo de référence). Un voile de nébuleuse au fond.

blender -b -P hyperespace.py -- --out /chemin/hyp_ --frames 120 --vitesse 1.0
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import commun as C  # noqa: E402


def point_cloud(name, pts, radius, color, strength):
    me = bpy.data.meshes.new(name)
    me.from_pydata(pts, [], [])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    m, N = C.material(name)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    out = N.new("ShaderNodeOutputMaterial")
    N.link(em.outputs["Emission"], out.inputs["Surface"])
    gn = bpy.data.node_groups.new(name, "GeometryNodeTree")
    gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = gn.nodes.new("NodeGroupInput")
    go = gn.nodes.new("NodeGroupOutput")
    mp = gn.nodes.new("GeometryNodeMeshToPoints")
    mp.inputs["Radius"].default_value = radius
    sm = gn.nodes.new("GeometryNodeSetMaterial")
    sm.inputs["Material"].default_value = m
    gn.links.new(gi.outputs[0], mp.inputs["Mesh"])
    gn.links.new(mp.outputs["Points"], sm.inputs["Geometry"])
    gn.links.new(sm.outputs["Geometry"], go.inputs[0])
    mod = ob.modifiers.new(name, "NODES")
    mod.node_group = gn
    return ob


def main():
    a = C.args({"--vitesse": dict(type=float, default=1.0), "--etoiles": dict(type=int, default=7000)})
    sc = C.reset()
    C.setup_render(sc, a, motion_blur=True)
    sc.render.motion_blur_shutter = 0.6
    C.bloom(sc, size=6, threshold=0.7)
    C.starfield(sc, density=1.0, milky=0.35, tint=(0.45, 0.4, 1.0), strength=0.8)
    rng = random.Random(a.seed)
    length = 160.0 * a.vitesse
    groups = {"blanc": ((1.0, 1.0, 1.0), []), "bleu": ((0.55, 0.7, 1.0), []), "or": ((1.0, 0.75, 0.4), [])}
    for _ in range(a.etoiles):
        r = 1.5 + abs(rng.gauss(0, 7.0))                   # un couloir vide au centre : on fonce entre les étoiles
        th = rng.uniform(0, 2 * math.pi)
        z = -rng.uniform(0, length + 60)
        key = rng.choices(list(groups), weights=(6, 3, 2))[0]
        groups[key][1].append((r * math.cos(th), r * math.sin(th), z))
    for name, (col, pts) in groups.items():
        point_cloud(name, pts, 0.018, col, 30.0)
    cam = C.camera(sc, lens=20)
    cam.rotation_euler = (0, 0, 0)                        # regarde vers −z
    # accélération progressive (ease-in), puis plein régime
    n = a.frames
    for f in range(1, n + 1, max(1, n // 12)):
        u = (f - 1) / max(1, n - 1)
        cam.location = (0, 0, -length * (u ** 2.2))
        cam.keyframe_insert("location", frame=f)
    cam.location = (0, 0, -length)
    cam.keyframe_insert("location", frame=n)
    cam.rotation_euler = (0, 0, 0)
    cam.keyframe_insert("rotation_euler", frame=1)
    cam.rotation_euler = (0, 0, math.radians(25))          # roulis lent
    cam.keyframe_insert("rotation_euler", frame=n)
    C.render(sc, a)


main()
