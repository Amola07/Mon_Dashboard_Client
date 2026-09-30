"""Épisode 4 — « Il y a plus d'arbres sur Terre que d'étoiles dans notre galaxie ».

La voix off (audio/voix.mp3) enseigne ; l'Orbe écoute, agit juste après chaque consigne (dans les silences naturels
de l'enregistrement) et réagit. Les repères d'animation sont rattachés aux phrases mesurées (SEG) : S(clé) est le
début d'une phrase, E(clé) sa fin.

    python -m films.episodes.ep04_arbres.ep04 sortie.mp4
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
from films.episodes.ep01_triangle.ep01 import CYAN, GOLD, PINK, VIOLET, WHITE, P, ease, lerp, out, pop, text_c
from films.persos.orbe import HUMEUR_DE, Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.mp3")

# ------------------------------------------------------------------------------------------------ minutage (mesuré)
SEG = [("h1", "Il y a plus d'arbres sur Terre…", 0.0, 1.91),
       ("h2", "que d'étoiles dans toute notre galaxie.", 2.85, 4.95), ("imp", "Impossible ?", 5.49, 6.21),
       ("compte", "Compte les étoiles.", 6.59, 7.38), ("voie", "La Voie lactée en contient…", 7.82, 9.36),
       ("cent", "entre 100 et 400 milliards.", 9.69, 11.98), ("maint", "Maintenant,", 12.45, 12.96),
       ("arbres", "compte les arbres.", 13.19, 13.95), ("trois", "3 000 milliards.", 14.32, 15.74),
       ("dix", "Presque 10 fois plus.", 16.12, 17.49),
       ("sec", "Si tu comptais 1 arbre par seconde, sans jamais t'arrêter…", 17.91, 21.31),
       ("ans", "il te faudrait près de 100 000 ans.", 21.77, 23.69),
       ("quatre", "Ça fait près de 400 arbres…", 24.17, 25.84), ("humain", "pour chaque humain.", 26.06, 26.78),
       ("pb", "Mais il y a un problème.", 27.26, 28.80), ("agri", "Avant l'agriculture,", 29.25, 30.41),
       ("deux", "il y en avait presque 2 fois plus.", 30.57, 32.42), ("annee", "Chaque année,", 32.78, 33.43),
       ("abat", "on en abat environ 15 milliards.", 33.68, 35.46), ("cinq", "Près de 500…", 35.92, 36.89),
       ("parsec", "par seconde.", 37.24, 37.94), ("pourtant", "Et pourtant…", 38.40, 39.00),
       ("leve", "lève les yeux.", 39.48, 40.10),
       ("galaxie", "Notre galaxie n'est qu'une parmi des centaines de milliards.", 40.50, 43.71),
       ("univers", "Dans l'univers,", 44.10, 44.94), ("etoiles", "il y a plus d'étoiles…", 45.18, 46.41),
       ("sable", "que de grains de sable sur toutes les plages de la Terre.", 46.61, 49.23),
       ("toujours", "Des étoiles, il y en aura toujours plus.", 49.65, 51.83), ("desarbres", "Des arbres…", 52.23, 52.82),
       ("garde", "seulement ceux qu'on garde.", 53.29, 54.55)]
_K = {k: (a, b) for k, _, a, b in SEG}


def S(k):
    return _K[k][0]


def E(k):
    return _K[k][1]


DUR = E("garde") + 2.8

# repères des scènes (tous APRÈS la consigne correspondante)
T_TILT = S("h2") + 0.7                                  # la balance penche du côté des arbres
T_SC = E("compte") + 0.05                               # il compte les étoiles
T_GAL = S("cent") + 0.1                                 # la Voie lactée se dessine
T_SLOCK = S("cent") + 1.2                               # « 100 – 400 milliards »
T_TC = E("arbres") + 0.05                               # il compte les arbres : la forêt pousse
T_TLOCK = S("trois") + 0.5                              # « 3 000 milliards »
T_BARS = S("dix") + 0.05
T_CLOCK = S("sec") + 0.35                               # un arbre par seconde…
T_FAST = S("sec") + 2.6                                 # … l'horloge s'emballe
T_YEARS = S("ans") + 0.4
T_SLEEP = S("ans") + 1.0
T_HUM = S("quatre") + 0.2
T_PB = S("pb")
T_GHOST = S("deux") + 0.3                               # les arbres d'avant l'agriculture
T_CUT = S("abat") + 0.3                                 # les arbres s'éteignent
T_UP = E("leve") + 0.05                                 # il lève les yeux : la caméra monte
T_SAND = S("univers") + 0.1
T_GRAINS = S("sable") + 0.2                             # les grains deviennent des étoiles
T_END = S("toujours")
T_BACK = S("desarbres") + 0.05                          # la forêt revient
T_SPROUT = E("garde") - 0.3                             # une pousse grandit à côté de l'Orbe
T_LOOP = E("garde") + 0.55                              # retour à l'image du début

ORBE = [(0.0, "surpris", "balance"), (S("imp") + 0.1, "reflechit", None), (T_SC, "neutre", "ray"),
        (T_SLOCK, "surpris", "sky"), (E("cent") + 0.2, "neutre", None), (T_TC, "neutre", "ray"),
        (T_TLOCK, "surpris", "forest"), (T_BARS + 0.3, "idee", "bars"), (T_CLOCK, "neutre", "ray"),
        (T_FAST, "surpris", "clock"), (T_SLEEP, "etourdi", None), (T_HUM, "joie", "human"),
        (T_PB, "reflechit", None), (T_GHOST + 0.3, "triste", "forest"), (T_CUT, "triste", "forest"),
        (S("cinq"), "surpris", "forest"), (S("pourtant") + 0.2, "neutre", None), (T_UP, "surpris", "up"),
        (S("galaxie") + 1.4, "amour", "up"), (T_SAND, "neutre", "sand"), (T_GRAINS + 0.4, "surpris", "sand"),
        (T_END, "joie", "up"), (T_BACK, "neutre", "sprout"), (T_SPROUT + 0.4, "amour", "sprout"),
        (T_LOOP, "surpris", "balance")]
EMO = [(0.5, "!"), (S("imp") + 0.15, "?"), (T_SLOCK + 0.05, "!"), (T_TLOCK + 0.05, "!"), (T_BARS + 0.35, "!"),
       (T_SLEEP + 0.1, "zzz"), (T_GHOST + 0.35, "…"), (S("cinq") + 0.05, "!"), (T_UP + 0.1, "!"),
       (T_GRAINS + 0.45, "!"), (T_SPROUT + 0.45, "♥")]
CHIRPS = [(0.5, "surprise"), (S("imp") + 0.15, "question"), (T_SLOCK + 0.05, "surprise"), (T_TLOCK + 0.05, "surprise"),
          (T_BARS + 0.35, "joie"), (T_SLEEP + 0.1, "triste"), (T_HUM + 0.3, "joie"), (T_GHOST + 0.35, "triste"),
          (S("cinq") + 0.05, "surprise"), (T_UP + 0.1, "surprise"), (T_GRAINS + 0.45, "surprise"),
          (T_SPROUT + 0.45, "joie")]


def win(t, a, b, fi=0.4, fo=0.4):
    """Opacité (0→1→0) d'un élément visible entre a et b."""
    return ease((t - a) / fi) * (1 - ease((t - b) / fo))


# ------------------------------------------------------------------------------------------------ ciel et étoiles
RNG = np.random.default_rng(11)
SKY = [(RNG.uniform(30, 1050), RNG.uniform(60, 980), RNG.uniform(1.5, 4.2), RNG.uniform(0, 6)) for _ in range(170)]
SKY.sort(key=lambda s_: math.hypot(s_[0] - 760, s_[1] - 520))           # ordre de comptage : près de l'Orbe d'abord


def star(c, x, y, r, a, col=(255, 250, 225)):
    if a <= 1:
        return
    c.drawCircle(x, y, r * 3.2, P(col, a * 0.25, blur=r * 1.6))
    c.drawCircle(x, y, r, P(col, a))


def draw_sky(c, t, a, dy=0.0, extra=0.0):
    """Ciel étoilé ; extra > 0 : de nouvelles étoiles apparaissent partout."""
    if a <= 1:
        return
    for x, y, r, ph in SKY:
        tw = 0.65 + 0.35 * math.sin(t * 2.2 + ph * 3)
        star(c, x, y + dy, r, a * tw)
    if extra > 0:
        rr = np.random.default_rng(5)
        n = int(500 * extra)
        pts = rr.uniform(0, 1, (500, 3))
        for i in range(n):
            x, y, ph = pts[i]
            star(c, x * W, y * 1500 + dy, 1.6, a * (0.5 + 0.4 * math.sin(t * 3 + ph * 9)))


GAL_PTS = []
for _i in range(1100):
    arm = _i % 2
    u = RNG.uniform(0.05, 1.0) ** 0.8
    th = arm * math.pi + u * 3.4 * math.pi / 2 * 2 + RNG.normal(0, 0.28)
    rad = u + RNG.normal(0, 0.04)
    GAL_PTS.append((rad * math.cos(th), rad * math.sin(th) * 0.55, RNG.uniform(0.6, 1.0)))


def draw_galaxy(c, cx, cy, r, a, rot=0.0, grow=1.0, col=(200, 190, 255)):
    """Galaxie spirale vue de biais (grow : proportion d'étoiles déjà apparues)."""
    if a <= 1 or r < 1:
        return
    c.drawOval(skia.Rect(cx - r * 0.5, cy - r * 0.22, cx + r * 0.5, cy + r * 0.22), P(col, a * 0.35, blur=r * 0.25))
    c.drawCircle(cx, cy, r * 0.12, P((255, 240, 210), a * 0.9, blur=r * 0.06))
    cr, sr = math.cos(rot), math.sin(rot)
    n = int(len(GAL_PTS) * grow)
    dot = max(0.8, r * 0.006)
    for x, y, b in GAL_PTS[:n] if r > 60 else GAL_PTS[:n:6]:
        X = x * cr - y * sr
        Y = x * sr + y * cr
        c.drawCircle(cx + X * r, cy + Y * r, dot, P(WHITE, a * b))


GALAXIES = [(RNG.uniform(40, 1040), RNG.uniform(80, 1500), RNG.uniform(14, 46), RNG.uniform(0, 6),
             (VIOLET, CYAN, PINK, GOLD, (200, 190, 255))[i % 5]) for i in range(90)]


# ------------------------------------------------------------------------------------------------ forêt
def tree(c, x, y, s, a, kind, shade, grow=1.0, ghost=False, dark=0.0):
    """Arbre stylisé : feuillu (3 boules) ou conifère (3 étages)."""
    if a <= 1 or grow <= 0.01:
        return
    h = 120 * s * grow
    if ghost:
        fill = P(WHITE, a * 0.12)
        edge = P(WHITE, a * 0.45, stroke=2.5)
    else:
        g = [(90, 200, 130), (60, 170, 120), (120, 215, 140), (70, 190, 160)][shade % 4]
        g = tuple(v * (1 - 0.75 * dark) for v in g)
        fill = P(g, a)
        edge = P(tuple(v * 0.7 for v in g), a, stroke=2)
        c.drawRect(skia.Rect(x - 6 * s, y - h * 0.32, x + 6 * s, y), P((120 * (1 - 0.6 * dark), 80, 60), a))
    if kind == 0:
        for dx, dy, rr in ((-0.18, -0.52, 0.26), (0.18, -0.52, 0.26), (0.0, -0.74, 0.3)):
            c.drawCircle(x + dx * h, y + dy * h, rr * h, fill)
            if ghost:
                c.drawCircle(x + dx * h, y + dy * h, rr * h, edge)
    else:
        for k in range(3):
            p = skia.Path()
            base = y - h * (0.25 + 0.22 * k)
            wdt = h * (0.42 - 0.1 * k)
            p.moveTo(x - wdt, base)
            p.lineTo(x, base - h * 0.42)
            p.lineTo(x + wdt, base)
            p.close()
            c.drawPath(p, fill)
            c.drawPath(p, edge)


FOREST = []
for row in range(9):
    y = 1080 + row * 50
    s = lerp(0.42, 1.0, row / 8)
    n = 14 - row // 2
    for i in range(n):
        x = (i + 0.5) * W / n + RNG.uniform(-25, 25)
        d = math.hypot(x - 540, y - 1080) / 700                         # ordre de pousse : depuis l'Orbe
        FOREST.append((x, y + RNG.uniform(-8, 8), s, int(RNG.integers(0, 2)), int(RNG.integers(0, 4)), d,
                       RNG.uniform(0, 1)))
FOREST.sort(key=lambda f: f[1])
GHOSTS = [(RNG.uniform(20, 1060), 1080 + RNG.uniform(0, 420), 0, int(RNG.integers(0, 2))) for _ in range(95)]
GHOSTS = [(x, y, lerp(0.42, 1.0, (y - 1080) / 420), k) for x, y, _, k in sorted(GHOSTS, key=lambda g: g[1])]


def forest_state(t):
    """(visibilité, pousse(tree), extinction(tree))."""
    vis = max(win(t, -1, S("compte"), 0.1, 0.5), win(t, T_TC - 0.1, S("univers") - 0.6, 0.1, 0.6),
              ease((t - T_BACK) / 0.8))

    def grow(f):
        if t < S("compte") + 0.5:
            return 1.0
        if t < T_BACK:
            return out((t - (T_TC + 1.1 * f[5])) / 0.45)
        return out((t - (T_BACK + 0.6 * f[5])) / 0.45)

    def cut(f):
        if not (T_CUT <= t < T_BACK):
            return 0.0
        tc = T_CUT + 3.6 * (f[6] ** 0.6)                              # de plus en plus vite
        return 1.0 if (f[6] < 0.45 and t >= tc) else 0.0

    return vis, grow, cut


def draw_ground(c, a, dy=0.0):
    if a <= 1:
        return
    p = skia.Path()
    p.moveTo(0, 1060 + dy)
    p.cubicTo(300, 1010 + dy, 700, 1050 + dy, W, 1020 + dy)
    p.lineTo(W, H)
    p.lineTo(0, H)
    p.close()
    c.drawPath(p, P((22, 48, 52), a))


def draw_forest(c, t, dy=0.0):
    vis, grow, cut = forest_state(t)
    if vis <= 0.01:
        return
    a = 255 * vis
    draw_ground(c, a, dy)
    ghost_a = win(t, T_GHOST, T_CUT + 0.4, 0.8, 0.6)
    items = [(f[1], 0, f) for f in FOREST] + ([(g[1], 1, g) for g in GHOSTS] if ghost_a > 0 else [])
    for _, is_g, f in sorted(items, key=lambda z: z[0]):
        if is_g:
            x, y, s, k = f
            u = ease((t - T_GHOST - 0.8 * ((x * 7) % 100) / 100) / 0.5)
            tree(c, x, y + dy, s, a * ghost_a * u, k, 0, 1.0, ghost=True)
        else:
            x, y, s, kind, shade, d, r = f
            cu = cut(f)
            if cu >= 1:
                tree(c, x, y + dy, s, a * 0.35, kind, shade, 0.25, ghost=True)          # souche fantôme
                continue
            tree(c, x, y + dy, s, a, kind, shade, grow(f))


# ------------------------------------------------------------------------------------------------ scènes
def draw_balance(c, t, a):
    if a <= 1:
        return
    tilt = math.radians(14) * out((t - T_TILT) / 0.9) if t < T_LOOP else math.radians(14) * out((t - T_LOOP - 0.4) / 0.9)
    fx, fy = 540.0, 760.0
    p = skia.Path()
    p.moveTo(fx, fy)
    p.lineTo(fx - 40, fy + 220)
    p.lineTo(fx + 40, fy + 220)
    p.close()
    c.drawPath(p, P((200, 200, 230), a * 0.9))
    L = 280
    lx, ly = fx - L * math.cos(tilt), fy - L * math.sin(tilt)
    rx, ry = fx + L * math.cos(tilt), fy + L * math.sin(tilt)
    c.drawLine(lx, ly, rx, ry, P(WHITE, a, stroke=8))
    for px, py in ((lx, ly), (rx, ry)):
        c.drawLine(px, py, px - 70, py + 120, P(WHITE, a * 0.6, stroke=3))
        c.drawLine(px, py, px + 70, py + 120, P(WHITE, a * 0.6, stroke=3))
        c.drawLine(px - 95, py + 120, px + 95, py + 120, P(WHITE, a, stroke=7))
    for i in range(7):                                                  # plateau gauche : des étoiles
        star(c, lx - 60 + i * 20, ly + 100 - (i % 2) * 16, 5, a)
    text_c(c, "étoiles", lx, ly + 180, 36, WHITE, a, shadow=False)
    for i in range(4):                                                  # plateau droit : des arbres
        tree(c, rx - 60 + i * 40, ry + 117, 0.5, a, i % 2, i)
    text_c(c, "arbres", rx, ry + 180, 36, WHITE, a, shadow=False)


def counter(c, t, t0, t1, lock_t, final, y, col=GOLD):
    """Compteur qui s'emballe puis se fige sur le texte final."""
    if t < t0:
        return
    a = 255 * win(t, t0, t1, 0.2, 0.4)
    if t < lock_t:
        u = (t - t0) / (lock_t - t0)
        n = int(3 + (10 ** (1 + 9 * u ** 2.2)))
        s = f"{n:,}".replace(",", " ")
        text_c(c, s, 540, y, 64, WHITE, a)
    else:
        sc = pop(t - lock_t)
        c.save()
        c.translate(540, y)
        c.scale(sc, sc)
        text_c(c, final, 0, 0, 74, col, a)
        c.restore()


def scene_count_stars(c, t):
    """Il pointe les étoiles une à une, puis la Voie lactée se dessine."""
    ray = None
    if T_SC <= t < T_TC:
        a = win(t, T_SC, S("maint") + 0.2, 0.2, 0.5)
        steps = [T_SC + 0.1, T_SC + 0.5, T_SC + 0.85]
        k = sum(1 for s_ in steps if t >= s_)
        if t > T_SC + 1.1:                                              # il accélère
            k = 3 + int(((t - T_SC - 1.1) / 1.0) ** 2 * 60)
        k = min(k, len(SKY))
        for i in range(k):
            x, y, r, _ = SKY[i]
            ring = a * (1 - ease((t - T_GAL) / 0.6)) if i >= 3 else a
            c.drawCircle(x, y, 16, P(CYAN, 170 * ring, stroke=2.5))
            if i < 3:
                text_c(c, str(i + 1), x + 26, y - 14, 34, CYAN, 255 * a, shadow=False)
        if 0 < k <= len(SKY) and t < T_GAL:
            ray = SKY[k - 1][:2]
        if t >= T_GAL:
            g = ease((t - T_GAL) / 1.0)
            draw_galaxy(c, 540, 470, 380, 255 * g * a, rot=-0.3 + t * 0.03, grow=g)
            text_c(c, "la Voie lactée", 540, 720, 38, WHITE, 255 * a * g * 0.8, shadow=False)
        counter(c, t, T_SC + 1.1, S("maint") + 0.2, T_SLOCK, "100 – 400 milliards", 880)
    return ray


def scene_count_trees(c, t):
    ray = None
    if T_TC <= t < T_BARS + 0.4:
        # le rayon suit la vague de pousse
        u = (t - T_TC) / 1.1
        if 0 <= u < 1:
            ang = t * 7
            ray = (540 + 480 * u * math.cos(ang) * 0.9, 1250 + 200 * u * math.sin(ang))
        counter(c, t, T_TC + 0.05, T_BARS + 0.1, T_TLOCK, "3 000 milliards", 820, (140, 230, 160))
    return ray


def scene_bars(c, t):
    if not (T_BARS <= t < T_CLOCK + 0.4):
        return
    a = 255 * win(t, T_BARS, T_CLOCK - 0.1, 0.3, 0.4)
    base = 960.0
    for x, val, lab, col, t0 in ((340, 400, "étoiles", (200, 190, 255), T_BARS), (740, 3040, "arbres", (120, 215, 140),
                                                                                  T_BARS + 0.25)):
        h = 0.14 * val * out((t - t0) / 0.8)
        c.drawRoundRect(skia.Rect(x - 90, base - h, x + 90, base), 16, 16, P(col, a * 0.85))
        c.drawRoundRect(skia.Rect(x - 90, base - h, x + 90, base), 16, 16, P(WHITE, a * 0.7, stroke=3))
        text_c(c, lab, x, base + 60, 40, WHITE, a, shadow=False)
    c.drawRect(skia.Rect(0, base + 1, W, H), P((20, 18, 42), a * 0.0))


def scene_clock(c, t):
    """Un arbre par seconde… l'horloge s'emballe… 100 000 ans."""
    ray = None
    if not (T_CLOCK <= t < S("quatre") + 0.3):
        return None
    a = 255 * win(t, T_CLOCK, S("quatre"), 0.3, 0.4)
    cx, cy, r = 400.0, 620.0, 170.0
    c.drawCircle(cx, cy, r, P((30, 26, 60), a * 0.85))
    c.drawCircle(cx, cy, r, P(WHITE, a, stroke=6))
    for k in range(12):
        u = k * math.pi / 6
        c.drawLine(cx + 0.82 * r * math.cos(u), cy + 0.82 * r * math.sin(u), cx + 0.93 * r * math.cos(u),
                   cy + 0.93 * r * math.sin(u), P(WHITE, a, stroke=5))
    # aiguille : une seconde par tic, puis de plus en plus vite
    tt = t - T_CLOCK
    turns = math.floor(tt) / 60 if t < T_FAST else (T_FAST - T_CLOCK) / 60 + ((t - T_FAST) ** 3) * 2.2
    ang = -math.pi / 2 + turns * 2 * math.pi
    c.drawLine(cx, cy, cx + 0.8 * r * math.cos(ang), cy + 0.8 * r * math.sin(ang), P(GOLD, a, stroke=7))
    c.drawCircle(cx, cy, 12, P(GOLD, a))
    if t < T_FAST:                                                      # il pointe un arbre à chaque seconde
        n = int(tt) + 1
        text_c(c, f"{n} arbre" + ("s" if n > 1 else ""), cx, cy + r + 70, 44, (140, 230, 160), a)
        f = FOREST[(n * 37) % len(FOREST)]
        ray = (f[0], f[1] - 60 * f[2])
    else:
        yrs = min(96000, int(((t - T_FAST) / (T_YEARS + 0.8 - T_FAST)) ** 2.5 * 96000)) if t < T_YEARS + 0.8 else 96000
        s = f"{yrs:,}".replace(",", " ") + " ans"
        text_c(c, s, cx, cy + r + 80, 64 if yrs == 96000 else 56, GOLD if yrs == 96000 else WHITE, a)
    return ray


def person(c, x, y, s, col, a):
    c.drawCircle(x, y - 22 * s, 8 * s, P(col, a))
    c.drawRoundRect(skia.Rect(x - 9 * s, y - 12 * s, x + 9 * s, y + 14 * s), 7 * s, 7 * s, P(col, a))


def scene_human(c, t):
    if not (T_HUM <= t < T_PB + 0.5):
        return
    a = 255 * win(t, T_HUM, T_PB, 0.3, 0.5)
    cx, cy = 540.0, 760.0
    c.drawOval(skia.Rect(cx - 300, cy - 30, cx + 300, cy + 60), P((30, 70, 60), a))
    person(c, cx, cy, 3.0 * pop(t - T_HUM), GOLD, a)
    n = 44
    for i in range(n):
        ti = T_HUM + 0.3 + 1.4 * i / n
        if t < ti:
            continue
        u = i * 2.39996
        rr = 110 + (i * 53 % 170)
        x, y = cx + rr * math.cos(u), cy + 18 + 0.2 * rr * math.sin(u)
        tree(c, x, y, 0.32, a, i % 2, i, out((t - ti) / 0.3))
    text_c(c, "≈ 400 arbres", cx, cy - 170, 60, (140, 230, 160), a * ease((t - T_HUM - 0.6) / 0.4))
    text_c(c, "pour toi", cx, cy + 140, 44, WHITE, a * ease((t - S("humain")) / 0.4), shadow=False)


def scene_loss(c, t):
    if T_CUT + 0.4 <= t < S("pourtant") + 0.3:
        a = 255 * win(t, T_CUT + 0.4, S("pourtant"), 0.3, 0.4)
        text_c(c, "15 000 000 000 / an", 540, 780, 64, PINK, a)
        if t >= S("cinq"):
            k = pop(t - S("cinq"))
            c.save()
            c.translate(540, 900)
            c.scale(k, k)
            text_c(c, "≈ 500 / seconde", 0, 0, 72, PINK, a)
            c.restore()
    if T_GHOST <= t < T_CUT + 0.4:
        a = 255 * win(t, T_GHOST + 0.4, T_CUT, 0.4, 0.4)
        text_c(c, "avant l'agriculture", 540, 880, 50, WHITE, a * 0.85, shadow=False)


def scene_universe(c, t):
    """La caméra monte : la Voie lactée rapetisse parmi des centaines de milliards de galaxies."""
    if not (T_UP <= t < T_SAND + 0.6):
        return
    fade = 1 - ease((t - T_SAND) / 0.6)
    u = ease((t - T_UP) / 1.6)
    r = lerp(420, 30, ease((t - S("galaxie")) / 2.2))
    for i, (x, y, rg, rot, col) in enumerate(GALAXIES):
        ti = S("galaxie") + 0.3 + 2.4 * (i / len(GALAXIES))
        if t < ti:
            continue
        draw_galaxy(c, x, y, rg * out((t - ti) / 0.4), 220 * fade, rot, 1.0, col)
    draw_galaxy(c, 540, lerp(-300, 560, u), r, 255 * fade, -0.3 + t * 0.03)
    if t >= S("galaxie") + 1.6:
        k = win(t, S("galaxie") + 1.6, T_SAND, 0.4, 0.4)
        c.drawCircle(540, 560, r + 22, P(GOLD, 255 * k, stroke=4))
        text_c(c, "nous", 540, 560 - r - 40, 40, GOLD, 255 * k, shadow=False)


SAND = [(RNG.uniform(0, W), RNG.uniform(1180, 1520), RNG.uniform(1.5, 3.5)) for _ in range(900)]


def scene_sand(c, t):
    if not (T_SAND <= t < T_END + 0.6):
        return None
    a = 255 * win(t, T_SAND, T_END, 0.5, 0.5)
    p = skia.Path()                                                     # une plage
    p.moveTo(0, 1150)
    p.cubicTo(300, 1120, 700, 1170, W, 1130)
    p.lineTo(W, H)
    p.lineTo(0, H)
    p.close()
    c.drawPath(p, P((230, 190, 130), a))
    wave_ = 1110 + 10 * math.sin(t * 2)
    c.drawRect(skia.Rect(0, 0, W, 0), P(WHITE, 0))
    for x, y, r in SAND:
        c.drawCircle(x, y, r, P((255, 225, 170), a * 0.8))
    c.drawLine(0, wave_, W, wave_ + 20, P(CYAN, a * 0.4, stroke=6))
    # une poignée de grains qui deviennent des étoiles et montent
    if t >= T_GRAINS:
        u = t - T_GRAINS
        for i in range(120):
            x, y, r = SAND[i * 7]
            k = ease((u - 0.012 * i) / 1.2)
            if k <= 0:
                continue
            gy = lerp(y, 150 + (i * 97) % 850, k)
            gx = lerp(x, (i * 211) % W, k * 0.3) if False else x
            col = tuple(lerp(a1, b1, k) for a1, b1 in zip((255, 225, 170), (255, 250, 225)))
            star(c, gx, gy, lerp(r, 3.0, k), a, col)
        text_c(c, "étoiles  >  grains de sable", 540, 1060, 50, GOLD, a * ease((t - T_GRAINS - 1.0) / 0.4))
    return None


def draw_sprout(c, t):
    """Une jeune pousse lumineuse, au premier plan, qui grandit à côté de l'Orbe."""
    if t < T_SPROUT:
        return
    a = 255 * (1 - ease((t - T_LOOP) / 0.6))
    g = out((t - T_SPROUT) / 1.0)
    x, y = 740.0, 1420.0
    col = (170, 255, 160)
    c.drawCircle(x, y - 90 * g, 120 * g, P(col, a * 0.35, blur=40))
    c.drawOval(skia.Rect(x - 70, y - 10, x + 70, y + 18), P((60, 40, 30), a))
    c.drawLine(x, y, x, y - 150 * g, P(col, a, stroke=10))
    for sgn, hy in ((-1, 0.75), (1, 0.95)):
        c.save()
        c.translate(x, y - 150 * g * hy)
        c.rotate(-sgn * 35)
        c.drawOval(skia.Rect(sgn * 8 * g - 34 * g + sgn * 30 * g, -16 * g, sgn * 8 * g + 34 * g + sgn * 30 * g, 16 * g),
                   P(col, a))
        c.restore()


# ------------------------------------------------------------------------------------------------ l'Orbe
def orbe_target(t):
    if T_SC - 0.2 <= t < T_TC - 0.4:
        return 760, 1000, 0.6
    if T_TC - 0.4 <= t < T_BARS:
        return 540, 560, 0.6
    if T_BARS <= t < T_CLOCK:
        return 540, 330, 0.6
    if T_CLOCK <= t < T_HUM:
        return 820, 380, 0.6
    if T_HUM <= t < T_PB:
        return 860, 420, 0.6
    if T_UP <= t < T_SAND:
        return 540, 1320, 0.7
    if T_SAND <= t < T_END:
        return 820, 520, 0.6
    if T_BACK <= t < T_LOOP:
        return 520, 1250, 0.75
    return 540, 430, 0.75


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
    i = max(0, min(int(f), len(_POSE) - 2))
    u = f - i
    a, b = _POSE[i], _POSE[i + 1]
    x, y, s = (a[j] + (b[j] - a[j]) * u for j in range(3))
    bob = 8 * math.sin(t * 2.1)
    if T_SLEEP <= t < T_HUM:                                            # il s'endort : lente respiration
        bob = 14 * math.sin(t * 1.3) + 20 * ease((t - T_SLEEP) / 0.6)
    return (x, y + bob), s


def orbe_state(t):
    cur, prev = ORBE[0], ORBE[0]
    for s_ in ORBE:
        if t >= s_[0]:
            prev, cur = cur, s_
    t0, expr, gaze = cur
    a = t - t0
    e = Etat(expr=expr, age=a, humeur_mix=a / 0.6,
             humeur_avant=HUMEUR_DE.get(prev[1], "calme") if prev is not cur else "calme")
    e.cligne = (t % 3.3) < 0.12 or (T_SLEEP + 0.3 <= t < T_HUM)          # yeux fermés quand il dort
    return e, gaze


def gaze_point(g, x, y):
    return {"balance": (540, 820), "sky": (540, 470), "forest": (540, 1250), "bars": (540, 800),
            "clock": (400, 620), "human": (540, 760), "up": (x, y - 500), "sand": (540, 1200),
            "sprout": (700, 1320)}.get(g)


def draw_beam(c, t, orig, s, tgt):
    d = (tgt[0] - orig[0], tgt[1] - orig[1])
    n = math.hypot(*d) or 1.0
    sx, sy = orig[0] + d[0] / n * 140 * s, orig[1] + d[1] / n * 140 * s
    c.drawLine(sx, sy, *tgt, P(CYAN, 110, blur=10, stroke=14))
    c.drawLine(sx, sy, *tgt, P(WHITE, 225, stroke=3.5))
    c.drawCircle(*tgt, 18 * (1 + 0.2 * math.sin(t * 10)), P(CYAN, 120, blur=10))


def draw_bubble(c, t, x, y, s):
    for t0, sym in EMO:
        a = t - t0
        dur = 2.0 if sym == "zzz" else 1.3
        if 0 <= a < dur:
            al = 255 * min(1.0, (dur - a) / 0.3)
            sc = pop(a) * max(s, 0.6) * 1.5
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
            ink = (60, 40, 110)
            if sym == "…":
                for k in range(3):
                    on = int(a * 5) % 4 > k
                    c.drawCircle(-18 + k * 18, -30, 7, P(ink, al if on else al * 0.3))
            elif sym == "zzz":
                for k in range(3):
                    f = skia.Font(E1.FONT, 22 + 8 * k)
                    c.drawString("z", -26 + k * 16, -14 - k * 12 + 3 * math.sin(a * 4 + k), f, P(ink, al))
            else:
                col = PINK if sym == "♥" else ink
                f = skia.Font(E1.FONT, 60)
                w = f.measureText(sym)
                c.drawString(sym, -w / 2, -9, f, P(col, al))
            c.restore()


def draw_orbe_at(c, t, ray):
    (x, y), s = orbe_pose(t)
    e, gaze = orbe_state(t)
    tgt = ray if gaze == "ray" else gaze_point(gaze, x, y)
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
    pan = 1100 * ease((t - T_UP) / 1.6) * (1 - ease((t - T_SAND) / 0.01)) if T_UP <= t < T_SAND else 0.0
    sky_a = 255 * max(win(t, -1, T_UP + 1.2, 0.1, 0.5), ease((t - T_END) / 0.6))
    draw_sky(c, t, sky_a, dy=pan, extra=ease((t - T_END - 0.3) / 2.0) * (1 - ease((t - T_LOOP) / 0.6)))
    draw_forest(c, t, dy=pan)
    hook_a = 255 * max(win(t, -1, S("compte"), 0.1, 0.5), ease((t - T_LOOP) / 0.6))
    draw_balance(c, t, hook_a)
    ray = scene_count_stars(c, t)
    ray = scene_count_trees(c, t) or ray
    scene_bars(c, t)
    ray = scene_clock(c, t) or ray
    scene_human(c, t)
    scene_loss(c, t)
    scene_universe(c, t)
    scene_sand(c, t)
    draw_sprout(c, t)
    draw_orbe_at(c, t, ray)
    if t < T_LOOP:
        E1.TIMING = [(txt, a, b) for _, txt, a, b in SEG]
        E1.draw_subtitle(c, t)
    else:
        text_c(c, "Tu en as planté combien ?", 540, 1690, 60, WHITE, 255 * ease((t - T_LOOP - 0.3) / 0.4))


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
    add(0.2, E1.swell(0.12))
    add(T_TILT, E1.tock(0.16))
    for k, dt in enumerate((0.1, 0.5, 0.85)):
        add(T_SC + dt, E1.pop_s(penta[k], 0.16))
    for k in range(12):
        add(T_SC + 1.1 + 0.9 * (k / 12) ** 0.5, E1.pop_s(penta[k % 6], 0.06))
    add(T_GAL, E1.sparkle(0.12))
    add(T_SLOCK, E1.ding(784, 0.14))
    for k in range(16):                                                # la forêt pousse : petits « bloops »
        add(T_TC + 1.1 * k / 16, E1.pop_s(300 + 25 * (k % 5), 0.08))
    add(T_TLOCK, E1.ding(660, 0.16))
    add(T_BARS, E1.swish(0.8, 0.12))
    add(T_BARS + 0.3, E1.sparkle(0.12))
    for k in range(int(T_FAST - T_CLOCK) + 1):                         # tic… tic…
        add(T_CLOCK + k, E1.tock(0.12))
    add(T_FAST, E1.swish(T_YEARS + 0.8 - T_FAST, 0.14))
    add(T_YEARS + 0.8, E1.ding(523, 0.14))
    add(T_HUM, E1.pop_s(500, 0.16))
    add(T_HUM + 0.3, E1.sparkle(0.1))
    add(T_GHOST, E1.swell(0.14))
    for k in range(20):                                                # les arbres s'éteignent, de plus en plus vite
        add(T_CUT + 3.6 * (0.45 * k / 20) ** 0.6, E1.tock(0.06))
    add(T_UP, E1.swish(1.6, 0.16))
    add(S("galaxie") + 0.3, E1.swell(0.16))
    add(S("galaxie") + 1.6, E1.ding(784, 0.12))
    add(T_SAND, E1.swish(1.2, 0.1))
    add(T_GRAINS, E1.sparkle(0.14))
    add(T_GRAINS + 0.8, E1.sparkle(0.1))
    add(T_BACK, E1.swell(0.1))
    add(T_SPROUT, E1.pop_s(440, 0.14))
    add(T_SPROUT + 0.3, E1.sparkle(0.12))
    add(T_LOOP, E1.swish(0.8, 0.1))
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
    out_path = sys.argv[1] if len(sys.argv) > 1 else "output/ep04_arbres.mp4"
    render(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
