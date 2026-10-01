"""Essai 15 s, style hologramme : 1D (deux points enferment), 2D (vue d'en haut), 3D (boule venue de la 4D).

    python -m films.holo.essai_dim sortie.mp4
"""
import math
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import hook as HK
from films.episodes.ep01_triangle import ep01 as E1
from films.holo.holo import (CYAN, CYAN_HI, RED, W, H, Camera, Frame, circle, ease, ease_out, flat_person, grid_floor,
                             heart_2d, human_wire, lerp, sphere_wire)

FPS = 30
DUR = 15.0
CUTS = (5.0, 10.0)


def shot1(t):
    cam = Camera((lerp(-0.6, 0.6, t / 5), 0.55, 4.3), (0, 0, 0), fov=42)
    fr = Frame(cam)
    xs = np.linspace(-7, 7, 120)
    fr.poly(np.stack([xs, 0 * xs, 0 * xs], 1), CYAN, 0.9, 3.0)
    for k in np.arange(-7, 7.01, 0.5):                                     # graduations
        fr.poly([(k, -0.04, 0), (k, 0.04, 0)], CYAN, 0.35, 1.2)
    lock = ease_out((t - 0.6) / 1.8)
    for s in (-1, 1):
        x = s * lerp(5.5, 0.75, lock)
        fr.dot((x, 0, 0), CYAN_HI, 1.0, 9)
        fr.poly([(x, -0.22, 0), (x, 0.22, 0)], CYAN_HI, 1.0, 3.0)
    bx = 0.45 * math.sin(t * 2.2) * (0.3 + 0.7 * lock) if t > 2.4 else 0.15 * math.sin(t * 1.5)
    bx = max(-0.62, min(0.62, bx))
    fr.dot((bx, 0, 0), RED, 1.0, 11, layer="r")
    return fr, "En une dimension, deux points suffisent pour t'enfermer. Pour toujours."


def shot2(t):
    u = ease((t - 0.3) / 2.6)
    cam = Camera((0.0, lerp(0.5, 5.0, u), lerp(4.2, 1.5, u)), (0, 0, -0.1), fov=44)
    fr = Frame(cam)
    grid_floor(fr, 0.0, size=6, step=0.5, a=0.28, fade=(2, 9))
    sq = np.array([(-0.85, 0, -1.25), (0.85, 0, -1.25), (0.85, 0, 1.15), (-0.85, 0, 1.15), (-0.85, 0, -1.25)])
    draw = ease(t / 0.9) * 4
    for i in range(4):
        k = min(1.0, max(0.0, draw - i))
        if k > 0:
            fr.poly([sq[i], sq[i] + (sq[i + 1] - sq[i]) * k], CYAN_HI, 1.0, 3.2)
    p = flat_person(1.0)
    fr.poly(np.stack([p[:, 0] * 0.95, np.zeros(len(p)), -p[:, 1] * 0.95 - 0.05], 1), CYAN, 0.95, 2.2, closed=True)
    lift = ease((t - 3.2) / 1.4) * 1.3
    h = heart_2d() * 0.16
    hz = -0.5
    if lift > 0.01:                                                        # le cœur sort par le haut, sans franchir le carré
        fr.poly([(0, 0.0, hz), (0, lift, hz)], RED, 0.35, 1.5, layer="r")
    fr.poly(np.stack([h[:, 0], np.full(len(h), lift), hz - h[:, 1]], 1), RED, 1.0, 3.0, layer="r")
    cap = "En deux dimensions, un carré est une prison parfaite. Mais d'en haut, tu vois tout son intérieur."
    return fr, cap


def shot3(t):
    ang = 0.35 - 0.12 * t / 5
    cam = Camera((7.6 * math.sin(ang), 2.0, 7.6 * math.cos(ang)), (0, 1.25, 0), fov=50)
    fr = Frame(cam)
    grid_floor(fr, 0.0, size=2.4, step=0.4, a=0.3, fade=(4, 11))
    X, Y, Z = 2.4, 2.8, 2.4
    corners = [(x, y, z) for x in (-X, X) for y in (0, Y) for z in (-Z, Z)]
    for i, a_ in enumerate(corners):
        for b_ in corners[i + 1:]:
            if sum(1 for k in range(3) if a_[k] != b_[k]) == 1:
                fr.poly([a_, b_], CYAN, 0.55, 1.8)
    fr.poly([(-X, 0.9, -Z), (-X, 2.0, -Z), (-X + 1.0, 2.0, -Z), (-X + 1.0, 0.9, -Z)], CYAN, 0.5, 1.6, closed=True)  # fenêtre
    human_wire(fr, (-0.85, 0, 0.4), a=0.9, heart=False)
    s = (t - 0.6) / 3.6 * 2 - 1                                            # position dans la 4e dimension
    if -1 < s < 1:
        r = 0.7 * math.sqrt(1 - s * s)
        sphere_wire(fr, (0.75, 1.25, 0), r, RED, 1.0, 2.2, layer="r", n_lat=10, n_lon=12, spin=t * 0.6)
    cap = "Un être en 4D qui traverse ton monde ? Tu verrais juste une boule surgir, grandir… puis disparaître."
    return fr, cap


def frame(c, t):
    if t < CUTS[0]:
        fr, cap = shot1(t)
        lt = t
    elif t < CUTS[1]:
        fr, cap = shot2(t - CUTS[0])
        lt = t - CUTS[0]
    else:
        fr, cap = shot3(t - CUTS[1])
        lt = t - CUTS[1]
    cap_a = ease((lt - 0.25) / 0.4) * (1 - ease((lt - 4.55) / 0.35))
    fr.compose(c, t, caption=cap, cap_a=cap_a)
    dip = 0.0
    for tc in CUTS:                                                       # fondu bref par le noir entre les plans
        dip = max(dip, 1 - min(1.0, abs(t - tc) / 0.28))
    dip = max(dip, 1 - min(1.0, t / 0.3), 1 - min(1.0, (DUR - t) / 0.4))
    if dip > 0:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(2, 5, 14, int(255 * dip))))


def soundtrack(path):
    sr = E1.SR
    n = int(DUR * sr)
    y = E1.music(DUR) * 0.9 + np.pad(HK.pad(DUR, 0.06), (0, 0))[:n]
    fx = np.zeros(n)

    def add(t0, s_, g=1.0):
        i = int(t0 * sr)
        m = min(n - i, len(s_))
        if m > 0:
            fx[i:i + m] += s_[:m] * g

    add(0.0, HK.sub_drop(0.3))
    add(0.0, HK.sting(0.14))
    add(1.0, E1.swish(1.6, 0.12))
    add(2.35, E1.tock(0.18))
    for tc in CUTS:
        add(tc - 0.3, E1.swish(0.8, 0.14))
    add(CUTS[0] + 3.2, E1.swell(0.14))
    add(CUTS[1] + 0.6, HK.sub_drop(0.22))
    add(CUTS[1] + 0.6, E1.sparkle(0.08))
    out = y + E1.soften(fx, 6)
    fade = np.minimum(1, np.minimum(np.arange(n) / (0.05 * sr), (n - np.arange(n)) / (0.8 * sr)))
    out = np.tanh(out * fade * 1.3) / np.tanh(1.3)
    st = np.stack([out, out], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def render(out_path):
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", f"{tmp}/a.wav", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/holo_essai.mp4")
