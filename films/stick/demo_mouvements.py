"""Planche animée de la bibliothèque de mouvements : Éclat joue chaque mouvement, l'un après l'autre.

    python -m films.stick.demo_mouvements sortie.mp4
"""
import math
import subprocess
import sys

import numpy as np
import skia

from . import corps as K
from . import mouvements as M
from .corps import Frame, build, v_add, v_mul

W, H = 1080, 1920
FPS = 24
SCALE = 2.6
GROUND_Y = 1300
FLOOR = Frame((0.0, 0.0), 0.0)
PAUSE = 8                                                      # images entre deux mouvements


def programme():
    """[(titre, durée en images, fonction image -> (pose, position caméra))]"""
    prog = []
    for c in M.CLIPS:
        prog.append((c.titre, c.duree + PAUSE, lambda f, c=c: (M.pose_at(c, f, FLOOR), 0.0)))
    prog.append(("Marche : contact, descente, passage, montée", 72,
                 lambda f: M.cycle("marche", f, FLOOR, expr="neutre")))
    prog.append(("Course : le corps penché, une phase de vol", 56,
                 lambda f: M.cycle("course", f, FLOOR, expr="decide")))
    return prog


def font(size, bold=True):
    return skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold() if bold else skia.FontStyle.Normal()), size)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/bibliotheque_mouvements.mp4"
    prog = programme()
    total = sum(d for _, d, _ in prog)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    cape = None
    cam = 0.0
    n = 0
    for k, (titre, dur, fn) in enumerate(prog):
        for f in range(dur):
            p, cu = fn(min(f, dur - PAUSE))
            cam += (cu - cam) * (1.0 if f == 0 else 0.35)
            c = surf.getCanvas()
            c.clear(skia.Color(0, 0, 0))
            c.drawString(titre, 50, 200, font(31), skia.Paint(AntiAlias=True, Color=skia.Color(235, 240, 255)))
            c.drawString(f"{k + 1}/{len(prog)}", 60, 260, font(30, False),
                         skia.Paint(AntiAlias=True, Color=skia.Color(140, 150, 170)))
            c.save()
            c.translate(W / 2, GROUND_Y)
            c.scale(SCALE, SCALE)
            c.translate(-cam, 0)
            # sol, avec des repères qui défilent (on voit qu'il avance)
            c.drawLine(cam - 400, 0, cam + 400, 0, skia.Paint(AntiAlias=True, Color=skia.Color(200, 205, 220),
                                                           StrokeWidth=1.6))
            for x in range(int(cam // 80) * 80 - 400, int(cam) + 400, 80):
                c.drawLine(x, 0, x, 8, skia.Paint(AntiAlias=True, Color=skia.Color(90, 95, 110), StrokeWidth=1.2))
            J = build(p)
            anchor = v_add(J["neck"], v_mul(J["fwd"], -5))
            if cape is None or f == 0:
                cape = K.Cape(anchor)
                for _ in range(30):
                    cape.step(anchor, v_mul(J["fwd"], -1), (0.0, 1800.0), 1 / 60)
            for _ in range(60 // FPS):
                cape.step(anchor, v_mul(J["fwd"], -1), (0.0, 1800.0), 1 / 60, flutter=0.25, t=n / FPS)
            K.draw(c, p, n / FPS, cape, J=J)
            c.restore()
            ff.stdin.write(surf.makeImageSnapshot().tobytes())
            n += 1
    ff.stdin.close()
    ff.wait()
    print(out, f"{total / FPS:.1f} s")


if __name__ == "__main__":
    main()
