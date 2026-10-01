"""Planète photoréaliste : bandes nuageuses, atmosphère lumineuse sur le limbe, anneaux à lacunes avec l'ombre de
la planète, lune, ciel étoilé. La caméra glisse lentement : les anneaux balaient l'image.

blender -b -P planete.py -- --out /chemin/pla_ --type gazeuse --frames 150
Types : gazeuse (Saturne/Jupiter), glace (bleu-vert pâle), rose (exotique), rocheuse (sans anneaux par défaut).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import commun as C  # noqa: E402

TYPES = {
    "gazeuse": dict(cols=[(0.0, (0.35, 0.22, 0.12, 1)), (0.3, (0.85, 0.68, 0.45, 1)), (0.55, (0.95, 0.88, 0.72, 1)),
                          (0.75, (0.7, 0.45, 0.25, 1)), (1.0, (0.98, 0.92, 0.8, 1))],
                    atmo=(1.0, 0.8, 0.55), ring=(0.95, 0.88, 0.75), anneaux=True, bandes=9.0),
    "glace": dict(cols=[(0.0, (0.35, 0.75, 0.8, 1)), (0.5, (0.55, 0.9, 0.9, 1)), (1.0, (0.8, 0.98, 0.98, 1))],
                  atmo=(0.45, 0.9, 1.0), ring=(0.6, 0.9, 0.85), anneaux=True, bandes=4.0),
    "rose": dict(cols=[(0.0, (0.55, 0.25, 0.5, 1)), (0.4, (0.9, 0.65, 0.85, 1)), (0.7, (0.98, 0.85, 0.95, 1)),
                       (1.0, (0.7, 0.4, 0.7, 1))],
                 atmo=(1.0, 0.6, 0.9), ring=(1.0, 0.45, 0.4), anneaux=True, bandes=6.0),
    "rocheuse": dict(cols=[(0.0, (0.25, 0.12, 0.08, 1)), (0.45, (0.55, 0.3, 0.2, 1)), (0.7, (0.75, 0.55, 0.45, 1)),
                           (1.0, (0.9, 0.85, 0.8, 1))],
                     atmo=(1.0, 0.55, 0.4), ring=(0.8, 0.7, 0.6), anneaux=False, bandes=0.0),
}


def planet_material(kind, seed):
    T = TYPES[kind]
    m, N = C.material("planete")
    tc = N.new("ShaderNodeTexCoord")
    warp = N.new("ShaderNodeTexNoise", noise_dimensions="4D", **{"W": seed * 2.3})
    warp.inputs["Scale"].default_value = 2.5
    warp.inputs["Detail"].default_value = 8.0
    warp.inputs["Roughness"].default_value = 0.6
    N.link(tc.outputs["Object"], warp.inputs["Vector"])
    if T["bandes"] > 0:                                    # géante gazeuse : bandes de latitude tourmentées
        sep = N.new("ShaderNodeSeparateXYZ")
        N.link(tc.outputs["Object"], sep.inputs["Vector"])
        lat = N.math("ADD", sep.outputs["Z"], N.math("MULTIPLY", N.math("SUBTRACT", warp.outputs["Fac"], 0.5), 0.12))
        band = N.new("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z", wave_profile="SIN")
        band.inputs["Scale"].default_value = T["bandes"] * 0.38
        band.inputs["Distortion"].default_value = 7.0
        band.inputs["Detail"].default_value = 6.0
        band.inputs["Detail Scale"].default_value = 2.0
        comb = N.new("ShaderNodeCombineXYZ")
        N.link(lat, comb.inputs["Z"])
        N.link(N.math("MULTIPLY", sep.outputs["X"], 0.2), comb.inputs["X"])
        N.link(comb.outputs["Vector"], band.inputs["Vector"])
        fine = N.new("ShaderNodeTexNoise", noise_dimensions="3D")
        fine.inputs["Scale"].default_value = 18.0
        fine.inputs["Detail"].default_value = 10.0
        N.link(tc.outputs["Object"], fine.inputs["Vector"])
        v = N.math("ADD", N.math("MULTIPLY", band.outputs["Fac"], 0.8), N.math("MULTIPLY", fine.outputs["Fac"], 0.25))
    else:                                                  # planète rocheuse : continents, cratères, calottes
        v = N.math("ADD", warp.outputs["Fac"], 0.0)
    col = N.ramp(v, T["cols"])
    bs = N.new("ShaderNodeBsdfPrincipled")
    N.link(col.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.85
    if T["bandes"] == 0:
        bump = N.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.4
        N.link(warp.outputs["Fac"], bump.inputs["Height"])
        N.link(bump.outputs["Normal"], bs.inputs["Normal"])
    out = N.new("ShaderNodeOutputMaterial")
    N.link(bs.outputs["BSDF"], out.inputs["Surface"])
    return m


def atmosphere_material(color, sun_dir):
    """Liseré lumineux : émission sur les bords (Fresnel), seulement du côté éclairé, par-dessus la planète."""
    m, N = C.material("atmosphere")
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    geo = N.new("ShaderNodeNewGeometry")
    dot = N.new("ShaderNodeVectorMath", operation="DOT_PRODUCT")
    N.link(geo.outputs["Normal"], dot.inputs[0])
    dot.inputs[1].default_value = sun_dir
    lit = N.new("ShaderNodeMapRange", clamp=True)
    N.link(dot.outputs["Value"], lit.inputs["Value"])
    lit.inputs["From Min"].default_value = -0.08
    lit.inputs["From Max"].default_value = 0.6
    rim = N.math("POWER", lw.outputs["Facing"], 2.2)
    k = N.math("MULTIPLY", rim, lit.outputs["Result"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    N.link(N.math("MULTIPLY", k, 6.0), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    add = N.new("ShaderNodeAddShader")
    N.link(em.outputs["Emission"], add.inputs[0])
    N.link(tr.outputs["BSDF"], add.inputs[1])
    out = N.new("ShaderNodeOutputMaterial")
    N.link(add.outputs["Shader"], out.inputs["Surface"])
    return m


def ring_material(color, seed):
    m, N = C.material("anneaux")
    tc = N.new("ShaderNodeTexCoord")
    ln = N.new("ShaderNodeVectorMath", operation="LENGTH")
    N.link(tc.outputs["Object"], ln.inputs[0])
    r = ln.outputs["Value"]                                # rayon (anneaux de 1,35 à 2,35 rayons planétaires)
    w1 = N.new("ShaderNodeTexWave", wave_type="RINGS", rings_direction="SPHERICAL", wave_profile="SIN")
    w1.inputs["Scale"].default_value = 30.0
    w1.inputs["Distortion"].default_value = 1.5
    w1.inputs["Detail"].default_value = 8.0
    N.link(tc.outputs["Object"], w1.inputs["Vector"])
    w2 = N.new("ShaderNodeTexWave", wave_type="RINGS", rings_direction="SPHERICAL", wave_profile="SAW")
    w2.inputs["Scale"].default_value = 7.0
    w2.inputs["Distortion"].default_value = 0.6
    w2.inputs["Phase Offset"].default_value = seed * 1.7
    N.link(tc.outputs["Object"], w2.inputs["Vector"])
    prof = N.ramp(N.math("SUBTRACT", N.math("DIVIDE", r, 2.4), 0.0),
                  [(0.0, (0, 0, 0, 1)), (0.55, (0, 0, 0, 1)), (0.57, (0.5, 0.5, 0.5, 1)), (0.72, (1, 1, 1, 1)),
                   (0.76, (0.08, 0.08, 0.08, 1)), (0.78, (0.9, 0.9, 0.9, 1)), (0.93, (0.6, 0.6, 0.6, 1)),
                   (0.98, (0, 0, 0, 1))])          # lacune type « division de Cassini » vers 0,77
    a = N.math("MULTIPLY", prof.outputs["Color"],
               N.math("ADD", N.math("MULTIPLY", w1.outputs["Fac"], 0.55), N.math("MULTIPLY", w2.outputs["Fac"], 0.45)))
    a = N.math("MULTIPLY", a, 1.3, clamp=True)
    tint = N.new("ShaderNodeMix", data_type="RGBA")
    tint.inputs["A"].default_value = (*color, 1)
    tint.inputs["B"].default_value = (color[0] * 0.55, color[1] * 0.5, color[2] * 0.45, 1)
    N.link(w2.outputs["Fac"], tint.inputs["Factor"])
    bs = N.new("ShaderNodeBsdfPrincipled")
    N.link(tint.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.9
    N.link(a, bs.inputs["Alpha"])
    out = N.new("ShaderNodeOutputMaterial")
    N.link(bs.outputs["BSDF"], out.inputs["Surface"])
    return m


def emissive(name, color, strength):
    m, N = C.material(name)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    out = N.new("ShaderNodeOutputMaterial")
    N.link(em.outputs["Emission"], out.inputs["Surface"])
    return m


def main():
    a = C.args({"--type": dict(default="gazeuse", choices=list(TYPES)),
                "--inclinaison": dict(type=float, default=24.0, help="inclinaison des anneaux (degrés)"),
                "--lune": dict(type=int, default=1)})
    T = TYPES[a.type]
    sc = C.reset()
    C.setup_render(sc, a)
    C.bloom(sc, size=7, threshold=0.8)
    C.starfield(sc, density=1.0, milky=0.15, strength=1.0)
    sun_dir = (0.92, -0.25, 0.3)                          # lumière de côté : moitié éclairée, terminateur net
    ld = bpy.data.lights.new("soleil", "SUN")
    ld.energy = 5.0
    ld.angle = math.radians(0.5)
    ld.color = (1.0, 0.97, 0.92)
    lo = bpy.data.objects.new("soleil", ld)
    sc.collection.objects.link(lo)
    C.look_at(lo, (-sun_dir[0], -sun_dir[1], -sun_dir[2]))
    root = bpy.data.objects.new("systeme", None)
    sc.collection.objects.link(root)
    root.rotation_euler = (math.radians(a.inclinaison), math.radians(-12), 0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=192, ring_count=96, radius=1.0)
    pl = bpy.context.object
    bpy.ops.object.shade_smooth()
    pl.data.materials.append(planet_material(a.type, a.seed))
    pl.parent = root
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.035)
    at = bpy.context.object
    bpy.ops.object.shade_smooth()
    at.data.materials.append(atmosphere_material(T["atmo"], sun_dir))
    at.parent = root
    if T["anneaux"]:
        bpy.ops.mesh.primitive_circle_add(vertices=256, radius=2.4, fill_type="NGON")
        rg = bpy.context.object
        rg.data.materials.append(ring_material(T["ring"], a.seed))
        rg.parent = root
    if a.lune:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.12, location=(-3.2, 2.5, 0.9))
        mo = bpy.context.object
        bpy.ops.object.shade_smooth()
        mm, MN = C.material("lune")
        no = MN.new("ShaderNodeTexNoise", noise_dimensions="3D")
        no.inputs["Scale"].default_value = 6.0
        no.inputs["Detail"].default_value = 12.0
        bs = MN.new("ShaderNodeBsdfPrincipled")
        MN.link(MN.ramp(no.outputs["Fac"], [(0.3, (0.25, 0.24, 0.23, 1)), (0.7, (0.7, 0.68, 0.65, 1))]).outputs["Color"],
                bs.inputs["Base Color"])
        o = MN.new("ShaderNodeOutputMaterial")
        MN.link(bs.outputs["BSDF"], o.inputs["Surface"])
        mo.data.materials.append(mm)
    cam = C.camera(sc, lens=42)
    pts, tgs = [], []
    for u in (0.0, 0.5, 1.0):                              # travelling en arc : les anneaux tournent dans l'image
        ang = math.radians(-35 + 30 * u)
        d = 6.4 - 0.9 * u
        pts.append((d * math.sin(ang), -d * math.cos(ang), 0.9 - 0.5 * u))
        tgs.append((0.25 - 0.2 * u, 0, -0.35))
    C.key_path(cam, a.frames, pts, tgs)
    C.render(sc, a)


main()
