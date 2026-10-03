"""Personnages « toon » plats (gros contours, tête ronde, visage en quelques traits) et décor de voiture au coucher du
soleil, pour les dialogues en champ-contrechamp.

Personnage dessiné de face, centré en (0, 0) = centre de la tête, rayon de tête R. Expressions : sourcils, paupières,
bouche (formes synchronisées sur la voix).
"""
import math

import numpy as np
import skia

INK = skia.Color(22, 20, 24)
R = 300.0


def P(col, stroke=0.0, a=255):
    if isinstance(col, tuple):
        col = skia.Color(*col, a)
    p = skia.Paint(AntiAlias=True, Color=col)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def contour(c, path, fill, w=9.0):
    c.drawPath(path, P(fill))
    c.drawPath(path, P(INK, w))


PERSOS = {
    "lui": {"peau": (246, 200, 146), "haut": (40, 110, 52), "cheveux": "pics"},
    "elle": {"peau": (246, 200, 146), "haut": (232, 36, 130), "cheveux": "chignon"},
}

# expressions : (sourcil gauche (angle, hauteur), sourcil droit, paupières 0 ouvert → 1 fermé, regard x)
EXPR = {
    "neutre": ((0, 0), (0, 0), 0.35, 0.0),
    "content": ((-6, -10), (6, -10), 0.15, 0.0),
    "blase": ((0, 8), (0, 8), 0.6, 0.0),
    "suspicieux": ((14, 6), (-4, -10), 0.55, 0.25),
    "choque": ((-14, -26), (14, -26), 0.0, 0.0),
    "moqueur": ((-4, -4), (-16, -18), 0.5, 0.15),
    "agace": ((18, 6), (-18, 6), 0.4, 0.0),
}


def tete(c, qui, expr="neutre", bouche="fermee", cligne=False, t=0.0, regard=0.0):
    p = PERSOS[qui]
    peau = p["peau"]
    # cou + corps (épaules) + ceinture
    corps = skia.Path()
    corps.moveTo(-440, 1300)
    corps.cubicTo(-420, 420, -300, 330, -120, 310)
    corps.lineTo(120, 310)
    corps.cubicTo(300, 330, 440, 420, 440, 1300)
    corps.close()
    cou = skia.Path()
    cou.addRect(skia.Rect(-80, 220, 80, 340))
    contour(c, cou, peau)
    contour(c, corps, p["haut"])
    col = skia.Path()                                     # col en V
    col.moveTo(-110, 312)
    col.quadTo(0, 400, 110, 312)
    c.drawPath(col, P(peau))
    c.drawPath(col, P(INK, 9))
    if qui == "elle":                                     # petit logo sur le haut
        r = skia.Rect(-40, 560, 40, 660)
        c.drawRect(r, P((245, 150, 30)))
        c.drawRect(r, P(INK, 7))
        c.drawCircle(-12, 590, 10, P(INK))
        c.drawCircle(14, 628, 10, P(INK))
    belt = skia.Path()                                    # ceinture de sécurité
    belt.moveTo(260, 330)
    belt.lineTo(330, 360)
    belt.lineTo(-460, 1060)
    belt.lineTo(-480, 980)
    belt.close()
    contour(c, belt, (60, 60, 66), 7)
    # cheveux arrière (chignon)
    if p["cheveux"] == "chignon":
        c.drawCircle(150, -300, 95, P(INK))
    # tête
    head = skia.Path()
    head.addCircle(0, 0, R)
    contour(c, head, peau, 10)
    # oreilles
    for sd in (-1, 1):
        e = skia.Path()
        e.addOval(skia.Rect(sd * R - 40, -40, sd * R + 40, 60))
        c.save()
        c.clipPath(head, skia.ClipOp.kDifference, True)
        contour(c, e, peau, 9)
        c.restore()
    # cheveux
    c.save()
    c.clipPath(head, doAntiAlias=True)
    if p["cheveux"] == "pics":
        h = skia.Path()
        h.moveTo(-R - 20, -60)
        xs = np.linspace(-R, R, 13)
        for k, x in enumerate(xs):
            y = -R * 0.42 + (40 if k % 2 else -10) - 40 * math.exp(-(x / 200) ** 2)
            h.lineTo(x, y)
        h.lineTo(R + 20, -60)
        h.lineTo(R + 20, -R - 40)
        h.lineTo(-R - 20, -R - 40)
        h.close()
        c.drawPath(h, P(INK))
    else:
        h = skia.Path()
        h.moveTo(-R - 20, 40)
        h.cubicTo(-R + 40, -R * 0.2, -120, -R * 0.55, 40, -R * 0.5)
        h.cubicTo(180, -R * 0.45, R - 40, -R * 0.2, R + 20, 60)
        h.lineTo(R + 20, -R - 40)
        h.lineTo(-R - 20, -R - 40)
        h.close()
        c.drawPath(h, P(INK))
    c.restore()
    c.drawPath(head, P(INK, 10))
    # visage
    (ag, ah), (dg, dh), lid, gx = EXPR[expr]
    gx += regard
    for sd, (ang, hh) in ((-1, (ag, ah)), (1, (dg, dh))):
        ex, ey = sd * 110, -20
        # sourcil
        c.save()
        c.translate(ex, ey - 78 + hh)
        c.rotate(ang * (1 if sd < 0 else 1))
        c.drawLine(-52, 0, 52, 0, P(INK, 22))
        c.restore()
        # œil : pupille + paupière supérieure
        l = 1.0 if cligne else lid
        if l > 0.92:
            c.drawLine(ex - 30, ey + 4, ex + 30, ey + 4, P(INK, 8))
            continue
        c.save()
        clip = skia.Path()
        clip.addRect(skia.Rect(ex - 45, ey - 26 + 60 * l, ex + 45, ey + 45))
        c.clipPath(clip)
        c.drawCircle(ex + gx * 18, ey + 6, 22, P(INK))
        c.restore()
        c.drawLine(ex - 38, ey - 26 + 60 * l, ex + 38, ey - 26 + 60 * l, P(INK, 9))
    # bouche
    mx, my = 0, 140
    if bouche == "fermee":
        m = skia.Path()
        if expr in ("content", "moqueur"):
            m.moveTo(mx - 70, my - 10)
            m.quadTo(mx + 10, my + 40, mx + 80, my - 20)
        elif expr in ("blase", "agace", "suspicieux"):
            m.moveTo(mx - 60, my + 6)
            m.lineTo(mx + 60, my)
        elif expr == "choque":
            c.drawOval(skia.Rect(mx - 30, my - 20, mx + 30, my + 40), P(INK))
            return
        else:
            m.moveTo(mx - 60, my)
            m.quadTo(mx, my + 14, mx + 60, my)
        c.drawPath(m, P(INK, 9))
        return
    w, h = {"mi": (130, 64), "ouverte": (165, 135), "o": (90, 100), "large": (200, 90)}[bouche]
    m = skia.Path()
    if expr in ("content", "moqueur") and bouche != "o":
        m.moveTo(mx - w / 2, my - h * 0.3)
        m.quadTo(mx, my - h * 0.45, mx + w / 2, my - h * 0.3)
        m.quadTo(mx + w * 0.4, my + h * 0.9, mx, my + h * 0.75)
        m.quadTo(mx - w * 0.4, my + h * 0.9, mx - w / 2, my - h * 0.3)
    else:
        m.addOval(skia.Rect(mx - w / 2, my - h / 2, mx + w / 2, my + h / 2))
    c.drawPath(m, P((120, 24, 36)))
    c.save()
    c.clipPath(m, doAntiAlias=True)
    c.drawRect(skia.Rect(mx - w, my - h, mx + w, my - h * 0.28), P((255, 255, 255)))     # dents
    c.drawOval(skia.Rect(mx - w * 0.35, my + h * 0.05, mx + w * 0.35, my + h * 0.9), P((235, 80, 90)))
    c.restore()
    c.drawPath(m, P(INK, 9))


# ------------------------------------------------------------------------------------------------ décor
def ville(c, x0, y0, x1, y1, t):
    """Vue par la vitre : ciel de coucher de soleil, immeubles, palmiers (défile doucement)."""
    c.save()
    c.clipRect(skia.Rect(x0, y0, x1, y1))
    sky = skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)],
                                         [skia.Color(250, 140, 60), skia.Color(250, 110, 120), skia.Color(150, 80, 170)])
    c.drawRect(skia.Rect(x0, y0, x1, y1), skia.Paint(Shader=sky))
    c.drawCircle(x0 + (x1 - x0) * 0.7, y0 + (y1 - y0) * 0.55, 90, P((255, 220, 120)))
    off = (t * 60) % 400
    rng = np.random.default_rng(3)
    for k in range(-1, 12):
        bx = x0 + k * 160 - off
        bh = rng.uniform(0.35, 0.8) * (y1 - y0)
        col = [(120, 70, 160), (90, 60, 140), (150, 80, 170)][k % 3]
        r = skia.Rect(bx, y1 - bh, bx + 130, y1)
        c.drawRect(r, P(col))
        c.drawRect(r, P(INK, 5))
        for wy in range(int(y1 - bh + 20), int(y1) - 20, 40):
            for wx in range(int(bx + 15), int(bx + 115), 35):
                c.drawRect(skia.Rect(wx, wy, wx + 18, wy + 22), P((255, 200, 120) if (wx + wy) % 3 else (80, 50, 110)))
    for k in range(-1, 6):                                         # palmiers au premier plan
        px = x0 + k * 330 - (t * 140) % 330 + 80
        c.drawLine(px, y1, px + 20, y1 - 260, P((40, 30, 50), 16))
        for a in range(6):
            ang = math.radians(-160 + a * 28)
            c.drawLine(px + 20, y1 - 260, px + 20 + 120 * math.cos(ang), y1 - 260 + 60 * math.sin(ang) + 30,
                       P((40, 30, 50), 12))
    c.restore()


def siege(c, x, y, s=1.0):
    """Appui-tête et dossier de siège beige, cerné."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    dos = skia.Path()
    dos.addRRect(skia.RRect.MakeRectXY(skia.Rect(-420, -230, 420, 1100), 120, 120))
    contour(c, dos, (205, 180, 140), 10)
    appui = skia.Path()
    appui.addRRect(skia.RRect.MakeRectXY(skia.Rect(-300, -560, 300, -140), 140, 140))
    contour(c, appui, (215, 190, 150), 10)
    for k in (-1, 1):
        p = skia.Path()
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect(k * 340 - 60, -200, k * 340 + 60, 1000), 50, 50))
        contour(c, p, (180, 155, 115), 8)
    c.restore()


def interieur(c, W, H, t, cote=1):
    """Fond d'un gros plan : plafond, vitre latérale avec la ville, montant de porte."""
    c.drawRect(skia.Rect(0, 0, W, H), P((120, 116, 120)))
    vx0, vx1 = (W * 0.42, W + 40) if cote > 0 else (-40, W * 0.58)
    ville(c, vx0, 250, vx1, 1050, t)
    fr = skia.Path()
    fr.addRRect(skia.RRect.MakeRectXY(skia.Rect(vx0, 250, vx1, 1050), 60, 60))
    c.drawPath(fr, P(INK, 12))
    c.drawRect(skia.Rect(0, 0, W, 200), P((150, 146, 150)))
    c.drawLine(0, 200, W, 200, P(INK, 10))
