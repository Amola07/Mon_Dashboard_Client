"""Épisode 24 — « Des éclairs dans un bocal » (Miller-Urey, 1952) — style oscilloscope, ≈ 65 s.

Moteur de l'épisode 21 ; dessins générés par IA et convertis en traits (films/illustrations/, outil
films/outils/image_en_traits.py).

    python -m films.episodes.ep24_miller.oscillo_ep24 output/ep24_oscillo.mp4
"""
import json
import math
import os
import sys

import numpy as np
import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, P, W, cercle_pts, ease, ecrit, faisceau,
                                                         fleche, rect_pts, titres, trace)
from films.outils.image_en_traits import DOSSIER, dessin
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
M.SEGS = os.path.join(HERE, "audio", "voix.json")
s, e = M.s, M.e
RNG = np.random.default_rng(24)


def ratio(nom):
    return json.load(open(os.path.join(DOSSIER, nom + ".json")))["ratio"]


def centre(nom, cx, cy, largeur):
    """Un dessin centré en (cx, cy)."""
    return dessin(nom, cx - largeur / 2, cy - largeur * ratio(nom) / 2, largeur)


def bocal(cx, cy, largeur):
    """Le bocal et son éclair, séparés (l'éclair se dessine en ambre)."""
    x0, y0 = cx - largeur / 2, cy - largeur * ratio("bocal_eclair") / 2
    tr = dessin("bocal_eclair", x0, y0, largeur)
    pot, foudre = [], []
    for l in tr:
        xs = [(p[0] - x0) / largeur for p in l]
        ys = [(p[1] - y0) / largeur for p in l]
        dedans = min(xs) >= 0.18 and max(xs) <= 0.8 and min(ys) >= 0.38 and max(ys) <= 1.72
        (foudre if dedans else pot).append(l)
    return pot, foudre


def etincelles(cx, cy, r, t, n=7):
    """Petites décharges qui crépitent autour d'un point."""
    tr = []
    for k in range(n):
        a = k * 2.4 + t * 13 + math.sin(t * 7 + k)
        l = r * (0.5 + 0.5 * abs(math.sin(t * 9 + k * 1.7)))
        pts = [(cx, cy)]
        for j in range(1, 4):
            d = l * j / 3
            pts.append((cx + d * math.cos(a) + RNG.normal(0, r * 0.12), cy + d * math.sin(a) + RNG.normal(0, r * 0.12)))
        tr.append(pts)
    return tr


def molecule(cx, cy, larg):
    return centre("molecule", cx, cy, larg)


# ------------------------------------------------------------------------------------------------ tableaux
def tab_accroche(c, t):
    gras = 1.0 + 0.8 * (1 - ease(t / 2.0))
    pot, foudre = bocal(540, 1040, 470)
    faisceau(c, pot, 1.0, VERT_PALE, 1.3 * gras)
    vif = 0.55 + 0.45 * abs(math.sin(t * 11)) * (0.6 + 0.4 * math.sin(t * 3.1))
    faisceau(c, foudre, 1.0, AMBRE, 1.6 * gras, vif)
    faisceau(c, etincelles(560, 1000, 120, t), 1.0, AMBRE, 0.8, 0.6 * vif)
    if t < s(1):
        ecrit(c, t, -1.0, "DES ÉCLAIRS", W / 2, 300, 96, AMBRE, True, 2.2, vitesse=0.0)
        ecrit(c, t, -1.0, "DANS UN BOCAL", W / 2, 400, 96, AMBRE, True, 2.2, vitesse=0.0)
    else:
        ecrit(c, t, s(1) + 0.9, "= LES BRIQUES", W / 2, 300, 88, VERT_PALE, True, 2.0, vitesse=0.0)
        ecrit(c, t, s(1) + 1.1, "DE LA VIE", W / 2, 400, 88, VERT_PALE, True, 2.0, vitesse=0.0)
        for k, (x, y) in enumerate(((470, 1220), (620, 1290), (520, 1380))):     # les molécules apparaissent
            if t > s(1) + 0.9 + 0.25 * k:
                bob = 8 * math.sin(t * 2 + k)
                trace(c, t, s(1) + 0.9 + 0.25 * k, 0.4, molecule(x, y + bob, 150), VERT_PALE, 0.9, bip=1500 + 200 * k)


def tab_miller(c, t):
    t0 = s(2)
    an = int(round(2026 - (2026 - 1952) * ease((t - t0) / 1.0)))
    ecrit(c, t, t0, f"{an}", W / 2, 470, 170, AMBRE, True, 2.2, vitesse=0.0)
    trace(c, t, s(3) - 0.2, 1.2, centre("etudiant", 540, 1040, 620), VERT_PALE, 1.1, bip=1100)
    ecrit(c, t, s(3) + 0.3, "STANLEY MILLER", W / 2, 1440, 52, VERT_PALE, True, 1.6)
    ecrit(c, t, s(3) + 1.6, "22 ANS · ÉTUDIANT", W / 2, 1510, 36, VERT)
    if t > s(4):                                                              # la question
        c.drawRect(skia.Rect(0, 560, W, 1560), P((2, 8, 4), 0, 215 * ease((t - s(4)) / 0.4), fill=True))
        ecrit(c, t, s(4) + 0.2, "COMMENT LA VIE", W / 2, 820, 76, VERT_PALE, True, 1.8)
        ecrit(c, t, s(4) + 0.6, "EST-ELLE APPARUE ?", W / 2, 910, 76, AMBRE, True, 1.8)
        trace(c, t, s(5), 0.8, [cercle_pts(540, 1180, 150, 60)], VERT, 1.0, bip=1100)
        ecrit(c, t, s(5) + 0.6, "?", 540, 1235, 150, AMBRE, True, 2.0, vitesse=0.0)
        ecrit(c, t, s(5) + 0.9, "TERRE SANS VIE", W / 2, 1400, 34, VERT)


# position des pièces de l'appareil, dans le repère du dessin (largeur = 1)
APP_X, APP_Y, APP_L = 190, 455, 700
PIECES = {"ballon": (0.159, 0.84), "eau": (0.159, 0.81), "sphere": (0.806, 0.373), "etincelle": (0.806, 0.367),
          "condenseur": (0.794, 0.796), "flamme": (0.129, 1.044)}


def piece(nom):
    px, py = PIECES[nom]
    return APP_X + px * APP_L, APP_Y + py * APP_L


def tab_appareil(c, t):
    t0 = s(6)
    titres(c, t, [(t0, "LA TERRE PRIMITIVE", VERT_PALE, 64), (s(7), "EN MINIATURE", AMBRE, 72),
                  (s(10), "UNE SEMAINE PLUS TARD", VERT_PALE, 56)])
    if t < s(7):                                                              # le paysage d'origine
        trace(c, t, t0, 1.6, centre("terre_primitive", 540, 950, 900), VERT_PALE, 1.0, bip=1100)
        return
    trace(c, t, s(7) - 0.1, 2.2, dessin("appareil_miller", APP_X, APP_Y, APP_L), VERT_PALE, 1.1, bip=900)
    bx, by = piece("ballon")
    if t > s(7) + 0.6:                                                        # l'eau qui bout
        for k in range(7):
            ph = (t * 0.9 + k / 7) % 1
            x = bx - 60 + (k * 23) % 120
            faisceau(c, [cercle_pts(x, by + 50 - ph * 90, 6 + 4 * ph, 10)], 1.0, VERT_PALE, 0.6, 1 - ph)
    lbl = [(s(7) + 1.3, "OCÉAN", (470, 1010), (bx + 40, by - 10)),
           (s(8) + 2.6, "ATMOSPHÈRE", (470, 770), (piece("sphere")[0] - 95, piece("sphere")[1] + 20)),
           (s(9) + 3.0, "ÉCLAIRS", (470, 670), (piece("etincelle")[0] - 30, piece("etincelle")[1]))]
    for tl, txt, (lx, ly), (px, py) in lbl:
        if t > tl and t < s(10) + 0.2:
            ecrit(c, t, tl, txt, lx, ly, 40, AMBRE, True, 1.6)
            trace(c, t, tl + 0.1, 0.3, [[(lx, ly + 12), (px, py)]], AMBRE, 0.8, bip=1700)
    if s(8) <= t:                                                             # les gaz
        sx, sy = piece("sphere")
        for k, g in enumerate(("CH4", "NH3", "H2")):
            if t > s(8) + 0.7 * k:
                a = t * 0.8 + k * 2.1
                ecrit(c, t, s(8) + 0.7 * k, g, sx + 70 * math.cos(a), sy + 55 * math.sin(a) + 10, 26, VERT_PALE,
                      vitesse=0.0)
    if t > s(9) + 0.5:                                                        # les étincelles
        ex, ey = piece("etincelle")
        faisceau(c, etincelles(ex, ey, 70, t, 9), 1.0, AMBRE, 1.0, 0.6 + 0.4 * abs(math.sin(t * 17)))
    if t > s(10):                                                             # une semaine : l'eau se colore
        jour = 1 + int(6 * ease((t - s(10)) / 2.0))
        ecrit(c, t, s(10), f"JOUR {jour}", 470, 760, 52, VERT_PALE, True, 1.6, vitesse=0.0)
        teinte = ease((t - s(11)) / 1.4)
        if t > s(10) + 0.5:
            r = 105
            traits = [[(bx - math.sqrt(max(0, r * r - (y - by) ** 2)), y), (bx + math.sqrt(max(0, r * r - (y - by) ** 2)), y)]
                      for y in np.arange(by - 20, by + r - 5, 12)]
            faisceau(c, traits, 1.0, AMBRE, 0.6, 0.25 + 0.7 * teinte)
        if t > s(11):
            ecrit(c, t, s(11), "ROSE", 470, 860, 44, AMBRE, True, 1.4, vitesse=0.0)
            ecrit(c, t, s(11) + 0.75, "→ ROUGE BRUN", 470, 930, 40, AMBRE, True, 1.4, vitesse=0.0)


def tab_acides(c, t):
    t0 = s(12)
    titres(c, t, [(t0, "DES ACIDES AMINÉS", AMBRE, 66), (s(13), "LES BRIQUES DES PROTÉINES", VERT_PALE, 50),
                  (s(14), "APPARUES TOUTES SEULES", AMBRE, 54)])
    if t < s(13):
        trace(c, t, t0 + 0.1, 1.0, molecule(540, 900, 760), AMBRE, 1.4, bip=1500)
        return
    k = ease((t - s(13)) / 0.6)
    n = 5
    for i in range(n):                                                        # une chaîne : une protéine
        x = 150 + i * 195
        y = 900 + 70 * math.sin(i * 1.3 + t * 1.5) * k
        trace(c, t, s(13) + 0.15 * i, 0.3, molecule(x, y, 180), AMBRE if i == 2 else VERT_PALE, 1.0,
              bip=1300 + 150 * i)
        if i:
            px = 150 + (i - 1) * 195
            py = 900 + 70 * math.sin((i - 1) * 1.3 + t * 1.5) * k
            trace(c, t, s(13) + 0.15 * i, 0.2, [[(px + 85, py), (x - 85, y)]], VERT, 0.8, bip=0)
    ecrit(c, t, s(13) + 0.9, "PROTÉINE", W / 2, 1120, 46, VERT_PALE, True, 1.4)
    ecrit(c, t, s(13) + 1.4, "TOUS LES ÊTRES VIVANTS", W / 2, 1190, 34, VERT)


def tab_nuance(c, t):
    t0 = s(15)
    ecrit(c, t, t0 + 0.1, "LA VIE", W / 2, 640, 110, VERT_PALE, True, 1.8, vitesse=0.0)
    trace(c, t, t0 + 0.6, 0.25, [[(330, 560), (750, 680)], [(750, 560), (330, 680)]], AMBRE, 2.2, bip=500)
    if t > s(16):
        trace(c, t, s(16), 0.8, centre("nuage", 540, 980, 520), VERT_PALE, 1.0, bip=1100)
        ecrit(c, t, s(16) + 1.0, "SES INGRÉDIENTS : OUI", W / 2, 1330, 56, AMBRE, True, 1.6)
        for i in range(4):                                                    # les briques naissent des éclairs
            tb = s(16) + 1.2 + 0.4 * i
            if t > tb:
                u = min(1.0, (t - tb) / 1.6)
                trace(c, t, tb, 0.2, molecule(400 + 90 * i, 1130 + 120 * u, 110), VERT_PALE, 0.8, bip=1600 + 100 * i)


def tab_flacons(c, t):
    t0 = s(17)
    titres(c, t, [(t0, "LE PLUS FOU…", AMBRE, 76), (s(18), "2008", AMBRE, 110)], halo=2.0)
    if t > s(18) + 0.2:
        trace(c, t, s(18) + 0.2, 1.2, centre("flacons_carton", 540, 900, 780), VERT_PALE, 1.0, bip=1100)
        ecrit(c, t, s(18) + 2.0, "OUBLIÉS DANS DES CARTONS", W / 2, 1250, 40, VERT)
    if t > s(19):
        n = int(round(22 * ease((t - s(19) - 0.5) / 2.2)))
        c.drawRect(skia.Rect(0, 1150, W, 1290), P((2, 8, 4), 0, 230, fill=True))
        ecrit(c, t, s(19), f"{n}", W / 2, 1300, 150, AMBRE, True, 2.2, vitesse=0.0)
        ecrit(c, t, s(19), "ACIDES AMINÉS", W / 2, 1380, 44, VERT_PALE, True, 1.4, vitesse=0.0)
    if t > s(20):
        ecrit(c, t, s(20), "BIEN PLUS QUE MILLER N'AVAIT VU", W / 2, 1450, 32, VERT_PALE)


def tab_question(c, t):
    t0 = s(21)
    pot, foudre = bocal(540, 820, 300)
    trace(c, t, t0, 0.6, pot, VERT_PALE, 1.1, bip=1100)
    faisceau(c, foudre, 1.0, AMBRE, 1.4, 0.6 + 0.4 * abs(math.sin(t * 11)))
    ecrit(c, t, t0 + 0.2, "ET VOUS ?", W / 2, 360, 120, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, t0 + 0.6, "RECRÉER LA VIE", W / 2, 1180, 56, VERT_PALE)
    ecrit(c, t, t0 + 1.0, "EN LABORATOIRE ?", W / 2, 1250, 56, VERT_PALE)
    if t > s(22):
        ecrit(c, t, s(22), "DITES-LE EN COMMENTAIRE", 500, 1360, 40, VERT_PALE, True, 1.5)
        b = 18 * abs(math.sin((t - s(22)) * 5))
        trace(c, t, s(22) + 0.2, 0.25, fleche(800 + b, 1346, 960 + b, 1346, 26), AMBRE, 1.8, bip=1700)
    if t > s(23):
        ecrit(c, t, s(23), "+ ABONNEZ-VOUS", W / 2, 1460, 46, AMBRE, True, 1.6)
        ecrit(c, t, s(23) + 0.5, "LA PROCHAINE EXPÉRIENCE ARRIVE", W / 2, 1520, 30, VERT)


def tableaux():
    return [(0.0, tab_accroche, None), (s(2) - 0.1, tab_miller, "neige"), (s(6) - 0.1, tab_appareil, "balayage"),
            (s(12) - 0.1, tab_acides, "glitch"), (s(15) - 0.1, tab_nuance, "noir"), (s(17) - 0.1, tab_flacons, "neige"),
            (s(21) - 0.1, tab_question, "balayage")]


def chocs():
    flashs = [s(1), s(9) + 3.0, s(12), s(18)]
    secousses = [(s(1), 0.2), (s(9) + 3.0, 0.15), (s(15) + 0.6, 0.15)]
    return flashs, secousses


def effets(tabs):
    ev = [(0.0, Z.crepitement(s(1) + 1.0, 0.12, 60)), (0.0, Z.vibration(1.4, 0.10)), (0.05, Z.craquement(0.3)),
          (0.6, Z.craquement(0.25)), (1.3, Z.craquement(0.3)), (s(1), Z.boom(0.5, 60)), (s(1) + 0.05, Z.snap(0.3))]
    ev += [(s(1) + 0.9 + 0.25 * k, Z.cloche(784 * 2 ** (k * 4 / 12), 0.08)) for k in range(3)]
    ev += [(s(2), Z.whoosh(1.0, 0.1, False)), (s(2) + 1.0, Z.thump(0.35)), (s(3), Z.cliquet(0.1)),
           (s(4), Z.riser(1.2, 0.08)), (s(4) + 0.2, Z.boom(0.3, 70)), (s(5) + 0.6, Z.chirp(400, 900, 0.3, 0.07))]
    ev += [(s(6), Z.vent(1.8, 0.08, 100, 500)), (s(6) + 0.4, Z.boom(0.2, 50)), (s(7), Z.bulles(2.5, 0.10)),
           (s(7) + 1.3, Z.cloche(523.3, 0.08)), (s(8) + 2.6, Z.cloche(659.3, 0.08)),
           (s(9) + 0.5, Z.crepitement(3.0, 0.14, 90)), (s(9) + 3.0, Z.snap(0.4)), (s(9) + 3.0, Z.cloche(784, 0.1)),
           (s(10), Z.tictac(2.0, 0.07, 0.3)), (s(11), Z.chirp(500, 300, 0.4, 0.06)), (s(11) + 0.75, Z.chirp(400, 200, 0.4, 0.06))]
    ev += [(s(12), Z.boom(0.45, 70)), (s(12) + 0.1, Z.scintillement(1.2, 0.06))]
    ev += [(s(13) + 0.15 * i, Z.pince(523.3 * 2 ** (i * 2 / 12), 0.08)) for i in range(5)]
    ev += [(s(14), Z.cloche(1046.5, 0.1)), (s(15) + 0.6, Z.thump(0.4)), (s(15) + 0.6, Z.alarme(0.06, 1)),
           (s(16), Z.vent(1.5, 0.06, 150, 800)), (s(16) + 1.0, Z.cloche(880, 0.1))]
    ev += [(s(17), Z.riser(0.9, 0.08)), (s(18), Z.boom(0.5, 60)), (s(18) + 0.3, Z.whoosh(0.6, 0.08))]
    ev += [(s(19) + 0.5 + 0.1 * i, Z.cliquet(0.05)) for i in range(22)]
    ev += [(s(19) + 2.7, Z.cloche(784, 0.1)), (s(19) + 2.75, Z.cloche(1046.5, 0.08)),
           (s(21), Z.boom(0.35, 70)), (s(21), Z.crepitement(1.0, 0.06, 40)), (s(22) + 0.2, Z.pince(784, 0.08)),
           (s(22) + 0.35, Z.pince(988, 0.08)), (s(22) + 0.5, Z.pince(1175, 0.08)), (s(23), Z.cloche(698.5, 0.1, 2.5))]
    for t0, _, tr in tabs[1:]:
        ev.append((t0, {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
                        "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}[tr]()))
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep24_oscillo.mp4")
