"""Épisode 8 — « Et si tu étais déjà mort ? » (mondes multiples et immortalité quantique).

La voix off (audio/voix.mp3) raconte ; l'Orbe vit l'expérience de pensée. Minutage : phrases mesurées (silences +
reconnaissance vocale) dans SEG ; S(clé) = début, E(clé) = fin.

    python -m films.episodes.ep08_quantique.ep08 sortie.mp4
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

SEG = [("h1", "Et si tu étais déjà mort…", 0.0, 1.77),
       ("h2", "et que tu vivais seulement la version où tu as survécu ?", 2.87, 5.46),
       ("phys", "Cette idée vient de la physique quantique.", 6.04, 8.17),
       ("interp", "Une des façons de l'interpréter s'appelle…", 8.72, 10.70),
       ("mondes", "les mondes multiples.", 11.01, 12.16), ("selon", "Selon elle,", 12.62, 13.28),
       ("hasard", "à chaque événement dû au hasard,", 13.50, 15.18), ("divise", "l'univers se divise.", 15.43, 16.74),
       ("br1", "Dans une branche,", 17.19, 18.15), ("gauche", "tu vas à gauche.", 18.37, 19.30),
       ("autre", "Dans une autre…", 19.75, 20.53), ("droite", "tu vas à droite.", 20.93, 21.79),
       ("toutes", "Toutes les possibilités existent en même temps.", 22.22, 24.60),
       ("troublant", "Mais voici où ça devient troublant.", 25.02, 26.66),
       ("accident", "Imagine un accident.", 27.08, 28.09), ("certaines", "Dans certaines branches,", 28.42, 29.43),
       ("sensort", "tu ne t'en sors pas.", 29.68, 30.42), ("dautres", "Dans d'autres…", 30.85, 31.51),
       ("si", "si.", 31.98, 32.33), ("vivre", "Tu ne peux vivre que celles où tu es encore là.", 32.71, 35.08),
       ("pdv", "De ton point de vue…", 35.48, 36.33), ("survis", "tu survis toujours.", 36.62, 37.62),
       ("immort", "C'est ce qu'on appelle l'immortalité quantique.", 37.99, 40.33),
       ("temps", "Avec le temps,", 40.74, 41.47), ("tout", "tu survivrais à tout…", 41.77, 42.97),
       ("pendant", "pendant que, dans ta branche,", 43.28, 44.90),
       ("autres", "les autres partiraient un à un.", 45.17, 46.81), ("rassure", "Rassure-toi :", 47.26, 47.84),
       ("verif", "personne ne peut le vérifier,", 48.12, 49.38),
       ("phys2", "et la plupart des physiciens n'y croient pas.", 49.61, 51.38),
       ("vieillir", "Vieillir, ce n'est pas un pile ou face.", 51.74, 53.84),
       ("question", "Mais une question reste…", 54.23, 55.56),
       ("combien", "combien de fois as-tu déjà failli ne pas être là ?", 56.01, 58.96)]
_K = {k: (a, b) for k, _, a, b in SEG}


def S(k):
    return _K[k][0]


def E(k):
    return _K[k][1]


DUR = E("combien") + 2.6

# repères (actions APRÈS la phrase qui les annonce)
T_TURN = S("h2") + 1.6                                   # il se retourne vers son fantôme
T_PART = S("phys") + 0.3                                 # une particule part vers les deux fentes
T_WAVE = S("phys") + 1.3                                 # elle devient onde
T_BUBBLE = S("mondes") - 0.1                             # l'univers-bulle
T_SPLIT = (E("divise") + 0.05, E("divise") + 0.6)        # la bulle se divise en 2, puis en 4
T_FORK = S("br1")                                        # l'embranchement
T_LEFT = E("gauche") + 0.05                              # une copie part à gauche
T_RIGHT = E("droite") + 0.05                             # l'autre part à droite
T_TREE = (S("toutes"), E("toutes"))                      # l'arbre des possibles pousse
T_DARK = S("troublant")
T_COIN = S("accident") + 0.2
T_DEAD = S("sensort")                                    # des branches s'éteignent
T_ALIVE = S("si")                                        # les autres s'allument
T_PATH = (E("si") + 0.3, E("survis"))                    # il parcourt le seul chemin allumé
T_TITLE = S("immort") + 0.9
T_FRIENDS = S("temps")
T_FADE = (S("autres") + 0.1, E("autres") + 0.3)          # ses amis s'éteignent un à un
T_WARM = S("rassure")
T_CURVE = S("vieillir") + 0.4
T_END = S("question")
T_LOOP = E("combien") + 0.5

ORBE = [(0.0, "surpris", "cam"), (T_TURN, "surpris", "ghost"), (S("phys"), "reflechit", "slit"),
        (T_WAVE + 0.6, "surpris", "slit"), (T_BUBBLE, "neutre", "bubble"), (T_SPLIT[0], "surpris", "bubble"),
        (T_FORK, "reflechit", "left"), (T_LEFT + 0.6, "neutre", "right"), (T_TREE[0], "surpris", "tree"),
        (T_DARK, "reflechit", None), (T_COIN, "neutre", "coin"), (T_DEAD, "triste", "tree"),
        (T_ALIVE, "joie", "tree"), (T_PATH[0], "neutre", "up"), (T_TITLE, "idee", None),
        (T_FRIENDS, "joie", "friends"), (T_FADE[0], "triste", "friends"), (T_WARM + 0.3, "neutre", None),
        (T_CURVE + 0.3, "joie", "curve"), (T_END, "reflechit", None), (S("combien") + 0.5, "neutre", "cam"),
        (T_LOOP, "neutre", None)]
EMO = [(T_TURN + 0.1, "!"), (T_WAVE + 0.65, "?"), (T_SPLIT[0] + 0.1, "!"), (T_TREE[0] + 0.3, "!"),
       (S("troublant") + 0.3, "…"), (T_DEAD + 0.1, "…"), (T_ALIVE + 0.05, "!"), (T_FADE[0] + 0.8, "…"),
       (T_CURVE + 0.35, "♥"), (S("combien") + 1.0, "?")]
CHIRPS = [(T_TURN + 0.1, "surprise"), (T_WAVE + 0.65, "question"), (T_SPLIT[0] + 0.1, "surprise"),
          (T_LEFT, "bip"), (T_RIGHT, "bip"), (T_TREE[0] + 0.3, "surprise"), (T_DEAD + 0.1, "triste"),
          (T_ALIVE + 0.05, "joie"), (T_FADE[0] + 0.8, "triste"), (T_CURVE + 0.35, "joie"),
          (S("combien") + 1.0, "question")]


def win(t, a, b, fi=0.4, fo=0.4):
    return ease((t - a) / fi) * (1 - ease((t - b) / fo))


def mini_orbe(c, t, x, y, s, a, expr="neutre", gray=False):
    """Une Orbe secondaire (copie, fantôme, ami) avec opacité."""
    if a <= 1 or s <= 0.01:
        return
    c.saveLayerAlpha(None, int(min(255, a)))
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    e = Etat(expr=expr, age=2.0, humeur_mix=1.0)
    e.cligne = (t % 3.7) < 0.1
    draw_orbe(c, t, e)
    if gray:
        c.drawCircle(0, 0, 150, P((40, 40, 50), 170))
    c.restore()
    c.restore()


# ------------------------------------------------------------------------------------------------ scènes
def scene_hook(c, t):
    """Le fantôme de l'Orbe derrière lui, qui s'efface (et revient pour la boucle)."""
    a = 0.0
    if t < S("phys") + 0.3:
        a = 120 * (1 - ease((t - (S("h2") + 2.0)) / 1.0))                # visible dès la 1re image
    if t >= T_LOOP:
        a = 120 * ease((t - T_LOOP) / 0.8)
    if a > 1:
        drift = -30 * ease(t / 5) if t < 10 else 0
        mini_orbe(c, t, 700, 780 + drift, 0.95, a, "neutre", gray=True)


SLITS = (430.0, 650.0)
WALL_Y = 1080.0
SCREEN_Y = 640.0


def scene_slits(c, t):
    if not (S("phys") <= t < T_BUBBLE + 0.6):
        return None
    a = 255 * win(t, S("phys"), T_BUBBLE, 0.4, 0.5)
    for x0, x1 in ((80, SLITS[0] - 22), (SLITS[0] + 22, SLITS[1] - 22), (SLITS[1] + 22, 1000)):
        c.drawRoundRect(skia.Rect(x0, WALL_Y - 14, x1, WALL_Y + 14), 6, 6, P((150, 140, 190), a))
    c.drawRect(skia.Rect(80, SCREEN_Y - 10, 1000, SCREEN_Y + 10), P((60, 50, 90), a))
    ray = None
    if T_PART <= t < T_WAVE:
        u = ease((t - T_PART) / (T_WAVE - T_PART))
        y = lerp(1480, WALL_Y + 20, u)
        c.drawCircle(540, y, 14, P(CYAN, a))
        c.drawCircle(540, y, 34, P(CYAN, a * 0.4, blur=12))
        ray = (540, y)
    if t >= T_WAVE:
        k = t - T_WAVE
        for sx in SLITS:
            for i in range(10):
                r = ((k * 180 + i * 60) % 600)
                al = a * 0.5 * (1 - r / 600) * min(1.0, k / 0.3)
                c.drawArc(skia.Rect(sx - r, WALL_Y - r, sx + r, WALL_Y + r), 180, 180, False, P(CYAN, al, stroke=3))
        # figure d'interférence sur l'écran
        g = ease((k - 1.0) / 1.2)
        for i in range(0, 900, 6):
            x = 90 + i
            d1 = math.hypot(x - SLITS[0], SCREEN_Y - WALL_Y)
            d2 = math.hypot(x - SLITS[1], SCREEN_Y - WALL_Y)
            v = math.cos((d1 - d2) / 34 * math.pi) ** 2 * math.exp(-((x - 540) / 380) ** 2)
            c.drawRect(skia.Rect(x, SCREEN_Y - 60, x + 6, SCREEN_Y - 12), P(CYAN, a * g * v))
    return ray


def bubble(c, x, y, r, a, label=None):
    c.drawCircle(x, y, r * 1.15, P(VIOLET, a * 0.25, blur=r * 0.3))
    sh = skia.GradientShader.MakeRadial(skia.Point(x - r * 0.3, y - r * 0.35), r * 1.3,
                                        [E1.rgb((255, 255, 255), a * 0.5), E1.rgb((150, 120, 255), a * 0.25),
                                         E1.rgb((40, 30, 90), a * 0.15)], [0.0, 0.5, 1.0])
    c.drawCircle(x, y, r, P(shader=sh))
    c.drawCircle(x, y, r, P((200, 180, 255), a * 0.8, stroke=3))
    rr = np.random.default_rng(int(x * 7 + y))
    for _ in range(14):
        px, py = rr.uniform(-0.7, 0.7, 2) * r
        c.drawCircle(x + px, y + py, 2.2, P(WHITE, a * 0.8))
    if label:
        text_c(c, label, x, y + 14, 40, WHITE, a, shadow=False)


def scene_bubble(c, t):
    if not (T_BUBBLE <= t < T_FORK + 0.5):
        return
    a = 255 * win(t, T_BUBBLE, T_FORK, 0.4, 0.5)
    cx, cy = 540.0, 1060.0
    s1 = ease((t - T_SPLIT[0]) / 0.45)
    s2 = ease((t - T_SPLIT[1]) / 0.45)
    if s1 <= 0:
        bubble(c, cx, cy, 220 * pop(t - T_BUBBLE), a, "mondes multiples" if t > S("mondes") + 0.2 else None)
        return
    for sx in (-1, 1):
        x = cx + sx * 190 * s1
        if s2 <= 0:
            bubble(c, x, cy, lerp(220, 160, s1), a)
        else:
            for sy in (-1, 1):
                bubble(c, x + sx * 30 * s2, cy + sy * 190 * s2, lerp(160, 120, s2), a)


FORK = (540.0, 1250.0)
LEFT_END, RIGHT_END = (270.0, 860.0), (810.0, 860.0)


def scene_fork(c, t):
    if not (T_FORK <= t < T_TREE[0] + 0.6):
        return
    a = 255 * win(t, T_FORK, T_TREE[0], 0.4, 0.5)
    g = ease((t - T_FORK) / 0.8)
    for end in (LEFT_END, RIGHT_END):
        ex, ey = lerp(FORK[0], end[0], g), lerp(FORK[1], end[1], g)
        c.drawLine(*FORK, ex, ey, P(VIOLET, a * 0.5, blur=8, stroke=16))
        c.drawLine(*FORK, ex, ey, P((210, 200, 255), a, stroke=5))
    c.drawLine(540, 1560, *FORK, P((210, 200, 255), a, stroke=5))
    text_c(c, "gauche", LEFT_END[0], LEFT_END[1] - 40, 38, WHITE, a * 0.8, shadow=False)
    text_c(c, "droite", RIGHT_END[0], RIGHT_END[1] - 40, 38, WHITE, a * 0.8, shadow=False)
    if t >= T_LEFT:                                             # la copie qui part à gauche
        u = ease((t - T_LEFT) / 0.9)
        mini_orbe(c, t, lerp(FORK[0], LEFT_END[0], u), lerp(FORK[1], LEFT_END[1] + 90, u), 0.6, a, "neutre")


# l'arbre des possibles
TREE = []                                                       # (x0, y0, x1, y1, profondeur, feuille_index)


def _grow(x, y, ang, ln, d, idx):
    x1, y1 = x + ln * math.sin(ang), y - ln * math.cos(ang)
    leaf = idx if d == 6 else None
    TREE.append((x, y, x1, y1, d, idx))
    if d < 6:
        spread = 0.52 - d * 0.045
        _grow(x1, y1, ang - spread, ln * 0.78, d + 1, idx * 2)
        _grow(x1, y1, ang + spread, ln * 0.78, d + 1, idx * 2 + 1)


_grow(540, 1560, 0.0, 190, 0, 0)
_rng = np.random.default_rng(8)
SURV = [int(_rng.integers(0, 2)) for _ in range(7)]            # le seul chemin qui survit


def on_path(d, idx):
    """Le segment (profondeur d, index idx) est-il sur le chemin du survivant ?"""
    want = 0
    for k in range(d):
        want = want * 2 + SURV[k + 1] if k + 1 < len(SURV) else want * 2
    return idx == want


ALIVE_LEAF = {i: bool(_rng.random() < 0.45) for i in range(64)}


def path_points():
    pts = []
    for x0, y0, x1, y1, d, idx in TREE:
        if on_path(d, idx):
            pts.append((d, (x0, y0), (x1, y1)))
    pts.sort()
    return [pts[0][1]] + [p[2] for p in pts]


PATH = path_points()


def scene_tree(c, t):
    if not (T_TREE[0] <= t < T_TITLE + 0.3):
        return None
    a = 255 * win(t, T_TREE[0], T_TITLE - 0.2, 0.3, 0.5)
    g = ease((t - T_TREE[0]) / 2.0) * 7
    dark = 1 - 0.45 * ease((t - T_DARK) / 0.8)
    for x0, y0, x1, y1, d, idx in TREE:
        k = min(1.0, max(0.0, g - d))
        if k <= 0:
            continue
        xe, ye = lerp(x0, x1, k), lerp(y0, y1, k)
        leaf_ids = range(idx << (6 - d), (idx + 1) << (6 - d))
        alive = any(ALIVE_LEAF[i] for i in leaf_ids) or on_path(d, idx)
        col = (200, 190, 255)
        al = a * dark
        w = max(2.0, 7 - d)
        if t >= T_DEAD and not alive:
            f = ease((t - T_DEAD - 0.15 * (idx % 5)) / 0.5)
            col = tuple(lerp(ci, 90, f) for ci in col)
            al *= 1 - 0.55 * f
        if t >= T_ALIVE and alive:
            f = ease((t - T_ALIVE) / 0.4)
            col = tuple(lerp(ci, cg, f) for ci, cg in zip(col, GOLD))
        if t >= T_PATH[0]:                                      # seul le chemin du survivant reste vif
            f = ease((t - T_PATH[0]) / 0.5)
            if on_path(d, idx):
                col = GOLD
                w += 3 * f
            else:
                al *= 1 - 0.7 * f
        c.drawLine(x0, y0, xe, ye, P(col, al * 0.35, blur=6, stroke=w * 2.5))
        c.drawLine(x0, y0, xe, ye, P(col, al, stroke=w))
        if d == 6 and k >= 1:
            dead = t >= T_DEAD and not ALIVE_LEAF[idx] and not on_path(d, idx)
            c.drawCircle(x1, y1, 9, P((110, 110, 120) if dead else CYAN, al))
    return None


def scene_coin(c, t):
    if not (T_COIN <= t < T_PATH[0] + 0.4):
        return
    a = 255 * win(t, T_COIN, T_PATH[0], 0.3, 0.4)
    cx, cy = 540.0, 470.0
    spin = math.cos((t - T_COIN) * 11)
    rx = 110 * abs(spin) + 6
    y = cy - 60 * abs(math.sin((t - T_COIN) * 3.2))
    c.drawOval(skia.Rect(cx - rx, y - 110, cx + rx, y + 110), P(GOLD, a))
    c.drawOval(skia.Rect(cx - rx, y - 110, cx + rx, y + 110), P((200, 150, 50), a, stroke=6))
    if abs(spin) > 0.35:
        c.save()
        c.translate(cx, y)
        c.scale(abs(spin), 1)
        text_c(c, "✓" if spin > 0 else "✕", 0, 30, 90, (120, 80, 20), a, shadow=False)
        c.restore()


def scene_title(c, t):
    if not (T_TITLE <= t < T_FRIENDS + 0.6):
        return
    a = 255 * win(t, T_TITLE, T_FRIENDS, 0.4, 0.5)
    sc = pop(t - T_TITLE)
    c.save()
    c.translate(540, 700)
    c.scale(sc, sc)
    text_c(c, "IMMORTALITÉ", 0, 0, 92, GOLD, a)
    text_c(c, "QUANTIQUE", 0, 100, 92, GOLD, a)
    c.restore()
    r = 190 + 8 * math.sin(t * 3)                               # anneau « infini » autour de l'Orbe
    c.drawCircle(540, 1150, r, P(GOLD, a * 0.35, blur=16, stroke=12))
    c.drawCircle(540, 1150, r, P(GOLD, a * 0.8, stroke=3))


FRIEND_COLS = [PINK, CYAN, GOLD, (140, 230, 160), VIOLET, (255, 150, 90)]


def scene_friends(c, t):
    if not (T_FRIENDS <= t < T_CURVE + 0.4):
        return
    a = 255 * win(t, T_FRIENDS, T_CURVE - 0.2, 0.5, 0.4)
    warm = ease((t - T_WARM) / 0.8)
    for i, col in enumerate(FRIEND_COLS):
        ang = -math.pi / 2 + i * 2 * math.pi / 6 + 0.1 * math.sin(t * 0.5)
        x, y = 540 + 290 * math.cos(ang), 1000 + 290 * math.sin(ang)
        ti = T_FADE[0] + (T_FADE[1] - T_FADE[0]) * i / 6
        gone = ease((t - ti) / 0.5) * (1 - warm)
        k = pop(t - T_FRIENDS - 0.1 * i)
        r = 46 * k
        cc = tuple(lerp(ci, 70, gone) for ci in col)
        al = a * (1 - 0.8 * gone)
        c.drawCircle(x, y, r * 1.6, P(cc, al * 0.35, blur=14))
        c.drawCircle(x, y, r, P(cc, al))
        c.drawCircle(x - r * 0.3, y - r * 0.1, r * 0.13, P((30, 20, 50), al))
        c.drawCircle(x + r * 0.3, y - r * 0.1, r * 0.13, P((30, 20, 50), al))


def scene_warm(c, t):
    """« Rassure-toi » : lumière chaude, puis une courbe douce remplace la pièce."""
    if not (T_WARM <= t < T_END + 0.5):
        return
    a = win(t, T_WARM, T_END, 0.8, 0.5)
    c.drawRect(skia.Rect(0, 0, W, H), P((255, 190, 120), 40 * a))
    if t >= S("verif") + 0.2:
        text_c(c, "invérifiable", 540, 1440, 44, WHITE, 255 * a * win(t, S("verif") + 0.2, T_CURVE - 0.2), shadow=False)
    if t >= S("phys2") + 0.3:
        text_c(c, "rejetée par la plupart des physiciens", 540, 1500, 36, WHITE,
               220 * a * win(t, S("phys2") + 0.3, T_CURVE - 0.2), shadow=False)
    if t >= T_CURVE:
        g = ease((t - T_CURVE) / 1.2)
        path = skia.Path()
        for i in range(0, 101):
            u = i / 100
            if u > g:
                break
            x = 190 + 700 * u
            y = 1200 + 260 * (1 / (1 + math.exp(-(u - 0.75) * 10)))
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        c.drawPath(path, P(GOLD, 255 * a * 0.4, blur=8, stroke=14))
        c.drawPath(path, P(GOLD, 255 * a, stroke=5))
        c.drawLine(190, 1480, 900, 1480, P(WHITE, 150 * a * g, stroke=2))
        text_c(c, "vieillir : lent et progressif", 540, 1560, 38, WHITE, 255 * a * ease((t - T_CURVE - 0.8) / 0.4),
               shadow=False)
        text_c(c, "pas un pile ou face", 540, 1150, 44, GOLD, 255 * a * ease((t - T_CURVE - 0.4) / 0.4))


def scene_end(c, t):
    if t < T_END:
        return
    a = 255 * ease((t - T_END) / 0.8) * (1 - ease((t - T_LOOP) / 0.6))
    for x0, y0, x1, y1, d, idx in TREE:                        # l'arbre, en fantôme derrière lui
        c.drawLine(x0, y0 - 250, x1, y1 - 250, P((200, 190, 255), a * 0.18, stroke=max(1.5, 5 - d)))
    k = pop(t - S("combien") - 1.0)
    if t > S("combien") + 1.0:
        text_c(c, "?", 540, 560, 180 * k, GOLD, a * 0.8)
    if t >= T_LOOP:
        text_c(c, "Combien de fois, toi ?", 540, 1690, 60, WHITE, 255 * ease((t - T_LOOP - 0.3) / 0.4))


# ------------------------------------------------------------------------------------------------ l'Orbe
def orbe_target(t):
    if t < S("phys"):
        return 440, 900, 1.0
    if t < T_BUBBLE:
        return 870, 420, 0.55
    if t < T_FORK:
        return 540, 430, 0.7
    if t < T_RIGHT:
        return FORK[0], FORK[1] + 90, 0.6
    if t < T_TREE[0]:
        return RIGHT_END[0], RIGHT_END[1] + 90, 0.6
    if t < T_COIN:
        return 540, 1640, 0.4
    if t < T_PATH[0]:
        return 870, 420, 0.5
    if t < T_TITLE:
        u = ease((t - T_PATH[0]) / (T_PATH[1] - T_PATH[0]))
        f = u * (len(PATH) - 1)
        i = min(int(f), len(PATH) - 2)
        v = f - i
        p = (lerp(PATH[i][0], PATH[i + 1][0], v), lerp(PATH[i][1], PATH[i + 1][1], v))
        return p[0], p[1] - 40, 0.4
    if t < T_WARM:
        return 540, 1000 if t >= T_FRIENDS else 1150, 0.8
    if t < T_END:
        return 540, 560 if t >= T_CURVE else 1000, 0.7
    return 540, 1000, 1.0


_POSE = {}


def orbe_pose(t):
    if not _POSE:
        n = int(DUR * FPS) + 2
        x, y, s = orbe_target(0.0)
        vx = vy = vs = 0.0
        h = 1.0 / (FPS * 4)
        w = 8.0
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
    e.cligne = t > 1.0 and (t % 3.3) < 0.12                                # yeux grands ouverts sur l'accroche
    return e, gaze


def gaze_point(g, x, y):
    return {"ghost": (700, 780), "slit": (540, 900), "bubble": (540, 1060), "left": LEFT_END, "right": RIGHT_END,
            "tree": (540, 1100), "coin": (540, 470), "up": (x, y - 400), "friends": (x + 200, y),
            "curve": (540, 1300), "cam": (x, y + 1)}.get(g)


def draw_bubble(c, t, x, y, s):
    for t0, sym in EMO:
        a = t - t0
        if 0 <= a < 1.3:
            al = 255 * min(1.0, (1.3 - a) / 0.3)
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
            else:
                f = skia.Font(E1.FONT, 60)
                w = f.measureText(sym)
                c.drawString(sym, -w / 2, -9, f, P(PINK if sym == "♥" else ink, al))
            c.restore()


def draw_orbe_at(c, t, ray):
    (x, y), s = orbe_pose(t)
    e, gaze = orbe_state(t)
    tgt = ray if (ray is not None and gaze == "slit") else gaze_point(gaze, x, y)
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
    # ambiance : plus sombre et mystérieuse, sauf pendant « rassure-toi »
    dim = 0.45 * (1 - win(t, T_WARM, T_END, 0.8, 0.8))
    c.drawRect(skia.Rect(0, 0, W, H), P((4, 3, 12), 255 * dim))
    scene_hook(c, t)
    ray = scene_slits(c, t)
    scene_bubble(c, t)
    scene_fork(c, t)
    scene_tree(c, t)
    scene_coin(c, t)
    scene_title(c, t)
    scene_friends(c, t)
    scene_warm(c, t)
    scene_end(c, t)
    draw_orbe_at(c, t, ray)
    if t < T_LOOP:
        E1.TIMING = [(txt, a, b) for _, txt, a, b in SEG]
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

    add(0.1, E1.swell(0.14))
    add(T_TURN, E1.swish(0.6, 0.1))
    add(T_PART, E1.swish(1.0, 0.1))
    add(T_WAVE, E1.ding(660, 0.12))
    add(T_WAVE + 1.0, E1.sparkle(0.08))
    add(T_BUBBLE, E1.pop_s(420, 0.16))
    add(T_SPLIT[0], E1.pop_s(520, 0.16))
    add(T_SPLIT[1], E1.pop_s(620, 0.14))
    add(T_FORK, E1.swish(0.8, 0.1))
    add(T_LEFT, E1.pop_s(480, 0.14))
    add(T_RIGHT, E1.pop_s(560, 0.14))
    for k in range(7):                                          # l'arbre se ramifie
        add(T_TREE[0] + 2.0 * k / 7, E1.ding(523 + 60 * k, 0.07))
    add(T_DARK, E1.swell(0.18))
    for k in range(10):                                         # la pièce tourne
        add(T_COIN + 0.2 * k, E1.tock(0.05))
    add(T_DEAD, E1.swell(0.12))
    add(T_ALIVE, E1.sparkle(0.12))
    add(T_PATH[0], E1.swish(T_PATH[1] - T_PATH[0], 0.08))
    add(T_TITLE, E1.swell(0.2))
    add(T_TITLE + 0.1, E1.ding(784, 0.14))
    for i in range(6):                                          # les amis s'éteignent
        add(T_FADE[0] + (T_FADE[1] - T_FADE[0]) * i / 6, E1.ding(660 - 50 * i, 0.08))
    add(T_WARM, E1.sparkle(0.12))
    add(T_CURVE, E1.swish(1.2, 0.08))
    add(T_END, E1.swell(0.14))
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
    st = np.stack([out_, out_], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


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


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep08_quantique.mp4")
