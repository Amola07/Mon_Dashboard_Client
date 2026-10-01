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
from films.persos import orbe as OR

# l'Orbe en bleu : toutes ses humeurs passent dans des bleus (nuances différentes selon l'émotion)
_BLEUS = {"calme": [(20, 80, 255), (0, 160, 255), (60, 100, 240), (0, 200, 255)],
          "joie": [(30, 130, 255), (0, 200, 255), (20, 90, 255), (80, 170, 255)],
          "reflexion": [(15, 70, 220), (0, 140, 240), (10, 60, 200), (40, 170, 255)],
          "surprise": [(40, 160, 255), (110, 210, 255), (20, 110, 255), (0, 220, 255)],
          "idee": [(40, 150, 255), (90, 210, 255), (30, 120, 255), (60, 190, 255)],
          "triste": [(20, 50, 160), (30, 80, 190), (15, 40, 140), (40, 90, 200)]}
OR.HUMEURS.update(_BLEUS)

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


# (début, expression, regard) — l'Orbe réagit aux moments clés
ORBE = [(0.0, "surpris", (0.5, -0.7)), (2.6, "neutre", (0.5, -0.6)), (6.9, "joie", (0.4, -0.5)),
        (11.0, "neutre", (0.4, -0.9)), (14.1, "surpris", (0.4, -0.9)), (16.6, "reflechit", (0.6, -0.6)),
        (20.3, "neutre", (0.6, -0.6)), (34.2, "surpris", (0.5, -0.7)), (35.4, "joie", (0.3, -0.4)),
        (43.4, "neutre", (0.5, -0.7)), (46.5, "surpris", (0.4, -0.8)), (48.1, "reflechit", (0.6, -0.6)),
        (58.9, "joie", (0.4, -0.8)), (68.3, "triste", (0.5, -0.8)), (75.4, "neutre", (0.4, -0.9)),
        (81.4, "joie", (0.4, -0.8))]
# trajectoire : (temps, x, y, échelle) ; entre deux clés, mouvement lissé. Reste au-dessus des sous-titres.
KEYS = [(0.0, 800, 1250, 0.55), (1.2, 800, 1250, 0.55), (1.6, 880, 1330, 0.5),       # recule au flash
        (2.6, 300, 1380, 0.55), (6.4, 260, 1400, 0.55),                               # se prélasse au parc
        (6.9, 520, 1260, 0.5), (8.6, 560, 1240, 0.5),                                 # dans le rayon de soleil
        (8.9, 260, 1360, 0.5), (10.9, 720, 1360, 0.5),                                # se promène dans la rue
        (11.2, 820, 1300, 0.5), (13.9, 820, 1300, 0.5), (14.4, 820, 1180, 0.52),       # regarde le ciel, sursaute
        (16.4, 820, 1260, 0.5), (17.0, 540, 1300, 0.45), (20.0, 540, 1150, 0.34),     # vers l'œil
        (25.4, 840, 1330, 0.45), (30.8, 820, 1300, 0.45),                             # attend la « photo » sur Terre
        (31.4, 760, 1330, 0.5), (34.0, 760, 1330, 0.5), (34.5, 820, 1420, 0.48),       # près de l'horloge, sursaute
        (35.0, 540, 1300, 0.52), (38.9, 560, 1270, 0.52),                             # flotte sur le lac
        (39.2, 160, 760, 0.42), (41.0, 900, 640, 0.42),                               # vole avec les oiseaux
        (41.4, 300, 1330, 0.5), (43.0, 340, 1330, 0.5),                               # au café
        (43.4, 760, 1200, 0.45), (45.6, 880, 1300, 0.45),                             # fuit devant le mur de lumière
        (46.3, 540, 1320, 0.55), (47.8, 540, 1300, 0.55),                             # le ciel s'éteint
        (48.1, 760, 820, 0.45), (52.7, 700, 760, 0.45)]                               # au bord du cercle vide
ORBIT = (52.9, 58.7, (540, 705), 400, -1.0)                 # tourne autour du vide avec la Terre (plan 17)
KEYS2 = [(58.9, 330, 1360, 0.5), (63.4, 330, 1340, 0.5),                               # allongée à côté du rêveur
         (63.7, 540, 1210, 0.45), (67.8, 540, 1210, 0.45),                            # posée sur la Terre
         (68.2, 780, 1400, 0.48), (75.0, 800, 1380, 0.48),                            # attend la lumière de l'étoile
         (75.4, 320, 1420, 0.5), (80.9, 540, 980, 0.42),                              # monte vers la fenêtre
         (81.3, 540, 960, 0.42), (84.6, 700, 1180, 0.5), (DUR, 800, 1250, 0.55)]      # revient au point de départ


def _smooth(keys, t):
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            u = u * u * (3 - 2 * u)
            return tuple(p + (q - p) * u for p, q in zip(a, b))
    return keys[-1][1:]


def orbe_pos(t):
    t0, t1, (cx, cy), r, w = ORBIT
    if t < ORBIT[0]:
        x, y, sc = _smooth(KEYS, t)
        if t > KEYS[-1][0]:                                 # rejoint l'orbite
            ang0 = -math.pi / 3
            u = (t - KEYS[-1][0]) / (t0 - KEYS[-1][0])
            u = u * u * (3 - 2 * u)
            x = x + (cx + r * math.cos(ang0) - x) * u
            y = y + (cy + r * math.sin(ang0) * 0.9 - y) * u
        return x, y, sc
    if t < t1:
        ang = -math.pi / 3 + w * 2 * math.pi * (t - t0) / 10.0
        return cx + r * math.cos(ang), cy + r * math.sin(ang) * 0.9, 0.42
    x, y, sc = _smooth(KEYS2, t)
    if t < KEYS2[0][0]:
        ang = -math.pi / 3 + w * 2 * math.pi * (t1 - t0) / 10.0
        u = (t - t1) / (KEYS2[0][0] - t1)
        x = cx + r * math.cos(ang) + (x - cx - r * math.cos(ang)) * u
        y = cy + r * math.sin(ang) * 0.9 + (y - cy - r * math.sin(ang) * 0.9) * u
    return x, y, sc


def draw_orbe(c, t):
    k = max(i for i, o in enumerate(ORBE) if o[0] <= t)
    t0, expr, reg = ORBE[k]
    prev = ORBE[k - 1][1] if k else expr
    e = OR.Etat(expr=expr, age=t - t0, regard=reg, humeur_mix=min(1.0, (t - t0) / 0.4),
                humeur_avant=OR.HUMEUR_DE.get(prev, "calme"))
    e.cligne = (t % 4.3) < 0.1 and expr != "surpris"
    x, y, sc = orbe_pos(t)
    if 20.3 <= t < 25.2:                                    # suit le grain de lumière du Soleil vers la Terre
        u = max(0.0, min(0.82, (t - 20.3) * 1.6 / 8.0 - 0.06))  # un peu derrière le grain (clip à ×1,6)
        px, py = 350 + (840 - 350) * u, 550 + (1700 - 550) * u
        k = min(1.0, (t - 20.3) / 0.4)
        x, y = x + (px + 110 - x) * k, y + (py - 30 - y) * k
        sc = 0.4
    if 8.9 <= t < 10.9:                                     # petits sauts dans la rue
        y -= 30 * abs(math.sin((t - 8.9) * 6))
    y += 8 * math.sin(t * 1.6)
    c.save()
    c.translate(x, y)
    c.scale(sc, sc)
    OR.draw_orbe(c, t, e, parle_pulse=False)
    c.restore()


AVEC_ORBE = False                                           # l'Orbe bleue (désactivée pour cet épisode)


def overlay(c, t):
    """Sous-titres (style de la chaîne) + compte à rebours de la dernière lumière (+ l'Orbe si activée)."""
    if AVEC_ORBE:
        draw_orbe(c, t)
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
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOIX, "-af",
                          "highpass=f=70,acompressor=threshold=-26dB:ratio=3:attack=5:release=150:makeup=2,"
                          "loudnorm=I=-15:TP=-2:LRA=7", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
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
    duck = 1 - 0.7 * np.minimum(1, env / 0.05)               # la musique s'efface davantage sous la voix
    tt = np.arange(n) / SR
    hole = np.clip(np.abs(tt - (S("eteint") + 0.6)) / 0.6, 0, 1)    # la musique se coupe quand le ciel s'éteint
    out_ = mix + E1.soften(fx, 6) * 0.6 + mus * 0.7 * duck * hole
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
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000",              # niveau visé par TikTok
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)
    have = [s[0] for s in SHOTS if os.path.exists(os.path.join(CLIPS, f"{s[0]}.mp4"))]
    print("plans présents :", " ".join(have))


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep09_soleil_ia.mp4")
