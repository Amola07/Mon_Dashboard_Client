"""Même scène (ouvriers tirant un bloc vers la pyramide en chantier, de nuit) rendue dans plusieurs styles avec
Blender (bpy), pour choisir une direction artistique.

    python -m films.styles.comparaison DOSSIER [style …]     styles : silhouette traits surfaces voxels gravure
"""
import math
import os
import sys

import bpy
import numpy as np

from films.constellation import corps as CO
from films.constellation import formes as F
from films.constellation import humain as HU

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
STYLES = sys.argv[2:] or ["silhouette", "traits", "surfaces", "voxels", "gravure"]

# ------------------------------------------------------------------ géométrie de la scène (repère des épisodes)
SLED0 = np.array([150.0, -262.0, 0.0])
D = -SLED0[:2] / np.linalg.norm(SLED0[:2])
D3, L3 = np.array([D[0], D[1], 0.0]), np.array([-D[1], D[0], 0.0])
U = 7.0                                    # instant de la démo (secondes depuis 24,6 s)
ZB = 76.0                                  # hauteur atteinte par le chantier
SLED = SLED0 + D3 * 0.44 * (U - 4.4)


def pyramid_mesh(zmax=ZB, steps=46):
    zs = [z for z in F.Z_COURSES if z <= zmax]
    zs = zs[:: max(1, len(zs) // steps)] + [zmax]
    V, Fc = [], []
    for z0, z1 in zip(zs[:-1], zs[1:]):
        s = F.HALF * (1 - z1 / F.HEIGHT) + 0.35
        b = len(V)
        V += [(-s, -s, z0), (s, -s, z0), (s, s, z0), (-s, s, z0), (-s, -s, z1), (s, -s, z1), (s, s, z1), (-s, s, z1)]
        Fc += [(b, b + 1, b + 5, b + 4), (b + 1, b + 2, b + 6, b + 5), (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7),
               (b + 4, b + 5, b + 6, b + 7)]
    return np.array(V), Fc


def workers():
    """Maillages des 8 ouvriers à l'instant U (même logique que la démo)."""
    out = []
    pulls = [(CO.Mouvement("tirer_lourd"), 110), (CO.Mouvement("trainer_lourd_1"), 125), (CO.Mouvement("trainer_lourd_2"), 110)]
    mods = ("qt_male", "mh", "qt_male", "qt_female")
    yaw = math.atan2(D[1], D[0])
    Rz = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
    bodies = {}
    for k in range(8):
        side, dist, ph = 0.8 * (k % 2 * 2 - 1), 3.0 + 1.6 * (k // 2), 9 * k
        mv, f0 = pulls[k % 3]
        P = mv.at((f0 + ph + (U - 4.4) * 30) / 30, loop=False)
        P0 = mv.P[int(f0 + ph), 0]
        Q = (P - [P0[0], P0[1], 0]) @ Rz.T + SLED0 + D3 * dist + L3 * side
        m = mods[k % 4]
        if m not in bodies:
            h = HU.Humain(10, modele=m)
            d = np.load(os.path.join(HU.DATA, f"humain_{m}.npz"))
            h.rest, h.w = d["v"].astype(np.float64), d["w"].astype(np.float64)
            fk = [HU.NAMES.index(n) for n in HU.NAMES if n.startswith(("pied", "orteils"))]
            h.feet = h.w[:, fk].sum(1) > 0.5
            bodies[m] = (h, d["f"])
        h, fc = bodies[m]
        out.append((h.points(Q), fc, (Q[CO.J["LeftHand"]] + Q[CO.J["RightHand"]]) / 2))
    return out


def new_mesh(name, V, Fc, mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in Fc])
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def box(name, c, size, mat, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(c))
    o = bpy.context.active_object
    o.name, o.scale, o.rotation_euler = name, size, (0, 0, rot_z)
    o.data.materials.append(mat)
    return o


def cyl(a, b, r, mat):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=float(np.linalg.norm(d)), location=tuple((a + b) / 2))
    o = bpy.context.active_object
    from mathutils import Vector
    o.rotation_euler = Vector(d).to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    return o


def mat(name, color, emit=0.0, rough=0.8, emit_color=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def world_gradient(top, bottom, strength=1.0):
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.0, 0.45
    ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = (*bottom, 1), (*top, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.5, 0.7
    nt.links.new(ramp.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = strength
    bpy.context.scene.world = w


def build(style):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    pal = {
        "silhouette": dict(stone=(0, 0, 0), body=(0, 0, 0), ground=(0.0, 0.0, 0.0)),
        "traits": dict(stone=(0.003, 0.006, 0.012), body=(0.003, 0.006, 0.012), ground=(0.002, 0.003, 0.006)),
        "surfaces": dict(stone=(0.55, 0.42, 0.26), body=(0.35, 0.22, 0.14), ground=(0.42, 0.32, 0.2)),
        "voxels": dict(stone=(0.62, 0.48, 0.3), body=(0.45, 0.3, 0.2), ground=(0.4, 0.3, 0.18)),
        "gravure": dict(stone=(0.93, 0.86, 0.72), body=(0.93, 0.86, 0.72), ground=(0.93, 0.86, 0.72)),
    }[style]
    stone, body, ground = (mat(n, pal[n]) for n in ("stone", "body", "ground"))
    rope = mat("corde", (0.5, 0.35, 0.18)) if style != "silhouette" else mat("corde", (0, 0, 0))
    V, Fc = pyramid_mesh()
    if style == "voxels":
        vox(V, Fc, stone, 2.5)
    else:
        new_mesh("pyramide", V, Fc, stone)
    bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(ground)
    # rampe, traîneau, bloc
    yaw = math.atan2(D[1], D[0])
    box("bloc", SLED + [0, 0, 0.8], (2.0, 1.4, 1.1), stone, yaw)
    for s in (-0.55, 0.55):
        box("patin", SLED + L3 * s + [0, 0, 0.12], (2.6, 0.12, 0.18), rope, yaw)
    for k, (Vw, fw, hand) in enumerate(workers()):
        if style == "voxels":
            vox(Vw, fw, body, 0.07)
        else:
            new_mesh(f"ouvrier{k}", Vw, fw, body)
        cyl(SLED + D3 * 1.1 + L3 * (0.8 * (k % 2 * 2 - 1)) * 0.4 + [0, 0, 0.9], hand, 0.02, rope)
    # torches et lune
    torch_pts = [SLED + D3 * d + L3 * s for d, s in ((2.0, 3.2), (7.0, -3.2), (12.0, 3.2))]
    flame = mat("flamme", (1, 0.45, 0.12), emit=30)
    for tp in torch_pts:
        cyl(tp, tp + [0, 0, 2.4], 0.04, rope)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=tuple(tp + [0, 0, 2.55]))
        bpy.context.active_object.data.materials.append(flame)
        bpy.ops.object.light_add(type="POINT", location=tuple(tp + [0, 0, 2.6]))
        l = bpy.context.active_object
        l.data.color, l.data.energy, l.data.shadow_soft_size = (1, 0.5, 0.18), 2500, 0.2
    bpy.ops.mesh.primitive_uv_sphere_add(radius=40, location=(-900, 1600, 700))
    bpy.context.active_object.data.materials.append(mat("lune", (0.9, 0.93, 1), emit=6))
    # lumière de lune
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 100))
    sun = bpy.context.active_object
    sun.rotation_euler = (math.radians(55), 0, math.radians(200))
    sun.data.color, sun.data.energy = (0.55, 0.65, 1.0), 2.5
    # caméra basse derrière le bloc, qui regarde l'équipe et la pyramide
    from mathutils import Vector
    cam_pos = SLED + D3 * 0.6 + L3 * 1.9 + [0, 0, 0.45]
    tgt = SLED + D3 * 30.0 + [0, 0, 9.0]
    cd = bpy.data.cameras.new("cam")
    cd.lens, cd.sensor_fit, cd.sensor_width = 22, "VERTICAL", 36
    cd.clip_end = 5000
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    cam.location = tuple(cam_pos)
    cam.rotation_euler = Vector(tgt - cam_pos).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 50
    sc.view_settings.view_transform = "AgX"
    # réglages propres à chaque style
    sun.rotation_euler = (math.radians(55), 0, math.radians(200))
    if style == "silhouette":
        world_gradient((0.015, 0.02, 0.07), (1.0, 0.42, 0.12), 1.4)
        for o in bpy.data.objects:
            if o.type == "LIGHT":
                o.data.energy = 0
        sc.view_settings.look = "AgX - High Contrast"
    elif style == "traits":
        world_gradient((0.0, 0.0, 0.004), (0.004, 0.008, 0.03), 1.0)
        for o in bpy.data.objects:
            if o.type == "LIGHT" and o.data.type == "SUN":
                o.data.energy = 0.3
        freestyle((0.25, 0.65, 1.0), 2.0)
    elif style in ("surfaces", "voxels"):
        world_gradient((0.05, 0.08, 0.2), (1.0, 0.55, 0.3), 1.2)
        sun.rotation_euler = (math.radians(80), 0, math.radians(110))     # soleil rasant de fin de journée
        sun.data.color, sun.data.energy = (1.0, 0.72, 0.45), 4.5
        sun.data.angle = math.radians(2)
        sc.view_settings.look = "AgX - Medium High Contrast"
    elif style == "gravure":
        world_gradient((0.93, 0.86, 0.72), (0.93, 0.86, 0.72), 1.0)
        for o in bpy.data.objects:
            if o.type == "LIGHT":
                o.data.energy = 0
        sc.view_settings.view_transform = "Standard"
        freestyle((0.1, 0.06, 0.03), 2.2)
    sc.render.filepath = os.path.join(OUT, f"style_{style}.png")
    bpy.ops.render.render(write_still=True)


def freestyle(color, thickness):
    sc = bpy.context.scene
    sc.render.use_freestyle = True
    vl = sc.view_layers[0]
    ls = vl.freestyle_settings.linesets[0] if vl.freestyle_settings.linesets else vl.freestyle_settings.linesets.new("l")
    ls.select_by_visibility, ls.select_by_edge_types = True, True
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("trait")
    ls.linestyle.color = color
    ls.linestyle.thickness = thickness


def vox(V, Fc, m, size):
    """Voxelise un maillage (échantillonnage de surface → grille) en cubes instanciés."""
    V = np.asarray(V, float)
    tris = []
    for f in Fc:
        for k in range(1, len(f) - 1):
            tris.append((f[0], f[k], f[k + 1]))
    T = np.array(tris)
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    area = np.linalg.norm(np.cross(B - A, C - A), axis=1) / 2
    n = int(min(400000, area.sum() / (size * size) * 6)) + 100
    g = np.random.default_rng(0)
    t = g.choice(len(T), n, p=area / area.sum())
    r1, r2 = np.sqrt(g.random(n)), g.random(n)
    P = A[t] * (1 - r1)[:, None] + B[t] * (r1 * (1 - r2))[:, None] + C[t] * (r1 * r2)[:, None]
    cells = np.unique(np.floor(P / size).astype(np.int64), axis=0)
    cub = np.array([(x, y, z) for z in (0, 1) for y in (0, 1) for x in (0, 1)], float)
    cf = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    Vv = (cells[:, None, :] + cub[None] * 0.94 + 0.03) * size
    Vv = Vv.reshape(-1, 3)
    Ff = [tuple(i * 8 + c for c in f) for i in range(len(cells)) for f in cf]
    new_mesh("vox", Vv, Ff, m)


for s in STYLES:
    build(s)
    print("STYLE", s)
