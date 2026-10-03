"""Épisode 9 — remontage dynamique des mêmes clips (films/montage_dyn.py).

    python -m films.episodes.ep09_soleil.montage_v2 output/ep09_soleil_v2.mp4
"""
import sys

from films import montage_dyn as MD
from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep09_soleil.ep09 import SEG, S, VOIX
from films.episodes.ep09_soleil.montage import CLIPS, SHOTS

SCALE = ("scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,"
         "unsharp=5:5:0.6:5:5:0.0")
MOTS = ["RIEN", "disparaître", "lumière", "passé", "mortes", "éteindrait", "gravité", "maintenant", "soudain"]
PARTIES = [S("raison"), S("imag"), S("soud"), S("pastout"), S("fasc"), S("proch")]
FX = [(S("soud") - 1.2, E1.swell(0.16), 1.0)]

if __name__ == "__main__":
    MD.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep09_soleil_v2.mp4", VOIX, CLIPS,
              [(t, a, b) for _, t, a, b in SEG], SHOTS, MOTS, PARTIES, scale_vf=SCALE, fx_extra=FX)
