"""Feuille d'animation (une image IA en grille : la même action à plusieurs instants) → images successives en traits.

    python -m films.outils.feuille_animation feuille.png nom 4x2
    → films/animations/nom.json  (une liste de dessins, dans l'ordre de lecture)

Chaque case garde sa position dans sa propre case (le personnage peut s'y déplacer) ; toutes les cases sont recalées
sur leur ligne de sol et mises à la même échelle. Le trait de sol et ce qui est dessous sont retirés.

Dans un tableau :
    from films.outils.feuille_animation import image_anim
    faisceau(c, image_anim("lancer", t - t0, x=540, pied=1330, haut=520), 1.0, VERT_PALE, 1.2)
"""
import json
import os
import sys

import cv2
import numpy as np

from films.outils.image_en_traits import amincir, ordonner, simplifier, suivre

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "..", "animations")


def sol(cell):
    """La ligne de sol : la rangée la plus remplie dans la moitié basse de la case."""
    cnt = cell.sum(1)
    h = len(cnt)
    return h // 2 + int(np.argmax(cnt[h // 2:]))


def personnages(img, n):
    """Sépare les n personnages d'une rangée : les n plus grands morceaux, puis chaque petit morceau (objet lancé,
    traits de vitesse) rejoint le groupe le plus proche, de proche en proche."""
    k, lab, st, _ = cv2.connectedComponentsWithStats(img, 8)
    ids = [i for i in range(1, k) if st[i, cv2.CC_STAT_AREA] >= 25]
    pts = {}
    for i in ids:
        p = np.argwhere(lab == i)
        pts[i] = p[:: max(1, len(p) // 300)]
    graines = sorted(sorted(ids, key=lambda i: -st[i, cv2.CC_STAT_AREA])[:n], key=lambda i: st[i, cv2.CC_STAT_LEFT])
    groupe = {g: j for j, g in enumerate(graines)}
    reste = [i for i in ids if i not in groupe]
    while reste:
        best = None
        for i in reste:
            for g in groupe:
                d = np.min(np.linalg.norm(pts[i][:, None, :] - pts[g][None, :, :], axis=2))
                if best is None or d < best[0]:
                    best = (d, i, g)
        _, i, g = best
        groupe[i] = groupe[g]
        reste.remove(i)
    return [np.isin(lab, [i for i, j in groupe.items() if j == c]) for c in range(n)]


def decouper(chemin, cols, rangs):
    img = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
    noir = img < 128
    H, L = noir.shape
    ch, cl = H // rangs, L // cols
    images = []
    for r in range(rangs):
        bande = noir[r * ch:(r + 1) * ch]
        sols = [sol(bande[:, c * cl:(c + 1) * cl]) for c in range(cols)]
        trait = np.median([bande[y, c * cl:(c + 1) * cl].sum() for c, y in enumerate(sols)])
        y_sol = int(np.median(sols)) if trait > 0.25 * cl else ch + 3   # sans ligne de sol (en apesanteur) : le bas de la case
        haut = cv2.morphologyEx(bande[:y_sol - 3].astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        for c, masque in enumerate(personnages(haut, cols)):
            lignes = ordonner(simplifier(suivre(amincir(masque)), eps=1.1))
            x0 = c * cl                                           # repère de la case : coin gauche, ligne de sol
            images.append([[(x - x0, y - y_sol) for x, y in l] for l in lignes])
    hauteur = -min(y for l in images[0] for _, y in l)            # échelle : la hauteur de la première image (debout)
    if hauteur < 0.5 * ch:                                        # personnage allongé ou à quatre pattes : on prend la
        hauteur = 0.63 * ch                                       # taille habituelle d'un personnage debout dans une case
    larg = cl / hauteur
    return {"largeur_case": larg,
            "images": [[[(round(x / hauteur, 4), round(y / hauteur, 4)) for x, y in l] for l in im] for im in images]}


_CACHE = {}


def animation(nom):
    if nom not in _CACHE:
        _CACHE[nom] = json.load(open(os.path.join(DOSSIER, nom + ".json")))
    return _CACHE[nom]


def pose_anim(nom, k, x, pied, haut, miroir=False):
    """L'image k, centrée en x (centre de la case), pieds en `pied`, de hauteur `haut` (hauteur de la 1re image)."""
    a = animation(nom)
    cx = a["largeur_case"] / 2
    sx = -1 if miroir else 1
    return [[(x + sx * (px - cx) * haut, pied + py * haut) for px, py in l] for l in a["images"][k]]


def image_anim(nom, u, x, pied, haut, durees=None, miroir=False):
    """L'image affichée au temps u (secondes) ; `durees` donne le temps de chaque image (12 i/s par défaut)."""
    n = len(animation(nom)["images"])
    durees = durees or [1 / 12] * n
    k = 0
    while k < n - 1 and u >= durees[k]:
        u -= durees[k]
        k += 1
    return pose_anim(nom, k, x, pied, haut, miroir)


def main():
    src, nom, grille = sys.argv[1], sys.argv[2], sys.argv[3]
    cols, rangs = (int(v) for v in grille.split("x"))
    d = decouper(src, cols, rangs)
    os.makedirs(DOSSIER, exist_ok=True)
    json.dump(d, open(os.path.join(DOSSIER, nom + ".json"), "w"))
    print(f"{nom} : {len(d['images'])} images, " + ", ".join(str(sum(len(l) for l in im)) for im in d["images"]) + " points")


if __name__ == "__main__":
    main()
