"""Épisode 8 avec l'accroche des 2 premières secondes (films.hook).

    python -m films.episodes.ep08_quantique.ep08_hook sortie.mp4
"""
import sys

from films import hook
from films.episodes.ep08_quantique import ep08 as ep

if __name__ == "__main__":
    hook.render(ep, "Tu es peut-être", "déjà mort.", "Immortalité quantique",
                sys.argv[1] if len(sys.argv) > 1 else "output/ep08_quantique_hook.mp4", beats=3)
