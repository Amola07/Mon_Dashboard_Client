"""Plan pilote de « Goutte » (Blender Cycles).

    blender -b --factory-startup -P pilote.py -- params.json
    python pilote.py params.json          (module bpy)

params.json : {"out": dossier des images, "scale": 0.5, "samples": 64, "device": "auto",
               "frames": [début, fin] (facultatif), "still": n° d'image (facultatif)}
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline as T  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
P = json.load(open(argv[0], encoding="utf-8"))
random.seed(3)
F = T.f


def lin(r, g, b):
    return ((r / 255) ** 2.2, (g / 255) ** 2.2, (b / 255) ** 2.2)


# ---------------------------------------------------------------- rendu
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.render.resolution_x = int(1080 * P.get("scale", 0.5)) // 2 * 2
sc.render.resolution_y = int(1920 * P.get("scale", 0.5)) // 2 * 2
sc.render.fps = T.FPS
sc.frame_start, sc.frame_end = 1, F(T.DURATION) - 1
if P.get("frames"):
    sc.frame_start, sc.frame_end = P["frames"]
sc.cycles.samples = P.get("samples", 64)
sc.cycles.use_denoising = True
sc.cycles.use_adaptive_sampling = True
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(P["out"], "f_")


def use_gpu():
    if P.get("device") == "cpu":
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
                return f"GPU {kind}"
    except Exception as e:
        print("GPU indisponible :", e)
    return "CPU"


print("Rendu sur", use_gpu(), flush=True)


# ---------------------------------------------------------------- outils
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def key(obj, path, frame, value, interp="BEZIER", easing="AUTO"):
    setattr(obj, path, value)
    obj.keyframe_insert(path, frame=frame)
    _set_interp(obj.animation_data, frame, interp, easing)


def _set_interp(ad, frame, interp, easing):
    if not ad or not ad.action:
        return
    curves = []
    try:
        curves = list(ad.action.fcurves)
    except AttributeError:  # Blender 5 : actions en couches
        for layer in ad.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves.extend(bag.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            if int(round(kp.co.x)) == frame:
                kp.interpolation = interp
                kp.easing = easing


def socket_key(sock, frame, value):
    sock.default_value = value
    sock.keyframe_insert("default_value", frame=frame)


# ---------------------------------------------------------------- ciel : lever du soleil + étoiles qui s'effacent
world = bpy.data.worlds.new("ciel")
sc.world = world
world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
sky = wn.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING"
sky.sun_rotation = 0.0                      # soleil vers +Y : devant la caméra
coord = wn.new("ShaderNodeTexCoord")
vor = wn.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 120
mr = wn.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = 0.04
mr.inputs["From Max"].default_value = 0.0
mr.inputs["To Max"].default_value = 30.0
star_amt = wn.new("ShaderNodeMath")
star_amt.operation = "MULTIPLY"
night = wn.new("ShaderNodeMix")
night.data_type = "RGBA"
night.blend_type = "ADD"
night.inputs["Factor"].default_value = 1.0
sky_gain = wn.new("ShaderNodeMix")          # le ciel s'éclaircit progressivement
sky_gain.data_type = "RGBA"
sky_gain.blend_type = "MULTIPLY"
sky_gain.inputs["Factor"].default_value = 1.0
wl.new(coord.outputs["Generated"], vor.inputs["Vector"])
wl.new(vor.outputs["Distance"], mr.inputs["Value"])
wl.new(mr.outputs["Result"], star_amt.inputs[0])
wl.new(sky.outputs["Color"], sky_gain.inputs["A"])
wl.new(sky_gain.outputs["Result"], night.inputs["A"])
wl.new(star_amt.outputs["Value"], night.inputs["B"])
wl.new(night.outputs["Result"], wn["Background"].inputs["Color"])
wn["Background"].inputs["Strength"].default_value = 0.6

for t, el, stars, gain in [(0, -3.5, 1.0, 0.25), (5, -2.5, 0.7, 0.45), (T.SUNRISE[0], -2.0, 0.5, 0.6),
                           (T.SUNRISE[1], 5.0, 0.0, 1.0)]:
    sky.sun_elevation = math.radians(el)
    sky.keyframe_insert("sun_elevation", frame=F(t))
    socket_key(star_amt.inputs[1], F(t), stars)
    socket_key(sky_gain.inputs["B"], F(t), (gain, gain, gain, 1))

# soleil : direction réglée par une contrainte vers le centre
bpy.ops.object.empty_add(location=(0, 0, 0))
origin = bpy.context.object
bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.angle = math.radians(1.5)
sun.data.color = lin(255, 196, 150)
c = sun.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = origin, "TRACK_NEGATIVE_Z", "UP_Y"
for t, el, energy in [(0, -3.5, 0.0), (T.SUNRISE[0], -1.0, 0.3), (T.SUNRISE[1], 5.0, 4.5)]:
    e = math.radians(el)
    sun.location = (0, 60 * math.cos(e), 60 * math.sin(e))
    sun.keyframe_insert("location", frame=F(t))
    sun.data.energy = energy
    sun.data.keyframe_insert("energy", frame=F(t))
# lumière d'aube froide et douce
bpy.ops.object.light_add(type="AREA", location=(-3, -5, 4))
dawn = bpy.context.object
dawn.data.size, dawn.data.color = 8, lin(150, 170, 255)
dawn.rotation_euler = (math.radians(50), 0, math.radians(-30))
for t, e in [(0, 120), (T.SUNRISE[1], 40)]:
    dawn.data.energy = e
    dawn.data.keyframe_insert("energy", frame=F(t))

# ---------------------------------------------------------------- dunes
sand = bpy.data.materials.new("sable")
sand.use_nodes = True
sn, sl = sand.node_tree.nodes, sand.node_tree.links
bsdf = sn["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (*lin(214, 156, 102), 1)
bsdf.inputs["Roughness"].default_value = 0.92
wave = sn.new("ShaderNodeTexWave")              # rides du vent
wave.inputs["Scale"].default_value = 9.0
wave.inputs["Distortion"].default_value = 6.0
wave.inputs["Detail"].default_value = 3.0
grain = sn.new("ShaderNodeTexNoise")             # grains
grain.inputs["Scale"].default_value = 900.0
mixb = sn.new("ShaderNodeMath")
mixb.operation = "ADD"
bump = sn.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.25
sl.new(wave.outputs["Fac"], mixb.inputs[0])
sl.new(grain.outputs["Fac"], mixb.inputs[1])
sl.new(mixb.outputs["Value"], bump.inputs["Height"])
sl.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

bpy.ops.mesh.primitive_plane_add(size=260, location=(0, 60, -2.2))
dunes = bpy.context.object
m = dunes.modifiers.new("sub", "SUBSURF")
m.subdivision_type, m.levels, m.render_levels = "SIMPLE", 8, 8
tex = bpy.data.textures.new("dunes", "CLOUDS")
tex.noise_scale = 7.0
d = dunes.modifiers.new("disp", "DISPLACE")
d.texture, d.strength = tex, 3.2
dunes.data.materials.append(sand)
bpy.ops.object.shade_smooth()
# la crête où la goutte atterrit : sommet exactement en z = 0
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=128, ring_count=64, location=(0, 0, -1.4))
crest = bpy.context.object
crest.scale = (9.0, 7.0, 1.4)
crest.data.materials.append(sand)
bpy.ops.object.shade_smooth()

# ---------------------------------------------------------------- la goutte
water = mat("eau", lin(215, 235, 255), rough=0.0, trans=1.0, ior=1.33)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=128, ring_count=64)
drop = bpy.context.object
for v in drop.data.vertices:
    z = v.co.z
    if z > 0:
        u = z / 0.5
        k = 1 - 0.55 * u ** 1.8
        v.co.x *= k
        v.co.y *= k
        v.co.z *= 1.0 + 0.5 * u
    v.co.z += 0.5                                  # origine sous la goutte : l'écrasement part du sol
drop.data.materials.append(water)
bpy.ops.object.shade_smooth()
black = mat("pupille", (0.005, 0.005, 0.008), rough=0.15, coat=1.0)
spark = mat("reflet", (1, 1, 1), emit=(1, 1, 1), strength=6)
eyes = []
for side in (-1, 1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055, segments=32, ring_count=16, location=(side * 0.14, -0.43, 0.6))
    e = bpy.context.object
    e.data.materials.append(black)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, segments=12, ring_count=6,
                                         location=(side * 0.14 - 0.018, -0.478, 0.625))
    s = bpy.context.object
    s.data.materials.append(spark)
    s.parent = e
    s.matrix_parent_inverse = e.matrix_world.inverted()
    e.parent = drop
    eyes.append(e)

LAND_Z = 0.0
# chute : très haut dans le ciel → contact (accélération), puis écrasement et rebond
key(drop, "location", F(0), (0.0, 0.0, 30.0), "CONSTANT")
key(drop, "location", F(T.FALL_START), (0.0, 0.0, 30.0), "QUAD", "EASE_IN")
key(drop, "location", F(T.LAND), (0.0, 0.0, LAND_Z), "BEZIER")
for dt, s in [(0, (1, 1, 1)), (0.08, (1.32, 1.32, 0.62)), (0.3, (0.9, 0.9, 1.14)), (0.5, (1.04, 1.04, 0.96)),
              (0.7, (1, 1, 1))]:
    key(drop, "scale", F(T.LAND + dt), s)
key(drop, "scale", F(T.LAND - 0.4), (0.8, 0.8, 1.35))   # étirée pendant la chute
key(drop, "scale", F(T.FALL_START), (0.8, 0.8, 1.35))
# yeux fermés pendant la chute, ouverture lente, regards, clignement, plissement au soleil
closed, opened, squint = (1, 1, 0.08), (1, 1, 1), (1.05, 1, 0.45)
for e in eyes:
    key(e, "scale", F(0), closed)
    key(e, "scale", F(T.EYES_OPEN[0]), closed)
    key(e, "scale", F(T.EYES_OPEN[1]), opened)
    key(e, "scale", F(T.BLINK[0]), opened)
    key(e, "scale", F((T.BLINK[0] + T.BLINK[1]) / 2), closed)
    key(e, "scale", F(T.BLINK[1]), opened)
    key(e, "scale", F(T.SQUINT[0]), opened)
    key(e, "scale", F(T.SQUINT[1]), squint)
    base = e.location.copy()
    for (t0, t1), dx in [(T.LOOK_LEFT, -0.045), (T.LOOK_RIGHT, 0.045), (T.LOOK_BACK, 0.0)]:
        key(e, "location", F(t0), e.location.copy())
        key(e, "location", F(t1), (base.x + dx, base.y, base.z))
for (t0, t1), rz in [(T.LOOK_LEFT, 0.18), (T.LOOK_RIGHT, -0.18), (T.LOOK_BACK, 0.0)]:
    key(drop, "rotation_euler", F(t0), drop.rotation_euler.copy())
    key(drop, "rotation_euler", F(t1), (0, 0, rz))

# grains de sable soulevés à l'impact
grain_m = mat("grain", lin(214, 160, 110), rough=0.9)
for k in range(26):
    a = random.uniform(0, 2 * math.pi)
    dist, hgt = random.uniform(0.35, 0.9), random.uniform(0.15, 0.45)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=random.uniform(0.008, 0.02), subdivisions=1, location=(0, 0, -0.05))
    g = bpy.context.object
    g.data.materials.append(grain_m)
    key(g, "location", F(T.LAND), (0.1 * math.cos(a), 0.1 * math.sin(a), -0.05), "LINEAR")
    key(g, "location", F(T.LAND + 0.25), (dist * 0.6 * math.cos(a), dist * 0.6 * math.sin(a), hgt), "QUAD", "EASE_IN")
    key(g, "location", F(T.LAND + 0.6), (dist * math.cos(a), dist * math.sin(a), -0.06))

# ---------------------------------------------------------------- caméras et coupes
target = {}


def camera(name, lens, fstop, keys):
    """keys : [(t, position, point visé)]"""
    bpy.ops.object.empty_add()
    tgt = bpy.context.object
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = name
    cam.data.lens = lens
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_object = drop
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    for t, loc, look in keys:
        key(cam, "location", F(t), loc)
        key(tgt, "location", F(t), look)
    return cam


cams = {
    "large": camera("large", 28, 8.0, [(0, (0.6, -16, 1.2), (0, 20, 9)), (4.6, (0.4, -13.5, 1.0), (0, 10, 1.6))]),
    "proche": camera("proche", 40, 2.0, [(5, (0.3, -4.4, 0.75), (0, 0, 0.9)), (9, (0.25, -4.0, 0.7), (0, 0, 0.6))]),
    "visage": camera("visage", 50, 2.2, [(9, (0.15, -3.3, 0.7), (0, 0, 0.62)), (14, (0.05, -3.0, 0.68), (0, 0, 0.6))]),
    "contre": camera("contre", 30, 2.0, [(14, (-0.55, -2.9, 0.14), (0, 0.5, 0.75)), (18, (-0.35, -2.5, 0.16), (0, 0.5, 0.8))]),
}
for t, name in T.SHOTS:
    mk = sc.timeline_markers.new(name, frame=F(t))
    mk.camera = cams[name]
sc.camera = cams["large"]

if P.get("still"):
    sc.frame_set(P["still"])
    for t, name in reversed(T.SHOTS):
        if P["still"] >= F(t):
            sc.camera = cams[name]
            break
    sc.render.filepath = os.path.join(P["out"], "still.png")
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
