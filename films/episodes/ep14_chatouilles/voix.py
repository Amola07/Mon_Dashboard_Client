"""Voix de l'épisode 14, générée en local avec Kokoro (sherpa-onnx, voix française « ff_siwis »).

Chaque phrase est synthétisée séparément puis assemblée avec des pauses maîtrisées (≤ 0,40 s), et le niveau est
normalisé. Modèle : https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models (kokoro-multi-lang-v1_0).

    KOKORO=/chemin/kokoro-multi-lang-v1_0 python -m films.episodes.ep14_chatouilles.voix
"""
import os
import wave

import numpy as np
import sherpa_onnx as so

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.environ.get("KOKORO", "/tmp/claude-0/-home-user-Mon-Dashboard-Client/074a8d09-4de2-5e84-a06b-0cddbabdcc79/"
                   "scratchpad/tts/kokoro-multi-lang-v1_0")
SID, SPEED = 30, 1.0
P_PHRASE, P_PARA = 0.28, 0.40

# paragraphes → phrases (orthographe parfois adaptée pour la prononciation)
TEXTE = [
    ["Pourquoi tu ne peux pas te chatouiller toi-même ?"],
    ["Essaye, pour voir.", "Vas-y, sous les côtes, sur la plante des pieds.", "Rien du tout.",
     "Pourtant, si ton pote fait exactement le même geste, tu te tords de rire."],
    ["Le coupable, c'est ton cerveau.", "Plus précisément, une petite zone à l'arrière de ta tête : le cervelet.",
     "Chaque fois que tu bouges, il prédit ce que tu vas ressentir.", "Et ce qu'il a prévu, il le rend plus faible.",
     "Bref, ta propre main ne peut pas te surprendre."],
    ["À la fin des années quatre-vingt-dix, des chercheurs de Londres ont fabriqué un robot à chatouilles.",
     "Toi, tu bouges une manette, et le robot recopie ton geste sur ta main.", "Sans délai, rien ne se passe.",
     "Mais s'ils ajoutent un retard de deux dixièmes de seconde, ça recommence à chatouiller.", "Plus le retard est long, plus ça chatouille.",
     "Ton cerveau ne fait plus le lien."],
    ["Et le plus fou ?", "Certaines personnes y arrivent.", "Des patients qui entendent des voix.",
     "Chez eux, le cerveau a du mal à distinguer ce qu'il fait lui-même de ce qui vient de l'extérieur."],
    ["Même les rats sont chatouilleux.",
     "Quand on les chatouille, ils poussent des petits cris ultrasoniques, une sorte de rire.",
     "Et ils reviennent chercher la main qui les chatouille."],
    ["Mais il reste un truc que personne n'explique vraiment.",
     "Pourquoi tu ris, alors que, la plupart du temps, tu détestes ça ?"],
]


def trim(x, sr, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a, b = max(0, idx[0] - int(0.02 * sr)), min(len(x), idx[-1] + int(0.14 * sr))
    return x[a:b]


def main(out=os.path.join(HERE, "audio", "voix.wav")):
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(kokoro=so.OfflineTtsKokoroModelConfig(
        model=f"{D}/model.onnx", voices=f"{D}/voices.bin", tokens=f"{D}/tokens.txt", data_dir=f"{D}/espeak-ng-data",
        lexicon=f"{D}/lexicon-us-en.txt", lang="fr"), num_threads=4))
    tts = so.OfflineTts(cfg)
    parts, sr = [], 24000
    for i, para in enumerate(TEXTE):
        for j, ph in enumerate(para):
            a = tts.generate(ph, sid=SID, speed=SPEED)
            sr = a.sample_rate
            parts.append(trim(np.array(a.samples, np.float32), sr))
            last = j == len(para) - 1
            if not (last and i == len(TEXTE) - 1):
                parts.append(np.zeros(int((P_PARA if last else P_PHRASE) * sr), np.float32))
    x = np.concatenate(parts)
    x *= 10 ** (-16 / 20) / (np.sqrt((x[np.abs(x) > 0.01] ** 2).mean()) + 1e-9)
    x = np.tanh(x * 1.2) / np.tanh(1.2)
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"{out} : {len(x) / sr:.1f} s")


if __name__ == "__main__":
    main()
