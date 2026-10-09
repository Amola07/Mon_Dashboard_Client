"""Une feuille de sprites générée par IA (une ligne = une animation) → dessins vectoriels à la même échelle.

    python -m films.outils.planche_sprites planche.webp 4x3 ligne1 ligne2 ligne3
    → films/illustrations_vecteur/<ligneK>_<1..4>.json

Contrairement à planche_vecteur (qui recadre chaque case au plus près), toutes les images d'une ligne partagent la
même fenêtre, prise à la même place dans chaque case : les 4 images se superposent exactement et l'animation ne
« saute » pas (la ligne de sol et l'échelle restent celles que l'IA a dessinées). Un nom « - » saute la ligne ;
« nom1,nom2,nom3,nom4 » donne un nom à chaque case (images indépendantes, recadrées chacune au plus près).
Règles de génération : films/REGLES_PLANCHES_JEU.md.
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

from films.outils.planche_pixel import cases, quantifier
from films.outils.planche_vecteur import DOSSIER, FAMILLES, EPS, contours
from films.styles.pixel_info import PALETTE_ICONES


def dessin(q, x0, y0, x1, y1):
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(q.shape[1], x1), min(q.shape[0], y1)
    c = q[y0:y1, x0:x1]
    zones = {}
    for i, col in enumerate(PALETTE_ICONES):
        fam, ton = FAMILLES[tuple(col)]
        m = c == i + 1
        if m.sum() >= 30:
            cs = contours(m)
            if cs:
                zones.setdefault(fam, {}).setdefault(str(ton), []).extend(cs)
    sil = contours(cv2.morphologyEx((c > 0).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0, 200,
                   EPS + 0.3)
    return {"taille": [x1 - x0, y1 - y0], "zones": zones, "silhouette": sil}


def convertir(chemin, cols, lignes, noms):
    a = np.asarray(Image.open(chemin).convert("RGB"))
    q = quantifier(a)
    h, w = q.shape
    cw, ch = w / cols, h / lignes
    boites = cases(q, cols, lignes)
    out = {}
    for r, nom in enumerate(noms[:lignes]):
        if nom == "-":
            continue
        bs = [boites[r * cols + k] for k in range(cols)]
        if "," in nom:                                         # images indépendantes
            for b, n in zip(bs, nom.split(",")):
                if b is not None and n != "-":
                    out[n] = dessin(q, b[0] - 4, b[1] - 4, b[2] + 4, b[3] + 4)
            continue
        rel = [(b[0] - k * cw, b[1] - r * ch, b[2] - k * cw, b[3] - r * ch) for k, b in enumerate(bs) if b is not None]
        fx0, fy0 = min(b[0] for b in rel) - 4, min(b[1] for b in rel) - 4    # la fenêtre commune de la ligne
        fx1, fy1 = max(b[2] for b in rel) + 4, max(b[3] for b in rel) + 4
        for k in range(cols):
            if bs[k] is not None:
                ox, oy = k * cw, r * ch
                out[f"{nom}_{k + 1}"] = dessin(q, int(ox + fx0), int(oy + fy0), int(ox + fx1), int(oy + fy1))
    return out


def main():
    src, grille = sys.argv[1], sys.argv[2]
    cols, lignes = map(int, grille.split("x"))
    os.makedirs(DOSSIER, exist_ok=True)
    for nom, d in convertir(src, cols, lignes, sys.argv[3:]).items():
        json.dump(d, open(os.path.join(DOSSIER, nom + ".json"), "w"))
        n = sum(len(v) for z in d["zones"].values() for v in z.values())
        print(f"{nom} : {d['taille'][0]} × {d['taille'][1]} px, {n} zones")


if __name__ == "__main__":
    main()
