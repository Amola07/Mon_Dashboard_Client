"""Démo : X Bot (Mixamo) en hologramme, enchaînant de vraies animations avec fondus.

    python -m films.holo.demo_xbot sortie.mp4
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
from films.holo.holo import W, H, Camera, Frame, ease, grid_floor
from films.holo.perso import Perso

FPS = 30
# (animation, début, fin, avance en m/s)
SEQ = [("standing_idle", 0.0, 2.2, 0.0), ("looking_around", 2.2, 5.6, 0.0), ("walking", 5.6, 8.8, 1.25),
       ("pointing", 8.8, 11.2, 0.0), ("surprised", 11.2, 13.6, 0.0)]
DUR = SEQ[-1][2]
FADE = 0.45
P = None


def pose(t):
    """Matrices d'os au temps t, avec fondu entre deux animations, et avancée cumulée."""
    ws, mats = [], []
    z = 0.0
    for name, a, b, v in SEQ:
        z += v * max(0.0, min(t, b) - a)
        w = ease((t - a + FADE / 2) / FADE) * (1 - ease((t - b + FADE / 2) / FADE)) if (a > 0 or t >= 0) else 1.0
        if a == 0:
            w = 1 - ease((t - b + FADE / 2) / FADE)
        if w > 1e-3:
            ws.append(w)
            mats.append(P.mats(name, max(0.0, t - a), loop=True))
    ws = np.array(ws) / sum(ws)
    M = sum(w * m for w, m in zip(ws, mats))
    return M, z


def frame(c, t):
    M, z = pose(t)
    ang = 0.55 - 0.9 * ease(t / DUR)
    cz = z * 0.9
    cam = Camera((3.6 * math.sin(ang), 1.2, cz + 3.6 * math.cos(ang)), (0, 0.95, cz), fov=42)
    fr = Frame(cam)
    grid_floor(fr, 0, size=6, step=0.3, a=0.26, center=(0, cz), fade=(2, 8))
    P.draw(fr, M, pos=(0, 0, z), t=t, beat_t=t, reveal=ease(t / 1.6) if t < 1.6 else 1.0)
    fr.compose(c, t)
    if t < 0.25:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(2, 5, 14, int(255 * (1 - t / 0.25)))))


def render(out_path):
    global P
    P = Perso()
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
    sr = E1.SR
    n = int(DUR * sr)
    y = E1.music(DUR) * 0.8 + HK.pad(DUR, 0.06)[:n]
    fx = np.zeros(n)
    for t0, s_ in ((0.0, HK.sub_drop(0.26)), (0.0, E1.swish(1.6, 0.12)), (11.2, HK.sting(0.14)),
                   (8.9, E1.ding(784, 0.1))):
        i = int(t0 * sr)
        m = min(n - i, len(s_))
        fx[i:i + m] += s_[:m]
    out = np.tanh((y + fx) * 1.2) / np.tanh(1.2) * np.minimum(1, (n - np.arange(n)) / (0.5 * sr))
    with wave.open(f"{tmp}/a.wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(np.stack([out, out], 1), -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", f"{tmp}/a.wav", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/holo_xbot.mp4")
