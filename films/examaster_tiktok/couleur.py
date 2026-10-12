"""Une planche d'illustrations EN COULEURS (aplats + contours sombres, fond blanc) → un dessin « oscilloscope en couleurs » par case.

    python -m films.examaster_tiktok.couleur planche.webp 3x3 nom1 … nom9
    → films/examaster_tiktok/data/nomK.json

Pour chaque case :
  - les traits fins sombres (contours, plis, détails du visage) → lignes d'un pixel (squelette) → tracées au faisceau ;
  - les grandes masses sombres (cheveux) → zone à hachurer ;
  - chaque couleur d'aplat (palette trouvée par k-moyennes sur toute la planche, donc la même d'une case à l'autre)
    → des hachures de faisceau (lignes parallèles serrées, un angle par couleur) qui « peignent » la zone.
Les coordonnées restent dans le repère de la case (pour garder l'alignement d'une case à l'autre : bouches, poses).
"""
import json
import os
import sys

import cv2
import numpy as np

from films.outils.image_en_traits import amincir, ordonner, simplifier, suivre

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "data")
SEUIL_FOND = 236                                  # un pixel dont les 3 canaux dépassent ça est du fond
SEUIL_SOMBRE = 52                                 # en dessous (niveau de gris), c'est de l'encre ou un cheveu (la peau fait ≈ 108, le pantalon ≈ 65)
ANGLES = [0, 45, -45, 0, 90, 30, -30, 60]


def premier_plan(img):
    return img.min(axis=2) <= SEUIL_FOND


def coupures(fg, n, axe):
    """Limites des n bandes d'une planche : là où il y a le moins de dessin près de la coupe régulière."""
    taille = fg.shape[axe]
    encre = np.convolve(fg.sum(axis=1 - axe).astype(float), np.ones(9) / 9, mode="same")
    bornes = [0]
    for k in range(1, n):
        c = k * taille // n
        lo, hi = max(c - int(0.18 * taille / n), 0), min(c + int(0.18 * taille / n), taille)
        zone = encre[lo:hi]
        creux = np.flatnonzero(zone <= zone.min() + 1e-9)
        bornes.append(lo + int(creux[len(creux) // 2]))
    bornes.append(taille)
    return bornes


def palette(img, k=9):
    """Les couleurs d'aplat de la planche (hors fond, hors traits sombres), par k-moyennes."""
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = premier_plan(img) & (gris >= SEUIL_SOMBRE + 8)
    px = img[m].astype(np.float32)
    if len(px) > 60000:
        px = px[np.random.default_rng(0).choice(len(px), 60000, replace=False)]
    _, _, centres = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    return centres[np.argsort(centres.sum(axis=1))]          # du plus sombre au plus clair (BGR)


def hachures(masque, pas, angle):
    """Lignes parallèles serrées remplissant un masque, avec un angle ; sens alterné (le faisceau fait des allers-retours)."""
    h, w = masque.shape
    d = int(np.hypot(w, h)) + 4
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    M[:, 2] += ((d - w) / 2, (d - h) / 2)
    rot = cv2.warpAffine(masque.astype(np.uint8), M, (d, d), flags=cv2.INTER_NEAREST)
    Mi = cv2.invertAffineTransform(M)
    segs, sens = [], 1
    for y in range(0, d, pas):
        ligne = np.concatenate([[0], rot[y], [0]])
        dif = np.diff(ligne.astype(np.int8))
        deb, fin = np.flatnonzero(dif == 1), np.flatnonzero(dif == -1)
        runs = [(a, b - 1) for a, b in zip(deb, fin) if b - a >= 3]
        if sens < 0:
            runs = runs[::-1]
        for a, b in runs:
            p0, p1 = (a, y), (b, y)
            if sens < 0:
                p0, p1 = p1, p0
            segs.append([tuple(np.round(Mi @ np.array([*p, 1.0]), 1)) for p in (p0, p1)])
        sens = -sens
    return [[(float(x), float(y)) for x, y in s] for s in segs]


def convertir_case(img, pal):
    fg = premier_plan(img).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
    garde = np.zeros(n, bool)
    garde[1:] = st[1:, cv2.CC_STAT_AREA] >= max(80, 0.04 * st[1:, cv2.CC_STAT_AREA].max())   # poussières et voisins qui débordent
    fg = garde[lab]
    ys, xs = np.nonzero(fg)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else [0, 0, 1, 1]
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sombre = (gris < SEUIL_SOMBRE) & fg
    cheveux = cv2.morphologyEx(sombre.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))).astype(bool)
    fin = cv2.morphologyEx(gris, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 30   # traits fins plus sombres que leur voisinage
    traits = (sombre | (fin & fg.astype(bool))) & ~cv2.dilate(cheveux.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    lignes = ordonner(simplifier(suivre(amincir(traits)), eps=1.2, mini=4))
    zones = []
    if cheveux.any():
        zones.append({"couleur": [int(v) for v in img[cheveux][:, ::-1].mean(axis=0)], "role": "cheveux",
                      "hachures": hachures(cheveux, 3, 0)})
    clair = fg & ~sombre
    d2 = ((img.astype(np.float32)[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(axis=3)
    etiquette = d2.argmin(axis=2)
    for j in range(len(pal)):
        m = (etiquette == j) & clair
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        if m.sum() < 60:
            continue
        zones.append({"couleur": [int(v) for v in pal[j][::-1]], "role": f"zone{j}",
                      "hachures": hachures(m, 3, ANGLES[j % len(ANGLES)])})
    return {"px": [bbox[2] - bbox[0], bbox[3] - bbox[1]], "bbox": bbox, "masque_fg": fg,
            "lignes": [[(round(x, 1), round(y, 1)) for x, y in l] for l in lignes], "zones": zones}


def main():
    chemin, grille, noms = sys.argv[1], sys.argv[2], sys.argv[3:]
    cols, rangs = (int(v) for v in grille.split("x"))
    img = cv2.imread(chemin)
    fg = premier_plan(img)
    bl, br = coupures(fg, cols, 1), coupures(fg, rangs, 0)
    pal = palette(img)
    os.makedirs(DOSSIER, exist_ok=True)
    cases = []
    for k, nom in enumerate(noms):
        r, c = divmod(k, cols)
        d = convertir_case(img[br[r]:br[r + 1], bl[c]:bl[c + 1]], pal)
        cases.append(d)
    # alignement des cases entre elles (utile pour les bouches : même tête, seule la bouche change)
    H = max(d["masque_fg"].shape[0] for d in cases)
    L = max(d["masque_fg"].shape[1] for d in cases)

    def pad(m):
        z = np.zeros((H, L), np.float32)
        z[:m.shape[0], :m.shape[1]] = m
        return z

    ref = pad(cases[0]["masque_fg"])
    for nom, d in zip(noms, cases):
        m = pad(d.pop("masque_fg"))
        (dx, dy), _ = cv2.phaseCorrelate(ref, m)
        d["decalage"] = [round(-dx, 1), round(-dy, 1)]
        json.dump(d, open(os.path.join(DOSSIER, nom + ".json"), "w"))
        nh = sum(len(z["hachures"]) for z in d["zones"])
        print(f"{nom} : {len(d['lignes'])} traits, {len(d['zones'])} zones, {nh} hachures, taille {d['px']}, décalage {d['decalage']}")
    print("palette (RGB) :", [tuple(int(v) for v in p[::-1]) for p in pal])


if __name__ == "__main__":
    main()
