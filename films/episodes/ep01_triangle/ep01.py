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
DUR = 49.2

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

T_DRAW = (0.1, 1.5)                  # le triangle se trace
T_DROP = 7.5                         # « 180 » tombe
T_BADGE = 9.9                        # « 180 » part en petit badge
T_ANG = (11.46, 13.17, 14.57)        # 72 (A), 51 (B), 57 (C)
T_FLY = 15.8                         # les nombres volent vers la somme
T_SUM = 16.71                        # « = 180 »
T_WOB = (19.3, 24.3)                 # déformation du triangle
T_LOCK = 23.78                       # « jamais »
T_BACK = 24.6                        # retour à la forme de départ
T_CUT = (25.8, 26.2, 26.6)           # découpe des trois coins
T_MOVE = (27.3, 28.6)                # les coins glissent et se collent
T_LINE = 29.1                        # ligne droite
T_ARC = 32.4                         # demi-cercle 180°
T_ZOOM = (36.2, 37.4)                # on recule : la planète
T_SPH = (38.4, 39.7)                 # triangle tracé sur la sphère
T_RIGHT = 39.72                      # trois angles droits
T_270 = 40.79
T_END = (46.9, 48.6)                 # retour à l'image de départ (boucle)

# Orbe : (début, expression, regard)
ORBE = [(0.0, "neutre", "tri"), (1.57, "joie", "tri"), (2.73, "reflechit", None), (6.37, "neutre", "haut"),
        (7.5, "surpris", "drop"), (8.97, "reflechit", None), (9.98, "neutre", "A"), (11.46, "neutre", "A"),
        (13.17, "neutre", "B"), (14.57, "neutre", "C"), (15.79, "reflechit", "sum"), (16.71, "surpris", "sum"),
        (18.09, "reflechit", None), (19.26, "neutre", "tri"), (22.65, "reflechit", "sum"),
        (23.78, "surpris", "sum"), (24.59, "neutre", "tri"), (27.31, "neutre", "P"), (29.07, "surpris", "P"),
        (30.63, "neutre", "P"), (32.4, "idee", "P"), (33.3, "joie", None), (34.34, "surpris", None),
        (35.22, "reflechit", None), (37.19, "surpris", "planete"), (39.72, "reflechit", "planete"),
        (40.79, "etourdi", None), (42.0, "reflechit", "planete"), (44.4, "idee", None), (45.8, "amour", None),
        (T_END[0] + 0.6, "neutre", "tri")]


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


def tri_at(t):
    """Sommets du triangle (repère centré) : forme de base, déformée pendant T_WOB."""
    A, B, C = A0, B0, C0
    if T_WOB[0] <= t <= T_BACK + 0.7:
        k = ease((t - T_WOB[0]) / 0.5) * (1 - ease((t - T_BACK) / 0.7))
        u = t - T_WOB[0]
        A = (A0[0] + k * 170 * math.sin(u * 1.7), A0[1] + k * 80 * math.sin(u * 2.3 + 1))
        B = (B0[0] + k * 60 * math.sin(u * 1.3 + 2), B0[1] - k * 90 * math.sin(u * 1.9))
        C = (C0[0] - k * 70 * math.sin(u * 1.1 + 0.5), C0[1] + k * 50 * math.sin(u * 2.1 + 2))
    return A, B, C


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
        if t < t0 - 0.35:
            continue
        v, a, b = V[name]
        st, sw = span(v, a, b)
        grow = ease((t - (t0 - 0.35)) / 0.7)
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
        sc = pop(t - (t0 - 0.35))
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
    for s in ORBE:
        if t >= s[0]:
            prev, cur = cur, s
    t0, expr, gaze = cur
    a = t - t0
    e = Etat(expr=expr, age=a, humeur_mix=a / 0.6,
             humeur_avant=HUMEUR_DE.get(prev[1], "calme") if prev is not cur else "calme")
    e.cligne = (t % 3.3) < 0.12
    return e, targets.get(gaze)


def orbe_pose(t):
    """Position et taille de l'Orbe à l'écran."""
    base = ((540.0, 470.0), 0.7)
    planet = ((250.0, 470.0), 0.55)
    u = ease((t - T_ZOOM[0]) / (T_ZOOM[1] - T_ZOOM[0])) * (1 - ease((t - T_END[0]) / (T_END[1] - T_END[0])))
    pos = lerp2(base[0], planet[0], u)
    s = lerp(base[1], planet[1], u)
    bob = 10 * math.sin(t * 2.1)
    return (pos[0], pos[1] + bob), s


def draw_orbe_at(c, t, targets, ray_target=None):
    (x, y), s = orbe_pose(t)
    e, g = orbe_state(t, targets)
    if g is not None:
        d = (g[0] - x, g[1] - y)
        n = math.hypot(*d) or 1.0
        k = min(1.0, n / 200)
        e.regard = (0.75 * d[0] / n * k, 0.75 * d[1] / n * k)
    if e.expr == "reflechit" and g is None:
        e.regard = (0.6 * ease(e.age / 0.3), -0.6 * ease(e.age / 0.3))
    if ray_target is not None:
        e.cible = ((ray_target[0] - x) / s, (ray_target[1] - y) / s)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    draw_orbe(c, t, e)
    c.restore()


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
    ray = None
    if 9.98 <= t < 11.0:
        ray = to_screen(A)
    for k, tc in enumerate(T_CUT):
        if tc - 0.05 <= t < tc + 0.4:
            name = "ABC"[k]
            v, a, b = {"A": (A, B, C), "B": (B, A, C), "C": (C, A, B)}[name]
            st, sw = span(v, a, b)
            aa = math.radians(st + sw * ease((t - tc) / 0.35))
            ray = to_screen((v[0] + 82 * math.cos(aa), v[1] + 82 * math.sin(aa)))
    if T_RIGHT - 0.1 <= t < T_RIGHT + 0.7:
        ray = proj(90, 0, 1.0)[0]
    draw_orbe_at(c, t, targets, ray)
    draw_subtitle(c, t)


# ------------------------------------------------------------------------------------------------ son
SR = foley.SR


def tone(freq, dur, amp=0.3, attack=0.005, decay=0.3, harm=((1, 1.0),)):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * freq * h * tt) for h, a in harm)
    env = np.minimum(1, tt / attack) * np.exp(-tt / decay)
    return y * env * amp


def ding(f=880, amp=0.25):
    return tone(f, 1.2, amp, 0.002, 0.35, ((1, 1.0), (2, 0.35), (3, 0.12)))


def pop_s(f=600, amp=0.3):
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    fr = f * (1 + 2 * np.exp(-tt * 60))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt / 0.03) * amp


def sparkle(amp=0.15):
    out_ = np.zeros(int(0.9 * SR))
    rng = np.random.default_rng(3)
    for k in range(7):
        s = ding(1600 + 400 * rng.random(), amp * (0.5 + 0.5 * rng.random()))
        i = int(k * 0.09 * SR)
        m = min(len(out_) - i, len(s))
        out_[i:i + m] += s[:m]
    return out_


def scribble(dur, amp=0.12):
    n = int(dur * SR)
    x = np.random.default_rng(5).standard_normal(n)
    x = np.convolve(x, np.ones(6) / 6, mode="same")
    tt = np.arange(n) / SR
    env = (0.6 + 0.4 * np.sin(tt * 40)) * np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 0.1)
    return x * env * amp


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
            p = tone(f, 0.8, 0.05, 0.003, 0.25, ((1, 1.0), (2, 0.2)))
            i = i0 + int(j * bar / 4 * SR)
            m = min(n - i, len(p))
            if m > 0:
                y[i:i + m] += p[:m]
    return y


def soundtrack(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOIX, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    voice = np.frombuffer(raw, np.int16).astype(float) / 32768
    n = int(DUR * SR)
    mix = np.zeros(n)
    mix[:min(n, len(voice))] += voice[:n]
    fx = np.zeros(n)

    def add(t, s, g=1.0):
        i = int(t * SR)
        m = min(n - i, len(s))
        if m > 0:
            fx[i:i + m] += s[:m] * g

    add(T_DRAW[0], scribble(T_DRAW[1] - T_DRAW[0]))
    add(T_DROP, foley.whoosh(0.35, 0.5, 700))
    add(T_DROP + 0.35, foley.thud(0.7), 0.8)
    add(T_DROP + 0.35, ding(660, 0.2))
    for k, t0 in enumerate(T_ANG):
        add(t0 - 0.35, pop_s(500 + 120 * k))
        add(t0 + 0.2, ding(700 + 140 * k, 0.12))
    add(T_FLY, foley.whoosh(0.5, 0.4, 1200))
    add(T_SUM, ding(880, 0.2))
    add(T_SUM, ding(1320, 0.12))
    add(T_WOB[0], foley.whoosh(1.2, 0.25, 500))
    add(T_LOCK, foley.clack(0.5, 14))
    for tc in T_CUT:
        add(tc, foley.snap(0.25))
    add(T_MOVE[0], foley.whoosh(1.2, 0.35, 900))
    add(T_MOVE[1], foley.clack(0.6, 20))
    add(T_LINE, sparkle(0.1))
    add(T_ARC, ding(523, 0.18))
    add(T_ARC + 0.1, ding(784, 0.14))
    add(33.3, sparkle(0.14))
    add(T_ZOOM[0], foley.whoosh(1.2, 0.4, 400))
    add(T_SPH[0], scribble(T_SPH[1] - T_SPH[0], 0.1))
    for k in range(3):
        add(T_RIGHT + 0.18 * k, pop_s(700 + 100 * k))
    add(T_270, foley.boom(0.4), 0.6)
    add(T_270, ding(587, 0.2))
    add(44.4, sparkle(0.14))
    add(T_END[0], foley.whoosh(1.2, 0.25, 600))
    mus = music(DUR)
    # la musique s'efface sous la voix (ducking)
    env = np.abs(mix)
    k = int(0.15 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = 1 - 0.55 * np.minimum(1, env / 0.05)
    out_ = mix + fx * 0.8 + mus * duck
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
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out_path], check=True)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "output/ep01_triangle.mp4"
    render(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
