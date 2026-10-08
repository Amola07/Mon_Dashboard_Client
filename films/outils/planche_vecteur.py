"""Une planche d'icônes générée par IA → un dessin VECTORIEL précis par case (pour l'oscilloscope 2.0).

    python -m films.outils.planche_vecteur planche.webp 3x3 nom1 … nom9
    python -m films.outils.planche_vecteur planche.webp 3x3 --pixel nom1 … nom9   (planche en pixel art : on efface
                                                                                  les marches d'escalier des bords)
    → films/illustrations_vecteur/nomK.json  (+ output/planche_vecteur_apercu.png)

Contrairement à planche_pixel (qui réduit l'image à ses « vrais pixels » pour le style pixel), on garde ici la pleine
définition de la planche : chaque zone de couleur (ramenée à la palette) devient un contour précis, à peine lissé.
Format : {"taille": [l, h], "zones": {"ambre"|"vert"|"pale": {"ton": [contours]}}, "silhouette": [contours]}.
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

from films.outils.planche_pixel import cases, quantifier
from films.styles.pixel_info import PALETTE_ICONES

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "..", "illustrations_vecteur")
FAMILLES = {(40, 175, 175): ("vert", 1), (26, 110, 112): ("vert", 2), (14, 52, 56): ("vert", 3),
            (128, 214, 214): ("vert", 0), (255, 138, 61): ("ambre", 1), (255, 196, 140): ("ambre", 0),
            (168, 72, 26): ("ambre", 2), (236, 242, 240): ("pale", 0), (120, 130, 132): ("pale", 2),
            (188, 198, 198): ("pale", 1), (66, 76, 80): ("pale", 3)}


def lisser(l, n=1):
    for _ in range(n):
        if len(l) < 4:
            return l
        m = [l[0]]
        for a, b in zip(l, l[1:]):
            m += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        m.append(l[-1])
        l = m
    return l


EPS, LISSAGE = 1.2, 1


def contours(masque, aire_min=30, eps=None):
    eps = EPS if eps is None else eps
    m = masque.astype(np.uint8) * 255
    noyau = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, noyau), cv2.MORPH_CLOSE, noyau)   # bruit de l'IA
    cs, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        if cv2.contourArea(c) < aire_min:
            continue
        c = cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float)
        pts = [(round(x, 1), round(y, 1)) for x, y in c] + [(round(c[0][0], 1), round(c[0][1], 1))]
        out.append([(round(x, 1), round(y, 1)) for x, y in lisser(pts, LISSAGE)])
    return out


def convertir(chemin, cols, lignes):
    a = np.asarray(Image.open(chemin).convert("RGB"))
    q = quantifier(a)
    boites = cases(q, cols, lignes)
    dessins = []
    for b in boites:
        if b is None:
            dessins.append(None)
            continue
        x0, y0, x1, y1 = b
        x0, y0, x1, y1 = max(0, x0 - 4), max(0, y0 - 4), min(q.shape[1], x1 + 4), min(q.shape[0], y1 + 4)
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
        dessins.append({"taille": [x1 - x0, y1 - y0], "zones": zones, "silhouette": sil})
    return dessins


def main():
    src, grille = sys.argv[1], sys.argv[2]
    cols, lignes = map(int, grille.split("x"))
    global EPS, LISSAGE
    noms = [n for n in sys.argv[3:] if n != "--pixel"]
    if "--pixel" in sys.argv:
        EPS, LISSAGE = 3.2, 2
    os.makedirs(DOSSIER, exist_ok=True)
    for nom, d in zip(noms, convertir(src, cols, lignes)):
        if d is None:
            print(f"{nom} : case vide")
            continue
        json.dump(d, open(os.path.join(DOSSIER, nom + ".json"), "w"))
        n = sum(len(v) for z in d["zones"].values() for v in z.values())
        print(f"{nom} : {d['taille'][0]} × {d['taille'][1]} px, {n} zones")


if __name__ == "__main__":
    main()
