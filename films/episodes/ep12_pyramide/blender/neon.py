"""Briques Blender communes de l'épisode 12 : matériaux néon, lignes, boîtes, pyramide et intérieur aux dimensions réelles.
Rendu Eevee rapide ; la lueur est ajoutée ensuite par ffmpeg (rendu.py)."""
import math
import bpy
from mathutils import Vector

FPS = 30
BLUE = (0.08, 0.35, 1.0)
BLUE_HI = (0.35, 0.65, 1.0)
RED = (1.0, 0.06, 0.04)
ORANGE = (1.0, 0.42, 0.08)
GOLD = (1.0, 0.68, 0.18)
COPPER = (0.95, 0.38, 0.12)
GREEN = (0.2, 0.9, 0.55)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    sc.world = w
    return sc


# ---------- matériaux ----------
def emit(rgb, strength, name="emit"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*rgb, 1)
    e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def strength_socket(m):
    return next(n for n in m.node_tree.nodes if n.type == "EMISSION").inputs[1]


def key_strength(m, pairs):
    """pairs = [(frame, strength)]"""
    s = strength_socket(m)
    for f, v in pairs:
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)


def glass(tint=(0.004, 0.008, 0.02), rough=0.15, name="verre"):
    """Verre sombre ; opacité animable via key_alpha."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.6
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(t.outputs[0], mx.inputs[1])
    nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], o.inputs[0])
    return m


def key_alpha(m, pairs):
    s = next(n for n in m.node_tree.nodes if n.type == "MIX_SHADER").inputs[0]
    for f, v in pairs:
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)


# ---------- géométrie ----------
def _obj(o, mat, parent):
    if mat is not None:
        o.data.materials.append(mat)
    if parent is not None:
        o.parent = parent
    return o


def empty(name="grp", loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location, e.rotation_euler = loc, rot
    return e


def box(x0, x1, y0, y1, z0, z1, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return _obj(o, mat, parent)


def mesh(verts, faces, mat, parent=None, name="mesh"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return _obj(o, mat, parent)


def line(points, r, mat, parent=None, cyclic=False, name="ligne"):
    """Polyligne en tube lumineux ; animable avec draw()."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 1
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, q in zip(sp.points, points):
        p.co = (*q, 1)
    sp.use_cyclic_u = cyclic
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    return _obj(o, mat, parent)


def draw(o, f0, f1, start=0.0, end=1.0):
    """Trace progressivement la ligne entre les images f0 et f1."""
    cu = o.data
    cu.bevel_factor_mapping_end = "SPLINE"
    cu.bevel_factor_end = start
    cu.keyframe_insert("bevel_factor_end", frame=f0)
    cu.bevel_factor_end = end
    cu.keyframe_insert("bevel_factor_end", frame=f1)


def rect(p, u, v, r, mat, parent=None):
    """Contour rectangulaire : coin p, côtés u et v."""
    p, u, v = Vector(p), Vector(u), Vector(v)
    return line([p, p + u, p + u + v, p + v], r, mat, parent, cyclic=True)


def outline_box(x0, x1, y0, y1, z0, z1, r, mat, parent=None):
    c = [Vector((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    E = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    return [line([c[a], c[b]], r, mat, parent) for a, b in E]


def sphere(loc, r, mat, parent=None, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    return _obj(bpy.context.active_object, mat, parent)


def light(loc, rgb, energy, parent=None, radius=0.05):
    bpy.ops.object.light_add(type="POINT", location=loc)
    l = bpy.context.active_object
    l.data.color, l.data.energy, l.data.shadow_soft_size = rgb, energy, radius
    if parent is not None:
        l.parent = parent
    return l


def flame(loc, scale=1.0, parent=None, energy=150, frames=200):
    """Flamme orange vacillante (sphère étirée + lumière)."""
    m = emit(ORANGE, 40)
    f = sphere(loc, 0.05 * scale, m, parent, seg=12)
    f.scale = (1, 1, 1.8)
    l = light((loc[0], loc[1], loc[2] + 0.1 * scale), (1.0, 0.45, 0.12), energy, parent)
    import random
    rnd = random.Random(7)
    for k in range(0, frames + 1, 6):
        l.data.energy = energy * rnd.uniform(0.65, 1.1)
        l.data.keyframe_insert("energy", frame=k + 1)
    return f, l, m


# ---------- caméra et rendu ----------
def camera(lens=24, loc=(0, -10, 2), target=(0, 0, 0)):
    sc = bpy.context.scene
    d = bpy.data.cameras.new("cam")
    d.lens, d.sensor_width = lens, 36
    d.clip_start, d.clip_end = 0.01, 5000
    cam = bpy.data.objects.new("cam", d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    tgt = empty("cible", target)
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    cam.location = loc
    return cam, tgt


def keys(obj, path, pairs):
    """pairs = [(frame, valeur)] ; interpolation lissée (Bézier par défaut)."""
    for f, v in pairs:
        setattr(obj, path, v)
        obj.keyframe_insert(path, frame=f)


def setup(frames, pct=50, samples=4):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = samples
    sc.eevee.use_raytracing = True
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, pct
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, frames
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - High Contrast"
    sc.render.image_settings.file_format = "PNG"


# ---------- la Grande Pyramide (vue en coupe : y = nord→sud, z = haut, origine au centre de la base) ----------
HALF, HEIGHT = 115.0, 146.6


def pyramid(parent=None, courses=36, glass_mat=None, edge=None, course_mat=None, r_edge=0.35, r_course=0.12):
    """Solide en verre + 4 arêtes + lignes d'assises. Renvoie (solide, [arêtes], [assises])."""
    a, h = HALF, HEIGHT
    V = [(-a, -a, 0), (a, -a, 0), (a, a, 0), (-a, a, 0), (0, 0, h)]
    solid = mesh(V, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)], glass_mat or glass(), parent, "pyramide")
    edge = edge or emit(BLUE, 6)
    edges = [line([V[i], V[4]], r_edge, edge, parent) for i in range(4)]
    edges.append(line(V[:4], r_edge, edge, parent, cyclic=True))
    cl = []
    if courses:
        course_mat = course_mat or emit(BLUE, 1.0)
        for k in range(1, courses):
            z = h * k / courses
            s = a * (1 - z / h) + 0.05
            cl.append(line([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], r_course, course_mat, parent, cyclic=True))
    return solid, edges, cl


# éléments intérieurs (coordonnées approchées des relevés publiés)
GG0, GG1 = Vector((0, -37.0, 21.7)), Vector((0, 5.0, 42.9))         # Grande Galerie (bas, haut)
VOID0, VOID1 = Vector((0, -27.0, 36.0)), Vector((0, 3.0, 51.0))      # « Big Void » (≥ 30 m, au-dessus de la galerie)
KC = (-5.2, 5.2, 8.0, 13.2, 43.0, 48.8)                              # chambre du roi (x, y, z)
QC = (-2.6, 2.6, -2.9, 2.9, 21.7, 27.9)                              # chambre de la reine


def interior(parent=None, mat=None, r=0.25):
    """Couloirs et chambres en lignes. Renvoie un dict de lignes."""
    mat = mat or emit(BLUE_HI, 5)
    L = {}
    ent = Vector((0, -HALF + 17.0 * HALF / HEIGHT, 17.0))
    L["descendant"] = line([ent, (0, -6.0, -30.0)], r, mat, parent)
    L["sous_terraine"] = line([(0, -6, -30), (0, 8, -30), (0, 8, -26), (0, -6, -26)], r, mat, parent, cyclic=True)
    L["ascendant"] = line([(0, -72.0, 2.0), GG0 + Vector((0, 0, 0))], r, mat, parent)
    L["horizontal"] = line([GG0, (0, -2.9, 21.7)], r, mat, parent)
    L["reine"] = line([(0, -2.9, 21.7), (0, 2.9, 21.7), (0, 2.9, 25.5), (0, 0, 27.9), (0, -2.9, 25.5)], r, mat, parent, cyclic=True)
    top = GG1 + Vector((0, 0, 8.6))
    L["galerie"] = line([GG0, GG1, top, GG0 + Vector((0, 0, 8.6))], r, mat, parent, cyclic=True)
    L["antichambre"] = line([GG1, (0, 8.0, 42.9)], r, mat, parent)
    L["roi"] = line([(0, 8.0, 43.0), (0, 13.2, 43.0), (0, 13.2, 48.8), (0, 8.0, 48.8)], r, mat, parent, cyclic=True)
    L["decharge"] = [line([(0, 8.0, z), (0, 13.2, z)], r * 0.6, mat, parent) for z in (51.0, 53.2, 55.4, 57.6)]
    L["decharge"].append(line([(0, 8.0, 59.5), (0, 10.6, 63.5), (0, 13.2, 59.5)], r * 0.6, mat, parent))
    L["conduits_reine"] = [line([(0, -2.9, 22.6), (0, -2.9 - 46.0, 22.6 + 38.6)], r * 0.5, mat, parent),
                           line([(0, 2.9, 22.6), (0, 2.9 + 46.0, 22.6 + 38.6)], r * 0.5, mat, parent)]
    L["conduits_roi"] = [line([(0, 8.0, 44.0), (0, -60.0, 81.0)], r * 0.5, mat, parent),
                         line([(0, 13.2, 44.0), (0, 70.0, 75.0)], r * 0.5, mat, parent)]
    nf = -HALF + 22.0 * HALF / HEIGHT
    L["couloir_nord"] = line([(0, nf, 23.0), (0, nf + 9.0, 23.0)], r, mat, parent)
    return L


def void(parent=None, mat=None, radius=2.2):
    """Le grand vide : capsule rouge inclinée au-dessus de la galerie."""
    mat = mat or emit(RED, 6)
    d = VOID1 - VOID0
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=d.length, location=(VOID0 + VOID1) / 2)
    o = bpy.context.active_object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return _obj(o, mat, parent)


# ---------- décor ----------
def stars(n=500, radius=1500, seed=3, parent=None, zmin=0.05):
    """Ciel étoilé : petites sphères lumineuses sur un dôme (un seul objet)."""
    import random
    rnd = random.Random(seed)
    m = emit((0.7, 0.8, 1.0), 3)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
    proto = bpy.context.active_object
    verts, faces = [], []
    pv = [v.co.copy() for v in proto.data.vertices]
    pf = [tuple(p.vertices) for p in proto.data.polygons]
    bpy.data.objects.remove(proto)
    for _ in range(n):
        th = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(zmin, 1)
        rr = math.sqrt(1 - z * z)
        c = Vector((rr * math.cos(th), rr * math.sin(th), z)) * radius
        s = radius * rnd.uniform(0.0006, 0.0018)
        base = len(verts)
        verts += [c + v * s for v in pv]
        faces += [tuple(base + i for i in f) for f in pf]
    return mesh(verts, faces, m, parent, "etoiles")


def ground(size=4000, z=0.0, mat=None, parent=None):
    mat = mat or glass(tint=(0.002, 0.004, 0.01), rough=0.35, name="sol")
    s = size / 2
    return mesh([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], [(0, 1, 2, 3)], mat, parent, "sol")


def reveal_emit(rgb, strength, axis="Z", name="revele"):
    """Émission visible seulement là où la coordonnée objet < seuil (seuil animable avec key_reveal)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sx = nt.nodes.new("ShaderNodeSeparateXYZ")
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = -1e6
    lt.name = "seuil"
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*rgb, 1)
    e.inputs[1].default_value = strength
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tc.outputs["Object"], sx.inputs[0])
    nt.links.new(sx.outputs[axis], lt.inputs[0])
    nt.links.new(lt.outputs[0], mx.inputs[0])
    nt.links.new(t.outputs[0], mx.inputs[1])
    nt.links.new(e.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], o.inputs[0])
    return m


def key_reveal(m, pairs):
    s = m.node_tree.nodes["seuil"].inputs[1]
    for f, v in pairs:
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)


def visible(obj, pairs):
    """pairs = [(frame, bool)] : apparition / disparition franche."""
    for f, v in pairs:
        obj.hide_render = not v
        obj.keyframe_insert("hide_render", frame=f)
        obj.hide_viewport = not v
        obj.keyframe_insert("hide_viewport", frame=f)


def spot(loc, rgb, energy, angle_deg=30, parent=None, blend=0.4):
    bpy.ops.object.light_add(type="SPOT", location=loc)
    l = bpy.context.active_object
    l.data.color, l.data.energy = rgb, energy
    l.data.spot_size, l.data.spot_blend = math.radians(angle_deg), blend
    l.data.shadow_soft_size = 0.02
    if parent is not None:
        l.parent = parent
    return l


def aim(obj, target):
    """Oriente un objet (lumière) vers une cible fixe."""
    d = Vector(target) - Vector(obj.location)
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def blocks_wall(x0, x1, z0, z1, y, bw=1.4, bh=1.0, depth=1.0, edge=None, face=None, parent=None, seed=1, r=0.012):
    """Mur de blocs (plan x-z à la profondeur y) : verre + joints lumineux décalés."""
    import random
    rnd = random.Random(seed)
    face = face or glass()
    edge = edge or emit(BLUE, 0.8)
    box(x0, x1, y, y + depth, z0, z1, face, parent)
    z, row = z0, 0
    while z < z1 - 1e-6:
        h = min(bh * rnd.uniform(0.85, 1.15), z1 - z)
        line([(x0, y - 0.005, z), (x1, y - 0.005, z)], r, edge, parent)
        x = x0 + (bw / 2 if row % 2 else 0) + rnd.uniform(-0.2, 0.2)
        while x < x1:
            if x > x0 + 0.05:
                line([(x, y - 0.005, z), (x, y - 0.005, z + h)], r, edge, parent)
            x += bw * rnd.uniform(0.8, 1.25)
        z += h
        row += 1
    line([(x0, y - 0.005, z1), (x1, y - 0.005, z1)], r, edge, parent)
