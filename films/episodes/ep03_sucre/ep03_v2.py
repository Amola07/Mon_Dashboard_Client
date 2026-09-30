"""Épisode 3, finition v2 (caméra vivante, sous-titres mot par mot, bloom, grain, impacts graves).

    python -m films.episodes.ep03_sucre.ep03_v2 sortie.mp4
"""
import sys

from films import finition
from films.episodes.ep03_sucre import ep03 as ep

REVEALS = [(ep.S("hook2") + 0.9, 0.8),          # « … morceau de sucre »
           (ep.T_ZOOM[0], 0.35), (ep.T_ENTER, 0.5),
           (ep.T_STADE, 0.6), (ep.S("rien"), 0.7),
           (ep.T_PCT + 1.4, 0.9),               # 99,9999 %
           (ep.T_FIELD, 0.4), (ep.T_CUBE, 1.0),  # le sucre
           (ep.T_HEAVY, 1.0),                   # 400 millions de tonnes
           (ep.T_BOOM, 1.0),                    # l'étoile s'effondre
           (ep.T_SCALE + 1.4, 0.7), (ep.T_GHOST[1], 0.6)]

if __name__ == "__main__":
    finition.render(ep, REVEALS, sys.argv[1] if len(sys.argv) > 1 else "output/ep03_sucre_v2.mp4")
