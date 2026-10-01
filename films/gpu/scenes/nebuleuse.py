"""Nébuleuse volumétrique : la caméra avance lentement entre des piliers de gaz éclairés à contre-jour.

blender -b -P nebuleuse.py -- --out /chemin/neb_ --palette bleu --frames 150
Palettes : bleu (bleu/violet/magenta), feu (rouge/orange/or), emeraude (vert/turquoise/or), rose (magenta/rouge).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import commun as C  # noqa: E402

PALETTES = {
    "bleu": [(0.0, (0.01, 0.03, 0.25, 1)), (0.35, (0.10, 0.20, 1.0, 1)), (0.6, (0.55, 0.20, 1.0, 1)),
             (0.8, (1.0, 0.20, 0.55, 1)), (1.0, (1.0, 0.65, 0.40, 1))],
    "feu": [(0.0, (0.15, 0.01, 0.0, 1)), (0.35, (0.9, 0.08, 0.02, 1)), (0.6, (1.0, 0.30, 0.03, 1)),
            (0.85, (1.0, 0.65, 0.15, 1)), (1.0, (1.0, 0.95, 0.7, 1))],
    "emeraude": [(0.0, (0.0, 0.05, 0.04, 1)), (0.35, (0.0, 0.5, 0.35, 1)), (0.6, (0.1, 0.9, 0.6, 1)),
                 (0.8, (0.9, 0.85, 0.2, 1)), (1.0, (1.0, 0.95, 0.8, 1))],
    "rose": [(0.0, (0.1, 0.0, 0.08, 1)), (0.35, (0.8, 0.05, 0.3, 1)), (0.6, (1.0, 0.15, 0.55, 1)),
             (0.8, (0.6, 0.3, 1.0, 1)), (1.0, (1.0, 0.85, 0.95, 1))],
}


def nebula_material(palette, seed, dom):
    m, N = C.material("nebuleuse")
    tc = N.new("ShaderNodeTexCoord")
    tc.object = dom                                        # coordonnées du domaine, même vues depuis un autre objet
    # déformation du domaine : de grandes volutes
    warp = N.new("ShaderNodeTexNoise", noise_dimensions="4D")
    warp.inputs["Scale"].default_value = 0.35
    warp.inputs["Detail"].default_value = 3.0
    warp.inputs["W"].default_value = seed * 3.1
    N.link(tc.outputs["Object"], warp.inputs["Vector"])
    wv = N.new("ShaderNodeVectorMath", operation="SUBTRACT")
    N.link(warp.outputs["Color"], wv.inputs[0])
    wv.inputs[1].default_value = (0.5, 0.5, 0.5)
    ws = N.new("ShaderNodeVectorMath", operation="SCALE")
    N.link(wv.outputs["Vector"], ws.inputs[0])
    ws.inputs["Scale"].default_value = 2.2
    q = N.new("ShaderNodeVectorMath", operation="ADD")
    N.link(tc.outputs["Object"], q.inputs[0])
    N.link(ws.outputs["Vector"], q.inputs[1])
    # forme : de grands volumes (bruit à basse fréquence, très contrasté)
    big = N.new("ShaderNodeTexNoise", noise_dimensions="4D")
    big.inputs["Scale"].default_value = 0.22
    big.inputs["Detail"].default_value = 2.0
    big.inputs["W"].default_value = seed * 7.7
    N.link(q.outputs["Vector"], big.inputs["Vector"])
    # détail : volutes fines et filaments
    det = N.new("ShaderNodeTexNoise", noise_dimensions="4D")
    det.inputs["Scale"].default_value = 1.1
    det.inputs["Detail"].default_value = 15.0
    det.inputs["Roughness"].default_value = 0.68
    det.inputs["Distortion"].default_value = 0.35
    det.inputs["W"].default_value = seed * 1.3
    N.link(q.outputs["Vector"], det.inputs["Vector"])
    rid = N.math("ABSOLUTE", N.math("SUBTRACT", det.outputs["Fac"], 0.5))
    ridge = N.math("POWER", N.math("SUBTRACT", 1.0, N.math("MULTIPLY", rid, 2.0)), 3.0)
    n = N.math("ADD", N.math("MULTIPLY", big.outputs["Fac"], 1.0),
               N.math("ADD", N.math("MULTIPLY", det.outputs["Fac"], 0.55), N.math("MULTIPLY", ridge, 0.12)))
    n_raw = n
    map_n = N.new("ShaderNodeMapRange", clamp=True)        # bornes réglées par calibrate()
    N.link(n_raw, map_n.inputs["Value"])
    dens_r = N.ramp(map_n.outputs["Result"], [(0.0, (0, 0, 0, 1)), (0.35, (0.25, 0.25, 0.25, 1)),
                                              (1.0, (1, 1, 1, 1))])
    dens = N.math("MULTIPLY", dens_r.outputs["Color"], 0.9)
    # couleur : champ « d'ionisation » lent, indépendant de la densité
    ion = N.new("ShaderNodeTexNoise", noise_dimensions="4D")
    ion.inputs["Scale"].default_value = 0.5
    ion.inputs["Detail"].default_value = 2.0
    ion.inputs["W"].default_value = seed * 5.3 + 2
    N.link(q.outputs["Vector"], ion.inputs["Vector"])
    ionr = N.math("ADD", N.math("MULTIPLY", ion.outputs["Fac"], 4.0), N.math("MULTIPLY", det.outputs["Fac"], 1.2))
    map_i = N.new("ShaderNodeMapRange", clamp=True)
    N.link(ionr, map_i.inputs["Value"])
    colr = N.ramp(map_i.outputs["Result"], PALETTES[palette])
    albedo = N.new("ShaderNodeMix", data_type="RGBA")      # le gaz diffuse sa propre couleur (pas du blanc)
    albedo.inputs["Factor"].default_value = 0.35
    N.link(colr.outputs["Color"], albedo.inputs["A"])
    albedo.inputs["B"].default_value = (0.02, 0.02, 0.03, 1)
    # le gaz fin luit, le gaz épais absorbe (poussière sombre)
    thin = N.math("SUBTRACT", 1.0, dens_r.outputs["Color"])
    glow = N.math("MULTIPLY", N.math("ADD", thin, 0.12), N.math("MULTIPLY", dens, 3.5))
    vol = N.new("ShaderNodeVolumePrincipled")
    N.link(dens, vol.inputs["Density"])
    N.link(albedo.outputs["Result"], vol.inputs["Color"])
    N.link(colr.outputs["Color"], vol.inputs["Emission Color"])
    N.link(glow, vol.inputs["Emission Strength"])
    vol.inputs["Absorption Color"].default_value = (0.05, 0.03, 0.04, 1)
    vol.inputs["Anisotropy"].default_value = 0.45            # diffusion vers l'avant : contre-jour lumineux
    out = N.new("ShaderNodeOutputMaterial")
    N.link(vol.outputs["Volume"], out.inputs["Volume"])
    return m, (warp, big, det, ion), {"n": (n_raw, map_n), "ion": (ionr, map_i), "out": out, "vol": vol}


def calibrate(sc, dom, m, h, coverage=0.32):
    """Mesure la distribution réelle du bruit sur trois coupes du domaine (rendu minuscule en EXR), puis règle
    les bornes : le gaz occupe ≈ `coverage` de l'espace, la palette couvre toute la plage de couleurs."""
    import numpy as np
    nt = m.node_tree
    em = nt.nodes.new("ShaderNodeEmission")
    out, vol = h["out"], h["vol"]
    for l in list(out.inputs["Volume"].links):
        nt.links.remove(l)
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    saved = (sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.camera,
             sc.render.use_compositing, sc.render.image_settings.file_format, sc.render.filepath,
             sc.cycles.samples, sc.cycles.use_denoising, sc.render.engine)
    sc.render.engine = "CYCLES"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 96, 96, 100
    sc.render.use_compositing = False
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.cycles.samples, sc.cycles.use_denoising = 1, False
    dom.hide_render = True
    cd = bpy.data.cameras.new("calib")
    cd.type = "ORTHO"
    cd.ortho_scale = 2 * max(dom.scale.x, dom.scale.y)
    cam = bpy.data.objects.new("calib", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    bpy.ops.mesh.primitive_plane_add(size=2)
    pl = bpy.context.object
    pl.scale = (dom.scale.x, dom.scale.y, 1)
    pl.data.materials.append(m)
    res = {}
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), "calib.exr")
    for key in ("n", "ion"):
        nt.links.new(h[key][0], em.inputs["Strength"])
        vals = []
        for z in (-0.6, 0.0, 0.6):
            pl.location = (0, 0, z * dom.scale.z)
            cam.location = (0, 0, z * dom.scale.z + 3)
            cam.rotation_euler = (0, 0, 0)
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(path)
            px = np.array(img.pixels[:]).reshape(-1, 4)[:, 0]
            bpy.data.images.remove(img)
            vals.append(px)
        res[key] = np.concatenate(vals)
    hn, hi = h["n"][1], h["ion"][1]
    hn.inputs["From Min"].default_value = float(np.quantile(res["n"], 1 - coverage))
    hn.inputs["From Max"].default_value = float(np.quantile(res["n"], 1 - coverage * 0.12))
    hi.inputs["From Min"].default_value = float(np.quantile(res["ion"], 0.04))
    hi.inputs["From Max"].default_value = float(np.quantile(res["ion"], 0.97))
    print("[calibrage] gaz", hn.inputs["From Min"].default_value, hn.inputs["From Max"].default_value,
          "couleur", hi.inputs["From Min"].default_value, hi.inputs["From Max"].default_value)
    bpy.data.objects.remove(pl)
    bpy.data.objects.remove(cam)
    nt.nodes.remove(em)
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    dom.hide_render = False
    (sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.camera,
     sc.render.use_compositing, sc.render.image_settings.file_format, sc.render.filepath,
     sc.cycles.samples, sc.cycles.use_denoising, sc.render.engine) = saved


def main():
    a = C.args({"--palette": dict(default="bleu", choices=list(PALETTES)),
                "--evolution": dict(type=float, default=0.25, help="vitesse d'évolution des volutes"),
                "--couverture": dict(type=float, default=0.2, help="part de l'espace remplie de gaz")})
    sc = C.reset()
    C.setup_render(sc, a)
    C.bloom(sc, size=8, threshold=0.5)
    C.starfield(sc, density=1.0, milky=0.12, strength=1.0)
    bpy.ops.mesh.primitive_cube_add(size=2)
    dom = bpy.context.object
    dom.name = "gaz"
    dom.scale = (9, 9, 16)
    m, noises, handles = nebula_material(a.palette, a.seed, dom)
    dom.data.materials.append(m)
    calibrate(sc, dom, m, handles, a.couverture)
    for nd in noises:                                     # le gaz ondule lentement
        C.key_value(nd.inputs["W"], a.frames, nd.inputs["W"].default_value,
                    nd.inputs["W"].default_value + a.evolution)
    # étoiles enfouies : elles illuminent le gaz par derrière
    pal = PALETTES[a.palette]
    for (x, y, z), power, col in (((1.5, 2.0, -6.0), 5000, pal[-1][1][:3]), ((-3.0, -1.0, -11.0), 3500, (0.8, 0.85, 1.0)),
                                  ((2.5, -3.0, 3.0), 900, pal[-2][1][:3])):
        ld = bpy.data.lights.new("etoile", "POINT")
        ld.energy = power
        ld.color = col
        ld.shadow_soft_size = 0.3
        lo = bpy.data.objects.new("etoile", ld)
        lo.location = (x, y, z)
        sc.collection.objects.link(lo)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(x, y, z))
        s = bpy.context.object
        sm, SN = C.material("coeur")
        em = SN.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*col, 1)
        em.inputs["Strength"].default_value = 400
        o = SN.new("ShaderNodeOutputMaterial")
        SN.link(em.outputs["Emission"], o.inputs["Surface"])
        s.data.materials.append(sm)
    cam = C.camera(sc, lens=22)
    C.key_path(cam, a.frames, [(0.3, -0.6, 13.0), (-0.2, 0.2, 9.0)],
               [(0.8, 0.8, -4.0), (0.3, 1.0, -8.0)])
    C.render(sc, a)


main()
