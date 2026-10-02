"""Démo : l'Orbe dit le début d'une voix off, bouche synchronisée (Rhubarb Lip Sync).

    python -m films.persos.demo_parle voix.mp3 debut duree sortie.mp4
"""
import math
import subprocess
import sys
import tempfile

import numpy as np
import skia

from films import montage_ia as MI
from films.episodes.ep12_pyramide.montage import SEG
from films.persos import levres as LV
from films.persos.orbe import H, W, Etat, P, draw_orbe, rgb


def main():
    voix, t0, dur, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    sync = LV.Synchro(voix, t0, dur)
    subs = MI.groups([(txt, a - t0, b - t0) for txt, a, b in SEG if t0 <= a < t0 + dur])
    surpris = [(6.24 - t0, 8.9 - t0)]                      # « quelque chose qui ne devrait pas être là »
    tmp = tempfile.mkdtemp()
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                            "-r", "30", "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", f"{tmp}/v.mp4"],
                           stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for i in range(int(dur * 30)):
        t = i / 30
        c = surf.getCanvas()
        c.drawRect(skia.Rect(0, 0, W, H), P(shader=skia.GradientShader.MakeLinear(
            [skia.Point(0, 0), skia.Point(0, H)], [rgb((22, 20, 44)), rgb((40, 26, 70)), rgb((18, 30, 60))])))
        c.drawCircle(200, 300, 400, P((120, 80, 255), 40, blur=120))
        c.drawCircle(900, 1500, 450, P((60, 200, 255), 35, blur=140))
        forme = sync(t)
        e = Etat(expr="parle", age=t, levres=forme)
        if any(a <= t < b for a, b in surpris):
            e.humeur_avant, e.humeur_mix = "calme", 1.0
            e.expr = "parle"
            e.regard = (0.0, -0.3)
        e.cligne = (t % 3.3) < 0.11
        e.regard = (0.25 * math.sin(t * 0.7), 0.1 * math.sin(t * 0.5)) if e.regard == (0.0, 0.0) else e.regard
        c.save()
        c.translate(W / 2, 820 + 12 * math.sin(t * 2.2))
        c.scale(1.6, 1.6)
        draw_orbe(c, t, e)
        c.restore()
        arr = np.ascontiguousarray(surf.makeImageSnapshot().toarray())
        MI.draw_sub(skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType).getCanvas(), t, subs)
        enc.stdin.write(arr.tobytes())
    enc.stdin.close()
    enc.wait()
    v = MI.load_voice(voix)[int(t0 * MI.SR): int((t0 + dur) * MI.SR)]
    MI.soundtrack(f"{tmp}/a.wav", v, dur)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    main()
