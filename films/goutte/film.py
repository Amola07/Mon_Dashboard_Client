"""Film complet « Goutte » (2 min) dans Blender Cycles.

    blender -b --factory-startup -P film.py -- params.json
    python film.py params.json            (module bpy)

params.json : {"out": dossier, "scale": 0.5, "samples": 96, "device": "auto",
               "frames": [début, fin] (facultatif), "step": 1, "still": n° (facultatif), "grains": true}
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assets as A  # noqa: E402
import film_timeline as T  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
P = json.load(open(argv[0], encoding="utf-8"))
F = T.f
N = F(T.DURATION) - 1
KEY_STEP = 2                     # une clé toutes les 2 images pour les mouvements calculés

# ---------------------------------------------------------------- rendu
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.render.resolution_x = int(1080 * P.get("scale", 0.5)) // 2 * 2
sc.render.resolution_y = int(1920 * P.get("scale", 0.5)) // 2 * 2
sc.render.fps = T.FPS
sc.frame_start, sc.frame_end = 1, N
if P.get("frames"):
    sc.frame_start, sc.frame_end = P["frames"]
sc.frame_step = P.get("step", 1)
sc.cycles.samples = P.get("samples", 96)
sc.cycles.use_denoising = True
sc.cycles.use_adaptive_sampling = True
sc.cycles.max_bounces = 8
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"
sc.view_settings.exposure = -0.4
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(P["out"], "f_")
sc.render.use_overwrite = False       # reprise possible après une interruption
sc.render.use_placeholder = True


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


def set_interp(obj_or_id, interp="LINEAR"):
    ad = obj_or_id.animation_data
    if not ad or not ad.action:
        return
    try:
        curves = list(ad.action.fcurves)
    except AttributeError:
        curves = [fc for layer in ad.action.layers for strip in layer.strips for bag in strip.channelbags
                  for fc in bag.fcurves]
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = interp


def key_track(obj, path, keys, index=None):
    """keys : [(t, valeur)] ; interpolation adoucie (Bézier)."""
    for t, v in keys:
        setattr(obj, path, v)
        obj.keyframe_insert(path, frame=F(t))


def sock_key(sock, t, v):
    sock.default_value = v
    sock.keyframe_insert("default_value", frame=F(t))


# ---------------------------------------------------------------- ciel animé (nuit → aube → midi → pluie → soir)
world = bpy.data.worlds.new("ciel")
sc.world = world
world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
sky = wn.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING"
coord = wn.new("ShaderNodeTexCoord")
vor = wn.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 120
mr = wn.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = 0.04
mr.inputs["From Max"].default_value = 0.0
mr.inputs["To Max"].default_value = 30.0
star_amt = wn.new("ShaderNodeMath")
star_amt.operation = "MULTIPLY"
gain = wn.new("ShaderNodeMix")
gain.data_type, gain.blend_type = "RGBA", "MULTIPLY"
gain.inputs["Factor"].default_value = 1.0
grey = wn.new("ShaderNodeMix")                      # ciel couvert pendant la pluie
grey.data_type = "RGBA"
grey.inputs["B"].default_value = (0.16, 0.18, 0.22, 1)
add = wn.new("ShaderNodeMix")
add.data_type, add.blend_type = "RGBA", "ADD"
add.inputs["Factor"].default_value = 1.0
wl.new(coord.outputs["Generated"], vor.inputs["Vector"])
wl.new(vor.outputs["Distance"], mr.inputs["Value"])
wl.new(mr.outputs["Result"], star_amt.inputs[0])
wl.new(sky.outputs["Color"], gain.inputs["A"])
wl.new(gain.outputs["Result"], grey.inputs["A"])
wl.new(grey.outputs["Result"], add.inputs["A"])
wl.new(star_amt.outputs["Value"], add.inputs["B"])
wl.new(add.outputs["Result"], wn["Background"].inputs["Color"])
wn["Background"].inputs["Strength"].default_value = 0.55

bpy.ops.object.empty_add(location=(0, 0, 0))
origin = bpy.context.object
bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.angle = math.radians(1.2)
c = sun.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = origin, "TRACK_NEGATIVE_Z", "UP_Y"
for t, el, rot, energy, stars, g in T.SKY:
    sky.sun_elevation, sky.sun_rotation = math.radians(el), math.radians(rot)
    sky.keyframe_insert("sun_elevation", frame=F(t))
    sky.keyframe_insert("sun_rotation", frame=F(t))
    sock_key(star_amt.inputs[1], t, stars)
    sock_key(gain.inputs["B"], t, (g, g, g, 1))
    sock_key(grey.inputs["Factor"], t, 0.75 if g < 0.5 else 0.0)
    e, r = math.radians(el), math.radians(rot)
    sun.location = (60 * math.sin(r) * math.cos(e), 60 * math.cos(r) * math.cos(e), 60 * math.sin(e))
    sun.keyframe_insert("location", frame=F(t))
    warm = min(1.0, max(0.0, (20 - el) / 20))           # soleil bas = lumière dorée
    sun.data.color = (1.0, 0.93 - 0.2 * warm, 0.85 - 0.35 * warm)
    sun.data.energy = energy
    sun.data.keyframe_insert("color", frame=F(t))
    sun.data.keyframe_insert("energy", frame=F(t))
bpy.ops.object.light_add(type="AREA", location=(-3, -6, 4))       # lumière d'ambiance froide
fill = bpy.context.object
fill.data.size, fill.data.color, fill.data.energy = 10, A.lin(170, 195, 255), 80
fill.rotation_euler = (math.radians(55), 0, math.radians(-25))

# ---------------------------------------------------------------- terrain
sand = A.sand_material()
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 60, -3.0))
dunes = bpy.context.object
m = dunes.modifiers.new("sub", "SUBSURF")
m.subdivision_type, m.levels, m.render_levels = "SIMPLE", 8, 8
tex = bpy.data.textures.new("dunes", "CLOUDS")
tex.noise_scale = 7.0
d = dunes.modifiers.new("disp", "DISPLACE")
d.texture, d.strength = tex, 2.0
dunes.data.materials.append(sand)
A.smooth(dunes)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=160, ring_count=80, location=(0, 0, -T.CREST[2]))
crest = A.smooth(bpy.context.object)
crest.scale = T.CREST
crest.data.materials.append(sand)
if P.get("grains", True):
    A.sand_grains(A.ground_patch(T.ground, center=(1.3, -0.8), radius=3.6, res=110), count=150000, size=0.018, seed=1)
    A.sand_grains(A.ground_patch(T.ground, center=(3.6, -0.6), radius=2.2, res=80), count=70000, size=0.018, seed=2)

# ---------------------------------------------------------------- la goutte
water = A.water_material()
D = A.drop(water=water)
body = D["body"]
A.hand_visor(D)
D["hand"].scale = (0, 0, 0)
for fr in range(1, N + 1, KEY_STEP):
    t = (fr - 1) / T.FPS
    loc, scl, rz = T.drop_state(t)
    body.location, body.scale, body.rotation_euler = loc, scl, (0, 0, rz)
    body.keyframe_insert("location", frame=fr)
    body.keyframe_insert("scale", frame=fr)
    body.keyframe_insert("rotation_euler", frame=fr)
set_interp(body)
for lid in D["lids"]:
    key_track(lid, "rotation_euler", [(t, (math.radians(a), 0, 0)) for t, a in T.LIDS])
left = D["lids"][0]
for t, a in T.WINK:
    left.rotation_euler = (math.radians(a), 0, 0)
    left.keyframe_insert("rotation_euler", frame=F(t))
for t, o, s in T.MOUTH:
    D["ooh"].scale = (o, o, o)
    D["ooh"].keyframe_insert("scale", frame=F(t))
    D["smile"].scale = (abs(s), 1.0, s) if s else (0, 0, 0)
    D["smile"].keyframe_insert("scale", frame=F(t))
for e in D["eyes"]:
    base = e.location.copy()
    for t, (dx, dz, _) in T.LOOKS:
        e.location = (base.x + dx, base.y, base.z + dz)
        e.keyframe_insert("location", frame=F(t))
for t, h in T.HAND:
    D["hand"].scale = (h, h, h)
    D["hand"].keyframe_insert("scale", frame=F(t))

bpy.ops.object.light_add(type="POINT")
fall_light = bpy.context.object
fall_light.data.color, fall_light.data.shadow_soft_size = A.lin(190, 215, 255), 0.6
for fr in range(1, F(T.LAND + 0.8), KEY_STEP):
    t = (fr - 1) / T.FPS
    (x, y, z), _, _ = T.drop_state(t)
    fall_light.location = (x - 1.2, y - 1.8, z + 1.3)
    fall_light.data.energy = 90 * (1 - T.smooth((t - T.LAND + 0.5) / 1.2))
    fall_light.keyframe_insert("location", frame=fr)
    fall_light.data.keyframe_insert("energy", frame=fr)

# vapeur au-dessus de la tête, puis la volute brillante qui monte au ciel
for i, (t0, t1) in enumerate(T.WISPS):
    w = A.wisp(height=0.6, seed=i, turns=1.1)
    w.parent = body
    w.location = (0.04, 0.0, 1.05)
    for t, s in [(0, 0), (t0, 0), (t0 + 0.6, 1), (t1 - 0.6, 1), (t1, 0)]:
        w.scale = (s, s, s)
        w.keyframe_insert("scale", frame=F(t))
    w.keyframe_insert("location", frame=F(t0))
    w.location = (0.1, 0.05, 1.35)
    w.keyframe_insert("location", frame=F(t1))
soul = A.wisp(height=0.9, glow=3.0, seed=9, turns=1.6, width=0.04)
for fr in range(F(T.SOUL[0] - 0.5), F(T.SOUL[1] + 1.2), KEY_STEP):
    t = (fr - 1) / T.FPS
    s = T.smooth((t - T.SOUL[0]) / 1.0) * (1 - T.smooth((t - T.SOUL[1]) / 0.8)) * 1.3
    soul.location, soul.scale = T.soul_pos(t), (s, s, s)
    soul.keyframe_insert("location", frame=fr)
    soul.keyframe_insert("scale", frame=fr)
soul.scale = (0, 0, 0)
soul.keyframe_insert("scale", frame=1)

# ---------------------------------------------------------------- caillou (bascule quand la goutte s'y abrite)
rock = A.rock(location=(T.ROCK[0], T.ROCK[1], T.ground(*T.ROCK) + 0.18), size=1.3)
rest = rock.location.copy()
for t, dx, dy, rx in [(0, 0, 0, 0), (55.2, 0, 0, 0), (55.6, -0.12, -0.08, -0.25), (56.0, -0.22, -0.14, -0.4),
                      (56.5, -0.18, -0.1, -0.33)]:
    rock.location = (rest.x + dx, rest.y + dy, rest.z)
    rock.rotation_euler = (rx, 0, rx * 0.5)
    rock.keyframe_insert("location", frame=F(t))
    rock.keyframe_insert("rotation_euler", frame=F(t))

# ---------------------------------------------------------------- la pousse (se redresse) et la grande fleur
S = (T.SPROUT[0], T.SPROUT[1], T.ground(*T.SPROUT))
H = A.sprout(location=S, alive=0.0, size=1.1)
bpy.data.objects.remove(H["stem"])
stem_c = bpy.data.curves.new("tige animée", "CURVE")
stem_c.dimensions = "3D"
stem_c.bevel_depth = 0.018
stem_c.bevel_resolution = 4
spl = stem_c.splines.new("POLY")
NP = 10
spl.points.add(NP - 1)
stem = bpy.data.objects.new("tige animée", stem_c)
bpy.context.collection.objects.link(stem)
stem.location = S
stem.data.materials.append(H["stem_mat"])


def stem_points(alive, size=1.1):
    bend = (1 - alive) * 0.9
    pts = []
    for i in range(NP):
        u = i / (NP - 1)
        h = 0.62 * u
        x = 0.28 * bend * max(0.0, (u - 0.45) / 0.55) ** 1.6
        z = h - 0.35 * bend * max(0.0, (u - 0.6) / 0.4) ** 2
        pts.append((x * size, 0.0, z * size))
    return pts


for t, a in T.SPROUT_ALIVE:
    for p, co in zip(spl.points, stem_points(a)):
        p.co = (*co, 1.0)
        p.keyframe_insert("co", frame=F(t))
    droop = math.radians(50 * (1 - a) - 25 * a)
    for lf in H["leaves"]:
        lf.rotation_euler = (0, droop, lf.rotation_euler.z)
        lf.keyframe_insert("rotation_euler", frame=F(t))
    green = A.lin(*[int(p + (q - p) * a) for p, q in zip((128, 112, 62), (95, 190, 90))])
    for m_ in (H["stem_mat"], H["leaf_mat"]):
        sock_key(m_.node_tree.nodes["Principled BSDF"].inputs["Base Color"], t, (*green, 1))

big = A.glass_flower(location=S, size=2.2, petals=8, seed=99)
for t, s in [(0, 0), (T.BIG_FLOWER[0], 0), (T.BIG_FLOWER[1], 1)]:
    big.scale = (s, s, s)
    big.keyframe_insert("scale", frame=F(t))

# ---------------------------------------------------------------- nuage, volutes qui montent, pluie, champ de fleurs
cl = A.cloud(location=T.CLOUD, size=2.3, frown=0.0)
full = cl.scale.copy()
for t, g in T.CLOUD_GROW:
    cl.scale = tuple(v * max(g, 0.001) for v in full)
    cl.keyframe_insert("scale", frame=F(t))
for bname in cl["brows"]:
    b = bpy.data.objects[bname]
    for t, fr_ in T.CLOUD_FROWN:
        b.scale = (fr_, fr_, fr_)
        b.keyframe_insert("scale", frame=F(t))
for i, ((x, y), t0) in enumerate(T.CLOUD_WISPS):
    w = A.wisp(height=0.9, glow=1.5, seed=20 + i, turns=1.4, width=0.04)
    for t, z, s, u in [(0, T.ground(x, y), 0, 0), (t0, T.ground(x, y), 0, 0), (t0 + 0.8, T.ground(x, y) + 0.8, 1.2, 0.1),
                       (t0 + 5.5, T.CLOUD[2] - 0.4, 1.6, 1.0), (t0 + 6.3, T.CLOUD[2], 0, 1.0)]:
        w.location = (x + (T.CLOUD[0] - x) * u, y + (T.CLOUD[1] - y) * u, z)
        w.scale = (s, s, s)
        w.keyframe_insert("location", frame=F(t))
        w.keyframe_insert("scale", frame=F(t))

# pluie : particules sous le nuage
bpy.ops.mesh.primitive_plane_add(size=1, location=(T.CLOUD[0], T.CLOUD[1] - 1.5, T.CLOUD[2] - 0.6))
emitter = bpy.context.object
emitter.scale = (12, 11, 1)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=12, ring_count=8, location=(0, 0, -60))
rdrop = A.smooth(bpy.context.object)
rdrop.scale = (1, 1, 5.0)
rain_m = A.mat("pluie", A.lin(220, 235, 255), rough=0.0, trans=1.0, ior=1.33, emit=A.lin(220, 235, 255), strength=0.35)
rdrop.data.materials.append(rain_m)
mod = emitter.modifiers.new("pluie", "PARTICLE_SYSTEM")
ps = mod.particle_system.settings
ps.count = 15000
ps.frame_start, ps.frame_end = F(T.RAIN[0]), F(T.RAIN[1] - 1.2)
ps.lifetime = int(1.6 * T.FPS)
ps.normal_factor = -6.0
ps.effector_weights.gravity = 1.0
ps.render_type = "OBJECT"
ps.instance_object = rdrop
ps.particle_size = 1.0
ps.use_rotations = True
ps.rotation_mode = "VEL"
ps.rotation_factor_random = 0.0
emitter.show_instancer_for_render = False

rnd = random.Random(7)
spots = []
while len(spots) < 110:
    x, y = rnd.uniform(0.3, 7.5), rnd.uniform(-2.8, 3.5)
    near_end = math.dist((x, y), T.END) < 1.0 or (abs(x - 3.5) < 0.9 and -4.6 < y < -1.0)   # champ de la dernière caméra
    if math.dist((x, y), T.SPROUT) < 0.8 or math.dist((x, y), T.ROCK) < 0.7 or near_end:
        continue
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    fl = A.glass_flower(location=(x, y, T.ground(x, y)), size=rnd.uniform(1.0, 1.8), petals=rnd.choice([5, 6, 7]), seed=i)
    t0 = T.FLOWERS[0] + (T.FLOWERS[1] - T.FLOWERS[0] - 1.5) * rnd.random()
    for t, s in [(0, 0), (t0, 0), (t0 + 1.2, 1.08), (t0 + 1.5, 1.0)]:
        fl.scale = (s, s, s)
        fl.keyframe_insert("scale", frame=F(t))
    fl.rotation_euler = (0, 0, rnd.uniform(0, 6.28))

# ---------------------------------------------------------------- caméras et coupes
def resolve(spec, t, extra=(0, 0, 0)):
    kind, dx, dy, dz = spec
    if kind == "goutte":
        (x, y, z), scl, _ = T.drop_state(t)
        k = 1.0
        return (x + dx * k + extra[0], y + dy * k + extra[1], z + dz * k + extra[2])
    return (dx + extra[0], dy + extra[1], dz + extra[2])


cams = []
shots = T.SHOTS + [(T.DURATION, None, None, None, None, None)]
for (t0, name, lens, fstop, cam_spec, aim_spec), (t1, *_) in zip(shots, shots[1:]):
    bpy.ops.object.empty_add()
    tgt = bpy.context.object
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = name
    cam.data.lens = lens
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36
    cam.data.clip_start = 0.02
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_object = tgt
    con = cam.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    move = T.CAMERA_MOVES.get(name, (0, 0, 0))
    fr0, fr1 = F(t0), F(t1)
    for fr in list(range(fr0, fr1, 3)) + [fr1]:
        t = (fr - 1) / T.FPS
        u = T.smooth((t - t0) / (t1 - t0))
        cam.location = resolve(cam_spec, min(t, t1 - 0.01), tuple(v * u for v in move))
        cam.keyframe_insert("location", frame=fr)
        aim = resolve(aim_spec, min(t, t1 - 0.01))
        if name == "adieu" and t > T.SOUL[0]:                   # suit la volute qui monte
            u = T.smooth((t - T.SOUL[0]) / 1.5)
            sp = T.soul_pos(t)
            aim = tuple(a0 + (b0 - a0) * u for a0, b0 in zip(aim, sp))
        tgt.location = aim
        tgt.keyframe_insert("location", frame=fr)
    mk = sc.timeline_markers.new(name, frame=fr0)
    mk.camera = cam
    cams.append((fr0, cam))
sc.camera = cams[0][1]

def camera_at(frame):
    for fr0, cam in reversed(cams):
        if frame >= fr0:
            return cam
    return cams[0][1]


stills = P.get("stills") or ([P["still"]] if P.get("still") else [])
if stills:
    for fr in stills:
        sc.frame_set(fr)
        sc.camera = camera_at(fr)
        sc.render.filepath = os.path.join(P["out"], f"still_{fr:04d}.png" if len(stills) > 1 else "still.png")
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
