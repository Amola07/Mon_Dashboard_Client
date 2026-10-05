"""Découpe une voix en phrases (d'après les silences) et écrit un voix.json à compléter.

    python -m films.outils.minuter_voix films/episodes/MON_EPISODE/audio/voix.mp3

Écrit audio/voix.json à côté du mp3 : une ligne [début, fin, "texte"] par morceau de voix.
Le texte est vide : recopie la bonne phrase du script dans chaque ligne (fusionne deux lignes si une phrase a été
coupée en deux : garde le début de la première et la fin de la seconde).
Option --modele DOSSIER : si tu as téléchargé un modèle Whisper sherpa-onnx, le texte est pré-rempli.
"""
import argparse
import json
import os
import re
import subprocess

import numpy as np


def morceaux(chemin, seuil_db=-30, silence_min=0.12):
    log = subprocess.run(["ffmpeg", "-i", chemin, "-af", f"silencedetect=noise={seuil_db}dB:d={silence_min}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    debuts_sil = [float(v) for v in re.findall(r"silence_start: ([0-9.]+)", log)]
    fins_sil = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", log)]
    duree = float(re.findall(r"Duration: (\d+):(\d+):([0-9.]+)", log)[0][2]) + 60 * float(
        re.findall(r"Duration: (\d+):(\d+):([0-9.]+)", log)[0][1])
    a_s = [0.0] + fins_sil
    b_s = debuts_sil + [duree]
    return [(a, b) for a, b in zip(a_s, b_s) if b - a >= 0.15]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voix")
    ap.add_argument("--modele", help="dossier sherpa-onnx-whisper-small (optionnel)")
    arg = ap.parse_args()
    segs = morceaux(arg.voix)
    textes = [""] * len(segs)
    if arg.modele:
        import sherpa_onnx
        m = os.path.join(arg.modele, "small-")
        rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=m + "encoder.int8.onnx", decoder=m + "decoder.int8.onnx",
                                                         tokens=m + "tokens.txt", language="fr", task="transcribe")
        sr = 16000
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", arg.voix, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                             capture_output=True).stdout
        x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        for i, (a, b) in enumerate(segs):
            st = rec.create_stream()
            st.accept_waveform(sr, np.concatenate([np.zeros(1600, np.float32), x[int(a * sr):int(b * sr)], np.zeros(3200, np.float32)]))
            rec.decode_stream(st)
            textes[i] = st.result.text.strip()
    sortie = os.path.join(os.path.dirname(arg.voix), "voix.json")
    lignes = [f'[{a:.2f},{b:.2f},{json.dumps(t, ensure_ascii=False)}]' for (a, b), t in zip(segs, textes)]
    with open(sortie, "w") as f:
        f.write("[" + ",\n".join(lignes) + "]\n")
    for i, ((a, b), t) in enumerate(zip(segs, textes)):
        print(f"{i:2d}  {a:6.2f} → {b:6.2f}  {t}")
    print("écrit :", sortie)


if __name__ == "__main__":
    main()
