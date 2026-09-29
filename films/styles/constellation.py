"""Style « Constellation » : tout le monde est fait de points d'étoiles reliés par des fils de lumière ;
seule la goutte est un corps plein et lumineux. Fond noir, ambiance cosmique.

    python -m films.styles.constellation <dossier>
"""
import math
import sys
from pathlib import Path

import numpy as np
import skia

W, H = 1080, 1920
STAR = (200, 225, 255)
DROP = (70, 200, 255)
GOLD = (255, 196, 110)
LIFE = (150, 255, 170)


def col(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def paint(c, style="fill", width=0.0, blur=0.0, add=False, shader=None):
    p = skia.Paint(AntiAlias=True, Color=c, StrokeWidth=width,
                   Style=skia.Paint.kStroke_Style if style == "stroke" else skia.Paint.kFill_Style)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if add:
        p.setBlendMode(skia.BlendMode.kPlus)
    if shader is not None:
        p.setShader(shader)
    return p


def star(c, x, y, r, rgb=STAR, a=1.0):
    """Un point d'étoile : cœur net, halo, et petite croix de diffraction pour les plus brillants."""
    c.drawCircle(x, y, r * 4, paint(col(rgb, 50 * a), blur=r * 3, add=True))
    c.drawCircle(x, y, r, paint(col((255, 255, 255), 255 * a)))
    if r > 3:
        for dx, dy in ((1, 0), (0, 1)):
            c.drawLine(x - dx * r * 5, y - dy * r * 5, x + dx * r * 5, y + dy * r * 5,
                       paint(col(rgb, 120 * a), "stroke", 1.2, add=True))


def thread(c, pts, rgb=STAR, a=0.35, width=1.4):
    """Fils de lumière entre les points (comme les lignes d'une constellation)."""
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    c.drawPath(p, paint(col(rgb, 255 * a * 0.4), "stroke", width * 4, blur=3, add=True))
    c.drawPath(p, paint(col(rgb, 255 * a), "stroke", width))


def sky(c, seed=1, n=420):
    r = np.random.default_rng(seed)
    for x, y, s, b in zip(r.uniform(0, W, n), r.uniform(0, H, n), r.power(4, n) * 2.2 + 0.4, r.uniform(0.2, 1.0, n)):
        c.drawCircle(x, y, s, paint(col(STAR, 200 * b)))
    neb = skia.GradientShader.MakeRadial((W * 0.3, H * 0.28), 700, [col((70, 60, 150), 45), col((0, 0, 0), 0)])
    c.drawPaint(paint(skia.ColorBLACK, shader=neb, add=True))


def dunes(c, y, seed=2, rgb=STAR):
    """Les dunes : des lignes de points d'étoiles, plus serrées et plus brillantes au premier plan."""
    r = np.random.default_rng(seed)
    for k, (yy, amp, ph) in enumerate([(y - 170, 40, 0.5), (y - 60, 55, 2.1), (y + 90, 70, 3.9)]):
        xs = np.linspace(-40, W + 40, 20 + 10 * k)
        ys = yy + amp * np.sin(xs * 0.004 + ph) + amp * 0.4 * np.sin(xs * 0.012 + seed + k)
        pts = list(zip(xs, ys))
        thread(c, pts, rgb, a=0.12 + 0.1 * k, width=1.0 + 0.4 * k)
        for (px, py) in pts:
            star(c, px, py, 1.4 + 0.9 * k * r.random(), rgb, 0.45 + 0.2 * k)
        for _ in range(60 + 40 * k):                       # poussière d'étoiles sous la ligne : le sable
            px = r.uniform(0, W)
            py = np.interp(px, xs, ys) + r.exponential(35 + 40 * k)
            c.drawCircle(px, py, r.uniform(0.6, 1.6), paint(col(rgb, r.uniform(60, 170))))


def sun(c, x, y, rad, heat=1.0, t=0.0):
    """Le soleil : une couronne d'étoiles dorées ; plus il chauffe, plus elles brillent et rayonnent."""
    g = skia.GradientShader.MakeRadial((x, y), rad * 3, [col(GOLD, 90 * heat), col(GOLD, 0)])
    c.drawCircle(x, y, rad * 3, paint(skia.ColorBLACK, shader=g, add=True))
    n = 28
    ring = []
    for k in range(n):
        a = 2 * math.pi * k / n + t * 0.1
        ring.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
    thread(c, ring + [ring[0]], GOLD, a=0.5)
    for i, (px, py) in enumerate(ring):
        star(c, px, py, 2.4 + 1.5 * (i % 4 == 0), GOLD, 0.9)
        if i % 2 == 0:
            a = 2 * math.pi * i / n
            for j in range(1, 4):
                rr = rad * (1 + 0.28 * j)
                star(c, x + math.cos(a) * rr, y + math.sin(a) * rr, 2.0 - 0.45 * j, GOLD, 0.8 - 0.2 * j)
    star(c, x, y, 6, GOLD, 1.0)


def drop_path(cx, base, size, sx=1.0, sz=1.0):
    path = skia.Path()
    n, r, pts = 90, size / 2, []
    for i in range(n + 1):
        a = -math.pi / 2 + 2 * math.pi * i / n
        x, y = math.cos(a) * r, math.sin(a) * r
        up = max(0.0, -y) / r
        x *= 1 - 0.55 * up ** 1.9
        y = y * (1 + 0.5 * up) if y < 0 else y
        pts.append((cx + x * sx, base - r * sz + y * sz))
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    path.close()
    return path


def goutte(c, cx, base, size, eyes=1.0, smile=1.0, glow=1.0):
    """L'héroïne : le seul corps plein de l'univers, une goutte de lumière bleue qui éclaire autour d'elle."""
    halo = skia.GradientShader.MakeRadial((cx, base - size * 0.5), size * 2.2, [col(DROP, 85 * glow), col(DROP, 0)])
    c.drawCircle(cx, base - size * 0.5, size * 2.2, paint(skia.ColorBLACK, shader=halo, add=True))
    p = drop_path(cx, base, size)
    body = skia.GradientShader.MakeRadial((cx - size * 0.12, base - size * 0.55), size * 0.9,
                                          [col((230, 250, 255)), col(DROP), col((20, 90, 200))], [0.0, 0.45, 1.0])
    c.drawPath(p, paint(skia.ColorBLACK, shader=body))
    c.drawPath(p, paint(col((210, 245, 255), 200), "stroke", 3))
    ey = base - size * 0.52
    for side in (-1, 1):
        ex = cx + side * size * 0.17
        w, h = size * 0.085, size * 0.15 * eyes
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ex - w / 2, ey - h / 2, ex + w / 2, ey + h / 2), w / 2, w / 2),
                    paint(col((8, 30, 70))))
        c.drawCircle(ex - w * 0.15, ey - h * 0.22, w * 0.22, paint(col((255, 255, 255))))
    if smile:
        m = skia.Path()
        m.moveTo(cx - size * 0.08, ey + size * 0.2)
        m.quadTo(cx, ey + size * 0.2 + size * 0.09 * smile, cx + size * 0.08, ey + size * 0.2)
        c.drawPath(m, paint(col((8, 30, 70)), "stroke", size * 0.028))
    # la lumière de la goutte allume les étoiles proches (reflet au sol)
    refl = skia.GradientShader.MakeRadial((cx, base + 10), size * 0.9, [col(DROP, 120 * glow), col(DROP, 0)])
    c.drawOval(skia.Rect.MakeLTRB(cx - size * 0.9, base - 12, cx + size * 0.9, base + 34),
               paint(skia.ColorBLACK, shader=refl, add=True))


def trail(c, cx, top, length, n=16):
    for k in range(n):
        u = k / n
        star(c, cx + 6 * math.sin(k), top - u * length, 3.2 * (1 - u) + 0.6, DROP, 1 - u)


def sprout(c, x, y, s, alive=0.0):
    rgb = tuple(a + (b - a) * alive for a, b in zip((140, 150, 170), LIFE))
    bend = 1 - alive
    stem = [(x + s * 0.3 * bend * (u ** 2), y - s * u * (1 - 0.35 * bend * u)) for u in np.linspace(0, 1, 7)]
    thread(c, stem, rgb, a=0.4 + 0.5 * alive, width=1.6)
    for px, py in stem:
        star(c, px, py, 1.8 + 1.4 * alive, rgb, 0.5 + 0.5 * alive)
    for side in (-1, 1):
        base = stem[3]
        pts = [base]
        for j in range(1, 5):
            a = -math.pi / 2 + side * (1.2 + 0.6 * bend - 0.5 * alive) + side * 0.08 * j
            pts.append((base[0] + math.cos(a) * s * 0.11 * j, base[1] + math.sin(a) * s * 0.11 * j + bend * 6 * j * j))
        thread(c, pts, rgb, a=0.5, width=1.4)
        for px, py in pts[1:]:
            star(c, px, py, 1.6 + alive * 1.2, rgb, 0.5 + 0.5 * alive)


def cloud(c, x, y, s, frown=0.0):
    r = np.random.default_rng(9)
    for _ in range(420):                                   # nébuleuse : nuée d'étoiles en forme de nuage
        a = r.uniform(0, 2 * math.pi)
        lobe = r.integers(5)
        lx, ly, lr = [(-0.55, 0.05, 0.32), (-0.2, -0.18, 0.42), (0.25, -0.12, 0.38), (0.6, 0.05, 0.3), (0.0, 0.1, 0.35)][lobe]
        d = r.random() ** 0.6 * lr
        px, py = x + (lx + math.cos(a) * d) * s, y + (ly + math.sin(a) * d) * s
        c.drawCircle(px, py, r.uniform(0.8, 2.6), paint(col(STAR, r.uniform(80, 230))))
    g = skia.GradientShader.MakeRadial((x, y), s * 0.9, [col((110, 130, 200), 70), col((0, 0, 0), 0)])
    c.drawCircle(x, y, s * 0.9, paint(skia.ColorBLACK, shader=g, add=True))
    for side in (-1, 1):
        ex, ey = x + side * 0.2 * s, y
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(ex - 0.03 * s, ey - 0.06 * s, 0.06 * s, 0.12 * s), 0.03 * s, 0.03 * s),
                    paint(col((255, 255, 255))))
        if frown:
            c.drawLine(ex - side * 0.1 * s, ey - 0.14 * s, ex + side * 0.07 * s, ey - 0.09 * s, paint(col((255, 255, 255)), "stroke", 5))


def rain(c, x0, x1, y0, y1, n=60, seed=5):
    r = np.random.default_rng(seed)
    for x, u in zip(r.uniform(x0, x1, n), r.uniform(0, 1, n)):
        y = y0 + (y1 - y0) * u
        c.drawLine(x, y, x - 5, y + 40, paint(col(DROP, 90), "stroke", 6, blur=4, add=True))
        c.drawLine(x, y, x - 5, y + 40, paint(col((200, 240, 255), 230), "stroke", 2.2))


def flower(c, x, y, s, petals=7, rot=0.0):
    stem = [(x, y - s * u) for u in np.linspace(0, 1, 5)]
    thread(c, stem, LIFE, a=0.5, width=1.4)
    cy = y - s
    for k in range(petals):
        a = rot + 2 * math.pi * k / petals
        pts = [(x + math.cos(a + 0.35 * math.sin(math.pi * u)) * s * 0.4 * u, cy + math.sin(a + 0.35 * math.sin(math.pi * u)) * s * 0.4 * u)
               for u in np.linspace(0, 1, 6)]
        thread(c, pts, DROP, a=0.6, width=1.3)
        star(c, *pts[-1], 2.6, DROP, 1.0)
    star(c, x, cy, 4.5, GOLD, 1.0)


def frame(out, name, draw):
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(skia.ColorBLACK)
    draw(c)
    s.makeImageSnapshot().save(str(out / f"{name}.png"), skia.kPNG)
    print(out / f"{name}.png", flush=True)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)

    def chute(c):
        sky(c)
        dunes(c, 1500)
        trail(c, W / 2, 700, 520)
        goutte(c, W / 2, 900, 180, eyes=1.2, smile=0)

    def soleil(c):
        sky(c, 3)
        sun(c, 760, 480, 120)
        dunes(c, 1450, 4, GOLD)
        goutte(c, 470, 1380, 300)

    def pousse(c):
        sky(c, 5)
        dunes(c, 1450, 6)
        sprout(c, 690, 1395, 260, alive=0.0)
        goutte(c, 400, 1400, 190, smile=-0.6)

    def pluie(c):
        sky(c, 7)
        cloud(c, W / 2, 520, 420, frown=1.0)
        rain(c, W / 2 - 330, W / 2 + 330, 660, 1330)
        dunes(c, 1500, 8)
        rr = np.random.default_rng(3)
        for k in range(9):
            flower(c, 90 + k * 115, 1450 + rr.uniform(-20, 20), rr.uniform(120, 230), rot=rr.uniform(0, 3))

    for name, fn in [("c1_chute", chute), ("c2_soleil", soleil), ("c3_pousse", pousse), ("c4_pluie", pluie)]:
        frame(out, name, fn)
