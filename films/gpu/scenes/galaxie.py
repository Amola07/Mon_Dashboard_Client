"""Galaxie spirale volumétrique : bras de gaz bleu, bulbe doré, régions roses de formation d'étoiles, couloirs
de poussière sombre. La caméra plonge depuis le dessus vers une vue rasante pendant que la galaxie tourne.

blender -b -P galaxie.py -- --out /chemin/gal_ --frames 150 --bras 2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import commun as C  # noqa: E402


def galaxy_material(arms, twist, seed):
    m, N = C.material("galaxie")
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    N.link(tc.outputs["Object"], sep.inputs["Vector"])
    x, y, z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    r = N.math("SQRT", N.math("ADD", N.math("MULTIPLY", x, x), N.math("MULTIPLY", y, y)))
    th = N.math("ARCTAN2", y, x)
    # spirale logarithmique : phase = bras·(θ − torsion·ln r)
    ph = N.math("MULTIPLY", N.math("SUBTRACT", th, N.math("MULTIPLY", N.math("LOGARITHM", N.math("ADD", r, 0.02),
                                                                                   2.718281828), twist)), arms)
    armw = N.math("POWER", N.math("MULTIPLY", N.math("ADD", N.math("COSINE", ph), 1.0), 0.5), 5.0)
    warp = N.new("ShaderNodeTexNoise", noise_dimensions="4D")
    warp.inputs["Scale"].default_value = 4.0
    warp.inputs["Detail"].default_value = 12.0
    warp.inputs["Roughness"].default_value = 0.62
    warp.inputs["W"].default_value = seed
    N.link(tc.outputs["Object"], warp.inputs["Vector"])
    clump = N.math("POWER", warp.outputs["Fac"], 3.5)
    disk = N.math("EXPONENT", N.math("MULTIPLY", r, -2.6))  # le disque s'éteint vers le bord
    thick = N.math("EXPONENT", N.math("MULTIPLY", N.math("ABSOLUTE", z), -26.0))
    arm_d = N.math("MULTIPLY", N.math("MULTIPLY", armw, clump), N.math("MULTIPLY", disk, thick))
    bulge = N.math("EXPONENT", N.math("MULTIPLY", N.math("SQRT", N.math("ADD", N.math("MULTIPLY", r, r),
                                                                           N.math("MULTIPLY", N.math("MULTIPLY", z, z), 9.0))), -9.0))
    dens = N.math("MULTIPLY", N.math("ADD", N.math("MULTIPLY", arm_d, 14.0), N.math("MULTIPLY", bulge, 6.0)), 1.0)
    # couleur : bulbe doré → bras bleus, taches roses là où le gaz est le plus dense dans les bras
    cr = N.ramp(N.math("MULTIPLY", r, 1.6), [(0.0, (1.0, 0.85, 0.55, 1)), (0.25, (1.0, 0.75, 0.5, 1)),
                                             (0.45, (0.6, 0.7, 1.0, 1)), (1.0, (0.35, 0.5, 1.0, 1))])
    hii = N.ramp(N.math("MULTIPLY", arm_d, 3.0), [(0.0, (0, 0, 0, 1)), (0.5, (0, 0, 0, 1)), (0.8, (1, 1, 1, 1))])
    col = N.new("ShaderNodeMix", data_type="RGBA")
    N.link(hii.outputs["Color"], col.inputs["Factor"])
    N.link(cr.outputs["Color"], col.inputs["A"])
    col.inputs["B"].default_value = (1.0, 0.25, 0.55, 1)
    # poussière : couloirs sombres juste à l'intérieur des bras
    dust_ph = N.math("COSINE", N.math("ADD", ph, 0.9))
    dust = N.math("MULTIPLY", N.math("POWER", N.math("MULTIPLY", N.math("ADD", dust_ph, 1.0), 0.5), 6.0),
                  N.math("MULTIPLY", disk, thick))
    vol = N.new("ShaderNodeVolumePrincipled")
    N.link(N.math("ADD", N.math("MULTIPLY", dust, 22.0), N.math("MULTIPLY", dens, 0.1)), vol.inputs["Density"])
    vol.inputs["Color"].default_value = (0.05, 0.03, 0.02, 1)
    N.link(col.outputs["Result"], vol.inputs["Emission Color"])
    N.link(N.math("MULTIPLY", dens, 2.0), vol.inputs["Emission Strength"])
    out = N.new("ShaderNodeOutputMaterial")
    N.link(vol.outputs["Volume"], out.inputs["Volume"])
    return m


def main():
    a = C.args({"--bras": dict(type=int, default=2), "--torsion": dict(type=float, default=2.2)})
    sc = C.reset()
    C.setup_render(sc, a)
    C.bloom(sc, size=8, threshold=0.6)
    C.starfield(sc, density=1.0, milky=0.05, strength=0.8)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.0, depth=0.5)
    g = bpy.context.object
    g.scale = (6, 6, 6)
    g.data.materials.append(galaxy_material(a.bras, a.torsion, a.seed))
    g.rotation_euler = (0, 0, 0)
    g.keyframe_insert("rotation_euler", frame=1)
    g.rotation_euler = (0, 0, math.radians(-14))           # la galaxie tourne lentement
    g.keyframe_insert("rotation_euler", frame=a.frames)
    C.linear_all()
    cam = C.camera(sc, lens=30)
    C.key_path(cam, a.frames, [(0.5, -2.0, 15.0), (1.5, -9.0, 6.0), (2.0, -10.5, 1.6)],
               [(0, 0, 0), (0, 0, 0), (0.0, 0.5, 0)])
    C.render(sc, a)


main()
