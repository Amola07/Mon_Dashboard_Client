"""Épisode 1 — « Pourquoi un triangle fait toujours 180° ? »

La voix off (fichier audio/voix.mp3) enseigne ; l'Orbe découvre et réagit. Toute l'animation est calée sur les
instants mesurés dans l'enregistrement (voir TIMING) : chaque phrase, chaque nombre prononcé.

    python -m films.episodes.ep01_triangle.ep01 sortie.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films.persos.orbe import HUMEUR_DE, Etat, draw_orbe
from films.stick import foley

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.mp3")
VOICE_END = 47.72
# La voix donne une consigne… puis se tait le temps que l'Orbe l'exécute. (instant dans l'enregistrement, pause)
GAPS = [(1.36, 1.9), (6.18, 0.6), (8.8, 0.6), (9.8, 1.0), (11.27, 1.3), (12.96, 0.9), (14.41, 0.9), (16.57, 1.2),
        (17.91, 0.8), (20.76, 2.6), (24.42, 0.9), (27.13, 1.5), (28.88, 1.6), (30.5, 0.6), (34.15, 0.9),
        (37.0, 1.2), (40.65, 2.1), (41.98, 0.7), (43.7, 0.5)]


def N(v):
    """Instant de l'enregistrement → instant dans la vidéo (après insertion des pauses)."""
    return v + sum(g for p, g in GAPS if p < v)


def GS(p):
    """Début de la pause insérée en p (l'Orbe agit à partir de là)."""
    return N(p)


DUR = N(VOICE_END) + 2.2

WHITE = (255, 255, 255)
GOLD = (255, 205, 90)
PINK = (255, 110, 180)
CYAN = (90, 220, 255)
VIOLET = (170, 120, 255)

# ------------------------------------------------------------------------------------------------ minutage (mesuré)
# (texte du sous-titre, début, fin) — instants mesurés sur l'enregistrement (pauses et creux d'énergie)
TIMING = [("Dessine un triangle.", 0.0, 1.16), ("N'importe lequel.", 1.57, 2.32),
          ("Je parie que je connais déjà un nombre caché à l'intérieur.", 2.73, 6.0),
          ("Ce nombre…", 6.37, 6.79), ("c'est 180 !", 7.48, 8.63),
          ("Tu ne me crois pas ?", 8.97, 9.61), ("Mesure ses trois angles.", 9.98, 11.07),
          ("72…", 11.46, 12.76), ("51…", 13.17, 14.25), ("57.", 14.57, 15.37),
          ("Additionne-les.", 15.79, 16.43), ("180.", 16.71, 17.74),
          ("Coïncidence ?", 18.09, 18.98), ("Change la forme du triangle !", 19.26, 20.56),
          ("Les angles changent…", 20.97, 22.2), ("mais leur somme…", 22.65, 23.5), ("jamais.", 23.78, 24.26),
          ("Voici pourquoi.", 24.59, 25.33), ("Découpe les trois coins…", 25.73, 26.95),
          ("…et colle-les côte à côte.", 27.31, 28.7), ("Ils forment une ligne droite.", 29.07, 30.36),
          ("Et une ligne droite,", 30.63, 31.52), ("c'est un demi-tour :", 31.62, 32.36),
          ("180 degrés.", 32.4, 33.18), ("Toujours.", 33.3, 33.96),
          ("Enfin…", 34.34, 34.86), ("presque toujours.", 35.22, 36.82),
          ("Sur une sphère, comme la Terre,", 37.19, 38.4), ("un triangle peut avoir…", 38.4, 39.72),
          ("trois angles droits.", 39.72, 40.51), ("270 degrés !", 40.79, 41.96),
          ("Les règles de la géométrie…", 42.0, 43.52),
          ("dépendent de la surface sur laquelle tu vis.", 43.88, 47.7)]

TIMING = [(txt, N(a_), N(b_)) for txt, a_, b_ in TIMING]
T_DRAW = (GS(1.36) + 0.35, GS(1.36) + 1.75)          # il trace le triangle APRÈS « Dessine un triangle »
T_DROP = N(7.48)                                     # « 180 » tombe (révélation du narrateur)
T_BADGE = GS(9.8) + 0.65                             # « 180 » part en petit badge
T_ANG = (GS(11.27) + 1.2, GS(12.96) + 0.8, GS(14.41) + 0.8)   # chaque angle finit d'être mesuré
T_FLY = GS(16.57) + 0.25                             # il additionne : les nombres volent
T_SUM = N(16.71)                                     # « = 180 »
G0 = GS(20.76)
T_WOB = (G0 + 0.25, N(24.3))                         # il tire sur les sommets
T_LOCK = N(23.78)                                    # « jamais »
T_BACK = N(24.6)                                     # retour à la forme de départ
T_CUT = (GS(27.13) + 0.2, GS(27.13) + 0.65, GS(27.13) + 1.1)   # il découpe les coins
T_MOVE = (GS(28.88) + 0.15, GS(28.88) + 1.45)        # il les porte et les colle
T_LINE = T_MOVE[1] + 0.05                            # ligne droite
T_ARC = N(32.4)                                      # demi-cercle 180°
T_ZOOM = (GS(37.0) + 0.35, GS(37.0) + 1.4)           # on recule : la planète
T_SPH = (GS(40.65) + 0.2, GS(40.65) + 1.4)           # il trace le triangle sur la sphère
T_RIGHT = GS(40.65) + 1.5                            # trois angles droits
T_270 = N(40.79)
T_END = (N(47.7) + 0.4, N(47.7) + 2.0)               # retour à l'image de départ (boucle)

# Orbe : (début, expression, regard) — il écoute, PUIS il agit, puis il réagit
ORBE = [(0.0, "neutre", None), (T_DRAW[0], "neutre", "ray"), (T_DRAW[1] + 0.1, "joie", "tri"),
        (N(2.73), "neutre", None), (GS(6.18) + 0.1, "reflechit", None), (N(6.37), "neutre", "haut"),
        (T_DROP + 0.3, "surpris", "drop"), (GS(9.8) + 0.05, "reflechit", "drop"),
        (GS(11.27) + 0.1, "neutre", "ray"), (T_FLY - 0.05, "neutre", "sum"), (T_SUM + 0.35, "surpris", "sum"),
        (N(18.98) + 0.1, "reflechit", None), (G0 + 0.25, "neutre", "ray"), (N(22.65), "reflechit", "ray"),
        (T_LOCK + 0.35, "triste", "sum"), (N(24.59), "reflechit", "tri"), (GS(27.13) + 0.15, "neutre", "ray"),
        (T_LINE + 0.2, "surpris", "P"), (N(30.63), "reflechit", "P"), (T_ARC + 0.4, "idee", "P"),
        (GS(34.15) + 0.1, "joie", None), (N(34.34) + 0.3, "surpris", None), (N(36.82) + 0.2, "reflechit", None),
        (T_ZOOM[1] - 0.2, "surpris", "planete"), (T_SPH[0], "neutre", "ray"), (T_RIGHT + 0.3, "surpris", "ray"),
        (T_270 + 0.5, "etourdi", None), (N(42.0), "reflechit", "planete"), (N(45.2), "idee", None),
        (N(46.6), "amour", None), (T_END[0] + 0.6, "neutre", "tri")]
# bulles au-dessus de l'Orbe : (instant, symbole) — toujours APRÈS ce qui les provoque
EMO = [(GS(6.18) + 0.15, "?"), (T_DROP + 0.35, "!"), (T_SUM + 0.4, "!"), (N(18.98) + 0.15, "?"),
       (N(22.65) + 0.1, "…"), (T_LINE + 0.25, "!"), (T_ARC + 0.45, "!"), (N(36.82) + 0.25, "?"),
       (T_ZOOM[1] - 0.15, "!"), (T_RIGHT + 0.35, "!")]
# petits sons doux de l'Orbe
CHIRPS = [(T_DRAW[1] + 0.15, "joie"), (GS(6.18) + 0.15, "question"), (T_DROP + 0.35, "surprise"),
          (GS(9.8) + 0.05, "non"), (T_ANG[0] - 0.4, "bip"), (T_ANG[1] - 0.4, "bip"), (T_ANG[2] - 0.4, "bip"),
          (T_SUM + 0.4, "surprise"), (N(18.98) + 0.15, "question"), (T_LOCK + 0.4, "triste"),
          (T_LINE + 0.25, "surprise"), (T_ARC + 0.45, "joie"), (N(36.82) + 0.25, "question"),
          (T_RIGHT + 0.35, "surprise"), (N(45.2), "joie")]

def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def out(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def pop(age, k=1.0):
    """Apparition « pop » : grandit vite avec un petit rebond."""
    if age <= 0:
        return 0.0
    return min(1.0, age / 0.12) * (1 + 0.28 * k * math.exp(-age * 9) * math.sin(age * 26))


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))


def rgb(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def P(color=WHITE, a=255, blur=0.0, stroke=0.0, shader=None):
    p = skia.Paint(AntiAlias=True, Color=rgb(color, a))
    if shader is not None:
        p.setShader(shader)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


FONT = skia.Typeface("DejaVu Sans", skia.FontStyle.Bold())


def text_c(c, s, x, y, size, color=WHITE, a=255, shadow=True):
    f = skia.Font(FONT, size)
    w = f.measureText(s)
    if shadow:
        c.drawString(s, x - w / 2 + 3, y + 4, f, P((0, 0, 0), a * 0.5, blur=4))
    c.drawString(s, x - w / 2, y, f, P(color, a))
    return w


# ------------------------------------------------------------------------------------------------ géométrie
CX, CY = 540.0, 1120.0
A0, B0, C0 = (28.5, -237.3), (-260.0, 119.0), (260.0, 119.0)          # angles : A 72°, B 51°, C 57°
PT = (0.0, 330.0)                                                     # là où les coins se rejoignent


GRAB = [("A", G0 + 0.25, G0 + 1.45, (180.0, 40.0), (190.0, -40.0)),
        ("B", G0 + 1.45, G0 + 2.6, (-80.0, -170.0), (-60.0, -190.0)),
        ("C", G0 + 2.6, N(22.45), (70.0, -150.0), (60.0, -190.0))]      # sommet, fenêtre, déplacement, place de l'Orbe
OFFS = {"A": (0.0, -200.0), "B": (-60.0, -190.0), "C": (60.0, -190.0)}


def tri_at(t):
    """Sommets du triangle (repère centré). Pendant la déformation, l'Orbe tire chaque sommet à son tour."""
    P0 = {"A": A0, "B": B0, "C": C0}
    out_ = dict(P0)
    for name, t0, t1, d, _ in GRAB:
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            k = math.sin(math.pi * u) * (1 + 0.06 * math.sin(u * 30))
            out_[name] = (P0[name][0] + d[0] * k, P0[name][1] + d[1] * k)
    return out_["A"], out_["B"], out_["C"]


def ang(v, a, b):
    """Angle en v (degrés) entre les directions vers a et vers b."""
    d1 = math.atan2(a[1] - v[1], a[0] - v[0])
    d2 = math.atan2(b[1] - v[1], b[0] - v[0])
    d = abs(math.degrees(d1 - d2)) % 360
    return 360 - d if d > 180 else d


def dir_deg(v, a):
    return math.degrees(math.atan2(a[1] - v[1], a[0] - v[0]))


def span(v, a, b):
    """(début, étendue) de l'angle intérieur en v, en degrés écran (sens horaire)."""
    d1, d2 = dir_deg(v, a), dir_deg(v, b)
    s = (d2 - d1) % 360
    return (d1, s) if s <= 180 else (d2, 360 - s)


def angles_display(A, B, C):
    """Valeurs affichées (entiers) : la troisième complète à 180 pour rester exacte à l'écran."""
    a = round(ang(A, B, C))
    b = round(ang(B, A, C))
    return a, b, 180 - a - b


# ------------------------------------------------------------------------------------------------ éléments
def draw_background(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P(shader=skia.GradientShader.MakeLinear(
        [skia.Point(0, 0), skia.Point(0, H)], [rgb((20, 18, 42)), rgb((38, 24, 68)), rgb((16, 28, 58))])))
    c.drawCircle(160 + 30 * math.sin(t * 0.2), 380, 420, P((120, 80, 255), 38, blur=130))
    c.drawCircle(920, 1500 + 40 * math.sin(t * 0.17), 460, P((60, 200, 255), 32, blur=150))
    # grille très discrète (papier millimétré de l'espace)
    for x in range(0, W, 60):
        c.drawLine(x, 0, x, H, P(WHITE, 7, stroke=1))
    for y in range(0, H, 60):
        c.drawLine(0, y, W, y, P(WHITE, 7, stroke=1))


def glow_line(c, a, b, color=WHITE, w=7, alpha=255):
    c.drawLine(*a, *b, P(color, 0.45 * alpha, blur=12, stroke=w * 2.4))
    c.drawLine(*a, *b, P(color, alpha, stroke=w))


def partial_path(pts, u):
    """Tracé progressif d'un polygone fermé (u : 0 → 1)."""
    seg = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    L = [math.dist(a, b) for a, b in seg]
    tot = sum(L)
    rem = u * tot
    out_ = []
    for (a, b), l in zip(seg, L):
        if rem <= 0:
            break
        k = min(1.0, rem / l)
        out_.append((a, lerp2(a, b, k)))
        rem -= l
    return out_


def sector_path(v, start, sweep, r):
    p = skia.Path()
    p.moveTo(*v)
    p.arcTo(skia.Rect(v[0] - r, v[1] - r, v[0] + r, v[1] + r), start, sweep, False)
    p.close()
    return p


VCOL = {"A": GOLD, "B": PINK, "C": CYAN}


def draw_triangle_scene(c, t, s):
    """Le triangle, ses angles, la somme, la découpe et la ligne droite (repère centré en (CX, CY))."""
    A, B, C = tri_at(t)
    V = {"A": (A, B, C), "B": (B, A, C), "C": (C, A, B)}
    cut_done = [t >= tc + 0.35 for tc in T_CUT]
    # --- les côtés
    if t >= T_DRAW[0]:
        u = ease((t - T_DRAW[0]) / (T_DRAW[1] - T_DRAW[0]))
        for a, b in partial_path([A, B, C], u):
            glow_line(c, a, b, WHITE, 7)
        for q in (A, B, C):
            if u > 0.99:
                c.drawCircle(*q, 9, P(WHITE))
    # --- angles : ils se mesurent un par un, puis restent affichés (valeurs vivantes pendant la déformation)
    vals = dict(zip("ABC", angles_display(A, B, C)))
    for k, name in enumerate("ABC"):
        t0 = T_ANG[k]
        if t < t0 - 0.9:
            continue
        v, a, b = V[name]
        st, sw = span(v, a, b)
        grow = ease((t - (t0 - 0.9)) / 1.0)
        moving = T_MOVE[0] <= t
        if cut_done[k] and moving:
            continue                                             # le coin a été découpé et déplacé
        col = VCOL[name]
        r = 66
        if t < t0 + 0.6:                                         # le rapporteur fantôme pendant la mesure
            ra = 120
            prot = skia.Path()
            prot.addArc(skia.Rect(v[0] - ra, v[1] - ra, v[0] + ra, v[1] + ra), st - 20, sw + 40)
            c.drawPath(prot, P(WHITE, 60 * (1 - ease((t - t0) / 0.6)), stroke=2))
            for d in range(0, int(sw + 40), 10):
                aa = math.radians(st - 20 + d)
                c.drawLine(v[0] + (ra - 12) * math.cos(aa), v[1] + (ra - 12) * math.sin(aa),
                           v[0] + ra * math.cos(aa), v[1] + ra * math.sin(aa),
                           P(WHITE, 70 * (1 - ease((t - t0) / 0.6)), stroke=2))
        c.drawPath(sector_path(v, st, sw * grow, r), P(col, 70))
        arc = skia.Path()
        arc.addArc(skia.Rect(v[0] - r, v[1] - r, v[0] + r, v[1] + r), st, sw * grow)
        c.drawPath(arc, P(col, 160, blur=6, stroke=10))
        c.drawPath(arc, P(col, stroke=5))
        # valeur (compte de 0 à la valeur pendant la mesure)
        mid = math.radians(st + sw / 2)
        lp = (v[0] + 118 * math.cos(mid), v[1] + 118 * math.sin(mid) + 16)
        val = vals[name] if t > t0 + 0.2 else int(vals[name] * grow)
        fly = ease((t - T_FLY) / 0.6) if t < T_WOB[0] else 0.0
        if T_FLY <= t < T_WOB[0]:                               # la valeur vole vers la somme
            continue
        sc = pop(t - (t0 - 0.9))
        c.save()
        c.translate(*lp)
        c.scale(sc, sc)
        text_c(c, f"{val}°", 0, 0, 50, col)
        c.restore()
    # --- la somme
    sy = -420.0
    if T_FLY <= t < T_BACK + 0.5:
        a_ = 255 * (1 - ease((t - T_BACK) / 0.5))
        terms = [vals["A"], vals["B"], vals["C"]]
        cols = [GOLD, PINK, CYAN]
        f = skia.Font(FONT, 60)
        parts = [f"{terms[0]}°", " + ", f"{terms[1]}°", " + ", f"{terms[2]}°", " = ", "180°"]
        pcols = [cols[0], WHITE, cols[1], WHITE, cols[2], WHITE, GOLD]
        widths = [f.measureText(x) for x in parts]
        show_eq = t >= T_SUM
        total = sum(widths if show_eq else widths[:5])
        x = -total / 2
        for k, (s_, w_, col) in enumerate(zip(parts, widths, pcols)):
            if k >= 5 and not show_eq:
                break
            if k in (0, 2, 4):                                   # chaque terme arrive de son sommet
                name = "ABC"[k // 2]
                v, a, b = V[name]
                st, sw = span(v, a, b)
                mid = math.radians(st + sw / 2)
                src = (v[0] + 118 * math.cos(mid) - w_ / 2, v[1] + 118 * math.sin(mid) + 16)
                u = out((t - T_FLY - 0.08 * k) / 0.55)
                pos = lerp2(src, (x, sy), u)
            else:
                pos = (x, sy)
            al = a_ * (min(1.0, (t - T_FLY) / 0.3) if k in (1, 3) else 1.0)
            if k >= 5:
                al = a_ * min(1.0, (t - T_SUM) / 0.15)
            if k == 6:
                sc = pop(t - T_SUM) * (1 + (0.25 * math.exp(-(t - T_LOCK) * 5) if t > T_LOCK else 0))
                c.save()
                c.translate(pos[0] + w_ / 2, pos[1] - 20)
                c.scale(sc, sc)
                c.drawString(s_, -w_ / 2 + 3, 24, f, P((0, 0, 0), al * 0.5, blur=4))
                c.drawString(s_, -w_ / 2, 20, f, P(col, al))
                if t > T_LOCK:                                   # verrouillé
                    glowa = al * (0.5 + 0.5 * math.sin((t - T_LOCK) * 6))
                    c.drawRoundRect(skia.Rect(-w_ / 2 - 14, -34, w_ / 2 + 14, 40), 18, 18,
                                    P(GOLD, glowa * 0.8, stroke=4))
                c.restore()
            else:
                c.drawString(s_, pos[0] + 3, pos[1] + 4, f, P((0, 0, 0), al * 0.5, blur=4))
                c.drawString(s_, pos[0], pos[1], f, P(col, al))
            x += w_
    # --- la découpe : pointillés de coupe sur chaque coin
    for k, name in enumerate("ABC"):
        tc = T_CUT[k]
        if not (tc <= t < T_MOVE[0] + 0.2):
            continue
        v, a, b = V[name]
        st, sw = span(v, a, b)
        u = ease((t - tc) / 0.35)
        cut = skia.Path()
        cut.addArc(skia.Rect(v[0] - 82, v[1] - 82, v[0] + 82, v[1] + 82), st, sw * u)
        eff = skia.DashPathEffect.Make([12, 10], -t * 60)
        pp = P(WHITE, 230, stroke=4)
        pp.setPathEffect(eff)
        c.drawPath(cut, pp)
    # --- les coins découpés glissent vers PT et se collent en ligne droite
    if t >= T_MOVE[0]:
        targets = {"B": -180.0, "A": -129.0, "C": -57.0}         # début de chaque secteur une fois collé
        sweeps = {"B": 51.0, "A": 72.0, "C": 57.0}
        spins = {"B": -129.0, "A": 174.0, "C": 123.0}
        for k, name in enumerate(("B", "A", "C")):
            v, a, b = V[name]
            st, sw = span(v, a, b)
            u = ease((t - T_MOVE[0] - 0.12 * k) / (T_MOVE[1] - T_MOVE[0] - 0.24))
            pos = lerp2(v, PT, u)
            rot = spins[name] * u
            col = VCOL[name]
            c.save()
            c.translate(*pos)
            c.rotate(rot)
            path = sector_path((0, 0), st, sw, 82)
            c.drawPath(path, P(col, 110))
            c.drawPath(path, P(col, stroke=4))
            c.restore()
            if u >= 1 and t > T_MOVE[1]:
                mid = math.radians(targets[name] + sweeps[name] / 2)
                text_c(c, f"{int(sweeps[name])}°", PT[0] + 128 * math.cos(mid),
                       PT[1] + 128 * math.sin(mid) + 14, 40, col, 255 * ease((t - T_MOVE[1]) / 0.3))
    # --- la ligne droite, puis le demi-tour
    if t >= T_LINE:
        u = out((t - T_LINE) / 0.5)
        glow_line(c, (PT[0] - 330 * u, PT[1]), (PT[0] + 330 * u, PT[1]), WHITE, 6)
    if t >= T_ARC:
        u = ease((t - T_ARC) / 0.6)
        arc = skia.Path()
        arc.addArc(skia.Rect(PT[0] - 200, PT[1] - 200, PT[0] + 200, PT[1] + 200), 180, 180 * u)
        c.drawPath(arc, P(GOLD, 150, blur=10, stroke=14))
        c.drawPath(arc, P(GOLD, stroke=6))
        if u > 0.9:
            sc = pop(t - T_ARC - 0.55)
            c.save()
            c.translate(PT[0], PT[1] - 250)
            c.scale(sc, sc)
            text_c(c, "180°", 0, 0, 80, GOLD)
            c.restore()


def draw_drop(c, t):
    """Le grand « 180° » qui tombe, rebondit, puis part en badge."""
    if t < T_DROP or t > T_FLY:
        return
    a = t - T_DROP
    y_land = 720.0
    if a < 0.35:
        y = -150 + (y_land + 150) * (a / 0.35) ** 2
        sq = 0.0
    else:
        b = a - 0.35
        y = y_land - 60 * abs(math.sin(b * 9)) * math.exp(-b * 5)
        sq = 0.25 * math.exp(-b * 9) * math.cos(b * 22)
    x, s = 540.0, 1.0
    if t > T_BADGE:
        u = ease((t - T_BADGE) / 0.6)
        x, y, s = lerp(540, 900, u), lerp(y_land, 270, u), lerp(1.0, 0.42, u)
    al = 255 * (1 - ease((t - (T_FLY - 0.4)) / 0.4))
    c.save()
    c.translate(x, y)
    c.scale(s * (1 + sq), s * (1 - sq))
    c.drawCircle(0, -40, 150, P(GOLD, 60 * al / 255, blur=50))
    text_c(c, "180°", 0, 0, 190, GOLD, al)
    c.restore()


# ------------------------------------------------------------------------------------------------ la planète
PC, PR = (560.0, 1120.0), 330.0
TILT = math.radians(24)


def proj(lat, lon, scale=1.0, cx=PC[0], cy=PC[1]):
    la, lo = math.radians(lat), math.radians(lon)
    x = PR * math.cos(la) * math.sin(lo)
    y0 = PR * math.sin(la)
    z0 = PR * math.cos(la) * math.cos(lo)
    y = y0 * math.cos(TILT) - z0 * math.sin(TILT)
    z = y0 * math.sin(TILT) + z0 * math.cos(TILT)
    return (cx + x * scale, cy - y * scale), z


def draw_planet(c, t, scale, alpha):
    if alpha <= 0:
        return
    cx, cy = PC
    R = PR * scale
    c.drawCircle(cx, cy, R * 1.15, P((80, 170, 255), 70 * alpha / 255, blur=60))
    sphere = skia.Path()
    sphere.addCircle(cx, cy, R)
    grad = skia.GradientShader.MakeRadial(skia.Point(cx - R * 0.35, cy - R * 0.4), R * 1.4,
                                          [rgb((120, 210, 255), alpha), rgb((40, 110, 210), alpha),
                                           rgb((18, 40, 110), alpha)], [0.0, 0.55, 1.0])
    c.drawPath(sphere, P(shader=grad))
    c.save()
    c.clipPath(sphere, doAntiAlias=True)
    for k in range(4):                                           # continents stylisés (taches douces)
        a = k * 1.7 + t * 0.12
        q, z = proj(20 * math.sin(k * 2.1), math.degrees(a) % 360 - 180, scale)
        if z > 0:
            c.drawCircle(*q, R * (0.2 + 0.05 * k), P((90, 220, 170), 80 * alpha / 255, blur=R * 0.06))
    for lat in range(-60, 90, 30):                               # parallèles
        path = skia.Path()
        first = True
        for lon in range(-180, 181, 6):
            q, z = proj(lat, lon, scale)
            if z < 0:
                first = True
                continue
            path.moveTo(*q) if first else path.lineTo(*q)
            first = False
        c.drawPath(path, P(WHITE, (70 if lat == 0 else 28) * alpha / 255, stroke=2 if lat else 3))
    for lon in range(-180, 180, 30):                             # méridiens
        path = skia.Path()
        first = True
        for lat in range(-90, 91, 5):
            q, z = proj(lat, lon, scale)
            if z < 0:
                first = True
                continue
            path.moveTo(*q) if first else path.lineTo(*q)
            first = False
        c.drawPath(path, P(WHITE, 28 * alpha / 255, stroke=2))
    c.drawCircle(cx - R * 0.35, cy - R * 0.45, R * 0.35, P(WHITE, 60 * alpha / 255, blur=R * 0.2))
    c.restore()
    c.drawCircle(cx, cy, R, P(WHITE, 90 * alpha / 255, stroke=3))


def sphere_triangle(t, scale):
    """Les trois côtés du triangle sphérique : pôle Nord → équateur (lon -45) → équateur (lon +45) → pôle."""
    e1 = [proj(90 - k, -45, scale)[0] for k in range(0, 91, 3)]
    e2 = [proj(0, -45 + k, scale)[0] for k in range(0, 91, 3)]
    e3 = [proj(k, 45, scale)[0] for k in range(0, 91, 3)]
    return [e1, e2, e3]


def draw_sphere_triangle(c, t, scale):
    if t < T_SPH[0]:
        return
    edges = sphere_triangle(t, scale)
    u = ease((t - T_SPH[0]) / (T_SPH[1] - T_SPH[0])) * 3
    for k, pts in enumerate(edges):
        kk = min(1.0, max(0.0, u - k))
        if kk <= 0:
            continue
        n = max(2, int(len(pts) * kk))
        path = skia.Path()
        path.moveTo(*pts[0])
        for q in pts[1:n]:
            path.lineTo(*q)
        c.drawPath(path, P(GOLD, 150, blur=10, stroke=14))
        c.drawPath(path, P(GOLD, stroke=6))
    if t >= T_RIGHT:                                             # trois angles droits
        corners = [(proj(90, 0, scale)[0], proj(82, -45, scale)[0], proj(82, 45, scale)[0]),
                   (proj(0, -45, scale)[0], proj(8, -45, scale)[0], proj(0, -37, scale)[0]),
                   (proj(0, 45, scale)[0], proj(8, 45, scale)[0], proj(0, 37, scale)[0])]
        for k, (v, a, b) in enumerate(corners):
            age = t - T_RIGHT - 0.18 * k
            if age <= 0:
                continue
            s = pop(age)
            m = (a[0] + b[0] - v[0], a[1] + b[1] - v[1])
            path = skia.Path()
            path.moveTo(*lerp2(v, a, s))
            path.lineTo(*lerp2(v, m, s))
            path.lineTo(*lerp2(v, b, s))
            c.drawPath(path, P(WHITE, stroke=5))
            c.drawCircle(*v, 8 * s, P(WHITE))
            lab = (v[0] + (v[0] - PC[0]) * 0.25, v[1] + (v[1] - PC[1]) * 0.25 + (-30 if k == 0 else 50))
            text_c(c, "90°", lab[0], lab[1], 40, WHITE, 255 * min(1.0, age / 0.2))
    if t >= T_270:
        sc = pop(t - T_270)
        c.save()
        c.translate(PC[0], PC[1] - PR * scale - 190)
        c.scale(sc, sc)
        c.drawCircle(0, -40, 150, P(GOLD, 60, blur=50))
        text_c(c, "270°", 0, 0, 150, GOLD)
        c.restore()


# ------------------------------------------------------------------------------------------------ l'Orbe
def orbe_state(t, targets):
    cur, prev = ORBE[0], ORBE[0]
    for s_ in ORBE:
        if t >= s_[0]:
            prev, cur = cur, s_
    t0, expr, gaze = cur
    a = t - t0
    e = Etat(expr=expr, age=a, humeur_mix=a / 0.6,
             humeur_avant=HUMEUR_DE.get(prev[1], "calme") if prev is not cur else "calme")
    e.cligne = (t % 3.3) < 0.12
    return e, targets.get(gaze)


def scr(q):
    return (CX + q[0], CY + q[1])


def pen_tip(t):
    u = ease((t - T_DRAW[0]) / (T_DRAW[1] - T_DRAW[0]))
    segs = partial_path([A0, B0, C0], max(u, 1e-4))
    return scr(segs[-1][1]) if segs else scr(A0)


def sphere_pen(t):
    edges = sphere_triangle(t, 1.0)
    u = ease((t - T_SPH[0]) / (T_SPH[1] - T_SPH[0])) * 3
    k = min(2, int(u))
    kk = min(1.0, u - k)
    pts = edges[k]
    return pts[min(len(pts) - 1, int(kk * (len(pts) - 1)))]


def pieces_now(t):
    """Position écran des coins découpés pendant qu'ils glissent (ordre B, A, C)."""
    A, B, C = tri_at(t)
    V = {"A": A, "B": B, "C": C}
    out_ = []
    for k, name in enumerate(("B", "A", "C")):
        u = ease((t - T_MOVE[0] - 0.12 * k) / (T_MOVE[1] - T_MOVE[0] - 0.24))
        out_.append(scr(lerp2(V[name], PT, u)))
    return out_


def ray_at(t):
    """Le rayon de l'Orbe (ce qu'il touche, et depuis quand) : c'est lui qui trace, mesure, tire, découpe, porte."""
    A, B, C = tri_at(t)
    V = {"A": A, "B": B, "C": C}
    if T_DRAW[0] <= t < T_DRAW[1] + 0.1:
        return pen_tip(t), T_DRAW[0]
    for name, t0, t1 in (("A", GS(11.27) + 0.45, GS(12.96)), ("B", GS(12.96) + 0.4, GS(14.41)),
                         ("C", GS(14.41) + 0.4, T_FLY - 0.2)):
        if t0 <= t < t1:
            return scr(V[name]), t0
    for name, t0, t1, _, _ in GRAB:
        if t0 <= t < t1:
            return scr(V[name]), t0
    for k, tc in enumerate(T_CUT):
        if tc - 0.05 <= t < tc + 0.4:
            name = "ABC"[k]
            v, a, b = {"A": (A, B, C), "B": (B, A, C), "C": (C, A, B)}[name]
            st, sw = span(v, a, b)
            aa = math.radians(st + sw * ease((t - tc) / 0.35))
            return scr((v[0] + 82 * math.cos(aa), v[1] + 82 * math.sin(aa))), tc - 0.05
    if T_MOVE[0] <= t < T_MOVE[1]:
        k = min(2, int((t - T_MOVE[0]) / 0.45))
        return pieces_now(t)[k], T_MOVE[0] + 0.45 * k
    if T_SPH[0] <= t < T_SPH[1]:
        return sphere_pen(t), T_SPH[0]
    if T_SPH[1] <= t < T_RIGHT + 0.8:
        return proj(90, 0, 1.0)[0], T_SPH[1]
    return None


def orbe_target(t):
    """Où l'Orbe veut être (x, y, taille) : il va là où se passe l'action."""
    A, B, C = tri_at(t)
    V = {"A": A, "B": B, "C": C}
    near = lambda name, off=None: (scr(V[name])[0] + (off or OFFS[name])[0],
                                   scr(V[name])[1] + (off or OFFS[name])[1])
    if t < T_DRAW[1] + 0.1:
        x, y = pen_tip(t)
        return x, y - 230, 0.75
    if t < N(2.73):
        return 540, 600, 0.8
    if t < T_DROP - 0.2:
        return 540, 560, 0.9
    if t < GS(11.27) + 0.1:
        return 540, 420, 0.85
    for name, t0, t1 in (("A", GS(11.27) + 0.1, GS(12.96)), ("B", GS(12.96), GS(14.41)),
                         ("C", GS(14.41), T_FLY - 0.3)):
        if t0 <= t < t1:
            x, y = near(name, (-40 if name == "B" else 40 if name == "C" else 0, -230))
            return x, y, 0.8
    if t < GRAB[0][1] - 0.1:
        return 540, 450, 0.8
    for name, t0, t1, _, off in GRAB:
        if t0 - 0.1 <= t < t1:
            x, y = near(name, off)
            return x, y, 0.72
    if t < T_CUT[0] - 0.25:
        return 540, 450, 0.8
    for k, tc in enumerate(T_CUT):
        if t < tc + 0.4:
            x, y = near("ABC"[k])
            return x, y, 0.7
    if t < T_MOVE[1] + 0.2:
        return 870, 1380, 0.7
    if t < T_ARC - 0.1:
        return 540, 560, 0.8
    if t < N(34.34):
        return 540, 530, 0.95
    if t < T_ZOOM[0]:
        return 540, 560, 0.85
    if t < T_SPH[0]:
        return 330, 720, 0.6
    if t < T_SPH[1]:
        x, y = sphere_pen(t)
        d = (x - PC[0], y - PC[1])
        n = math.hypot(*d) or 1.0
        return x + d[0] / n * 150, y + d[1] / n * 150, 0.6
    if t < T_RIGHT + 0.9:
        p = proj(90, 0, 1.0)[0]
        return p[0] - 190, p[1] - 80, 0.6
    if t < T_END[0] + 0.3:
        return 190, 560, 0.62
    x, y = pen_tip(0.0)
    return x, y - 230, 0.75


_POSE = {}


def orbe_pose(t):
    """Position et taille de l'Orbe : il suit sa cible avec un ressort (il se déplace, il ne se téléporte pas)."""
    if not _POSE:
        n = int(DUR * FPS) + 2
        x, y, s = orbe_target(0.0)
        vx = vy = vs = 0.0
        sub = 4
        h = 1.0 / (FPS * sub)
        w = 11.0
        for f in range(n):
            _POSE[f] = (x, y, s)
            for k in range(sub):
                tx, ty, ts = orbe_target((f + k / sub) / FPS)
                vx += (w * w * (tx - x) - 2 * 0.8 * w * vx) * h
                vy += (w * w * (ty - y) - 2 * 0.8 * w * vy) * h
                vs += (w * w * (ts - s) - 2 * 0.9 * w * vs) * h
                x, y, s = x + vx * h, y + vy * h, s + vs * h
    f = t * FPS
    i = min(int(f), len(_POSE) - 2)
    u = f - i
    a, b = _POSE[i], _POSE[i + 1]
    x, y, s = (a[j] + (b[j] - a[j]) * u for j in range(3))
    y += 8 * math.sin(t * 2.1)
    h0 = GS(9.8) + 0.05
    if h0 <= t < h0 + 0.9:                                      # « non, je n'y crois pas » : il secoue la tête
        x += 22 * math.sin((t - h0) * 16) * (1 - (t - h0) / 0.9)
    if GRAB[0][1] <= t < GRAB[2][2]:                            # l'effort : il tremble en tirant
        x += 3 * math.sin(t * 60)
    b0 = T_ARC + 0.4
    if b0 <= t < b0 + 0.6:                                      # le déclic : il bondit
        y -= 60 * math.sin(math.pi * (t - b0) / 0.6)
    return (x, y), s


def draw_beam(c, t, orig, s):
    r = ray_at(t)
    if r is None:
        return None
    (tx, ty), t0 = r
    d = (tx - orig[0], ty - orig[1])
    n = math.hypot(*d) or 1.0
    ux, uy = d[0] / n, d[1] / n
    sx, sy = orig[0] + ux * 140 * s, orig[1] + uy * 140 * s
    g = ease((t - t0) / 0.18)
    ex, ey = sx + (tx - sx) * g, sy + (ty - sy) * g
    c.drawLine(sx, sy, ex, ey, P(CYAN, 110, blur=10, stroke=18))
    c.drawLine(sx, sy, ex, ey, P(WHITE, 235, stroke=5))
    if g > 0.95:
        pulse = 1 + 0.2 * math.sin(t * 10)
        c.drawCircle(tx, ty, 24 * pulse, P(CYAN, 130, blur=12))
        c.drawCircle(tx, ty, 9, P(WHITE))
    return (tx, ty)


def draw_emote(c, t, x, y, s):
    for t0, sym in EMO:
        a = t - t0
        if 0 <= a < 1.3:
            al = 255 * min(1.0, (1.3 - a) / 0.3)
            sc = pop(a) * s * 1.5
            c.save()
            c.translate(x + 120 * s, y - 170 * s - 18 * min(1.0, a / 0.4))
            c.scale(sc, sc)
            c.drawCircle(0, -30, 46, P(WHITE, al * 0.9))
            c.drawCircle(0, -30, 46, P(VIOLET, al, stroke=4))
            tail = skia.Path()
            tail.moveTo(-22, 6)
            tail.lineTo(-40, 30)
            tail.lineTo(-4, 12)
            tail.close()
            c.drawPath(tail, P(WHITE, al * 0.9))
            if sym == "…":
                for k in range(3):
                    on = int(a * 5) % 4 > k
                    c.drawCircle(-18 + k * 18, -30, 7, P((60, 40, 110), al if on else al * 0.3))
            else:
                f = skia.Font(FONT, 60)
                w = f.measureText(sym)
                c.drawString(sym, -w / 2, -9, f, P((60, 40, 110), al))
            c.restore()


def draw_orbe_at(c, t, targets):
    (x, y), s = orbe_pose(t)
    hit = draw_beam(c, t, (x, y), s)
    targets = dict(targets, ray=hit)
    e, g = orbe_state(t, targets)
    if g is not None:
        d = (g[0] - x, g[1] - y)
        n = math.hypot(*d) or 1.0
        k = min(1.0, n / 200)
        e.regard = (0.75 * d[0] / n * k, 0.75 * d[1] / n * k)
    elif e.expr == "reflechit":
        e.regard = (0.6 * ease(e.age / 0.3), -0.6 * ease(e.age / 0.3))
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    draw_orbe(c, t, e)
    c.restore()
    draw_emote(c, t, x, y, s)


# ------------------------------------------------------------------------------------------------ sous-titres
def draw_subtitle(c, t):
    cur = None
    for k, (txt, t0, t1) in enumerate(TIMING):
        nxt = TIMING[k + 1][1] if k + 1 < len(TIMING) else t1 + 1.0
        if t0 - 0.05 <= t < min(nxt, t1 + 0.9):
            cur = (txt, t0)
    if cur is None:
        return
    txt, t0 = cur
    words = txt.split(" ")
    lines, line = [], ""
    for w_ in words:
        if len(line) + len(w_) + 1 > 24 and line:
            lines.append(line)
            line = w_
        else:
            line = (line + " " + w_).strip()
    lines.append(line)
    sc = pop(t - t0 + 0.05, 0.6)
    f = skia.Font(FONT, 64)
    c.save()
    c.translate(540, 1690 - 40 * (len(lines) - 1))
    c.scale(sc, sc)
    for i, ln in enumerate(lines):
        y = i * 82
        w = f.measureText(ln)
        x = -w / 2
        for token in ln.split(" "):
            tw = f.measureText(token + " ")
            col = GOLD if any(ch.isdigit() for ch in token) else WHITE
            outline = P((10, 8, 30), 255, stroke=12)
            c.drawString(token, x, y, f, outline)
            c.drawString(token, x, y, f, P(col))
            x += tw
    c.restore()


# ------------------------------------------------------------------------------------------------ image complète
def frame(c, t):
    draw_background(c, t)
    zoom = ease((t - T_ZOOM[0]) / (T_ZOOM[1] - T_ZOOM[0]))
    endk = ease((t - T_END[0]) / (T_END[1] - T_END[0]))
    A, B, C = tri_at(t)
    tri_scale = lerp(1.0, 0.25, zoom)
    tri_alpha = 1 - zoom                                        # on recule : il rétrécit et s'efface
    if tri_alpha > 0.01:
        layer = skia.Surface(W, H)
        lc = layer.getCanvas()
        lc.clear(skia.ColorTRANSPARENT)
        lc.translate(CX, CY - 260 * zoom)
        lc.scale(tri_scale, tri_scale)
        draw_triangle_scene(lc, t, tri_scale)
        c.drawImage(layer.makeImageSnapshot(), 0, 0, skia.SamplingOptions(), P(WHITE, 255 * tri_alpha))
    # la planète
    if zoom > 0 and t < T_END[1]:
        pa = zoom * (1 - endk)
        ps = lerp(0.3, 1.0, out(zoom))
        draw_planet(c, t, ps, 255 * pa)
        if pa > 0.9:
            layer = skia.Surface(W, H)
            lc = layer.getCanvas()
            lc.clear(skia.ColorTRANSPARENT)
            draw_sphere_triangle(lc, t, ps)
            c.drawImage(layer.makeImageSnapshot(), 0, 0, skia.SamplingOptions(), P(WHITE, 255 * min(1.0, (1 - endk) * 1.2)))
    draw_drop(c, t)
    # l'Orbe : cibles du regard et du rayon
    to_screen = lambda q: (CX + q[0], CY + q[1])
    targets = {"tri": (CX, CY), "A": to_screen(A), "B": to_screen(B), "C": to_screen(C), "haut": (540, 0),
               "drop": (540, 720), "sum": (540, CY - 420), "P": to_screen(PT), "planete": PC}
    draw_orbe_at(c, t, targets)
    draw_subtitle(c, t)


# ------------------------------------------------------------------------------------------------ son
SR = foley.SR


def tone(freq, dur, amp=0.3, attack=0.005, decay=0.3, harm=((1, 1.0),)):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * freq * h * tt) for h, a in harm)
    env = np.minimum(1, tt / attack) * np.exp(-tt / decay)
    return y * env * amp


def soften(y, k=18):
    """Filtre passe-bas simple : arrondit tous les sons (rien d'aigu ni de claquant)."""
    return np.convolve(y, np.ones(k) / k, mode="same")


def ding(f=880, amp=0.25):
    """Clochette douce : une octave plus grave, attaque lente, presque pure (marimba feutré)."""
    f = f / 2
    return tone(f, 1.4, amp * 0.8, 0.012, 0.5, ((1, 1.0), (2, 0.12), (4, 0.03)))


def pop_s(f=600, amp=0.3):
    """« Bloop » rond et grave (bulle), au lieu d'un clic."""
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    fr = f * 0.4 * (1 + 0.35 * np.minimum(1, tt / 0.1))
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.minimum(1, tt / 0.012) * np.exp(-tt / 0.07)
    return y * amp * 0.7


def sparkle(amp=0.15):
    """Petit carillon doux (trois notes montantes, graves et feutrées)."""
    out_ = np.zeros(int(1.6 * SR))
    for k, f in enumerate((523.25, 659.25, 783.99)):
        s_ = tone(f, 1.2, amp * 0.6, 0.02, 0.45, ((1, 1.0), (2, 0.08)))
        i = int(k * 0.12 * SR)
        m = min(len(out_) - i, len(s_))
        out_[i:i + m] += s_[:m]
    return out_


def scribble(dur, amp=0.12):
    """Crayon feutré : bruit très filtré, doux."""
    n = int(dur * SR)
    x = np.random.default_rng(5).standard_normal(n)
    x = soften(soften(x, 40), 40)
    tt = np.arange(n) / SR
    env = (0.7 + 0.3 * np.sin(tt * 18)) * np.minimum(1, tt / 0.1) * np.minimum(1, (dur - tt) / 0.15)
    return x * env * amp * 2.2


def swish(dur, amp=0.25):
    """Souffle doux (mouvement), grave et filtré."""
    n = int(dur * SR)
    x = soften(soften(np.random.default_rng(9).standard_normal(n), 60), 60)
    tt = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    return x * env * amp * 3.0


def tock(amp=0.25):
    """« Toc » de bois feutré (quand deux pièces se collent)."""
    return tone(170, 0.35, amp, 0.004, 0.07, ((1, 1.0), (2.6, 0.15)))


def swell(amp=0.25):
    """Nappe grave qui gonfle (grande révélation), sans explosion."""
    n = int(2.0 * SR)
    tt = np.arange(n) / SR
    env = np.minimum(1, tt / 0.35) * np.exp(-np.maximum(0, tt - 0.35) / 0.7)
    return (np.sin(2 * np.pi * 110 * tt) + 0.5 * np.sin(2 * np.pi * 165 * tt)
            + 0.25 * np.sin(2 * np.pi * 220 * tt)) * env * amp


def music(dur):
    """Nappe douce (accords la mineur – fa – do – sol) + petites notes pincées, très discrètes."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.zeros(n)
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]
    bar = 3.0
    for k in range(int(dur / bar) + 1):
        ch = chords[k % 4]
        i0 = int(k * bar * SR)
        seg = np.arange(int(bar * 1.3 * SR)) / SR
        env = np.minimum(1, seg / 0.8) * np.minimum(1, np.maximum(0, (bar * 1.3 - seg) / 0.8))
        s = sum(np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(2 * np.pi * 2 * f * seg) for f in ch) * env * 0.035
        m = min(n - i0, len(s))
        if m > 0:
            y[i0:i0 + m] += s[:m]
        for j in range(4):                                      # notes pincées
            f = ch[j % 3] * 2
            p = tone(f, 1.0, 0.04, 0.02, 0.35, ((1, 1.0), (2, 0.06)))
            i = i0 + int(j * bar / 4 * SR)
            m = min(n - i, len(p))
            if m > 0:
                y[i:i + m] += p[:m]
    return y


def chirp(f0, f1, dur, amp=0.22):
    """Voyelle douce de l'Orbe : sinus pur, glissé lent, attaque et chute arrondies."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    f = f0 + (f1 - f0) * (u * u * (3 - 2 * u))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.08 * np.sin(2 * ph)
    env = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.5
    return y * env * amp * 0.55


def seq(*parts):
    out_ = np.zeros(0)
    for p in parts:
        out_ = np.concatenate([out_, p if isinstance(p, np.ndarray) else np.zeros(int(p * SR))])
    return out_


def orbe_voice(kind):
    """La « voix » de l'Orbe : de petits « hmm ? », « oh ! », « mmm » doux et graves (jamais aigus)."""
    if kind == "question":
        return seq(chirp(260, 280, 0.14), 0.03, chirp(280, 420, 0.24))
    if kind == "surprise":
        return chirp(300, 520, 0.26, 0.26)
    if kind == "joie":
        return seq(chirp(330, 350, 0.12), 0.02, chirp(392, 410, 0.12), 0.02, chirp(494, 523, 0.2))
    if kind == "triste":
        return chirp(380, 230, 0.55, 0.2)
    if kind == "non":
        return seq(chirp(330, 290, 0.16), 0.08, chirp(330, 280, 0.18))
    if kind == "effort":
        return chirp(200, 230, 0.2, 0.16)
    return chirp(420, 440, 0.12, 0.14)


def soundtrack(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOIX, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    voice = np.frombuffer(raw, np.int16).astype(float) / 32768
    n = int(DUR * SR)
    mix = np.zeros(n)
    # la voix, découpée aux pauses et replacée avec les silences d'action
    cuts = [0.0] + [p for p, _ in GAPS] + [len(voice) / SR]
    for a_, b_ in zip(cuts, cuts[1:]):
        chunk = voice[int(a_ * SR):int(b_ * SR)]
        i = int(N(a_ + 1e-6) * SR)
        m = min(n - i, len(chunk))
        if m > 0:
            mix[i:i + m] += chunk[:m]
    fx = np.zeros(n)

    def add(t, s_, g=1.0):
        i = int(t * SR)
        m = min(n - i, len(s_))
        if m > 0:
            fx[i:i + m] += s_[:m] * g

    add(T_DRAW[0], scribble(T_DRAW[1] - T_DRAW[0]))
    add(T_DROP - 0.1, swish(0.45, 0.2))
    add(T_DROP + 0.35, tock(0.3))
    add(T_DROP + 0.35, ding(660, 0.16))
    for k, t0 in enumerate(T_ANG):
        add(t0 - 0.9, swish(0.9, 0.08))
        add(t0 + 0.1, ding(660 + 110 * k, 0.12))
    add(T_FLY, swish(0.6, 0.18))
    add(T_SUM, ding(880, 0.16))
    add(T_SUM + 0.12, ding(1100, 0.1))
    for _, t0, _, _, _ in GRAB:
        add(t0, swish(0.9, 0.12))
    add(T_LOCK, tock(0.28))
    for tc in T_CUT:
        add(tc, swish(0.35, 0.14))
    add(T_MOVE[0], swish(1.3, 0.16))
    add(T_MOVE[1] - 0.05, tock(0.28))
    add(T_LINE + 0.1, sparkle(0.12))
    add(T_ARC, ding(523, 0.16))
    add(T_ARC + 0.15, ding(784, 0.12))
    add(T_ARC + 0.45, sparkle(0.12))
    add(T_ZOOM[0], swish(1.3, 0.2))
    add(T_SPH[0], scribble(T_SPH[1] - T_SPH[0], 0.1))
    for k in range(3):
        add(T_RIGHT + 0.18 * k, pop_s(700 + 100 * k, 0.25))
    add(T_270, swell(0.18))
    add(T_270, ding(587, 0.15))
    add(N(45.2), sparkle(0.12))
    for t0, kind in CHIRPS:
        add(t0, orbe_voice(kind), 0.9)
    add(T_END[0], swish(1.4, 0.15))
    mus = music(DUR)
    # la musique s'efface sous la voix (ducking)
    env = np.abs(mix)
    k = int(0.15 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = 1 - 0.55 * np.minimum(1, env / 0.05)
    out_ = mix + soften(fx, 6) * 0.8 + mus * duck
    out_ = np.tanh(out_ * 1.3) / np.tanh(1.3)
    stereo = np.stack([out_, out_], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(stereo, -1, 1) * 32767).astype(np.int16).tobytes())


def render(out_path, t0=0.0, t1=DUR):
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(t0 * FPS), int(t1 * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    wav = f"{tmp}/a.wav"
    soundtrack(wav)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-ss", str(t0), "-t", str(t1 - t0), "-i", wav,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "output/ep01_triangle.mp4"
    render(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
