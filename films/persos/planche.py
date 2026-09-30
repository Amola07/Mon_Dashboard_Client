"""Planche animée de six personnages candidats pour les vidéos éducatives.

Chacun est conçu pour ce que je sais animer parfaitement : formes simples et pleines, gros contour, grands yeux,
émotions lisibles sur un écran de téléphone, et des mouvements « naturels » pour leur nature (rebond, flottement,
pièces rigides d'un robot), sans bras et jambes articulés à inventer.

Chaque personnage joue la même séquence : repos → surprise (« ! ») → joie (sautille) → réflexion (« ? »), en boucle.

    python -m films.persos.planche sortie.mp4
"""
import math
import subprocess
import sys

import skia

W, H, FPS = 1080, 1920, 30
DUR = 12.0
OUT = (34, 28, 58)                                             # contour
LW = 6.0


def rgb(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(a))


def fill(c, a=255, shader=None, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=rgb(c, a))
    if shader is not None:
        p.setShader(shader)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(c=OUT, w=LW, a=255):
    p = skia.Paint(AntiAlias=True, Color=rgb(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def vgrad(y0, y1, c0, c1):
    return skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [rgb(c0), rgb(c1)])


def shade(c, k):
    return tuple(max(0, min(255, v * k)) for v in c)


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# ------------------------------------------------------------------------------------------------ état commun
def state(t, offset=0.0):
    """Expression, émotion, sautillement, écrasement, inclinaison, regard, clignement."""
    t = (t + offset) % DUR
    s = dict(expr="neutre", emote=None, emote_age=0.0, y=0.0, sq=0.0, tilt=0.0, look=(0.0, 0.0), blink=False, arms=0.0)
    bob = math.sin(t * 2 * math.pi * 0.7)
    s["y"] = -4 * bob                                           # respiration
    s["sq"] = 0.02 * bob
    if 3.0 <= t < 5.0:                                          # surprise : bond vers le haut, étiré, puis retombe
        a = t - 3.0
        s["expr"], s["emote"], s["emote_age"] = "surpris", "!", a
        jump = math.exp(-a * 3.5) * math.sin(min(a, 0.6) / 0.6 * math.pi) if a < 0.6 else 0.0
        s["y"] = -70 * jump
        s["sq"] = -0.16 * jump + (0.12 * math.exp(-(a - 0.6) * 9) if a > 0.6 else 0.0)
        s["arms"] = 1.0
        s["look"] = (0.0, -0.3)
    elif 5.0 <= t < 8.0:                                        # joie : petits sauts avec écrasement à l'atterrissage
        a = t - 5.0
        s["expr"], s["emote"], s["emote_age"] = "joie", "etincelles", a
        p = (a % 0.5) / 0.5
        s["y"] = -46 * 4 * p * (1 - p)
        s["sq"] = 0.18 * math.exp(-p * 12) - 0.08 * math.sin(math.pi * p)
        s["arms"] = 2.0 + math.sin(a * 16)
    elif 8.0 <= t < 11.0:                                       # réflexion : tête penchée, regard en haut
        a = t - 8.0
        s["expr"], s["emote"], s["emote_age"] = "reflechit", "?", a
        k = ease(a / 0.3)
        s["tilt"] = 10 * k
        s["look"] = (0.6 * k, -0.7 * k)
        s["arms"] = 3.0
    elif t >= 11.0:
        s["look"] = (0.0, 0.0)
    s["blink"] = (t % 3.3) < 0.12 and s["expr"] in ("neutre", "reflechit")
    return s


# ------------------------------------------------------------------------------------------------ visage
def eyes(c, x, y, r, gap, st, pupil=OUT, robot=False):
    expr, look = st["expr"], st["look"]
    arc = (120, 255, 230) if robot else OUT                    # sur l'écran du robot, les traits sont lumineux
    for side in (-1, 1):
        ex = x + side * gap
        if st["blink"] or expr == "joie":
            path = skia.Path()
            path.moveTo(ex - r * 0.8, y + r * 0.1)
            if expr == "joie":
                path.quadTo(ex, y - r * 0.9, ex + r * 0.8, y + r * 0.1)
            else:
                path.lineTo(ex + r * 0.8, y + r * 0.1)
            c.drawPath(path, stroke(arc, w=LW * 0.9))
            continue
        rr = r * (1.22 if expr == "surpris" else 1.0)
        if robot:
            rect = skia.RRect.MakeRectXY(skia.Rect(ex - rr * 0.7, y - rr, ex + rr * 0.7, y + rr), rr * 0.4, rr * 0.4)
            c.drawRRect(rect, fill((120, 255, 230)))
            c.drawRRect(rect, fill((255, 255, 255), 120, blur=6))
            continue
        c.drawOval(skia.Rect(ex - rr * 0.82, y - rr, ex + rr * 0.82, y + rr), fill((255, 255, 255)))
        c.drawOval(skia.Rect(ex - rr * 0.82, y - rr, ex + rr * 0.82, y + rr), stroke(w=LW * 0.7))
        pr = rr * (0.32 if expr == "surpris" else 0.46)
        px, py = ex + look[0] * rr * 0.35, y + look[1] * rr * 0.4
        c.drawCircle(px, py, pr, fill(pupil))
        c.drawCircle(px - pr * 0.35, py - pr * 0.4, pr * 0.33, fill((255, 255, 255)))
        if expr == "reflechit" and side == 1:                   # un sourcil levé
            c.drawLine(ex - rr * 0.7, y - rr * 1.45, ex + rr * 0.7, y - rr * 1.7, stroke(w=LW * 0.8))


def mouth(c, x, y, w, st, color=OUT):
    expr = st["expr"]
    if expr == "surpris":
        c.drawOval(skia.Rect(x - w * 0.18, y - w * 0.12, x + w * 0.18, y + w * 0.3), fill((90, 30, 50)))
        c.drawOval(skia.Rect(x - w * 0.18, y - w * 0.12, x + w * 0.18, y + w * 0.3), stroke(w=LW * 0.7))
    elif expr == "joie":
        p = skia.Path()
        p.moveTo(x - w * 0.45, y - w * 0.05)
        p.quadTo(x, y + w * 0.75, x + w * 0.45, y - w * 0.05)
        p.close()
        c.drawPath(p, fill((200, 60, 90)))
        c.drawPath(p, stroke(w=LW * 0.7))
    elif expr == "reflechit":
        p = skia.Path()
        p.moveTo(x - w * 0.22, y + w * 0.05)
        p.quadTo(x + w * 0.02, y - w * 0.06, x + w * 0.26, y + w * 0.02)
        c.drawPath(p, stroke(w=LW * 0.8))
    else:
        p = skia.Path()
        p.moveTo(x - w * 0.28, y)
        p.quadTo(x, y + w * 0.22, x + w * 0.28, y)
        c.drawPath(p, stroke(w=LW * 0.8))


def emote(c, x, y, st, color=(255, 255, 255)):
    kind, age = st["emote"], st["emote_age"]
    if not kind:
        return
    pop = min(1.0, age / 0.15) * (1 + 0.3 * math.exp(-age * 7) * math.sin(age * 35))
    if kind in ("!", "?"):
        f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), max(1.0, 64 * pop))
        c.drawString(kind, x - 2, y + 2, f, fill(OUT))
        c.drawString(kind, x - 6, y - 2, f, fill((255, 214, 80)))
    else:
        for i in range(4):
            a = age * 2.5 + i * math.pi / 2
            sx, sy = x + 36 * math.cos(a), y + 20 * math.sin(a) - 10
            r = 9 + 3 * math.sin(age * 9 + i)
            p = skia.Path()
            for k in range(8):
                rr = r if k % 2 == 0 else r * 0.35
                ang = k * math.pi / 4
                q = (sx + rr * math.cos(ang), sy + rr * math.sin(ang))
                p.moveTo(*q) if k == 0 else p.lineTo(*q)
            p.close()
            c.drawPath(p, fill((255, 230, 120)))


def ground_shadow(c, y_jump, width):
    k = 1 - min(0.6, abs(y_jump) / 120)
    c.drawOval(skia.Rect(-width * k, 118, width * k, 134), fill((0, 0, 0), 60 * k, blur=6))


def squash(c, st, pivot_y=110):
    """Écrasement autour des pieds (le bas reste posé)."""
    sq = st["sq"]
    c.translate(0, pivot_y)
    c.scale(1 + sq, 1 - sq)
    c.translate(0, -pivot_y)


# ------------------------------------------------------------------------------------------------ les personnages
def piou(c, st, t):
    """Oiseau rond (famille « birb ») : corps-boule, bec, petites ailes, houppette."""
    ground_shadow(c, st["y"], 70)
    c.translate(0, st["y"])
    squash(c, st)
    c.rotate(st["tilt"])
    body = (255, 196, 60)
    # ailes
    for side in (-1, 1):
        flap = {0.0: 0, 1.0: 55, 3.0: 20}.get(st["arms"], 25 + 35 * math.sin(t * 18))
        c.save()
        c.translate(side * 78, 30)
        c.rotate(side * (-20 - flap))
        c.drawOval(skia.Rect(-18, -8, 18, 48), fill(shade(body, 0.85)))
        c.drawOval(skia.Rect(-18, -8, 18, 48), stroke())
        c.restore()
    c.drawCircle(0, 20, 88, fill(body, shader=vgrad(-70, 110, (255, 220, 110), (245, 150, 40))))
    c.drawOval(skia.Rect(-50, 40, 50, 105), fill((255, 240, 200)))          # ventre
    c.drawCircle(0, 20, 88, stroke())
    p = skia.Path()                                                          # houppette
    p.moveTo(-6, -64)
    p.quadTo(-10, -100, 10, -96)
    p.moveTo(4, -66)
    p.quadTo(16, -96, 30, -84)
    c.drawPath(p, stroke(w=LW))
    eyes(c, 0, -2, 22, 34, st)
    b = skia.Path()                                                          # bec
    b.moveTo(-14, 26)
    b.lineTo(14, 26)
    b.lineTo(0, 26 + (26 if st["expr"] == "surpris" else 18))
    b.close()
    c.drawPath(b, fill((255, 120, 50)))
    c.drawPath(b, stroke(w=LW * 0.8))
    if st["expr"] == "joie":
        c.drawLine(-14, 30, 14, 30, stroke(w=LW * 0.6))
    emote(c, 70, -100, st)


def bulle(c, st, t):
    """Blob gélatineux : le corps ondule, s'écrase et rebondit (pure physique de forme)."""
    ground_shadow(c, st["y"], 90)
    c.translate(0, st["y"])
    squash(c, st)
    c.rotate(st["tilt"] * 0.6)
    path = skia.Path()
    n = 48
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        r = 92 + 2.5 * math.sin(3 * a + t * 3) + 1.5 * math.sin(5 * a - t * 4)
        x, y = r * math.cos(a) * 1.08, r * math.sin(a) * 0.92 + 26
        if math.sin(a) > 0:
            y = min(y, 110)                                                   # base aplatie, posée
        path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
    path.close()
    c.drawPath(path, fill((0, 0, 0), shader=vgrad(-80, 110, (140, 255, 170), (30, 190, 140))))
    c.drawPath(path, stroke())
    c.drawOval(skia.Rect(-62, -44, -24, -22), fill((255, 255, 255), 170))    # reflet
    c.drawCircle(-66, -6, 7, fill((255, 255, 255), 150))
    eyes(c, 0, 10, 23, 36, st)
    mouth(c, 0, 52, 70, st)
    for side in (-1, 1):
        c.drawOval(skia.Rect(side * 60 - 13, 36, side * 60 + 13, 46), fill((255, 110, 150), 140))
    emote(c, 80, -90, st)


def ampoule(c, st, t):
    """Ampoule : l'idée incarnée — elle s'allume quand elle comprend."""
    ground_shadow(c, st["y"], 50)
    c.translate(0, st["y"])
    squash(c, st)
    c.rotate(st["tilt"])
    lit = st["expr"] in ("joie", "surpris") or (st["expr"] == "reflechit" and st["emote_age"] > 2.2)
    glow = (255, 236, 130) if lit else (225, 240, 255)
    if lit:
        c.drawCircle(0, -10, 150, fill((255, 220, 90), 90, blur=45))
        for i in range(8):                                                     # rayons
            a = i * math.pi / 4 + t * 0.8
            c.drawLine(118 * math.cos(a), -10 + 118 * math.sin(a), 146 * math.cos(a), -10 + 146 * math.sin(a),
                       stroke((255, 214, 80), 7))
    bulb = skia.Path()
    bulb.addCircle(0, -10, 86)
    c.drawPath(bulb, fill(glow, shader=vgrad(-100, 80, (255, 255, 240) if lit else (245, 250, 255), glow)))
    c.drawPath(bulb, stroke())
    base = skia.Rect(-40, 70, 40, 118)                                         # culot
    c.drawRoundRect(base, 8, 8, fill((150, 160, 185)))
    for k in range(3):
        c.drawLine(-40, 82 + k * 12, 40, 82 + k * 12, stroke(w=LW * 0.6))
    c.drawRoundRect(base, 8, 8, stroke())
    c.drawOval(skia.Rect(-58, -72, -26, -44), fill((255, 255, 255), 200))
    eyes(c, 0, -14, 21, 33, st)
    mouth(c, 0, 28, 64, st)
    emote(c, 80, -120, st)


def bip(c, st, t):
    """Robot : pièces rigides — le mouvement mécanique est naturel pour lui (antenne, bras qui pivotent)."""
    ground_shadow(c, st["y"], 80)
    c.translate(0, st["y"])
    squash(c, st)
    body = (120, 150, 255)
    # bras (rectangles arrondis qui pivotent à l'épaule)
    for side in (-1, 1):
        ang = {0.0: 10, 1.0: 70, 3.0: 20}.get(st["arms"], 120 + 25 * math.sin(t * 16))
        if st["arms"] == 3.0 and side == 1:
            ang = 150                                                          # main au menton
        c.save()
        c.translate(side * 62, 48)
        c.rotate(-side * ang)
        c.drawRoundRect(skia.Rect(-11, 0, 11, 56), 11, 11, fill(shade(body, 0.85)))
        c.drawRoundRect(skia.Rect(-11, 0, 11, 56), 11, 11, stroke())
        c.drawCircle(0, 60, 13, fill((200, 210, 230)))
        c.drawCircle(0, 60, 13, stroke())
        c.restore()
    c.drawRoundRect(skia.Rect(-58, 30, 58, 112), 18, 18, fill(body, shader=vgrad(30, 112, body, shade(body, 0.7))))
    c.drawRoundRect(skia.Rect(-58, 30, 58, 112), 18, 18, stroke())
    c.drawCircle(0, 70, 12, fill((255, 90, 120) if st["expr"] != "neutre" else (90, 230, 140)))
    c.drawCircle(0, 70, 12, stroke(w=LW * 0.7))
    c.save()
    c.rotate(st["tilt"])                                                       # la tête pivote sur son axe
    head = skia.Rect(-82, -100, 82, 30)
    c.drawRoundRect(head, 28, 28, fill(body, shader=vgrad(-100, 30, shade(body, 1.15), body)))
    c.drawRoundRect(head, 28, 28, stroke())
    screen = skia.Rect(-64, -82, 64, 12)
    c.drawRoundRect(screen, 20, 20, fill((24, 30, 60)))
    ant = -100 - 34
    c.drawLine(0, -100, 0, ant, stroke(w=LW))
    blink = (t * 2) % 1 < 0.5
    c.drawCircle(0, ant - 8, 11, fill((255, 90, 110) if blink else (255, 190, 200)))
    c.drawCircle(0, ant - 8, 11, stroke(w=LW * 0.7))
    eyes(c, 0, -40, 17, 30, st, robot=True)
    mouth(c, 0, -8, 50, st, color=(120, 255, 230))
    c.restore()
    emote(c, 88, -150, st)


def haricot(c, st, t):
    """Petit humain en forme de haricot : corps et tête d'un seul bloc, petites mains et pieds ronds sans
    coudes ni genoux (ils flottent autour du corps : rien à articuler)."""
    ground_shadow(c, st["y"], 60)
    c.translate(0, st["y"])
    squash(c, st)
    c.rotate(st["tilt"] * 0.7)
    skin = (255, 200, 170)
    shirt = (255, 90, 110)
    for side in (-1, 1):                                                       # pieds
        c.drawOval(skia.Rect(side * 30 - 22, 96, side * 30 + 22, 118), fill((60, 60, 90)))
        c.drawOval(skia.Rect(side * 30 - 22, 96, side * 30 + 22, 118), stroke(w=LW * 0.8))
    bean = skia.Path()
    bean.addRRect(skia.RRect.MakeRectXY(skia.Rect(-66, -110, 66, 104), 66, 66))
    c.save()
    c.clipPath(bean, doAntiAlias=True)
    c.drawRect(skia.Rect(-70, -120, 70, 110), fill(skin))
    c.drawRect(skia.Rect(-70, 20, 70, 110), fill(shirt))                       # tee-shirt
    c.drawRect(skia.Rect(-70, 20, 70, 32), fill(shade(shirt, 0.8)))
    c.restore()
    c.drawPath(bean, stroke())
    hair = skia.Path()                                                         # cheveux
    hair.moveTo(-60, -60)
    hair.quadTo(-50, -122, 10, -112)
    hair.quadTo(52, -110, 62, -62)
    hair.quadTo(20, -84, -60, -60)
    c.drawPath(hair, fill((70, 45, 40)))
    c.drawPath(hair, stroke(w=LW * 0.8))
    for side in (-1, 1):                                                       # mains flottantes
        if st["arms"] == 1.0:
            hx, hy = side * 104, -10
        elif st["arms"] == 3.0 and side == 1:
            hx, hy = 30, -2                                                    # main au menton
        elif st["arms"] >= 1.5:
            hx, hy = side * 96, -70 + 14 * math.sin(t * 16 + side)
        else:
            hx, hy = side * 86, 64 + 4 * math.sin(t * 4)
        c.drawCircle(hx, hy, 17, fill(skin))
        c.drawCircle(hx, hy, 17, stroke(w=LW * 0.8))
    eyes(c, 0, -36, 18, 28, st)
    mouth(c, 0, -4, 56, st)
    emote(c, 76, -130, st)


def nuage(c, st, t):
    """Petit nuage : il flotte, il n'a jamais besoin de marcher."""
    fy = -30 + 8 * math.sin(t * 2.2)
    c.drawOval(skia.Rect(-60, 118, 60, 132), fill((0, 0, 0), 35, blur=8))
    c.translate(0, fy + st["y"] * 0.8)
    squash(c, st, pivot_y=40)
    c.rotate(st["tilt"])
    if st["expr"] == "joie":                                                   # arc-en-ciel derrière lui
        for k, col in enumerate(((255, 90, 90), (255, 200, 60), (90, 200, 255))):
            c.drawArc(skia.Rect(-150 + k * 12, -40 + k * 12, 150 - k * 12, 260 - k * 12), 180, 180, False,
                      stroke(col, 9, 220))
    blobs = [(-60, 10, 48), (-16, -26, 60), (40, -14, 54), (70, 22, 40), (0, 30, 56), (-72, 38, 34)]
    path = skia.Path()
    for x, y, r in blobs:
        path.addCircle(x, y, r)
    path.setFillType(skia.PathFillType.kWinding)
    c.drawPath(path, stroke(w=LW * 2))                                         # contour extérieur
    c.drawPath(path, fill((255, 255, 255), shader=vgrad(-80, 90, (250, 252, 255), (200, 215, 245))))
    if st["expr"] == "surpris":                                               # petit éclair de surprise
        z = skia.Path()
        z.moveTo(-8, 90)
        z.lineTo(8, 112)
        z.lineTo(-2, 114)
        z.lineTo(10, 140)
        c.drawPath(z, stroke((255, 200, 60), 6))
    eyes(c, 0, 2, 19, 30, st)
    mouth(c, 0, 38, 56, st)
    for side in (-1, 1):
        c.drawOval(skia.Rect(side * 52 - 12, 26, side * 52 + 12, 36), fill((255, 150, 180), 140))
    emote(c, 90, -100, st)


CHARS = [("Piou", "oiseau rond", piou, (255, 244, 214)), ("Bulle", "blob gélatineux", bulle, (220, 250, 232)),
         ("Eurêka", "ampoule", ampoule, (255, 246, 206)), ("Bip", "robot", bip, (224, 230, 255)),
         ("Léo", "haricot humain", haricot, (255, 228, 222)), ("Cumulus", "petit nuage", nuage, (218, 236, 255))]


def draw(c, t):
    c.clear(rgb((250, 246, 240)))
    title = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 50)
    c.drawString("Quel personnage ?", 290, 110, title, fill(OUT))
    cw, ch = 505, 560
    for i, (name, kind, fn, bg) in enumerate(CHARS):
        x0 = 24 + (i % 2) * (cw + 22)
        y0 = 160 + (i // 2) * (ch + 20)
        rect = skia.Rect(x0, y0, x0 + cw, y0 + ch)
        c.drawRoundRect(rect, 36, 36, fill(bg))
        c.drawRoundRect(rect, 36, 36, stroke(shade(bg, 0.8), 4))
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(rect, 36, 36), doAntiAlias=True)
        c.translate(x0 + cw / 2, y0 + 290)
        c.scale(1.28, 1.28)
        fn(c, state(t, offset=i * 0.12), t + i * 0.37)
        c.restore()
        c.drawString(f"{i + 1}. {name}", x0 + 28, y0 + ch - 58, skia.Font(skia.Typeface("DejaVu Sans",
                     skia.FontStyle.Bold()), 34), fill(OUT))
        c.drawString(kind, x0 + 28, y0 + ch - 22, skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Normal()),
                     26), fill(shade(OUT, 2.2)))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/planche_personnages.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        draw(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    for t, name in ((1.5, "repos"), (6.2, "joie")):
        s = skia.Surface(W, H)
        draw(s.getCanvas(), t)
        s.makeImageSnapshot().save(out.replace(".mp4", f"_{name}.png"))
    print(out)


if __name__ == "__main__":
    main()
