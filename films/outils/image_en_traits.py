"""Convertit une illustration au trait (image PNG/JPG, par exemple générée par IA) en traits pour le faisceau.

    python -m films.outils.image_en_traits image.png nom   → films/illustrations/nom.json + output/nom_traits.png

Étapes : noir et blanc → squelette d'un pixel (amincissement de Zhang-Suen) → suivi des lignes → simplification →
ordre de tracé de proche en proche. Les points sont ramenés dans une boîte [0, 1] (largeur = 1).

Dans un tableau :
    from films.outils.image_en_traits import dessin
    trace(c, t, t0, 1.2, dessin("voiture", x=200, y=700, largeur=680), VERT_PALE, 1.2)
"""
import json
import math
import os
import sys

import cv2
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "..", "illustrations")
VOISINS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def binaire(chemin, max_cote=900):
    img = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f"image illisible : {chemin}")
    k = max_cote / max(img.shape)
    if k < 1:
        img = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    _, b = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if (b > 0).mean() > 0.5:                                   # traits sombres sur fond clair : on inverse
        b = 255 - b
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(b, 8)  # on retire les poussières
    garde = np.zeros(n, bool)
    garde[1:] = stats[1:, cv2.CC_STAT_AREA] >= 25
    return garde[lab]


def amincir(img):
    """Squelette d'un pixel (Zhang-Suen), en numpy."""
    I = img.astype(np.uint8).copy()
    while True:
        change = False
        for etape in (0, 1):
            P = np.pad(I, 1)
            p2, p3, p4, p5 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:], P[2:, 2:]
            p6, p7, p8, p9 = P[2:, 1:-1], P[2:, :-2], P[1:-1, :-2], P[:-2, :-2]
            B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            A = sum(((seq[k] == 0) & (seq[k + 1] == 1)).astype(np.uint8) for k in range(8))
            if etape == 0:
                c = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                c = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            m = (I == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if m.any():
                I[m] = 0
                change = True
        if not change:
            return I.astype(bool)


def suivre(sq):
    """Transforme le squelette en lignes continues (d'une extrémité ou d'un carrefour à l'autre)."""
    pix = set(zip(*np.nonzero(sq)))

    def vois(p):
        """Voisins utiles : les 4 directs, et un diagonal seulement s'il n'est pas déjà relié par un direct
        (sinon chaque marche d'escalier du squelette ferait un faux carrefour)."""
        y, x = p
        out = [(y + dy, x + dx) for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)) if (y + dy, x + dx) in pix]
        for dy, dx in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            q = (y + dy, x + dx)
            if q in pix and (y + dy, x) not in pix and (y, x + dx) not in pix:
                out.append(q)
        return out

    deg = {p: len(vois(p)) for p in pix}
    noeuds = [p for p in pix if deg[p] != 2]
    vu = set()
    lignes = []

    def arete(a, b):
        return (a, b) if a < b else (b, a)

    def marcher(depart, suivant):
        ligne = [depart, suivant]
        vu.add(arete(depart, suivant))
        prec, cur = depart, suivant
        while deg[cur] == 2:
            nxt = [q for q in vois(cur) if q != prec and arete(cur, q) not in vu]
            if not nxt:
                break
            vu.add(arete(cur, nxt[0]))
            prec, cur = cur, nxt[0]
            ligne.append(cur)
        return ligne

    for n in noeuds:
        for q in vois(n):
            if arete(n, q) not in vu:
                lignes.append(marcher(n, q))
    for p in pix:                                              # boucles fermées sans extrémité
        for q in vois(p):
            if arete(p, q) not in vu:
                lignes.append(marcher(p, q))
    return [[(x, y) for y, x in l] for l in lignes]


def simplifier(lignes, eps=1.3, mini=4):
    out = []
    for l in lignes:
        if len(l) < 2:
            continue
        a = np.array(l, np.float32).reshape(-1, 1, 2)
        if cv2.arcLength(a, False) < mini:
            continue
        s = cv2.approxPolyDP(a, eps, False).reshape(-1, 2)
        out.append([(float(x), float(y)) for x, y in s])
    return out


def ordonner(lignes):
    """Ordre de tracé naturel : on part du haut à gauche, puis toujours la ligne la plus proche."""
    reste = list(lignes)
    if not reste:
        return []
    cur = min(reste, key=lambda l: l[0][1] + l[0][0] * 0.5)
    reste.remove(cur)
    ordre = [cur]
    while reste:
        fin = ordre[-1][-1]
        meilleur, inv, d = None, False, 1e18
        for l in reste:
            for rev, p in ((False, l[0]), (True, l[-1])):
                dd = math.dist(fin, p)
                if dd < d:
                    meilleur, inv, d = l, rev, dd
        reste.remove(meilleur)
        l = meilleur[::-1] if inv else meilleur
        if d < 4:                                              # la suite directe d'un même trait : on raccorde
            ordre[-1] = ordre[-1] + l[1:]
        else:
            ordre.append(l)
    return ordre


def convertir(chemin):
    lignes = ordonner(simplifier(suivre(amincir(binaire(chemin)))))
    xs = [p[0] for l in lignes for p in l]
    ys = [p[1] for l in lignes for p in l]
    x0, y0, w = min(xs), min(ys), max(max(xs) - min(xs), 1e-6)
    return {"ratio": (max(ys) - y0) / w,
            "traits": [[(round((x - x0) / w, 4), round((y - y0) / w, 4)) for x, y in l] for l in lignes]}


def dessin(nom, x, y, largeur, miroir=False):
    """Les traits d'une illustration, placés avec son coin haut-gauche en (x, y)."""
    d = json.load(open(os.path.join(DOSSIER, nom + ".json")))
    return [[(x + (1 - px if miroir else px) * largeur, y + py * largeur) for px, py in l] for l in d["traits"]]


def main():
    src, nom = sys.argv[1], sys.argv[2]
    d = convertir(src)
    os.makedirs(DOSSIER, exist_ok=True)
    json.dump(d, open(os.path.join(DOSSIER, nom + ".json"), "w"))
    n = sum(len(l) for l in d["traits"])
    print(f"{nom} : {len(d['traits'])} traits, {n} points")
    import skia
    from films.styles.oscillo_ascenseur import VERT_PALE, faisceau
    W = 900
    H = int(W * d["ratio"]) + 120
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(skia.Color(2, 8, 4))
    faisceau(c, dessin(nom, 60, 60, W - 120), 1.0, VERT_PALE, 1.1)
    os.makedirs("output", exist_ok=True)
    s.makeImageSnapshot().save(f"output/{nom}_traits.png")


if __name__ == "__main__":
    main()
