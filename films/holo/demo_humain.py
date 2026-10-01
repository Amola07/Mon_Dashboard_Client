"""Démo 6 s : humain détaillé en hologramme (scanner de bas en haut, rotation, cœur qui bat).

    python -m films.holo.demo_humain sortie.mp4
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
from films.holo import humain as HU
from films.holo.holo import W, H, Camera, Frame, ease, grid_floor

FPS, DUR = 30, 6.0


def frame(c, t):
    ang = 0.9 - 0.75 * ease(t / DUR) if t < DUR else 0.15
    dist = 3.3 - 0.9 * ease((t - 2.6) / 3.0)
    ty = 0.9 + 0.35 * ease((t - 2.6) / 3.0)
    cam = Camera((dist * math.sin(ang), ty + 0.2, dist * math.cos(ang)), (0, ty, 0), fov=40)
    fr = Frame(cam)
    grid_floor(fr, 0, size=3, step=0.3, a=0.25, fade=(2, 7))
    HU.pedestal(fr, t)
    HU.motes(fr, t)
    HU.human(fr, (0, 0, 0), 0.0, 1.0, 1.0, beat_t=t, reveal=ease(t / 2.4) if t < 2.4 else 1.0, t=t)
    fr.compose(c, t, caption="Avec une dimension de plus, on pourrait voir ton cœur… sans jamais toucher ta peau.",
               cap_a=ease((t - 2.6) / 0.5))
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
    for t0, s_ in ((0.0, HK.sub_drop(0.28)), (0.0, E1.swish(2.4, 0.14)), (2.5, HK.sting(0.14))):
        i = int(t0 * sr)
        m = min(n - i, len(s_))
        fx[i:i + m] += s_[:m]
    for k in range(5):                                         # battements de cœur doux
        tt = np.arange(int(0.25 * sr)) / sr
        s_ = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt / 0.06) * 0.25
        i = int((2.6 + k * 0.84) * sr)
        m = min(n - i, len(s_))
        if m > 0:
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
    render(sys.argv[1] if len(sys.argv) > 1 else "output/holo_humain.mp4")
