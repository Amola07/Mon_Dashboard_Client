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
