"""Instant de chaque mot d'une voix, pour caler l'animation sur le mot exact (et pas sur le début de la phrase).

    python -m films.outils.mots_voix films/episodes/MON_EPISODE/audio/voix.mp3            # alignement sur le son
    python -m films.outils.mots_voix films/episodes/MON_EPISODE/audio/voix.mp3 --whisper  # Whisper (plus précis)
    → audio/mots.json : [[début, fin, "mot"], …] en secondes dans le fichier d'origine (avant resserrage des silences)

Alignement sur le son (par défaut, sans modèle à télécharger) : le texte de chaque phrase est connu (voix.json) ; on
repère les syllabes dans l'enveloppe de la voix (pics d'énergie entre 300 et 2500 Hz) et on pose chaque mot sur sa
première syllabe. Précision ≈ 0,1 s. Whisper (pip install faster-whisper) demande d'accéder à huggingface.co.

Dans un épisode (après M.preparer()) : temps_mot = mots.charger(M) puis mots.mot("dossier") → instant du mot à l'écran.
"""
import json
import os
import sys
import unicodedata

from films import montage_ia as MI


def transcrire(chemin, modele="small"):
    from faster_whisper import WhisperModel
    m = WhisperModel(modele, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(chemin, language="fr", word_timestamps=True, vad_filter=False)
    return [[round(w.start, 3), round(w.end, 3), w.word.strip()] for s in segs for w in s.words]


VOYELLES = set("aeiouyàâäéèêëîïôöùûüœæ")


def syllabes(mot):
    """Nombre approximatif de syllabes prononcées d'un mot français écrit."""
    m = mot.lower().strip(".,;:!?…«»\"'()")
    n = 0
    for part in m.replace("'", "-").replace("’", "-").split("-"):
        if not part:
            continue
        groupes = sum(1 for i, ch in enumerate(part) if ch in VOYELLES and (i == 0 or part[i - 1] not in VOYELLES))
        if groupes > 1 and (part.endswith("e") or part.endswith("es") or part.endswith("ent")):
            groupes -= 1                                                  # e muet final
        n += max(1, groupes) if any(ch.isalpha() for ch in part) else 0
    return max(1, n)


def aligner(chemin_mp3, chemin_json):
    """Mots posés sur les syllabes détectées dans le son, phrase par phrase."""
    import numpy as np
    from scipy.signal import butter, find_peaks, sosfiltfilt
    v = MI.load_voice(chemin_mp3)
    sr = MI.SR
    bande = sosfiltfilt(butter(4, [300, 2500], btype="band", fs=sr, output="sos"), v)
    pas = int(0.01 * sr)
    n = len(bande) // pas
    env = np.sqrt((bande[:n * pas].reshape(n, pas) ** 2).mean(1))
    env = np.convolve(env, np.hanning(5) / np.hanning(5).sum(), mode="same")
    out = []
    for a, b, txt in json.load(open(chemin_json)):
        ws = [w for w in txt.replace("…", "").split() if any(ch.isalnum() for ch in w)]
        if not ws:
            continue
        i0, i1 = int(a / 0.01), max(int(a / 0.01) + 2, int(b / 0.01))
        e = env[i0:i1]
        pics, _ = find_peaks(e, distance=8, prominence=0.12 * (e.max() + 1e-9))
        tp = a + pics * 0.01 if len(pics) else np.array([a, b])
        syl = [syllabes(w) for w in ws]
        total = sum(syl)
        k = 0
        debuts = []
        for nb in syl:                                                    # syllabe k → pic de rang proportionnel
            r = k / max(1, total - 1) * (len(tp) - 1) if total > 1 else 0
            j0 = int(r)
            t = tp[j0] + (tp[min(j0 + 1, len(tp) - 1)] - tp[j0]) * (r - j0)
            debuts.append(max(a, t - 0.06))                               # la consonne d'attaque, avant le pic
            k += nb
        debuts[0] = a
        fins = debuts[1:] + [b]
        out += [[round(x, 3), round(y, 3), w] for x, y, w in zip(debuts, fins, ws)]
    return out


def normal(txt):
    txt = unicodedata.normalize("NFD", txt.lower())
    return "".join(ch for ch in txt if ch.isalnum())


MOTS = []


def charger(M):
    """Lit audio/mots.json de l'épisode et passe les instants dans le temps de la vidéo (silences resserrés)."""
    chemin = os.path.join(os.path.dirname(M.SEGS), "mots.json")
    _, N, _ = MI.tighten(MI.load_voice(M.VOIX), max_gap=0.40, thr_db=-38.0)
    MOTS[:] = [(N(a), N(b), normal(w)) for a, b, w in json.load(open(chemin))]
    return MOTS


def mot(txt, apres=0.0, fin=False):
    """Début (ou fin) du premier mot qui commence par `txt` et qui arrive après l'instant `apres`."""
    cle = normal(txt)
    for a, b, w in MOTS:
        if a >= apres - 0.05 and w.startswith(cle):
            return b if fin else a
    raise KeyError(f"mot introuvable après {apres:.2f} s : {txt}")


if __name__ == "__main__":
    src = sys.argv[1]
    if "--whisper" in sys.argv:
        mots = transcrire(src)
    else:
        mots = aligner(src, os.path.join(os.path.dirname(src), "voix.json"))
    sortie = os.path.join(os.path.dirname(src), "mots.json")
    json.dump(mots, open(sortie, "w"), ensure_ascii=False)
    print(f"{len(mots)} mots → {sortie}")
