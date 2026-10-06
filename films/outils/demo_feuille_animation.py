"""Essai : la feuille d'animation « lancer » jouée image par image, à vitesse réelle puis au ralenti.

    PYTHONPATH=. python films/outils/demo_feuille_animation.py output/essai_lancer.mp4 son.wav
"""
import subprocess, sys
import skia, numpy as np
from films.styles.oscillo_ascenseur import VERT, VERT_PALE, AMBRE, faisceau
from films.outils.feuille_animation import pose_anim
from films.outils.image_en_traits import dessin
from films.styles import oscillo_son as Z
W, H, FPS = 1080, 1920, 30
SOL = 1330
DUR = [0.6, 0.18, 0.18, 0.08, 0.08, 0.12, 0.16]           # temps de chaque image, la dernière est tenue
def pose_au(u, ralenti):
    u /= ralenti
    k = 0
    while k < 7 and u >= DUR[k]:
        u -= DUR[k]; k += 1
    dx = 0 if k < 7 else -min(260, 150 * u)               # recul : il glisse à l'opposé du lancer
    return k, dx
PASSES = [(0.0, 1.0, "VITESSE RÉELLE"), (3.4, 2.5, "RALENTI")]
T = 3.4 + 2.5 * 3.4 / 1.0 * 0 + 6.5
out = sys.argv[1]
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-i", sys.argv[2], "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac",
                       "-shortest", out], stdin=subprocess.PIPE)
surf = skia.Surface(W, H); prev = None
lac = dessin("lac", -70, 650, 1220)
font = skia.Font(skia.Typeface("DejaVu Sans Mono"), 54)
for f in range(int(T * FPS)):
    t = f / FPS
    c = surf.getCanvas()
    c.clear(skia.Color(2, 8, 4))
    if prev is not None:
        p = skia.Paint(); p.setAlphaf(150 / 255); c.drawImage(prev, 0, 0, skia.SamplingOptions(), p)
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(2, 8, 4, 90)))
    faisceau(c, lac, 1.0, VERT, 0.9, 0.45)
    t0, ral, nom = PASSES[1] if t >= PASSES[1][0] else PASSES[0]
    k, dx = pose_au(t - t0, ral)
    faisceau(c, pose_anim("lancer", k, 540 + dx, SOL, 560), 1.0, VERT_PALE, 1.2)
    pt = skia.Paint(Color=skia.Color(*AMBRE), AntiAlias=True)
    c.drawString(nom, (W - font.measureText(nom)) / 2, 380, font, pt)
    c.drawString(f"IMAGE {k + 1}/8", 60, 1600, skia.Font(skia.Typeface("DejaVu Sans Mono"), 34), skia.Paint(Color=skia.Color(*VERT)))
    prev = surf.makeImageSnapshot()
    ff.stdin.write(prev.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
ff.stdin.close(); ff.wait()
