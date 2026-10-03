"""Personnages toon v2 : même style plat (tête ronde, gros contours) mais dessin nettement plus riche — ombrages
en aplats (cel shading), yeux complets (blanc, iris, reflet, paupières), nez, oreilles détaillées, reflets dans les
cheveux, épaisseurs de trait variées, vêtements avec plis, accessoires. Plus un cerveau-personnage dans le même style.

Repère : centre de la tête en (0, 0), rayon R. y vers le bas.
"""
import math
from dataclasses import dataclass

import skia

INK = skia.Color(24, 20, 26)
R = 300.0


def P(col, stroke=0.0, a=255):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*col, a) if isinstance(col, tuple) else col)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def sombre(c, k=0.78):
    return tuple(int(v * k) for v in c)


def clair(c, k=0.35):
    return tuple(int(v + (255 - v) * k) for v in c)


def forme(c, path, fill, w=10.0, ombre=None, ombre_path=None):
    """Aplat + ombre (aplat plus sombre découpé dans la forme) + contour."""
    c.drawPath(path, P(fill))
    if ombre_path is not None:
        c.save()
        c.clipPath(path, doAntiAlias=True)
        c.drawPath(ombre_path, P(ombre or sombre(fill)))
        c.restore()
    c.drawPath(path, P(INK, w))


@dataclass
class Look:
    peau: tuple = (243, 196, 146)
    cheveux: str = "pics"          # pics, chignon, bonnet
    couleur_cheveux: tuple = (34, 28, 30)
    haut: tuple = (46, 120, 62)
    iris: tuple = (96, 62, 40)
    barbe: bool = False
    cernes: float = 0.0            # 0–1
    yeux_rouges: float = 0.0
    capuche: bool = False


LOOKS = {
    "lui": Look(barbe=True),
    "elle": Look(cheveux="chignon", haut=(232, 40, 132), iris=(70, 50, 36)),
    "sommeil": Look(cheveux="bonnet", haut=(120, 170, 230), peau=(240, 205, 165), iris=(80, 110, 150)),
    "insomnie": Look(cheveux="pics", haut=(36, 36, 44), cernes=1.0, yeux_rouges=1.0, capuche=True,
                     peau=(232, 192, 150)),
}

# expressions : sourcils (angle, hauteur) g/d, paupière haute 0–1, paupière basse 0–1, regard (x, y)
EXPR = {
    "neutre": ((0, 0), (0, 0), 0.25, 0.0, (0, 0)),
    "content": ((-8, -12), (8, -12), 0.1, 0.25, (0, 0)),
    "blase": ((2, 10), (-2, 10), 0.55, 0.1, (0.1, 0.1)),
    "fatigue": ((-12, 6), (12, 6), 0.68, 0.15, (0, 0.2)),
    "dort": ((0, 8), (0, 8), 1.0, 0.0, (0, 0)),
    "agace": ((18, 8), (-18, 8), 0.4, 0.15, (0, 0)),
    "suppliant": ((-20, -10), (20, -10), 0.35, 0.0, (0, -0.2)),
    "choque": ((-12, -30), (12, -30), 0.0, 0.0, (0, 0)),
    "excite": ((-10, -24), (10, -24), 0.0, 0.0, (0.15, -0.1)),
    "curieux": ((-4, -22), (14, 6), 0.1, 0.0, (0.3, -0.2)),
    "moqueur": ((-4, -4), (-16, -18), 0.45, 0.2, (0.2, 0)),
    "malin": ((10, 4), (-14, -16), 0.35, 0.15, (0.25, 0)),
}


# ------------------------------------------------------------------------------------------------ visage
def oeil(c, x, y, s, look, haut, bas, gx, gy, cligne, side):
    """Œil complet : blanc en amande, iris + pupille + reflet, paupières couleur peau, cils."""
    w, h = 46 * s, 34 * s
    amande = skia.Path()
    amande.moveTo(x - w, y)
    amande.cubicTo(x - w * 0.6, y - h * 1.25, x + w * 0.6, y - h * 1.25, x + w, y - h * 0.1)
    amande.cubicTo(x + w * 0.6, y + h * 0.95, x - w * 0.6, y + h * 0.95, x - w, y)
    amande.close()
    haut = 1.0 if cligne else haut
    if haut >= 0.97:                                               # fermé : courbe vers le bas
        p = skia.Path()
        p.moveTo(x - w, y)
        p.quadTo(x, y + h * 0.7, x + w, y - h * 0.1)
        c.drawPath(p, P(INK, 8 * s))
        for k in (-0.6, 0.0, 0.6):                                  # cils
            c.drawLine(x + k * w, y + h * 0.33 * (1 - abs(k)), x + k * w * 1.15, y + h * 0.7, P(INK, 4 * s))
        return
    blanc = (255, 250, 245) if look.yeux_rouges < 0.5 else (255, 222, 222)
    c.drawPath(amande, P(blanc))
    c.save()
    c.clipPath(amande, doAntiAlias=True)
    if look.yeux_rouges > 0:
        for k in range(3):
            a = math.radians(160 + k * 20) if side < 0 else math.radians(-20 - k * 20)
            c.drawLine(x + w * math.cos(a), y + h * math.sin(a), x + w * 0.45 * math.cos(a), y + h * 0.4 * math.sin(a),
                       P((220, 60, 60), 2.5 * s))
    ix, iy = x + gx * w * 0.45, y + gy * h * 0.4 + 2 * s
    c.drawCircle(ix, iy, 24 * s, P(look.iris))
    c.drawCircle(ix, iy, 24 * s, P(sombre(look.iris, 0.6), 3 * s))
    c.drawCircle(ix, iy, 12 * s, P(INK))
    c.drawCircle(ix - 8 * s, iy - 9 * s, 6 * s, P((255, 255, 255)))
    # paupière haute (couleur peau) et basse
    if haut > 0.02:
        lid = skia.Path()
        yy = y - h * 1.2 + (h * 2.0) * haut
        lid.addRect(skia.Rect(x - w * 1.2, y - h * 1.6, x + w * 1.2, yy))
        c.drawPath(lid, P(sombre(look.peau, 0.92)))
        c.drawLine(x - w * 1.1, yy, x + w * 1.1, yy, P(INK, 6 * s))
    if bas > 0.02:
        lid = skia.Path()
        yy = y + h * 0.95 - h * 1.2 * bas
        lid.addRect(skia.Rect(x - w * 1.2, yy, x + w * 1.2, y + h * 1.6))
        c.drawPath(lid, P(look.peau))
        c.drawLine(x - w * 0.8, yy, x + w * 0.8, yy, P(INK, 3 * s))
    c.restore()
    c.drawPath(amande, P(INK, 7 * s))
    # ligne de cils (plus épaisse en haut, vers l'extérieur)
    c.drawLine(x + side * w * 0.95, y - h * 0.05, x + side * w * 1.25, y - h * 0.35, P(INK, 6 * s))
    if look.cernes > 0:
        p = skia.Path()
        p.moveTo(x - w * 0.8, y + h * 1.0)
        p.quadTo(x, y + h * 1.7, x + w * 0.8, y + h * 1.0)
        c.drawPath(p, P((140, 90, 110), 7 * s, int(200 * look.cernes)))


def sourcil(c, x, y, ang, side, s=1.0, col=INK):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    p = skia.Path()                                                  # trait effilé
    p.moveTo(-58 * s * side, 6 * s)
    p.cubicTo(-30 * s * side, -14 * s, 30 * s * side, -16 * s, 60 * s * side, -2 * s)
    p.cubicTo(30 * s * side, -2 * s, -20 * s * side, 2 * s, -58 * s * side, 6 * s)
    p.close()
    c.drawPath(p, P(col))
    c.drawPath(p, P(col, 9 * s))
    c.restore()


def bouche(c, x, y, forme_b, expr, look, s=1.0):
    if forme_b == "fermee":
        m = skia.Path()
        if expr in ("content", "moqueur", "malin", "excite"):
            m.moveTo(x - 70 * s, y - 14 * s)
            m.quadTo(x + 5 * s, y + 42 * s, x + 80 * s, y - 24 * s)
            c.drawPath(m, P(INK, 9 * s))
            c.drawLine(x + 72 * s, y - 34 * s, x + 86 * s, y - 14 * s, P(INK, 6 * s))     # fossette
        elif expr in ("blase", "agace", "fatigue"):
            m.moveTo(x - 58 * s, y + 8 * s)
            m.quadTo(x, y - 2 * s, x + 58 * s, y + 2 * s)
            c.drawPath(m, P(INK, 9 * s))
        elif expr == "dort":
            m.moveTo(x - 30 * s, y + 4 * s)
            m.quadTo(x, y + 14 * s, x + 30 * s, y + 4 * s)
            c.drawPath(m, P(INK, 8 * s))
        elif expr in ("choque",):
            c.drawOval(skia.Rect(x - 32 * s, y - 24 * s, x + 32 * s, y + 44 * s), P((110, 26, 40)))
            c.drawOval(skia.Rect(x - 32 * s, y - 24 * s, x + 32 * s, y + 44 * s), P(INK, 8 * s))
        else:
            m.moveTo(x - 55 * s, y)
            m.quadTo(x, y + 16 * s, x + 55 * s, y)
            c.drawPath(m, P(INK, 9 * s))
        return
    w, h = {"mi": (120, 58), "ouverte": (160, 128), "o": (84, 96), "large": (200, 84)}[forme_b]
    w, h = w * s, h * s
    m = skia.Path()
    if expr in ("content", "moqueur", "excite", "malin") and forme_b != "o":
        m.moveTo(x - w / 2, y - h * 0.32)
        m.quadTo(x, y - h * 0.5, x + w / 2, y - h * 0.32)
        m.quadTo(x + w * 0.42, y + h * 0.95, x, y + h * 0.8)
        m.quadTo(x - w * 0.42, y + h * 0.95, x - w / 2, y - h * 0.32)
    else:
        m.addOval(skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2))
    c.drawPath(m, P((112, 22, 38)))
    c.save()
    c.clipPath(m, doAntiAlias=True)
    c.drawRect(skia.Rect(x - w, y - h, x + w, y - h * 0.26), P((255, 252, 246)))
    c.drawLine(x - w, y - h * 0.26, x + w, y - h * 0.26, P((200, 190, 185), 3 * s))
    c.drawOval(skia.Rect(x - w * 0.36, y + h * 0.05, x + w * 0.36, y + h * 0.95), P((236, 86, 100)))
    c.drawOval(skia.Rect(x - w * 0.36, y + h * 0.05, x + w * 0.36, y + h * 0.95), P((190, 50, 70), 3 * s))
    c.restore()
    c.drawPath(m, P(INK, 9 * s))


def tete(c, qui, expr="neutre", forme_b="fermee", cligne=False, t=0.0, corps=True, inclinaison=0.0):
    look = LOOKS[qui]
    peau = look.peau
    (ag, ah), (dg, dh), haut, bas, (gx, gy) = EXPR[expr]
    if corps:
        torse(c, look)
    c.save()
    c.rotate(inclinaison)
    if look.cheveux == "chignon":
        ch = skia.Path()
        ch.addCircle(150, -300, 100)
        forme(c, ch, look.couleur_cheveux, 9, clair(look.couleur_cheveux, 0.2), _decal(ch, -30, -30))
    if look.capuche:
        cap = skia.Path()
        cap.addOval(skia.Rect(-R - 70, -R - 60, R + 70, R + 120))
        forme(c, cap, look.haut, 11, sombre(look.haut, 0.7), _decal(cap, 0, 70))
    # oreilles (sous la tête)
    for sd in (-1, 1):
        e = skia.Path()
        e.addOval(skia.Rect(sd * R - 46, -48, sd * R + 46, 66))
        forme(c, e, peau, 9, sombre(peau), _decal(e, sd * 14, 6))
        p = skia.Path()
        p.moveTo(sd * R + sd * 18, -18)
        p.quadTo(sd * R + sd * 4, 12, sd * R + sd * 20, 34)
        c.drawPath(p, P(INK, 5))
    head = skia.Path()
    head.moveTo(0, -R)
    head.cubicTo(R * 0.56, -R, R, -R * 0.58, R, 0)
    head.cubicTo(R, R * 0.62, R * 0.55, R * 1.02, 0, R * 1.02)
    head.cubicTo(-R * 0.55, R * 1.02, -R, R * 0.62, -R, 0)
    head.cubicTo(-R, -R * 0.58, -R * 0.56, -R, 0, -R)
    head.close()
    ombre = skia.Path()                                              # ombre propre côté droit et sous le menton
    ombre.addCircle(-R * 0.22, -R * 0.12, R * 1.05)
    ombre2 = skia.Path()
    ombre2.addRect(skia.Rect(-2 * R, -2 * R, 2 * R, 2 * R))
    ombre_head = skia.Op(ombre2, ombre, skia.PathOp.kDifference_PathOp)
    forme(c, head, peau, 11, sombre(peau, 0.86), ombre_head)
    # joues
    for sd in (-1, 1):
        c.drawOval(skia.Rect(sd * 165 - 52, 70, sd * 165 + 52, 112), P((240, 140, 130), a=70))
    # barbe de quelques jours
    if look.barbe:
        b = skia.Path()
        b.moveTo(-R * 0.95, R * 0.35)
        b.cubicTo(-R * 0.75, R * 1.1, R * 0.75, R * 1.1, R * 0.95, R * 0.35)
        b.cubicTo(R * 0.7, R * 0.8, R * 0.3, R * 0.72, 0, R * 0.74)
        b.cubicTo(-R * 0.3, R * 0.72, -R * 0.7, R * 0.8, -R * 0.95, R * 0.35)
        b.close()
        c.save()
        c.clipPath(head, doAntiAlias=True)
        c.drawPath(b, P((80, 58, 50), a=120))
        mo = skia.Path()
        mo.moveTo(-70, 128)
        mo.quadTo(0, 108, 70, 128)
        c.drawPath(mo, P((80, 58, 50), 14, 110))
        c.restore()
    # cheveux (avant)
    cheveux(c, look, head)
    c.drawPath(head, P(INK, 11))
    # nez
    n = skia.Path()
    n.moveTo(14, 30)
    n.cubicTo(34, 60, 24, 84, 0, 86)
    c.drawPath(n, P(INK, 7))
    c.drawPath(n, P(sombre(peau, 0.8), 3))
    # yeux et sourcils
    for sd, (ang, hh) in ((-1, (ag, ah)), (1, (dg, dh))):
        ex, ey = sd * 118, -14
        oeil(c, ex, ey, 1.38, look, haut, bas, gx, gy, cligne, sd)
        sourcil(c, ex, ey - 96 + hh, ang, sd, 1.15, sombre(look.couleur_cheveux, 0.8))
    bouche(c, 0, 158, forme_b, expr, look)
    c.restore()


def _decal(path, dx, dy):
    p = skia.Path(path)
    p.offset(dx, dy)
    return p


def cheveux(c, look, head):
    col = look.couleur_cheveux
    c.save()
    c.clipPath(head, doAntiAlias=True)
    h = skia.Path()
    if look.cheveux == "pics":
        h.moveTo(-R - 30, -40)
        n = 11
        for k in range(n + 1):
            x = -R + 2 * R * k / n
            y = -R * 0.40 - 50 * math.exp(-(x / 210) ** 2) + (34 if k % 2 else -22)
            h.lineTo(x, y)
        h.lineTo(R + 30, -40)
        h.lineTo(R + 30, -R - 60)
        h.lineTo(-R - 30, -R - 60)
        h.close()
    elif look.cheveux == "chignon":
        h.moveTo(-R - 20, 50)
        h.cubicTo(-R + 40, -R * 0.2, -120, -R * 0.58, 40, -R * 0.52)
        h.cubicTo(180, -R * 0.47, R - 40, -R * 0.2, R + 20, 70)
        h.lineTo(R + 20, -R - 40)
        h.lineTo(-R - 20, -R - 40)
        h.close()
    else:                                                            # bonnet de nuit
        h.moveTo(-R - 20, -R * 0.36)
        h.cubicTo(-R * 0.4, -R * 0.52, R * 0.4, -R * 0.52, R + 20, -R * 0.36)
        h.lineTo(R + 20, -R - 60)
        h.lineTo(-R - 20, -R - 60)
        h.close()
        col = (120, 170, 230)
    c.drawPath(h, P(col))
    hl = skia.Path(h)                                                # reflet
    hl.offset(-40, -40)
    c.save()
    c.clipPath(h, doAntiAlias=True)
    c.drawPath(hl, P(clair(col, 0.18)))
    c.restore()
    c.drawPath(h, P(INK, 7))
    c.restore()
    if look.cheveux == "bonnet":                                     # pointe du bonnet + pompon
        p = skia.Path()
        p.moveTo(-R * 0.9, -R * 0.55)
        p.cubicTo(-R * 0.4, -R * 1.5, R * 0.6, -R * 1.6, R * 1.25, -R * 0.9)
        p.lineTo(R * 0.9, -R * 0.55)
        p.close()
        forme(c, p, col, 10, sombre(col, 0.82), _decal(p, 30, 40))
        b = skia.Path()
        b.addRRect(skia.RRect.MakeRectXY(skia.Rect(-R - 20, -R * 0.62, R + 20, -R * 0.36), 40, 40))
        forme(c, b, (245, 245, 250), 9)
        pom = skia.Path()
        pom.addCircle(R * 1.25, -R * 0.9, 46)
        forme(c, pom, (245, 245, 250), 9)


def torse(c, look):
    corps = skia.Path()
    corps.moveTo(-460, 1400)
    corps.cubicTo(-440, 430, -310, 330, -120, 300)
    corps.lineTo(120, 300)
    corps.cubicTo(310, 330, 440, 430, 460, 1400)
    corps.close()
    cou = skia.Path()
    cou.addRect(skia.Rect(-82, 200, 82, 340))
    forme(c, cou, look.peau, 10, sombre(look.peau, 0.8), _decal(cou, 0, -60))
    pl = skia.Path()
    pl.moveTo(470, 300)
    pl.cubicTo(250, 500, 320, 900, 300, 1500)
    pl.lineTo(700, 1500)
    pl.lineTo(700, 300)
    pl.close()
    forme(c, corps, look.haut, 11, sombre(look.haut, 0.8), pl)
    for x0, x1 in ((-260, -300), (230, 280)):                       # plis
        p = skia.Path()
        p.moveTo(x0, 520)
        p.quadTo(x0 - 10, 640, x1, 760)
        c.drawPath(p, P(sombre(look.haut, 0.6), 7))
    col = skia.Path()
    col.moveTo(-118, 302)
    col.quadTo(0, 410, 118, 302)
    c.drawPath(col, P(look.peau))
    c.drawPath(col, P(INK, 10))


# ------------------------------------------------------------------------------------------------ cerveau
def cerveau(c, expr="excite", forme_b="fermee", cligne=False, t=0.0):
    """Cerveau-personnage : deux hémisphères roses à circonvolutions, grands yeux, petits bras."""
    rose = (245, 150, 172)
    corps = skia.Path()
    n = 40
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        rr = R * (1 + 0.055 * math.sin(a * 9 + 0.5))
        x, y = rr * 1.12 * math.cos(a), rr * 0.86 * math.sin(a)
        corps.moveTo(x, y) if i == 0 else corps.lineTo(x, y)
    corps.close()
    om = skia.Path()
    om.addOval(skia.Rect(-R * 1.4, R * 0.15, R * 1.4, R * 1.6))
    forme(c, corps, rose, 12, sombre(rose, 0.82), om)
    c.save()
    c.clipPath(corps, doAntiAlias=True)
    c.drawLine(0, -R, 0, -R * 0.35, P(sombre(rose, 0.62), 10))     # sillon central
    for k in range(9):                                               # circonvolutions
        x0 = -R * 1.05 + k * R * 0.27
        p = skia.Path()
        p.moveTo(x0, -R * 0.85)
        p.cubicTo(x0 + 70, -R * 0.55, x0 - 60, -R * 0.35, x0 + 30, -R * 0.12)
        c.drawPath(p, P(sombre(rose, 0.68), 8))
    for k in range(6):
        y0 = R * 0.05 + k * 0
        p = skia.Path()
        x0 = -R * 1.0 + k * R * 0.4
        p.moveTo(x0, R * 0.55)
        p.cubicTo(x0 + 40, R * 0.35, x0 + 90, R * 0.75, x0 + 140, R * 0.5)
        c.drawPath(p, P(sombre(rose, 0.68), 8))
    c.drawOval(skia.Rect(-R * 0.75, -R * 0.82, -R * 0.2, -R * 0.55), P(clair(rose, 0.45)))
    c.restore()
    c.drawPath(corps, P(INK, 12))
    look = Look(peau=rose, iris=(60, 140, 90))
    (ag, ah), (dg, dh), haut, bas, (gx, gy) = EXPR[expr]
    for sd, (ang, hh) in ((-1, (ag, ah)), (1, (dg, dh))):
        ex, ey = sd * 128, -10
        oeil(c, ex, ey, 1.7, look, haut, bas, gx, gy, cligne, sd)
        sourcil(c, ex, ey - 118 + hh, ang, sd, 1.2, (120, 40, 70))
    bouche(c, 0, 150, forme_b, expr, look, 1.05)
    # petits bras qui gesticulent
    for sd in (-1, 1):
        a = math.radians(30 + 25 * math.sin(t * 5 + sd))
        x0, y0 = sd * R * 1.05, R * 0.3
        x1, y1 = x0 + sd * 120 * math.cos(a), y0 - 120 * math.sin(a)
        c.drawLine(x0, y0, x1, y1, P(INK, 30))
        c.drawLine(x0, y0, x1, y1, P(rose, 16))
        c.drawCircle(x1, y1, 26, P(rose))
        c.drawCircle(x1, y1, 26, P(INK, 8))
