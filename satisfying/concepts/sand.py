"""Art du sable : du sable coloré coule dans un cadre de verre et forme des dunes en couches, puis s'écoule (boucle)."""
import math

import numpy as np
import skia

from ..engine import FPS, H, W, color, lerp_rgb, paint, smooth

TITLE = "Dunes de sable coloré"
CELL = 4


def _step(grid, cols, rng, floor_open):
    """Une passe de chute : chaque grain descend, sinon glisse en diagonale (pente naturelle des dunes)."""
    gh, gw = grid.shape
    if floor_open:
        grid[-1] = False
    for y in range(gh - 2, -1, -1):
        row, below = grid[y], grid[y + 1]
        fall = row & ~below
        if fall.any():
            below |= fall
            cols[y + 1][fall] = cols[y][fall]
            row &= ~fall
        stuck = row & below
        if not stuck.any():
            continue
        left_first = rng.random(gw) < 0.5
        for d in ((-1, 1) if rng.random() < 0.5 else (1, -1)):
            cand = stuck & (left_first if d == -1 else ~left_first) | (stuck & (rng.random(gw) < 0.15))
            if d == -1:
                ok = np.zeros(gw, bool)
                ok[1:] = cand[1:] & ~below[:-1]
                idx = np.where(ok)[0]
                tgt = idx - 1
            else:
                ok = np.zeros(gw, bool)
                ok[:-1] = cand[:-1] & ~below[1:]
                idx = np.where(ok)[0]
                tgt = idx + 1
            if len(idx):
                below[tgt] = True
                cols[y + 1][tgt] = cols[y][idx]
                row[idx] = False
                stuck[idx] = False


def render(ctx):
    rng, pal, pt, v = ctx.rng, ctx.pal, ctx.painter, ctx.video
    fw, fh = 760, 1160
    fx, fy = (W - fw) / 2, (H - fh) / 2 - 40
    gw, gh = fw // CELL, fh // CELL
    grid = np.zeros((gh, gw), bool)
    cols = np.zeros((gh, gw, 3), np.uint8)
    fill_s = ctx.seconds - 2.8
    n_fill = int(fill_s * FPS)
    n_drain = int(2.8 * FPS)
    target = gw * gh * float(rng.uniform(0.78, 0.86))
    per_frame = target / (n_fill - 30)
    steps = 3
    layer_s = float(rng.uniform(3.2, 5.0))
    order = list(rng.permutation(len(pal.accents)))
    nozzles = int(rng.integers(1, 3))
    phases = rng.uniform(0, 2 * math.pi, (nozzles, 3))
    speeds = rng.uniform(0.08, 0.2, (nozzles, 3))
    stream = np.zeros(n_fill + n_drain)

    def nozzle_x(k, t):
        u = sum(math.sin(2 * math.pi * speeds[k, j] * t + phases[k, j]) / (j + 1) for j in range(3)) / 1.83
        return int((0.5 + 0.44 * u) * (gw - 1))

    last_layer = -1
    img = np.zeros((gh, gw, 4), np.uint8)
    carry = 0.0
    for f in range(n_fill + n_drain):
        if ctx.done(f):
            break
        t = f / FPS
        pouring = f < n_fill - 30
        if pouring:
            layer = int(t / layer_s)
            if layer != last_layer:
                last_layer = layer
                ctx.sound.hit(t, 0.9)
            u = (t % layer_s) / layer_s
            a = pal.accents[order[layer % len(order)]]
            b = pal.accents[order[(layer + 1) % len(order)]]
            base = lerp_rgb([a, b], smooth((u - 0.8) / 0.2))
            carry += per_frame
            n = int(carry)
            carry -= n
            for k in range(nozzles):
                x0 = nozzle_x(k, t)
                m = n // nozzles
                xs = np.clip(x0 + rng.integers(-2, 3, m), 0, gw - 1)
                surface = np.where(grid.any(0), grid.argmax(0), gh)   # le filet arrive directement sur le tas
                ys = surface[xs] - 1 - rng.integers(0, 3, m)
                ok = ys >= 0
                xs, ys = xs[ok], ys[ok]
                free = ~grid[ys, xs]
                xs, ys = xs[free], ys[free]
                grid[ys, xs] = True
                shade = rng.uniform(0.82, 1.08, (len(xs), 1))
                cols[ys, xs] = np.clip(np.array(base)[None, :] * shade, 0, 255).astype(np.uint8)
            stream[f] = 1.0
        else:
            stream[f] = 0.0
        for _ in range(steps):
            _step(grid, cols, rng, floor_open=f >= n_fill)
        if f >= n_fill:
            stream[f] = min(1.0, grid.sum() / (gw * gh * 0.3)) * 1.4
        c = v.canvas
        pt.background(c)
        # cadre de verre
        rect = skia.Rect.MakeXYWH(fx - 14, fy - 14, fw + 28, fh + 28)
        c.drawRRect(skia.RRect.MakeRectXY(rect, 26, 26), paint(color(pal.surface, 170)))
        c.drawRRect(skia.RRect.MakeRectXY(rect, 26, 26), paint(color(pal.rim, 255), "stroke", 4))
        img[..., :3] = cols
        img[..., 3] = np.where(grid, 255, 0)
        im = skia.Image.fromarray(img, colorType=skia.ColorType.kRGBA_8888_ColorType)
        c.drawImageRect(im, skia.Rect.MakeXYWH(fx, fy, fw, fh), skia.SamplingOptions(skia.FilterMode.kNearest))
        # filet de sable qui tombe
        if pouring:
            for k in range(nozzles):
                x = fx + (nozzle_x(k, t) + 0.5) * CELL
                col_now = tuple(int(q) for q in base)
                top = fy - 14
                heights = np.where(grid[:, nozzle_x(k, t)])[0]
                bottom = fy + (heights[0] if len(heights) else gh) * CELL
                c.drawLine(x, 0, x, bottom, paint(color(col_now, 120), "stroke", 3.5))
                c.drawLine(x, 0, x, top, paint(color(col_now, 220), "stroke", 3.5))
        # reflet du verre
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(fx + 16, fy + 20, 18, fh - 40), 9, 9),
                    paint(skia.Color(255, 255, 255, 22)))
        v.emit()
    ctx.sound.bed("sable", stream, level=0.9)
    return (n_fill + n_drain) / FPS
