"""Six concepts « modernes » pour Bip : rendu en volume doux, sans contour noir épais.

Tendances 2025-2026 : mascottes en 3D douce façon jouet (« plushcore »), verre dépoli et reflets (« liquid
clarity »), orbes lumineux des assistants IA, formes minimales. Tout est dessiné en 2D avec des dégradés, des
reflets, des ombres floues et des lumières de contour, pour donner l'illusion du volume.

    python -m films.persos.bip_moderne sortie.mp4
"""
import math
import subprocess
import sys

import skia

W, H, FPS = 1080, 1920, 30
DUR = 11.4


def rgb(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(a))


def P(color=(255, 255, 255), a=255, shader=None, blur=0.0, style=None, w=0.0):
    p = skia.Paint(AntiAlias=True, Color=rgb(color, a))
    if shader is not None:
        p.setShader(shader)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap(skia.Paint.kRound_Cap)
    return p


def radial(cx, cy, r, stops):
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, [rgb(c, a) for c, a, _ in stops],
                                          [p for _, _, p in stops])


def linear(p0, p1, stops):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], [rgb(c, a) for c, a, _ in stops],
                                          [p for _, _, p in stops])


def mix(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def volume(c, path, base, light, dark, bounds, rim=(255, 255, 255)):
    """Remplit une forme avec un éclairage doux : lumière en haut à gauche, ombre en bas, liseré de contour."""
    l, t, r, b = bounds
    cx, cy = (l + r) / 2, (t + b) / 2
    R = max(r - l, b - t)
    c.drawPath(path, P(shader=radial(l + (r - l) * 0.34, t + (b - t) * 0.28, R * 0.9,
                                    [(light, 255, 0.0), (base, 255, 0.55), (dark, 255, 1.0)])))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.drawOval(skia.Rect(l + (r - l) * 0.45, t + (b - t) * 0.7, r + (r - l) * 0.2, b + (b - t) * 0.3),
               P(rim, 60, blur=R * 0.06))                        # lumière de contour (en bas à droite)
    c.drawOval(skia.Rect(l + (r - l) * 0.16, t + (b - t) * 0.08, l + (r - l) * 0.52, t + (b - t) * 0.3),
               P((255, 255, 255), 120, blur=R * 0.04))           # reflet principal
    c.restore()


def shadow(c, y, w, a=70):
    c.drawOval(skia.Rect(-w, y - 9, w, y + 9), P((0, 0, 0), a, blur=12))


# ------------------------------------------------------------------------------------------------ yeux modernes
def eyes(c, cx, cy, gap, h, st, t, color=(255, 255, 255), glow=True, dark=False):
    """Deux « pilules » (style assistant IA) qui changent de forme selon l'émotion."""
    expr = st["expr"]
    lx, ly = st["look"]
    g = P(color, 150, blur=h * 0.35) if glow else None
    for side in (-1, 1):
        x, y = cx + side * gap + lx * h * 0.35, cy + ly * h * 0.25
        wdt = h * 0.46
        if st["blink"]:
            shape = skia.RRect.MakeRectXY(skia.Rect(x - wdt * 0.7, y - h * 0.06, x + wdt * 0.7, y + h * 0.06),
                                          h * 0.06, h * 0.06)
            c.drawRRect(shape, P(color))
            continue
        if expr in ("joie", "idee"):
            p = skia.Path()
            p.moveTo(x - wdt * 0.75, y + h * 0.12)
            p.quadTo(x, y - h * 0.62, x + wdt * 0.75, y + h * 0.12)
            if g:
                c.drawPath(p, P(color, 150, blur=h * 0.2, style="stroke", w=h * 0.26))
            c.drawPath(p, P(color, style="stroke", w=h * 0.2))
            continue
        if expr == "surpris":
            if g:
                c.drawCircle(x, y, h * 0.48, g)
            c.drawCircle(x, y, h * 0.44, P(color))
            continue
        hh = h * (0.28 if (expr == "reflechit" and side == 1) else 1.0)
        shape = skia.RRect.MakeRectXY(skia.Rect(x - wdt / 2, y - hh / 2, x + wdt / 2, y + hh / 2), wdt / 2, wdt / 2)
        if g:
            c.drawRRect(shape, g)
        c.drawRRect(shape, P(color))
        if dark:
            c.drawCircle(x - wdt * 0.15, y - hh * 0.22, wdt * 0.18, P((255, 255, 255), 230))


def mouth(c, cx, cy, s, st, t, color=(255, 255, 255)):
    expr = st["expr"]
    if expr in ("joie", "idee"):
        p = skia.Path()
        p.moveTo(cx - s, cy)
        p.quadTo(cx, cy + s * 1.1, cx + s, cy)
        c.drawPath(p, P(color, style="stroke", w=s * 0.32))
    elif expr == "surpris":
        c.drawCircle(cx, cy + s * 0.3, s * 0.34, P(color, style="stroke", w=s * 0.24))
    elif expr == "parle":
        o = s * (0.2 + 0.5 * abs(math.sin(t * 14)))
        c.drawRoundRect(skia.Rect(cx - s * 0.5, cy - o / 2, cx + s * 0.5, cy + o / 2), o / 2, o / 2, P(color))


# ------------------------------------------------------------------------------------------------ les concepts
def orbe(c, st, t):
    """1. Orbe IA : sphère aux couleurs qui tournent lentement, deux yeux-lumière."""
    shadow(c, 190, 90, 90)
    c.drawCircle(0, 0, 175, P((140, 90, 255), 110, blur=60))
    path = skia.Path()
    path.addCircle(0, 0, 140)
    rot = t * 40
    sweep = skia.GradientShader.MakeSweep(0, 0, [rgb(x) for x in ((90, 120, 255), (190, 90, 255), (255, 110, 190),
                                                                  (90, 220, 255), (90, 120, 255))],
                                          localMatrix=skia.Matrix.RotateDeg(rot))
    c.drawPath(path, P(shader=sweep))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.drawCircle(-30, -40, 150, P((255, 255, 255), 90, blur=40))
    c.drawCircle(40, 60, 120, P((20, 10, 60), 120, blur=40))
    c.drawOval(skia.Rect(-90, -118, 10, -70), P((255, 255, 255), 170, blur=10))
    c.restore()
    c.drawCircle(0, 0, 140, P((255, 255, 255), 120, style="stroke", w=3))
    eyes(c, 0, -6, 38, 64, st, t)
    mouth(c, 0, 50, 22, st, t)


def galet(c, st, t):
    """2. Galet de verre dépoli : lumières colorées qui bougent derrière la vitre."""
    shadow(c, 190, 110)
    rect = skia.Rect(-150, -130, 150, 150)
    rr = skia.RRect.MakeRectXY(rect, 120, 110)
    c.save()
    c.clipRRect(rr, doAntiAlias=True)
    for k, col in enumerate(((255, 110, 170), (110, 170, 255), (140, 255, 210))):
        a = t * 0.7 + k * 2.1
        c.drawCircle(70 * math.cos(a), 10 + 60 * math.sin(a * 1.3), 110, P(col, 230, blur=45))
    c.drawRRect(rr, P((255, 255, 255), 95))                       # le verre dépoli
    c.drawRect(skia.Rect(-150, -130, 150, -40), P(shader=linear((0, -130), (0, -40),
                                                                [((255, 255, 255), 120, 0.0),
                                                                 ((255, 255, 255), 0, 1.0)])))
    c.restore()
    c.drawRRect(rr, P((255, 255, 255), 220, style="stroke", w=4))
    eyes(c, 0, 0, 44, 70, st, t, color=(30, 30, 60), glow=False, dark=True)
    mouth(c, 0, 62, 24, st, t, color=(30, 30, 60))


def peluche(c, st, t):
    """3. Robot « peluche » en 3D douce : mat, pastel, joues rondes, sans contour."""
    shadow(c, 200, 100)
    for side in (-1, 1):                                          # petites oreilles rondes
        ear = skia.Path()
        ear.addCircle(side * 150, -10, 38)
        volume(c, ear, (255, 170, 150), (255, 210, 195), (220, 120, 110), (side * 150 - 38, -48, side * 150 + 38, 28))
    body = skia.Path()
    body.addRRect(skia.RRect.MakeRectXY(skia.Rect(-70, 100, 70, 190), 45, 45))
    volume(c, body, (170, 200, 255), (215, 230, 255), (120, 150, 225), (-70, 100, 70, 190))
    head = skia.Path()
    head.addRRect(skia.RRect.MakeRectXY(skia.Rect(-150, -130, 150, 120), 110, 100))
    volume(c, head, (175, 205, 255), (225, 238, 255), (115, 145, 220), (-150, -130, 150, 120))
    face = skia.RRect.MakeRectXY(skia.Rect(-105, -80, 105, 72), 70, 64)
    c.drawRRect(face, P(shader=linear((0, -80), (0, 72), [((52, 58, 110), 255, 0.0), ((28, 30, 70), 255, 1.0)])))
    c.drawRRect(face, P((255, 255, 255), 50, style="stroke", w=3))
    eyes(c, 0, -10, 40, 58, st, t, color=(150, 255, 240))
    mouth(c, 0, 40, 20, st, t, color=(150, 255, 240))
    for side in (-1, 1):
        c.drawOval(skia.Rect(side * 118 - 18, 58, side * 118 + 18, 80), P((255, 140, 170), 150, blur=4))
    ant = skia.Path()
    ant.addCircle(4 * math.sin(t * 4), -168, 18)
    c.drawLine(0, -130, 4 * math.sin(t * 4), -160, P((140, 160, 220), style="stroke", w=8))
    volume(c, ant, (255, 200, 90), (255, 235, 170), (230, 150, 50), (-18, -186, 18, -150))


def visiere(c, st, t):
    """4. Visière : coque blanche brillante, grande visière noire laquée où s'allument les yeux."""
    shadow(c, 200, 100)
    head = skia.Path()
    head.addRRect(skia.RRect.MakeRectXY(skia.Rect(-150, -140, 150, 130), 130, 120))
    volume(c, head, (238, 240, 246), (255, 255, 255), (170, 176, 196), (-150, -140, 150, 130), rim=(170, 210, 255))
    visor = skia.Path()
    visor.addRRect(skia.RRect.MakeRectXY(skia.Rect(-128, -70, 128, 60), 65, 65))
    c.drawPath(visor, P(shader=linear((0, -70), (0, 60), [((40, 44, 60), 255, 0.0), ((6, 7, 14), 255, 1.0)])))
    c.save()
    c.clipPath(visor, doAntiAlias=True)
    eyes(c, 0, -4, 46, 60, st, t, color=(255, 255, 255))
    mouth(c, 0, 38, 18, st, t)
    c.drawOval(skia.Rect(-120, -80, 60, -30), P((255, 255, 255), 40))          # reflet laqué
    c.restore()
    for side in (-1, 1):                                         # deux voyants latéraux
        c.drawCircle(side * 146, 0, 9, P((255, 120, 90) if st["expr"] != "neutre" else (120, 220, 255)))
    ring = skia.Path()
    ring.addCircle(0, 175, 30)
    volume(c, ring, (238, 240, 246), (255, 255, 255), (170, 176, 196), (-30, 145, 30, 205))


def holo(c, st, t):
    """5. Hologramme : tête de lumière projetée par un petit socle, lignes de balayage, léger scintillement."""
    base = skia.Path()
    base.addOval(skia.Rect(-80, 175, 80, 205))
    volume(c, base, (60, 70, 100), (110, 120, 160), (25, 30, 50), (-80, 175, 80, 205))
    cone = skia.Path()
    cone.moveTo(-60, 185)
    cone.lineTo(-150, 30)
    cone.lineTo(150, 30)
    cone.lineTo(60, 185)
    cone.close()
    c.drawPath(cone, P(shader=linear((0, 185), (0, 30), [((90, 230, 255), 90, 0.0), ((90, 230, 255), 0, 1.0)])))
    flick = 0.85 + 0.15 * math.sin(t * 37) * math.sin(t * 13)
    head = skia.Path()
    head.addRRect(skia.RRect.MakeRectXY(skia.Rect(-140, -140, 140, 110), 110, 100))
    c.drawPath(head, P((90, 230, 255), 70 * flick))
    c.save()
    c.clipPath(head, doAntiAlias=True)
    off = (t * 40) % 10
    for y in range(-150, 120, 10):
        c.drawLine(-150, y + off, 150, y + off, P((200, 250, 255), 50 * flick, style="stroke", w=2))
    c.restore()
    c.drawPath(head, P((90, 230, 255), 120, blur=14, style="stroke", w=10))
    c.drawPath(head, P((200, 250, 255), 230 * flick, style="stroke", w=3))
    eyes(c, 0, -14, 44, 62, st, t, color=(220, 255, 255))
    mouth(c, 0, 44, 22, st, t, color=(220, 255, 255))


def chrome(c, st, t):
    """6. Chrome liquide : goutte de métal poli qui ondule, reflets de studio."""
    shadow(c, 190, 110)
    path = skia.Path()
    n = 64
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        r = 140 + 3 * math.sin(3 * a + t * 2.2) + 2 * math.sin(5 * a - t * 3)
        q = (r * math.cos(a) * 1.05, r * math.sin(a) * 0.95 + 10)
        path.moveTo(*q) if i == 0 else path.lineTo(*q)
    path.close()
    c.drawPath(path, P(shader=linear((0, -140), (0, 160), [((250, 252, 255), 255, 0.0), ((170, 180, 200), 255, 0.3),
                                                          ((60, 66, 86), 255, 0.52), ((210, 220, 240), 255, 0.62),
                                                          ((120, 130, 150), 255, 0.85), ((230, 235, 245), 255, 1.0)])))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.drawOval(skia.Rect(-110, -120, -10, -70), P((255, 255, 255), 230, blur=6))
    c.drawOval(skia.Rect(40, 40, 170, 120), P((255, 170, 220), 90, blur=20))   # reflet coloré
    c.restore()
    eyes(c, 0, -10, 44, 64, st, t, color=(20, 22, 34), glow=False, dark=True)
    mouth(c, 0, 50, 22, st, t, color=(20, 22, 34))


CONCEPTS = [("Orbe IA", orbe), ("Galet de verre", galet), ("Peluche 3D", peluche), ("Visière", visiere),
            ("Hologramme", holo), ("Chrome liquide", chrome)]
SEQ = [(0.0, "neutre"), (1.8, "joie"), (3.6, "reflechit"), (5.2, "parle"), (6.8, "surpris"), (8.4, "idee"),
       (9.9, "neutre")]


def state(t, i):
    cur = SEQ[0]
    for s in SEQ:
        if t >= s[0]:
            cur = s
    t0, expr = cur
    a = t - t0
    look = (0.0, 0.0)
    if expr == "reflechit":
        look = (0.6 * ease(a / 0.3), -0.6 * ease(a / 0.3))
    blink = (t + i * 0.4) % 3.1 < 0.12 and expr in ("neutre", "parle")
    return dict(expr=expr, look=look, blink=blink, a=a)


def draw(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P(shader=linear((0, 0), (0, H), [((22, 20, 44), 255, 0.0),
                                                                       ((40, 26, 70), 255, 0.6),
                                                                       ((18, 30, 60), 255, 1.0)])))
    c.drawCircle(200, 300, 400, P((120, 80, 255), 40, blur=120))
    c.drawCircle(900, 1500, 450, P((60, 200, 255), 35, blur=140))
    f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 54)
    c.drawString("Bip, version moderne ?", 220, 110, f, P((255, 255, 255)))
    for i, (name, fn) in enumerate(CONCEPTS):
        cx = 270 + (i % 2) * 540
        cy = 480 + (i // 2) * 580
        card = skia.RRect.MakeRectXY(skia.Rect(cx - 250, cy - 290, cx + 250, cy + 270), 44, 44)
        c.drawRRect(card, P((255, 255, 255), 14))
        c.drawRRect(card, P((255, 255, 255), 40, style="stroke", w=2))
        st = state(t, i)
        a = st["a"]
        sq = 0.07 * math.exp(-a * 8) * math.cos(a * 28)
        hover = 8 * math.sin(t * 2.2 + i * 0.8)
        c.save()
        c.translate(cx, cy - 30 + hover)
        c.scale(0.8 * (1 + sq), 0.8 * (1 - sq))
        if st["expr"] == "reflechit":
            c.rotate(6 * ease(a / 0.3))
        fn(c, st, t + i * 0.3)
        c.restore()
        lf = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 34)
        label = f"{i + 1}. {name}"
        c.drawString(label, cx - lf.measureText(label) / 2, cy + 240, lf, P((255, 255, 255), 235))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/bip_moderne.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        draw(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    for tt, name in ((0.9, ""), (2.5, "_joie")):
        s = skia.Surface(W, H)
        draw(s.getCanvas(), tt)
        s.makeImageSnapshot().save(out.replace(".mp4", f"{name}.png"))
    print(out)


if __name__ == "__main__":
    main()
