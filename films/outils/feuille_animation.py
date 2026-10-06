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
    """Sépare les n personnages d'une rangée : dans chaque colonne, le plus grand morceau sert de départ ; chaque autre
    morceau (objet lancé, traits de vitesse, bouts détachés) rejoint le groupe le plus proche, de proche en proche."""
    k, lab, st, cen = cv2.connectedComponentsWithStats(img, 8)
    L = img.shape[1]
    ids = [i for i in range(1, k) if st[i, cv2.CC_STAT_AREA] >= 25]
    pts = {}
    for i in ids:
        p = np.argwhere(lab == i)
        pts[i] = p[:: max(1, len(p) // 300)]
    graines = []                                                  # les plus grands morceaux, bien espacés en largeur
    for i in sorted(ids, key=lambda i: -st[i, cv2.CC_STAT_AREA]):
        if len(graines) == n:
            break
        if all(abs(cen[i][0] - cen[g][0]) > 0.55 * L / n for g in graines):
            graines.append(i)
    graines.sort(key=lambda i: cen[i][0])
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
    return [np.isin(lab, [i for i, j in groupe.items() if j == c]) for c in range(len(graines))]


def traits_de_sol(noir, cols, gris=None):
    """Les traits de sol (longs traits horizontaux, parfois pâles, un peu penchés ou coupés) : masque + morceaux
    (y, x0, x1). Un trait de sol se répète à la même hauteur dans plusieurs cases d'une rangée, contrairement aux
    rayures d'une doudoune."""
    H, L = noir.shape
    trait = gris < 200 if gris is not None else noir
    epais = cv2.dilate(trait.astype(np.uint8), np.ones((5, 9), np.uint8))
    long = cv2.morphologyEx(epais, cv2.MORPH_OPEN, np.ones((1, int(L / cols * 0.35)), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(long, 8)
    cand = [(float(cen[i][1]), st[i, cv2.CC_STAT_LEFT], st[i, cv2.CC_STAT_LEFT] + st[i, cv2.CC_STAT_WIDTH], i)
            for i in range(1, n) if st[i, cv2.CC_STAT_HEIGHT] < 22]
    # sous un trait de sol, c'est vide ; sous une rayure de doudoune ou de combinaison, il y a la suite du corps
    cand = [m for m in cand if trait[int(m[0]) + 6:int(m[0]) + 18, m[1]:m[2]].mean() < 0.04]
    gardes = [m for m in cand if sum(1 for o in cand if abs(o[0] - m[0]) < 8) >= max(2, cols - 1)]
    # un personnage allongé dessine aussi des traits horizontaux répétés : seul le plus bas d'une rangée est le sol
    gardes.sort(key=lambda m: -m[0])
    sols = []
    for m in gardes:
        if not any(0 < y - m[0] < 0.6 * H / 4 for y in sols) or any(abs(y - m[0]) < 8 for y in sols):
            sols.append(m[0])
    gardes = [m for m in gardes if any(abs(y - m[0]) < 0.1 for y in sols)]
    masque = cv2.dilate(np.isin(lab, [m[3] for m in gardes]).astype(np.uint8), np.ones((5, 3), np.uint8)) > 0
    return masque, [m[:3] for m in gardes]


def rangees_de_sol(morceaux, H, rangs):
    """Regroupe les traits de sol par rangée ; None si on n'en trouve pas une par rangée."""
    groupes = []
    for m in sorted(morceaux):
        if groupes and m[0] - groupes[-1][-1][0] < H / rangs * 0.4:
            groupes[-1].append(m)
        else:
            groupes.append([m])
    return groupes if len(groupes) == rangs else None


def sans_poussieres(noir, mini=14):
    """Retire les petits morceaux isolés : flocons, débris de trait de sol, points."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(noir.astype(np.uint8), 8)
    garde = np.zeros(n, bool)
    garde[1:] = np.maximum(st[1:, cv2.CC_STAT_WIDTH], st[1:, cv2.CC_STAT_HEIGHT]) >= mini
    return garde[lab]


def coupures(noir, rangs):
    """Sans trait de sol : chaque limite entre rangées passe là où il y a le moins d'encre, près de sa place attendue
    (au milieu d'un espace vide quand il y en a un)."""
    H = noir.shape[0]
    occ = noir.sum(1).astype(float)
    bornes = [0]
    for r in range(1, rangs):
        att = r * H / rangs
        a, b = int(att - 0.15 * H / rangs * 2), int(att + 0.15 * H / rangs * 2)
        fen = occ[a:b]
        m = fen.min()
        ys = np.nonzero(fen <= m)[0]                              # le milieu de la plus longue plage minimale
        runs, debut = [], ys[0]
        for u, v in zip(ys, ys[1:]):
            if v != u + 1:
                runs.append((debut, u))
                debut = v
        runs.append((debut, ys[-1]))
        d, f = max(runs, key=lambda x: x[1] - x[0])
        bornes.append(a + (d + f) // 2)
    return bornes + [H]


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
    masque, morceaux = traits_de_sol(noir, cols, img)
    groupes = rangees_de_sol(morceaux, H, rangs)
    noir = sans_poussieres(noir & ~masque)                        # on efface tous les traits de sol, flocons, débris
    ys = [float(np.median([m[0] for m in g])) for g in groupes] if groupes else None
    bornes = coupures(noir, rangs)
    vus = []
    rangees = []
    for r in range(rangs):
        if ys:                                                    # bande : du dessous du sol précédent à son sol
            y0 = int(ys[r - 1] + (ys[r] - ys[r - 1]) * 0.15) if r else 0
            y1 = int(ys[r]) + 4
            dans = groupes[r]
        else:                                                     # bandes égales ; un sol s'il y en a un dans la bande
            y0, y1 = bornes[r], bornes[r + 1]
            dans = [m for m in morceaux if y0 + (y1 - y0) * 0.5 < m[0] <= y1 + 6]
        bande = cv2.morphologyEx(noir[y0:y1].astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        masques = personnages(bande, cols)
        segs = sorted(dans, key=lambda m: m[1])
        if len(segs) == cols:
            centres = [(m[1] + m[2]) / 2 for m in segs]
            sols = [m[0] for m in segs]
        else:
            centres = [(c + 0.5) * L / cols for c in range(cols)]
            if dans:
                sols = [float(np.median([m[0] for m in dans]))] * cols
            else:                                                 # sans sol : le bas des personnages de la rangée
                bas = [y0 + np.nonzero(m.any(1))[0].max() for m in masques if m.any()]
                sols = [float(np.median(bas))] * cols
        if len(segs) != cols and len(masques) == cols:            # sans sol par case : on garde les masques pour
            vus.append([float(np.median(np.nonzero(m)[1])) if m.any() else np.nan for m in masques])  # recaler la grille
        rangee = []
        for c, m in enumerate(masques):
            lignes = ordonner(simplifier(suivre(amincir(m)), eps=1.1))
            rangee.append([[(x - centres[c], y + y0 - sols[c]) for x, y in l] for l in lignes])
        rangees.append(rangee)
    if len(vus) == rangs:                                         # grille réelle : x = a + b·colonne (moindres carrés)
        cs = np.array([c for _ in vus for c in range(cols)], float)
        xs = np.array([x for r in vus for x in r], float)
        ok = ~np.isnan(xs)
        b, a = np.polyfit(cs[ok], xs[ok], 1)
        ancien = [(c + 0.5) * L / cols for c in range(cols)]
        rangees = [[[[(x + ancien[c] - (a + b * c), y) for x, y in l] for l in im] for c, im in enumerate(rg)]
                   for rg in rangees]

    def taille(im):
        ys = [y for l in im for _, y in l]
        return max(ys) - min(ys) if ys else 1.0

    images = list(rangees[0])                                     # l'IA rapetisse souvent les rangées du bas : chaque
    for rg in rangees[1:]:                                        # rangée reprend la taille où la précédente s'arrête
        k = np.median([taille(im) for im in images[-2:]]) / max(1e-6, np.median([taille(im) for im in rg[:2]]))
        k = k if 0.75 < k < 1.33 and abs(k - 1) > 0.04 else 1.0
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
        _SUITES[cle] = stabiliser(images)
    return _SUITES[cle]


def stabiliser(images, fen=7):
    """Retire le tremblement gauche-droite d'une image à l'autre (l'IA ne place jamais le personnage exactement au
    même endroit) en gardant le vrai déplacement : la position suit sa moyenne glissante sur `fen` images."""
    xs = np.array([np.median([x for l in im for x, _ in l]) if im else 0.0 for im in images])
    n = len(xs)
    lisse = np.array([xs[max(0, k - fen // 2):k + fen // 2 + 1].mean() for k in range(n)])
    return [[[(x + lisse[k] - xs[k], y) for x, y in l] for l in im] for k, im in enumerate(images)]


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
