"""Images de validation des éléments du film (une scène par élément).

    python lookdev.py <visiere|caillou|pousse|nuage|toutes> <dossier> [échantillons] [échelle]
"""
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assets as A  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
which, out = argv[0], argv[1]
samples = int(argv[2]) if len(argv) > 2 else 48
scale = float(argv[3]) if len(argv) > 3 else 0.5


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = int(1080 * scale) // 2 * 2, int(1920 * scale) // 2 * 2
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = -0.6
    return sc


def camera(loc, look, lens=50, fstop=2.4, focus=None):
    bpy.ops.object.empty_add(location=look)
    tgt = bpy.context.object
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.data.lens = lens
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_distance = focus or math.dist(loc, look)
    bpy.context.scene.camera = cam


def crest_z(x, y):
    q = 1 - (x / 9) ** 2 - (y / 7) ** 2
    return -1.4 + 1.4 * math.sqrt(max(q, 0))


def render(name):
    sc = bpy.context.scene
    sc.render.filepath = os.path.join(out, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("image :", sc.render.filepath, flush=True)


def visiere():
    reset()
    A.sky(38, 25, 0.7)
    A.sun(38, 25, 5.0)
    A.desert()
    d = A.drop()
    A.hand_visor(d)
    for lid in d["lids"]:
        lid.rotation_euler = (math.radians(12), 0, 0)
    A.wisp(location=(0.05, -0.05, 1.12), height=0.7, seed=1)
    A.wisp(location=(-0.08, 0.02, 1.08), height=0.5, turns=0.9, width=0.025, seed=3)
    camera((0.35, -3.3, 0.85), (0, 0, 0.8), lens=50, fstop=2.2)
    render("visiere")


def caillou():
    reset()
    A.sky(55, 20, 0.5)
    A.sun(55, 20, 4.5)          # soleil derrière le caillou : petite ombre vers la caméra
    A.desert()
    A.rock(location=(0.25, 0.5, 0.12), size=1.3)
    d = A.drop(location=(-0.05, 0.02, 0.0), size=0.8)
    d["body"].scale = (0.95, 0.95, 0.72)          # s'écrase pour tenir dans l'ombre
    d["body"].rotation_euler = (0, 0, math.radians(15))
    d["smile"].scale = (0, 0, 0)
    d["ooh"].scale = (1, 1, 1)
    camera((-0.2, -3.6, 0.9), (0, 0.2, 0.35), lens=45, fstop=2.4)
    render("caillou")


def pousse():
    reset()
    A.sky(12, 120, 0.6)
    A.sun(12, 120, 4.0, color=(255, 200, 150))
    A.desert()
    A.sprout(location=(0.35, 0.1, crest_z(0.35, 0.1)), alive=0.0, size=1.1)
    d = A.drop(location=(-0.35, 0.0, crest_z(-0.35, 0)), size=0.55)
    d["body"].rotation_euler = (0, 0, math.radians(-35))
    for lid in d["lids"]:
        lid.rotation_euler = (math.radians(20), 0, 0)    # regard triste
    d["smile"].scale = (0.6, 1, -0.5)                    # sourire à l'envers
    camera((0.05, -2.9, 0.45), (0.05, 0.05, 0.25), lens=45, fstop=2.2)
    render("pousse")


def nuage():
    reset()
    A.sky(7, 200, 0.45)
    A.sun(7, 200, 2.5, color=(255, 190, 150))
    A.desert()
    rnd = random.Random(9)
    for k in range(34):
        x, y = rnd.uniform(-3.5, 3.5), rnd.uniform(0.5, 6.5)
        A.glass_flower(location=(x, y, crest_z(x, y)), size=rnd.uniform(0.5, 0.9), petals=rnd.choice([5, 6, 7]), seed=k)
    A.glass_flower(location=(0.9, -0.2, crest_z(0.9, -0.2)), size=1.1, petals=7, seed=99)
    A.cloud(location=(0, 8, 4.4), size=1.3, frown=1.0)
    A.rain(area=(-3.5, 3.5, 1, 9), top=4.0, count=180)
    camera((0.0, -2.4, 0.4), (0, 7, 3.3), lens=20, fstop=5.0, focus=3.0)
    render("nuage")


scenes = {"visiere": visiere, "caillou": caillou, "pousse": pousse, "nuage": nuage}
for name in (scenes if which == "toutes" else [which]):
    scenes[name]()
