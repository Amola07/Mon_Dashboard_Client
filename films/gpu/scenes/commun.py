"""Outils communs aux scènes Blender (à lancer avec : blender -b -P scene.py -- [options]).

Réglages de rendu (Cycles sur GPU OptiX/CUDA si présent, sinon CPU), format TikTok 1080×1920 à 30 i/s,
étalonnage AgX contrasté, halo par le compositeur, ciel étoilé procédural, et petites aides pour les nœuds.
"""
import argparse
import math
import sys

import bpy

W, H, FPS = 1080, 1920, 30


def args(extra=None):
    """Options après « -- » : --out, --res (échelle %), --samples, --frames, --start, --engine, --seed."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="//rendu/")
    p.add_argument("--res", type=int, default=100, help="échelle de résolution en % (25 pour un aperçu)")
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--frames", type=int, default=150, help="nombre d'images (30 = 1 s)")
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--engine", default="CYCLES", choices=["CYCLES", "EEVEE"])
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--still", type=int, default=0, help="n'image unique à rendre (0 = toute l'animation)")
    for a, kw in (extra or {}).items():
        p.add_argument(a, **kw)
    return p.parse_args(argv)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def setup_render(sc, a, motion_blur=False):
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = a.res
    sc.render.fps = FPS
    sc.frame_start = 1
    sc.frame_end = a.frames
    if a.engine == "EEVEE":
        sc.render.engine = "BLENDER_EEVEE_NEXT"
        sc.eevee.taa_render_samples = max(16, a.samples)
        sc.eevee.use_volumetric_shadows = True
        sc.eevee.volumetric_tile_size = "2"
        sc.eevee.volumetric_samples = 128
    else:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = a.samples
        sc.cycles.use_denoising = True
        sc.cycles.volume_step_rate = 1.0
        sc.cycles.volume_max_steps = 512
        sc.cycles.max_bounces = 6
        sc.cycles.volume_bounces = 1
        sc.cycles.seed = a.seed
        sc.cycles.device = "CPU"
        try:                                               # GPU : OptiX (RTX, T4) puis CUDA (P100)
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for kind in ("OPTIX", "CUDA"):
                try:
                    prefs.compute_device_type = kind
                    prefs.get_devices()
                    gpus = [d for d in prefs.devices if d.type == kind]
                    if gpus:
                        for d in prefs.devices:
                            d.use = d.type == kind
                        sc.cycles.device = "GPU"
                        sc.cycles.denoiser = "OPTIX" if kind == "OPTIX" else "OPENIMAGEDENOISE"
                        print(f"[rendu] GPU {kind} : {[d.name for d in gpus]}")
                        break
                except TypeError:
                    continue
        except Exception as e:                             # pas de GPU : on rend sur le processeur
            print("[rendu] CPU", e)
    sc.render.use_motion_blur = motion_blur
    sc.render.motion_blur_shutter = 0.5
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.filepath = a.out


def bloom(sc, size=7, mix=0.0, threshold=0.6, kind="FOG_GLOW"):
    """Halo des hautes lumières dans le compositeur."""
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    gl = nt.nodes.new("CompositorNodeGlare")
    gl.glare_type = kind
    gl.quality = "HIGH"
    gl.size = size
    gl.mix = mix
    gl.threshold = threshold
    out = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], gl.inputs["Image"])
    nt.links.new(gl.outputs["Image"], out.inputs["Image"])


class Nodes:
    """Petite aide pour écrire des arbres de nœuds lisibles."""

    def __init__(self, tree):
        self.t = tree
        self.n = tree.nodes
        self.l = tree.links

    def new(self, kind, **props):
        node = self.n.new(kind)
        for k, v in props.items():
            if k in node.inputs.keys():
                node.inputs[k].default_value = v
            else:
                setattr(node, k, v)
        return node

    def link(self, a, b):
        self.l.new(a, b)

    def math(self, op, a, b=None, clamp=False):
        m = self.n.new("ShaderNodeMath")
        m.operation = op
        m.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                self.l.new(v, m.inputs[i])
        return m.outputs[0]

    def ramp(self, src, stops, interp="LINEAR"):
        """stops : [(position, (r, g, b, a)), …]"""
        r = self.n.new("ShaderNodeValToRGB")
        r.color_ramp.interpolation = interp
        els = r.color_ramp.elements
        while len(els) > 1:
            els.remove(els[-1])
        els[0].position, els[0].color = stops[0]
        for pos, col in stops[1:]:
            e = els.new(pos)
            e.color = col
        self.l.new(src, r.inputs["Fac"])
        return r


def material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, Nodes(m.node_tree)


def starfield(sc, density=1.0, milky=0.25, tint=(0.5, 0.6, 1.0), strength=1.0):
    """Ciel : deux couches d'étoiles (Voronoi) de tailles et couleurs variées + voile de voie lactée."""
    w = bpy.data.worlds.new("ciel")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    N = Nodes(nt)
    tc = N.new("ShaderNodeTexCoord")
    total = None
    for scale, thr, gain in ((420.0, 0.045, 6.0), (130.0, 0.03, 18.0)):
        vo = N.new("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature="F1")
        vo.inputs["Scale"].default_value = scale * density
        vo.inputs["Randomness"].default_value = 1.0
        N.link(tc.outputs["Generated"], vo.inputs["Vector"])
        star = N.math("LESS_THAN", vo.outputs["Distance"], thr)
        sepc = N.new("ShaderNodeSeparateColor")
        N.link(vo.outputs["Color"], sepc.inputs["Color"])
        b = N.math("POWER", sepc.outputs["Red"], 6.0)
        lay = N.math("MULTIPLY", star, N.math("MULTIPLY", b, gain))
        total = lay if total is None else N.math("ADD", total, lay)
    no = N.new("ShaderNodeTexNoise", noise_dimensions="3D")
    no.inputs["Scale"].default_value = 2.0
    no.inputs["Detail"].default_value = 10.0
    no.inputs["Roughness"].default_value = 0.62
    N.link(tc.outputs["Generated"], no.inputs["Vector"])
    haze = N.math("MULTIPLY", N.math("POWER", no.outputs["Fac"], 4.0), milky)
    col = N.new("ShaderNodeMix", data_type="RGBA")
    col.inputs["Factor"].default_value = 1.0
    bg = N.new("ShaderNodeBackground")
    em_col = N.new("ShaderNodeCombineColor")
    lum = N.math("ADD", total, haze)
    N.link(N.math("MULTIPLY", lum, tint[0]), em_col.inputs["Red"])
    N.link(N.math("MULTIPLY", lum, tint[1]), em_col.inputs["Green"])
    N.link(N.math("MULTIPLY", lum, tint[2]), em_col.inputs["Blue"])
    N.link(em_col.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    out = N.new("ShaderNodeOutputWorld")
    N.link(bg.outputs["Background"], out.inputs["Surface"])
    for nd in list(nt.nodes):                              # nettoie les nœuds orphelins
        if not any(o.is_linked for o in nd.outputs) and nd.type not in ("OUTPUT_WORLD",):
            nt.nodes.remove(nd)
    return w


def camera(sc, lens=24.0, dof=None):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.clip_start = 0.01
    cd.clip_end = 5000
    if dof:
        cd.dof.use_dof = True
        cd.dof.focus_distance, cd.dof.aperture_fstop = dof
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def look_at(obj, target):
    from mathutils import Vector
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def key_path(cam, frames, points, targets, ease=True):
    """Trajectoire de caméra : positions et cibles clés réparties sur l'animation (courbes lissées)."""
    n = len(points)
    for i, (p, tg) in enumerate(zip(points, targets)):
        f = 1 + round((frames - 1) * i / max(1, n - 1))
        cam.location = p
        look_at(cam, tg)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    if cam.animation_data and cam.animation_data.action:
        for fc in _fcurves(cam.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.easing = "AUTO" if ease else "EASE_IN_OUT"


def _fcurves(action):
    if hasattr(action, "fcurves") and len(action.fcurves):
        return action.fcurves
    out = []                                               # Blender 4.4+ : actions en couches
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def key_value(socket, frames, v0, v1):
    socket.default_value = v0
    socket.keyframe_insert("default_value", frame=1)
    socket.default_value = v1
    socket.keyframe_insert("default_value", frame=frames)


def linear_all():
    for a in bpy.data.actions:
        for fc in _fcurves(a):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def render(sc, a):
    if a.still:
        sc.frame_set(a.still)
        sc.render.filepath = a.out if a.out.endswith(".png") else a.out + f"{a.still:04d}.png"
        bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
