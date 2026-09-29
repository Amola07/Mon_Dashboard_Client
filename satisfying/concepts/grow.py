"""La balle grossit à chaque rebond jusqu'à remplir le cercle, puis redevient petite (boucle)."""
import math

import numpy as np
import skia

from ..engine import FPS, H, W, Ripples, circle_hit, color, lerp_rgb, paint

TITLE = "Balle qui grossit à chaque rebond"
SUBSTEPS = 12


def _simulate(growth, rng, cx, cy, R, r0, start, gravity, max_frames):
    pos, vel = list(start), [400.0, 0.0]
    r, frames, events = r0, [], []
    dt = 1 / FPS / SUBSTEPS
    for f in range(max_frames):
        for _ in range(SUBSTEPS):
            vel[1] += gravity * dt
            pos[0] += vel[0] * dt
            pos[1] += vel[1] * dt
            hit = circle_hit(pos, vel, r, cx, cy, R)
            if hit:
                n, vn = hit
                kick = rng.uniform(-70, 70)
                vel[0] += -n[1] * kick
                vel[1] += n[0] * kick
                speed = math.hypot(*vel)
                vel[0] *= max(speed, 900) / speed
                vel[1] *= max(speed, 900) / speed
                r += growth
                events.append((f / FPS, (cx + n[0] * R, cy + n[1] * R), min(1.0, vn / 1400)))
                if r >= R - 4:
                    frames.append((tuple(pos), R - 4))
                    return frames, events
        frames.append((tuple(pos), r))
    return frames, events


def plan(rng, sound, seconds):
    """Simule la scène (positions et rayons à 60 i/s) et note les impacts dans la bande-son."""
    cx, cy, R = W / 2, H / 2 - 60, float(rng.uniform(400, 460))
    r0 = float(rng.uniform(14, 22))
    start = (cx + rng.uniform(-80, 80), cy - rng.uniform(150, 250))
    gravity = float(rng.uniform(1300, 1700))
    sim_seed = int(rng.integers(1 << 30))
    best = None
    for g in np.linspace(0.8, 2.6, 40):
        fr, ev = _simulate(g, np.random.default_rng(sim_seed), cx, cy, R, r0, start, gravity, 90 * FPS)
        d = len(fr) / FPS
        score = abs(d - seconds + 2.6) + (100 if d < seconds - 3 else 0)  # jamais sous le seuil d'une minute
        if best is None or score < best[0]:
            best = (score, fr, ev)
    _, frames, events = best
    fill = len(frames)
    end_pos, end_r = frames[-1]
    n_out = int(2.6 * FPS)
    for j in range(1, n_out + 1):
        e = (j / n_out) ** 2 * (3 - 2 * j / n_out)
        frames.append(((end_pos[0] * (1 - e) + start[0] * e, end_pos[1] * (1 - e) + start[1] * e),
                       end_r * (1 - e) + r0 * e))
    for t, p, s in events:
        sound.hit(t, s)
    for j, st in enumerate([4, 3, 2, 1, 0]):
        sound.hit(fill / FPS + 0.15 + j * 0.4, 0.8, step=st + 5)
    return {"cx": cx, "cy": cy, "R": R, "r0": r0, "frames": frames, "events": events, "fill": fill}


def render(ctx):
    rng, pal, pt, v = ctx.rng, ctx.pal, ctx.painter, ctx.video
    p = plan(rng, ctx.sound, ctx.seconds)
    cx, cy, R, r0, frames = p["cx"], p["cy"], p["R"], p["r0"], p["frames"]
    by_frame = {}
    for t, pt_, s in p["events"]:
        by_frame.setdefault(int(round(t * FPS)), []).append((pt_, s))

    ripples, trail = Ripples(), []
    for f, (pos, r) in enumerate(frames):
        if ctx.done(f):
            break
        rgb = lerp_rgb(pal.accents, (r - r0) / (R - 4 - r0))
        for p, s in by_frame.get(f, []):
            ripples.add(p[0], p[1], rgb, 0.5 + 0.5 * s)
        c = v.canvas
        pt.background(c)
        pt.container(c, cx, cy, R)
        c.save()
        c.clipPath(skia.Path.Circle(cx, cy, R), doAntiAlias=True)
        ripples.draw(c)
        trail = (trail + [(pos, r, rgb)])[-12:]
        for j, (tp, tr, trgb) in enumerate(trail[:-1]):
            c.drawCircle(tp[0], tp[1], tr, paint(color(trgb, 70 * (j + 1) / len(trail))))
        pt.ball(c, pos[0], pos[1], r, rgb)
        c.restore()
        v.emit()
    return len(frames) / FPS
