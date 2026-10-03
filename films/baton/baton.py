"""Bonhomme bâton vectoriel, style « dessin au trait » : membres en tubes blancs cernés de noir, mains dessinées,
visage expressif, poses enchaînées avec cinématique inverse et petits mouvements permanents.

    b = Baton()
    b.draw(canvas, etat)      # etat = Etat(...) : pose courante (interpolée), regard, bouche, clignement…

Repère : pieds au sol en (0, 0), le personnage mesure ~620 px (tête comprise), y vers le bas.
"""
import math
from dataclasses import dataclass, field

import skia

INK = skia.Color(18, 18, 22)
WHITE = skia.Color(255, 255, 255)

# squelette au repos (repère du bonhomme)
HANCHE = (0.0, -300.0)
COU = (0.0, -505.0)
TETE_R = 62.0
L_BRAS, L_AVBRAS = 118.0, 112.0
L_CUISSE, L_TIBIA = 146.0, 146.0


def P(color=INK, stroke=0.0, cap=True):
    p = skia.Paint(AntiAlias=True, Color=color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap if cap else skia.Paint.kButt_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def back(u, s=1.4):
    """Arrivée avec léger dépassement (pose plus vivante)."""
    u = min(max(u, 0.0), 1.0) - 1
    return 1 + u * u * ((s + 1) * u + s)


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))


def ik_dehors(a, target, l1, l2, cote, cx):
    """Coude du côté extérieur du corps (cote = -1 à gauche de l'écran, +1 à droite)."""
    s1, s2 = ik(a, target, l1, l2, 1), ik(a, target, l1, l2, -1)
    return s1 if (s1[0] - cx) * cote >= (s2[0] - cx) * cote else s2


def ik(a, target, l1, l2, flip=1):
    """Cinématique inverse à deux os : renvoie le coude/genou."""
    dx, dy = target[0] - a[0], target[1] - a[1]
    d = min(math.hypot(dx, dy), l1 + l2 - 0.5)
    d = max(d, abs(l1 - l2) + 0.5)
    base = math.atan2(dy, dx)
    cosang = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    ang = base + flip * math.acos(max(-1, min(1, cosang)))
    return (a[0] + l1 * math.cos(ang), a[1] + l1 * math.sin(ang))


def tube(c, pts, w=11.0):
    """Membre : tube blanc cerné de noir le long d'une polyligne."""
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    c.drawPath(p, P(INK, w + 6.0))
    c.drawPath(p, P(WHITE, w))


# ------------------------------------------------------------------------------------------------ poses
# main gauche/droite (côté écran) : cible de la main (repère du bonhomme), forme de la main, sens du coude
POSES = {
    "repos":    {"mg": (-72, -268), "md": (72, -268), "fg": "ouverte", "fd": "ouverte", "inc": 0.0},
    "index":    {"mg": (-150, -720), "md": (58, -340), "fg": "index", "fd": "hanche", "inc": -3.0},
    "pointe_g": {"mg": (-235, -640), "md": (58, -340), "fg": "index", "fd": "hanche", "inc": -5.0},
    "pointe_d": {"mg": (-58, -340), "md": (235, -640), "fg": "hanche", "fd": "index", "inc": 5.0},
    "reflechit": {"mg": (-72, -268), "md": (40, -610), "fg": "ouverte", "fd": "tete", "inc": 4.0},
    "explique": {"mg": (-165, -395), "md": (58, -340), "fg": "paume", "fd": "hanche", "inc": -2.0},
    "deux":     {"mg": (-175, -390), "md": (175, -390), "fg": "paume", "fd": "paume", "inc": 0.0},
    "menton":   {"mg": (-72, -268), "md": (18, -555), "fg": "ouverte", "fd": "menton", "inc": 2.0},
}


@dataclass
class Etat:
    pose_a: str = "repos"
    pose_b: str = "repos"
    u: float = 1.0                 # avancement de la transition a → b (0–1, déjà « adouci »)
    t: float = 0.0                 # temps (mouvements permanents)
    bouche: float = 0.0            # ouverture de la bouche (0–1) pendant la parole
    humeur: str = "sourire"        # sourire, neutre, inquiet, surpris, malin
    cligne: float = 0.0
    regard: tuple = (0.0, 0.0)
    question: float = 0.0          # « ? » au-dessus de la tête (0–1)
    gratte: float = 0.0            # traits de grattage près de la main (0–1)
    extra: dict = field(default_factory=dict)


class Baton:
    def pose(self, e):
        pa, pb = POSES[e.pose_a], POSES[e.pose_b]
        u = e.u
        t = e.t
        resp = 3.5 * math.sin(t * 2.1)                      # respiration
        sway = 4.0 * math.sin(t * 0.9)
        inc = lerp(pa["inc"], pb["inc"], u) + 1.2 * math.sin(t * 0.9)
        hip = (HANCHE[0] + sway * 0.4, HANCHE[1] - resp * 0.3)
        ang = math.radians(inc)
        neck = (hip[0] + (COU[1] - HANCHE[1]) * -math.sin(ang) + sway,
                hip[1] + (COU[1] - HANCHE[1]) * math.cos(ang) - resp)
        sh = (neck[0], neck[1] + 22)                         # épaules (point unique sous le cou)
        mains = {}
        for k in ("mg", "md"):
            a, b = pa[k], pb[k]
            # trajectoire en arc : la main passe un peu au-dessus de la ligne droite
            m = lerp2(a, b, u)
            arc = math.sin(math.pi * min(max(u, 0), 1)) * 30
            m = (m[0] + sway + (neck[0] - COU[0]) * 0.8, m[1] - arc - resp * 0.6)
            mains[k] = m
        forme = {k: (pb[f] if u > 0.5 else pa[f]) for k, f in (("mg", "fg"), ("md", "fd"))}
        return hip, neck, sh, mains, forme

    def draw(self, c, e):
        hip, neck, sh, mains, forme = self.pose(e)
        # ombre au sol
        c.drawOval(skia.Rect(-150, -14, 150, 14), P(skia.Color(0, 0, 0, 40)))
        # jambes (pieds fixes, genoux par IK)
        for sd in (-1, 1):
            foot = (sd * 42.0, -14.0)
            hp = (hip[0] + sd * 6, hip[1])
            knee = ik_dehors(hp, foot, L_CUISSE, L_TIBIA, sd, hip[0])
            tube(c, [hp, knee, foot], 9.0)
            # chaussure blanche
            sx = foot[0] + sd * 22
            r = skia.Rect(sx - 34, -22, sx + 34, 2)
            c.drawOval(r, P(WHITE))
            c.drawOval(r, P(INK, 4.5))
        # tronc
        c.drawLine(*hip, *neck, P(INK, 9.0))
        # bras + mains (le bras droit à l'écran d'abord)
        for k, sd in (("md", 1), ("mg", -1)):
            m = mains[k]
            if forme[k] in ("tete", "menton", "hanche"):
                coude = ik_dehors(sh, m, L_BRAS, L_AVBRAS, sd, neck[0])
            else:                                            # coude vers le bas, côté extérieur si égalité
                s1, s2 = ik(sh, m, L_BRAS, L_AVBRAS, 1), ik(sh, m, L_BRAS, L_AVBRAS, -1)
                coude = max((s1, s2), key=lambda q: q[1] + 0.3 * (q[0] - neck[0]) * sd)
            tube(c, [sh, coude, m], 9.0)
            self.main(c, m, coude, forme[k], sd, e)
        self.tete(c, neck, e)

    # -------------------------------------------------------------------------------------------- mains
    def main(self, c, m, coude, forme, sd, e):
        ang = math.degrees(math.atan2(m[1] - coude[1], m[0] - coude[0]))
        c.save()
        c.translate(*m)
        c.rotate(ang)
        fill, ink = P(WHITE), P(INK, 4.5)
        if forme == "index":                                   # poing + index tendu
            c.drawOval(skia.Rect(-4, -17, 30, 17), fill)
            c.drawOval(skia.Rect(-4, -17, 30, 17), ink)
            r = skia.RRect.MakeRectXY(skia.Rect(18, -26, 58, -12), 7, 7)
            c.drawRRect(r, fill)
            c.drawRRect(r, ink)
        elif forme in ("ouverte", "paume", "tete", "menton"):
            c.drawOval(skia.Rect(-2, -15, 28, 15), fill)
            c.drawOval(skia.Rect(-2, -15, 28, 15), ink)
            for k in range(4):                                 # doigts
                a = math.radians(-36 + 24 * k)
                x0, y0 = 22 + 4 * math.cos(a), 14 * math.sin(a)
                x1, y1 = x0 + 22 * math.cos(a), y0 + 22 * math.sin(a)
                if forme == "tete":
                    wig = 4 * math.sin(e.t * 22 + k)          # il se gratte
                    y1 += wig
                c.drawLine(x0, y0, x1, y1, P(INK, 10.5))
                c.drawLine(x0, y0, x1, y1, P(WHITE, 4.5))
            c.drawLine(8, sd * 13, 14, sd * 30, P(INK, 10.5))   # pouce
            c.drawLine(8, sd * 13, 14, sd * 30, P(WHITE, 4.5))
        elif forme == "hanche":                                # poing posé sur la hanche
            c.drawOval(skia.Rect(-4, -15, 26, 15), fill)
            c.drawOval(skia.Rect(-4, -15, 26, 15), ink)
        c.restore()

    # -------------------------------------------------------------------------------------------- tête
    def tete(self, c, neck, e):
        cx, cy = neck[0] + 4, neck[1] - TETE_R - 6
        c.drawLine(*neck, cx, cy + TETE_R - 4, P(INK, 9.0))
        c.drawCircle(cx, cy, TETE_R, P(WHITE))
        c.drawCircle(cx, cy, TETE_R, P(INK, 6.0))
        gx, gy = e.regard[0] * 10 + 8, e.regard[1] * 8
        hum = e.humeur
        # yeux
        for sd in (-1, 1):
            ex, ey = cx + gx + sd * 20, cy - 10 + gy
            if e.cligne > 0.5:
                c.drawLine(ex - 8, ey, ex + 8, ey, P(INK, 4.0))
            else:
                h = 11 if hum != "surpris" else 14
                c.drawOval(skia.Rect(ex - 6, ey - h, ex + 6, ey + h * 0.6), P(INK))
                c.drawCircle(ex - 1.5, ey - h * 0.45, 2.2, P(WHITE))
            # sourcils
            by = ey - 22
            if hum == "inquiet":
                c.drawLine(ex - 10, by - sd * 4 + 2, ex + 10, by + sd * 4, P(INK, 4.0))
            elif hum == "malin":
                c.drawLine(ex - 10, by + (4 if sd < 0 else -4), ex + 10, by + (-2 if sd < 0 else 2), P(INK, 4.0))
            elif hum == "surpris":
                c.drawLine(ex - 9, by - 6, ex + 9, by - 6, P(INK, 4.0))
            else:
                p = skia.Path()
                p.moveTo(ex - 10, by + 2)
                p.quadTo(ex, by - 4, ex + 10, by + 2)
                c.drawPath(p, P(INK, 4.0))
        # bouche
        mx, my = cx + gx * 0.8, cy + 26
        o = e.bouche
        if o > 0.08:
            w, h = 14 + 6 * o, 5 + 16 * o
            if hum == "sourire" or hum == "malin":
                p = skia.Path()
                p.moveTo(mx - w, my - 2)
                p.quadTo(mx, my + h * 1.8, mx + w, my - 2)
                p.close()
                c.drawPath(p, P(INK))
            else:
                c.drawOval(skia.Rect(mx - w * 0.7, my - h / 2, mx + w * 0.7, my + h / 2), P(INK))
        else:
            p = skia.Path()
            if hum == "sourire":
                p.moveTo(mx - 16, my - 4)
                p.quadTo(mx, my + 12, mx + 16, my - 6)
            elif hum == "malin":
                p.moveTo(mx - 14, my)
                p.quadTo(mx + 2, my + 8, mx + 18, my - 8)
            elif hum == "inquiet":
                p.moveTo(mx - 13, my + 5)
                p.quadTo(mx, my - 6, mx + 13, my + 5)
            elif hum == "surpris":
                c.drawCircle(mx, my + 2, 7, P(INK, 4.0))
            else:
                p.moveTo(mx - 12, my + 1)
                p.lineTo(mx + 12, my + 1)
            if hum != "surpris":
                c.drawPath(p, P(INK, 4.5))
        # « ? » et traits de grattage
        if e.question > 0.01:
            q = e.question
            c.save()
            c.translate(cx - 50, cy - TETE_R - 60 - 6 * math.sin(e.t * 3))
            c.scale(q, q)
            f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 110)
            c.drawString("?", -30, 40, f, P(INK))
            c.restore()
        if e.gratte > 0.01:
            for k in range(3):
                a = math.radians(-60 + 25 * k)
                r0 = TETE_R + 12 + 3 * math.sin(e.t * 20 + k)
                x0, y0 = cx + 28 + r0 * math.cos(a), cy - 20 + r0 * math.sin(a)
                c.drawLine(x0, y0, x0 + 12 * math.cos(a), y0 + 12 * math.sin(a),
                           P(skia.Color(18, 18, 22, int(255 * e.gratte)), 4.0))
