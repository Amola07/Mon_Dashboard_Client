"""Une planche d'illustrations IA (grille de poses ou d'objets) → un dessin en traits par case, à l'échelle commune.

    python -m films.outils.planche_en_traits planche.webp 3x3 nom1 nom2 ... nom9
    → films/illustrations/nomK.json (même format que image_en_traits, plus "px" = [largeur, hauteur] du dessin en
      pixels de la case : deux poses d'une même planche gardent donc leur taille relative)

Dans un tableau, pour garder l'échelle entre poses :
    d = json.load(open(".../nom.json")); largeur = d["px"][0] * k      # k = pixels d'écran par pixel de planche
"""
import json
import os
import sys
import tempfile

import cv2
import numpy as np

from films.outils.image_en_traits import DOSSIER, ordonner, simplifier, suivre, amincir, binaire


def coupures(img, n, axe):
    """Limites des n bandes (lignes si axe = 0, colonnes si axe = 1) : là où il y a le moins d'encre près de la
    coupe régulière. Une chaussure qui déborde un peu de sa case n'est plus coupée en deux."""
    taille = img.shape[axe]
    encre = (img < 128).sum(axis=1 - axe).astype(float)
    encre = np.convolve(encre, np.ones(5) / 5, mode="same")
    bornes = [0]
    for k in range(1, n):
        c = k * taille // n
        lo, hi = max(c - int(0.12 * taille / n), 0), min(c + int(0.12 * taille / n), taille)
        zone = encre[lo:hi]
        creux = np.flatnonzero(zone <= zone.min() + 1e-9)
        bornes.append(lo + int(creux[len(creux) // 2]))
    bornes.append(taille)
    return bornes


def planche_en_traits(chemin, cols, rangs, noms):
    img = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
    bl, br = coupures(img, cols, 1), coupures(img, rangs, 0)
    os.makedirs(DOSSIER, exist_ok=True)
    for k, nom in enumerate(noms):
        r, c = divmod(k, cols)
        cellule = img[br[r]:br[r + 1], bl[c]:bl[c + 1]]
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            cv2.imwrite(f.name, cellule)
        lignes = ordonner(simplifier(suivre(amincir(binaire(f.name)))))
        os.unlink(f.name)
        xs = [p[0] for l in lignes for p in l]
        ys = [p[1] for l in lignes for p in l]
        x0, y0, w = min(xs), min(ys), max(max(xs) - min(xs), 1e-6)
        d = {"ratio": (max(ys) - y0) / w, "px": [round(w, 1), round(max(ys) - y0, 1)],
             "traits": [[(round((x - x0) / w, 4), round((y - y0) / w, 4)) for x, y in l] for l in lignes]}
        json.dump(d, open(os.path.join(DOSSIER, nom + ".json"), "w"))
        print(nom, len(lignes), "traits", d["px"])


if __name__ == "__main__":
    cols, rangs = (int(v) for v in sys.argv[2].split("x"))
    planche_en_traits(sys.argv[1], cols, rangs, sys.argv[3:])
