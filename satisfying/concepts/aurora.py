"""Aurore boréale : des voiles de lumière ondulent au-dessus des montagnes, sous les étoiles (boucle parfaite)."""
import math

import numpy as np
import skia

from ..engine import FPS, H, W, color, paint

TITLE = "Aurore boréale"
SCALE = 4   # l'aurore est dessinée en basse résolution puis agrandie : flou naturel


def _ridge(rng, base, amp, n=200):
    xs = np.linspace(0, W, n)
    ys = np.full(n, base, float)
    for j in range(5):
        ys += amp / (j + 1) * np.sin(xs * rng.uniform(0.002, 0.004) * (j + 1) + rng.uniform(0, 6.28))
    return xs, ys


def render(ctx):
    rng, pal, pt, v = ctx.rng, ctx.pal, ctx.painter, ctx.video
    T = float(round(ctx.seconds))
    frames = int(T * FPS)
    lw, lh = W // SCALE, H // SCALE
    low = skia.Surface(lw, lh)
    n_rib = int(rng.integers(2, 4))
    ribbons = []
    for i in range(n_rib):
        base = float(rng.uniform(0.34, 0.55)) * lh
        height = float(rng.uniform(0.16, 0.3)) * lh
        waves = [(float(rng.uniform(5, 14)) / (j + 1), 2 * math.pi / float(rng.uniform(380, 900)) * (j + 1),
                  2 * math.pi * int(rng.integers(1, 4)) * (1 if rng.integers(2) else -1) / T,
                  float(rng.uniform(0, 6.28))) for j in range(3)]
        c1, c2 = rng.choice(len(pal.accents), 2, replace=False)
        ribbons.append((base, height, waves, pal.accents[int(c1)], pal.accents[int(c2)],
                        2 * math.pi * int(rng.integers(2, 6)) / T, float(rng.uniform(0.02, 0.06))))
    ridges = [_ridge(rng, H * (0.72 + 0.07 * k), 90 - 20 * k) for k in range(3)]
    ridge_cols = [tuple(q * (0.35 + 0.18 * k) for q in pal.bg[1]) for k in range(3)]

    ctx.sound.bed("vent", np.ones(frames) * 0.6, level=0.7)
    t = float(rng.uniform(0.3, 1.2))
    while t < T - 1:
        ctx.sound.hit(t, float(rng.uniform(0.4, 0.8)))
        t += float(rng.uniform(1.4, 3.0))

    xs = np.arange(0, lw, 1.0)
    for f in range(frames):
        if ctx.done(f):
            break
        t = f / FPS
        lc = low.getCanvas()
        lc.clear(skia.ColorTRANSPARENT)
        for base, height, waves, ca, cb, pulse_w, ray_k in ribbons:
            yb = base + sum(a * np.sin(k * xs * SCALE + w * t + ph) for a, k, w, ph in waves)
            hh = height * (0.65 + 0.35 * np.sin(xs * SCALE * 0.004 + pulse_w * t))
            rays = 0.55 + 0.45 * np.sin(xs * SCALE * ray_k + pulse_w * 3 * t) ** 2
            for x, y0, h, r in zip(xs, yb, hh, rays):
                sh = skia.GradientShader.MakeLinear([(x, y0), (x, y0 - h)],
                                                    [color(ca, 95 * r), color(cb, 55 * r), color(cb, 0)],
                                                    [0.0, 0.35, 1.0])
                lc.drawLine(x, y0 + 2, x, y0 - h, paint(shader=sh, style="stroke", width=1.0,
                                                        blend=skia.BlendMode.kPlus))
        c = v.canvas
        pt.background(c)
        c.drawImageRect(low.makeImageSnapshot(), skia.Rect.MakeWH(W, H), skia.SamplingOptions(skia.FilterMode.kLinear),
                        paint(blend=skia.BlendMode.kPlus))
        for (rx, ry), rc in zip(ridges, ridge_cols):
            path = skia.Path()
            path.moveTo(0, H)
            for x, y in zip(rx, ry):
                path.lineTo(x, y)
            path.lineTo(W, H)
            path.close()
            c.drawPath(path, paint(color(rc)))
        v.emit()
    return T
