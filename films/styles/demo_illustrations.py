"""Démo : les illustrations générées par IA (films/illustrations/*.json) tracées au faisceau, l'une après l'autre.

    python -m films.styles.demo_illustrations output/demo_illustrations.mp4
"""
import json
import os
import subprocess
import sys

import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import ease
from films.outils.image_en_traits import DOSSIER, dessin
from films.styles.oscillo_ascenseur import AMBRE, VERT_PALE, P, faisceau

W, H, FPS = 1080, 1920, 30
ORDRE = ["nuage", "eclair", "voiture", "pneu", "perso_pluie", "perso_portiere", "perso_assis", "perso_surpris",
         "perso_calme", "avion", "cage", "decapotable", "perso_montre"]
D = 2.2


def render(out):
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    for fr in range(int(D * len(ORDRE) * FPS)):
        t = fr / FPS
        k = int(t // D)
        tl = t - k * D
        nom = ORDRE[k]
        ratio = json.load(open(os.path.join(DOSSIER, nom + ".json")))["ratio"]
        larg = min(900, 1000 / max(ratio, 1e-6))
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        if prec is not None and tl > 0.05:
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), P((0, 0, 0), 0, 150, fill=True))
        tr = dessin(nom, (W - larg) / 2, 960 - larg * ratio / 2, larg)
        faisceau(c, tr, ease(tl / 1.4), VERT_PALE, 1.1)
        prec = surf.makeImageSnapshot()
        M.ecrit(c, t, -1, "DESSIN IA → FAISCEAU", W / 2, 260, 56, AMBRE, True, 1.8, vitesse=0.0)
        M.ecran(c, t, [])
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    print("OK", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/demo_illustrations.mp4")
