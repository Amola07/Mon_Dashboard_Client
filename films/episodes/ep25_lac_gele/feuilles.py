"""Épisode 25 — conversion des feuilles d'animation (24 cases = 1 s à 24 i/s) et retouches de montage.

    python -m films.episodes.ep25_lac_gele.feuilles DOSSIER_DES_IMAGES

Les images sources (générées par IA) restent hors du dépôt ; seuls les traits (films/animations/*.json) y sont.
"""
import json
import os
import subprocess
import sys

from films.outils.feuille_animation import DOSSIER

# image source → (nom, grille)
FEUILLES = {
    "60": ("p04_1", "6x4"), "63": ("p04_2", "6x4"), "61": ("p05", "6x4"), "64": ("p02", "6x4"), "65": ("p01", "7x4"),
    "66": ("p09_1", "6x4"), "75": ("p09_2", "6x4"), "74": ("p09_3", "6x4"), "73": ("p09_4", "6x4"),
    "67": ("p08", "6x4"), "68": ("p07", "6x4"), "70": ("p06_1", "6x4"), "69": ("p06_2", "6x4"),
    "72": ("p10_1", "6x4"), "71": ("p10_2", "6x4"), "76": ("p14", "6x4"), "77": ("p13", "6x4"), "78": ("p12", "6x4"),
    "80": ("p11_1", "6x4"), "79": ("p11_2", "6x4"), "85": ("p19_1", "6x4"), "84": ("p19_2", "6x4"),
    "82": ("p20_1", "6x4"), "81": ("p20_2", "6x4"), "83": ("p21", "6x4"),
    "89": ("p17_1", "6x4"), "88": ("p17_2", "6x4"), "87": ("p17_3", "6x4"), "86": ("p18", "6x4"),
}


def retoucher(nom, f):
    chemin = os.path.join(DOSSIER, nom + ".json")
    d = json.load(open(chemin))
    d["images"] = f(d["images"])
    json.dump(d, open(chemin, "w"))


def main():
    src = sys.argv[1]
    for num, (nom, grille) in FEUILLES.items():
        subprocess.run([sys.executable, "-m", "films.outils.feuille_animation", os.path.join(src, num + ".webp"), nom,
                        grille], check=True)
    # plan 1 : les pieds sont coupés dans la dernière rangée (7 cases) → on garde les 21 premières
    retoucher("p01", lambda ims: ims[:21])
    # plan 20 : l'élan finit par une case à deux chaussures → on coupe les 2 dernières ; le lancer de la feuille 2
    # part vers la gauche alors que l'élan et la chute vont vers la droite → miroir
    retoucher("p20_1", lambda ims: ims[:22])
    retoucher("p20_2", lambda ims: [[[(-x, y) for x, y in l] for l in im] for im in ims])


if __name__ == "__main__":
    main()
