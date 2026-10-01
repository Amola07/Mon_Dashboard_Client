"""Démo 6 s : l'humain hologramme marche (squelette CC0 MakeHuman, cycle de marche), caméra qui l'accompagne.

    python -m films.holo.demo_marche sortie.mp4
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
from films.holo import humain as HU, marche as MA
from films.holo.holo import W, H, Camera, Frame, ease, grid_floor

FPS, DUR = 30, 6.0
Z0 = -2.6


def frame(c, t):
    pose = MA.walk(t)
    zc = Z0 + MA.STRIDE * t / MA.CYCLE                    # position du marcheur
    ang = 1.15 - 0.55 * ease(t / DUR)                     # la caméra passe du profil au trois-quarts
    cam = Camera((3.4 * math.sin(ang), 1.15, zc + 0.3 + 3.4 * math.cos(ang)), (0, 0.92, zc + 0.3), fov=40)
    fr = Frame(cam)
    grid_floor(fr, 0, size=6, step=0.3, a=0.28, center=(0, zc), fade=(2, 8))
    HU.human(fr, (0, 0, Z0), 0.0, 1.0, 1.0, beat_t=t, t=t, pose=pose)
    fr.compose(c, t, caption="Il marche : un vrai squelette articulé, sous la lumière.", cap_a=ease((t - 0.6) / 0.5))
    if t < 0.25:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(2, 5, 14, int(255 * (1 - t / 0.25)))))


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
    sr = E1.SR
    n = int(DUR * sr)
    y = E1.music(DUR) * 0.8 + HK.pad(DUR, 0.06)[:n]
    fx = np.zeros(n)
    k = 0
    while True:                                           # pas feutrés, au contact de chaque pied
        t0 = 0.25 * MA.CYCLE + k * MA.CYCLE / 2
        if t0 > DUR:
            break
        tt = np.arange(int(0.2 * sr)) / sr
        s_ = np.sin(2 * np.pi * 70 * tt) * np.exp(-tt / 0.04) * 0.18
        i = int(t0 * sr)
        m = min(n - i, len(s_))
        fx[i:i + m] += s_[:m]
        k += 1
    out = np.tanh((y + fx) * 1.2) / np.tanh(1.2) * np.minimum(1, (n - np.arange(n)) / (0.5 * sr))
    with wave.open(f"{tmp}/a.wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(np.stack([out, out], 1), -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", f"{tmp}/a.wav", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/holo_marche.mp4")
