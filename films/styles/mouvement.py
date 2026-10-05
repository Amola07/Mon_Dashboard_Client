"""Personnages animés par des mouvements MoMask (films/mouvements/*.npy), projetés en 2D pour le faisceau.

Un mouvement = articulations 3D (22 points, 20 images/s, y vers le haut). On le voit de profil (légèrement de
trois quarts), tourné vers la droite (sens=1) ou la gauche (sens=-1), accroché par le bassin ou par les pieds.
"""
import math
import os

import numpy as np

from films.styles.oscillo_ascenseur import cercle_pts

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mouvements")
CHAINES = [[0, 2, 5, 8, 11], [0, 1, 4, 7, 10], [0, 3, 6, 9, 12, 15], [9, 14, 17, 19, 21], [9, 13, 16, 18, 20]]
_CACHE = {}


def charger(nom):
    if nom not in _CACHE:
        j = np.load(os.path.join(DOSSIER, nom + ".npy"))
        h = j[0, 2] - j[0, 1]                                           # hanche droite − hanche gauche
        avant = np.cross([0.0, 1.0, 0.0], h)
        avant[1] = 0
        avant /= np.linalg.norm(avant) + 1e-9
        cote = np.cross(avant, [0.0, 1.0, 0.0])
        _CACHE[nom] = (j, avant, cote)
    return _CACHE[nom]


def instant(t, debut=0.0, fin=None, boucle=None, n=None):
    """Temps dans le mouvement : de `debut` à `fin` (s), puis figé, ou en boucle ('aller-retour')."""
    fin = fin if fin is not None else n / 20.0
    d = max(1e-6, fin - debut)
    if boucle == "aller-retour":
        u = (t / d) % 2.0
        u = u if u <= 1 else 2 - u
        return debut + u * d
    return debut + min(max(t, 0.0), d)


def figure(nom, t, cx, cy, ech, sens=1, ancre="bassin", debut=0.0, fin=None, boucle=None, rot=0.0, profondeur=0.3):
    """Les traits du personnage à l'instant t. (cx, cy) = position du bassin (ou du sol sous lui si ancre='pieds')."""
    j, avant, cote = charger(nom)
    f = instant(t, debut, fin, boucle, len(j)) * 20
    f = min(max(f, 0.0), len(j) - 1.001)
    i = int(f)
    a = j[i] + (j[i + 1] - j[i]) * (f - i)
    r = a[0].copy()
    if ancre == "pieds":
        r[1] = 0.0
    cr, sr = math.cos(rot), math.sin(rot)
    pts = []
    for p in a:
        d = p - r
        x = sens * (d @ avant + profondeur * (d @ cote)) * ech
        y = -d[1] * ech
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    tr = [[pts[k] for k in ch] for ch in CHAINES]
    cou, tete = np.array(pts[12]), np.array(pts[15])
    centre = tete + (tete - cou) * 0.6
    tr.append(cercle_pts(centre[0], centre[1], 0.1 * ech, 18))
    return tr


# ------------------------------------------------------------------------------------------------ corps en volume
import skia  # noqa: E402

from films.styles.oscillo_ascenseur import P  # noqa: E402

# (articulation a, articulation b, rayon en a, rayon en b) — en mètres, proportions d'un adulte
TRONC = [(0, 3, 0.15, 0.14), (3, 6, 0.14, 0.13), (6, 9, 0.135, 0.16), (9, 12, 0.12, 0.065), (12, 15, 0.06, 0.055),
         (9, 13, 0.11, 0.07), (9, 14, 0.11, 0.07), (13, 16, 0.07, 0.06), (14, 17, 0.07, 0.06),
         (0, 1, 0.13, 0.10), (0, 2, 0.13, 0.10)]
MEMBRES = {
    "bras_g": [(16, 18, 0.055, 0.042), (18, 20, 0.042, 0.03), (20, "main", 0.035, 0.022)],
    "bras_d": [(17, 19, 0.055, 0.042), (19, 21, 0.042, 0.03), (21, "main", 0.035, 0.022)],
    "jambe_g": [(1, 4, 0.085, 0.055), (4, 7, 0.055, 0.037), (7, 10, 0.042, 0.03)],
    "jambe_d": [(2, 5, 0.085, 0.055), (5, 8, 0.055, 0.037), (8, 11, 0.042, 0.03)],
}


def _capsule(a, b, ra, rb, n=9):
    """Contour d'un segment de membre qui s'affine de ra à rb (deux cercles reliés par leurs tangentes)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    p = skia.Path()
    if L < 1e-3 or L <= abs(ra - rb):
        p.addCircle(a[0], a[1], max(ra, rb))
        return p
    ang = math.atan2(dy, dx)
    phi = math.acos(max(-1.0, min(1.0, (ra - rb) / L)))
    pts = [(b[0] + rb * math.cos(ang - phi + 2 * phi * k / n), b[1] + rb * math.sin(ang - phi + 2 * phi * k / n))
           for k in range(n + 1)]
    pts += [(a[0] + ra * math.cos(ang + phi + (2 * math.pi - 2 * phi) * k / (2 * n)),
             a[1] + ra * math.sin(ang + phi + (2 * math.pi - 2 * phi) * k / (2 * n))) for k in range(2 * n + 1)]
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def _union(chemins):
    tot = chemins[0]
    for q in chemins[1:]:
        r = skia.Op(tot, q, skia.PathOp.kUnion_PathOp)
        tot = r if r is not None else tot
    return tot


def corps(nom, t, cx, cy, ech, sens=1, ancre="bassin", debut=0.0, fin=None, boucle=None, rot=0.0, profondeur=0.3,
          taille=1.0):
    """Les volumes du corps à l'instant t : [(chemin, profondeur)], du plus lointain au plus proche."""
    j, avant, cote = charger(nom)
    f = instant(t, debut, fin, boucle, len(j)) * 20
    f = min(max(f, 0.0), len(j) - 1.001)
    i = int(f)
    a = j[i] + (j[i + 1] - j[i]) * (f - i)
    r = a[0].copy()
    if ancre == "pieds":
        r[1] = 0.0
    cr, sr = math.cos(rot), math.sin(rot)
    pts, prof = [], []
    for p in a:
        d = p - r
        x = sens * (d @ avant + profondeur * (d @ cote)) * ech
        y = -d[1] * ech
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
        prof.append(sens * (d @ cote))
    R = ech * taille

    def point(k, prec):
        if k == "main":                                            # la main prolonge l'avant-bras
            u, v = pts[prec[0]], pts[prec[1]]
            return (v[0] + (v[0] - u[0]) * 0.32, v[1] + (v[1] - u[1]) * 0.32)
        return pts[k]

    morceaux = []
    tronc = [_capsule(pts[a_], pts[b_], ra * R, rb * R) for a_, b_, ra, rb in TRONC]
    tete, cou = np.array(pts[15]), np.array(pts[12])
    centre = tete + (tete - cou) * 0.55
    ch = skia.Path()
    ch.addOval(skia.Rect(centre[0] - 0.095 * R, centre[1] - 0.115 * R, centre[0] + 0.095 * R, centre[1] + 0.115 * R))
    tronc.append(ch)
    morceaux.append((_union(tronc), 0.0))
    for nom_m, segs in MEMBRES.items():
        chemins = []
        for a_, b_, ra, rb in segs:
            pa = pts[a_]
            pb = point(b_, (segs[1][0], segs[1][1]) if b_ == "main" else None)
            chemins.append(_capsule(pa, pb, ra * R, rb * R))
        idx = [s_[0] for s_ in segs]
        morceaux.append((_union(chemins), float(np.mean([prof[k] for k in idx]))))
    morceaux.sort(key=lambda m: -m[1])                              # le plus loin d'abord
    return morceaux


def dessiner(c, morceaux, col, w=1.0, intense=1.0, fond=(2, 8, 4)):
    """Chaque volume : rempli de noir (il cache ce qui est derrière), puis son contour au faisceau."""
    for chemin, _ in morceaux:
        c.drawPath(chemin, P(fond, 0, 255, fill=True))
        for wl, a_, b_ in ((12 * w, 40, 14), (5 * w, 110, 4), (2.0 * w, 255, 0)):
            c.drawPath(chemin, P(col, wl, a_ * intense, b_))
