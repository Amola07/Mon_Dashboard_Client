"""Spirographe : des bras qui tournent dessinent lentement une rosace, puis elle s'efface (boucle)."""
import math

import numpy as np
import skia

from ..engine import FPS, H, W, color, lerp_rgb, paint, smooth

TITLE = "Rosace de spirographe"
SAMPLES = 48


def render(ctx):
    rng, pal, pt, v = ctx.rng, ctx.pal, ctx.painter, ctx.video
    cx, cy, R = W / 2, H / 2 - 60, 470.0
    m = int(rng.integers(18, 55)) * (1 if rng.integers(2) else -1)
    q = int(rng.integers(2, 7)) * m + int(rng.integers(-3, 4))
    if q in (0, 1):
        q = 3 * m
    a = np.array([rng.uniform(0.45, 0.62), rng.uniform(0.2, 0.34), rng.uniform(0.04, 0.12)])
    a = a / a.sum() * (R - 40)
    freqs = [1, m, q]
    phases = rng.uniform(0, 2 * math.pi, 3)
    draw_s = ctx.seconds - 3.0
    fade_s = 3.0
    total = int((draw_s + fade_s) * FPS)
    width = float(rng.uniform(2.2, 3.6))

    def point(tau):
        z = sum(a[k] * np.exp(1j * (freqs[k] * tau + phases[k])) for k in range(3))
        return cx + z.real, cy + z.imag

    # sons : pointes et creux de la rosace (extrêmes du rayon)
    taus = np.linspace(0, 2 * math.pi, int(draw_s * FPS) * SAMPLES)
    z2 = sum(a[k] * np.exp(1j * (freqs[k] * taus + phases[k])) for k in range(2))  # sans le petit bras
    rad = np.abs(z2)
    tips = np.where((rad[1:-1] > rad[:-2]) & (rad[1:-1] >= rad[2:]))[0] + 1
    dips = np.where((rad[1:-1] < rad[:-2]) & (rad[1:-1] <= rad[2:]))[0] + 1
    for idx in tips:
        ctx.sound.hit(taus[idx] / (2 * math.pi) * draw_s, 0.9)
    for idx in dips:
        ctx.sound.hit(taus[idx] / (2 * math.pi) * draw_s, 0.5, octave=-1)
    tip_frames = {int(taus[i] / (2 * math.pi) * draw_s * FPS) for i in tips}

    layer = skia.Surface(W, H)
    layer.getCanvas().clear(skia.ColorTRANSPARENT)
    prev = point(0.0)
    glow = 0.0
    for f in range(total):
        if ctx.done(f):
            break
        u = min(1.0, (f + 1) / (draw_s * FPS))
        tau = 2 * math.pi * u
        lc = layer.getCanvas()
        if f < draw_s * FPS:
            t0 = 2 * math.pi * f / (draw_s * FPS)
            ts = np.linspace(t0, tau, SAMPLES + 1)
            px, py = point(ts)
            rgb = lerp_rgb(pal.accents + pal.accents[:1], u)
            path = skia.Path()
            path.moveTo(*prev)
            for i in range(1, len(ts)):
                path.lineTo(px[i], py[i])
            lc.drawPath(path, paint(color(rgb, 215), "stroke", width))
            prev = (px[-1], py[-1])
        if f in tip_frames:
            glow = 1.0
        glow *= 0.9
        c = v.canvas
        pt.background(c)
        pt.container(c, cx, cy, R)
        fade = 1 - smooth((f - draw_s * FPS) / (fade_s * FPS * 0.8)) if f >= draw_s * FPS else 1.0
        if fade > 0:
            c.drawImage(layer.makeImageSnapshot(), 0, 0, skia.SamplingOptions(), paint(skia.Color(0, 0, 0, int(255 * fade))))
        # bras articulés
        z0 = complex(cx, cy)
        pts = [z0]
        for k in range(3):
            pts.append(pts[-1] + a[k] * complex(math.cos(freqs[k] * tau + phases[k]), math.sin(freqs[k] * tau + phases[k])))
        arm = color(pal.shadow if not pal.dark else pal.rim, 110)
        for k in range(3):
            c.drawLine(pts[k].real, pts[k].imag, pts[k + 1].real, pts[k + 1].imag, paint(arm, "stroke", 3))
        for k in range(3):
            c.drawCircle(pts[k].real, pts[k].imag, 6, paint(arm))
        rgb = lerp_rgb(pal.accents + pal.accents[:1], u)
        pt.ball(c, pts[3].real, pts[3].imag, 11 + 3 * glow, rgb)
        v.emit()
    return total / FPS
