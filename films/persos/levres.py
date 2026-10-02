"""Synchronisation labiale de l'Orbe à partir de la voix.

Les formes de bouche sont calculées par Rhubarb Lip Sync (MIT, github.com/DanielSWolf/rhubarb-lip-sync), en mode
« phonetic » (indépendant de la langue, marche en français) : A fermée (m, b, p), B entrouverte (s, t, k), C ouverte
(é, è), D grande ouverte (a), E arrondie (o), F lèvres en avant (ou, u), G f/v, H l, X repos.

    cues = analyse("voix.mp3")            # [(instant, forme), …] (mis en cache à côté du fichier : .levres.tsv)
    forme = bouche_a(cues, t)              # (largeur, hauteur, dents, langue) lissés entre deux formes
"""
import glob
import os
import subprocess
import tempfile

import numpy as np

RHUBARB_DIRS = [os.environ.get("RHUBARB", ""), "/tmp/claude-0/-home-user-Mon-Dashboard-Client/074a8d09-4de2-5e84-a06b-0cddbabdcc79/scratchpad/rhubarb"]

# largeur, hauteur (px, pour un Orbe de rayon 140), dents visibles, langue visible
FORMES = {"X": (40, 4, 0, 0), "A": (46, 4, 0, 0), "B": (52, 16, 1, 0), "C": (58, 34, 0, 0), "D": (64, 54, 0, 1),
          "E": (44, 42, 0, 0), "F": (26, 26, 0, 0), "G": (52, 12, 1, 0), "H": (56, 38, 0, 1)}


def _rhubarb():
    for d in RHUBARB_DIRS:
        if d:
            hits = glob.glob(os.path.join(d, "**", "rhubarb"), recursive=True)
            hits = [h for h in hits if os.path.isfile(h) and os.access(h, os.X_OK)]
            if hits:
                return hits[0]
    raise FileNotFoundError("Rhubarb Lip Sync introuvable (variable RHUBARB)")


def analyse(audio, start=0.0, dur=None):
    cache = f"{audio}.{start:.2f}-{dur or 0:.2f}.levres.tsv"
    if not os.path.exists(cache):
        with tempfile.TemporaryDirectory() as tmp:
            wav = os.path.join(tmp, "v.wav")
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(start), "-i", audio]
            if dur:
                cmd += ["-t", str(dur)]
            subprocess.run(cmd + ["-ac", "1", "-ar", "16000", wav], check=True)
            subprocess.run([_rhubarb(), "-r", "phonetic", "-f", "tsv", "--extendedShapes", "GHX", wav, "-o", cache],
                           check=True, capture_output=True)
    cues = []
    for line in open(cache):
        a, b = line.split()
        cues.append((float(a), b))
    return cues


def bouche_a(cues, t, blend=0.06):
    """Forme de bouche à l'instant t, avec un fondu de `blend` secondes vers chaque nouvelle forme."""
    if not cues:
        return FORMES["X"]
    times = [c[0] for c in cues]
    i = int(np.searchsorted(times, t, side="right")) - 1
    if i < 0:
        return FORMES["X"]
    cur = np.array(FORMES[cues[i][1]], float)
    prev = np.array(FORMES[cues[i - 1][1]], float) if i > 0 else np.array(FORMES["X"], float)
    k = min(1.0, (t - cues[i][0]) / blend)
    k = k * k * (3 - 2 * k)
    return tuple(prev * (1 - k) + cur * k)
