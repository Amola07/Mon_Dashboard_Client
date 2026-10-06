"""Feuille d'animation (une image IA en grille : la même action à plusieurs instants) → images successives en traits.

    python -m films.outils.feuille_animation feuille.png nom 6x4
    → films/animations/nom.json  (une liste de dessins, dans l'ordre de lecture)

Chaque case garde sa position dans sa propre case (le personnage peut s'y déplacer) ; toutes les cases sont recalées
sur leur ligne de sol et mises à la même échelle. Le trait de sol et ce qui est dessous sont retirés.

Dans un tableau :
    from films.outils.feuille_animation import plan
    faisceau(c, plan(["p04_1", "p04_2"], t - t0, x=540, pied=1330, haut=560), 1.0, VERT_PALE, 1.2)
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


def lignes_de_sol(noir, rangs):
    """Les lignes de sol de la feuille : des rangées très remplies (les rangées de cases ne sont pas toujours égales)."""
    H, L = noir.shape
    cnt = noir.sum(1)
    ys = [y for y in range(H) if cnt[y] > 0.3 * L]
    groupes = []
    for y in ys:
        if groupes and y - groupes[-1][-1] <= 3:
            groupes[-1].append(y)
        else:
            groupes.append([y])
    sols = [int(np.median(g)) for g in groupes]
    return sols if len(sols) == rangs else None


def centres_de_cases(ligne, cols, L):
    """Le centre de chaque case, d'après les morceaux du trait de sol."""
    segs, x = [], 0
    while x < L:
        if ligne[x]:
            a = x
            while x < L and ligne[x]:
                x += 1
            segs.append((a, x))
        x += 1
    segs = [sg for sg in segs if sg[1] - sg[0] > L / cols * 0.3]
    if len(segs) != cols:
        return [(c + 0.5) * L / cols for c in range(cols)]
    return [(a + b) / 2 for a, b in segs]


def lisser_tailles(images, fen=5, tol=0.15):
    """L'IA dessine parfois une case un peu plus grande ou plus petite : on ramène chaque image vers la taille médiane
    de ses voisines (un vrai changement de taille, comme s'accroupir, dure plusieurs images et n'est pas touché)."""
    hs = [max(1e-6, -min(y for l in im for _, y in l)) for im in images]
    out = []
    for k, im in enumerate(images):
        m = float(np.median(hs[max(0, k - fen // 2):k + fen // 2 + 1]))
        f = m / hs[k]
        f = f if abs(f - 1) <= tol else 1.0
        out.append([[(x * f, y * f) for x, y in l] for l in im])
    return out


def decouper(chemin, cols, rangs):
    img = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
    noir = img < 128
    H, L = noir.shape
    sols = lignes_de_sol(noir, rangs)
    rangees = []
    for r in range(rangs):
        if sols:                                                  # bande : de la ligne de sol précédente à la sienne
            y0 = sols[r - 1] + 4 if r else 0
            y_sol = sols[r]
            centres = centres_de_cases(noir[y_sol] | noir[y_sol + 1], cols, L)
        else:                                                     # sans sol (apesanteur) : bandes égales
            y0, y_sol = r * H // rangs, (r + 1) * H // rangs
            centres = [(c + 0.5) * L / cols for c in range(cols)]
        haut = cv2.morphologyEx(noir[y0:y_sol - 3].astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        rangee = []
        for c, masque in enumerate(personnages(haut, cols)):
            lignes = ordonner(simplifier(suivre(amincir(masque)), eps=1.1))
            rangee.append([[(x - centres[c], y + y0 - y_sol) for x, y in l] for l in lignes])
        rangees.append(rangee)
    # une rangée dessinée plus petite ou plus grande que les autres par l'IA : on la remet à l'échelle commune
    med = [np.median([-min(y for l in im for _, y in l) for im in rg]) for rg in rangees]
    ref = float(np.median(med))
    images = []
    for rg, m in zip(rangees, med):
        k = ref / m if abs(ref / m - 1) > 0.08 else 1.0
        images += [[[(x * k, y * k) for x, y in l] for l in im] for im in rg]
    images = lisser_tailles(images)
    ch = H / rangs
    hauteur = -min(y for l in images[0] for _, y in l)            # échelle : la hauteur de la première image (debout)
    if hauteur < 0.5 * ch:                                        # personnage allongé ou à quatre pattes : on prend la
        hauteur = 0.63 * ch                                       # taille habituelle d'un personnage debout dans une case
    return {"largeur_case": 0.0,
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


def _haut(im):
    ys = [y for l in im for _, y in l]
    return max(ys) - min(ys)


def _bas(im):
    return max(y for l in im for _, y in l)


_SUITES = {}


def suite(noms):
    """Les images de plusieurs feuilles enchaînées (un plan) : la case 1 d'une feuille de suite reprend la dernière
    de la précédente, on la retire, et on recale l'échelle et le bas sur cette dernière image."""
    cle = tuple(noms)
    if cle not in _SUITES:
        images = list(animation(noms[0])["images"])
        for nom in noms[1:]:
            ims = animation(nom)["images"]
            k = _haut(images[-1]) / max(_haut(ims[0]), 1e-6)
            dy = _bas(images[-1]) - _bas(ims[0]) * k
            images += [[[(px * k, py * k + dy) for px, py in l] for l in im] for im in ims[1:]]
        _SUITES[cle] = images
    return _SUITES[cle]


def plan(noms, u, x, pied, haut, fps=24, miroir=False, vitesse=1.0):
    """Le dessin d'un plan au temps u : un dessin par image à 24 i/s, la dernière image est tenue (jamais de boucle).
    `vitesse` < 1 donne un ralenti."""
    images = suite([noms] if isinstance(noms, str) else noms)
    k = min(len(images) - 1, max(0, int(u * fps * vitesse)))
    sx = -1 if miroir else 1
    return [[(x + sx * px * haut, pied + py * haut) for px, py in l] for l in images[k]]


def duree(noms, fps=24):
    return len(suite([noms] if isinstance(noms, str) else noms)) / fps


def main():
    src, nom, grille = sys.argv[1], sys.argv[2], sys.argv[3]
    cols, rangs = (int(v) for v in grille.split("x"))
    d = decouper(src, cols, rangs)
    os.makedirs(DOSSIER, exist_ok=True)
    json.dump(d, open(os.path.join(DOSSIER, nom + ".json"), "w"))
    print(f"{nom} : {len(d['images'])} images, " + ", ".join(str(sum(len(l) for l in im)) for im in d["images"]) + " points")


if __name__ == "__main__":
    main()
