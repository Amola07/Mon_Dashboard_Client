"""Comparaison : ancien personnage (poses interpolées, « robot ») et nouveau (mouvement humain MoMask, lignes souples,
extrémités qui suivent avec retard), dans le même style de traits.

    python -m films.styles.demo_souple output/demo_souple.mp4
"""
import subprocess
import sys

import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import bonhomme, ease
from films.styles import mouvement as MV
from films.styles.oscillo_ascenseur import AMBRE, VERT, VERT_PALE, P, faisceau

W, H, FPS = 1080, 1920, 30
SCENES = [("panique_debout", "« IL PANIQUE »", "debout", "flotte"), ("chute_allonge", "« IL TOMBE ET S'ALLONGE »", "debout", "allonge")]
D = 4.0


def render(out):
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    for fr in range(int(D * len(SCENES) * FPS)):
        t = fr / FPS
        k = int(t // D)
        tl = t - k * D
        nom, lib, p0, p1 = SCENES[k]
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        if prec is not None and tl > 0.05:
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), P((0, 0, 0), 0, 150, fill=True))
        for y in (900, 1560):
            faisceau(c, [[(120, y), (960, y)]], 1.0, VERT, 0.8, 0.8)
        # avant : deux poses et un fondu entre elles
        u = ease((tl - 0.5) / 1.6) if p1 == "allonge" else 0.5 + 0.5 * __import__("math").sin(tl * 6)
        faisceau(c, bonhomme(540, 900, 3.6, p0, p1, u), 1.0, VERT_PALE, 1.4)
        # maintenant : le mouvement humain, en lignes souples
        faisceau(c, MV.figure(nom, tl, 540, 1560, 290, 1, ancre="pieds"), 1.0, VERT_PALE, 1.4)
        prec = surf.makeImageSnapshot()
        M.ecrit(c, t, -1, lib, W / 2, 230, 50, AMBRE, True, 1.8, vitesse=0.0)
        M.ecrit(c, t, -1, "AVANT", 160, 380, 36, VERT, False, vitesse=0.0)
        M.ecrit(c, t, -1, "MAINTENANT", 160, 1040, 36, AMBRE, False, 1.4, vitesse=0.0)
        M.ecran(c, t, [])
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    print("OK", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/demo_souple.mp4")
