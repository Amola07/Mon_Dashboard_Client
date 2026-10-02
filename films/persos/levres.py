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


def enveloppe(audio, start=0.0, dur=None, rate=100):
    """Volume de la voix (0–1) échantillonné à `rate` Hz : attaque rapide, relâchement doux."""
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", audio]
    if dur:
        cmd += ["-t", str(dur)]
    raw = subprocess.run(cmd + ["-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
    hop = 16000 // rate
    n = len(x) // hop
    # énergie dans la bande de la voix (les plosives sourdes et le souffle comptent peu)
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1))
    db = 20 * np.log10(rms + 1e-6)
    voiced = db[db > db.max() - 40]
    lo, hi = np.percentile(voiced, 25), np.percentile(voiced, 99)
    v = np.clip((db - lo) / (hi - lo), 0, 1)                # normalisé sur la voix elle-même : suit les syllabes
    out = np.zeros(n)
    for i in range(1, n):                                   # attaque 20 ms, relâchement 70 ms
        a = 0.6 if v[i] > out[i - 1] else 0.13
        out[i] = out[i - 1] + a * (v[i] - out[i - 1])
    return out, rate


class Synchro:
    """Bouche pilotée par deux sources : l'ouverture suit le volume de la voix (ce que l'œil juge en premier),
    la forme (largeur, arrondi, dents, langue) suit les phonèmes de Rhubarb ; les consonnes m/b/p ferment la bouche."""

    def __init__(self, audio, start=0.0, dur=None, avance=0.045):
        self.cues = analyse(audio, start, dur)
        self.env, self.rate = enveloppe(audio, start, dur)
        self.avance = avance                                # la bouche anticipe légèrement le son

    def __call__(self, t):
        t = t + self.avance
        w, h, dents, langue = bouche_a(self.cues, t, blend=0.05)
        i = min(len(self.env) - 1, max(0, int(t * self.rate)))
        v = self.env[i]
        cur = cue_a(self.cues, t)
        if v < 0.08 or cur == "X":                           # silence : lèvres fermées
            return (w, 4.0, 0, 0)
        if cur == "A":                                      # m, b, p : fermeture brève (moins franche si la voix
            return (w, 4.0 + 9.0 * max(0.0, v - 0.5), 0, 0)  # reste forte : Rhubarb confond parfois avec n)
        hmax = {"B": 22, "G": 16, "F": 30, "E": 46, "C": 44, "H": 42, "D": 60}.get(cur, 40)
        hh = 6 + (hmax - 6) * (0.35 + 0.65 * v)
        return (w * (0.9 + 0.15 * v), hh, dents, langue)


def cue_a(cues, t):
    times = [c[0] for c in cues]
    i = int(np.searchsorted(times, t, side="right")) - 1
    return cues[i][1] if i >= 0 else "X"


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
