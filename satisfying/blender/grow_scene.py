"""Scène Blender (Cycles) de « la balle qui grossit » : anneau de verre, bille laquée, ciel étoilé, sol miroir.

Lancé par satisfying.render3d, soit avec le Blender officiel :
    blender -b --factory-startup -P grow_scene.py -- params.json
soit avec le module Python bpy : python grow_scene.py params.json
Ne dépend que de bpy et numpy (fournis avec Blender).
"""
import json
import math
import sys
import time

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
P = json.load(open(argv[0], encoding="utf-8"))
tracks = np.load(P["tracks"])
X, Z, RAD, COL = tracks["x"], tracks["z"], tracks["r"], tracks["color"]
N = len(X)
RING = P["ring_radius"]


def lin(rgb):
    return tuple((c / 255) ** 2.2 for c in rgb)


# ---------------------------------------------------------------- réglages du rendu
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.render.resolution_x, sc.render.resolution_y = P["width"], P["height"]
sc.render.fps = P["fps"]
sc.frame_start, sc.frame_end = 1, N
sc.cycles.samples = P["samples"]
sc.cycles.use_denoising = True
sc.cycles.use_adaptive_sampling = True
sc.cycles.max_bounces = 8
sc.cycles.transmission_bounces = 8
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.render.filepath = P["frames_dir"] + "/f_"


def use_gpu():
    want = P.get("device", "auto")
    if want == "cpu":
        return "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
            try:
                prefs.compute_device_type = kind
            except TypeError:
                continue
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type == kind]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == kind
                sc.cycles.device = "GPU"
                if kind == "OPTIX":
                    sc.cycles.denoiser = "OPTIX"
                return f"GPU {kind} ({', '.join(d.name for d in gpus)})"
    except Exception as e:  # pas de GPU utilisable
        print("GPU indisponible :", e)
    return "CPU"


print("Rendu sur", use_gpu(), flush=True)


# ---------------------------------------------------------------- matières
def principled(name, base, rough=0.2, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.05
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m, b


# ciel : noir profond, étoiles (Voronoi) et voile de nébuleuse très léger
world = bpy.data.worlds.new("ciel")
sc.world = world
world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn["Background"]
coord = wn.new("ShaderNodeTexCoord")
vor = wn.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 110.0
vor.inputs["Randomness"].default_value = 1.0
vor.feature = "F1"
stars = wn.new("ShaderNodeMapRange")
stars.inputs["From Min"].default_value = 0.045
stars.inputs["From Max"].default_value = 0.0
stars.inputs["To Min"].default_value = 0.0
stars.inputs["To Max"].default_value = 40.0
bright = wn.new("ShaderNodeTexNoise")          # étoiles d'éclats différents
bright.inputs["Scale"].default_value = 60.0
bright.inputs["Detail"].default_value = 0.0
mul = wn.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
nebula = wn.new("ShaderNodeTexNoise")
nebula.inputs["Scale"].default_value = 1.4
nebula.inputs["Detail"].default_value = 6.0
ramp = wn.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.5
ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
ramp.color_ramp.elements[1].position = 0.85
ramp.color_ramp.elements[1].color = (*[c * 0.06 for c in lin(P["nebula"])], 1)
add = wn.new("ShaderNodeMix")
add.data_type = "RGBA"
add.blend_type = "ADD"
add.inputs["Factor"].default_value = 1.0
wl.new(coord.outputs["Generated"], vor.inputs["Vector"])
wl.new(coord.outputs["Generated"], bright.inputs["Vector"])
wl.new(coord.outputs["Generated"], nebula.inputs["Vector"])
wl.new(vor.outputs["Distance"], stars.inputs["Value"])
wl.new(stars.outputs["Result"], mul.inputs[0])
wl.new(bright.outputs["Fac"], mul.inputs[1])
wl.new(nebula.outputs["Fac"], ramp.inputs["Fac"])
wl.new(ramp.outputs["Color"], add.inputs["A"])
wl.new(mul.outputs["Value"], add.inputs["B"])
wl.new(add.outputs["Result"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

accent = lin(P["accent"])
# anneau de verre, cœur lumineux constant (jamais de clignotement)
bpy.ops.mesh.primitive_torus_add(major_radius=RING + 0.11, minor_radius=0.11, major_segments=220,
                                 minor_segments=32, rotation=(math.pi / 2, 0, 0))
bpy.ops.object.shade_smooth()
glass, _ = principled("verre", (1, 1, 1), rough=0.03, trans=1.0, ior=1.5)
bpy.context.object.data.materials.append(glass)
bpy.ops.mesh.primitive_torus_add(major_radius=RING + 0.11, minor_radius=0.014, major_segments=220,
                                 minor_segments=12, rotation=(math.pi / 2, 0, 0))
bpy.ops.object.shade_smooth()
neon, _ = principled("néon", accent, emit=accent, strength=P["neon_strength"])
bpy.context.object.data.materials.append(neon)

# sol miroir sombre
bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, -RING - 0.75))
floor_obj = bpy.context.object
floor, _ = principled("sol", (0.0, 0.0, 0.0), rough=0.1)
bpy.context.object.data.materials.append(floor)

# bille laquée : couleur animée
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=96, ring_count=48)
bpy.ops.object.shade_smooth()
ball = bpy.context.object
ball_mat, ball_bsdf = principled("bille", lin(COL[0]), rough=0.16, coat=1.0, emit=lin(COL[0]), strength=0.15)
ball.data.materials.append(ball_mat)

# les lampes n'éclairent que l'anneau et la bille : aucun reflet de lampe dans le sol miroir
lit = bpy.data.collections.new("éclairés")
for ob in bpy.data.objects:
    if ob is not floor_obj and ob.type == "MESH":
        lit.objects.link(ob)


# lumières : grande clé douce, contre-jour teinté, rappel
def area(loc, rot, energy, size, col=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    lamp = bpy.context.object
    lamp.data.energy, lamp.data.size, lamp.data.color = energy, size, col
    lamp.rotation_euler = rot
    try:
        lamp.light_linking.receiver_collection = lit
    except AttributeError:
        pass
    return lamp


area((3.2, -8, 8.5), (math.radians(42), 0, math.radians(22)), 2600, 6)   # assez haut : hors du reflet du sol
area((-3.5, 4, 2.5), (math.radians(-115), 0, math.radians(-40)), 700, 4, tuple(0.4 + 0.6 * c for c in accent))

# caméra : léger mouvement circulaire lent, qui boucle
bpy.ops.object.empty_add(location=(0, 0, 0))
target = bpy.context.object
bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.sensor_fit = "HORIZONTAL"
cam.data.sensor_width = 36
cam.data.lens = 50
cam.data.dof.use_dof = True
cam.data.dof.focus_object = target
cam.data.dof.aperture_fstop = 3.2
track = cam.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
sc.camera = cam
dist, height, swing = P["cam_distance"], P["cam_height"], math.radians(P["cam_swing_deg"])

# ---------------------------------------------------------------- animation (une clé par image)
for i in range(N):
    f = i + 1
    ball.location = (float(X[i]), 0.0, float(Z[i]))
    ball.scale = (float(RAD[i]),) * 3
    ball.keyframe_insert("location", frame=f)
    ball.keyframe_insert("scale", frame=f)
    c = lin(COL[i])
    ball_bsdf.inputs["Base Color"].default_value = (*c, 1)
    ball_bsdf.inputs["Emission Color"].default_value = (*c, 1)
    ball_bsdf.inputs["Base Color"].keyframe_insert("default_value", frame=f)
    ball_bsdf.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
    a = swing * math.sin(2 * math.pi * i / N)
    cam.location = (dist * math.sin(a), -dist * math.cos(a), height)
    cam.keyframe_insert("location", frame=f)

if P.get("still"):
    sc.frame_set(P["still"])
    sc.render.filepath = P["frames_dir"] + "/still.png"
    bpy.ops.render.render(write_still=True)
else:
    t0 = time.time()
    bpy.ops.render.render(animation=True)
    print(f"{N} images en {time.time() - t0:.0f} s", flush=True)
