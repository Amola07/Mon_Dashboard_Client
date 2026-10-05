"""Démo : personnages animés par MoMask (mouvement généré à partir d'une phrase), rendus au faisceau.

Les mouvements sont des articulations 3D (22 points, 20 images/s, repère HumanML3D, y vers le haut), générés par
le script momask `generer_mouvements.py` et rangés dans films/mouvements/.

    python -m films.styles.demo_momask output/demo_momask.mp4
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.styles.oscillo_ascenseur import AMBRE, VERT, VERT_PALE, P, cercle_pts, faisceau

W, H, FPS = 1080, 1920, 30
ICI = os.path.dirname(os.path.abspath(__file__))
MOUV = os.path.join(ICI, "..", "mouvements")
CHAINES = [[0, 2, 5, 8, 11], [0, 1, 4, 7, 10], [0, 3, 6, 9, 12, 15], [9, 14, 17, 19, 21], [9, 13, 16, 18, 20]]
CLIPS = [("m0.npy", "« FLOTTE ET AGITE LES BRAS »"), ("m1.npy", "« TOMBE, LES GENOUX CÈDENT »"),
         ("m2.npy", "« COINCÉ, TIRE SUR SA JAMBE »")]
DUREE_CLIP = 4.0


def pose(j, t, ang, cx, sol, ech):
    """Articulations à l'instant t (interpolées depuis 20 i/s), projetées en vue de trois quarts."""
    f = min(len(j) - 1.001, t * 20)
    i = int(f)
    a = j[i] + (j[i + 1] - j[i]) * (f - i)
    x0, z0 = j[0, 0, 0], j[0, 0, 2]
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + ech * ((p[0] - x0) * ca + (p[2] - z0) * sa), sol - ech * p[1]) for p in a]


def traits(pts, ech):
    tr = [[pts[k] for k in ch] for ch in CHAINES]
    tete = pts[15]
    tr.append(cercle_pts(tete[0], tete[1] - 0.06 * ech, 0.1 * ech, 20))
    return tr


def render(out):
    clips = [(np.load(os.path.join(MOUV, f)), lib) for f, lib in CLIPS]
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    sol, ech = 1380, 420
    for fr in range(int(DUREE_CLIP * len(clips) * FPS)):
        t = fr / FPS
        k = int(t // DUREE_CLIP)
        tl = t - k * DUREE_CLIP
        j, lib = clips[k]
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        if prec is not None and tl > 0.05:
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), P((0, 0, 0), 0, 150, fill=True))
        faisceau(c, [[(120, sol), (960, sol)]], 1.0, VERT, 0.8, 0.8)
        for x in range(150, 960, 60):                                       # perspective du sol
            faisceau(c, [[(x, sol), (540 + (x - 540) * 1.6, sol + 120)]], 1.0, VERT, 0.4, 0.35)
        pts = pose(j, tl, 0.5, 540, sol, ech)
        faisceau(c, traits(pts, ech), 1.0, VERT_PALE, 1.5)
        prec = surf.makeImageSnapshot()
        M.ecrit(c, t, -1, "PERSONNAGE GÉNÉRÉ", W / 2, 230, 64, AMBRE, True, 2.0, vitesse=0.0)
        M.ecrit(c, t, -1, "par une phrase (MoMask)", W / 2, 290, 30, VERT, vitesse=0.0)
        M.ecrit(c, t, -1, lib, W / 2, 1560, 38, VERT_PALE, True, 1.4, vitesse=0.0)
        M.ecran(c, t, [])
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    print("OK", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/demo_momask.mp4")
