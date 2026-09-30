"""Bip, version 2 : le robot mascotte des vidéos éducatives.

Choix de conception (tous pensés pour être animés sans défaut) :
  • grosse tête, petit corps (proportions « chibi ») : attachant et lisible sur un téléphone ;
  • il flotte sur un petit réacteur : jamais de jambes à animer, un flottement toujours juste ;
  • des mains flottantes, sans bras : il peut montrer, saluer, compter, sans coude à articuler ;
  • son visage est un écran : les yeux changent de forme (ronds, joie, étoiles, cœurs, spirales) et l'écran peut
    afficher un symbole ou un nombre — idéal pour enseigner (« 180° » s'affiche sur son visage) ;
  • une antenne-ampoule qui s'allume quand il a une idée ; deux oreilles-haut-parleurs qui vibrent quand il parle.

    python -m films.persos.bip sortie.mp4
"""
import math
import subprocess
import sys

import skia

from .planche import OUT, ease, fill, rgb, shade, stroke, vgrad

W, H, FPS = 1080, 1920, 30
LW = 7.0
SCREEN = (18, 24, 52)
PALETTES = {
    "blanc": dict(shell=(246, 244, 240), shell2=(206, 208, 220), accent=(255, 128, 64), glow=(110, 240, 255)),
    "bleu": dict(shell=(130, 170, 255), shell2=(80, 110, 220), accent=(255, 205, 70), glow=(120, 255, 220)),
    "menthe": dict(shell=(170, 240, 210), shell2=(90, 190, 160), accent=(255, 110, 140), glow=(255, 240, 150)),
}


def star_path(x, y, r, k=0.45, n=5, rot=-math.pi / 2):
    p = skia.Path()
    for i in range(2 * n):
        rr = r if i % 2 == 0 else r * k
        a = rot + i * math.pi / n
        q = (x + rr * math.cos(a), y + rr * math.sin(a))
        p.moveTo(*q) if i == 0 else p.lineTo(*q)
    p.close()
    return p


def heart_path(x, y, r):
    p = skia.Path()
    p.moveTo(x, y + r * 0.9)
    p.cubicTo(x - r * 1.4, y - r * 0.1, x - r * 0.7, y - r * 1.2, x, y - r * 0.45)
    p.cubicTo(x + r * 0.7, y - r * 1.2, x + r * 1.4, y - r * 0.1, x, y + r * 0.9)
    p.close()
    return p


def screen_face(c, expr, t, glow, look=(0.0, 0.0), blink=False, text=None):
    """Tout se passe sur l'écran : yeux qui changent de forme, bouche, symboles."""
    g = fill(glow)
    halo = fill(glow, 120, blur=8)
    if text:                                                    # l'écran affiche une information
        f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 58)
        wdt = f.measureText(text)
        c.drawString(text, -wdt / 2, 22, f, halo)
        c.drawString(text, -wdt / 2, 22, f, g)
        return
    for side in (-1, 1):
        ex, ey = side * 42 + look[0] * 10, -12 + look[1] * 8
        if blink:
            c.drawRoundRect(skia.Rect(ex - 18, ey - 3, ex + 18, ey + 3), 3, 3, g)
        elif expr == "joie":
            p = skia.Path()
            p.moveTo(ex - 18, ey + 8)
            p.quadTo(ex, ey - 22, ex + 18, ey + 8)
            c.drawPath(p, stroke(glow, 9))
        elif expr == "idee":
            c.drawPath(star_path(ex, ey, 24), halo)
            c.drawPath(star_path(ex, ey, 22), g)
        elif expr == "amour":
            s = 1 + 0.12 * math.sin(t * 12)
            c.drawPath(heart_path(ex, ey, 18 * s), halo)
            c.drawPath(heart_path(ex, ey, 18 * s), g)
        elif expr == "etourdi":
            p = skia.Path()
            for k in range(40):
                a = k * 0.45 + t * 8 * side
                r = k * 0.55
                q = (ex + r * math.cos(a), ey + r * math.sin(a))
                p.moveTo(*q) if k == 0 else p.lineTo(*q)
            c.drawPath(p, stroke(glow, 4))
        elif expr == "surpris":
            c.drawCircle(ex, ey, 22, stroke(glow, 7))
            c.drawCircle(ex, ey, 7, g)
        elif expr == "reflechit":
            if side == 1:                                       # un œil plissé, l'autre grand ouvert
                c.drawRoundRect(skia.Rect(ex - 18, ey - 2, ex + 18, ey + 8), 5, 5, g)
            else:
                c.drawRoundRect(skia.Rect(ex - 16, ey - 20, ex + 16, ey + 20), 12, 12, g)
        else:
            c.drawRoundRect(skia.Rect(ex - 16, ey - 22, ex + 16, ey + 22), 14, 14, halo)
            c.drawRoundRect(skia.Rect(ex - 16, ey - 22, ex + 16, ey + 22), 14, 14, g)
            c.drawCircle(ex - 5, ey - 10, 5, fill((255, 255, 255), 220))
    # bouche
    if expr in ("joie", "idee", "amour"):
        p = skia.Path()
        p.moveTo(-22, 26)
        p.quadTo(0, 50, 22, 26)
        c.drawPath(p, stroke(glow, 7))
    elif expr == "surpris":
        c.drawCircle(0, 36, 9, stroke(glow, 6))
    elif expr == "reflechit":
        dots = int(t * 3) % 4                                   # « chargement… »
        for k in range(3):
            c.drawCircle(-18 + k * 18, 36, 5, fill(glow, 255 if k < dots else 70))
    elif expr == "parle":
        o = 6 + 10 * abs(math.sin(t * 14))
        c.drawRoundRect(skia.Rect(-16, 30 - o / 2, 16, 30 + o / 2), 8, 8, g)
    elif expr == "etourdi":
        p = skia.Path()
        p.moveTo(-22, 34)
        for k in range(1, 7):
            p.lineTo(-22 + k * 7.3, 34 + (6 if k % 2 else -6))
        c.drawPath(p, stroke(glow, 5))
    else:
        c.drawRoundRect(skia.Rect(-14, 30, 14, 36), 3, 3, g)


def hand(c, x, y, pal, pose="ouverte", rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.drawCircle(0, 0, 20, fill(pal["shell"], shader=vgrad(-20, 20, pal["shell"], pal["shell2"])))
    c.drawCircle(0, 0, 20, stroke(w=LW * 0.8))
    if pose == "pointe":                                        # index tendu, bien visible
        f = skia.Rect(-8, -52, 8, -10)
        c.drawRoundRect(f, 8, 8, fill(pal["shell"]))
        c.drawRoundRect(f, 8, 8, stroke(w=LW * 0.8))
        c.drawCircle(0, 0, 14, fill(pal["shell"]))
    if pose == "ouverte":
        for k in (-1, 0, 1):
            c.drawLine(k * 7, -14, k * 8, -22, stroke(w=LW * 0.7))
    c.restore()


def draw_bip(c, t, expr="neutre", pal=PALETTES["blanc"], hands=("repos", "repos"), look=(0.0, 0.0),
             blink=False, sq=0.0, tilt=0.0, bulb=False, text=None, talking=False):
    """Bip dessiné autour de (0, 0) = centre de la tête ; la base du réacteur est vers +200."""
    hover = 7 * math.sin(t * 2.4)
    # ombre au sol (elle respire avec le flottement)
    k = 1 - hover / 60
    c.drawOval(skia.Rect(-80 * k, 262, 80 * k, 280), fill((0, 0, 0), 55 * k, blur=8))
    c.save()
    c.translate(0, hover)
    # réacteur : flamme douce
    fl = 1 + 0.18 * math.sin(t * 30) + 0.1 * math.sin(t * 47)
    flame = skia.Path()
    flame.moveTo(-22, 178)
    flame.quadTo(0, 178 + 70 * fl, 22, 178)
    flame.close()
    c.drawPath(flame, fill(pal["glow"], 150, blur=10))
    c.drawPath(flame, fill((255, 255, 255), 210))
    # corps (petite capsule)
    c.save()
    c.translate(0, 120)
    c.scale(1 + sq, 1 - sq)
    body = skia.Rect(-58, 0, 58, 66)
    c.drawRoundRect(body, 30, 30, fill(pal["shell"], shader=vgrad(0, 66, pal["shell"], pal["shell2"])))
    c.drawRoundRect(body, 30, 30, stroke())
    c.drawCircle(0, 30, 13, fill(pal["accent"]))                         # emblème
    c.drawCircle(0, 30, 13, stroke(w=LW * 0.7))
    c.restore()
    # tête
    c.save()
    c.rotate(tilt)
    c.scale(1 + sq * 0.6, 1 - sq * 0.6)
    # antenne-ampoule
    wob = 6 * math.sin(t * 5)
    c.drawLine(0, -118, wob, -160, stroke(w=LW))
    if bulb:
        c.drawCircle(wob, -170, 34, fill((255, 230, 120), 150, blur=16))
    c.drawCircle(wob, -170, 15, fill((255, 236, 140) if bulb else pal["accent"]))
    c.drawCircle(wob, -170, 15, stroke(w=LW * 0.8))
    # oreilles-haut-parleurs
    vib = 3 * math.sin(t * 40) if talking else 0.0
    for side in (-1, 1):
        ear = skia.Rect(side * 150 - 20 + vib * side, -40, side * 150 + 20 + vib * side, 40)
        c.drawRoundRect(ear, 14, 14, fill(pal["accent"]))
        c.drawRoundRect(ear, 14, 14, stroke())
        for k in (-1, 0, 1):
            c.drawLine(side * 150 - 8 + vib * side, k * 12, side * 150 + 8 + vib * side, k * 12,
                       stroke(w=LW * 0.5))
    head = skia.Rect(-140, -120, 140, 110)
    c.drawRoundRect(head, 70, 70, fill(pal["shell"], shader=vgrad(-120, 110, shade(pal["shell"], 1.04),
                                                                  pal["shell2"])))
    c.drawRoundRect(head, 70, 70, stroke())
    c.drawOval(skia.Rect(-110, -104, -40, -76), fill((255, 255, 255), 170))   # reflet de la coque
    # écran
    scr = skia.Rect(-110, -84, 110, 80)
    c.drawRoundRect(scr, 48, 48, fill(SCREEN, shader=vgrad(-84, 80, (30, 38, 80), SCREEN)))
    c.drawRoundRect(scr, 48, 48, stroke(w=LW * 0.8))
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(scr, 48, 48), doAntiAlias=True)
    screen_face(c, expr, t, pal["glow"], look, blink, text)
    c.drawOval(skia.Rect(-96, -76, 20, -40), fill((255, 255, 255), 28))          # reflet de la vitre
    c.restore()
    c.restore()
    # mains flottantes
    for side, pose in zip((-1, 1), hands):
        if pose == "repos":
            hand(c, side * 118, 150 + 5 * math.sin(t * 2.4 + side), pal, "poing")
        elif pose == "salut":
            hand(c, side * 190, -40 + 8 * math.sin(t * 10), pal, "ouverte", 20 * math.sin(t * 10))
        elif pose == "haut":
            hand(c, side * 190, -90 + 10 * math.sin(t * 12 + side), pal, "ouverte", side * 10)
        elif pose == "menton":
            hand(c, side * 70, 118, pal, "poing")
        elif pose == "pointe":
            hand(c, side * 192, 10 + 4 * math.sin(t * 3), pal, "pointe", side * 75)
    c.restore()


# ------------------------------------------------------------------------------------------------ présentation
SEQ = [(0.0, dict(expr="neutre", hands=("repos", "salut"), talking=False)),
       (2.2, dict(expr="parle", hands=("repos", "repos"), talking=True)),
       (4.2, dict(expr="reflechit", hands=("repos", "menton"))),
       (6.2, dict(expr="idee", hands=("haut", "haut"), bulb=True)),
       (7.8, dict(expr="parle", hands=("repos", "pointe"), talking=True)),
       (9.4, dict(expr="neutre", hands=("repos", "pointe"), text="180°")),
       (11.0, dict(expr="surpris", hands=("haut", "haut"))),
       (12.4, dict(expr="etourdi", hands=("repos", "repos"))),
       (13.8, dict(expr="amour", hands=("repos", "repos"))),
       (15.2, dict(expr="joie", hands=("haut", "haut")))]
DUR = 16.6


def frame(c, t):
    c.clear(rgb((246, 242, 236)))
    c.drawRect(skia.Rect(0, 0, W, H), fill((0, 0, 0), shader=vgrad(0, H, (255, 236, 214), (214, 226, 255))))
    title = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 64)
    c.drawString("Bip", 470, 190, title, fill(OUT))
    cur = SEQ[0]
    for s in SEQ:
        if t >= s[0]:
            cur = s
    t0, st = cur
    a = t - t0
    sq = 0.1 * math.exp(-a * 8) * math.cos(a * 30)                # petit rebond à chaque changement d'expression
    blink = (t % 3.1) < 0.12 and st["expr"] in ("neutre", "parle")
    c.save()
    c.translate(W / 2, 820)
    c.scale(1.6, 1.6)
    draw_bip(c, t, st["expr"], PALETTES["blanc"], st["hands"], blink=blink, sq=sq,
             tilt=8 * ease(a / 0.3) if st["expr"] == "reflechit" else 0.0, bulb=st.get("bulb", False),
             text=st.get("text"), talking=st.get("talking", False))
    c.restore()
    labels = {"neutre": "bonjour", "parle": "il explique", "reflechit": "il réfléchit", "idee": "il a une idée",
              "surpris": "surprise", "etourdi": "sonné", "amour": "il adore", "joie": "joie"}
    lab = "l'écran affiche le résultat" if st.get("text") else labels[st["expr"]]
    f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Normal()), 44)
    wdt = f.measureText(lab)
    c.drawString(lab, W / 2 - wdt / 2, 1560, f, fill(shade(OUT, 1.8)))


def sheet(path):
    """Planche : trois couleurs, et six expressions."""
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.drawRect(skia.Rect(0, 0, W, H), fill((0, 0, 0), shader=vgrad(0, H, (255, 236, 214), (214, 226, 255))))
    f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 46)
    c.drawString("Bip : trois couleurs", 60, 90, f, fill(OUT))
    for i, name in enumerate(("blanc", "bleu", "menthe")):
        c.save()
        c.translate(180 + i * 360, 420)
        c.scale(0.9, 0.9)
        draw_bip(c, 0.6 + i, "neutre", PALETTES[name], ("repos", "repos"))
        c.restore()
    c.drawString("… et ses expressions", 60, 810, f, fill(OUT))
    ex = [("joie", ("haut", "haut"), None, False), ("idee", ("repos", "haut"), None, True),
          ("reflechit", ("repos", "menton"), None, False), ("surpris", ("haut", "haut"), None, False),
          ("amour", ("repos", "repos"), None, False), ("neutre", ("repos", "pointe"), "180°", False)]
    for i, (e, hd, txt, b) in enumerate(ex):
        c.save()
        c.translate(190 + (i % 3) * 350, 1080 + (i // 3) * 520)
        c.scale(0.72, 0.72)
        draw_bip(c, 1.3 + i, e, PALETTES["blanc"], hd, bulb=b, text=txt)
        c.restore()
    s.makeImageSnapshot().save(path)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/bip_v2.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    sheet(out.replace(".mp4", "_planche.png"))
    print(out)


if __name__ == "__main__":
    main()
