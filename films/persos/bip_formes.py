"""Six silhouettes pour Bip (même visage-écran, mêmes mains flottantes, mêmes expressions).

    python -m films.persos.bip_formes sortie.mp4
"""
import math
import subprocess
import sys

import skia

from .bip import PALETTES, SCREEN, hand, screen_face
from .planche import OUT, ease, fill, rgb, shade, stroke, vgrad

W, H, FPS = 1080, 1920, 30
LW = 7.0
PAL = PALETTES["blanc"]


def shell_fill(y0, y1, pal=PAL):
    return fill(pal["shell"], shader=vgrad(y0, y1, shade(pal["shell"], 1.04), pal["shell2"]))


def antenna(c, x, y, t, bulb, pal=PAL, length=40):
    wob = 5 * math.sin(t * 5)
    c.drawLine(x, y, x + wob, y - length, stroke(w=LW))
    if bulb:
        c.drawCircle(x + wob, y - length - 10, 32, fill((255, 230, 120), 150, blur=16))
    c.drawCircle(x + wob, y - length - 10, 14, fill((255, 236, 140) if bulb else pal["accent"]))
    c.drawCircle(x + wob, y - length - 10, 14, stroke(w=LW * 0.8))


def screen(c, path, cx, cy, k, expr, t, blink, text, pal=PAL):
    c.drawPath(path, fill(SCREEN, shader=vgrad(cy - 90 * k, cy + 90 * k, (30, 38, 80), SCREEN)))
    c.drawPath(path, stroke(w=LW * 0.8))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.translate(cx, cy)
    c.scale(k, k)
    screen_face(c, expr, t, pal["glow"], (0.0, 0.0), blink, text)
    c.restore()
    c.save()
    c.clipPath(path, doAntiAlias=True)
    b = path.getBounds()
    c.drawOval(skia.Rect(b.left() + b.width() * 0.08, b.top() + b.height() * 0.06, b.left() + b.width() * 0.55,
                         b.top() + b.height() * 0.3), fill((255, 255, 255), 30))
    c.restore()


def flame(c, y, t, pal=PAL, w=20):
    fl = 1 + 0.18 * math.sin(t * 30) + 0.1 * math.sin(t * 47)
    p = skia.Path()
    p.moveTo(-w, y)
    p.quadTo(0, y + 64 * fl, w, y)
    p.close()
    c.drawPath(p, fill(pal["glow"], 150, blur=10))
    c.drawPath(p, fill((255, 255, 255), 210))


def hands(c, t, pose, spread=170, y=110):
    for side in (-1, 1):
        if pose == "haut":
            hand(c, side * (spread + 20), -80 + 10 * math.sin(t * 12 + side), PAL, "ouverte", side * 10)
        elif pose == "pointe" and side == 1:
            hand(c, spread + 20, 0, PAL, "pointe", 75)
        else:
            hand(c, side * spread, y + 5 * math.sin(t * 2.4 + side), PAL, "poing")


# ------------------------------------------------------------------------------------------------ les formes
def goutte(c, t, e):
    """1. Goutte : un seul bloc, tête ronde qui s'effile vers le réacteur."""
    flame(c, 214, t, w=14)
    body = skia.Path()
    body.moveTo(0, 222)
    body.cubicTo(-70, 200, -150, 90, -150, -10)
    body.cubicTo(-150, -110, -80, -150, 0, -150)
    body.cubicTo(80, -150, 150, -110, 150, -10)
    body.cubicTo(150, 90, 70, 200, 0, 222)
    body.close()
    c.drawPath(body, shell_fill(-150, 222))
    c.drawPath(body, stroke())
    c.drawCircle(0, 150, 12, fill(PAL["accent"]))
    c.drawCircle(0, 150, 12, stroke(w=LW * 0.7))
    antenna(c, 0, -150, t, e["bulb"])
    scr = skia.Path()
    scr.addOval(skia.Rect(-112, -112, 112, 64))
    screen(c, scr, 0, -24, 0.95, e["expr"], t, e["blink"], e["text"])
    hands(c, t, e["hands"], 190, 120)


def bulle(c, t, e):
    """2. Bulle : tête-sphère vitrée (l'écran EST la tête), col, petit corps."""
    flame(c, 200, t)
    body = skia.Rect(-56, 116, 56, 190)
    c.drawRoundRect(body, 34, 34, shell_fill(116, 190))
    c.drawRoundRect(body, 34, 34, stroke())
    c.drawCircle(0, 152, 11, fill(PAL["accent"]))
    c.drawCircle(0, 152, 11, stroke(w=LW * 0.7))
    collar = skia.Rect(-92, 86, 92, 124)
    c.drawRoundRect(collar, 19, 19, fill(PAL["accent"]))
    c.drawRoundRect(collar, 19, 19, stroke())
    antenna(c, 0, -136, t, e["bulb"], length=32)
    scr = skia.Path()
    scr.addCircle(0, -24, 124)
    screen(c, scr, 0, -20, 1.05, e["expr"], t, e["blink"], e["text"])
    c.drawCircle(0, -24, 124, stroke(shade(PAL["shell2"], 1.0), 12))
    c.drawCircle(0, -24, 124, stroke(w=LW * 0.9))
    c.drawOval(skia.Rect(-92, -120, -40, -84), fill((255, 255, 255), 150))
    hands(c, t, e["hands"], 170, 150)


def oeuf(c, t, e):
    """3. Œuf : silhouette lisse d'une seule pièce, bandeau-écran horizontal."""
    flame(c, 208, t, w=16)
    egg = skia.Path()
    egg.moveTo(0, -170)
    egg.cubicTo(110, -170, 150, -30, 140, 70)
    egg.cubicTo(130, 170, 60, 212, 0, 212)
    egg.cubicTo(-60, 212, -130, 170, -140, 70)
    egg.cubicTo(-150, -30, -110, -170, 0, -170)
    egg.close()
    c.drawPath(egg, shell_fill(-170, 212))
    c.drawPath(egg, stroke())
    c.drawOval(skia.Rect(-100, -150, -50, -110), fill((255, 255, 255), 170))
    scr = skia.Path()
    scr.addRRect(skia.RRect.MakeRectXY(skia.Rect(-122, -76, 122, 58), 60, 60))
    screen(c, scr, 0, -12, 0.9, e["expr"], t, e["blink"], e["text"])
    c.drawCircle(0, 140, 12, fill(PAL["accent"]))
    c.drawCircle(0, 140, 12, stroke(w=LW * 0.7))
    antenna(c, 0, -170, t, e["bulb"], length=30)
    hands(c, t, e["hands"], 190, 120)


def tele(c, t, e):
    """4. Télé rétro : écran bombé, deux antennes en V, un bouton sur le côté."""
    flame(c, 196, t)
    body = skia.Rect(-60, 118, 60, 186)
    c.drawRoundRect(body, 30, 30, shell_fill(118, 186))
    c.drawRoundRect(body, 30, 30, stroke())
    for side in (-1, 1):
        c.drawLine(side * 30, -120, side * 72 + 4 * math.sin(t * 5), -196, stroke(w=LW * 0.9))
        c.drawCircle(side * 72 + 4 * math.sin(t * 5), -198, 10, fill((255, 236, 140) if e["bulb"] else PAL["accent"]))
        c.drawCircle(side * 72 + 4 * math.sin(t * 5), -198, 10, stroke(w=LW * 0.7))
    head = skia.Rect(-160, -124, 160, 118)
    c.drawRoundRect(head, 58, 58, fill(PAL["accent"], shader=vgrad(-124, 118, shade(PAL["accent"], 1.1),
                                                                   shade(PAL["accent"], 0.8))))
    c.drawRoundRect(head, 58, 58, stroke())
    scr = skia.Path()
    scr.addRRect(skia.RRect.MakeRectXY(skia.Rect(-128, -96, 92, 90), 50, 50))
    screen(c, scr, -18, -4, 0.95, e["expr"], t, e["blink"], e["text"])
    for k, y in enumerate((-40, 20)):
        c.drawCircle(128, y, 13, fill(shade(PAL["accent"], 0.7)))
        c.drawCircle(128, y, 13, stroke(w=LW * 0.7))
    hands(c, t, e["hands"], 196, 150)


def chat(c, t, e):
    """5. Chat-robot : tête arrondie à oreilles pointues, petites moustaches lumineuses."""
    flame(c, 200, t)
    body = skia.Rect(-56, 116, 56, 190)
    c.drawRoundRect(body, 34, 34, shell_fill(116, 190))
    c.drawRoundRect(body, 34, 34, stroke())
    for side in (-1, 1):
        ear = skia.Path()
        tw = 4 * math.sin(t * 3 + side)
        ear.moveTo(side * 70, -110)
        ear.lineTo(side * 128 + tw, -196)
        ear.lineTo(side * 142, -70)
        ear.close()
        c.drawPath(ear, shell_fill(-196, -70))
        c.drawPath(ear, stroke())
        inner = skia.Path()
        inner.moveTo(side * 90, -104)
        inner.lineTo(side * 124 + tw * 0.8, -166)
        inner.lineTo(side * 130, -94)
        inner.close()
        c.drawPath(inner, fill(PAL["accent"]))
    head = skia.Rect(-150, -130, 150, 118)
    c.drawRoundRect(head, 90, 80, shell_fill(-130, 118))
    c.drawRoundRect(head, 90, 80, stroke())
    scr = skia.Path()
    scr.addRRect(skia.RRect.MakeRectXY(skia.Rect(-116, -88, 116, 84), 70, 64))
    screen(c, scr, 0, -8, 0.95, e["expr"], t, e["blink"], e["text"])
    for side in (-1, 1):
        for k in (-1, 1):
            c.drawLine(side * 150, 40 + k * 12, side * 186, 34 + k * 18, stroke(PAL["glow"], 5))
    hands(c, t, e["hands"], 190, 150)


def dome(c, t, e):
    """6. Dôme : casque en demi-sphère, visière large, base plate qui flotte."""
    flame(c, 150, t, w=26)
    base = skia.Rect(-150, 70, 150, 140)
    c.drawRoundRect(base, 34, 34, fill(PAL["accent"], shader=vgrad(70, 140, PAL["accent"],
                                                                   shade(PAL["accent"], 0.75))))
    c.drawRoundRect(base, 34, 34, stroke())
    for k in range(-2, 3):
        c.drawCircle(k * 50, 104, 7, fill((255, 255, 255), 150))
    dome_p = skia.Path()
    dome_p.moveTo(-160, 80)
    dome_p.cubicTo(-160, -150, 160, -150, 160, 80)
    dome_p.close()
    c.drawPath(dome_p, shell_fill(-120, 80))
    c.drawPath(dome_p, stroke())
    antenna(c, 60, -66, t, e["bulb"], length=40)
    scr = skia.Path()
    scr.addRRect(skia.RRect.MakeRectXY(skia.Rect(-112, -26, 112, 64), 40, 40))
    screen(c, scr, 0, 18, 0.62, e["expr"], t, e["blink"], e["text"])
    hands(c, t, e["hands"], 196, 20)


SHAPES = [("1. Goutte", goutte), ("2. Bulle", bulle), ("3. Œuf", oeuf), ("4. Télé rétro", tele),
          ("5. Chat-robot", chat), ("6. Dôme", dome)]
SEQ = [(0.0, dict(expr="neutre", hands="repos", bulb=False, text=None)),
       (1.8, dict(expr="joie", hands="haut", bulb=False, text=None)),
       (3.6, dict(expr="reflechit", hands="repos", bulb=False, text=None)),
       (5.2, dict(expr="idee", hands="haut", bulb=True, text=None)),
       (6.8, dict(expr="neutre", hands="pointe", bulb=False, text="180°")),
       (8.4, dict(expr="surpris", hands="haut", bulb=False, text=None)),
       (9.8, dict(expr="amour", hands="repos", bulb=False, text=None))]
DUR = 11.4


def draw(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), fill((0, 0, 0), shader=vgrad(0, H, (255, 236, 214), (214, 226, 255))))
    f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 54)
    c.drawString("Quelle forme pour Bip ?", 210, 110, f, fill(OUT))
    cur = SEQ[0]
    for s in SEQ:
        if t >= s[0]:
            cur = s
    t0, st = cur
    a = t - t0
    e = dict(st, blink=(t % 3.1) < 0.12 and st["expr"] == "neutre")
    sq = 0.08 * math.exp(-a * 8) * math.cos(a * 30)
    for i, (name, fn) in enumerate(SHAPES):
        cx = 270 + (i % 2) * 540
        cy = 470 + (i // 2) * 580
        hover = 7 * math.sin(t * 2.4 + i * 0.7)
        c.drawOval(skia.Rect(cx - 70, cy + 190, cx + 70, cy + 204), fill((0, 0, 0), 50, blur=8))
        c.save()
        c.translate(cx, cy - 20 + hover)
        c.scale(0.82 * (1 + sq), 0.82 * (1 - sq))
        if st["expr"] == "reflechit":
            c.rotate(7 * ease(a / 0.3))
        fn(c, t + i * 0.3, e)
        c.restore()
        lf = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 36)
        wdt = lf.measureText(name)
        c.drawString(name, cx - wdt / 2, cy + 250, lf, fill(OUT))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/bip_formes.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        draw(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    s = skia.Surface(W, H)
    draw(s.getCanvas(), 0.9)
    s.makeImageSnapshot().save(out.replace(".mp4", ".png"))
    s2 = skia.Surface(W, H)
    draw(s2.getCanvas(), 2.4)
    s2.makeImageSnapshot().save(out.replace(".mp4", "_joie.png"))
    print(out)


if __name__ == "__main__":
    main()
