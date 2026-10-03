"""Découpe la planche Gemini (planche.webp) en pièces RGBA détourées (pieces/*.png) + positions dans la planche."""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NOMS = {(103, 26): "complet", (566, 47): "tete", (1340, 71): "appareil", (768, 126): "torse",
        (1132, 178): "bras_d_haut", (606, 267): "bras_g_haut", (1108, 406): "avbras_d", (650, 431): "avbras_g",
        (986, 487): "jambe_d", (707, 489): "jambe_g", (1293, 422): "bouche_fermee", (1293, 501): "bouche_mi",
        (1293, 573): "bouche_ouverte", (1462, 431): "sourcil_g", (1549, 431): "sourcil_d", (1465, 454): "oeil_g",
        (1552, 454): "oeil_d", (1462, 542): "sourcil_g_ferme", (1549, 542): "sourcil_d_ferme",
        (1467, 584): "oeil_g_ferme", (1555, 584): "oeil_d_ferme"}


def main():
    im = cv2.imread(os.path.join(HERE, "planche.webp"), cv2.IMREAD_COLOR)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    mask = (g < 238).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask, 8)
    os.makedirs(os.path.join(HERE, "pieces"), exist_ok=True)
    pos = {}
    for i in range(1, n):
        x, y, w, h, a = st[i]
        nom = next((v for (kx, ky), v in NOMS.items() if abs(kx - x) <= 4 and abs(ky - y) <= 4), None)
        if nom is None or a < 300:
            continue
        m = (lab[y:y + h, x:x + w] == i).astype(np.uint8) * 255
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        full = np.zeros_like(m)
        cv2.drawContours(full, cs, -1, 255, -1)                  # trous remplis (blanc des yeux, dents)
        if nom == "complet":                                       # sauf le personnage entier : les jours
            full = m.copy()                                         # entre bras et corps restent transparents
        full = cv2.erode(full, np.ones((3, 3), np.uint8))               # retire le liseré blanc
        alpha = cv2.GaussianBlur(full, (3, 3), 0)
        p = 2
        rgba = np.zeros((h + 2 * p, w + 2 * p, 4), np.uint8)
        rgba[p:-p, p:-p, :3] = im[y:y + h, x:x + w]
        rgba[p:-p, p:-p, 3] = alpha
        cv2.imwrite(os.path.join(HERE, "pieces", f"{nom}.png"), rgba)
        pos[nom] = [int(x) - p, int(y) - p, int(w) + 2 * p, int(h) + 2 * p]
    json.dump(pos, open(os.path.join(HERE, "pieces", "positions.json"), "w"), indent=1)
    print(len(pos), "pièces")


if __name__ == "__main__":
    main()
