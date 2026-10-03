"""Épisode 14 — « Pourquoi tu ne peux pas te chatouiller toi-même ? », version Orbe (ton : on parle à un ami).

L'Orbe, immobile en bas, dit le texte (voix Kokoro générée par voix.py, bouche synchronisée) ; au-dessus, les
illustrations. Réutilise les pions, fils, cerveaux et écrans de l'épisode 13.

    python -m films.episodes.ep14_chatouilles.orbe_ep14 output/ep14_orbe.mp4
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import skia

from films import hook as HK
from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep01_triangle.ep01 import CYAN, GOLD, PINK, VIOLET, WHITE, P, ease, lerp, pop, text_c
from films.episodes.ep13_baillement import orbe_ep13 as B
from films.episodes.ep13_baillement.orbe_ep13 import AMBER, DARK, RED, brain, mix, pion, thread, win
from films.episodes.ep14_chatouilles.voix import TEXTE
from films.persos import levres as LV
from films.persos.orbe import Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.wav")

TIMES = [(0.00, 2.10), (2.59, 3.62), (3.99, 6.42), (6.80, 7.60), (7.96, 11.68), (12.17, 13.74), (14.12, 17.59),
         (17.97, 21.01), (21.39, 23.50), (23.88, 26.29), (26.78, 31.67), (32.04, 35.59), (35.97, 37.51),
         (37.89, 42.21), (42.59, 44.50), (44.87, 46.42), (46.90, 47.70), (48.06, 49.60), (49.98, 51.58),
         (51.95, 57.02), (57.52, 58.89), (59.26, 63.26), (63.64, 65.75), (66.25, 69.00), (69.38, 72.59)]
PHRASES = [ph for para in TEXTE for ph in para]
SUBS = [(ph.replace("quatre-vingt-dix", "90").replace("deux dixièmes", "0,2").replace(" ?", " ?")
         .replace(" :", " :"), a, b) for ph, (a, b) in zip(PHRASES, TIMES)]
DUR = TIMES[-1][1] + 1.6
T = 0.0
GREEN = (140, 230, 160)


# ------------------------------------------------------------------------------------------------ dessins
def main_(c, x, y, s, col, a, wiggle=0.0, ang=0.0):
    """Une main ronde (moufle) : paume et quatre doigts qui gigotent quand wiggle > 0."""
    if a <= 1:
        return
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    for k in range(4):
        dx = -27 + 18 * k
        ln = 46 + 8 * (k in (1, 2)) + 14 * wiggle * math.sin(T * 22 + k * 1.7)
        c.drawRoundRect(skia.Rect(dx - 8, -ln, dx + 8, 0), 8, 8, P(col, a))
        c.drawRoundRect(skia.Rect(dx - 8, -ln, dx + 8, 0), 8, 8, P(mix(col, DARK, 0.4), a, stroke=3))
    c.drawRoundRect(skia.Rect(-40, -14, 34, 44), 26, 26, P(col, a))
    c.drawRoundRect(skia.Rect(-40, -14, 34, 44), 26, 26, P(mix(col, DARK, 0.4), a, stroke=3))
    c.drawRoundRect(skia.Rect(26, -4, 52, 14), 9, 9, P(col, a))         # pouce
    c.restore()


def rit(c, x, y, s, col, k, a, angry=False):
    """Pion qui rit (k 0–1) : il tremble, yeux plissés en ^ ^, bouche ouverte, « ha ha » qui s'envolent."""
    if a <= 1:
        return
    sh = 6 * k * math.sin(T * 40)
    pion(c, x + sh, y, s, col, 0.0, a)
    if k <= 0.05:
        return
    c.save()
    c.translate(x + sh, y)
    c.scale(s, s)
    c.drawCircle(0, 0, 56, P(col, a * k))                       # efface le visage neutre
    ink = (28, 18, 50)
    for sd in (-1, 1):
        p = skia.Path()
        p.moveTo(sd * 20 - 10, -4)
        p.lineTo(sd * 20, -14)
        p.lineTo(sd * 20 + 10, -4)
        c.drawPath(p, P(ink, a * k, stroke=4.5))
        if angry:                                               # sourcils froncés
            c.drawLine(sd * 20 - 12, -32 + (6 if sd < 0 else 0), sd * 20 + 12, -32 + (0 if sd < 0 else 6),
                       P(ink, a * k, stroke=5))
    m = skia.Path()
    m.moveTo(-20, 12)
    m.quadTo(0, 48, 20, 12)
    m.close()
    c.drawPath(m, P((70, 20, 50), a * k))
    c.drawPath(m, P(ink, a * k, stroke=3))
    c.restore()
    for j in range(3):
        u = ((T * 0.9) + j / 3) % 1
        text_c(c, "ha", x + s * (70 + 25 * j) * (1 if j % 2 else -1), y - s * (80 + 120 * u), 34 * s + 8, WHITE,
               a * k * (1 - u), shadow=False)


def onde(c, x0, x1, y, amp, col, a, ph=0.0, w=5):
    p = skia.Path()
    for i in range(0, 61):
        u = i / 60
        yy = y - amp * math.sin(u * 4 * math.pi + ph) * math.sin(u * math.pi)
        p.moveTo(lerp(x0, x1, u), yy) if i == 0 else p.lineTo(lerp(x0, x1, u), yy)
    c.drawPath(p, P(col, a * 0.35, blur=6, stroke=w * 2.5))
    c.drawPath(p, P(col, a, stroke=w))


def tete_profil(c, x, y, r, a, cerv=0.0):
    """Tête de profil (tournée vers la droite) avec le cerveau, et le cervelet qui s'allume (cerv 0–1)."""
    c.drawCircle(x, y, r * 1.05, P(VIOLET, a * 0.25, blur=30))
    c.drawCircle(x, y, r, P((70, 50, 120), a * 0.9))
    c.drawCircle(x, y, r, P((200, 180, 255), a, stroke=5))
    c.drawCircle(x + r * 0.97, y + r * 0.1, r * 0.1, P((70, 50, 120), a))      # nez
    c.drawCircle(x + r * 0.45, y - r * 0.05, r * 0.07, P(WHITE, a))            # œil
    brain(c, x - r * 0.08, y - r * 0.28, r * 0.5, PINK, a)
    cx, cy = x - r * 0.45, y + r * 0.2                                          # cervelet
    c.drawCircle(cx, cy, r * 0.24, P(GOLD, a * 0.5 * cerv, blur=r * 0.15))
    c.drawOval(skia.Rect(cx - r * 0.2, cy - r * 0.13, cx + r * 0.2, cy + r * 0.13), P(mix(PINK, GOLD, cerv), a))
    for k in range(4):
        yy = cy - r * 0.09 + k * r * 0.06
        c.drawLine(cx - r * 0.17, yy, cx + r * 0.17, yy, P(mix((150, 60, 110), (150, 100, 20), cerv), a, stroke=3))
    return cx, cy


def robot(c, x, y, s, a, ext=0.0):
    """Bras robotique posé à droite, qui tend vers la gauche une pointe en mousse ; ext fait bouger le bras."""
    c.save()
    c.translate(x, y)
    c.scale(-s, s)
    grey, dk = (170, 180, 205), (90, 100, 130)
    c.drawRoundRect(skia.Rect(-60, 40, 60, 80), 12, 12, P(dk, a))
    j1 = (0, 30)
    a1 = math.radians(-70 + 3 * ext)
    j2 = (j1[0] + 150 * math.cos(a1), j1[1] + 150 * math.sin(a1))
    a2 = math.radians(12 + 5 * ext)
    j3 = (j2[0] + 260 * math.cos(a2), j2[1] + 260 * math.sin(a2))
    for p, q in ((j1, j2), (j2, j3)):
        c.drawLine(*p, *q, P(grey, a, stroke=30))
        c.drawLine(*p, *q, P(dk, a, stroke=4))
    for j in (j1, j2):
        c.drawCircle(*j, 22, P(dk, a))
        c.drawCircle(*j, 10, P(CYAN, a))
    c.drawCircle(*j3, 20, P((255, 220, 120), a))                               # mousse
    c.restore()
    return x - s * j3[0], y + s * j3[1]


def manette(c, x, y, s, a, tilt=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawRoundRect(skia.Rect(-60, 0, 60, 50), 16, 16, P((90, 100, 130), a))
    c.save()
    c.rotate(tilt)
    c.drawLine(0, 0, 0, -70, P((200, 205, 225), a, stroke=10))
    c.drawCircle(0, -74, 18, P(RED, a))
    c.restore()
    c.restore()


def rat(c, x, y, s, a, dos=False, cris=0.0):
    """Rat : sur le dos (pattes en l'air) ou à quatre pattes, avec queue ; cris = ondes ultrasoniques."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    g, pink, ink = (200, 200, 215), (255, 170, 190), (40, 24, 40)
    tail = skia.Path()
    tail.moveTo(-90, 10)
    tail.cubicTo(-150, 40, -170, -40, -220, -10 + 10 * math.sin(T * 4))
    c.drawPath(tail, P(pink, a, stroke=8))
    c.drawOval(skia.Rect(-110, -50, 70, 60), P(g, a))
    if dos:
        for fx in (-70, -30, 10, 40):
            c.drawLine(fx, -40, fx + 6 * math.sin(T * 18 + fx), -80, P(pink, a, stroke=10))
    else:
        for fx in (-70, -20, 20, 50):
            c.drawLine(fx, 50, fx, 70, P(pink, a, stroke=10))
    c.drawCircle(70, -10, 52, P(g, a))
    c.drawCircle(60, -62, 26, P(g, a))
    c.drawCircle(60, -62, 15, P(pink, a))
    c.drawCircle(120, 0, 9, P(pink, a))
    if dos:
        for sd in (-1, 1):
            q = skia.Path()
            q.moveTo(82 + sd * 2 - 9, -20)
            q.lineTo(82 + sd * 2, -28)
            q.lineTo(82 + sd * 2 + 9, -20)
            c.drawPath(q, P(ink, a, stroke=4))
        m = skia.Path()
        m.moveTo(92, 14)
        m.quadTo(104, 36, 118, 14)
        m.close()
        c.drawPath(m, P((90, 20, 40), a))
    else:
        c.drawCircle(88, -22, 7, P(ink, a))
    c.restore()
    if cris > 0:
        for k in range(4):
            r = ((T * 220 + k * 50) % 200) * s
            c.drawArc(skia.Rect(x + 110 * s - r, y - r, x + 110 * s + r, y + r), -50, 100, False,
                      P(CYAN, a * cris * (1 - r / (200 * s)), stroke=5))


def big(c, s, x, y, size, col, a, t0, o):
    k = pop(o - t0)
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(k, k)
    text_c(c, s, 0, 0, size, col, a)
    c.restore()


# ------------------------------------------------------------------------------------------------ scènes
def sc_essai(c, o):
    """Gauche : il se chatouille, rien. Droite : son pote le chatouille, il se tord de rire."""
    a = 255 * win(o, -1, 11.9, 0.3, 0.4)
    if a <= 1:
        return
    L, R = (300, 700), (780, 700)
    pion(c, *L, 1.3, CYAN, 0.0, a)
    main_(c, L[0] + 90, L[1] + 140, 1.15, CYAN, a, wiggle=1.0 if 2.6 <= o < 7.7 else 0.3, ang=-30)
    if o >= 6.8:
        text_c(c, "…", L[0], L[1] - 110, 70, WHITE, a * ease((o - 6.8) / 0.3))
    k = ease((o - 8.6) / 0.3)
    rit(c, *R, 1.3, PINK, k, a)
    main_(c, R[0] - 100, R[1] + 130, 1.15, GOLD, a * ease((o - 7.9) / 0.4), wiggle=1.0, ang=30)
    if o < 2.6 or o >= 7.9:
        text_c(c, "toi", L[0], 1060, 44, CYAN, a * 0.9)
        text_c(c, "ton pote", R[0], 1060, 44, GOLD, a * 0.9 * ease((o - 7.9) / 0.4))


def sc_cervelet(c, o):
    a = 255 * win(o, 12.0, 26.4)
    if a <= 1:
        return
    hx, hy, r = 540, 560, 290
    cerv = ease((o - 14.9) / 0.5)
    cx, cy = tete_profil(c, hx, hy, r, a * pop(o - 12.1), cerv)
    if o >= 15.6:
        text_c(c, "cervelet", cx - 40, cy + 120, 50, GOLD, a * ease((o - 15.6) / 0.3))
    if o >= 17.9:                                               # le signal ressenti et la prédiction
        al = a * ease((o - 17.9) / 0.4)
        damp = 1 - 0.85 * ease((o - 21.6) / 1.0)
        onde(c, 140, 940, 1000, 60 * damp, CYAN, al, ph=T * 6)
        onde(c, 140, 940, 1000, 60, GOLD, al * 0.5 * ease((o - 19.0) / 0.4) * (1 - ease((o - 23.9) / 0.4)),
             ph=T * 6, w=3)
        text_c(c, "ressenti", 220, 920, 38, CYAN, al, shadow=False)
        if o >= 19.0:
            text_c(c, "prévu", 860, 920, 38, GOLD, al * ease((o - 19.0) / 0.3) * (1 - ease((o - 23.9) / 0.4)),
                   shadow=False)


ROBOT_HAND = (720, 720)


def sc_robot(c, o):
    a = 255 * win(o, 26.6, 46.6)
    if a <= 1:
        return
    big(c, "LONDRES · années 90", 540, 250, 56, GOLD, a, 26.9, o)
    stick = math.sin(T * 5) * 18 if 32.0 <= o < 44.6 else 0.0
    delay = ease((o - 38.4) / 0.4)
    laugh = ease((o - 39.6) / 0.4) * (1 - ease((o - 44.9) / 0.5))
    # le câble manette → robot (il se rompt quand le cerveau ne fait plus le lien)
    brk = ease((o - 45.0) / 0.4)
    ca = a * 0.85 * ease((o - 32.0) / 0.4)
    for sd in (-1, 1):
        p = skia.Path()
        x0, x1 = (330, 600) if sd < 0 else (620, 900)
        p.moveTo(x0, 930 + (30 * brk if sd > 0 else 0))
        p.cubicTo(lerp(x0, x1, 0.3), 1010, lerp(x0, x1, 0.7), 1010, x1, 930 + (30 * brk if sd < 0 else 0))
        c.drawPath(p, P(GOLD, ca, stroke=6))
    rit(c, 280, 640, 1.2, CYAN, laugh, a)
    main_(c, 470, 770, 1.0, CYAN, a, ang=90)
    manette(c, 330, 900, 1.0, a * ease((o - 32.0) / 0.4), tilt=stick)
    tip = robot(c, 900, 860, 1.25, a, ext=math.sin((T - 0.2 * delay) * 5) * ease((o - 32.0) / 0.4))
    if o >= 38.4 and o < 42.6:
        big(c, "+ 0,2 s", 540, 470, 70, GOLD, a, 38.6, o)
    if o >= 42.6:                                               # plus le retard est long, plus ça chatouille
        al = a * ease((o - 42.6) / 0.3) * (1 - ease((o - 44.9) / 0.4))
        for i, (lab, hgt) in enumerate((("0", 20), ("0,1", 70), ("0,2", 130), ("0,3", 180))):
            x = 330 + i * 140
            g = ease((o - 42.7 - 0.15 * i) / 0.4)
            c.drawRoundRect(skia.Rect(x - 40, 560 - hgt * g, x + 40, 560), 10, 10, P(GOLD, al))
            text_c(c, lab, x, 605, 34, WHITE, al, shadow=False)
        text_c(c, "retard (s)", 540, 650, 34, WHITE, al * 0.8, shadow=False)


def sc_patients(c, o):
    a = 255 * win(o, 46.7, 57.3)
    if a <= 1:
        return
    big(c, "?!", 540, 330, 120, GOLD, a * (1 - ease((o - 48.4) / 0.4)), 46.9, o)
    laugh = ease((o - 48.4) / 0.4)
    rit(c, 540, 680, 1.15, VIOLET, laugh, a)
    main_(c, 620, 800, 0.9, VIOLET, a * ease((o - 48.0) / 0.3), wiggle=1.0, ang=-30)
    if o >= 50.0:                                               # des voix autour de lui
        for k in range(4):
            ang = -math.pi / 2 + (k - 1.5) * 0.7
            x, y = 540 + 290 * math.cos(ang), 600 + 230 * math.sin(ang)
            s = pop(o - 50.1 - 0.15 * k)
            c.drawRoundRect(skia.Rect(x - 50 * s, y - 32 * s, x + 50 * s, y + 32 * s), 20, 20, P(WHITE, a * 0.85))
            for d in range(3):
                c.drawCircle(x - 22 * s + 22 * d * s, y, 6 * s, P(DARK, a))
    if o >= 52.0:                                               # moi / dehors qui se confondent
        m = ease((o - 52.4) / 2.5)
        al = a * ease((o - 52.0) / 0.4)
        for sd, lab, col in ((-1, "moi", CYAN), (1, "dehors", GOLD)):
            x = 540 + sd * lerp(170, 60, m)
            c.drawCircle(x, 1040, 110, P(col, al * 0.18))
            c.drawCircle(x, 1040, 110, P(col, al, stroke=5))
            text_c(c, lab, 540 + sd * 200, 1040 + 14, 40, col, al * (1 - m * 0.6), shadow=False)


def sc_rats(c, o):
    a = 255 * win(o, 57.3, 66.0)
    if a <= 1:
        return
    if o < 63.5:
        rat(c, 560, 720, 1.4 * pop(o - 57.5), a, dos=True, cris=ease((o - 59.4) / 0.3))
        main_(c, 520, 600, 1.0, GOLD, a * ease((o - 57.8) / 0.3), wiggle=1.0, ang=180)
        if o >= 60.6:
            big(c, "50 kHz", 820, 470, 64, CYAN, a, 60.6, o)
        return
    u = ease((o - 63.6) / 1.8)                                  # il court après la main
    hx = lerp(380, 820, u)
    main_(c, hx + 120, 700, 1.0, GOLD, a, wiggle=0.6, ang=180)
    rat(c, hx - 110, 760, 1.2, a)


def sc_fin(c, o):
    a = 255 * win(o, 66.0, 200)
    if a <= 1:
        return
    big(c, "?", 540, 380, 200, GOLD, a, 66.4, o)
    k = ease((o - 69.5) / 0.4)
    rit(c, 540, 760, 1.25, PINK, k, a, angry=o >= 70.6)
    main_(c, 400, 880, 0.9, GOLD, a * k, wiggle=1.0, ang=30)


SCENES = [sc_essai, sc_cervelet, sc_robot, sc_patients, sc_rats, sc_fin]

# ------------------------------------------------------------------------------------------------ l'Orbe
HOME = (540.0, 1330.0, 0.74)
MOODS = [(0.0, "surpris", "surprise"), (2.6, "parle", None), (8.6, "joie", "joie"), (11.7, "parle", None),
         (14.9, "idee", "idee"), (17.6, "parle", None), (39.6, "joie", "joie"), (42.4, "parle", None),
         (46.9, "surpris", "surprise"), (49.6, "parle", None), (57.5, "joie", "joie"), (59.2, "parle", None),
         (66.2, "reflechit", "reflexion"), (69.3, "parle", None)]
FOCUS = [(0.0, (540, 700)), (12.1, (540, 560)), (17.9, (540, 1000)), (26.7, (540, 650)), (46.8, (540, 680)),
         (57.4, (560, 720)), (66.2, None)]
POINTS = [(8.0, 10.2, (700, 790)), (15.0, 17.4, (410, 620)), (38.6, 40.8, (540, 470)), (42.8, 44.4, (750, 420)),
          (52.4, 54.6, (540, 1040)), (60.6, 62.6, (820, 450))]
SYNC = None


def draw_orbe_at(c, t):
    (yeux, hum), (_, hum0), tc = B.last(MOODS, t)
    x, y, s = HOME
    e = Etat(expr="parle", age=t - tc, levres=SYNC(t), yeux=yeux, humeur=hum or "calme",
             humeur_avant=hum0 or "calme", humeur_mix=(t - tc) / 0.5)
    e.cligne = yeux == "parle" and (t % 3.4) < 0.11
    (fp,), _, _ = B.last([(a_, b_) for a_, b_ in FOCUS], t)
    if fp is None:
        e.regard = (0.0, 0.05)
    else:
        d = (fp[0] - x, fp[1] - y)
        n = math.hypot(*d) or 1.0
        e.regard = (0.7 * d[0] / n, 0.7 * d[1] / n)
    for a_, b_, pt in POINTS:
        if a_ <= t < b_:
            e.cible = ((pt[0] - x) / s, (pt[1] - y) / s)
            e.age = t - a_
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    draw_orbe(c, t, e)
    c.restore()


def frame(c, t):
    global T
    T = t
    B.T = t
    E1.draw_background(c, t)
    c.drawRect(skia.Rect(0, 0, W, H), P((4, 3, 12), 255 * 0.35))
    for sc in SCENES:
        sc(c, t)
    draw_orbe_at(c, t)
    E1.draw_subtitle(c, t)


def fx_events():
    return [(0.0, E1.swell(0.12), 1.0), (8.6, E1.sparkle(0.1), 1.0), (12.2, E1.swish(0.6, 0.1), 1.0),
            (14.9, E1.ding(700, 0.12), 1.0), (26.9, E1.ding(660, 0.12), 1.0), (38.6, E1.pop_s(520, 0.14), 1.0),
            (39.6, E1.sparkle(0.1), 1.0), (45.0, HK.sub_drop(0.25), 1.0), (46.9, E1.swell(0.14), 1.0),
            (57.5, E1.pop_s(560, 0.12), 1.0), (60.6, E1.ding(784, 0.12), 1.0), (66.4, E1.swell(0.14), 1.0),
            (70.6, HK.sub_drop(0.3), 1.0)]


def render(out_path, t_from=0.0, t_to=None):
    global SYNC
    SYNC = LV.Synchro(VOIX)
    E1.TIMING = SUBS
    t_to = DUR if t_to is None else t_to
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(t_from * FPS), int(t_to * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
        if f % 300 == 0:
            print(f"{f / FPS:6.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()
    wav = f"{tmp}/a.wav"
    MI.soundtrack(wav, MI.load_voice(VOIX), DUR, fx_events())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-ss", str(t_from), "-t", str(t_to - t_from), "-i", wav,
                    "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out_path], check=True)
    print("OK", out_path)


if __name__ == "__main__":
    a = sys.argv[2:]
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep14_orbe.mp4",
           float(a[0]) if a else 0.0, float(a[1]) if len(a) > 1 else None)
