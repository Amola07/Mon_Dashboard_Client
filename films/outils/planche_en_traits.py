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

from films.outils.image_en_traits import DOSSIER, ordonner, simplifier, suivre, amincir, binaire


def planche_en_traits(chemin, cols, rangs, noms):
    img = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
    H, L = img.shape
    ch, cl = H // rangs, L // cols
    os.makedirs(DOSSIER, exist_ok=True)
    for k, nom in enumerate(noms):
        r, c = divmod(k, cols)
        cellule = img[r * ch:(r + 1) * ch, c * cl:(c + 1) * cl]
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
