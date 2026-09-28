"""Chaque rebond fait naître une nouvelle balle, le cercle se remplit, puis toutes se rejoignent en une seule (boucle)."""
import math

import numpy as np
import skia

from ..engine import FPS, H, W, Ripples, paint

TITLE = "Balles qui se multiplient"
SUBSTEPS = 8


def render(ctx):
    rng, pal, pt, v = ctx.rng, ctx.pal, ctx.painter, ctx.video
    cx, cy, R = W / 2, H / 2 - 60, float(rng.uniform(420, 460))
    r = float(rng.uniform(13, 19))
    cap = int(rng.integers(70, 130))
    gravity = float(rng.uniform(1000, 1500))
    speed_min = float(rng.uniform(650, 850))
    start = np.array([cx, cy - R * 0.5])
    grow_s = ctx.seconds - 2.6
    interval = (grow_s - 4) / cap
    pos = start[None, :].copy()
    vel = np.array([[rng.uniform(-350, 350), 0.0]])
    col_idx = [0]
    last_spawn = -10.0
    ripples = Ripples(life=0.55, reach=90)
    dt = 1 / FPS / SUBSTEPS
    n_grow = int(grow_s * FPS)
    n_out = int(2.6 * FPS)
    end_pos = None
    for f in range(n_grow + n_out):
        if ctx.done(f):
            break
        t = f / FPS
        if f < n_grow:
            for _ in range(SUBSTEPS):
                vel[:, 1] += gravity * dt
                pos += vel * dt
                d = pos - (cx, cy)
                dist = np.hypot(d[:, 0], d[:, 1])
                hit = dist + r >= R
                if not hit.any():
                    continue
                n = d[hit] / dist[hit, None]
                pos[hit] = (cx, cy) + n * (R - r - 0.5)
                vn = (vel[hit] * n).sum(1)
                out = vn > 0
                idx = np.where(hit)[0][out]
                n, vn = n[out], vn[out]
                if not len(idx):
                    continue
                vel[idx] -= 2 * vn[:, None] * n
                kick = rng.uniform(-60, 60, len(idx))
                vel[idx] += np.column_stack([-n[:, 1], n[:, 0]]) * kick[:, None]
                sp = np.hypot(vel[idx, 0], vel[idx, 1])
                vel[idx] *= (np.maximum(sp, speed_min) / sp)[:, None]
                if len(pos) < cap and t - last_spawn >= interval:
                    j = int(idx[0])
                    ang = rng.uniform(0.3, 0.8) * (1 if rng.integers(2) else -1)
                    cs, sn = math.cos(ang), math.sin(ang)
                    nv = np.array([vel[j, 0] * cs - vel[j, 1] * sn, vel[j, 0] * sn + vel[j, 1] * cs])
                    pos = np.vstack([pos, pos[j]])
                    vel = np.vstack([vel, nv])
                    col_idx.append(len(col_idx) % len(pal.accents))
                    last_spawn = t
                    ctx.sound.hit(t, min(1.0, vn[0] / 1200))
                    p = (cx, cy) + n[0] * R
                    ripples.add(p[0], p[1], pal.accents[col_idx[-1]], 0.8)
            draw_pos = pos
        else:
            if end_pos is None:
                end_pos = pos.copy()
                for k, st in enumerate([4, 3, 2, 1, 0]):
                    ctx.sound.hit(t + 0.1 + k * 0.4, 0.8, step=st + 5)
            u = (f - n_grow) / n_out
            e = u * u * (3 - 2 * u)
            draw_pos = end_pos * (1 - e) + start * e
        c = v.canvas
        pt.background(c)
        pt.container(c, cx, cy, R)
        c.save()
        c.clipPath(skia.Path.Circle(cx, cy, R), doAntiAlias=True)
        ripples.draw(c)
        for k in range(len(draw_pos) - 1, -1, -1):
            pt.ball(c, draw_pos[k, 0], draw_pos[k, 1], r, pal.accents[col_idx[k]], shadow=True)
        c.restore()
        v.emit()
    return (n_grow + n_out) / FPS
