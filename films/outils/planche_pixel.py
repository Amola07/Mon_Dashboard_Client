"""Une planche d'icônes pixel art générée par IA → une icône PNG transparente par case, en vrais pixels, à notre palette.

    python -m films.outils.planche_pixel planche.webp 3x3 5 nom1 nom2 … nom9
      3x3 : colonnes × lignes de la grille ; 5 : taille d'un « pixel » de l'IA, en pixels de l'image (≈ 4 à 7)
    → films/illustrations_pixel/nomK.png  (+ output/planche_pixel_apercu.png)

Étapes : le fond noir devient transparent ; chaque pixel est ramené à la couleur la plus proche de la palette
(films/styles/pixel_info.PALETTE_ICONES) ; l'image est réduite à la taille réelle de ses pixels en gardant la couleur
majoritaire de chaque bloc (pas de flou) ; les morceaux de dessin sont regroupés par case de la grille.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

from films.styles.pixel_info import PALETTE_ICONES

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "..", "illustrations_pixel")


def quantifier(a):
    """Indice de la couleur de palette la plus proche (0 = fond transparent)."""
    pal = np.array(PALETTE_ICONES, np.float32)
    fond = a.max(axis=2) < 28
    d = ((a[..., None, :].astype(np.float32) - pal[None, None]) ** 2).sum(-1)
    q = d.argmin(-1) + 1
    q[fond] = 0
    return q


def reduire(q, f):
    """Réduit par le facteur f en gardant, pour chaque bloc, l'indice majoritaire (le fond ne gagne qu'à plus de 60 %)."""
    h, w = q.shape
    H, W = int(h / f), int(w / f)
    out = np.zeros((H, W), np.int32)
    n = len(PALETTE_ICONES) + 1
    for y in range(H):
        y0, y1 = int(y * f), max(int(y * f) + 1, int((y + 1) * f))
        for x in range(W):
            x0, x1 = int(x * f), max(int(x * f) + 1, int((x + 1) * f))
            c = np.bincount(q[y0:y1, x0:x1].ravel(), minlength=n)
            tot = c.sum()
            if c[0] > 0.6 * tot:
                continue
            c[0] = 0
            out[y, x] = c.argmax()
    return out


def cases(q, cols, lignes):
    """Regroupe les morceaux de dessin par case de la grille → [(x0, y0, x1, y1)] dans l'ordre de lecture."""
    masque = ndimage.binary_dilation(q > 0, iterations=2)
    lab, n = ndimage.label(masque)
    h, w = q.shape
    boites = [None] * (cols * lignes)
    for i, sl in enumerate(ndimage.find_objects(lab)):
        ys, xs = sl
        if (ys.stop - ys.start) * (xs.stop - xs.start) < 12:
            continue                                                       # poussière
        cy, cx = (ys.start + ys.stop) / 2, (xs.start + xs.stop) / 2
        k = min(lignes - 1, int(cy / h * lignes)) * cols + min(cols - 1, int(cx / w * cols))
        b = boites[k]
        boites[k] = (xs.start, ys.start, xs.stop, ys.stop) if b is None else \
            (min(b[0], xs.start), min(b[1], ys.start), max(b[2], xs.stop), max(b[3], ys.stop))
    return boites


def convertir(chemin, cols, lignes, f):
    a = np.asarray(Image.open(chemin).convert("RGB"))
    q = reduire(quantifier(a), f)
    pal = np.array([(0, 0, 0)] + list(PALETTE_ICONES), np.uint8)
    icones = []
    for b in cases(q, cols, lignes):
        if b is None:
            icones.append(None)
            continue
        x0, y0, x1, y1 = b
        c = q[y0:y1, x0:x1]
        rgba = np.dstack([pal[c], np.where(c > 0, 255, 0).astype(np.uint8)])
        icones.append(Image.fromarray(rgba, "RGBA"))
    return icones


def apercu(icones, noms, chemin):
    k = 3
    larg = sum((i.width if i else 10) * k + 20 for i in icones) + 20
    haut = max((i.height if i else 10) for i in icones) * k + 40
    pl = Image.new("RGB", (larg, haut), (6, 10, 12))
    x = 20
    for i in icones:
        if i:
            pl.paste(i.resize((i.width * k, i.height * k), Image.NEAREST), (x, 20), i.resize((i.width * k, i.height * k), Image.NEAREST))
            x += i.width * k + 20
    pl.save(chemin)


def main():
    src, grille, f = sys.argv[1], sys.argv[2], float(sys.argv[3])
    cols, lignes = map(int, grille.split("x"))
    noms = sys.argv[4:]
    icones = convertir(src, cols, lignes, f)
    os.makedirs(DOSSIER, exist_ok=True)
    for nom, ic in zip(noms, icones):
        if ic is None:
            print(f"{nom} : case vide")
            continue
        ic.save(os.path.join(DOSSIER, nom + ".png"))
        print(f"{nom} : {ic.width} × {ic.height} pixels")
    os.makedirs("output", exist_ok=True)
    apercu(icones, noms, "output/planche_pixel_apercu.png")


if __name__ == "__main__":
    main()
