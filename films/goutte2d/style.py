"""« Goutte » en 2D graphique : fond noir, monde en traits blancs fins, héroïne d'une seule couleur vive.

Éléments de dessin partagés par les images de style et le film.
"""
import math

import numpy as np
import skia

W, H = 1080, 1920
BLACK = skia.Color(0, 0, 0)
LINE = (235, 238, 245)
DROP = (64, 190, 255)          # la seule couleur vive : la goutte
SUN = (255, 170, 60)
LEAF = (110, 225, 120)


def col(rgb, a=255):
    return skia.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(max(0, min(255, a))))


def paint(c, style="fill", width=0.0, blur=0.0, blend=None, cap_round=True, shader=None):
    p = skia.Paint(AntiAlias=True, Color=c, StrokeWidth=width,
                   Style=skia.Paint.kStroke_Style if style == "stroke" else skia.Paint.kFill_Style)
    if cap_round:
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    if shader is not None:
        p.setShader(shader)
    return p


class Dust:
    """Poussières lumineuses qui flottent (profondeur, comme des particules dans un rayon de lumière)."""

    def __init__(self, n=90, seed=1):
        r = np.random.default_rng(seed)
        self.p = np.column_stack([r.uniform(0, W, n), r.uniform(0, H, n), r.uniform(0.8, 3.2, n),
                                  r.uniform(0, 6.28, n), r.uniform(4, 16, n)])

    def draw(self, c, t, alpha=1.0):
        for x, y, s, ph, sp in self.p:
            a = (0.3 + 0.7 * (0.5 + 0.5 * math.sin(ph + t * 0.9))) * alpha
            yy = (y - t * sp) % H
            xx = x + 12 * math.sin(ph + t * 0.3)
            if s > 2.4:
                c.drawCircle(xx, yy, s * 2.5, paint(col(LINE, 30 * a), blur=s * 2))
            c.drawCircle(xx, yy, s, paint(col(LINE, 160 * a)))


def glow_path(c, path, rgb, width, glow=1.0, alpha=255):
    """Trait net + halo doux (l'« éclat » des lignes)."""
    if glow > 0:
        c.drawPath(path, paint(col(rgb, 90 * glow * alpha / 255), "stroke", width * 3.5, blur=width * 2.2,
                               blend=skia.BlendMode.kPlus))
    c.drawPath(path, paint(col(rgb, alpha), "stroke", width))


def dot(c, x, y, r=7, rgb=LINE, alpha=255):
    c.drawCircle(x, y, r, paint(col((0, 0, 0), alpha)))
    c.drawCircle(x, y, r, paint(col(rgb, alpha), "stroke", 2.5))


def drop_path(cx, base_y, size, sx=1.0, sz=1.0, lean=0.0):
    """Silhouette de goutte (pointe vers le haut), base posée en base_y."""
    path = skia.Path()
    n = 64
    r = size * 0.5
    pts = []
    for i in range(n + 1):
        a = -math.pi / 2 + 2 * math.pi * i / n          # part du bas
        x = math.cos(a) * r
        y = math.sin(a) * r                              # y vers le bas (écran)
        up = max(0.0, -y) / r                            # 0 en bas/milieu, 1 en haut
        k = 1 - 0.55 * up ** 1.9
        x *= k
        y = y * (1 + 0.55 * up) if y < 0 else y
        pts.append((cx + x * sx + lean * (-y / r) * size * 0.15, base_y - r * sz + y * sz))
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.close()
    return path


def draw_drop(c, cx, base_y, size, sx=1.0, sz=1.0, lean=0.0, eyes=1.0, look=(0.0, 0.0), mouth=0.0, glow=1.0,
              alpha=255):
    """L'héroïne : aplat bleu lumineux, contour plus clair, deux yeux blancs (eyes : 1 ouverts, 0 fermés)."""
    p = drop_path(cx, base_y, size, sx, sz, lean)
    c.drawPath(p, paint(col(DROP, 70 * glow * alpha / 255), blur=size * 0.18, blend=skia.BlendMode.kPlus))
    shade = skia.GradientShader.MakeLinear([(cx, base_y - size * sz * 1.2), (cx, base_y)],
                                           [col((120, 215, 255), alpha), col(DROP, alpha), col((30, 120, 220), alpha)],
                                           [0.0, 0.55, 1.0])
    c.drawPath(p, paint(skia.ColorBLACK, shader=shade))
    c.drawPath(p, paint(col((190, 235, 255), alpha), "stroke", max(3.0, size * 0.035)))
    # yeux : deux capsules blanches ; fermés = petits arcs
    ey = base_y - size * sz * 0.52
    for side in (-1, 1):
        ex = cx + side * size * 0.17 * sx + look[0] * size
        eyy = ey + look[1] * size
        h = size * 0.13 * max(eyes, 0.0)
        w = size * 0.075
        if eyes > 0.15:
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ex - w / 2, eyy - h / 2, ex + w / 2, eyy + h / 2), w / 2, w / 2),
                        paint(col((255, 255, 255), alpha)))
        else:
            arc = skia.Path()
            arc.moveTo(ex - w * 0.8, eyy)
            arc.quadTo(ex, eyy + w * 0.8, ex + w * 0.8, eyy)
            c.drawPath(arc, paint(col((255, 255, 255), alpha), "stroke", max(2.5, size * 0.025)))
    if mouth:
        my = ey + size * 0.2
        m = skia.Path()
        m.moveTo(cx - size * 0.08, my)
        m.quadTo(cx, my + size * 0.1 * mouth, cx + size * 0.08, my)
        c.drawPath(m, paint(col((255, 255, 255), alpha), "stroke", max(2.5, size * 0.025)))
    return p


def horizon(c, y, t=0.0, amp=26, width=3.0, alpha=255):
    """Les dunes : une seule ligne blanche ondulée, avec des points aux crêtes."""
    path = skia.Path()
    xs = np.linspace(-20, W + 20, 90)
    ys = y + amp * np.sin(xs * 0.006 + 0.7) + amp * 0.5 * np.sin(xs * 0.017 + 2.1)
    path.moveTo(xs[0], ys[0])
    for x_, y_ in zip(xs[1:], ys[1:]):
        path.lineTo(x_, y_)
    glow_path(c, path, LINE, width, glow=0.6, alpha=alpha)
    crest = [i for i in range(1, len(ys) - 1) if ys[i] < ys[i - 1] and ys[i] <= ys[i + 1]]
    for i in crest:
        dot(c, xs[i], ys[i], 6, alpha=alpha)
    return xs, ys


def sun(c, x, y, r, heat=0.0, t=0.0):
    """Soleil : cercle au trait, qui se remplit d'un dégradé chaud quand il chauffe ; ondes de chaleur."""
    if heat > 0:
        g = skia.GradientShader.MakeRadial((x, y), r * 3.2, [col(SUN, 110 * heat), col(SUN, 0)])
        c.drawCircle(x, y, r * 3.2, paint(skia.ColorBLACK, shader=g, blend=skia.BlendMode.kPlus))
        fill = skia.GradientShader.MakeRadial((x, y), r, [col((255, 230, 160), 230 * heat), col(SUN, 150 * heat)])
        c.drawCircle(x, y, r, paint(skia.ColorBLACK, shader=fill))
    circ = skia.Path()
    circ.addCircle(x, y, r)
    glow_path(c, circ, LINE if heat < 0.5 else (255, 225, 170), 3.0, glow=0.8)
    for k in range(12):                                # rayons : petits traits
        a = 2 * math.pi * k / 12 + t * 0.2
        r0, r1 = r * 1.25, r * (1.45 + 0.08 * math.sin(t * 3 + k))
        ray = skia.Path()
        ray.moveTo(x + math.cos(a) * r0, y + math.sin(a) * r0)
        ray.lineTo(x + math.cos(a) * r1, y + math.sin(a) * r1)
        glow_path(c, ray, LINE if heat < 0.5 else (255, 225, 170), 3.0, glow=0.5)


def heat_waves(c, x, y0, y1, t, alpha=200):
    for k in range(3):
        p = skia.Path()
        xx = x + (k - 1) * 38
        p.moveTo(xx, y0)
        n = 24
        for i in range(1, n + 1):
            yy = y0 + (y1 - y0) * i / n
            p.lineTo(xx + 9 * math.sin(i * 0.8 + t * 5 + k), yy)
        c.drawPath(p, paint(col(SUN, alpha * (0.6 + 0.4 * math.sin(t * 2 + k))), "stroke", 2.5))


def vapor(c, x, y, t, h=160, alpha=255):
    """Vapeur : petits points qui montent en tremblant (particules de la goutte)."""
    for k in range(9):
        u = ((t * 0.5 + k / 9) % 1.0)
        yy = y - u * h
        xx = x + 18 * math.sin(u * 7 + k * 1.3)
        a = alpha * (1 - u)
        c.drawCircle(xx, yy, 4 + 3 * (1 - u), paint(col((170, 225, 255), a)))
        c.drawCircle(xx, yy, 12, paint(col(DROP, 40 * a / 255), blur=8, blend=skia.BlendMode.kPlus))


def rock(c, x, y, s, alpha=255):
    pts = [(-0.55, 0), (-0.45, -0.4), (-0.1, -0.62), (0.35, -0.5), (0.58, -0.12), (0.55, 0)]
    p = skia.Path()
    p.moveTo(x + pts[0][0] * s, y + pts[0][1] * s)
    for px, py in pts[1:]:
        p.lineTo(x + px * s, y + py * s)
    p.close()
    c.drawPath(p, paint(col((0, 0, 0), alpha)))
    glow_path(c, p, LINE, 3.0, glow=0.5, alpha=alpha)
    for px, py in pts[1:-1]:
        dot(c, x + px * s, y + py * s, 5, alpha=alpha)


def sprout(c, x, y, s, alive=0.0, alpha=255):
    """Pousse au trait vert : tige courbée et feuilles tombantes (sèche) → droite et ouvertes (vivante)."""
    bend = (1 - alive)
    green = tuple(a + (b - a) * alive for a, b in zip((150, 140, 90), LEAF))
    stem = skia.Path()
    stem.moveTo(x, y)
    top = (x + 0.35 * s * bend, y - s * (1.0 - 0.3 * bend))
    stem.cubicTo(x, y - 0.5 * s, x + 0.05 * s * bend, y - 0.9 * s, *top)
    glow_path(c, stem, green, 4.0, glow=0.4 + 0.8 * alive, alpha=alpha)
    for side in (-1, 1):
        lx, ly = x + side * 0.01 * s, y - 0.55 * s
        droop = 0.9 * bend - 0.35 * alive
        ang = (-math.pi / 2 + side * (math.pi / 2 - 0.3)) + side * droop
        tip = (lx + math.cos(ang) * 0.42 * s, ly + math.sin(ang) * 0.42 * s)
        leaf = skia.Path()
        leaf.moveTo(lx, ly)
        nx, ny = -(tip[1] - ly) * 0.35, (tip[0] - lx) * 0.35
        mx, my = (lx + tip[0]) / 2, (ly + tip[1]) / 2
        leaf.quadTo(mx + nx, my + ny, *tip)
        leaf.quadTo(mx - nx, my - ny, lx, ly)
        c.drawPath(leaf, paint(col(green, 60 * alive * alpha / 255)))
        glow_path(c, leaf, green, 3.5, glow=0.3 + 0.8 * alive, alpha=alpha)


def cloud(c, x, y, s, frown=0.0, eyes=1.0, alpha=255):
    p = skia.Path()
    for dx, dy, r in [(-0.55, 0.05, 0.32), (-0.2, -0.18, 0.42), (0.25, -0.12, 0.38), (0.6, 0.05, 0.3), (0.0, 0.1, 0.35)]:
        p.addCircle(x + dx * s, y + dy * s, r * s)
    try:
        p = skia.Op(p, skia.Path(), skia.PathOp.kUnion_PathOp) or p
    except Exception:
        pass
    c.drawPath(p, paint(col((20, 26, 36), alpha)))
    glow_path(c, p, LINE, 3.5, glow=0.6, alpha=alpha)
    for side in (-1, 1):
        ex, ey = x + side * 0.2 * s, y - 0.02 * s
        w, h = 0.06 * s, 0.11 * s * eyes
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ex - w / 2, ey - h / 2, ex + w / 2, ey + h / 2), w / 2, w / 2),
                    paint(col((255, 255, 255), alpha)))
        if frown:
            b = skia.Path()
            b.moveTo(ex - side * 0.1 * s, ey - 0.13 * s - 0.03 * s * frown)
            b.lineTo(ex + side * 0.07 * s, ey - 0.1 * s + 0.02 * s * frown)
            c.drawPath(b, paint(col((255, 255, 255), alpha), "stroke", 4))


def rain(c, x0, x1, y0, y1, t, n=70, seed=3, alpha=255):
    r = np.random.default_rng(seed)
    xs, ph, sp = r.uniform(x0, x1, n), r.uniform(0, 1, n), r.uniform(0.9, 1.3, n)
    for x, p, s in zip(xs, ph, sp):
        u = (p + t * s * 0.9) % 1.0
        y = y0 + (y1 - y0) * u
        c.drawLine(x, y, x - 6, y + 34, paint(col(DROP, alpha * (0.5 + 0.5 * (1 - u))), "stroke", 3.5))


def flower(c, x, y, s, bloom=1.0, petals=6, rot=0.0, alpha=255):
    """Fleur géométrique : pétales tracés comme une rosace, qui s'ouvrent."""
    stem = skia.Path()
    stem.moveTo(x, y)
    stem.lineTo(x, y - s * bloom)
    glow_path(c, stem, LEAF, 3.0, glow=0.5, alpha=alpha)
    cy = y - s * bloom
    if bloom <= 0.05:
        return
    for k in range(petals):
        a = rot + 2 * math.pi * k / petals
        pp = skia.Path()
        r = 0.42 * s * bloom
        pp.moveTo(x, cy)
        tip = (x + math.cos(a) * r, cy + math.sin(a) * r)
        n1 = (x + math.cos(a + 0.5) * r * 0.6, cy + math.sin(a + 0.5) * r * 0.6)
        n2 = (x + math.cos(a - 0.5) * r * 0.6, cy + math.sin(a - 0.5) * r * 0.6)
        pp.quadTo(*n1, *tip)
        pp.quadTo(*n2, x, cy)
        c.drawPath(pp, paint(col(DROP, 70 * alpha / 255)))
        glow_path(c, pp, (150, 220, 255), 2.5, glow=0.8, alpha=alpha)
    dot(c, x, cy, 0.07 * s * bloom + 3, rgb=(255, 230, 160), alpha=alpha)
