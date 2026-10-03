"""Voix provisoire (Kokoro local, « ff_siwis ») pour caler le montage en attendant la voix ElevenLabs.

Écrit audio/voix_provisoire.wav et audio/voix_provisoire.json (début, fin, texte de chaque phrase).

    python -m films.episodes.ep17_sucre.voix_provisoire
"""
import json
import os
import wave

import numpy as np
import sherpa_onnx as so

from films.episodes.ep14_chatouilles.voix import D, trim

HERE = os.path.dirname(os.path.abspath(__file__))
SID, SPEED = 30, 1.05
P_PHRASE, P_PARA = 0.22, 0.38

TEXTE = [
    ["Toute l'humanité tient dans un morceau de sucre.", "Huit milliards de personnes.", "Et ce n'est pas une image."],
    ["Regarde ta main.", "Elle a l'air pleine, solide.", "Pourtant, elle est presque entièrement vide."],
    ["Parce qu'elle est faite d'atomes.", "Et un atome, c'est surtout… du vide.",
     "Si un atome avait la taille d'un stade de foot, son noyau serait une petite bille posée au centre.",
     "Tout le reste, c'est de l'espace."],
    ["Alors imagine qu'on retire tout ce vide.", "De toi.", "De moi.", "De chaque être humain sur Terre."],
    ["Il ne resterait qu'une matière incroyablement dense…", "qui tiendrait dans un morceau de sucre."],
]


def main():
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(kokoro=so.OfflineTtsKokoroModelConfig(
        model=f"{D}/model.onnx", voices=f"{D}/voices.bin", tokens=f"{D}/tokens.txt", data_dir=f"{D}/espeak-ng-data",
        lexicon=f"{D}/lexicon-us-en.txt", lang="fr"), num_threads=4))
    tts = so.OfflineTts(cfg)
    parts, segs, t, sr = [], [], 0.0, 24000
    for i, para in enumerate(TEXTE):
        for j, ph in enumerate(para):
            a = tts.generate(ph.replace("…", ","), sid=SID, speed=SPEED)
            sr = a.sample_rate
            x = trim(np.array(a.samples, np.float32), sr)
            segs.append((round(t, 3), round(t + len(x) / sr, 3), ph))
            parts.append(x)
            t += len(x) / sr
            p = P_PHRASE if j < len(para) - 1 else P_PARA
            parts.append(np.zeros(int(p * sr), np.float32))
            t += p
    y = np.concatenate(parts)
    y = y / (np.abs(y).max() + 1e-9) * 0.9
    with wave.open(os.path.join(HERE, "audio", "voix_provisoire.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    json.dump(segs, open(os.path.join(HERE, "audio", "voix_provisoire.json"), "w"), ensure_ascii=False, indent=0)
    print(f"{t:.1f} s", len(segs), "phrases")


if __name__ == "__main__":
    main()
