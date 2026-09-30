"""Épisode 2 — « Il existe des infinis plus grands que d'autres » (Cantor).

La voix off (audio/voix.mp3) enseigne ; l'Orbe écoute, agit juste après chaque consigne (dans les silences naturels
de l'enregistrement) et réagit. Minutage : 40 segments de parole mesurés sur l'enregistrement (voir SEG).

    python -m films.episodes.ep02_infinis.ep02 sortie.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep01_triangle.ep01 import (CYAN, FONT, GOLD, PINK, VIOLET, WHITE, P, ease, lerp, lerp2, out,
                                               pop, text_c)
from films.persos.orbe import HUMEUR_DE, Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.mp3")
DUR = 67.6
MONO = skia.Typeface("DejaVu Sans Mono", skia.FontStyle.Bold())

# ------------------------------------------------------------------------------------------------ minutage (mesuré)
SEG = [("Il existe des infinis…", 0.0, 1.76), ("plus grands que d'autres.", 2.59, 3.71),
       ("Tu ne me crois pas ?", 4.10, 4.75), ("Alors compte.", 5.21, 5.92), ("Un…", 6.36, 6.71),
       ("deux…", 7.18, 7.68), ("trois…", 8.14, 8.60), ("Ça ne s'arrête jamais.", 8.97, 10.07),
       ("C'est l'infini.", 10.43, 11.19), ("Maintenant,", 11.63, 12.14),
       ("garde seulement les nombres pairs.", 12.37, 13.99), ("Il y en a moitié moins…", 14.37, 15.45),
       ("pas vrai ?", 15.81, 16.21), ("Faux.", 16.61, 16.95),
       ("Relie 1 à 2, 2 à 4, 3 à 6…", 17.42, 20.59), ("Chaque nombre a son partenaire.", 20.94, 22.49),
       ("Personne n'est oublié.", 22.90, 24.00),
       ("Les pairs sont exactement aussi nombreux que tous les nombres.", 24.39, 27.36),
       ("Alors…", 27.73, 28.25), ("tous les infinis sont-ils égaux ?", 28.56, 29.92),
       ("Il y a 150 ans,", 30.40, 31.54), ("un mathématicien,", 31.81, 32.78),
       ("Georg Cantor, a trouvé la réponse.", 32.99, 35.41), ("Prends tous les nombres entre 0 et 1.", 35.84, 38.07),
       ("Et essaie de les ranger dans une liste.", 38.48, 40.18), ("Tous.", 40.51, 40.91),
       ("Maintenant,", 41.34, 41.82), ("fabrique un nouveau nombre.", 42.08, 43.28),
       ("Change le 1er chiffre du 1er nombre…", 43.69, 45.97), ("le 2e chiffre du 2e…", 46.39, 48.03),
       ("le 3e du 3e…", 48.44, 49.92), ("Ce nouveau nombre est différent de chaque nombre de ta liste.", 50.36, 53.47),
       ("Il n'y est pas.", 53.84, 54.43), ("Ta liste infinie…", 54.88, 55.90), ("a oublié quelqu'un.", 56.22, 57.33),
       ("Aucune liste ne pourra jamais tous les contenir.", 57.74, 60.34), ("Cet infini-là est plus grand.", 60.69, 62.40),
       ("Et il y a encore plus grand…", 62.79, 64.06), ("et encore…", 64.49, 65.30), ("à l'infini.", 65.70, 66.34)]

# repères des scènes
T_INF1, T_INF2 = 0.2, 2.6                      # le premier ∞, puis le second qui grossit
T_COUNT = (6.36, 7.18, 8.14)                   # « un… deux… trois… » (il compte après « Alors compte »)
T_RUSH = 8.6                                   # la rangée file de plus en plus vite
T_ROWS = 11.5                                  # rangée stable 1, 2, 3… pour la suite
T_EVENS = 14.05                                # il garde les pairs (après la consigne)
T_FAUX = 16.61
T_SLIDE = (17.45, 18.3)                        # les pairs se resserrent
T_LINK = [18.35, 19.2, 20.05] + [20.65 + 0.13 * k for k in range(5)]   # fils 1↔2, 2↔4, 3↔6, puis la suite
T_EQ = 24.9                                    # « ∞ = ∞ »
T_Q = 27.7                                     # « alors… égaux ? » : la scène s'efface
T_CANTOR = (30.4, 35.6)
T_SEG = (35.9, 38.3)                           # le segment [0, 1] se remplit
T_LIST = 38.45                                 # les nombres se rangent en liste
T_DIAG = [44.3, 46.7, 48.6, 49.4, 49.65, 49.9, 50.15]   # il parcourt la diagonale
T_CMP = 50.8                                   # comparaison ligne par ligne
T_OUT = 53.9                                   # « il n'y est pas »
T_BIG = 57.75                                  # deux infinis côte à côte
T_BIGGER = 60.7
T_NEST = (62.8, 64.5, 65.7)                    # encore plus grand… et encore… à l'infini
T_FADE = (66.5, 67.4)

ROWS = ["57142857", "12398401", "88888888", "31415926", "00723319", "61803398", "25000000"]
NEWD = [str((int(r[k]) + 1) % 10) for k, r in enumerate(ROWS)]          # 6 3 9 2 4 4 1

ORBE = [(0.0, "neutre", None), (2.7, "reflechit", "inf"), (4.2, "neutre", None), (5.95, "neutre", "ray"),
        (9.2, "surpris", "ray"), (10.6, "etourdi", None), (11.8, "neutre", None), (14.0, "neutre", "ray"),
        (15.55, "joie", "rows"), (16.75, "surpris", "rows"), (17.4, "neutre", "ray"), (22.95, "joie", "rows"),
        (25.3, "idee", "eq"), (27.75, "reflechit", None), (30.5, "neutre", "card"), (33.2, "joie", "card"),
        (35.9, "neutre", "ray"), (41.35, "reflechit", "list"), (43.3, "neutre", "ray"), (50.4, "reflechit", "new"),
        (53.95, "surpris", "new"), (56.3, "surpris", "new"), (57.9, "reflechit", "big"), (60.8, "idee", "big"),
        (62.9, "surpris", None), (64.6, "etourdi", None), (65.8, "amour", None), (T_FADE[0] + 0.3, "neutre", None)]
EMO = [(3.8, "?"), (9.25, "!"), (16.75, "!"), (25.35, "!"), (30.0, "?"), (41.4, "…"), (53.95, "!"), (56.35, "!"),
       (60.85, "!")]
CHIRPS = [(3.8, "question"), (9.25, "surprise"), (15.6, "joie"), (16.75, "surprise"), (25.35, "joie"),
          (30.0, "question"), (53.95, "surprise"), (56.35, "surprise"), (60.85, "joie"), (65.9, "joie")]


# ------------------------------------------------------------------------------------------------ outils
def seg_text(t):
    for k, (txt, a, b) in enumerate(SEG):
        nxt = SEG[k + 1][1] if k + 1 < len(SEG) else b + 1.2
        if a - 0.05 <= t < min(nxt, b + 0.9):
            return txt, a
    return None


def lemniscate(cx, cy, a, n=120):
    p = skia.Path()
    for i in range(n + 1):
        u = 2 * math.pi * i / n
        d = 1 + math.sin(u) ** 2
        q = (cx + a * math.cos(u) / d, cy + a * math.sin(u) * math.cos(u) / d)
        p.moveTo(*q) if i == 0 else p.lineTo(*q)
    p.close()
    return p


def draw_inf(c, cx, cy, a, color=GOLD, alpha=255, grow=1.0, w=None):
    """Symbole ∞ tracé (grow : portion tracée 0→1)."""
    if alpha <= 1 or a < 2:
        return
    w = w or max(4.0, a * 0.09)
    path = lemniscate(cx, cy, a)
    if grow < 1:
        meas = skia.PathMeasure(path, False)
        seg = skia.Path()
        meas.getSegment(0, meas.getLength() * max(0.0, grow), seg, True)
        path = seg
    c.drawPath(path, P(color, 0.45 * alpha, blur=w * 1.6, stroke=w * 2.2))
    c.drawPath(path, P(color, alpha, stroke=w))


def pearl(c, x, y, n, alpha=255, scale=1.0, col=VIOLET, r=40):
    if alpha <= 1 or scale <= 0.01:
        return
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    c.drawCircle(0, 0, r * 1.5, P(col, 0.35 * alpha, blur=18))
    sh = skia.GradientShader.MakeRadial(skia.Point(-r * 0.35, -r * 0.4), r * 1.4,
                                        [E1.rgb((255, 255, 255), alpha), E1.rgb(col, alpha),
                                         E1.rgb(tuple(v * 0.45 for v in col), alpha)], [0.0, 0.45, 1.0])
    c.drawCircle(0, 0, r, P(shader=sh))
    s = str(n)
    f = skia.Font(FONT, r * (0.95 if len(s) < 3 else 0.7))
    w = f.measureText(s)
    c.drawString(s, -w / 2, r * 0.34, f, P((25, 18, 50), alpha))
    c.restore()


# ------------------------------------------------------------------------------------------------ scènes
ROW_Y, EVEN_Y = 980.0, 1210.0
XS = [120 + 110 * k for k in range(8)]                  # abscisses des perles 1..8


def counting_x(n, t):
    """Rangée qui compte : elle file vers la gauche de plus en plus vite."""
    shown = sum(1 for m in range(1, len(_CT) + 1) if t >= count_t(m))
    scroll = max(0.0, shown - 7.0) * 118
    return 140 + (n - 1) * 118 - scroll


_CT = list(T_COUNT)
while _CT[-1] < T_ROWS:                                           # après « trois », la rangée accélère
    _CT.append(max(T_RUSH, _CT[-1]) + max(0.035, 0.35 * 0.85 ** (len(_CT) - 3)))


def count_t(n):
    return _CT[n - 1] if n <= len(_CT) else 1e9


def scene_count(c, t):
    if t < T_COUNT[0] - 0.05 or t > T_ROWS + 0.2:
        return None
    fade = 1 - ease((t - (T_ROWS - 0.6)) / 0.6)
    newest = None
    for n in range(1, len(_CT) + 1):
        tn = count_t(n)
        if t < tn:
            break
        x = counting_x(n, t)
        if x < -60:
            continue
        persp = 1 - max(0.0, (t - 10.3)) * 0.35                  # « c'est l'infini » : elle part à l'horizon
        a = 255 * fade * max(0.0, min(1.0, persp))
        pearl(c, x, ROW_Y, n, a, pop(t - tn))
        newest = (x, ROW_Y)
    if t > 9.6:                                                   # le ∞ apparaît au bout de la rangée
        k = ease((t - 9.6) / 0.8)
        draw_inf(c, 930, ROW_Y, 70 * k, GOLD, 255 * k * fade)
    return newest


def scene_rows(c, t):
    """Rangée 1..8 + pairs ; puis les pairs se resserrent et les fils relient n ↔ 2n."""
    if t < T_ROWS or t > T_Q + 0.8:
        return None
    a = 255 * ease((t - T_ROWS) / 0.6) * (1 - ease((t - T_Q) / 0.7))
    ray = None
    for k in range(8):
        pearl(c, XS[k], ROW_Y, k + 1, a, 1.0, VIOLET)
    text_c(c, "…", 1010, ROW_Y + 14, 60, WHITE, a)
    text_c(c, "tous les nombres", 540, ROW_Y - 90, 34, WHITE, a * 0.7, shadow=False)
    if t >= T_EVENS - 0.1:
        slide = ease((t - T_SLIDE[0]) / (T_SLIDE[1] - T_SLIDE[0]))
        for k in range(8):
            v = 2 * (k + 1)
            x0 = XS[v - 1] if v <= 8 else XS[7] + 110 * (v - 8)   # position « sous sa valeur »
            x = lerp(x0, XS[k], slide)
            if v <= 8:                                            # il descend les pairs de la rangée du haut
                td = T_EVENS + 0.28 * (k)
                u = out((t - td) / 0.35)
                if t < td:
                    continue
                y = lerp(ROW_Y, EVEN_Y, u)
                if t < td + 0.35:
                    ray = (x, y)
            else:
                y = EVEN_Y
                if slide <= 0:
                    continue
            al = a * (1.0 if v <= 8 else slide)
            if x < 1040:
                pearl(c, x, y, v, al, 1.0, CYAN)
        if t > T_EVENS + 1.2:
            text_c(c, "…", 1010, EVEN_Y + 14, 60, WHITE, a)
            text_c(c, "seulement les pairs", 540, EVEN_Y + 100, 34, WHITE, a * 0.7, shadow=False)
    for k, tl in enumerate(T_LINK):                               # les fils de lumière
        if t < tl:
            continue
        u = ease((t - tl) / 0.35)
        x = XS[k]
        y0, y1 = ROW_Y + 42, EVEN_Y - 42
        c.drawLine(x, y0, x, lerp(y0, y1, u), P(GOLD, 0.45 * a, blur=8, stroke=12))
        c.drawLine(x, y0, x, lerp(y0, y1, u), P(GOLD, a, stroke=4))
        if t < tl + 0.4:
            ray = (x, lerp(y0, y1, u))
        if t > 22.9:                                              # « personne n'est oublié » : les paires brillent
            g = 0.5 + 0.5 * math.sin((t - 22.9) * 6 - k * 0.6)
            c.drawCircle(x, ROW_Y, 52, P(GOLD, a * 0.35 * g, stroke=4))
            c.drawCircle(x, EVEN_Y, 52, P(GOLD, a * 0.35 * g, stroke=4))
    if t >= T_EQ:
        sc = pop(t - T_EQ)
        c.save()
        c.translate(540, 1400)
        c.scale(sc, sc)
        draw_inf(c, -170, 0, 80, VIOLET, a)
        text_c(c, "=", 0, 26, 110, WHITE, a)
        draw_inf(c, 170, 0, 80, CYAN, a)
        c.restore()
    return ray


def scene_cantor(c, t):
    if not (T_CANTOR[0] <= t < T_CANTOR[1] + 0.5):
        return
    a = 255 * ease((t - T_CANTOR[0]) / 0.5) * (1 - ease((t - T_CANTOR[1]) / 0.5))
    sc = 0.9 + 0.1 * out((t - T_CANTOR[0]) / 0.5)
    c.save()
    c.translate(540, 1080)
    c.scale(sc, sc)
    card = skia.RRect.MakeRectXY(skia.Rect(-250, -300, 250, 300), 40, 40)
    c.drawRRect(card, P((255, 255, 255), 0.08 * a))
    c.drawRRect(card, P(GOLD, 0.7 * a, stroke=3))
    # silhouette stylisée (tête, barbe, épaules, col)
    body = skia.Path()
    body.moveTo(-170, 210)
    body.cubicTo(-160, 90, -80, 60, 0, 60)
    body.cubicTo(80, 60, 160, 90, 170, 210)
    body.close()
    c.drawPath(body, P(VIOLET, 0.8 * a))
    c.drawCircle(0, -40, 90, P((200, 180, 255), 0.85 * a))
    beard = skia.Path()
    beard.moveTo(-70, -10)
    beard.cubicTo(-70, 90, 70, 90, 70, -10)
    beard.cubicTo(40, 20, -40, 20, -70, -10)
    c.drawPath(beard, P((120, 90, 190), 0.9 * a))
    c.restore()
    if t > 32.95:
        k = ease((t - 32.95) / 0.4)
        text_c(c, "Georg Cantor", 540, 1450, 64, WHITE, a * k)
    if t > 30.45:
        k = ease((t - 30.45) / 0.4)
        text_c(c, "1874", 540, 760, 70, GOLD, a * k)


def scene_list(c, t):
    """Le segment [0, 1] se remplit ; les nombres se rangent en liste ; la diagonale ; le nouveau nombre."""
    ray = None
    if t < T_SEG[0] or t > T_BIG + 0.5:
        return None
    gone = 1 - ease((t - T_BIG) / 0.5)
    # --- le segment
    if t < T_LIST + 1.0:
        a = 255 * ease((t - T_SEG[0]) / 0.4) * (1 - ease((t - T_LIST) / 0.8))
        x0, x1, y = 140.0, 940.0, 1000.0
        c.drawLine(x0, y, x1, y, P(WHITE, a, stroke=4))
        for x, lab in ((x0, "0"), (x1, "1")):
            c.drawLine(x, y - 18, x, y + 18, P(WHITE, a, stroke=4))
            text_c(c, lab, x, y + 80, 50, WHITE, a)
        rng = np.random.default_rng(7)
        pts = rng.random(900)
        k = int(900 * ease((t - T_SEG[0]) / (T_SEG[1] - T_SEG[0])) ** 2)
        for i in range(k):
            px = x0 + (x1 - x0) * pts[i]
            c.drawCircle(px, y, 3.2, P(GOLD, a * 0.8))
        if T_SEG[0] <= t < T_SEG[1]:
            ray = (x0 + (x1 - x0) * pts[max(0, k - 1)], y)
    # --- la liste
    f = skia.Font(MONO, 50)
    cw = f.measureText("0")
    X0, Y0, DY = 330.0, 700.0, 92.0
    for r, row in enumerate(ROWS):
        tr = T_LIST + 0.3 * r
        if t < tr:
            continue
        u = out((t - tr) / 0.45)
        y = lerp(1000, Y0 + DY * r, u)
        dim = 1.0
        if t > T_OUT:
            dim = 1 - 0.6 * ease((t - T_OUT) / 0.6)
        a = 255 * min(1.0, (t - tr) / 0.2) * gone * dim
        text_c(c, f"{r + 1}", 180, y + 18, 44, VIOLET, a, shadow=False)
        c.drawString("→", 225, y + 16, skia.Font(FONT, 40), P(WHITE, a * 0.6))
        c.drawString("0," + row + "…", X0, y + 18, f, P(WHITE, a))
        if t < tr + 0.45:
            ray = (X0 + cw * 5, y)
        # la diagonale : il allume le r-ième chiffre de la r-ième ligne
        if t >= T_DIAG[r] - 0.35:
            cx = X0 + cw * (2 + r) + cw / 2
            hu = ease((t - (T_DIAG[r] - 0.35)) / 0.3)
            box = skia.Rect(cx - cw * 0.62, y - 30, cx + cw * 0.62, y + 32)
            col = GOLD
            if t >= T_CMP + 0.32 * r:                             # comparaison : cette case diffère
                col = PINK
            c.drawRoundRect(box, 10, 10, P(col, 0.3 * a * hu))
            c.drawRoundRect(box, 10, 10, P(col, a * hu, stroke=4))
            if T_DIAG[r] - 0.35 <= t < T_DIAG[r] + 0.45:
                ray = (cx, y)
        if t >= T_CMP + 0.32 * r:                                 # « ≠ » en bout de ligne
            k = pop(t - (T_CMP + 0.32 * r))
            c.save()
            c.translate(X0 + cw * 11.8, y + 16)
            c.scale(k, k)
            text_c(c, "≠", 0, 0, 56, PINK, a)
            c.restore()
    if t >= T_LIST + 2.2:
        text_c(c, "⋮", 180, Y0 + DY * 7 + 20, 50, WHITE, 255 * gone * (1 - 0.6 * ease((t - T_OUT) / 0.6)))
    # --- le nouveau nombre
    if t >= T_DIAG[0] - 0.2:
        a = 255 * gone
        f2 = skia.Font(MONO, 64)
        cw2 = f2.measureText("0")
        lift = ease((t - (T_OUT + 0.2)) / 0.9)
        y = lerp(1440, 1370, lift)
        s = "0,"
        shown = [d for r, d in enumerate(NEWD) if t >= T_DIAG[r] + (0.55 if r < 3 else 0.2)]
        full = s + "".join(shown) + ("…" if len(shown) == len(NEWD) else "")
        x = 540 - cw2 * 11 / 2
        glow = 0.5 + 0.5 * math.sin(t * 4) if t > T_OUT else 0.0
        c.drawRoundRect(skia.Rect(x - 24, y - 60, x + cw2 * 11 + 24, y + 26), 22, 22,
                        P(GOLD, a * (0.12 + 0.2 * glow)))
        c.drawRoundRect(skia.Rect(x - 24, y - 60, x + cw2 * 11 + 24, y + 26), 22, 22, P(GOLD, a * 0.8, stroke=3))
        c.drawString(full, x, y, f2, P(GOLD, a))
        text_c(c, "le nouveau nombre", 540, y + 76, 34, WHITE, a * 0.75, shadow=False)
        for r in range(len(NEWD)):                                # le chiffre changé descend de sa case
            td = T_DIAG[r]
            if td <= t < td + 0.55 and r < 3:
                u = ease((t - td) / 0.5)
                sx = X0 + cw * (2 + r) + cw / 2
                sy = Y0 + DY * r
                tx = x + cw2 * (2 + r) + cw2 / 2
                q = lerp2((sx, sy), (tx, y - 20), u)
                text_c(c, NEWD[r], q[0], q[1] + 18, 56, GOLD, 255 * gone)
    return ray


def scene_big(c, t):
    if t < T_BIG or t > T_FADE[1]:
        return
    a = 255 * ease((t - T_BIG) / 0.6) * (1 - ease((t - T_NEST[0]) / 0.8))
    k = pop(t - T_BIG)
    draw_inf(c, 290, 1060, 95 * k, VIOLET, a)
    text_c(c, "les nombres entiers", 290, 1200, 34, WHITE, a * 0.8, shadow=False)
    g = 1 + 0.55 * ease((t - T_BIGGER) / 0.8)
    draw_inf(c, 730, 1060, 150 * k * g, GOLD, a)
    text_c(c, "les nombres réels", 730, 1200 + 60 * (g - 1), 34, WHITE, a * 0.8, shadow=False)
    # --- des infinis emboîtés, à perte de vue (zoom continu)
    if t >= T_NEST[0]:
        fade = 1 - ease((t - T_FADE[0]) / (T_FADE[1] - T_FADE[0]))
        z = math.exp((t - T_NEST[0]) * 0.55)
        cols = [VIOLET, CYAN, GOLD, PINK, WHITE]
        for i, ti in enumerate((T_NEST[0], T_NEST[0] + 0.6, T_NEST[1], T_NEST[1] + 0.5, T_NEST[2])):
            if t < ti:
                continue
            aa = 255 * fade * ease((t - ti) / 0.5)
            size = 60 * (1.7 ** i) * z / (1.7 ** 3)
            if size > 1400:
                continue
            draw_inf(c, 540, 1060, size, cols[i % len(cols)], aa * max(0.0, 1 - size / 1400))


# ------------------------------------------------------------------------------------------------ l'Orbe
def orbe_target(t):
    if T_COUNT[0] - 0.3 <= t < T_ROWS:
        return 540, 560, 0.72
    if T_EVENS <= t < T_Q:
        return 540, 560, 0.72
    if T_SEG[0] <= t < T_BIG:
        return 880, 430, 0.62
    return 540, 430, 0.8


_POSE = {}


def orbe_pose(t):
    if not _POSE:
        n = int(DUR * FPS) + 2
        x, y, s = orbe_target(0.0)
        vx = vy = vs = 0.0
        h = 1.0 / (FPS * 4)
        w = 7.0
        for f in range(n):
            _POSE[f] = (x, y, s)
            for k in range(4):
                tx, ty, ts = orbe_target((f + k / 4) / FPS)
                vx += (w * w * (tx - x) - 2 * 0.85 * w * vx) * h
                vy += (w * w * (ty - y) - 2 * 0.85 * w * vy) * h
                vs += (w * w * (ts - s) - 2 * 0.9 * w * vs) * h
                x, y, s = x + vx * h, y + vy * h, s + vs * h
    f = t * FPS
    i = min(int(f), len(_POSE) - 2)
    u = f - i
    a, b = _POSE[i], _POSE[i + 1]
    x, y, s = (a[j] + (b[j] - a[j]) * u for j in range(3))
    return (x, y + 8 * math.sin(t * 2.1)), s


def orbe_state(t):
    cur, prev = ORBE[0], ORBE[0]
    for s_ in ORBE:
        if t >= s_[0]:
            prev, cur = cur, s_
    t0, expr, gaze = cur
    a = t - t0
    e = Etat(expr=expr, age=a, humeur_mix=a / 0.6,
             humeur_avant=HUMEUR_DE.get(prev[1], "calme") if prev is not cur else "calme")
    e.cligne = (t % 3.3) < 0.12
    return e, gaze


GAZE = {"inf": (540, 1060), "rows": (540, 1090), "eq": (540, 1400), "card": (540, 1080), "list": (540, 950),
        "new": (540, 1450), "big": (730, 1060)}


def draw_beam(c, t, orig, s, tgt):
    d = (tgt[0] - orig[0], tgt[1] - orig[1])
    n = math.hypot(*d) or 1.0
    sx, sy = orig[0] + d[0] / n * 140 * s, orig[1] + d[1] / n * 140 * s
    c.drawLine(sx, sy, *tgt, P(CYAN, 110, blur=10, stroke=16))
    c.drawLine(sx, sy, *tgt, P(WHITE, 225, stroke=4))
    c.drawCircle(*tgt, 20 * (1 + 0.2 * math.sin(t * 10)), P(CYAN, 120, blur=10))


def draw_bubble(c, t, x, y, s):
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


def draw_orbe_at(c, t, ray):
    (x, y), s = orbe_pose(t)
    e, gaze = orbe_state(t)
    tgt = ray if gaze == "ray" else GAZE.get(gaze)
    if gaze == "ray" and ray is not None:
        draw_beam(c, t, (x, y), s, ray)
    if tgt is not None:
        d = (tgt[0] - x, tgt[1] - y)
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
    draw_bubble(c, t, x, y, s)


# ------------------------------------------------------------------------------------------------ image
def frame(c, t):
    E1.draw_background(c, t)
    # hook : un ∞, puis un second qui devient plus grand
    if t < 5.6:
        a = 255 * (1 - ease((t - 4.8) / 0.8))
        g1 = ease((t - T_INF1) / 1.2)
        big = ease((t - T_INF2) / 0.9)
        draw_inf(c, lerp(540, 330, big), 1060, 120, VIOLET, a, g1)
        if t >= T_INF2:
            draw_inf(c, 760, 1060, lerp(40, 190, big) * (1 + 0.04 * math.sin(t * 5)), GOLD, a, ease((t - T_INF2) / 0.6))
    ray = scene_count(c, t)
    r2 = scene_rows(c, t)
    ray = r2 or ray
    scene_cantor(c, t)
    r3 = scene_list(c, t)
    ray = r3 or ray
    scene_big(c, t)
    draw_orbe_at(c, t, ray)
    # sous-titres (même style que l'épisode 1)
    E1.TIMING = SEG
    E1.draw_subtitle(c, t)


# ------------------------------------------------------------------------------------------------ son
SR = E1.SR


def soundtrack(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOIX, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    voice = np.frombuffer(raw, np.int16).astype(float) / 32768
    n = int(DUR * SR)
    mix = np.zeros(n)
    mix[:min(n, len(voice))] += voice[:n]
    fx = np.zeros(n)

    def add(t, s_, g=1.0):
        i = int(t * SR)
        m = min(n - i, len(s_))
        if m > 0:
            fx[i:i + m] += s_[:m] * g

    penta = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    add(T_INF1, E1.swish(1.2, 0.12))
    add(T_INF2, E1.swell(0.14))
    for k in range(40):                                            # chaque perle : un « bloop » sur une gamme douce
        tn = count_t(k + 1)
        if tn < T_ROWS - 0.8:
            add(tn, E1.pop_s(penta[k % 6], 0.2 if k < 3 else 0.1))
    add(10.4, E1.sparkle(0.1))
    for k in range(4):
        add(T_EVENS + 0.28 * k, E1.pop_s(penta[(k * 2 + 1) % 6], 0.16))
    add(T_SLIDE[0], E1.swish(0.9, 0.14))
    for k, tl in enumerate(T_LINK):
        add(tl, E1.ding(660 + 55 * k, 0.12 if k < 3 else 0.06))
    add(T_EQ, E1.ding(784, 0.16))
    add(T_EQ + 0.15, E1.ding(1046, 0.12))
    add(T_EQ + 0.4, E1.sparkle(0.12))
    add(T_CANTOR[0], E1.swell(0.12))
    add(T_SEG[0], E1.scribble(T_SEG[1] - T_SEG[0], 0.06))
    for r in range(len(ROWS)):
        add(T_LIST + 0.3 * r, E1.swish(0.4, 0.08))
        add(T_DIAG[r] - 0.35, E1.tock(0.2 if r < 3 else 0.12))
        add(T_DIAG[r] + 0.2, E1.ding(587 + 45 * r, 0.1))
        add(T_CMP + 0.32 * r, E1.pop_s(300, 0.14))
    add(T_OUT, E1.swell(0.16))
    add(56.25, E1.sparkle(0.12))
    add(T_BIG, E1.swish(1.0, 0.14))
    add(T_BIGGER, E1.swell(0.2))
    for tn in T_NEST:
        add(tn, E1.sparkle(0.1))
    for t0, kind in CHIRPS:
        add(t0, E1.orbe_voice(kind), 0.9)
    mus = E1.music(DUR)
    env = np.convolve(np.abs(mix), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
    duck = 1 - 0.55 * np.minimum(1, env / 0.05)
    out_ = mix + E1.soften(fx, 6) * 0.8 + mus * duck
    fade = np.ones(n)
    k = int(0.6 * SR)
    fade[-k:] = np.linspace(1, 0, k)
    out_ = np.tanh(out_ * fade * 1.3) / np.tanh(1.3)
    stereo = np.stack([out_, out_], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(stereo, -1, 1) * 32767).astype(np.int16).tobytes())


def render(out_path):
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    wav = f"{tmp}/a.wav"
    soundtrack(wav)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out_path], check=True)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "output/ep02_infinis.mp4"
    render(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
