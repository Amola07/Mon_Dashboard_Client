"""« POV : ton cerveau à 3 h du matin » — animation toon v2 sur un audio fourni (dialogue/nuit/audio.wav).

Plans : lui au lit (la nuit, lumière de lune), le Cerveau qui flotte dans une lueur verte, puis Sommeil et Insomnie
dans le couloir. Bouches synchronisées sur l'audio (Rhubarb), expressions par réplique.

    python -m films.dialogue.nuit output/cerveau_3h.mp4
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import skia

from films.dialogue import toon2 as T
from films.persos import levres as LV

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "nuit", "audio.wav")
W, H, FPS = 1080, 1920, 30
DUR = 38.2
F_BAN = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "fonts", "Montserrat-Bold.ttf"))
F_LAB = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "fonts", "Montserrat-ExtraBold.ttf"))

# (début, fin, qui parle, expression)
TOURS = [(0.00, 3.40, "C", "curieux"), (3.40, 3.95, "M", "blase"), (3.95, 7.20, "C", "excite"),
         (7.20, 8.20, "C", "content"), (8.20, 11.15, "M", "fatigue"), (11.15, 15.00, "C", "excite"),
         (15.00, 15.80, "M~", "dort"), (15.80, 18.66, "C", "curieux"), (18.66, 21.10, "M", "blase"),
         (21.10, 24.20, "C", "malin"), (24.20, 29.65, "M", "suppliant"), (29.65, 31.85, "C", "moqueur"),
         (31.85, 34.78, "S", "fatigue"), (34.78, DUR, "I", "malin")]
SYNC = None


def tour(t):
    for a, b, q, e in TOURS:
        if a <= t < b:
            return a, b, q, e
    return TOURS[-1]


def bouche(t, parle):
    if not parle:
        return "fermee"
    w, h, _, _ = SYNC(t)
    if h > 40:
        return "ouverte"
    if h > 14:
        return "mi" if w > 40 else "o"
    return "fermee"


# ------------------------------------------------------------------------------------------------ décors
def chambre(c, t, lueur_verte=0.0):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                        [skia.Color(26, 30, 62), skia.Color(14, 16, 36)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    # fenêtre : lune et étoiles
    win = skia.Rect(620, 180, 1000, 640)
    c.drawRect(win, T.P((18, 24, 60)))
    rng = np.random.default_rng(2)
    for _ in range(26):
        x, y = rng.uniform(630, 990), rng.uniform(190, 630)
        tw = 0.6 + 0.4 * math.sin(t * 3 + x)
        c.drawCircle(x, y, rng.uniform(2, 4), T.P((255, 250, 220), a=int(255 * tw)))
    c.drawCircle(880, 300, 62, T.P((250, 240, 200)))
    c.drawCircle(905, 285, 58, T.P((18, 24, 60)))
    c.drawRect(win, T.P(T.INK, 12))
    c.drawLine(810, 180, 810, 640, T.P(T.INK, 10))
    c.drawLine(620, 410, 1000, 410, T.P(T.INK, 10))
    # rayon de lune
    beam = skia.Path()
    beam.moveTo(620, 640)
    beam.lineTo(1000, 640)
    beam.lineTo(700, 1500)
    beam.lineTo(150, 1500)
    beam.close()
    c.drawPath(beam, T.P((150, 170, 255), a=26))
    # table de nuit + réveil 3:00
    table = skia.Path()
    table.addRect(skia.Rect(40, 1080, 330, 1500))
    T.forme(c, table, (92, 64, 52), 10, (70, 48, 40), T._decal(table, 160, 0))
    rev = skia.Path()
    rev.addRRect(skia.RRect.MakeRectXY(skia.Rect(70, 960, 300, 1080), 22, 22))
    T.forme(c, rev, (40, 40, 48), 9)
    f = skia.Font(F_LAB, 74)
    blink = (t % 1.0) < 0.5
    txt = "3:00" if blink else "3 00"
    c.drawString(txt, 185 - f.measureText("3:00") / 2, 1048, f, T.P((255, 60, 60)))
    if lueur_verte > 0:
        g = skia.GradientShader.MakeRadial(skia.Point(W / 2, 820), 760,
                                           [skia.Color(80, 255, 120, int(150 * lueur_verte)),
                                            skia.Color(40, 200, 90, 0)])
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))


def lit_avant(c):
    """Couette par-dessus le personnage."""
    cou = skia.Path()
    cou.moveTo(-60, 1330)
    cou.cubicTo(250, 1180, 700, 1230, W + 60, 1260)
    cou.lineTo(W + 60, H + 40)
    cou.lineTo(-60, H + 40)
    cou.close()
    T.forme(c, cou, (70, 92, 170), 12, (52, 70, 140), T._decal(cou, 0, 160))
    for k in range(4):
        p = skia.Path()
        x = 120 + k * 250
        p.moveTo(x, 1330 + 40 * k % 60)
        p.quadTo(x + 60, 1520, x + 20, 1720)
        c.drawPath(p, T.P((40, 56, 120), 8))


def oreiller(c):
    o = skia.Path()
    o.addRRect(skia.RRect.MakeRectXY(skia.Rect(250, 760, 1060, 1260), 160, 160))
    T.forme(c, o, (232, 236, 248), 12, (196, 204, 228), T._decal(o, 0, 150))


def couloir(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), T.P((60, 54, 80)))
    for x in (0, 380, 760):
        d = skia.Path()
        d.addRect(skia.Rect(x + 60, 260, x + 320, 1100))
        T.forme(c, d, (110, 84, 70), 10, (88, 66, 56), T._decal(d, 140, 0))
        c.drawCircle(x + 290, 700, 14, T.P((240, 200, 80)))
    c.drawRect(skia.Rect(0, 1100, W, H), T.P((80, 66, 60)))
    c.drawLine(0, 1100, W, 1100, T.P(T.INK, 10))
    g = skia.GradientShader.MakeRadial(skia.Point(W / 2, 200), 900,
                                       [skia.Color(255, 230, 170, 70), skia.Color(255, 230, 170, 0)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))


def etiquette(c, txt, x, y, col=(255, 255, 255), icone=None):
    f = skia.Font(F_LAB, 62)
    w = f.measureText(txt)
    c.drawString(txt, x - w / 2, y, f, T.P(T.INK, 14))
    c.drawString(txt, x - w / 2, y, f, T.P(col))
    if icone == "z":
        f2 = skia.Font(F_LAB, 46)
        c.drawString("z", x + w / 2 + 10, y - 20, f2, T.P((120, 170, 255)))
        c.drawString("z", x + w / 2 + 40, y - 50, skia.Font(F_LAB, 34), T.P((120, 170, 255)))
    if icone == "x":
        cx, cy = x + w / 2 + 40, y - 22
        for s in (-1, 1):
            c.drawLine(cx - 22, cy - 22 * s, cx + 22, cy + 22 * s, T.P((235, 40, 50), 12))


def bandeau(c):
    txt = "POV : ton cerveau à 3h du matin"
    f = skia.Font(F_BAN, 46)
    w = f.measureText(txt)
    r = skia.RRect.MakeRectXY(skia.Rect(W / 2 - w / 2 - 26, 120, W / 2 + w / 2 + 26, 196), 14, 14)
    c.drawRRect(r, T.P((255, 255, 255)))
    c.drawString(txt, W / 2 - w / 2, 174, f, T.P((10, 10, 12)))


# ------------------------------------------------------------------------------------------------ plans
def plan_moi(c, t, expr, parle, age):
    chambre(c, t)
    z = 1 + 0.035 * min(1, age / 3)
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(z, z)
    c.translate(-W / 2, -H / 2)
    oreiller(c)
    c.save()
    c.translate(650, 960 + 4 * math.sin(t * 1.6))
    c.scale(0.98, 0.98)
    cl = ((t + 0.4) % 3.6) < 0.12
    T.tete(c, "lui", expr, bouche(t, parle), cl, t, corps=True, inclinaison=-14 + (3 * math.sin(t * 8) if parle else 0))
    c.restore()
    lit_avant(c)
    # lumière bleue de la nuit
    c.drawRect(skia.Rect(0, 0, W, H), T.P((40, 60, 160), a=40))
    c.restore()


def plan_cerveau(c, t, expr, parle, age):
    chambre(c, t, lueur_verte=1.0)
    z = 1 + 0.05 * min(1, age / 3)
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(z, z)
    c.translate(-W / 2, -H / 2)
    c.save()
    c.translate(540, 860 + 26 * math.sin(t * 2.4))
    c.rotate(4 * math.sin(t * 1.7) + (3 * math.sin(t * 11) if parle else 0))
    c.scale(1.18, 1.18)
    T.cerveau(c, expr, bouche(t, parle), ((t + 1.1) % 3.1) < 0.1, t)
    c.restore()
    c.restore()
    c.drawRect(skia.Rect(0, 0, W, H), T.P((60, 255, 120), a=22))
    etiquette(c, "Cerveau", W / 2, 1420, (255, 160, 190))


def plan_fin(c, t, qui, expr, parle):
    couloir(c, t)
    for x, nom, q in ((265, "Sommeil", "sommeil"), (815, "Insomnie", "insomnie")):
        actif = (q == "sommeil" and qui == "S") or (q == "insomnie" and qui == "I")
        e = expr if actif else ("fatigue" if q == "sommeil" else "malin")
        c.save()
        c.translate(x, 840 + (6 * math.sin(t * 9) if actif and parle else 0))
        c.scale(0.6, 0.6)
        T.tete(c, q, e, bouche(t, actif and parle), ((t + x) % 3.4) < 0.1, t, corps=True,
               inclinaison=(6 if q == "sommeil" else -4))
        c.restore()
        etiquette(c, nom, x, 1560, icone="z" if q == "sommeil" else "x")
    # Insomnie retient Sommeil par le bras
    c.drawLine(600, 1250, 450, 1220, T.P(T.INK, 46))
    c.drawLine(600, 1250, 450, 1220, T.P((36, 36, 44), 30))
    c.drawCircle(442, 1218, 30, T.P((232, 192, 150)))
    c.drawCircle(442, 1218, 30, T.P(T.INK, 8))


def frame(c, t, t_plan):
    a, b, q, e = tour(t)
    parle = not q.endswith("~")
    q = q.rstrip("~")
    age = t - t_plan
    if q == "M":
        plan_moi(c, t, e, parle, age)
    elif q == "C":
        plan_cerveau(c, t, e, parle, age)
    else:
        plan_fin(c, t, q, e, parle)
    bandeau(c)


def render(out):
    global SYNC
    SYNC = LV.Synchro(AUDIO)
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    last, t_plan = None, 0.0
    for f in range(int(DUR * FPS)):
        t = f / FPS
        q = tour(t)[2].rstrip("~")
        key = q if q in ("M", "C") else "F"
        if key != last:
            last, t_plan = key, t
        frame(surf.getCanvas(), t, t_plan)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", AUDIO, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/cerveau_3h.mp4")
