"""Vague de pendules vue de dessus : ils se désynchronisent en motifs puis se réalignent (boucle parfaite)."""
import math

import numpy as np
import skia

from ..engine import FPS, H, W, Ripples, color, lerp_rgb, paint

TITLE = "Vague de pendules"


def render(ctx):
    rng, pal, pt, v = ctx.rng, ctx.pal, ctx.painter, ctx.video
    T = float(round(ctx.seconds))          # tous les pendules se réalignent à T : la vidéo boucle
    n = int(rng.integers(12, 19))
    k0 = int(rng.integers(22, 34))
    freqs = [(k0 + i) / T for i in range(n)]
    cx = W / 2
    amp = float(rng.uniform(360, 410))
    top, bottom = H / 2 - 60 - 560, H / 2 - 60 + 560
    ys = np.linspace(top, bottom, n)
    bob = min(34.0, (bottom - top) / n * 0.36)
    snake = bool(rng.integers(2))
    reverse = bool(rng.integers(2))
    cols = [lerp_rgb(pal.accents, i / max(1, n - 1)) for i in range(n)]

    hits = {}
    for i, f in enumerate(freqs):
        for j in range(int(T * f) + 1):
            t = j / f
            if t < T:
                ctx.sound.hit(t, 0.8, step=(n - 1 - i) if reverse else i, octave=-1)
                hits.setdefault(int(round(t * FPS)), []).append(i)
    ripples = Ripples(life=0.5, reach=70)
    frames = int(T * FPS)
    history = []
    for fr in range(frames):
        if ctx.done(fr):
            break
        t = fr / FPS
        xs = [cx + amp * math.cos(2 * math.pi * f * t) for f in freqs]
        c = v.canvas
        pt.background(c)
        for i, y in enumerate(ys):
            c.drawLine(cx - amp, y, cx + amp, y, paint(color(pal.rim if not pal.dark else pal.surface, 255),
                                                      "stroke", bob * 0.5))
            c.drawLine(cx - amp, y, cx + amp, y, paint(color(pal.shadow, 25), "stroke", 2))
        for i in hits.get(fr, []):
            ripples.add(cx + amp, ys[i], cols[i], 0.8)
        ripples.draw(c)
        history = (history + [xs])[-8:]
        for h_i, hx in enumerate(history[:-1]):
            a = 60 * (h_i + 1) / len(history)
            for i, y in enumerate(ys):
                c.drawCircle(hx[i], y, bob * 0.8, paint(color(cols[i], a)))
        if snake:
            path = skia.Path()
            path.moveTo(xs[0], ys[0])
            for i in range(1, n):
                my = (ys[i - 1] + ys[i]) / 2
                path.cubicTo(xs[i - 1], my, xs[i], my, xs[i], ys[i])
            c.drawPath(path, paint(color(pal.shadow if not pal.dark else pal.accents[2], 60), "stroke", 3))
        for i, y in enumerate(ys):
            pt.ball(c, xs[i], y, bob, cols[i])
        v.emit()
    return T
