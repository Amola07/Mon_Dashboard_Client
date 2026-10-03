"""Scène de théâtre (rideaux, plancher, projecteur), accessoires, effets comiques et bruitages."""
import math

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1
from films.theatre.acteur import INK, WHITE, P

W, H = 1080, 1920
SOL = 1430.0
SR = E1.SR


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


# ------------------------------------------------------------------------------------------------ décor
def decor(c, t, ouverture, lumiere=1.0):
    # fond de scène
    c.drawRect(skia.Rect(-400, -400, W + 400, H + 400), P(skia.Color(38, 30, 44)))
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, SOL - 250), 720,
                                        [skia.Color(255, 244, 214, int(235 * lumiere)), skia.Color(120, 100, 120, 0)])
    c.drawRect(skia.Rect(-400, -400, W + 400, H + 400), skia.Paint(Shader=sh))
    # plancher en perspective
    floor = skia.Path()
    floor.moveTo(-200, SOL - 40)
    floor.lineTo(W + 200, SOL - 40)
    floor.lineTo(W + 200, H)
    floor.lineTo(-200, H)
    floor.close()
    c.drawPath(floor, P(skia.Color(176, 120, 72)))
    for k in range(-8, 9):
        c.drawLine(W / 2 + k * 70, SOL - 40, W / 2 + k * 260, H, P(skia.Color(140, 92, 52), 3))
    for y in (SOL + 60, SOL + 200, SOL + 380):
        c.drawLine(0, y, W, y, P(skia.Color(150, 100, 58), 2))
    c.drawLine(-10, SOL - 40, W + 10, SOL - 40, P(INK, 5))
    spot = skia.GradientShader.MakeRadial(skia.Point(W / 2, SOL + 10), 420,
                                          [skia.Color(255, 240, 200, int(120 * lumiere)), skia.Color(255, 240, 200, 0)])
    c.save()
    c.scale(1, 0.3)
    c.translate(0, (SOL + 10) / 0.3 - (SOL + 10))
    c.drawCircle(W / 2, SOL + 10, 420, skia.Paint(Shader=spot))
    c.restore()


def rideaux(c, ouverture):
    """Rideaux rouges : ouverture 0 = fermés, 1 = ouverts (relevés sur les côtés)."""
    for sd in (-1, 1):
        larg = lerp(W / 2 + 20, 56, ouverture)
        x0 = 0 if sd < 0 else W - larg
        r = skia.Rect(x0, 0, x0 + larg, H - 260)
        shader = skia.GradientShader.MakeLinear([skia.Point(x0, 0), skia.Point(x0 + 46, 0)],
                                                [skia.Color(150, 18, 30), skia.Color(205, 40, 50),
                                                 skia.Color(120, 12, 24)],
                                                None, skia.TileMode.kRepeat)
        c.drawRect(r, skia.Paint(Shader=shader))
        c.drawRect(r, P(INK, 4))
    # lambrequin
    c.drawRect(skia.Rect(0, 0, W, 170), P(skia.Color(160, 20, 32)))
    for k in range(9):
        x = k * W / 8
        c.drawOval(skia.Rect(x - 80, 120, x + 80, 220), P(skia.Color(160, 20, 32)))
        c.drawOval(skia.Rect(x - 80, 120, x + 80, 220), P(INK, 4))
    c.drawRect(skia.Rect(0, 0, W, 150), P(skia.Color(160, 20, 32)))
    c.drawLine(0, 150, W, 150, P(skia.Color(240, 190, 60), 10))
    # avant-scène sombre
    c.drawRect(skia.Rect(0, H - 260, W, H), P(skia.Color(20, 14, 18)))
    c.drawLine(0, H - 260, W, H - 260, P(skia.Color(240, 190, 60), 8))


# ------------------------------------------------------------------------------------------------ accessoires
def peau_banane(c, x, y, s=1.0, ang=0.0, ecrase=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s * (1 + 0.3 * ecrase), s * (1 - 0.4 * ecrase))
    jaune, brun = skia.Color(250, 214, 60), skia.Color(120, 80, 30)
    for k, a in enumerate((-70, -15, 40)):
        c.save()
        c.rotate(a)
        p = skia.Path()
        p.moveTo(0, 0)
        p.cubicTo(-14, -14, -10, -46, 6, -58)
        p.cubicTo(16, -40, 16, -12, 0, 0)
        p.close()
        c.drawPath(p, P(jaune))
        c.drawPath(p, P(INK, 3.5))
        c.restore()
    c.drawOval(skia.Rect(-16, -12, 16, 8), P(jaune))
    c.drawOval(skia.Rect(-16, -12, 16, 8), P(INK, 3.5))
    c.drawCircle(0, -2, 5, P(brun))
    c.restore()


def banane(c, x, y, ang=0.0, s=1.0):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    p = skia.Path()
    p.moveTo(-55, -10)
    p.cubicTo(-30, 30, 30, 30, 55, -10)
    p.cubicTo(30, 10, -30, 10, -55, -10)
    p.close()
    c.drawPath(p, P(skia.Color(250, 214, 60)))
    c.drawPath(p, P(INK, 4))
    c.drawLine(-55, -10, -64, -18, P(skia.Color(120, 80, 30), 6))
    c.restore()


# ------------------------------------------------------------------------------------------------ effets
def etoiles(c, x, y, t, k=1.0):
    for i in range(5):
        a = t * 4 + i * 2 * math.pi / 5
        sx, sy = x + 80 * math.cos(a), y + 26 * math.sin(a)
        r = 14 * k
        p = skia.Path()
        for j in range(10):
            rr = r if j % 2 == 0 else r * 0.45
            aa = -math.pi / 2 + j * math.pi / 5
            q = (sx + rr * math.cos(aa), sy + rr * math.sin(aa))
            p.moveTo(*q) if j == 0 else p.lineTo(*q)
        p.close()
        c.drawPath(p, P(skia.Color(255, 220, 60)))
        c.drawPath(p, P(INK, 2.5))


FONT = skia.Typeface.MakeFromFile("films/fonts/BebasNeue-Regular.ttf")


def bulle(c, x, y, txt, k=1.0, queue=(-40, 70), taille=64):
    if k <= 0:
        return
    f = skia.Font(FONT, taille)
    w = f.measureText(txt) + 50
    h = taille + 34
    c.save()
    c.translate(x, y)
    s = min(1.0, k) * (1 + 0.25 * math.exp(-k * 5) * math.sin(k * 14))
    c.scale(s, s)
    q = skia.Path()
    q.moveTo(-14, h / 2 - 8)
    q.lineTo(queue[0], queue[1])
    q.lineTo(14, h / 2 - 8)
    q.close()
    r = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), 30, 30)
    c.drawPath(q, P(WHITE))
    c.drawPath(q, P(INK, 4))
    c.drawRRect(r, P(WHITE))
    c.drawRRect(r, P(INK, 4))
    c.drawRect(skia.Rect(-16, h / 2 - 12, 16, h / 2 - 1), P(WHITE))
    c.drawString(txt, -f.measureText(txt) / 2, taille * 0.36, f, P(INK))
    c.restore()


def notes(c, x, y, t):
    for i in range(3):
        u = (t * 0.8 + i / 3) % 1
        nx, ny = x + 30 * math.sin(u * 6 + i) + i * 18, y - 150 * u
        a = int(255 * (1 - u))
        col = skia.Color(20, 20, 24, a)
        c.drawOval(skia.Rect(nx - 10, ny - 7, nx + 10, ny + 7), P(col))
        c.drawLine(nx + 9, ny, nx + 9, ny - 34, P(col, 3.5))
        c.drawLine(nx + 9, ny - 34, nx + 22, ny - 26, P(col, 3.5))


def traits_vitesse(c, x, y, k, sens=1):
    for i in range(3):
        yy = y - 30 + i * 30
        c.drawLine(x - sens * 40, yy, x - sens * (40 + 60 * k), yy, P(skia.Color(20, 20, 24, int(200 * k)), 4))


# ------------------------------------------------------------------------------------------------ sons
def _t(n):
    return np.arange(n) / SR


def tap(amp=0.12):
    n = int(0.08 * SR)
    tt = _t(n)
    return np.sin(2 * np.pi * 220 * tt) * np.exp(-tt / 0.012) * amp + \
        np.random.default_rng(1).normal(0, 1, n) * np.exp(-tt / 0.006) * amp * 0.3


def glissade(amp=0.25):
    n = int(0.45 * SR)
    tt = _t(n)
    f = 300 + 1300 * (tt / tt[-1]) ** 1.5
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tt / 0.02) * np.exp(-tt / 0.3) * amp


def boing(amp=0.3):
    n = int(0.6 * SR)
    tt = _t(n)
    f = 180 + 90 * np.sin(2 * np.pi * 11 * tt) * np.exp(-tt / 0.25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.22) * amp


def bonk(amp=0.35):
    n = int(0.35 * SR)
    tt = _t(n)
    f = 520 * np.exp(-tt / 0.08) + 160
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.07) * amp


def sifflet(dur, amp=0.07):
    n = int(dur * SR)
    tt = _t(n)
    mel = [988, 1175, 1319, 1175, 988, 880, 988, 1319]
    idx = (tt / 0.22).astype(int) % len(mel)
    f = np.array(mel)[idx] * (1 + 0.01 * np.sin(2 * np.pi * 6 * tt))
    env = np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 0.1)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env * amp


def tss(amp=0.18):
    n = int(0.9 * SR)
    tt = _t(n)
    x = np.random.default_rng(3).normal(0, 1, n)
    x = x - np.convolve(x, np.ones(6) / 6, "same")                 # aigus
    return x * np.exp(-tt / 0.28) * amp


def ba_dum_tss():
    out = np.zeros(int(1.4 * SR))
    for t0, f0 in ((0.0, 190), (0.18, 150)):
        n = int(0.3 * SR)
        tt = _t(n)
        s = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.6 * np.exp(-tt / 0.03))) / SR) * np.exp(-tt / 0.12) * 0.35
        out[int(t0 * SR): int(t0 * SR) + n] += s
    c = tss(0.25)
    out[int(0.38 * SR): int(0.38 * SR) + len(c)] += c
    return out


def applaudissements(dur, amp=0.18):
    n = int(dur * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(7)
    clap_n = int(0.03 * SR)
    tt = _t(clap_n)
    for _ in range(int(dur * 60)):
        i = rng.integers(0, n - clap_n)
        out[i:i + clap_n] += rng.normal(0, 1, clap_n) * np.exp(-tt / 0.006) * rng.uniform(0.3, 1.0)
    env = np.minimum(1, _t(n) / 0.4) * np.minimum(1, (dur - _t(n)) / 0.6)
    return out * env * amp


def rideau_son(dur=1.0, amp=0.12):
    n = int(dur * SR)
    x = np.convolve(np.random.default_rng(4).normal(0, 1, n), np.ones(40) / 40, "same")
    tt = _t(n)
    return x * np.sin(np.pi * tt / dur) * amp * 4
