"""Épisode 13 — « Pourquoi on bâille quand quelqu'un d'autre bâille ? », version Orbe.

L'Orbe dit le texte (bouche synchronisée sur la voix, films.persos.levres) ; au-dessus de lui, des illustrations
animées. Les petits personnages (« pions ») bâillent, et la contagion circule le long de fils dorés. L'Orbe ne bâille
jamais : il se déplace d'une scène à l'autre, rebondit sur les syllabes accentuées, penche vers ce qu'il regarde et
montre les éléments clés avec son rayon de lumière.

Les scènes sont écrites dans le temps de la voix d'origine (o) ; O(t) ramène le temps de la vidéo à ce temps.

    python -m films.episodes.ep13_baillement.orbe_ep13 output/ep13_orbe.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import hook as HK
from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep01_triangle.ep01 import CYAN, GOLD, PINK, VIOLET, WHITE, P, ease, lerp, pop, text_c
from films.episodes.ep13_baillement.montage import SEG
from films.persos import levres as LV
from films.persos.orbe import Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.mp3")

# ------------------------------------------------------------------------------------------------ temps
GAP_AT, GAP = 2.80, 0.0                   # (aucun silence ajouté)
END_O = 118.75
TAIL = 1.8
DUR = END_O + GAP + TAIL


def N(o):
    return o + GAP if o >= GAP_AT else o


def O(t):
    if t < GAP_AT:
        return t
    return GAP_AT if t < GAP_AT + GAP else t - GAP



T = 0.0                                   # temps vidéo de l'image en cours (mouvements continus)


def win(o, a, b, fi=0.35, fo=0.35):
    return ease((o - a) / fi) * (1 - ease((o - b) / fo))


def yawn_curve(age, dur=1.7):
    """0 → 1 (bouche grande ouverte, tenue) → 0."""
    if age <= 0 or age >= dur:
        return 0.0
    u = age / dur
    return ease(u / 0.35) * (1 - ease((u - 0.72) / 0.28))


def yawn_at(o, *starts, dur=1.7):
    return max([yawn_curve(o - s, dur) for s in starts] + [0.0])


# ------------------------------------------------------------------------------------------------ dessins
DARK = (24, 16, 48)
AMBER = (255, 185, 80)
ICE = (200, 240, 255)
RED = (255, 90, 90)


def mix(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


def pion(c, x, y, s, col, yawn=0.0, a=255, look=0.0, body=True, glasses=False, cold=0.0, glow=0.0, eyes_down=False):
    """Petit personnage : tête ronde, corps en pilule. yawn 0–1 ; cold 0–1 (visage figé, glacé) ; glow : halo doré."""
    if a <= 1 or s <= 0.01:
        return
    col = mix(col, ICE, cold)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if body:
        c.drawRoundRect(skia.Rect(-46, 52, 46, 190), 44, 44, P(mix(col, DARK, 0.45), a))
        c.drawRoundRect(skia.Rect(-46, 52, 46, 190), 44, 44, P(col, a * 0.7, stroke=3))
    hy = -8 * yawn                                              # la tête se renverse un peu
    if glow > 0:
        c.drawCircle(0, hy, 80, P(AMBER, a * 0.45 * glow, blur=26))
    c.drawCircle(0, hy, 62, P(col, a * 0.35, blur=18))
    sh = skia.GradientShader.MakeRadial(skia.Point(-18, hy - 22), 80, [E1.rgb(mix(col, WHITE, 0.45), a),
                                                                    E1.rgb(col, a), E1.rgb(mix(col, DARK, 0.35), a)],
                                        [0.0, 0.55, 1.0])
    c.drawCircle(0, hy, 56, P(shader=sh))
    if glow > 0:
        c.drawCircle(0, hy, 56, P(AMBER, a * glow, stroke=4))
    ink = (28, 18, 50)
    lx = 8 * look
    if yawn > 0.35:                                             # yeux plissés
        for sd in (-1, 1):
            p = skia.Path()
            p.moveTo(lx + sd * 20 - 9, hy - 10)
            p.quadTo(lx + sd * 20, hy - 3, lx + sd * 20 + 9, hy - 10)
            c.drawPath(p, P(ink, a, stroke=4.5))
    elif cold > 0.5:                                            # regard vide : deux traits
        for sd in (-1, 1):
            c.drawLine(lx + sd * 20 - 8, hy - 8, lx + sd * 20 + 8, hy - 8, P(ink, a, stroke=4.5))
    else:
        dy = 4 if eyes_down else 0
        blink = (T * 1.0 + x * 0.013) % 3.9 < 0.1
        for sd in (-1, 1):
            if blink:
                c.drawLine(lx + sd * 20 - 6, hy - 8 + dy, lx + sd * 20 + 6, hy - 8 + dy, P(ink, a, stroke=4))
            else:
                c.drawCircle(lx + sd * 20, hy - 8 + dy, 6.5, P(ink, a))
    my = hy + 24
    if yawn > 0.02:
        w, h = 18 + 10 * yawn, 6 + 34 * yawn
        c.drawOval(skia.Rect(lx - w / 2, my - 4, lx + w / 2, my - 4 + h), P((70, 20, 50), a))
        c.drawOval(skia.Rect(lx - w / 2, my - 4, lx + w / 2, my - 4 + h), P(ink, a, stroke=3))
    elif cold > 0.5:
        c.drawLine(lx - 12, my, lx + 12, my, P(ink, a, stroke=4))
    else:
        p = skia.Path()
        p.moveTo(lx - 10, my - 2)
        p.quadTo(lx, my + 5, lx + 10, my - 2)
        c.drawPath(p, P(ink, a, stroke=4))
    if glasses:
        for sd in (-1, 1):
            c.drawCircle(lx + sd * 20, hy - 8, 14, P(WHITE, a, stroke=3.5))
        c.drawLine(lx - 6, hy - 8, lx + 6, hy - 8, P(WHITE, a, stroke=3))
    if cold > 0:                                                # givre
        for k in range(7):
            ang = -math.pi * (0.15 + 0.7 * k / 6)
            r0 = 56
            c.drawLine(r0 * math.cos(ang), hy + r0 * math.sin(ang), (r0 + 12) * math.cos(ang),
                       hy + (r0 + 12) * math.sin(ang), P(ICE, a * cold, stroke=3))
    c.restore()


def thread(c, p, q, w, a, pulses=(), col=AMBER):
    """Fil doré entre deux têtes ; pulses = positions 0–1 des impulsions (et leur force)."""
    if a <= 1:
        return
    c.drawLine(*p, *q, P(col, a * 0.25, blur=6, stroke=w * 3))
    c.drawLine(*p, *q, P(col, a * 0.8, stroke=w))
    for u, k in pulses:
        if 0 <= u <= 1 and k > 0:
            x, y = lerp(p[0], q[0], u), lerp(p[1], q[1], u)
            c.drawCircle(x, y, 10 + 2 * w, P(col, a * 0.6 * k, blur=10))
            c.drawCircle(x, y, 4 + w * 0.8, P(WHITE, a * k))


def label(c, s, x, y, size=40, col=WHITE, a=255):
    text_c(c, s, x, y, size, col, a)


def year(c, o, s, t0, x=540, y=300, a=255):
    k = pop(o - t0)
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(k, k)
    text_c(c, s, 0, 0, 120, GOLD, a)
    c.restore()


def chimp(c, x, y, s, yawn=0.0, a=255, look=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    fur, face, ink = (120, 84, 70), (226, 186, 156), (40, 22, 30)
    hy = -6 * yawn
    for sd in (-1, 1):
        c.drawCircle(sd * 66, hy - 4, 24, P(fur, a))
        c.drawCircle(sd * 66, hy - 4, 13, P(face, a))
    c.drawCircle(0, hy, 66, P(fur, a * 0.4, blur=16))
    c.drawCircle(0, hy, 62, P(fur, a))
    c.drawOval(skia.Rect(-42, hy - 40, 42, hy + 8), P(face, a))
    c.drawOval(skia.Rect(-38, hy - 2, 38, hy + 50), P(face, a))
    lx = 7 * look
    for sd in (-1, 1):
        if yawn > 0.35:
            c.drawLine(lx + sd * 18 - 8, hy - 18, lx + sd * 18 + 8, hy - 16, P(ink, a, stroke=4))
        else:
            c.drawCircle(lx + sd * 18, hy - 18, 6, P(ink, a))
    c.drawCircle(lx - 6, hy + 8, 3, P(ink, a))
    c.drawCircle(lx + 6, hy + 8, 3, P(ink, a))
    my = hy + 22
    if yawn > 0.02:
        w, h = 30 + 16 * yawn, 4 + 44 * yawn
        r = skia.Rect(lx - w / 2, my, lx + w / 2, my + h)
        c.drawOval(r, P((90, 20, 40), a))
        if yawn > 0.3:                                          # canines
            for sd in (-1, 1):
                tp = skia.Path()
                tp.moveTo(lx + sd * w * 0.32 - 5, my + 4)
                tp.lineTo(lx + sd * w * 0.32 + 5, my + 4)
                tp.lineTo(lx + sd * w * 0.32, my + 4 + 14 * yawn)
                tp.close()
                c.drawPath(tp, P(WHITE, a))
        c.drawOval(r, P(ink, a, stroke=3))
    else:
        c.drawLine(lx - 16, my + 10, lx + 16, my + 10, P(ink, a, stroke=4))
    c.restore()


def dog(c, x, y, s, yawn=0.0, a=255, look=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    fur, dark, ink = (236, 190, 110), (180, 120, 60), (40, 24, 20)
    hy = -6 * yawn
    for sd in (-1, 1):                                          # oreilles tombantes
        e = skia.Path()
        e.addOval(skia.Rect(sd * 52 - 20, hy - 40, sd * 52 + 20, hy + 40))
        c.save()
        c.rotate(sd * -14)
        c.drawPath(e, P(dark, a))
        c.restore()
    c.drawCircle(0, hy, 64, P(fur, a * 0.4, blur=16))
    c.drawCircle(0, hy, 58, P(fur, a))
    lx = 7 * look
    for sd in (-1, 1):
        if yawn > 0.35:
            c.drawLine(lx + sd * 22 - 8, hy - 16, lx + sd * 22 + 8, hy - 14, P(ink, a, stroke=4))
        else:
            c.drawCircle(lx + sd * 22, hy - 16, 7, P(ink, a))
    c.drawOval(skia.Rect(lx - 32, hy + 2, lx + 32, hy + 46), P((250, 225, 180), a))
    c.drawOval(skia.Rect(lx - 11, hy + 6, lx + 11, hy + 20), P(ink, a))
    my = hy + 34
    if yawn > 0.02:
        w, h = 26 + 14 * yawn, 4 + 50 * yawn
        r = skia.Rect(lx - w / 2, my, lx + w / 2, my + h)
        c.drawOval(r, P((90, 20, 40), a))
        if yawn > 0.3:                                          # langue qui s'enroule
            c.drawOval(skia.Rect(lx - w * 0.3, my + h * 0.45, lx + w * 0.3, my + h * 0.95), P((255, 120, 150), a))
        c.drawOval(r, P(ink, a, stroke=3))
    c.restore()


def mouse(c, x, y, s, yawn=0.0, a=255):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    g, ink = (190, 190, 210), (40, 24, 40)
    for sd in (-1, 1):
        c.drawCircle(sd * 46, -44, 32, P(g, a))
        c.drawCircle(sd * 46, -44, 18, P((255, 170, 190), a))
    c.drawCircle(0, 0, 54, P(g, a))
    for sd in (-1, 1):
        if yawn > 0.35:
            c.drawLine(sd * 18 - 7, -10, sd * 18 + 7, -8, P(ink, a, stroke=4))
        else:
            c.drawCircle(sd * 18, -10, 6, P(ink, a))
    c.drawCircle(0, 10, 6, P((255, 140, 170), a))
    if yawn > 0.02:
        c.drawOval(skia.Rect(-10 - 4 * yawn, 20, 10 + 4 * yawn, 22 + 26 * yawn), P((90, 20, 40), a))
    c.restore()


def cat(c, x, y, s, yawn=0.0, a=255):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    f, ink = (150, 150, 175), (30, 20, 40)
    for sd in (-1, 1):
        e = skia.Path()
        e.moveTo(sd * 22, -50)
        e.lineTo(sd * 56, -82)
        e.lineTo(sd * 58, -26)
        e.close()
        c.drawPath(e, P(f, a))
    c.drawCircle(0, 0, 58, P(f, a))
    for sd in (-1, 1):
        if yawn > 0.35:
            c.drawLine(sd * 22 - 9, -12, sd * 22 + 9, -10, P(ink, a, stroke=4))
        else:
            c.drawOval(skia.Rect(sd * 22 - 8, -24, sd * 22 + 8, 0), P((190, 255, 160), a))
            c.drawOval(skia.Rect(sd * 22 - 2.5, -22, sd * 22 + 2.5, -2), P(ink, a))
        for k in (-1, 1):
            c.drawLine(sd * 30, 18 + 6 * k, sd * 70, 12 + 14 * k, P(WHITE, a * 0.6, stroke=2))
    tri = skia.Path()
    tri.moveTo(-7, 8)
    tri.lineTo(7, 8)
    tri.lineTo(0, 16)
    tri.close()
    c.drawPath(tri, P((255, 150, 170), a))
    if yawn > 0.02:
        r = skia.Rect(-12 - 6 * yawn, 20, 12 + 6 * yawn, 22 + 40 * yawn)
        c.drawOval(r, P((90, 20, 40), a))
        c.drawOval(r, P(ink, a, stroke=3))
    c.restore()


def brain(c, x, y, r, col, a=255):
    """Cerveau stylisé : deux hémisphères bosselés et quelques circonvolutions."""
    c.drawCircle(x, y, r * 1.2, P(col, a * 0.3, blur=r * 0.35))
    path = skia.Path()
    n = 26
    for i in range(n + 1):
        ang = 2 * math.pi * i / n
        rr = r * (1 + 0.07 * math.sin(ang * 9))
        px, py = x + rr * 1.15 * math.cos(ang), y + rr * 0.82 * math.sin(ang)
        path.moveTo(px, py) if i == 0 else path.lineTo(px, py)
    path.close()
    c.drawPath(path, P(mix(col, DARK, 0.25), a))
    c.drawPath(path, P(mix(col, WHITE, 0.3), a, stroke=max(2.0, r * 0.04)))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.drawLine(x, y - r, x, y + r, P(DARK, a * 0.6, stroke=max(2.0, r * 0.05)))
    for k in range(6):
        sx = x + (-0.8 + 0.32 * k) * r
        p = skia.Path()
        p.moveTo(sx, y - r * 0.7)
        p.cubicTo(sx + r * 0.25, y - r * 0.3, sx - r * 0.25, y + r * 0.1, sx + r * 0.1, y + r * 0.6)
        c.drawPath(p, P(mix(col, WHITE, 0.4), a * 0.7, stroke=max(1.5, r * 0.035)))
    c.restore()


def screen(c, x, y, w, h, a, content):
    r = skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    c.drawRoundRect(r, 18, 18, P((10, 10, 24), a))
    c.save()
    c.clipRect(r)
    content()
    c.restore()
    c.drawRoundRect(r, 18, 18, P(CYAN, a * 0.35, blur=10, stroke=10))
    c.drawRoundRect(r, 18, 18, P((200, 220, 255), a, stroke=5))
    c.drawRect(skia.Rect(x - 30, y + h / 2, x + 30, y + h / 2 + 30), P((120, 130, 170), a))


def clock(c, x, y, r, ang, a, col=WHITE):
    c.drawCircle(x, y, r, P(col, a * 0.25, blur=14))
    c.drawCircle(x, y, r, P(DARK, a))
    c.drawCircle(x, y, r, P(col, a, stroke=6))
    for k in range(12):
        q = k * math.pi / 6
        c.drawLine(x + 0.8 * r * math.cos(q), y + 0.8 * r * math.sin(q), x + 0.9 * r * math.cos(q),
                   y + 0.9 * r * math.sin(q), P(col, a, stroke=4))
    c.drawLine(x, y, x + 0.75 * r * math.sin(ang), y - 0.75 * r * math.cos(ang), P(GOLD, a, stroke=6))
    c.drawLine(x, y, x + 0.45 * r * math.sin(ang / 12), y - 0.45 * r * math.cos(ang / 12), P(col, a, stroke=7))
    c.drawCircle(x, y, 8, P(GOLD, a))


def arrow(c, x0, y0, x1, y1, col, a, w=6):
    c.drawLine(x0, y0, x1, y1, P(col, a, stroke=w))
    ang = math.atan2(y1 - y0, x1 - x0)
    for sd in (-1, 1):
        c.drawLine(x1, y1, x1 - 26 * math.cos(ang + sd * 0.5), y1 - 26 * math.sin(ang + sd * 0.5), P(col, a, stroke=w))


# ------------------------------------------------------------------------------------------------ scènes (temps o)
def sc_hook(c, o):
    """Deux pions face à face : le bâillement saute de l'un à l'autre, puis « voir » et « entendre »."""
    a = 255 * win(o, -1, 6.3, 0.3, 0.4)
    if a <= 1:
        return
    L, R = (330, 720), (750, 720)
    yl = yawn_at(o, 0.0, dur=1.8)
    yr = yawn_at(o, 1.15, dur=1.9)
    u = (o - 0.7) / 0.6
    thread(c, (L[0] + 60, L[1]), (R[0] - 60, R[1]), 3, a * win(o, 0.5, 2.6, 0.3, 0.4), [(u, 1.0)])
    pion(c, *L, 1.15, PINK, yl, a, look=1, glow=ease((o - 0.1) / 0.3) * (1 - ease((o - 2.4) / 0.5)))
    pion(c, *R, 1.15, CYAN, yr, a, look=-1, glow=ease((o - 1.2) / 0.3) * (1 - ease((o - 3.2) / 0.5)))
    if o >= 3.25:                                               # voir : un œil
        k = pop(o - 3.3) * (1 - ease((o - 5.2) / 0.3))
        if k > 0:
            c.save()
            c.translate(540, 420)
            c.scale(k, k)
            eye = skia.Path()
            eye.moveTo(-80, 0)
            eye.quadTo(0, -62, 80, 0)
            eye.quadTo(0, 62, -80, 0)
            c.drawPath(eye, P(WHITE, a * 0.3, blur=10, stroke=12))
            c.drawPath(eye, P(WHITE, a, stroke=6))
            c.drawCircle(0, 0, 24, P(CYAN, a))
            c.drawCircle(0, 0, 10, P(DARK, a))
            c.restore()
    if o >= 5.4:                                                # entendre : des ondes sonores
        for k in range(4):
            r = ((o - 5.4) * 160 + k * 45) % 180
            al = a * (1 - r / 180) * ease((o - 5.4) / 0.2)
            c.drawArc(skia.Rect(L[0] + 40 - r, L[1] - 40 - r, L[0] + 40 + r, L[1] - 40 + r), -40, 80, False,
                      P(AMBER, al, stroke=6))


ROW = [(110 + 95.5 * i) for i in range(10)]
ROW_COLS = [PINK, CYAN, VIOLET, GOLD, (140, 230, 160), (255, 150, 90), CYAN, PINK, VIOLET, (140, 230, 160)]
ROW_YAWN = {0: 6.9, 3: 7.9, 4: 8.8, 6: 9.6, 8: 10.3}


def sc_moitie(c, o):
    a = 255 * win(o, 6.45, 11.45)
    if a <= 1:
        return
    clock(c, 540, 400, 110, 2 * math.pi * 3 * ease((o - 8.6) / 2.6), a)
    for i, x in enumerate(ROW):
        st = ROW_YAWN.get(i)
        y = yawn_at(o, st, dur=1.5) if st else 0.0
        g = ease((o - st) / 0.3) if st else 0.0
        pion(c, x, 760, 0.55 * pop(o - 6.5 - 0.04 * i), ROW_COLS[i], y, a, glow=g)
    if o >= 7.0:
        k = pop(o - 7.0)
        c.save()
        c.translate(540, 1030)
        c.scale(k, k)
        text_c(c, "1 adulte sur 2", 0, 0, 62, GOLD, a)
        c.restore()


def sc_provine(c, o):
    a = 255 * win(o, 11.55, 17.2)
    if a <= 1:
        return
    year(c, o, "1986", 11.75, a=a)
    pion(c, 380, 700, 1.0 * pop(o - 11.8), (230, 230, 245), 0.0, a, look=1, glasses=True)
    c.drawRoundRect(skia.Rect(430, 790, 520, 900), 8, 8, P((150, 110, 70), a))     # porte-bloc
    c.drawRect(skia.Rect(442, 805, 508, 890), P(WHITE, a))
    for k in range(int(min(5, max(0, (o - 14) * 2)))):
        c.drawLine(452 + 9 * k, 820, 452 + 9 * k, 850, P(DARK, a, stroke=3))     # bâtons de comptage
    if o >= 12.4:
        sw = pop(o - 12.4)
        c.save()
        c.translate(760, 640)
        c.scale(sw, sw)
        c.drawRect(skia.Rect(-14, -142, 14, -118), P(WHITE, a))
        clock(c, 0, 0, 110, 2 * math.pi * (o - 12.4) / 2, a, col=(220, 230, 255))
        c.restore()
    if o >= 13.5:
        text_c(c, "Robert Provine", 380, 1040, 52, WHITE, a * ease((o - 13.5) / 0.4))


def sheet(c, x, y, a, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.drawRoundRect(skia.Rect(-80, -100, 80, 100), 10, 10, P(WHITE, a))
    for k in range(9):
        c.drawLine(-58, -74 + 18 * k, 58 - (30 if k % 3 == 2 else 0), -74 + 18 * k, P((150, 150, 175), a, stroke=5))
    c.restore()


def sc_lecture(c, o):
    a = 255 * win(o, 17.3, 23.95)
    if a <= 1:
        return
    y = yawn_at(o, 21.4, dur=1.9)
    idea = ease((o - 22.4) / 0.5)
    pion(c, 540, 640, 1.25 * pop(o - 17.35), VIOLET, y, a, eyes_down=o < 21.3, glow=idea)
    sheet(c, 540, 930, a, rot=-4 + 2 * math.sin(T * 1.3))
    if o >= 22.3:                                               # l'idée monte de la feuille à la tête
        for k in range(5):
            u = ((o - 22.3) * 0.9 + k / 5) % 1
            c.drawCircle(540 + 30 * math.sin(u * 7 + k), lerp(830, 650, u), 9, P(AMBER, a * (1 - u)))


# le réseau : centre, famille, amis, inconnus
CEN = (540.0, 690.0)
RINGS = [("famille", 175, [-30, 90, 210], PINK, 7, 27.14),
         ("amis", 305, [-54, 18, 90, 162, 234], CYAN, 4, 30.27),
         ("inconnus", 435, [-67.5 + 45 * k for k in range(8)], (160, 160, 185), 1.5, 31.6)]
YAWNERS = {0: [0, 1, 2], 1: [0, 2, 3], 2: [5]}


def ring_pos(r, deg):
    return CEN[0] + r * math.cos(math.radians(deg)), CEN[1] + r * math.sin(math.radians(deg))


def sc_reseau(c, o):
    a = 255 * win(o, 24.0, 36.45)
    if a <= 1:
        return
    for ri, (name, r, angs, col, w, t0) in enumerate(RINGS):
        on = ease((o - t0) / 0.5)
        appear = pop(o - 24.2 - 0.25 * ri)
        for j, d in enumerate(angs):
            p = ring_pos(r, d)
            # impulsions : rapides et fortes sur les liens épais, faibles et mourantes sur les liens fins
            pulses = []
            for start in (t0 + 0.2, 33.4, 34.8):
                u = (o - start) * (2.2 if ri == 0 else 1.4 if ri == 1 else 0.8)
                k = 1.0 if ri < 2 else max(0.0, 1 - u * 1.6)
                pulses.append((u, k))
            thread(c, CEN, p, w * (0.4 + 0.6 * on), a * (0.25 + 0.75 * on) * min(1, appear), pulses, col=AMBER)
        for j, d in enumerate(angs):
            p = ring_pos(r, d)
            yw = yawn_at(o, t0 + 0.6 + 0.25 * j, 34.0 + 0.3 * ri, dur=1.5) if j in YAWNERS[ri] else 0.0
            pion(c, p[0], p[1] - 20, 0.42 * appear, col, yw, a, body=False, glow=0.8 * yw)
        if o >= t0:
            text_c(c, name, CEN[0], CEN[1] - r + 14, 40, col if ri < 2 else WHITE, a * ease((o - t0) / 0.3))
    pion(c, CEN[0], CEN[1] - 20, 0.5 * pop(o - 24.1), GOLD, yawn_at(o, 27.2, 30.3, 31.7, 33.4, dur=1.2), a,
         body=False, glow=1.0)


def sc_foetus(c, o):
    a = 255 * win(o, 36.6, 40.05)
    if a <= 1:
        return
    fan = skia.Path()
    ax, ay = 540, 230
    fan.moveTo(ax, ay)
    fan.arcTo(skia.Rect(ax - 820, ay - 820, ax + 820, ay + 820), 55, 70, False)
    fan.close()
    c.save()
    c.clipPath(fan, doAntiAlias=True)
    c.drawRect(skia.Rect(0, 0, W, H), P((30, 40, 62), a))
    rng = np.random.default_rng(int(o * 12))
    for _ in range(260):
        x, y = rng.uniform(100, 980), rng.uniform(230, 1060)
        c.drawCircle(x, y, rng.uniform(1, 3), P((150, 170, 210), a * rng.uniform(0.1, 0.5)))
    c.drawOval(skia.Rect(250, 470, 830, 990), P((10, 14, 28), a))       # poche amniotique
    c.restore()
    c.drawPath(fan, P((160, 190, 230), a * 0.6, stroke=3))
    # le fœtus (profil, tourné vers la gauche) : grosse tête, corps recroquevillé
    fc, line = (225, 232, 250), (120, 135, 175)
    y = yawn_at(o, 37.5, dur=2.0)
    body = skia.Path()
    body.addOval(skia.Rect(470, 680, 700, 930))
    c.drawPath(body, P(fc, a))
    c.drawPath(body, P(line, a, stroke=4))
    c.drawOval(skia.Rect(590, 880, 690, 935), P(fc, a))                # jambe repliée
    c.drawOval(skia.Rect(590, 880, 690, 935), P(line, a, stroke=4))
    c.drawCircle(460, 650, 130, P(fc, a * 0.3, blur=24))
    c.drawCircle(460, 650, 122, P(fc, a))
    c.drawCircle(460, 650, 122, P(line, a, stroke=4))
    c.drawCircle(350, 655, 16, P(fc, a))                               # nez
    c.drawOval(skia.Rect(470, 760, 530, 800), P(fc, a))                # bras et main
    c.drawOval(skia.Rect(470, 760, 530, 800), P(line, a, stroke=4))
    p = skia.Path()                                                    # œil fermé
    p.moveTo(375, 615)
    p.quadTo(392, 628, 410, 615)
    c.drawPath(p, P(line, a, stroke=5))
    c.drawArc(skia.Rect(470, 615, 520, 670), -80, 200, False, P(line, a, stroke=4))   # oreille
    w, h = 26 + 14 * y, 5 + 46 * y
    c.drawOval(skia.Rect(372 - w / 2, 690, 372 + w / 2, 690 + h), P((70, 60, 100), a))
    cord = skia.Path()
    cord.moveTo(560, 860)
    cord.cubicTo(620, 960, 700, 900, 760, 1000)
    c.drawPath(cord, P((190, 205, 240), a, stroke=11))
    if o >= 37.2:
        k = pop(o - 37.2)
        c.save()
        c.translate(540, 1150)
        c.scale(k, k)
        text_c(c, "11 semaines", 0, 0, 64, GOLD, a)
        c.restore()


def sc_enfant(c, o):
    a = 255 * win(o, 40.0, 48.2)
    if a <= 1:
        return
    grow = ease((o - 42.0) / 1.6)
    adult = yawn_at(o, 40.5, 44.6, dur=1.7)
    kid = yawn_at(o, 45.2, dur=1.8)
    pion(c, 720, 640, 1.0, CYAN, adult, a, look=-1)
    pion(c, 360, 760 - 90 * grow, lerp(0.55, 0.8, grow) * pop(o - 40.05), PINK, kid, a, look=1,
         glow=ease((o - 45.2) / 0.3))
    if 41.0 <= o < 42.6:                                        # aucune réaction
        k = pop(o - 41.0) * (1 - ease((o - 42.3) / 0.3))
        text_c(c, "✕", 250, 640, 90 * k, (170, 170, 190), a)
    # frise des âges
    al = a * ease((o - 41.6) / 0.4)
    x0, x1, yy = 160, 920, 1080
    c.drawLine(x0, yy, x1, yy, P(WHITE, al * 0.8, stroke=4))
    for k in range(7):
        x = lerp(x0, x1, k / 6)
        c.drawLine(x, yy - 12, x, yy + 12, P(WHITE, al, stroke=4))
        text_c(c, str(k), x, yy + 56, 34, WHITE, al * 0.8, shadow=False)
    mx = lerp(x0, lerp(x0, x1, 4.5 / 6), ease((o - 42.0) / 1.6))
    c.drawCircle(mx, yy, 16, P(GOLD, al))
    if o >= 43.2:
        text_c(c, "4–5 ans", mx, yy - 34, 46, GOLD, a * ease((o - 43.2) / 0.3))
    if o >= 45.6:                                               # les émotions des autres
        for k, (col, kind) in enumerate([(GOLD, "joie"), (CYAN, "triste"), (PINK, "surpris")]):
            ang = -math.pi / 2 + (k - 1) * 0.9 + 0.15 * math.sin(T * 1.5 + k)
            x, y = 360 + 170 * math.cos(ang), 600 + 150 * math.sin(ang)
            s = 28 * pop(o - 45.6 - 0.15 * k)
            c.drawCircle(x, y, s, P(col, a))
            c.drawCircle(x - s * 0.35, y - s * 0.2, s * 0.12, P(DARK, a))
            c.drawCircle(x + s * 0.35, y - s * 0.2, s * 0.12, P(DARK, a))
            p = skia.Path()
            if kind == "joie":
                p.moveTo(x - s * 0.4, y + s * 0.2)
                p.quadTo(x, y + s * 0.65, x + s * 0.4, y + s * 0.2)
                c.drawPath(p, P(DARK, a, stroke=s * 0.12))
            elif kind == "triste":
                p.moveTo(x - s * 0.4, y + s * 0.5)
                p.quadTo(x, y + s * 0.1, x + s * 0.4, y + s * 0.5)
                c.drawPath(p, P(DARK, a, stroke=s * 0.12))
            else:
                c.drawCircle(x, y + s * 0.35, s * 0.18, P(DARK, a))


def sc_especes(c, o):
    a = 255 * win(o, 48.2, 54.25)
    if a <= 1:
        return
    if o < 50.9:                                                # humain → chimpanzé → chien
        b = a * (1 - ease((o - 50.5) / 0.4))
        xs = [230, 540, 850]
        for i in range(2):
            u = (o - 48.7 - 0.7 * i) / 0.6
            thread(c, (xs[i] + 80, 650), (xs[i + 1] - 80, 650), 4, b * ease((o - 48.5) / 0.3), [(u, 1.0)])
        pion(c, xs[0], 650, 0.8 * pop(o - 48.3), PINK, yawn_at(o, 48.4, dur=1.3), b, body=False,
             glow=ease((o - 48.4) / 0.3))
        chimp(c, xs[1], 650, 0.85 * pop(o - 48.5), yawn_at(o, 49.2, dur=1.3), b)
        dog(c, xs[2], 650, 0.85 * pop(o - 48.7), yawn_at(o, 49.9, dur=1.3), b)
        return
    b = a * ease((o - 50.7) / 0.3)

    def tv():
        chimp(c, 740, 560, 0.95, yawn_at(o, 51.0, 52.9, dur=1.7), 255)
    screen(c, 740, 540, 420, 320, b, tv)
    chimp(c, 330, 820, 1.25, yawn_at(o, 52.2, dur=1.9), b, look=1)


def sc_chiens(c, o):
    a = 255 * win(o, 54.3, 61.0)
    if a <= 1:
        return
    year(c, o, "2008", 54.5, a=a * (1 - ease((o - 57.6) / 0.3)))
    pion(c, 320, 690, 1.05 * pop(o - 54.4), (230, 230, 245), yawn_at(o, 55.4, dur=1.9), a, look=1)
    dog(c, 760, 800, 1.3 * pop(o - 54.6), yawn_at(o, 57.0, dur=2.0), a, look=-1)
    if o >= 57.8:                                               # 21 chiens sur 29
        for i in range(29):
            x, y = 220 + (i % 10) * 71, 230 + (i // 10) * 70
            lit = i < 21 and o >= 58.0 + 0.07 * i
            k = pop(o - 57.8 - 0.02 * i)
            c.drawCircle(x, y, 22 * k, P(GOLD if lit else (90, 90, 120), a))
            if lit:
                c.drawCircle(x, y, 30 * k, P(GOLD, a * 0.4, blur=8))
        if o >= 59.3:
            k = pop(o - 59.3)
            c.save()
            c.translate(540, 1080)
            c.scale(k, k)
            text_c(c, "21 chiens sur 29", 0, 0, 62, GOLD, a)
            c.restore()


def faces_grid(c, o, x, y, w, h, a):
    for i in range(6):
        fx = x - w / 2 + (i % 3 + 0.5) * w / 3
        fy = y - h / 2 + (i // 3 + 0.5) * h / 2
        pion(c, fx, fy, 0.75, [PINK, CYAN, GOLD, VIOLET, (140, 230, 160), (255, 150, 90)][i],
             yawn_curve((o * 0.8 + i * 0.37) % 2.2, 1.8), a, body=False)


def sc_baylor(c, o):
    a = 255 * win(o, 61.0, 76.0)
    if a <= 1:
        return
    if o < 67.4:
        b = a * (1 - ease((o - 67.0) / 0.4))
        year(c, o, "2015", 61.3, a=b)
        if o >= 62.4:
            text_c(c, "université Baylor", 540, 400, 50, WHITE, b * ease((o - 62.4) / 0.4))
        for i in range(135):                                    # 135 étudiants
            x, y = 155 + (i % 15) * 55, 500 + (i // 15) * 55
            k = pop(o - 63.0 - 0.012 * i)
            m = ease((o - 64.5 - 0.012 * i) / 0.3)
            c.drawCircle(x, y, 17 * k, P(mix((110, 110, 150), CYAN, m), b))
        if o >= 66.0:
            text_c(c, "135 étudiants", 540, 1060, 58, GOLD, b * ease((o - 66.0) / 0.3))
        return
    b = a * ease((o - 67.1) / 0.3)
    screen(c, 540, 420, 600, 330, b, lambda: faces_grid(c, o, 540, 420, 600, 330, 255))
    cold = ease((o - 69.4) / 0.8)
    xs = [250, 540, 830]
    for i, x in enumerate(xs):
        if i == 1:
            pion(c, x, 820, 0.95, VIOLET, 0.0, b, cold=cold)
        else:
            pion(c, x, 820, 0.95, [PINK, None, CYAN][i], yawn_at(o, 68.6 + 0.4 * i, 70.6 + 0.5 * i, 73.8 + 0.3 * i,
                                                                dur=1.6), b, glow=0.6)
    if o >= 72.3:
        text_c(c, "psychopathie", 540, 1110, 50, ICE, b * ease((o - 72.3) / 0.3))


def sc_question(c, o):
    a = 255 * win(o, 76.0, 79.2)
    if a <= 1:
        return
    k = pop(o - 77.5)
    c.save()
    c.translate(540, 560)
    c.scale(k, k)
    c.drawCircle(0, -60, 150, P(GOLD, a * 0.25, blur=60))
    text_c(c, "?", 0, 40, 300, GOLD, a)
    c.restore()


def o2(c, x, y, a, s=1.0):
    c.drawCircle(x - 14 * s, y, 18 * s, P(RED, a))
    c.drawCircle(x + 14 * s, y, 18 * s, P(RED, a))
    text_c(c, "O₂", x, y + 11 * s, 28 * s, WHITE, a, shadow=False)


def sc_oxygene(c, o):
    a = 255 * win(o, 79.2, 89.85)
    if a <= 1:
        return
    if o < 83.2:                                                # la vieille idée : l'oxygène monte au cerveau
        b = a * (1 - ease((o - 82.8) / 0.4))
        brain(c, 540, 470, 150 * pop(o - 79.3), PINK, b)
        for k in range(7):
            u = ((o - 79.6) * 0.45 + k / 7) % 1
            o2(c, 540 + 160 * math.sin(k * 2.1 + u * 3), lerp(1080, 560, u), b * min(1, u * 5) * (1 - u), 1.8)
        return
    b = a * ease((o - 83.1) / 0.3)
    year(c, o, "1987", 83.1, y=280, a=b)
    pion(c, 400, 640, 1.15, VIOLET, yawn_at(o, 86.6, dur=2.0), b, look=1)
    c.drawOval(skia.Rect(400 - 50, 640 - 2, 400 + 50, 640 + 70), P((200, 240, 255), b * 0.35))   # masque
    c.drawOval(skia.Rect(400 - 50, 640 - 2, 400 + 50, 640 + 70), P(WHITE, b * 0.9, stroke=4))
    tube = skia.Path()
    tube.moveTo(450, 680)
    tube.cubicTo(560, 760, 620, 640, 720, 600)
    c.drawPath(tube, P((200, 230, 255), b * 0.8, stroke=8))
    c.drawRoundRect(skia.Rect(690, 560, 820, 900), 60, 60, P((70, 170, 110), b))   # bouteille
    c.drawRoundRect(skia.Rect(730, 520, 780, 570), 10, 10, P((180, 180, 200), b))
    o2(c, 755, 760, b, 1.2)
    for k in range(3):                                          # l'oxygène circule dans le tube
        u = ((o - 83.6) * 0.8 + k / 3) % 1
        c.drawCircle(lerp(720, 450, u), 640 + 60 * math.sin(u * math.pi), 9, P(RED, b))
    # l'hypothèse, barrée
    if o >= 83.5:
        al = b * ease((o - 83.5) / 0.3)
        text_c(c, "manque d'oxygène", 540, 1060, 56, WHITE, al)
        g = ease((o - 86.0) / 0.5)
        if g > 0:
            c.drawLine(300, 1040, lerp(300, 780, g), 1040, P(RED, al, stroke=9))


HEAD = (540.0, 640.0)


def sc_thermique(c, o):
    a = 255 * win(o, 89.8, 100.3)
    if a <= 1:
        return
    hx, hy = HEAD
    cool = ease((o - 92.5) / 1.6)
    y = yawn_at(o, 94.7, dur=3.6)
    hot, cold_c = (255, 130, 60), (110, 220, 255)
    c.drawCircle(hx, hy, 250, P(VIOLET, a * 0.25, blur=40))
    c.drawCircle(hx, hy, 240, P((70, 50, 120), a * 0.9))
    c.drawCircle(hx, hy, 240, P((200, 180, 255), a, stroke=5))
    brain(c, hx, hy - 85, 120, mix(hot, cold_c, cool), a)
    ink = (28, 18, 50)
    for sd in (-1, 1):
        if y > 0.35:
            p = skia.Path()
            p.moveTo(hx + sd * 60 - 18, hy + 50)
            p.quadTo(hx + sd * 60, hy + 64, hx + sd * 60 + 18, hy + 50)
            c.drawPath(p, P(WHITE, a, stroke=7))
        else:
            c.drawCircle(hx + sd * 60, hy + 52, 14, P(WHITE, a))
    mw, mh = 40 + 30 * y, 8 + 110 * y
    c.drawOval(skia.Rect(hx - mw / 2, hy + 110, hx + mw / 2, hy + 110 + mh), P((40, 12, 50), a))
    c.drawOval(skia.Rect(hx - mw / 2, hy + 110, hx + mw / 2, hy + 110 + mh), P(WHITE, a, stroke=5))
    # thermomètre
    tx = 905
    c.drawRoundRect(skia.Rect(tx - 22, 360, tx + 22, 760), 22, 22, P(WHITE, a * 0.9, stroke=5))
    c.drawCircle(tx, 790, 40, P(mix(hot, cold_c, cool), a))
    lvl = lerp(390, 680, cool)
    c.drawRoundRect(skia.Rect(tx - 10, lvl, tx + 10, 780), 10, 10, P(mix(hot, cold_c, cool), a))
    # air frais qui entre
    if 94.8 <= o < 98.5:
        al = a * win(o, 94.8, 98.2, 0.3, 0.3)
        for k in range(5):
            u = ((o - 94.8) * 0.9 + k / 5) % 1
            x = lerp(140, hx - 10, u)
            yy = hy + 170 + 50 * math.sin(u * 8 + k)
            c.drawCircle(x, yy, 12 * (1 - u * 0.5), P(CYAN, al * (1 - u)))
            c.drawCircle(x, yy, 24, P(CYAN, al * 0.3 * (1 - u), blur=8))
    if 96.8 <= o < 98.6:                                        # mâchoire qui s'étire
        al = a * win(o, 96.8, 98.3, 0.2, 0.3)
        for sd in (-1, 1):
            arrow(c, hx + sd * 120, hy + 140, hx + sd * 120, hy + 230, WHITE, al)
    if o >= 98.4:                                               # afflux de sang
        al = a * ease((o - 98.4) / 0.3)
        for sd in (-1, 1):
            vx = hx + sd * 70
            c.drawLine(vx, 1180, vx, hy + 230, P(RED, al * 0.5, stroke=14))
            for k in range(4):
                u = ((o - 98.4) * 1.3 + k / 4) % 1
                c.drawCircle(vx, lerp(1180, hy - 40, u), 12, P(RED, al * (1 - u * 0.6)))


def sc_froid(c, o):
    a = 255 * win(o, 100.3, 104.95)
    if a <= 1:
        return
    pion(c, 330, 720, 1.2, PINK, 0.0, a, look=1)
    fr = pop(o - 100.9)
    c.save()                                                    # poche de froid sur le front
    c.translate(330, 680)
    c.scale(fr, fr)
    c.drawRoundRect(skia.Rect(-70, -55, 70, -5), 16, 16, P(CYAN, a * 0.4, blur=14))
    c.drawRoundRect(skia.Rect(-70, -55, 70, -5), 16, 16, P((150, 230, 255), a))
    for k in range(9):
        c.drawCircle(-55 + 14 * k, -42 + 18 * (k % 2), 3, P(WHITE, a))
    c.restore()
    screen(c, 780, 600, 340, 300, a, lambda: pion(c, 780, 600, 1.0, CYAN, yawn_curve((o - 101.0) % 2.4, 2.0), 255,
                                                   body=False))
    if o >= 103.0:
        k = pop(o - 103.0)
        c.save()
        c.translate(540, 1080)
        c.scale(k, k)
        text_c(c, "contagion ↓", 0, 0, 64, CYAN, a)
        c.restore()


def sc_mammiferes(c, o):
    a = 255 * win(o, 105.0, 109.65)
    if a <= 1:
        return
    t0 = 106.3
    row = [(150, 0.8, mouse, 0.7), (390, 0.95, cat, 1.1), (650, 1.05, chimp, 1.7), (905, 1.15, None, 2.6)]
    for i, (x, s, fn, d) in enumerate(row):
        k = pop(o - 105.1 - 0.12 * i)
        y = yawn_at(o, t0, dur=d)
        if fn is None:
            pion(c, x, 600, s * k, PINK, y, a, body=False)
        else:
            fn(c, x, 600, s * k, y, a)
        brain(c, x, 360, (28 + 20 * i) * k, (255, 170, 200), a)
        # durée du bâillement : la barre pousse tant que la bouche est ouverte
        g = min(1.0, max(0.0, (o - t0) / d))
        hgt = 300 * d / 2.6 * g
        c.drawRoundRect(skia.Rect(x - 34, 1100 - hgt, x + 34, 1100), 12, 12, P(GOLD, a * 0.9))
        c.drawRoundRect(skia.Rect(x - 34, 1100 - hgt, x + 34, 1100), 12, 12, P(GOLD, a * 0.4, blur=10))
    c.drawLine(80, 1104, 1000, 1104, P(WHITE, a * 0.7, stroke=4))


def sc_mystere(c, o):
    a = 255 * win(o, 109.7, 113.4)
    if a <= 1:
        return
    brain(c, 540 + 10 * math.sin(T * 0.8), 600, 220 * pop(o - 109.75), VIOLET, a)
    fl = 0.6 + 0.4 * math.sin(T * 9) * math.sin(T * 3.3)
    c.drawCircle(560, 640, 70, P(AMBER, a * 0.5 * fl, blur=30))
    k = pop(o - 110.6)
    if k > 0:
        c.save()
        c.translate(560, 640)
        c.scale(k, k)
        text_c(c, "?", 0, 50, 170, GOLD, a)
        c.restore()


def sc_fin(c, o, t):
    a = 255 * win(o, 113.3, 200)
    if a <= 1:
        return
    fade = 1.0
    L, R = (300, 640), (780, 640)
    yl = yawn_at(o, 114.4, dur=1.9)
    yr = yawn_at(o, 116.0, dur=1.9)
    thread(c, (L[0] + 60, L[1]), (R[0] - 60, R[1]), 4, a * fade, [((o - 115.2) / 0.8, 1.0)])
    if o >= 117.4:                                              # le miroir
        al = a * fade * ease((o - 117.4) / 0.5)
        for k in range(16):
            c.drawLine(540, 420 + k * 30, 540, 435 + k * 30, P(WHITE, al * 0.7, stroke=4))
    pion(c, *L, 1.1, CYAN, yl, a * fade, look=1, glow=ease((o - 114.4) / 0.3))
    pion(c, *R, 1.1, CYAN, yr, a * fade, look=-1, glow=ease((o - 116.0) / 0.3))


# ------------------------------------------------------------------------------------------------ l'Orbe
# (instant o, position) : l'Orbe change de place à chaque scène pour laisser voir l'illustration et l'accompagner
STATIONS = [(0.0, (540, 1320, 0.76)), (3.2, (380, 1300, 0.72)), (6.4, (720, 1310, 0.72)), (11.6, (760, 1280, 0.72)),
            (17.3, (360, 1300, 0.74)), (24.0, (540, 1330, 0.68)), (27.1, (330, 1320, 0.68)), (31.6, (760, 1320, 0.68)),
            (36.6, (790, 1300, 0.72)), (40.0, (380, 1310, 0.72)), (44.4, (720, 1300, 0.72)), (48.2, (540, 1320, 0.72)),
            (50.7, (300, 1290, 0.7)), (54.3, (560, 1300, 0.74)), (57.8, (760, 1300, 0.72)), (61.0, (380, 1320, 0.72)),
            (67.1, (700, 1320, 0.7)), (69.3, (540, 1290, 0.72)), (76.0, (540, 1150, 0.92)), (79.2, (760, 1310, 0.72)),
            (83.1, (360, 1300, 0.72)), (89.8, (760, 1310, 0.72)), (94.7, (330, 1300, 0.72)), (100.3, (730, 1300, 0.72)),
            (105.0, (540, 1320, 0.72)), (109.7, (380, 1300, 0.74)), (113.3, (540, 1300, 0.8)), (117.4, (540, 1200, 0.95))]
# (de, à, point montré par le rayon de lumière)
POINTS = [(11.9, 13.3, (540, 300)), (37.3, 39.2, (470, 650)), (43.2, 44.3, (700, 1050)), (58.0, 60.6, (540, 300)),
          (66.0, 66.9, (540, 1060)), (69.6, 72.2, (540, 800)), (86.2, 88.0, (540, 1050)), (92.4, 94.2, (905, 600)),
          (103.1, 104.6, (330, 650)), (107.0, 109.2, (905, 850)), (110.6, 112.8, (560, 640))]


def orbe_target(t):
    o = O(t)
    pos = STATIONS[0][1]
    for t0, p in STATIONS:
        if o >= t0:
            pos = p
    return pos


# (instant o, yeux, humeur) pendant qu'il parle
MOODS = [(0.0, "surpris", "surprise"), (2.6, "parle", None), (21.4, "joie", "joie"), (23.6, "parle", None),
         (36.8, "surpris", "surprise"), (39.8, "parle", None), (48.3, "joie", "joie"), (50.5, "parle", None),
         (59.3, "surpris", "surprise"), (61.1, "parle", None), (69.3, "triste", "triste"), (75.6, "parle", None),
         (76.0, "reflechit", "reflexion"), (79.2, "parle", None), (85.9, "surpris", "surprise"), (88.0, "parle", None),
         (89.9, "idee", "idee"), (92.0, "parle", None), (109.8, "reflechit", "reflexion"), (113.3, "parle", None)]
FOCUS = [(0.0, (540, 720)), (6.4, (540, 760)), (11.6, (380, 700)), (17.3, (540, 700)), (24.0, CEN),
         (36.6, (470, 700)), (40.0, (540, 700)), (48.2, (540, 650)), (50.7, (740, 540)), (54.3, (760, 800)),
         (57.8, (540, 300)), (61.0, (540, 600)), (67.1, (540, 820)), (76.0, None), (79.2, (540, 500)),
         (83.1, (400, 640)), (89.8, HEAD), (100.3, (330, 700)), (105.0, (540, 560)), (109.7, (540, 600)),
         (113.3, (540, 640)), (117.4, None)]

_POSE = {}


def orbe_pose(t):
    """Position (ressort amorti vers la station), vitesse horizontale (pour l'inclinaison) et échelle."""
    if not _POSE:
        n = int(DUR * FPS) + 2
        x, y, s = orbe_target(0.0)
        vx = vy = vs = 0.0
        h = 1.0 / (FPS * 4)
        w = 5.5
        for f in range(n):
            _POSE[f] = (x, y, s, vx)
            for k in range(4):
                tx, ty, ts = orbe_target((f + k / 4) / FPS)
                vx += (w * w * (tx - x) - 2 * 0.7 * w * vx) * h
                vy += (w * w * (ty - y) - 2 * 0.7 * w * vy) * h
                vs += (w * w * (ts - s) - 2 * 0.9 * w * vs) * h
                x, y, s = x + vx * h, y + vy * h, s + vs * h
    f = t * FPS
    i = max(0, min(int(f), len(_POSE) - 2))
    u = f - i
    a, b = _POSE[i], _POSE[i + 1]
    return tuple(a[j] + (b[j] - a[j]) * u for j in range(4))


def last(lst, o):
    cur, prev, tc = lst[0][1:], lst[0][1:], lst[0][0]
    for item in lst:
        if o >= item[0]:
            prev, cur, tc = cur, item[1:], item[0]
    return cur, prev, tc


SYNC = None


def voice_level(t):
    i = min(len(SYNC.env) - 1, max(0, int((t + 0.03) * SYNC.rate)))
    return float(SYNC.env[i])


def draw_orbe_at(c, t):
    o = O(t)
    x, y, vx, s = None, None, None, None
    x, y, s, vx = orbe_pose(t)
    (yeux, hum), (_, hum0), tc = last(MOODS, o)
    age = o - tc
    v = voice_level(t)
    # mouvements : flottement, petite dérive, rebond sur les syllabes fortes, saut aux réactions
    x += 16 * math.sin(t * 0.9) + 6 * math.sin(t * 2.3)
    y += 9 * math.sin(t * 2.1) - 16 * v
    if yeux in ("surpris", "joie", "idee"):
        y -= 55 * math.sin(math.pi * min(1.0, age / 0.5)) if age < 0.5 else 0.0
    e = Etat(expr="parle", age=age, levres=SYNC(t), yeux=yeux, humeur=hum or "calme",
             humeur_avant=hum0 or "calme", humeur_mix=age / 0.5)
    e.cligne = yeux == "parle" and (t % 3.4) < 0.11
    (fp,), _, _ = last([(a, b) for a, b in FOCUS], o)
    if fp is None:
        e.regard = (0.0, 0.05)
    else:
        d = (fp[0] - x, fp[1] - y)
        n = math.hypot(*d) or 1.0
        e.regard = (0.7 * d[0] / n, 0.7 * d[1] / n)
    # inclinaison : vers ce qu'il regarde, dans le sens du déplacement, et un léger balancement en parlant
    tilt = 7 * e.regard[0] - max(-14.0, min(14.0, vx * 0.03)) + 4 * math.sin(t * 1.3) * (0.4 + v)
    for a_, b_, pt in POINTS:
        if a_ <= o < b_:
            dx, dy = (pt[0] - x) / s, (pt[1] - y) / s
            r = math.radians(-tilt)
            e.cible = (dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r))
            e.age = o - a_
    c.save()
    c.translate(x, y)
    c.rotate(tilt)
    c.scale(s * (1 + 0.03 * v), s * (1 - 0.02 * v))
    draw_orbe(c, t, e)
    c.restore()


# ------------------------------------------------------------------------------------------------ image
SCENES = [sc_hook, sc_moitie, sc_provine, sc_lecture, sc_reseau, sc_foetus, sc_enfant, sc_especes, sc_chiens,
          sc_baylor, sc_question, sc_oxygene, sc_thermique, sc_froid, sc_mammiferes, sc_mystere]


def frame(c, t):
    global T
    T = t
    o = O(t)
    E1.draw_background(c, t)
    c.drawRect(skia.Rect(0, 0, W, H), P((4, 3, 12), 255 * 0.35))
    for sc in SCENES:
        sc(c, o)
    sc_fin(c, o, t)
    draw_orbe_at(c, t)
    E1.draw_subtitle(c, t)


# ------------------------------------------------------------------------------------------------ son
def voice_track():
    v = MI.load_voice(VOIX)
    sr = MI.SR
    i = int(GAP_AT * sr)
    return np.concatenate([v[:i], np.zeros(int(GAP * sr)), v[i:]]) if GAP else v


def fx_events():
    ev = [(0.0, E1.swell(0.12), 1.0), (N(6.9), E1.pop_s(500, 0.12), 1.0),
          (N(11.75), E1.ding(660, 0.12), 1.0), (N(21.4), E1.pop_s(520, 0.14), 1.0), (N(22.4), E1.sparkle(0.1), 1.0),
          (N(24.1), E1.swish(0.8, 0.1), 1.0), (N(27.3), E1.ding(700, 0.1), 1.0), (N(30.4), E1.ding(620, 0.09), 1.0),
          (N(31.7), E1.ding(540, 0.06), 1.0), (N(37.2), E1.ding(784, 0.12), 1.0), (N(43.2), E1.pop_s(560, 0.12), 1.0),
          (N(48.3), E1.swish(0.8, 0.1), 1.0), (N(54.5), E1.ding(660, 0.12), 1.0), (N(59.3), E1.ding(784, 0.12), 1.0),
          (N(61.3), E1.ding(660, 0.12), 1.0), (N(69.4), HK.sub_drop(0.3), 1.0), (N(77.5), E1.swell(0.14), 1.0),
          (N(83.1), E1.ding(660, 0.12), 1.0), (N(86.0), E1.swish(0.5, 0.1), 1.0), (N(89.9), E1.sparkle(0.12), 1.0),
          (N(103.0), E1.pop_s(480, 0.12), 1.0), (N(106.3), E1.swish(2.6, 0.06), 1.0), (N(110.6), HK.sub_drop(0.3), 1.0),
          (N(117.4), E1.swell(0.14), 1.0)]
    ev += [(N(t0 + 0.6), E1.ding(523 + 40 * i, 0.06), 1.0) for i, t0 in enumerate((58.0, 58.5, 59.0))]
    return ev


def render(out_path, t_from=0.0, t_to=None):
    global SYNC
    tmp = tempfile.mkdtemp()
    voice = voice_track()
    cache = os.path.join(HERE, "audio", "voix_orbe.wav")
    with wave.open(cache, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(MI.SR)
        w.writeframes((np.clip(voice, -1, 1) * 32767).astype(np.int16).tobytes())
    SYNC = LV.Synchro(cache)
    E1.TIMING = [(txt.replace(" ?", "\u00a0?"), N(a), N(b)) for txt, a, b in SEG]
    t_to = DUR if t_to is None else t_to
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    f0, f1 = int(t_from * FPS), int(t_to * FPS)
    for f in range(f0, f1):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
        if f % 300 == 0:
            print(f"{f / FPS:6.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()
    wav = f"{tmp}/a.wav"
    MI.soundtrack(wav, voice, DUR, fx_events())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-ss", str(t_from), "-t", str(t_to - t_from), "-i", wav,
                    "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out_path], check=True)
    print("OK", out_path)


if __name__ == "__main__":
    a = sys.argv[2:]
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep13_orbe.mp4",
           float(a[0]) if a else 0.0, float(a[1]) if len(a) > 1 else None)
