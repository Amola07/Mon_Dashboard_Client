"""Une balle s'échappe d'anneaux qui tournent : chaque anneau franchi éclate en billes."""
import math

import numpy as np
import skia

from ..engine import FPS, H, W, Particles, Ripples, color, lerp_rgb, paint, smooth

TITLE = "Évasion des anneaux qui tournent"
SUBSTEPS = 10


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _simulate(rings, gap, cx, cy, r, gravity, speed_min, seed, max_frames):
    rng = np.random.default_rng(seed)
    pos, vel = [cx + 10.0, cy - 20.0], [rng.uniform(-300, 300), -200.0]
    k, passing = 0, False
    frames, bounces, breaks = [], [], []
    dt = 1 / FPS / SUBSTEPS
    for f in range(max_frames):
        for sub in range(SUBSTEPS):
            t = (f + sub / SUBSTEPS) / FPS
            vel[1] += gravity * dt
            pos[0] += vel[0] * dt
            pos[1] += vel[1] * dt
            if k >= len(rings):
                continue
            Rk, a0, w = rings[k]
            dx, dy = pos[0] - cx, pos[1] - cy
            dist = math.hypot(dx, dy)
            if passing:
                if dist - r > Rk + 8:
                    breaks.append((t, k))
                    k, passing = k + 1, False
                elif dist + r < Rk:
                    passing = False
                continue
            if dist + r >= Rk:
                diff = _wrap(math.atan2(dy, dx) - (a0 + w * t))
                if abs(diff) < gap / 2 - r / Rk:
                    passing = True
                    continue
                n = (dx / dist, dy / dist)
                pos[0], pos[1] = cx + n[0] * (Rk - r - 0.5), cy + n[1] * (Rk - r - 0.5)
                vn = vel[0] * n[0] + vel[1] * n[1]
                if vn > 0:
                    vel[0] -= 2 * vn * n[0]
                    vel[1] -= 2 * vn * n[1]
                    kick = rng.uniform(-60, 60)
                    vel[0] += -n[1] * kick
                    vel[1] += n[0] * kick
                    s = math.hypot(*vel)
                    vel[0] *= max(s, speed_min) / s
                    vel[1] *= max(s, speed_min) / s
                    bounces.append((t, (cx + n[0] * Rk, cy + n[1] * Rk), min(1.0, vn / 1200), k))
        frames.append((tuple(pos), k))
        if k >= len(rings) and (f / FPS) > breaks[-1][0] + 0.8:
            break
    return frames, bounces, breaks


def render(ctx):
    rng, pal, pt, v = ctx.rng, ctx.pal, ctx.painter, ctx.video
    cx, cy = W / 2, H / 2 - 60
    n = int(rng.integers(7, 11))
    r_in, r_out = float(rng.uniform(85, 110)), float(rng.uniform(440, 480))
    radii = np.linspace(r_in, r_out, n)
    base_w = float(rng.uniform(0.5, 1.0))
    rings = [(float(Rk), float(rng.uniform(0, 2 * math.pi)), base_w * (1 if i % 2 else -1) * rng.uniform(0.8, 1.3))
             for i, Rk in enumerate(radii)]
    ball_r, gravity, speed_min = float(rng.uniform(11, 16)), float(rng.uniform(900, 1300)), float(rng.uniform(650, 850))
    goal = ctx.seconds - 3.2
    best = None
    for attempt in range(6):   # la trajectoire est chaotique : on essaie plusieurs départs et ouvertures
        seed = int(rng.integers(1 << 30))
        for gap in np.linspace(0.07, 0.9, 42):
            fr, bo, br = _simulate(rings, gap, cx, cy, ball_r, gravity, speed_min, seed, 90 * FPS)
            if len(br) < n:
                if best is None:
                    best = (1e9, gap, fr, bo, br)
                continue
            d = br[-1][0]
            score = abs(d - goal) + (100 if d < goal - 3 else 0)
            if best is None or score < best[0]:
                best = (score, gap, fr, bo, br)
        if best[0] < 1.5:
            break
    _, gap, frames, bounces, breaks = best
    print(f"  évasion en {breaks[-1][0] if breaks else 0:.1f} s (ouverture {math.degrees(gap):.0f}°)", flush=True)
    n = len(breaks)                       # (cas extrême : la balle n'est pas sortie de tous les anneaux)
    rings = rings[:max(n, 1)]
    width = float(rng.uniform(12, 18))

    by_frame_b, by_frame_k = {}, {}
    for t, p, s, k in bounces:
        by_frame_b.setdefault(int(t * FPS), []).append((p, s, k))
        ctx.sound.hit(t, s)
    for t, k in breaks:
        by_frame_k.setdefault(int(t * FPS), []).append(k)
        ctx.sound.hit(t, 1.0, step=5 + k)
    esc = len(frames)
    n_out = int(2.4 * FPS)
    total = esc + n_out
    ring_rgb = [lerp_rgb(pal.accents, i / max(1, n - 1)) for i in range(n)]
    parts, ripples = Particles(gravity=500), Ripples(life=0.6, reach=120)
    broken = set()
    for f in range(total):
        if ctx.done(f):
            break
        t = f / FPS
        c = v.canvas
        pt.background(c)
        for p, s, k in by_frame_b.get(f, []):
            ripples.add(p[0], p[1], ring_rgb[k], 0.4 + 0.6 * s)
        for k in by_frame_k.get(f, []):
            broken.add(k)
            Rk = rings[k][0]
            m = int(40 + Rk / 6)
            ang = np.linspace(0, 2 * math.pi, m, endpoint=False) + rng.uniform(0, 1)
            sp = rng.uniform(80, 260, m)
            parts.burst(cx + np.cos(ang) * Rk, cy + np.sin(ang) * Rk, np.cos(ang) * sp, np.sin(ang) * sp - 60,
                        rng.uniform(0.9, 1.6, m), rng.uniform(width * 0.35, width * 0.6, m), ring_rgb[k])
        for i, (Rk, a0, w) in enumerate(rings):
            scale = 1.0
            if f >= esc:  # réapparition des anneaux, du centre vers l'extérieur
                scale = smooth((f - esc) / n_out * 1.6 - i / n * 0.6)
                if scale <= 0:
                    continue
            elif i in broken:
                continue
            rr = Rk * scale
            ang = math.degrees(a0 + w * t + gap / 2)
            sweep = 360 - math.degrees(gap)
            rect = skia.Rect.MakeLTRB(cx - rr, cy - rr, cx + rr, cy + rr)
            path = skia.Path()
            path.addArc(rect, ang, sweep)
            c.save()
            c.translate(0, 8)
            c.drawPath(path, paint(color(pal.shadow, 70 if pal.dark else 40), "stroke", width, blur=8))
            c.restore()
            c.drawPath(path, paint(color(ring_rgb[i]), "stroke", width))
            c.drawPath(path, paint(skia.Color(255, 255, 255, 70), "stroke", width * 0.25))
        ripples.draw(c)
        parts.draw(c, pt)
        pos, _k = frames[min(f, esc - 1)]
        if f < esc:
            pt.ball(c, pos[0], pos[1], ball_r, pal.accents[-1] if pal.dark else (255, 255, 255))
        else:
            e = smooth((f - esc) / n_out)
            pt.ball(c, cx + 10, cy - 20, ball_r * e, pal.accents[-1] if pal.dark else (255, 255, 255))
        v.emit()
    return total / FPS
