"""Épisode 10 — « Pourquoi un satellite ne tombe jamais ? » : montage des clips générés sur la voix.

clips/NN.mp4 (non versionnés) → coupés, recalés et agrandis en 1080×1920 ; sous-titres ; voix mise en avant,
musique discrète, niveau final fort. Un plan absent est remplacé par une carte « PLAN NN à générer ».

    python -m films.episodes.ep10_satellite.montage output/ep10_satellite.mp4
"""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

from films import hook as HK
from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep09_soleil import montage as M9

HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.mp3")
DUR = 76.6
SR = E1.SR

# minutage mesuré (silences + reconnaissance vocale), texte corrigé d'après le script
SEG = [("Des milliers de satellites tournent au-dessus de vous.", 0.00, 2.32), ("Sans aile.", 2.79, 3.39),
       ("Sans moteur allumé.", 3.81, 4.77), ("Sans câble pour les retenir.", 5.15, 6.61),
       ("Pourquoi ne tombent-ils pas ?", 7.16, 8.31), ("Parce qu'ils tombent.", 8.82, 9.70),
       ("En permanence.", 10.10, 11.12), ("Un satellite est en chute libre.", 11.60, 13.08),
       ("Il tombe vers la Terre à chaque instant.", 13.46, 15.39),
       ("Mais il avance si vite que la Terre se dérobe sous lui.", 15.83, 18.60),
       ("Le sol s'éloigne aussi vite qu'il tombe.", 19.03, 21.16), ("Il ne touche jamais.", 21.60, 22.76),
       ("C'est le principe de l'orbite.", 23.23, 24.66), ("Une chute sans fin.", 25.01, 26.02),
       ("Newton l'avait compris il y a plus de 300 ans.", 26.49, 28.78),
       ("Un boulet tiré du haut d'une montagne retombe plus loin.", 29.18, 31.89),
       ("Tiré plus fort,", 32.30, 33.16), ("encore plus loin.", 33.44, 34.18), ("Tiré assez fort,", 34.57, 35.60),
       ("il fait le tour de la planète.", 35.92, 37.40), ("La vitesse est la clé.", 37.82, 39.07),
       ("28 000 km/h.", 39.44, 41.01), ("Un tour de la Terre en 90 minutes.", 41.35, 43.49),
       ("Trop lent,", 43.90, 44.36), ("il retombe.", 44.65, 45.26), ("Trop rapide,", 45.60, 46.24),
       ("il s'en va.", 46.57, 47.08), ("Pas de marge.", 47.46, 48.07), ("Pas de deuxième chance.", 48.44, 49.43),
       ("La gravité ne s'arrête pas là-haut.", 49.85, 51.47), ("Elle garde presque toute sa force.", 51.86, 53.68),
       ("Les astronautes ne sont pas en apesanteur.", 54.06, 56.05),
       ("Ils tombent avec leur station.", 56.39, 57.74), ("Ensemble.", 58.12, 58.67),
       ("Au même rythme.", 59.00, 59.81), ("Et une fois lancé,", 60.24, 61.12),
       ("plus besoin de moteur.", 61.42, 62.45), ("Rien ne le freine.", 62.84, 63.79), ("Pas d'air.", 64.17, 64.72),
       ("Pas de frottement.", 65.02, 65.62), ("Il tombe seul,", 66.00, 66.89), ("pendant des années.", 67.19, 68.04),
       ("Alors souvenez-vous.", 68.48, 69.35), ("Il y a, au-dessus de vous…", 69.76, 71.13),
       ("une machine qui tombe depuis des années…", 71.44, 73.62), ("et qui ne touchera jamais le sol.", 74.08, 76.12)]

# (plan, début, fin, départ dans le clip, vitesse) — coupes dans les silences
SHOTS = [("01", 0.00, 2.75, 0.0, 1.0), ("02", 2.75, 7.10, 0.0, 1.0), ("03", 7.10, 11.40, 0.0, 1.0),
         ("04", 11.40, 15.60, 0.0, 1.0), ("05", 15.60, 23.00, 0.0, 1.0), ("06", 23.00, 26.30, 0.0, 1.0),
         ("07", 26.30, 29.00, 0.0, 1.0), ("08", 29.00, 34.40, 0.0, 1.0), ("09", 34.40, 37.65, 0.0, 1.0),
         ("10", 37.65, 43.70, 0.0, 1.0), ("11", 43.70, 47.30, 0.0, 1.0), ("12", 47.30, 49.65, 0.0, 1.0),
         ("13", 49.65, 53.90, 0.0, 1.0), ("14", 53.90, 57.95, 0.0, 1.0), ("15", 57.95, 60.05, 0.0, 1.0),
         ("16", 60.05, 64.00, 0.0, 1.0), ("17", 64.00, 68.30, 0.0, 1.0), ("18", 68.30, 71.30, 0.0, 1.0),
         ("19", 71.30, DUR, 0.0, 1.0)]


def overlay(c, t):
    E1.TIMING = SEG
    E1.draw_subtitle(c, t)


def soundtrack(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOIX, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout                  # voix telle quelle, sans traitement
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

    add(0.0, E1.swell(0.14))
    add(8.75, HK.sub_drop(0.45))                           # « Parce qu'ils tombent. »
    add(15.6, E1.swish(1.2, 0.08))
    add(23.0, E1.ding(523, 0.08))
    add(29.6, HK.sub_drop(0.2))                            # tirs du canon
    add(32.3, HK.sub_drop(0.22))
    add(34.6, HK.sub_drop(0.25))
    add(35.0, E1.swish(2.0, 0.08))
    add(37.65, E1.swish(1.0, 0.1))
    add(43.9, E1.swell(0.1))
    add(45.6, E1.swish(0.6, 0.1))
    add(54.0, E1.sparkle(0.08))
    add(60.3, E1.swish(0.8, 0.07))
    add(68.5, E1.swell(0.12))
    add(74.1, E1.sparkle(0.1))
    mus = E1.music(DUR)
    env = np.convolve(np.abs(mix), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
    duck = 1 - 0.55 * np.minimum(1, env / 0.05)
    out_ = mix + E1.soften(fx, 6) * 0.8 + mus * duck                  # musique de fond à son niveau habituel
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
    M9.CLIPS = os.path.join(HERE, "clips")
    M9.overlay = overlay
    tmp = tempfile.mkdtemp()
    parts = [M9.shot_file(tmp, *s) for s in SHOTS]
    with open(f"{tmp}/list.txt", "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy",
                    f"{tmp}/base.mp4"], check=True)
    M9.burn(f"{tmp}/base.mp4", f"{tmp}/v.mp4")
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)
    have = [s[0] for s in SHOTS if os.path.exists(os.path.join(M9.CLIPS, f"{s[0]}.mp4"))]
    print("plans présents :", " ".join(have))


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep10_satellite.mp4")
