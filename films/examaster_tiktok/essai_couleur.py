"""Essai : le personnage d'ExaMaster en « oscilloscope en couleurs » (poses puis tête qui parle).

    python -m films.examaster_tiktok.essai_couleur neon output/essai_neon.mp4
    python -m films.examaster_tiktok.essai_couleur papier output/essai_papier.mp4

Données : films/examaster_tiktok/data/*.json (voir couleur.py). Deux rendus de la même image : couleurs vives sur fond
sombre (le faisceau brille), ou encre en couleurs sur papier clair.
"""
import colorsys
import json
import math
import os
import subprocess
import sys
import tempfile

import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.styles.oscillo_ascenseur import MONO, P, ease, faisceau

W, H, FPS = 1080, 1920, 30
ICI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ICI, "data")

def vif(r):
    """Couleur d'aplat → couleur de phosphore : même teinte, pleine luminosité."""
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in r))
    return tuple(int(255 * c) for c in colorsys.hsv_to_rgb(h, min(1.0, s * 1.1 + 0.05), 1.0))


def encre(r):
    """Couleur d'aplat → encre sur papier : même teinte, assez foncée pour se lire ; les gris clairs restent gris."""
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in r))
    if s < 0.12 and v > 0.7:
        return (190, 182, 170)
    return tuple(int(255 * c) for c in colorsys.hsv_to_rgb(h, min(1.0, s * 1.05 + 0.1), min(v, 0.8)))


def gris(r):
    """Noir et blanc : la couleur d'aplat devient un gris d'encre (plus la couleur est sombre, plus le trait est noir) ;
    les teintes très claires (le t-shirt) restent du papier blanc."""
    lum = 0.299 * r[0] + 0.587 * r[1] + 0.114 * r[2]
    if lum > 205:
        return None
    g = int(25 + lum * 0.9)
    return (g, g, g)


THEMES = {
    "nb": dict(fond=(252, 251, 247), contour=(14, 14, 14), cheveux=(20, 20, 20), titre="NOIR ET BLANC", ecran=False, coul=gris),
    "neon": dict(fond=(7, 6, 22), contour=(240, 244, 255), cheveux=(150, 130, 255), titre="NÉON", ecran=True, coul=vif),
    "papier": dict(fond=(250, 246, 238), contour=(27, 21, 48), cheveux=(60, 46, 120), titre="PAPIER", ecran=False, coul=encre),
}

_cache = {}


def charger(nom):
    if nom not in _cache:
        _cache[nom] = json.load(open(os.path.join(DATA, nom + ".json")))
    return _cache[nom]


def transformer(nom, ancre, X, Y, k, recale=True):
    """Polylignes de la case, placées à l'écran : le point `ancre` (repère de la case) va en (X, Y), échelle k."""
    cle = (nom, ancre, X, Y, k, recale)
    if cle in _cache:
        return _cache[cle]
    d = charger(nom)
    dx, dy = d["decalage"] if recale else (0, 0)

    def f(l):
        return [((x + dx - ancre[0]) * k + X, (y + dy - ancre[1]) * k + Y) for x, y in l]

    r = ([f(l) for l in d["lignes"]], [(z, [f(h) for h in z["hachures"]]) for z in d["zones"]])
    _cache[cle] = r
    return r


def dessiner(c, th, nom, ancre, X, Y, k, t_loc, recale=True):
    """Une case tracée au faisceau : les contours d'abord, puis chaque couleur « peinte » en hachures."""
    lignes, zones = transformer(nom, ancre, X, Y, k, recale)
    for i, (z, hach) in enumerate(zones):
        u = ease(max(0.0, min(1.0, (t_loc - (0.7 + 0.09 * i)) / 0.45)))
        if u <= 0:
            continue
        col = th["cheveux"] if z["role"] == "cheveux" else th["coul"](tuple(z["couleur"]))
        if col is None:
            continue
        faisceau(c, hach, u, col, 1.1, 1.0)
    faisceau(c, lignes, ease(max(0.0, min(1.0, t_loc / 0.9))), th["contour"], 1.0, 1.0)


def centre_bas(nom):
    x0, y0, x1, y1 = charger(nom)["bbox"]
    return ((x0 + x1) / 2, y1)


def centre(nom):
    x0, y0, x1, y1 = charger(nom)["bbox"]
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def bas_tete(nom):
    return centre_bas(nom)


PREF = os.environ.get("EXA_PREFIXE", "pz_")                       # pz_ : planche de poses en couleurs ; nbl_ : en dessin au trait
POSES = [(PREF + n, t0, v) for n, t0, v in (("salut", 0.0, 1.0), ("pointe", 2.6, 2.6), ("phone", 3.4, 2.6), ("pouce", 4.2, 2.6),
                                           ("surpris", 5.0, 2.6), ("poing", 5.8, 2.6), ("haussement", 6.6, 2.6))]
T_TETE = 7.5 if PREF == "pz_" else 99.0
PAROLE = ["ex_neutre", "ex_ah", "ex_oh", "ex_ii", "ex_ah", "ex_sourire", "ex_oh", "ex_ii", "ex_ah", "ex_neutre",
          "ex_grand_sourire", "ex_ah", "ex_oh", "ex_ii", "ex_ah", "ex_oh", "ex_sourire", "ex_ah"]
DUREE = 11.8 if PREF == "pz_" else 7.8


def image(c, th, t):
    c.clear(skia.Color(*th["fond"]))
    if t < T_TETE:
        nom, t0, v = max([p for p in POSES if p[1] <= t], key=lambda p: p[1])
        a = centre_bas(nom)
        bob = 5 * math.sin(t * 2.2) if t > 1.9 else 0
        dessiner(c, th, nom, a, 540, 1590 + bob, 2.55, (t - t0) * v, recale=False)
    else:
        tl = t - T_TETE
        if tl < 1.4:
            nom, tt = "ex_neutre", tl * 1.1
        else:
            tp = tl - 1.4
            nom = PAROLE[int(tp / 0.15) % len(PAROLE)]
            if 2.5 < tp < 2.65:
                nom = "ex_cligne"
            tt = 9.0
        dessiner(c, th, nom, bas_tete("ex_neutre"), 540, 1935, 3.0, tt)
    f = skia.Font(MONO, 34)
    c.drawString(f"ESSAI · {th['titre']}", 40, 80, f, P(th["contour"], 0, 200, fill=True))


def rendre(theme, sortie):
    th = THEMES[theme]
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-an", sortie],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for fr in range(int(DUREE * FPS)):
        t = fr / FPS
        c = surf.getCanvas()
        image(c, th, t)
        if th["ecran"]:
            M.ecran(c, t, [])
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
        if fr % 60 == 0:
            print(f"{t:5.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()
    print("OK", sortie)


if __name__ == "__main__":
    rendre(sys.argv[1], sys.argv[2])
