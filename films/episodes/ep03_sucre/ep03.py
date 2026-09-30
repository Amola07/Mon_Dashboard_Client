"""Épisode 3 — « Toute l'humanité tient dans un morceau de sucre ».

La voix off (audio/voix.mp3) enseigne ; l'Orbe écoute, agit juste après chaque consigne (dans les silences naturels
de l'enregistrement) et réagit. Tous les repères d'animation sont rattachés aux phrases mesurées (SEG) : S(clé) est le
début d'une phrase, E(clé) sa fin.

    python -m films.episodes.ep03_sucre.ep03 sortie.mp4
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
SEG = [("hook1", "Toute l'humanité…", 0.0, 1.12), ("hook2", "tient dans un morceau de sucre.", 2.0, 3.84),
       ("imp", "Impossible ?", 4.35, 5.02), ("main", "Regarde ta main.", 5.43, 6.17), ("zoom", "Zoome.", 6.60, 6.98),
       ("encore", "Encore.", 7.63, 8.09), ("cells", "Des cellules…", 8.57, 9.47), ("mol", "des molécules…", 9.83, 10.78),
       ("atoms", "des atomes.", 11.21, 12.01), ("maint", "Maintenant,", 12.45, 12.99),
       ("enter", "entre dans un atome.", 13.29, 14.32),
       ("bille", "Si son noyau avait la taille d'une bille…", 14.75, 16.83),
       ("stade", "l'atome serait grand comme un stade.", 17.18, 19.04), ("entre", "Et entre les deux ?", 19.54, 20.30),
       ("rien", "Rien.", 20.73, 21.04), ("vide", "Du vide.", 21.55, 22.07),
       ("corps", "Ton corps est fait de vide…", 22.58, 24.01), ("pct", "à plus de 99,9999 %.", 24.29, 27.76),
       ("table", "Alors pourquoi ta main ne traverse pas la table ?", 28.20, 30.35),
       ("elec", "Ses électrons repoussent ceux de la table.", 30.78, 32.74),
       ("touch", "Tu ne touches jamais vraiment rien.", 33.13, 34.66), ("maint2", "Maintenant,", 35.17, 35.62),
       ("enleve", "enlève tout le vide.", 35.95, 36.93), ("ecrase", "Écrase chaque atome…", 37.33, 38.54),
       ("humain", "de chaque humain sur Terre.", 38.73, 40.10), ("huit", "8 milliards de personnes…", 40.48, 42.06),
       ("sucre", "dans un seul morceau de sucre.", 42.35, 44.25), ("pese", "Un sucre qui pèserait…", 44.63, 45.88),
       ("tonnes", "400 millions de tonnes.", 46.11, 47.79), ("existe", "Et ça existe vraiment.", 48.13, 49.31),
       ("geante", "Quand une étoile géante meurt,", 49.74, 51.18),
       ("ecrase2", "elle s'écrase exactement comme ça.", 51.45, 53.40), ("neutron", "Une étoile à neutrons.", 53.80, 55.04),
       ("soleil", "Plus lourde que le Soleil…", 55.40, 56.78), ("ville", "dans la taille d'une ville.", 56.98, 58.19),
       ("cuill", "Une seule cuillère de cette étoile pèse plus que toute l'humanité.", 58.55, 62.00),
       ("souv", "Alors souviens-toi…", 62.46, 63.31), ("fait", "tu es fait…", 63.63, 64.23),
       ("presque", "presque entièrement…", 64.44, 65.41), ("rien2", "de rien.", 65.71, 66.35)]
_K = {k: (a, b) for k, _, a, b in SEG}


def S(k):
    return _K[k][0]


def E(k):
    return _K[k][1]


DUR = E("rien2") + 2.6

# repères des scènes (tous APRÈS la consigne correspondante)
T_HAND = S("main") + 0.25                               # la main apparaît
T_ZOOM = [E("zoom") + 0.05, S("cells") - 0.25, S("mol") - 0.2, S("atoms") - 0.2]   # peau, cellules, molécules, atomes
T_ENTER = E("enter") + 0.05                             # il plonge dans un atome
T_BILLE = S("bille") + 0.9                              # le noyau-bille
T_STADE = S("stade") + 0.5                              # on recule : le stade
T_RIEN = S("rien")
T_PCT = S("pct") + 0.1
T_TABLE = S("table") + 0.3
T_PUSH = E("table") + 0.05                              # il essaie d'appuyer (après la question)
T_FIELD = S("elec") + 0.4                               # on voit les électrons se repousser
T_VIDE = E("enleve") + 0.05                             # il aspire le vide
T_CRUSH = S("ecrase") + 0.4
T_CROWD = S("humain") + 0.1
T_SQUEEZE = (S("huit") + 0.3, S("sucre") + 0.2)         # la foule se comprime
T_CUBE = S("sucre") + 0.2
T_ONTOP = S("pese") + 0.1                               # le sucre se pose sur l'Orbe
T_HEAVY = S("tonnes") + 0.2                             # 400 millions de tonnes : il s'enfonce
T_STAR = S("geante") + 0.1
T_BOOM = S("ecrase2") + 0.45
T_SUN = S("soleil") + 0.15
T_CITY = S("ville") + 0.15
T_SPOON = S("cuill") + 0.2
T_SCALE = S("cuill") + 0.45 * (E("cuill") - S("cuill"))
T_GHOST = (S("presque"), E("rien2"))                    # il devient presque transparent
T_LOOP = E("rien2") + 0.6                               # retour à l'image du début

ORBE = [(0.0, "surpris", "cube"), (S("imp") + 0.2, "reflechit", None), (E("main") + 0.05, "neutre", "hand"),
        (T_ZOOM[0], "surpris", "zoom"), (T_ZOOM[1] + 0.2, "joie", "zoom"), (T_ZOOM[3] + 0.3, "neutre", "zoom"),
        (T_ENTER, "surpris", "zoom"), (T_BILLE, "reflechit", "marble"), (T_STADE + 0.3, "surpris", "marble"),
        (S("vide") + 0.1, "triste", "marble"), (T_PCT + 1.4, "surpris", "self"), (T_TABLE, "reflechit", "table"),
        (T_PUSH, "neutre", "table"), (T_FIELD + 0.4, "surpris", "table"), (S("touch") + 0.3, "etourdi", None),
        (T_VIDE, "neutre", "center"), (T_CROWD, "surpris", "center"), (T_CUBE + 0.1, "joie", "center"),
        (T_ONTOP, "neutre", "up"), (T_HEAVY, "etourdi", "up"), (S("existe") + 0.3, "reflechit", None),
        (T_STAR, "neutre", "star"), (T_BOOM + 0.1, "surpris", "star"), (T_CITY + 0.3, "idee", "star"),
        (T_SPOON, "neutre", "spoon"), (T_SCALE + 0.9, "surpris", "balance"), (S("souv"), "neutre", None),
        (S("fait") + 0.2, "reflechit", "self"), (T_GHOST[0] + 0.3, "surpris", "self"), (T_LOOP, "amour", "cube")]
EMO = [(S("imp") + 0.25, "?"), (T_ZOOM[0] + 0.1, "!"), (T_BILLE + 0.1, "…"), (T_PCT + 1.45, "!"),
       (E("table") + 0.0, "?"), (T_FIELD + 0.45, "!"), (T_CUBE + 0.15, "!"), (T_BOOM + 0.15, "!"), (T_SCALE + 0.95, "!"),
       (T_GHOST[0] + 0.35, "!")]
CHIRPS = [(0.4, "surprise"), (S("imp") + 0.25, "question"), (T_ZOOM[1] + 0.2, "joie"), (S("rien") + 0.3, "triste"),
          (T_PCT + 1.45, "surprise"), (E("table"), "question"), (T_PUSH + 0.1, "effort"), (T_PUSH + 0.9, "effort"),
          (T_FIELD + 0.45, "surprise"), (T_CUBE + 0.15, "joie"), (T_HEAVY + 0.05, "triste"), (T_BOOM + 0.15, "surprise"),
          (T_SCALE + 0.95, "surprise"), (T_GHOST[0] + 0.35, "surprise"), (T_LOOP + 0.1, "joie")]


# ------------------------------------------------------------------------------------------------ outils
def win(t, a, b, fi=0.4, fo=0.4):
    """Opacité (0→1→0) d'un élément visible entre a et b."""
    return ease((t - a) / fi) * (1 - ease((t - b) / fo))


RNG = np.random.default_rng(3)
CROWD = [(RNG.uniform(60, 1020), RNG.uniform(760, 1500), RNG.uniform(0.7, 1.2), RNG.uniform(0, 1),
          (VIOLET, CYAN, PINK, GOLD, (140, 230, 170))[i % 5]) for i in range(170)]


def person(c, x, y, s, col, a):
    if a <= 1 or s <= 0.02:
        return
    c.drawCircle(x, y - 22 * s, 8 * s, P(col, a))
    c.drawRoundRect(skia.Rect(x - 9 * s, y - 12 * s, x + 9 * s, y + 14 * s), 7 * s, 7 * s, P(col, a))


def draw_crowd(c, t, cx, cy, u, a, spread=1.0):
    """Foule : u = 0 dispersée, u = 1 aspirée au point (cx, cy)."""
    for x, y, s, d, col in CROWD:
        k = ease(min(1.0, max(0.0, (u - d * 0.35) / 0.65)))
        px = lerp(cx + (x - cx) * spread, cx, k)
        py = lerp(cy + (y - cy) * spread, cy, k)
        person(c, px, py + 3 * math.sin(t * 3 + d * 20) * (1 - k), s * (1 - 0.85 * k), col, a * (1 - 0.6 * k))


CUBE_V = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
CUBE_F = [((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)), ((0, 4, 5, 1), (0, -1, 0)), ((2, 3, 7, 6), (0, 1, 0)),
          ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1))]


def draw_cube(c, t, cx, cy, size, a, glow=1.0):
    """Morceau de sucre qui tourne lentement (projection orthographique, faces éclairées)."""
    if a <= 1 or size < 1:
        return
    th, ph = t * 0.6, 0.55

    def rot(p):
        x, y, z = p
        x, z = x * math.cos(th) + z * math.sin(th), -x * math.sin(th) + z * math.cos(th)
        y, z = y * math.cos(ph) - z * math.sin(ph), y * math.sin(ph) + z * math.cos(ph)
        return x, y, z

    vs = [rot(v) for v in CUBE_V]
    c.drawCircle(cx, cy, size * 2.4, P((255, 245, 225), 0.3 * a * glow, blur=size * 0.9))
    faces = []
    for idx, n in CUBE_F:
        nx, ny, nz = rot(n)
        if nz < 0:
            continue
        light = 0.55 + 0.45 * max(0.0, -0.3 * nx - 0.7 * ny + 0.6 * nz)
        faces.append((nz, idx, light))
    for _, idx, light in sorted(faces):
        path = skia.Path()
        for j, i in enumerate(idx):
            x, y, _ = vs[i]
            q = (cx + x * size, cy + y * size)
            path.moveTo(*q) if j == 0 else path.lineTo(*q)
        path.close()
        col = tuple(min(255, v * light) for v in (255, 250, 240))
        c.drawPath(path, P(col, a))
        c.drawPath(path, P((255, 255, 255), a * 0.8, stroke=max(1.5, size * 0.04)))
    r = np.random.default_rng(1)                          # grains de sucre
    for _ in range(12):
        gx, gy = r.uniform(-0.7, 0.7, 2) * size
        c.drawCircle(cx + gx, cy + gy, size * 0.035, P((255, 255, 255), a * 0.7))


# doigts : (base x, base y, longueur, largeur, inclinaison en degrés) ; paume vers nous, doigts légèrement écartés
FINGERS = [(-104, -52, 232, 66, -9), (-34, -72, 262, 68, -2), (36, -66, 246, 64, 5), (102, -40, 186, 56, 13)]
THUMB = (-146, 70, 196, 86, -50)


def _finger_path(bx, by, L, w, ang):
    """Doigt effilé au bout arrondi, orienté vers le haut puis incliné."""
    w1 = w * 0.84
    p = skia.Path()
    p.moveTo(-w / 2, 40)
    p.cubicTo(-w / 2, -L * 0.4, -w1 / 2, -L * 0.7, -w1 / 2, -L + w1 / 2)
    p.arcTo(skia.Rect(-w1 / 2, -L, w1 / 2, -L + w1), 180, 180, False)
    p.cubicTo(w1 / 2, -L * 0.7, w / 2, -L * 0.4, w / 2, 40)
    p.close()
    m = skia.Matrix()
    m.setRotate(ang)
    m.postTranslate(bx, by)
    p.transform(m)
    return p


def _hand_path():
    palm = skia.Path()
    palm.moveTo(-160, -40)
    palm.cubicTo(-125, -88, 125, -88, 160, -30)
    palm.cubicTo(182, 60, 160, 175, 104, 222)
    palm.lineTo(-104, 222)
    palm.cubicTo(-160, 175, -182, 60, -160, -40)
    palm.close()
    wrist = skia.Path()
    wrist.addRRect(skia.RRect.MakeRectXY(skia.Rect(-110, 150, 110, 440), 40, 40))
    out_ = skia.Op(palm, wrist, skia.PathOp.kUnion_PathOp)
    for f in FINGERS + [THUMB]:
        out_ = skia.Op(out_, _finger_path(*f), skia.PathOp.kUnion_PathOp)
    return out_


HAND = _hand_path()
_b = FINGERS[1]
TIP = (_b[0] + (_b[2] - 45) * math.sin(math.radians(_b[4])), _b[1] - (_b[2] - 45) * math.cos(math.radians(_b[4])))


def draw_hand(c, cx, cy, s, a):
    """Main ouverte, paume face à nous : silhouette d'un seul tenant, plis des doigts et lignes de la main."""
    if a <= 1:
        return
    c.save()
    c.translate(cx, cy)
    c.scale(s, s)
    skin_hi, skin, skin_lo, line = (255, 222, 200), (255, 192, 168), (236, 150, 140), (214, 118, 118)
    c.drawPath(HAND, P((255, 170, 150), a * 0.35, blur=40))                  # halo doux
    sh = skia.GradientShader.MakeLinear([skia.Point(0, -360), skia.Point(0, 520)],
                                        [E1.rgb(skin_hi, a), E1.rgb(skin, a), E1.rgb(skin_lo, a)], [0.0, 0.45, 1.0])
    c.drawPath(HAND, P(shader=sh))
    c.save()                                                                  # ombre douce au creux de la paume
    c.clipPath(HAND, doAntiAlias=True)
    c.drawOval(skia.Rect(-110, 0, 110, 200), P(skin_lo, a * 0.35, blur=40))
    c.drawOval(skia.Rect(-120, -60, 20, 60), P((255, 255, 255), a * 0.18, blur=30))
    c.restore()
    c.drawPath(HAND, P(line, a * 0.9, stroke=5))
    for bx, by, L, w, ang in FINGERS + [THUMB]:                               # plis des phalanges
        c.save()
        c.translate(bx, by)
        c.rotate(ang)
        for k, u in enumerate((0.36, 0.66) if (bx, by) != THUMB[:2] else (0.5,)):
            ww = w * (0.5 - 0.08 * u) * 0.8
            y = -L * u
            path = skia.Path()
            path.moveTo(-ww, y)
            path.quadTo(0, y + 7, ww, y)
            c.drawPath(path, P(line, a * 0.55, stroke=4))
        c.restore()
    creases = skia.Path()                                                     # lignes de la main
    creases.moveTo(150, 20)
    creases.cubicTo(80, 10, 0, 40, -80, 0)                                    # ligne de cœur
    creases.moveTo(-138, 60)
    creases.cubicTo(-60, 60, 30, 90, 110, 120)                                # ligne de tête
    creases.moveTo(-120, 70)
    creases.cubicTo(-60, 110, -50, 170, -70, 220)                             # ligne de vie
    c.drawPath(creases, P(line, a * 0.5, stroke=5))
    c.restore()


def draw_skin(c, t, s, a):
    """Gros plan : empreinte digitale."""
    if a <= 1:
        return
    c.save()
    c.translate(540, 1060)
    c.scale(s, s)
    c.drawCircle(0, 0, 430, P((255, 196, 170), a * 0.9))
    for k in range(1, 16):
        r = 26 * k
        path = skia.Path()
        for i in range(0, 181):
            u = math.pi * 2 * i / 180
            rr = r * (1 + 0.04 * math.sin(u * 5 + k))
            q = (rr * math.cos(u) * 0.8, rr * math.sin(u))
            path.moveTo(*q) if i == 0 else path.lineTo(*q)
        c.drawPath(path, P((225, 140, 130), a * 0.8, stroke=6))
    c.restore()


CELLS = [(RNG.uniform(-480, 480), RNG.uniform(-560, 560), RNG.uniform(90, 140), RNG.uniform(0, 6)) for _ in range(26)]


def draw_cells(c, t, s, a):
    if a <= 1:
        return
    c.save()
    c.translate(540, 1060)
    c.scale(s, s)
    for x, y, r, ph in CELLS:
        path = skia.Path()
        for i in range(0, 61):
            u = math.pi * 2 * i / 60
            rr = r * (1 + 0.07 * math.sin(u * 3 + ph + t * 1.5))
            q = (x + rr * math.cos(u), y + rr * math.sin(u))
            path.moveTo(*q) if i == 0 else path.lineTo(*q)
        path.close()
        c.drawPath(path, P(PINK, a * 0.35))
        c.drawPath(path, P(PINK, a * 0.9, stroke=5))
        c.drawCircle(x + r * 0.15, y - r * 0.1, r * 0.3, P(VIOLET, a * 0.9))
    c.restore()


MOLS = [(RNG.uniform(-440, 440), RNG.uniform(-520, 520), RNG.integers(3, 6), RNG.uniform(0, 6)) for _ in range(14)]


def draw_molecules(c, t, s, a):
    if a <= 1:
        return
    c.save()
    c.translate(540, 1060)
    c.scale(s, s)
    for x, y, n, ph in MOLS:
        pts = [(x, y)]
        for k in range(n - 1):
            u = ph + t * 0.8 + k * 2 * math.pi / (n - 1)
            pts.append((x + 70 * math.cos(u), y + 70 * math.sin(u) * 0.8))
        for q in pts[1:]:
            c.drawLine(x, y, *q, P(WHITE, a * 0.6, stroke=8))
        for i, q in enumerate(pts):
            col = CYAN if i == 0 else (GOLD if i % 2 else WHITE)
            c.drawCircle(*q, 34 if i == 0 else 22, P(col, a))
    c.restore()


def draw_atom(c, t, x, y, r, a, nucleus=True):
    for k in range(3):
        c.save()
        c.translate(x, y)
        c.rotate(k * 60 + t * 10)
        c.drawOval(skia.Rect(-r, -r * 0.35, r, r * 0.35), P(CYAN, a * 0.55, stroke=max(1.5, r * 0.035)))
        u = t * 3 + k * 2.1
        c.drawCircle(r * math.cos(u), r * 0.35 * math.sin(u), max(2.5, r * 0.07), P(WHITE, a))
        c.restore()
    if nucleus:
        c.drawCircle(x, y, max(3.0, r * 0.12), P(GOLD, a))
        c.drawCircle(x, y, max(3.0, r * 0.12) * 2.2, P(GOLD, a * 0.35, blur=8))


def draw_atoms(c, t, s, a):
    if a <= 1:
        return
    c.save()
    c.translate(540, 1060)
    c.scale(s, s)
    for i in range(-2, 3):
        for j in range(-3, 4):
            if (i, j) != (0, 0):
                draw_atom(c, t, i * 230 + (j % 2) * 115, j * 200, 95, a * 0.8)
    draw_atom(c, t, 0, 0, 95, a)
    c.restore()


LEVELS = [None, draw_skin, draw_cells, draw_molecules, draw_atoms]
LABELS = [None, "peau", "cellules", "molécules", "atomes"]


def scene_zoom(c, t):
    if t < T_HAND or t > T_ENTER + 1.2:
        return
    end = 1 - ease((t - T_ENTER) / 0.35)
    # la main (niveau 0)
    ha = win(t, T_HAND, T_ZOOM[0] + 0.3, 0.4, 0.4)
    if ha > 0:
        z = ease((t - T_ZOOM[0]) / 0.6)                        # on plonge vers le bout du majeur (l'empreinte)
        hs = 1.05 * pop(t - T_HAND) * (1 + 5 * z)
        tx = lerp(540 + TIP[0] * 1.05, 540, z)                 # le bout du doigt glisse vers le centre de l'écran
        ty = lerp(1160 + TIP[1] * 1.05, 1060, z)
        draw_hand(c, tx - TIP[0] * hs, ty - TIP[1] * hs, hs, 255 * ha)
    for k in range(1, 5):
        t0 = T_ZOOM[k - 1]
        t1 = T_ZOOM[k] if k < 4 else T_ENTER
        if t < t0:
            continue
        u_in = ease((t - t0) / 0.55)
        u_out = ease((t - t1) / 0.5) if k < 4 else 0.0
        s = lerp(0.25, 1.0, u_in) * (1 + 5 * u_out) * (1 + 0.04 * (t - t0))
        a = 255 * u_in * (1 - u_out) * end
        LEVELS[k](c, t, s, a)
        if a > 1:
            text_c(c, LABELS[k], 540, 1520, 44, WHITE, a * win(t, t0 + 0.2, t1, 0.3, 0.2) * 0.8)
    if t >= T_ENTER:                                           # on traverse le nuage : l'atome central grandit
        u = ease((t - T_ENTER) / 0.9)
        draw_atom(c, t, 540, 1060, 95 * (1 + 14 * u), 255 * (1 - u), nucleus=False)


def dashed(color, a, w, on=26, off=18):
    p = P(color, a, stroke=w)
    p.setPathEffect(skia.DashPathEffect.Make([on, off], 0))
    return p


def scene_void(c, t):
    """Noyau-bille au centre d'un stade immense ; puis tout s'éteint : le vide."""
    if t < T_ENTER or t > T_PCT + 3.2:
        return
    dark = win(t, T_ENTER + 0.2, T_TABLE - 0.3, 0.7, 0.6)
    c.drawRect(skia.Rect(0, 0, W, H), P((4, 3, 12), 220 * dark))
    fade = 1 - ease((t - T_PCT) / 0.6)
    a = 255 * fade
    # la bille (le noyau)
    if t >= T_BILLE:
        k = pop(t - T_BILLE)
        rr = lerp(60, 7, ease((t - T_STADE) / 1.4))
        c.drawCircle(540, 1060, rr * 2.4 * k, P(GOLD, a * 0.35, blur=rr))
        c.drawCircle(540, 1060, rr * k, P(GOLD, a))
        text_c(c, "noyau", 540, 1060 - rr - 30 - 20 * (1 - ease((t - T_STADE) / 1.4)), 36, GOLD,
               a * win(t, T_BILLE + 0.3, T_RIEN + 0.6), shadow=False)
    # le stade, qui apparaît pendant que la caméra recule
    if t >= T_STADE:
        u = ease((t - T_STADE) / 1.4)
        sc = lerp(5.0, 1.0, u)
        dim = 1 - 0.75 * ease((t - (T_RIEN + 0.2)) / 0.8)
        aa = a * min(1.0, (t - T_STADE) / 0.3) * dim
        c.save()
        c.translate(540, 1060)
        c.scale(sc, sc)
        c.drawOval(skia.Rect(-470, -640, 470, 640), dashed(WHITE, aa * 0.8, 5))
        c.drawOval(skia.Rect(-400, -560, 400, 560), P(WHITE, aa * 0.5, stroke=3))
        c.drawRoundRect(skia.Rect(-250, -380, 250, 380), 20, 20, P((120, 230, 160), aa * 0.5, stroke=4))
        c.drawLine(-250, 0, 250, 0, P((120, 230, 160), aa * 0.5, stroke=4))
        c.drawCircle(0, 0, 80, P((120, 230, 160), aa * 0.5, stroke=4))
        e = t * 1.3                                          # un électron sur les gradins
        c.drawCircle(440 * math.cos(e), 600 * math.sin(e), 12, P(CYAN, aa))
        c.drawCircle(440 * math.cos(e), 600 * math.sin(e), 26, P(CYAN, aa * 0.4, blur=10))
        c.restore()
        text_c(c, "atome", 540, 380 + 20 * (1 - u), 40, WHITE, aa * win(t, T_STADE + 0.8, T_RIEN + 0.3), shadow=False)
    if t >= T_RIEN + 0.4:                                    # « du vide »
        text_c(c, "vide", 330, 820, 46, WHITE, a * 0.55 * win(t, T_RIEN + 0.4, T_PCT, 0.6, 0.4), shadow=False)
        text_c(c, "vide", 760, 1340, 46, WHITE, a * 0.55 * win(t, T_RIEN + 0.8, T_PCT, 0.6, 0.4), shadow=False)
    # le compteur 99,9999 %
    if t >= T_PCT:
        u = out((t - T_PCT) / 1.4)
        v = 99.9999 * u
        s = f"{v:0.4f}".replace(".", ",") + " %"
        k = win(t, T_PCT, T_TABLE - 0.2, 0.3, 0.4)
        text_c(c, s, 540, 1100, 120, GOLD, 255 * k)
        text_c(c, "de vide", 540, 1200, 52, WHITE, 255 * k * ease((t - T_PCT - 1.3) / 0.4))


TABLE_Y = 1300.0


def scene_table(c, t):
    if t < T_TABLE or t > T_VIDE + 0.6:
        return
    a = 255 * win(t, T_TABLE, T_VIDE, 0.5, 0.5)
    top = TABLE_Y
    c.drawRoundRect(skia.Rect(140, top, 940, top + 60), 16, 16, P((190, 130, 90), a))
    c.drawRoundRect(skia.Rect(140, top, 940, top + 14), 8, 8, P((230, 175, 125), a))
    for x in (200, 850):
        c.drawRect(skia.Rect(x, top + 60, x + 34, top + 300), P((160, 105, 70), a))
    if t >= T_FIELD:                                          # électrons qui se repoussent, dans l'interstice
        k = ease((t - T_FIELD) / 0.5)
        (ox, oy), s, _ = orbe_pose(t)
        gap_top = oy + 140 * s
        for i in range(-3, 4):
            x = 540 + i * 34
            c.drawCircle(x, gap_top + 2, 6, P(CYAN, a * k))
            c.drawCircle(x, top + 2, 6, P(CYAN, a * k))
            for j in range(2):
                ph = (t * 1.6 + j * 0.5 + i * 0.13) % 1.0
                yy = lerp(gap_top + 4, top, 0.5)
                h = (top - gap_top) * 0.5 * ph
                c.drawLine(x - 10, yy - h, x + 10, yy - h, P(CYAN, a * k * (1 - ph) * 0.7, stroke=3))
                c.drawLine(x - 10, yy + h, x + 10, yy + h, P(CYAN, a * k * (1 - ph) * 0.7, stroke=3))
        if t >= S("touch"):
            kk = win(t, S("touch"), T_VIDE, 0.4, 0.4)
            text_c(c, "↕ jamais de contact", 540, top + 140, 40, CYAN, a * kk, shadow=False)


VOID_ATOMS = [(RNG.uniform(160, 920), RNG.uniform(780, 1420)) for _ in range(12)]


def scene_crush(c, t):
    """On enlève le vide : les orbites s'effondrent ; puis la foule se comprime en un sucre."""
    if t < T_VIDE - 0.1 or t > T_STAR + 0.6:
        return None
    a_at = 255 * win(t, T_VIDE - 0.1, T_CROWD + 0.3, 0.3, 0.4)
    for i, (x, y) in enumerate(VOID_ATOMS):
        shrink = ease((t - (T_VIDE + 0.06 * i)) / 0.6)
        crush = ease((t - T_CRUSH) / 0.8)
        px, py = lerp(x, 540, crush), lerp(y, 1080, crush)
        if shrink < 1:
            draw_atom(c, t, px, py, 70 * (1 - shrink), a_at, nucleus=False)
        c.drawCircle(px, py, 8, P(GOLD, a_at))
        c.drawCircle(px, py, 20, P(GOLD, a_at * 0.35, blur=8))
    # la foule, puis le sucre
    if t >= T_CROWD:
        u = (t - T_SQUEEZE[0]) / (T_SQUEEZE[1] - T_SQUEEZE[0])
        a = 255 * ease((t - T_CROWD) / 0.5) * (1 - ease((t - T_CUBE) / 0.3))
        draw_crowd(c, t, 540, 1080, max(0.0, min(1.0, u)), a)
        if t >= S("huit") and t < T_ONTOP + 1.5:
            text_c(c, "8 000 000 000", 540, 700, 72, GOLD, 255 * win(t, S("huit"), T_ONTOP, 0.3, 0.5))
    cube = None
    if t >= T_CUBE:
        k = pop(t - T_CUBE)
        a = 255 * (1 - ease((t - T_STAR) / 0.5))
        (ox, oy), s, sq = orbe_pose(t)
        on = ease((t - T_ONTOP) / 0.6)
        cx = 540
        cy = lerp(1080, oy - 140 * s * sq[1] - 64, on)
        size = 60 * k
        draw_cube(c, t, cx, cy, size, a)
        cube = (cx, cy)
        if t >= T_HEAVY:
            kk = win(t, T_HEAVY, T_STAR, 0.2, 0.4)
            text_c(c, "400 000 000 t", 540, 700, 80, GOLD, a * kk)
            for i in range(3):                               # lignes de poids
                ph = ((t - T_HEAVY) * 1.4 + i / 3) % 1.0
                y0 = cy - 150 + ph * 80
                c.drawLine(cx - 90 + i * 90, y0, cx - 90 + i * 90, y0 + 40, P(WHITE, a * kk * (1 - ph), stroke=5))
    return cube


def scene_star(c, t):
    """Étoile géante → explosion → étoile à neutrons sur une ville ; puis la cuillère et la balance."""
    if t < T_STAR or t > S("souv") + 0.8:
        return
    fin = 1 - ease((t - S("souv")) / 0.7)
    cx, cy = 540.0, 1060.0
    boom = t >= T_BOOM
    if not boom:
        u = ease((t - T_STAR) / (T_BOOM - T_STAR))
        r = lerp(60, 330, u) * (1 + 0.03 * math.sin(t * 9))
        c.drawCircle(cx, cy, r * 1.4, P((255, 110, 70), 90, blur=r * 0.4))
        sh = skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, [E1.rgb((255, 220, 150)), E1.rgb((255, 120, 70)),
                                                                     E1.rgb((200, 50, 60))], [0.0, 0.6, 1.0])
        c.drawCircle(cx, cy, r, P(shader=sh))
        text_c(c, "étoile géante", cx, cy + r + 70, 40, WHITE, 255 * ease((t - T_STAR) / 0.5), shadow=False)
    else:
        a = t - T_BOOM
        if a < 0.5:                                           # effondrement + éclair doux
            u = ease(a / 0.35)
            r = lerp(330, 16, u)
            c.drawRect(skia.Rect(0, 0, W, H), P((255, 240, 220), 150 * (1 - a / 0.5)))
            c.drawCircle(cx, cy, r, P((255, 230, 200)))
        ring = a * 900
        c.drawCircle(cx, cy, ring, P(CYAN, 200 * max(0.0, 1 - a / 1.2) * fin, stroke=10))
        # la ville (plan de rues)
        if t >= T_CITY:
            k = ease((t - T_CITY) / 0.6) * fin * (1 - ease((t - T_SPOON) / 0.5))
            for i in range(-6, 7):
                c.drawLine(cx - 320, cy + i * 52, cx + 320, cy + i * 52, P(CYAN, 110 * k, stroke=3))
                c.drawLine(cx + i * 52, cy - 320, cx + i * 52, cy + 320, P(CYAN, 110 * k, stroke=3))
            rr = np.random.default_rng(4)
            for _ in range(40):
                i, j = rr.integers(-6, 6, 2)
                c.drawRect(skia.Rect(cx + i * 52 + 6, cy + j * 52 + 6, cx + i * 52 + 46, cy + j * 52 + 46),
                           P(VIOLET, 90 * k))
            text_c(c, "≈ 20 km", cx, cy + 400, 44, WHITE, 255 * k, shadow=False)
        sa = fin * (1 - ease((t - T_SCALE) / 0.4))
        rs = 30 + 3 * math.sin(t * 12)
        c.drawCircle(cx, cy, rs * 4, P((200, 230, 255), 120 * sa, blur=40))
        c.drawCircle(cx, cy, rs, P((235, 245, 255), 255 * sa))
        if t >= S("neutron"):
            text_c(c, "étoile à neutrons", cx, cy - 120, 46, WHITE, 255 * sa * win(t, S("neutron"), T_CITY + 0.3))
        if t >= T_SUN:                                        # le Soleil, à côté, pour comparer la masse
            k = win(t, T_SUN, T_CITY + 0.2, 0.4, 0.4) * fin
            c.drawCircle(cx, 690, 80, P((255, 200, 80), 255 * k))
            c.drawCircle(cx, 690, 120, P((255, 200, 80), 80 * k, blur=30))
            text_c(c, "plus lourde que le Soleil", cx, 830, 40, GOLD, 255 * k, shadow=False)
        # la cuillère prélève un peu d'étoile
        if T_SPOON <= t < T_SCALE + 0.4:
            u = ease((t - T_SPOON) / 0.8)
            k = win(t, T_SPOON, T_SCALE, 0.3, 0.3) * fin
            sx, sy = lerp(900, cx + 20, u), lerp(700, cy - 10, u)
            if t > T_SPOON + 1.0:
                sx, sy = lerp(cx + 20, 760, ease((t - T_SPOON - 1.0) / 0.6)), lerp(cy - 10, 800,
                                                                                 ease((t - T_SPOON - 1.0) / 0.6))
            draw_spoon(c, sx, sy, 1.0, 255 * k, full=t > T_SPOON + 0.9)
        if t >= T_SCALE:
            draw_balance(c, t, fin)


def draw_spoon(c, x, y, s, a, full=False):
    c.save()
    c.translate(x, y)
    c.rotate(-30)
    c.scale(s, s)
    c.drawRoundRect(skia.Rect(40, -9, 300, 9), 9, 9, P((210, 215, 230), a))
    c.drawOval(skia.Rect(-60, -38, 60, 38), P((225, 230, 240), a))
    if full:
        c.drawCircle(0, 0, 24, P((235, 245, 255), a))
        c.drawCircle(0, 0, 50, P((200, 230, 255), a * 0.5, blur=14))
    c.restore()


def draw_balance(c, t, fin):
    k = ease((t - T_SCALE) / 0.5) * fin
    a = 255 * k
    tilt = math.radians(16) * out((t - T_SCALE - 0.6) / 0.9)          # la cuillère (à droite) l'emporte
    fx, fy = 540.0, 1000.0
    c.drawPath(_tri(fx, fy), P((200, 200, 220), a))
    L = 330
    lx, ly = fx - L * math.cos(tilt), fy - L * math.sin(tilt)
    rx, ry = fx + L * math.cos(tilt), fy + L * math.sin(tilt)
    c.drawLine(lx, ly, rx, ry, P(WHITE, a, stroke=10))
    for px, py in ((lx, ly), (rx, ry)):
        c.drawLine(px, py, px - 80, py + 160, P(WHITE, a * 0.7, stroke=3))
        c.drawLine(px, py, px + 80, py + 160, P(WHITE, a * 0.7, stroke=3))
        c.drawLine(px - 110, py + 160, px + 110, py + 160, P(WHITE, a, stroke=8))
    # plateau gauche : l'humanité ; plateau droit : une cuillère d'étoile
    for i in range(28):
        col = (VIOLET, CYAN, PINK, GOLD)[i % 4]
        person(c, lx - 90 + (i % 7) * 30, ly + 150 - (i // 7) * 34, 0.85, col, a)
    text_c(c, "l'humanité", lx, ly + 240, 38, WHITE, a, shadow=False)
    draw_spoon(c, rx - 10, ry + 128, 0.45, a, full=True)
    text_c(c, "1 cuillère", rx, ry + 240, 38, WHITE, a, shadow=False)


def _tri(x, y):
    p = skia.Path()
    p.moveTo(x, y)
    p.lineTo(x - 60, y + 320)
    p.lineTo(x + 60, y + 320)
    p.close()
    return p


# ------------------------------------------------------------------------------------------------ l'Orbe
def orbe_target(t):
    if E("main") <= t < T_ZOOM[0]:
        return 540, 560, 0.72
    if T_BILLE <= t < T_PCT:
        return 860, 400, 0.55
    if T_TABLE <= t < T_VIDE:
        s = 0.72
        if t >= T_PUSH:
            return 540, TABLE_Y - 140 * s - 26, s
        return 540, 820, s
    if T_ONTOP - 0.6 <= t < T_STAR:
        return 540, 1260, 0.72
    if T_STAR <= t < S("souv"):
        return 180, 400, 0.55
    if S("souv") <= t < T_LOOP:
        return 540, 1000, 1.1
    return 540, 430, 0.8


_POSE = {}


def _build_pose():
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


def orbe_pose(t):
    """Position, échelle et écrasement (sx, sy) de l'Orbe."""
    if not _POSE:
        _build_pose()
    f = t * FPS
    i = max(0, min(int(f), len(_POSE) - 2))
    u = f - i
    a, b = _POSE[i], _POSE[i + 1]
    x, y, s = (a[j] + (b[j] - a[j]) * u for j in range(3))
    bob = 8 * math.sin(t * 2.1)
    sx = sy = 1.0
    if T_PUSH <= t < T_VIDE:                                  # il pousse vers la table, sans jamais la toucher
        bob = 3 * math.sin(t * 17) * ease((t - T_PUSH) / 0.3)
        sy = 1 - 0.06 * (0.5 + 0.5 * math.sin(t * 8))
    if T_HEAVY <= t < T_STAR:                                 # écrasé par le sucre
        k = pop(t - T_HEAVY, 0.8) * (1 - ease((t - T_STAR) / 0.4))
        sx, sy = 1 + 0.18 * k, 1 - 0.22 * k
        y += 50 * k
        bob *= 0.2
    return (x, y + bob), s, (sx, sy)


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


def gaze_point(g, x, y):
    return {"cube": (540, 1080), "hand": (540, 1100), "zoom": (540, 1060), "marble": (540, 1060),
            "table": (540, TABLE_Y), "center": (540, 1080), "star": (540, 1060), "spoon": (560, 1000),
            "balance": (540, 1150), "self": (x, y + 400), "up": (x, y - 400)}.get(g)


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
            if sym == "…":
                for k in range(3):
                    on = int(a * 5) % 4 > k
                    c.drawCircle(-18 + k * 18, -30, 7, P((60, 40, 110), al if on else al * 0.3))
            else:
                f = skia.Font(E1.FONT, 60)
                w = f.measureText(sym)
                c.drawString(sym, -w / 2, -9, f, P((60, 40, 110), al))
            c.restore()


def draw_orbe_at(c, t):
    (x, y), s, (sx, sy) = orbe_pose(t)
    e, gaze = orbe_state(t)
    tgt = gaze_point(gaze, x, y)
    if tgt is not None:
        d = (tgt[0] - x, tgt[1] - y)
        n = math.hypot(*d) or 1.0
        k = min(1.0, n / 200)
        e.regard = (0.75 * d[0] / n * k, 0.75 * d[1] / n * k)
    elif e.expr == "reflechit":
        e.regard = (0.6 * ease(e.age / 0.3), -0.6 * ease(e.age / 0.3))
    ghost = 1.0
    if T_GHOST[0] <= t < T_LOOP + 0.8:                       # « fait de rien » : il devient presque transparent
        ghost = 1 - 0.75 * ease((t - T_GHOST[0]) / (T_GHOST[1] - T_GHOST[0])) * (1 - ease((t - T_LOOP) / 0.8))
    if ghost < 0.999:
        c.saveLayerAlpha(None, int(255 * ghost))
    c.save()
    c.translate(x, y + 140 * s * (1 - sy))
    c.scale(s * sx, s * sy)
    draw_orbe(c, t, e)
    c.restore()
    if ghost < 0.999:
        c.restore()
        for i in range(8):                                    # quelques atomes visibles à travers lui
            u = t * 0.7 + i * 0.8
            c.drawCircle(x + 90 * s * math.cos(u * 1.3 + i), y + 90 * s * math.sin(u + i * 2), 5,
                         P(GOLD, 255 * (1 - ghost)))
    draw_bubble(c, t, x, y, s)


# ------------------------------------------------------------------------------------------------ image
def scene_hook(c, t):
    """Hook et boucle : la foule aspirée dans un morceau de sucre."""
    if t < S("imp") + 0.6:
        a = 255 * (1 - ease((t - S("imp")) / 0.6))
        u = ease((t - 0.3) / 2.8)
        draw_crowd(c, t, 540, 1080, u, a)
        draw_cube(c, t, 540, 1080, 60 * (0.85 + 0.15 * ease(t / 0.6)), a)
    if t >= T_LOOP:                                           # boucle : on revient exactement à l'image de départ
        a = 255 * ease((t - T_LOOP) / 0.8)
        draw_crowd(c, t, 540, 1080, 0.0, a)
        draw_cube(c, t, 540, 1080, 60 * 0.85, a)
        text_c(c, "Tu te sens plus léger ?", 540, 1690, 60, WHITE, a * ease((t - T_LOOP - 0.3) / 0.4))


def frame(c, t):
    E1.draw_background(c, t)
    scene_hook(c, t)
    scene_zoom(c, t)
    scene_void(c, t)
    scene_table(c, t)
    scene_crush(c, t)
    scene_star(c, t)
    draw_orbe_at(c, t)
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

    add(0.3, E1.swish(2.8, 0.12))
    add(1.2, E1.swell(0.12))
    add(T_HAND, E1.pop_s(400, 0.16))
    for k, tz in enumerate(T_ZOOM):                          # chaque niveau de zoom : un souffle et un « bloop »
        add(tz - 0.1, E1.swish(0.7, 0.12))
        add(tz + 0.35, E1.pop_s(520 + 90 * k, 0.16))
    add(T_ENTER, E1.swish(1.0, 0.16))
    add(T_ENTER + 0.4, E1.swell(0.14))
    add(T_BILLE, E1.ding(784, 0.14))
    add(T_STADE, E1.swish(1.4, 0.12))
    add(T_RIEN + 0.2, E1.swell(0.1))
    for i in range(10):
        add(T_PCT + 0.13 * i, E1.tock(0.05))
    add(T_PCT + 1.4, E1.ding(1046, 0.14))
    add(T_TABLE, E1.tock(0.16))
    add(T_FIELD, E1.sparkle(0.08))
    add(T_VIDE, E1.swish(1.0, 0.16))
    add(T_CRUSH, E1.swell(0.14))
    add(T_SQUEEZE[0], E1.swish(T_SQUEEZE[1] - T_SQUEEZE[0], 0.12))
    add(T_CUBE, E1.pop_s(600, 0.2))
    add(T_CUBE + 0.1, E1.sparkle(0.12))
    add(T_ONTOP + 0.55, E1.tock(0.18))
    add(T_HEAVY, E1.swell(0.24))
    add(T_HEAVY + 0.05, E1.tock(0.22))
    add(T_STAR, E1.swell(0.14))
    add(T_BOOM, E1.swell(0.26))
    add(T_BOOM + 0.1, E1.swish(1.2, 0.18))
    add(T_SUN, E1.ding(660, 0.1))
    add(T_CITY, E1.sparkle(0.1))
    add(T_SPOON + 0.9, E1.pop_s(500, 0.14))
    add(T_SCALE + 0.6, E1.swish(0.9, 0.12))
    add(T_SCALE + 1.4, E1.tock(0.2))
    add(T_GHOST[0], E1.swell(0.1))
    add(T_LOOP, E1.sparkle(0.12))
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
    out_path = sys.argv[1] if len(sys.argv) > 1 else "output/ep03_sucre.mp4"
    render(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
