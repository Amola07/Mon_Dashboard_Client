"""Océan de nuit : houle en couches sous la lune et son reflet qui scintille (boucle parfaite)."""
import math

import numpy as np
import skia

from ..engine import FPS, H, W, color, lerp_rgb, paint

TITLE = "Océan sous la lune"


def render(ctx):
    rng, pal, pt, v = ctx.rng, ctx.pal, ctx.painter, ctx.video
    T = float(round(ctx.seconds))
    horizon = float(rng.uniform(760, 900))
    moon_x, moon_y = float(rng.uniform(0.3, 0.7) * W), float(rng.uniform(360, horizon - 220))
    moon_r = float(rng.uniform(55, 85))
    moon_rgb = lerp_rgb([(255, 250, 235), pal.accents[int(rng.integers(len(pal.accents)))]], 0.25)
    water_rgb = max(pal.accents, key=lambda q: q[2] - q[0])   # la teinte la plus bleue de la palette
    L = int(rng.integers(12, 17))
    xs = np.linspace(-20, W + 20, 140)
    layers = []
    for k in range(L):
        u = (k + 1) / L
        base = horizon + (H + 40 - horizon) * u ** 1.5
        amp = 3 + 55 * u ** 1.5
        comps = []
        for j in range(3):
            cycles = int(rng.integers(1, 4)) * (1 if rng.integers(2) else -1)   # entier : boucle exacte
            wl = float(rng.uniform(260, 700)) * (0.4 + u)
            comps.append((amp * (0.6, 0.3, 0.15)[j], 2 * math.pi / wl, 2 * math.pi * cycles / T,
                          float(rng.uniform(0, 2 * math.pi))))
        fill = lerp_rgb([(12, 26, 48), water_rgb], 0.10 + 0.08 * (1 - u))
        fill = tuple(c * (1.15 - 0.55 * u) for c in fill)   # plus clair au loin, plus sombre devant
        layers.append((base, comps, fill, u))
    swell = 2 * math.pi * int(rng.integers(6, 10)) / T

    # sons : ressac continu qui suit la houle, notes rares et douces
    frames = int(T * FPS)
    env = np.array([0.55 + 0.45 * (0.5 + 0.5 * math.sin(swell * f / FPS)) for f in range(frames)])
    ctx.sound.bed("océan", env, level=1.3)
    t = float(rng.uniform(0.3, 1.0))
    while t < T - 1:
        ctx.sound.hit(t, float(rng.uniform(0.4, 0.8)))
        t += float(rng.uniform(1.1, 2.4))

    dash_y = np.sort(rng.uniform(horizon + 4, H, 90))
    dash_ph = rng.uniform(0, 2 * math.pi, len(dash_y))
    for f in range(frames):
        if ctx.done(f):
            break
        t = f / FPS
        c = v.canvas
        pt.background(c)
        # lune et halo
        c.drawCircle(moon_x, moon_y, moon_r * 3.2, paint(shader=skia.GradientShader.MakeRadial(
            (moon_x, moon_y), moon_r * 3.2, [color(moon_rgb, 60), color(moon_rgb, 0)])))
        c.drawCircle(moon_x, moon_y, moon_r, paint(shader=skia.GradientShader.MakeRadial(
            (moon_x - moon_r * 0.3, moon_y - moon_r * 0.3), moon_r * 1.4,
            [color(moon_rgb, 255, 1.05), color(moon_rgb, 255, 0.9)])))
        # mer : fond, puis couches de l'horizon vers le bas
        c.drawRect(skia.Rect.MakeLTRB(0, horizon, W, H), paint(color(layers[0][2])))
        sw = 0.85 + 0.15 * math.sin(swell * t)
        for k, (base, comps, fill, u) in enumerate(layers):
            ys = base + sum(a * sw * np.sin(kx * xs - w * t + ph) for a, kx, w, ph in comps)
            path = skia.Path()
            path.moveTo(xs[0], H + 10)
            for x, y in zip(xs, ys):
                path.lineTo(x, y)
            path.lineTo(xs[-1], H + 10)
            path.close()
            c.drawPath(path, paint(color(fill)))
            crest = skia.Path()
            crest.moveTo(xs[0], ys[0])
            for x, y in zip(xs[1:], ys[1:]):
                crest.lineTo(x, y)
            c.drawPath(crest, paint(color(lerp_rgb([water_rgb, moon_rgb], 0.5), 25 + 55 * u), "stroke",
                                    1.0 + 1.6 * u))
            # reflet de la lune sur cette couche
            dx = moon_x - xs[0]
            i = int(dx / (xs[1] - xs[0]))
            if 0 <= i < len(ys):
                yref = ys[i]
                wdt = (18 + 90 * u) * (0.6 + 0.4 * math.sin(t * 1.3 + k))
                c.drawOval(skia.Rect.MakeLTRB(moon_x - wdt, yref - 2 - 3 * u, moon_x + wdt, yref + 2 + 3 * u),
                           paint(color(moon_rgb, 90 + 80 * u), blur=2 + 3 * u))
        # scintillement du reflet
        for y, ph in zip(dash_y, dash_ph):
            u = (y - horizon) / (H - horizon)
            a = max(0.0, math.sin(ph + t * 2.1)) ** 2
            if a < 0.05:
                continue
            x = moon_x + math.sin(ph * 3 + t * 0.8) * (10 + 110 * u)
            w_ = 6 + 40 * u
            c.drawLine(x - w_, y, x + w_, y, paint(color(moon_rgb, 150 * a), "stroke", 1.5 + 2 * u,
                                                   blend=skia.BlendMode.kPlus))
        v.emit()
    return T
