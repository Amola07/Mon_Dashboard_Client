"""Pistes de style pour « Goutte » : la même scène (la goutte sous le soleil, dans les dunes) dans plusieurs styles.

    python -m films.styles.directions <dossier>
"""
import math
import sys
from pathlib import Path

import numpy as np
import skia

W, H = 1080, 1920
rng = np.random.default_rng(3)


# ---------------------------------------------------------------- outils communs
def layer(draw):
    """Dessine une forme blanche sur fond transparent et renvoie son masque (float 0..1)."""
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    draw(c, skia.Paint(AntiAlias=True, Color=skia.ColorWHITE))
    return s.makeImageSnapshot().toarray()[..., 3].astype(np.float32) / 255


def blur(a, r):
    """Flou gaussien (Skia) d'un masque 0..1."""
    if r <= 0:
        return a
    h, w = a.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 3] = np.clip(a * 255, 0, 255).astype(np.uint8)
    rgba[..., :3] = 255
    img = skia.Image.fromarray(rgba, colorType=skia.ColorType.kRGBA_8888_ColorType)
    s = skia.Surface(w, h)
    c = s.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(r, r, skia.TileMode.kClamp))
    c.drawImage(img, 0, 0, skia.SamplingOptions(), p)
    return s.makeImageSnapshot().toarray()[..., 3].astype(np.float32) / 255


def noise(scale, octaves=4, seed=0):
    """Bruit de valeur lissé (texture de papier, granulation)."""
    r = np.random.default_rng(seed)
    total = np.zeros((H, W), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale / 2 ** o))
        small = r.random((H // s + 2, W // s + 2)).astype(np.float32)
        big = np.kron(small, np.ones((s, s), np.float32))[:H, :W]
        total += blur(big, max(1, s // 2)) * amp if s > 2 else big * amp
        norm += amp
        amp *= 0.5
    total /= norm
    return (total - total.min()) / (total.max() - total.min() + 1e-9)


def dune_shape(y, amp, phase, seed):
    def draw(c, p):
        path = skia.Path()
        path.moveTo(-10, H + 10)
        for x in range(-10, W + 20, 12):
            yy = y + amp * math.sin(x * 0.004 + phase) + amp * 0.35 * math.sin(x * 0.011 + seed)
            path.lineTo(x, yy)
        path.lineTo(W + 10, H + 10)
        path.close()
        c.drawPath(path, p)
    return draw


def drop_shape(cx, base, size):
    def draw(c, p):
        path = skia.Path()
        n = 80
        r = size / 2
        pts = []
        for i in range(n + 1):
            a = -math.pi / 2 + 2 * math.pi * i / n
            x, y = math.cos(a) * r, math.sin(a) * r
            up = max(0.0, -y) / r
            x *= 1 - 0.55 * up ** 1.9
            y = y * (1 + 0.5 * up) if y < 0 else y
            pts.append((cx + x, base - r + y))
        path.moveTo(*pts[0])
        for q in pts[1:]:
            path.lineTo(*q)
        path.close()
        c.drawPath(path, p)
    return draw


def circle(cx, cy, r):
    return lambda c, p: c.drawCircle(cx, cy, r, p)


def eyes_smile(cx, base, size):
    def draw(c, p):
        ey = base - size * 0.5
        for side in (-1, 1):
            w, h = size * 0.08, size * 0.14
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx + side * size * 0.17 - w / 2, ey - h / 2, w, h), w / 2, w / 2), p)
        m = skia.Path()
        m.moveTo(cx - size * 0.09, ey + size * 0.19)
        m.quadTo(cx, ey + size * 0.28, cx + size * 0.09, ey + size * 0.19)
        q = skia.Paint(p)
        q.setStyle(skia.Paint.kStroke_Style)
        q.setStrokeWidth(size * 0.03)
        q.setStrokeCap(skia.Paint.kRound_Cap)
        c.drawPath(m, q)
    return draw


def save(img, path):
    img = np.clip(img, 0, 1)
    rgba = np.dstack([(img * 255).astype(np.uint8), np.full((H, W), 255, np.uint8)])
    skia.Image.fromarray(rgba, colorType=skia.ColorType.kRGBA_8888_ColorType).save(str(path), skia.kPNG)


def rgb(*c):
    return np.array(c, np.float32) / 255


SCENE = dict(sun=(760, 520, 150), drop=(470, 1390, 330))
DUNES = [(1060, 70, 0.3, 1), (1230, 55, 2.0, 2), (1400, 45, 4.1, 3)]


# ---------------------------------------------------------------- 1. aquarelle
def aquarelle(out):
    paper = noise(60, 5, 1) * 0.06 + noise(4, 2, 2) * 0.05
    img = np.ones((H, W, 3), np.float32) * rgb(248, 240, 226) - paper[..., None]
    sky = np.linspace(0, 1, H)[:, None, None]
    img *= 1 - (1 - (rgb(250, 214, 170) * (1 - sky * 0.6) + rgb(246, 236, 222) * sky * 0.6)) * 0.55

    def wash(mask, color, strength=0.85, edge=1.0, gran=0.35, seed=0):
        nonlocal img
        soft = blur(mask, 3)
        g = noise(18, 3, seed)
        edge_dark = np.clip(soft - blur(soft, 14), 0, 1) * 2.2 * edge      # le pigment s'accumule au bord
        a = np.clip(soft * strength * (0.75 + gran * (g - 0.5)) + edge_dark * strength, 0, 1)
        img = img * (1 - a[..., None] * (1 - color))                      # peinture = multiplication

    sx, sy, sr = SCENE["sun"]
    wash(layer(circle(sx, sy, sr)), rgb(250, 170, 70), 0.75, seed=4)
    wash(blur(layer(circle(sx, sy, sr * 1.8)), 40), rgb(252, 205, 140), 0.35, edge=0, seed=5)
    for i, (y, amp, ph, sd) in enumerate(DUNES):
        wash(layer(dune_shape(y, amp, ph, sd)), rgb(236, 176, 118) * (1 - 0.08 * i), 0.55 + 0.1 * i, seed=10 + i)
    cx, base, size = SCENE["drop"]
    m = layer(drop_shape(cx, base, size))
    wash(blur(np.roll(m, (20, -12), (0, 1)), 18) * 0.8, rgb(150, 120, 110), 0.35, edge=0, seed=6)   # ombre douce
    wash(m, rgb(70, 150, 230), 0.8, edge=1.3, gran=0.5, seed=7)
    hl = layer(circle(cx - size * 0.16, base - size * 0.72, size * 0.09))                    # papier réservé = reflet
    img = img * (1 - hl[..., None]) + hl[..., None] * rgb(250, 248, 242)
    ink = layer(eyes_smile(cx, base, size))
    img = img * (1 - ink[..., None] * 0.92) + ink[..., None] * rgb(30, 40, 60) * 0.92
    save(img, out / "1_aquarelle.png")


# ---------------------------------------------------------------- 2. papier découpé rétroéclairé
def papier(out):
    fibre = noise(3, 2, 11) * 0.06 + noise(40, 3, 12) * 0.05
    img = np.ones((H, W, 3), np.float32) * rgb(255, 196, 140)
    sky = np.linspace(0, 1, H)[:, None, None]
    img = img * (1 - sky) + rgb(255, 150, 120) * sky
    img -= fibre[..., None] * 0.6

    def cut(mask, color, depth=1.0, seed=0):
        nonlocal img
        shadow = blur(np.roll(mask, (int(14 * depth), int(8 * depth)), (0, 1)), int(10 * depth))
        img *= 1 - shadow[..., None] * 0.45
        tex = 1 - (noise(3, 2, seed) * 0.07 + noise(30, 2, seed + 1) * 0.05)
        m = mask[..., None]
        img = img * (1 - m) + m * color * tex[..., None]
        rim = np.clip(mask - blur(mask, 2), 0, 1)                                           # bord du papier éclairé
        img += rim[..., None] * 0.25

    sx, sy, sr = SCENE["sun"]
    halo = blur(layer(circle(sx, sy, sr * 1.6)), 50)
    img += halo[..., None] * rgb(255, 230, 170) * 0.35
    cut(layer(circle(sx, sy, sr)), rgb(255, 238, 190), 0.6, seed=20)
    cols = [rgb(236, 128, 96), rgb(210, 96, 84), rgb(170, 70, 80)]
    for (y, amp, ph, sd), cc in zip(DUNES, cols):
        cut(layer(dune_shape(y, amp, ph, sd)), cc, 1.2, seed=sd * 7)
    cx, base, size = SCENE["drop"]
    cut(layer(drop_shape(cx, base, size)), rgb(80, 175, 240), 1.6, seed=30)
    inner = layer(drop_shape(cx - size * 0.05, base - size * 0.1, size * 0.72))
    cut(inner * layer(drop_shape(cx, base, size)), rgb(140, 210, 255), 0.5, seed=31)
    ink = layer(eyes_smile(cx, base, size))
    img = img * (1 - ink[..., None]) + ink[..., None] * rgb(40, 40, 70)
    save(img, out / "2_papier_decoupe.png")


# ---------------------------------------------------------------- 3. risographie (deux encres, trame, décalage)
def riso(out):
    paper = rgb(246, 240, 228) - (noise(3, 2, 40) * 0.05)[..., None]
    pink, blue = rgb(255, 72, 150), rgb(40, 110, 230)

    def halftone(tone, cell=10, angle=0.3):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        u = xx * math.cos(angle) + yy * math.sin(angle)
        v = -xx * math.sin(angle) + yy * math.cos(angle)
        d = np.hypot((u % cell) - cell / 2, (v % cell) - cell / 2) / (cell * 0.7071)
        return (d < np.sqrt(np.clip(tone, 0, 1)) * 1.0).astype(np.float32)

    sx, sy, sr = SCENE["sun"]
    cx, base, size = SCENE["drop"]
    ink_p = np.zeros((H, W), np.float32)
    ink_b = np.zeros((H, W), np.float32)
    ink_p = np.maximum(ink_p, layer(circle(sx, sy, sr)))
    ink_p = np.maximum(ink_p, halftone(blur(layer(circle(sx, sy, sr * 1.9)), 30) * 0.6, 12))
    for i, (y, amp, ph, sd) in enumerate(DUNES):
        m = layer(dune_shape(y, amp, ph, sd))
        ink_p = np.maximum(ink_p, halftone(m * (0.35 + 0.2 * i), 9, 0.25))
        if i == 2:
            ink_b = np.maximum(ink_b, halftone(m * 0.3, 9, 1.1))
    d = layer(drop_shape(cx, base, size))
    ink_b = np.maximum(ink_b, d)
    ink_b = np.clip(ink_b - layer(circle(cx - size * 0.16, base - size * 0.72, size * 0.09)), 0, 1)
    face = layer(eyes_smile(cx, base, size))
    ink_b = np.clip(ink_b - face, 0, 1)
    ink_p = np.roll(ink_p, (5, -4), (0, 1))                                                 # repérage imparfait
    grain = 0.85 + 0.15 * noise(2, 1, 41)
    img = paper * (1 - (ink_p * grain)[..., None] * (1 - pink)) * (1 - (ink_b * grain)[..., None] * (1 - blue))
    save(img, out / "3_risographie.png")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    for fn in (aquarelle, papier, riso):
        fn(out)
        print("ok", fn.__name__, flush=True)
