"""Aperçu rapide d'un épisode oscilloscope : quelques images fixes en planche, sans rendre la vidéo (quelques secondes).

    python -m films.outils.apercu films.episodes.modele_oscillo.oscillo_modele 0 1.5 3 5 8
    → output/apercu.png  (une vignette par instant donné, en secondes)
"""
import importlib
import os
import sys

import skia


def main():
    module = importlib.import_module(sys.argv[1])
    instants = [float(x) for x in sys.argv[2:]] or [0.0, 1.0, 2.0, 4.0]
    M = module.M
    M.preparer()
    tabs = M.tableaux()
    lw, lh = 270, 480
    planche = skia.Surface(lw * len(instants), lh)
    pc = planche.getCanvas()
    pc.clear(skia.Color(0, 0, 0))
    for i, t in enumerate(instants):
        surf = skia.Surface(M.W, M.H)
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        k = max(j for j, x in enumerate(tabs) if x[0] <= t)
        tabs[k][1](c, t)
        M.sous_titres(c, t)
        M.ecran(c, t, [])
        pc.drawImageRect(surf.makeImageSnapshot(), skia.Rect(i * lw, 0, (i + 1) * lw, lh))
        f = skia.Font(M.MONO, 22)
        pc.drawString(f"{t:.1f} s", i * lw + 8, 26, f, skia.Paint(Color=skia.Color(255, 255, 255)))
    os.makedirs("output", exist_ok=True)
    planche.makeImageSnapshot().save("output/apercu.png")
    print("écrit : output/apercu.png")


if __name__ == "__main__":
    main()
