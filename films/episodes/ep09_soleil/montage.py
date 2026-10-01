"""Épisode 9 — montage des clips générés (images animées par IA) sur la voix.

clips/NN.mp4 (non versionnés) → chaque plan est coupé, recalé (point de départ / vitesse) et agrandi en 1080×1920,
puis on superpose sous-titres et compte à rebours, et on mixe voix + musique + effets.
Un plan absent est remplacé par une carte « PLAN NN à générer » (aperçu du montage en cours).

    python -m films.episodes.ep09_soleil.montage output/ep09_soleil_ia.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import hook as HK
from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep09_soleil.ep09 import SEG, S, E, VOIX, text, F_BOLD, F_MED

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
CLIPS = os.path.join(HERE, "clips")
DUR = 85.6

# (plan, début, fin, départ dans le clip, vitesse) — coupes placées dans les silences de la voix
SHOTS = [
    ("01", 0.00, 2.60, 0.70, 1.0),     # le Soleil se contracte dès la 1re image, flash, onde de choc
    ("02", 2.60, 6.65, 0.00, 1.0),
    ("03", 6.65, 8.80, 0.50, 1.0),
    ("04", 8.80, 11.00, 0.50, 1.0),
    ("05", 11.00, 16.60, 0.50, 1.0),   # il devient un anneau creux vers 14 s (« n'existe déjà plus »)
    ("07", 16.60, 20.30, 0.00, 1.0),
    ("08", 20.30, 25.20, 0.00, 1.6),   # le photon arrive sur Terre en fin de phrase
    ("09", 25.20, 31.20, 0.00, 1.0),
    ("10", 31.20, 34.60, 6.60, 1.0),   # flash de disparition (9,6 s du clip) sur « maintenant »
    ("11", 34.60, 39.10, 0.00, 1.0),
    ("12", 39.10, 41.15, 0.00, 1.0),
    ("13", 41.15, 43.20, 0.80, 1.0),
    ("14", 43.20, 46.20, 2.20, 1.0),   # le mur de lumière passe la Terre sur « la dernière lumière arriverait »
    ("15", 46.20, 47.90, 0.70, 1.0),   # le Soleil s'éteint sur « s'éteindrait »
    ("16", 47.90, 52.90, 0.00, 1.0),
    ("17", 52.90, 58.70, 0.00, 1.0),
    ("18", 58.70, 63.55, 0.00, 1.0),
    ("19", 63.55, 68.00, 0.00, 1.0),
    ("20", 68.00, 75.20, 0.00, 1.25),  # sa lumière atteint la Terre sur « …pas fini son voyage »
    ("21", 75.20, 81.15, 0.00, 1.0),
    ("22", 81.15, DUR, 1.50, 1.0),     # gerbe de lumière sur « encore en train d'arriver », le Soleil se reforme
]
T_VANISH = 34.2                                              # le Soleil disparaît (flash du plan 10)
T_LAST = S("dern") + 0.2


def shot_file(tmp, plan, t0, t1, start, speed):
    out = f"{tmp}/s{plan}.mp4"
    n = int(round(t1 * FPS)) - int(round(t0 * FPS))
    src = os.path.join(CLIPS, f"{plan}.mp4")
    scale = ("scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,"
             "unsharp=5:5:0.6:5:5:0.0,fps=30")
    if os.path.exists(src):
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                                 capture_output=True, text=True).stdout)
        need = (t1 - t0) * speed
        pad = max(0.0, start + need - d + 0.1)                 # clip trop court : on fige la dernière image
        vf = f"setpts=(PTS-STARTPTS)/{speed},{scale},tpad=stop_mode=clone:stop_duration={pad / speed + 0.2:.2f}"
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{start}", "-i", src, "-an", "-vf", vf]
    else:
        vf = (f"drawtext=text='PLAN {plan}':fontcolor=white@0.8:fontsize=110:x=(w-text_w)/2:y=(h-text_h)/2-80,"
              f"drawtext=text='a generer':fontcolor=white@0.5:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2+60")
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=0x0a1030:s={W}x{H}:r={FPS}", "-vf", vf]
    subprocess.run(cmd + ["-frames:v", str(n), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out], check=True)
    return out


def overlay(c, t):
    """Sous-titres (style de la chaîne) + compte à rebours de la dernière lumière."""
    if T_VANISH <= t < T_LAST + 1.2:
        u = min(1.0, (t - T_VANISH) / (T_LAST - T_VANISH))
        s = int(math.ceil(500 * (1 - u)))
        a = 255 * min(1.0, (t - T_VANISH) / 0.2) * (1 - max(0.0, (t - T_LAST - 0.7) / 0.5))
        text(c, f"{s // 60}:{s % 60:02d}", 540, 230, 120, (255, 120, 110) if s < 60 else (255, 255, 255), a,
             glow=(255, 140, 90))
    E1.TIMING = [(txt, a, b) for _, txt, a, b in SEG]
    E1.draw_subtitle(c, t)
    if S("imag") - 0.2 < t < S("ici"):
        k = min(1.0, (t - S("imag") + 0.2) / 0.3, (S("ici") - t) / 0.3)
        text(c, "Expérience de pensée", 540, 1560, 32, (220, 225, 255), 200 * k, font=F_MED)


def burn(base, out):
    """Décode la vidéo de base image par image, dessine la surcouche (skia), réencode."""
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE)
    size = W * H * 4
    f = 0
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        arr = np.frombuffer(buf, np.uint8).reshape(H, W, 4).copy()
        surf = skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType)
        overlay(surf.getCanvas(), f / FPS)
        enc.stdin.write(arr.tobytes())
        f += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()


SR = E1.SR


def soundtrack(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOIX, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    voice = np.frombuffer(raw, np.int16).astype(float) / 32768
    n = int(DUR * SR)
    mix = np.zeros(n)
    mix[:min(n, len(voice))] += voice[:n]
    fx = np.zeros(n)

    def add(t, s_, g=1.0):
        i = int(t * SR)
        m = min(n - i, len(s_))
        if m > 0:
            fx[i:i + m] += s_[:m] * g

    add(0.0, E1.swell(0.16))                                 # le Soleil se contracte…
    add(1.25, HK.sub_drop(0.5))                             # … flash et onde de choc
    add(1.3, E1.swish(0.9, 0.12))
    add(S("lum"), E1.sparkle(0.07))
    add(S("plus"), E1.swell(0.14))
    add(16.6, E1.swish(0.6, 0.08))
    for k in range(5):                                      # le photon voyage
        add(S("met") + 0.9 * k, E1.ding(523 + 40 * k, 0.05))
    add(S("quand"), E1.swish(0.8, 0.06))
    add(T_VANISH - 0.1, HK.sub_drop(0.45))
    add(T_VANISH, E1.swish(0.6, 0.12))
    k = 0
    while T_VANISH + 0.5 * k < T_LAST:                      # tic-tac du compte à rebours
        add(T_VANISH + 0.5 * k, E1.tock(0.04 + 0.002 * k))
        k += 1
    add(S("soud"), E1.swell(0.2))
    add(S("eteint") + 0.1, HK.sub_drop(0.55))
    add(S("pastout"), E1.pop_s(520, 0.1))
    add(S("passe"), E1.sparkle(0.09))
    add(S("etoiles") + 1.5, E1.ding(392, 0.08))
    add(S("passe2"), E1.ding(784, 0.1))
    add(S("arrive") + 1.0, E1.sparkle(0.1))
    mus = E1.music(DUR)
    env = np.convolve(np.abs(mix), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
    duck = 1 - 0.55 * np.minimum(1, env / 0.05)
    tt = np.arange(n) / SR
    hole = np.clip(np.abs(tt - (S("eteint") + 0.6)) / 0.6, 0, 1)    # la musique se coupe quand le ciel s'éteint
    out_ = mix + E1.soften(fx, 6) * 0.8 + mus * duck * hole
    fade = np.ones(n)
    k = int(0.6 * SR)
    fade[-k:] = np.linspace(1, 0, k)
    out_ = np.tanh(out_ * fade * 1.3) / np.tanh(1.3)
    st = np.stack([out_, out_], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def render(out_path):
    tmp = tempfile.mkdtemp()
    parts = [shot_file(tmp, *s) for s in SHOTS]
    with open(f"{tmp}/list.txt", "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy",
                    f"{tmp}/base.mp4"], check=True)
    burn(f"{tmp}/base.mp4", f"{tmp}/v.mp4")
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)
    have = [s[0] for s in SHOTS if os.path.exists(os.path.join(CLIPS, f"{s[0]}.mp4"))]
    print("plans présents :", " ".join(have))


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep09_soleil_ia.mp4")
