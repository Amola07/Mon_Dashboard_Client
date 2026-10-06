"""Épisode 25 — « Surtout… ne marchez pas » (coincé sur un lac gelé parfaitement lisse) — style oscilloscope.

Format énigme : la solution (lancer sa chaussure, troisième loi de Newton) n'arrive qu'à la fin.
Moteur de l'épisode 21 ; dessins générés par IA et convertis en traits (films/illustrations/).

    python -m films.episodes.ep25_lac_gele.oscillo_ep25 output/ep25_oscillo.mp4
"""
import json
import math
import os
import sys

import numpy as np
import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, P, W, cercle_pts, ease, ecrit, faisceau,
                                                         fleche, pointilles, titres, trace)
from films.outils.image_en_traits import DOSSIER, dessin
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
M.SEGS = os.path.join(HERE, "audio", "voix.json")
s, e = M.s, M.e
SOL = 1330                                                                    # niveau des pieds sur la glace


def ratio(nom):
    return json.load(open(os.path.join(DOSSIER, nom + ".json")))["ratio"]


def centre(nom, cx, cy, largeur, miroir=False):
    """Un dessin centré en (cx, cy)."""
    return dessin(nom, cx - largeur / 2, cy - largeur * ratio(nom) / 2, largeur, miroir)


def perso(nom, cx, haut, pied=SOL, miroir=False):
    """Un personnage de hauteur donnée, posé sur la glace (pieds en `pied`)."""
    larg = haut / ratio(nom)
    return dessin(nom, cx - larg / 2, pied - haut, larg, miroir)


def bouge(traits, dx=0.0, dy=0.0):
    return [[(x + dx, y + dy) for x, y in l] for l in traits]


def tourne(traits, cx, cy, a):
    ca, sa = math.cos(a), math.sin(a)
    return [[(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in l] for l in traits]


def lac(c, t, t0=-1.0, intense=0.55, y=650):
    """Le décor : le lac gelé en plan large."""
    trace(c, t, t0, 1.2, dessin("lac", -70, y, 1220), VERT, 0.9, intense, bip=0)


def croix(cx, cy, r=34):
    return [[(cx - r, cy - r), (cx + r, cy + r)], [(cx + r, cy - r), (cx - r, cy + r)]]


def reflets(t, cx, n=5, larg=360):
    """Petits reflets qui défilent sur la glace lisse."""
    tr = []
    for k in range(n):
        x = cx - larg / 2 + ((k * 97 + t * 40) % larg)
        y = SOL + 40 + 26 * k
        tr.append([(x, y), (x + 50 + 10 * k, y)])
    return tr


def compteur(c, t, t0, x, y):
    """Le chronomètre de l'énigme, qui tourne jusqu'à la solution."""
    if t < t0:
        return
    r = 46
    u = min(1.0, (t - t0) / (s(18) - t0))
    faisceau(c, [cercle_pts(x, y, r, 40)], 1.0, VERT, 0.8, 0.6)
    a = -math.pi / 2 + 2 * math.pi * u
    pts = [(x + r * math.cos(-math.pi / 2 + (a + math.pi / 2) * k / 30), y + r * math.sin(-math.pi / 2 + (a + math.pi / 2) * k / 30))
           for k in range(31)]
    faisceau(c, [pts], 1.0, AMBRE, 1.6)
    faisceau(c, [[(x, y), (x + 0.8 * r * math.cos(a), y + 0.8 * r * math.sin(a))]], 1.0, AMBRE, 1.2)


# ------------------------------------------------------------------------------------------------ tableaux
def tab_accroche(c, t):
    gras = 1.0 + 0.8 * (1 - ease(t / 2.0))
    lac(c, t, intense=0.6 + 0.4 * (1 - ease(t / 2.0)))
    tremble = 6 * math.sin(t * 9) * (1 - ease((t - 0.2) / 3.0)) if t < 3.2 else 0
    faisceau(c, perso("perso_debout", 540 + tremble, 600), 1.0, VERT_PALE, 1.2 * gras)
    faisceau(c, reflets(t, 540), 1.0, VERT, 0.7, 0.5)
    if t < s(2):
        k = 1 + 0.06 * abs(math.sin(t * 6)) if t > s(1) else 1.0
        ecrit(c, t, -1.0, "SURTOUT…", W / 2, 300, 70, VERT_PALE, True, 1.8, vitesse=0.0)
        ecrit(c, t, -1.0, "NE MARCHEZ", W / 2, 420, int(118 * k), AMBRE, True, 2.4, vitesse=0.0)
        ecrit(c, t, -1.0, "PAS", W / 2, 540, int(118 * k), AMBRE, True, 2.4, vitesse=0.0)
    else:
        ecrit(c, t, s(2), "GLACE PARFAITEMENT LISSE", W / 2, 330, 52, VERT_PALE, True, 1.6)
        ecrit(c, t, s(2) + 0.8, "FROTTEMENT = 0", W / 2, 420, 70, AMBRE, True, 2.0)
        ecrit(c, t, s(2) + 1.8, "COINCÉ POUR TOUJOURS ?", W / 2, 1460, 46, VERT_PALE, True, 1.6)
        for k, x in enumerate((140, 940)):                                    # le bord, inaccessible
            trace(c, t, s(2) + 1.3 + 0.2 * k, 0.4, pointilles(540 + (x - 540) * 0.25, SOL - 200, x, SOL - 200),
                  VERT, 0.8, bip=1500 + 300 * k)
        ecrit(c, t, s(2) + 1.6, "BORD", 140, SOL - 225, 30, VERT)
        ecrit(c, t, s(2) + 1.8, "BORD", 940, SOL - 225, 30, VERT)


ESSAIS = [("MARCHER", 3), ("RAMPER", 4), ("SAUTER", 5)]


def tab_essais(c, t):
    lac(c, t)
    for k, (nom, i) in enumerate(ESSAIS):                                     # la liste qui se barre
        if t > s(i):
            x = 210 + 330 * k
            ecrit(c, t, s(i), nom, x, 330, 56, VERT_PALE, True, 1.4, vitesse=0.0)
            if t > s(i) + 0.9:
                trace(c, t, s(i) + 0.9, 0.2, croix(x, 312, 40), AMBRE, 2.0, bip=500)
    if t < s(4):                                                              # marcher : les pieds patinent
        u = t - s(3)
        faisceau(c, perso("perso_glisse", 540 + 18 * math.sin(u * 14), 470), 1.0, VERT_PALE, 1.2)
        for k in range(3):
            faisceau(c, [[(380 + 60 * k + 20 * math.sin(u * 14 + k), SOL + 20), (440 + 60 * k + 20 * math.sin(u * 14 + k), SOL + 20)]],
                     1.0, VERT, 0.8, 0.6)
        ecrit(c, t, s(3) + 0.6, "LES PIEDS GLISSENT SUR PLACE", W / 2, 1480, 38, VERT)
    elif t < s(5):                                                            # ramper : pareil
        u = t - s(4)
        faisceau(c, perso("perso_rampe", 540 + 14 * math.sin(u * 12), 300), 1.0, VERT_PALE, 1.2)
        ecrit(c, t, s(4) + 0.5, "PAREIL", W / 2, 1480, 52, AMBRE, True, 1.6)
    else:                                                                     # sauter : on retombe au même endroit
        u = t - s(5)
        h = 260 * abs(math.sin(u * 2.6))
        faisceau(c, perso("perso_saut", 540, 500, SOL - h), 1.0, VERT_PALE, 1.2)
        faisceau(c, [[(440, SOL + 12), (640, SOL + 12)]], 1.0, AMBRE, 1.6)
        trace(c, t, s(5) + 0.4, 0.4, fleche(800, SOL - 380, 800, SOL - 60, 24), VERT, 1.0, bip=900)
        ecrit(c, t, s(5) + 0.9, "MÊME ENDROIT", W / 2, 1480, 52, AMBRE, True, 1.6)


def tab_defi(c, t):
    t0 = s(6)
    ecrit(c, t, t0, "UN SEUL GESTE", W / 2, 360, 92, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, t0 + 0.5, "PEUT VOUS SAUVER", W / 2, 460, 64, VERT_PALE, True, 1.6)
    trace(c, t, t0 + 0.2, 0.9, perso("perso_reflechit", 540, 640, 1300), VERT_PALE, 1.2, bip=1100)
    for k, (x, y) in enumerate(((330, 760), (770, 720), (800, 940))):         # des points d'interrogation qui flottent
        if t > t0 + 0.8 + 0.25 * k:
            ecrit(c, t, t0 + 0.8 + 0.25 * k, "?", x, y + 14 * math.sin(t * 2 + k), 96 - 16 * k, AMBRE, True, 1.8,
                  vitesse=0.0)
    if t > s(7):
        c.drawRect(skia.Rect(0, 1340, W, 1560), P((2, 8, 4), 0, 220, fill=True))
        ecrit(c, t, s(7), "TROUVEZ-LE AVANT LA FIN", W / 2, 1410, 48, VERT_PALE, True, 1.5)
        ecrit(c, t, s(7) + 1.0, "→ EN COMMENTAIRE", W / 2, 1490, 46, AMBRE, True, 1.6)
        compteur(c, t, s(7) + 0.4, 900, 1180)


def tab_pistes(c, t):
    lac(c, t, intense=0.4)
    compteur(c, t, s(7) + 0.4, 960, 230)
    titres(c, t, [(s(8), "SE TORTILLER ?", VERT_PALE, 66), (s(9), "SOUFFLER ?", VERT_PALE, 66),
                  (s(10), "ATTENDRE ?", VERT_PALE, 66)])
    if t < s(9):                                                              # le corps bouge, le centre de gravité non
        u = t - s(8)
        a = 0.22 * math.sin(u * 7)
        corps = tourne(perso("perso_debout", 540, 520), 540, SOL - 260, a)
        faisceau(c, bouge(corps, -60 * math.sin(u * 7) * 0.4), 1.0, VERT_PALE, 1.2)
        if t > s(8) + 1.2:
            g = (540, SOL - 270)
            trace(c, t, s(8) + 1.2, 0.3, [cercle_pts(*g, 16, 20), [(g[0] - 34, g[1]), (g[0] + 34, g[1])],
                                          [(g[0], g[1] - 34), (g[0], g[1] + 34)]], AMBRE, 1.6, bip=1700)
            ecrit(c, t, s(8) + 1.5, "CENTRE DE GRAVITÉ", W / 2, 1450, 44, AMBRE, True, 1.5)
            ecrit(c, t, s(8) + 2.6, "DÉPLACEMENT : 0 MM", W / 2, 1515, 40, VERT_PALE)
    elif t < s(10):                                                           # souffler : presque rien
        u = t - s(9)
        dx = 3 * u
        faisceau(c, perso("perso_debout", 540 - dx, 520, miroir=True), 1.0, VERT_PALE, 1.2)
        for k in range(4):
            ph = (u * 1.6 + k / 4) % 1
            x0 = 600 - dx + 280 * ph
            faisceau(c, [[(x0, SOL - 540 + 24 * k), (x0 + 90, SOL - 540 + 24 * k)]], 1.0, VERT_PALE, 1.2, 1 - ph)
        trace(c, t, s(9) + 0.6, 0.3, fleche(480 - dx, SOL - 520, 400 - dx, SOL - 520, 18), AMBRE, 1.0, bip=1200)
        ecrit(c, t, s(9) + 1.4, "À PEINE…", W / 2, 1450, 52, AMBRE, True, 1.6)
        ecrit(c, t, s(9) + 3.0, "DES HEURES", W / 2, 1520, 44, VERT_PALE)
    else:                                                                     # attendre : des mois
        u = ease((t - s(10)) / 1.6)
        jours = int(1 + 180 * u)
        faisceau(c, perso("perso_reflechit", 540, 520), 1.0, VERT_PALE, 1.0, 0.8)
        ecrit(c, t, s(10), f"JOUR {jours}", W / 2, 620, 100, AMBRE, True, 2.0, vitesse=0.0)
        ecrit(c, t, s(10) + 1.6, "DES MOIS", W / 2, 1460, 60, AMBRE, True, 1.8)


def tab_pousser(c, t):
    t0 = s(11)
    titres(c, t, [(t0, "POUR AVANCER…", VERT_PALE, 66), (t0 + 1.6, "IL FAUT POUSSER", AMBRE, 72),
                  (s(13), "SANS FROTTEMENT", AMBRE, 72), (s(14), "RIEN…", AMBRE, 96)])
    compteur(c, t, s(7) + 0.4, 960, 200)
    if t < s(14):
        faisceau(c, [[(80, SOL), (1000, SOL)]], 1.0, VERT, 1.0, 0.8)          # le sol
        u = t - t0
        faisceau(c, perso("perso_debout", 540, 560), 1.0, VERT_PALE, 1.1)
        if t > s(12):                                                         # action et réaction du sol
            ecrit(c, t, s(12) + 0.2, "VOUS POUSSEZ LE SOL", 330, 1420, 40, AMBRE, True, 1.4)
            trace(c, t, s(12) + 0.2, 0.4, fleche(520, SOL + 30, 300, SOL + 30, 26), AMBRE, 2.0, bip=800)
            ok = t < s(13)
            if t > s(12) + 2.2:
                ecrit(c, t, s(12) + 2.2, "LE SOL VOUS POUSSE", 750, 1490, 40, VERT_PALE, True, 1.4)
                trace(c, t, s(12) + 2.2, 0.4, fleche(560, SOL - 280, 820, SOL - 280, 30), VERT_PALE, 2.2 if ok else 1.0,
                      1.0 if ok else 0.35, bip=1300)
            if not ok:
                trace(c, t, s(13) + 0.5, 0.2, croix(690, SOL - 280, 60), AMBRE, 2.4, bip=500)
                ecrit(c, t, s(13) + 0.9, "PLUS RIEN À POUSSER", W / 2, 1560, 44, AMBRE, True, 1.5)
        return
    ecrit(c, t, s(14) + 0.9, "SAUF CE QUE VOUS", W / 2, 460, 64, VERT_PALE, True, 1.6)   # l'indice
    ecrit(c, t, s(14) + 1.3, "AVEZ SUR VOUS", W / 2, 540, 64, AMBRE, True, 1.8)
    trace(c, t, s(14) + 0.7, 0.8, perso("perso_debout", 540, 760, 1420), VERT_PALE, 1.2, bip=1100)
    for k, (x, y) in enumerate(((620, 700), (420, 990), (660, 1060), (430, 1400), (650, 1400))):
        if t > s(14) + 1.4 + 0.15 * k:
            ecrit(c, t, s(14) + 1.4 + 0.15 * k, "?", x, y + 8 * math.sin(t * 3 + k), 60, AMBRE, True, 1.6, vitesse=0.0)


def tab_station(c, t):
    t0 = s(15)
    trace(c, t, t0, 1.4, centre("module", 540, 960, 1060), VERT, 0.7, 0.32, bip=900)
    c.drawRect(skia.Rect(0, 220, W, 400), P((2, 8, 4), 0, 220, fill=True))
    titres(c, t, [(t0, "LES ASTRONAUTES", VERT_PALE, 66), (s(16), "LOIN DES PAROIS", AMBRE, 72),
                  (s(17), "LA MÊME SOLUTION", AMBRE, 72)])
    u = t - t0
    a = 0.25 * math.sin(u * 0.9)
    astro = tourne(centre("astronaute_flotte", 540, 980 + 20 * math.sin(u * 1.3), 420), 540, 980, a)
    trace(c, t, t0 + 0.4, 0.9, astro, VERT_PALE, 1.2, bip=1300)
    if t > s(16) + 1.2:                                                       # les parois, hors d'atteinte
        for x0, x1 in ((330, 90), (750, 990)):
            trace(c, t, s(16) + 1.2, 0.4, fleche(x0, 980, x1, 980, 22), AMBRE, 1.2, bip=1500)
        ecrit(c, t, s(16) + 2.4, "RIEN POUR S'AGRIPPER", W / 2, 1420, 44, VERT_PALE, True, 1.5)
    if t > s(17):
        compteur(c, t, s(7) + 0.4, 960, 500)
        c.drawRect(skia.Rect(0, 1360, W, 1580), P((2, 8, 4), 0, 220, fill=True))
        ecrit(c, t, s(17) + 1.6, "VOUS L'AVEZ TROUVÉE ?", W / 2, 1460, 60, AMBRE, True, 2.0)


def tab_solution(c, t):
    lac(c, t, intense=0.45)
    titres(c, t, [(s(18), "ENLEVEZ VOTRE CHAUSSURE", AMBRE, 58), (s(19), "LANCEZ-LA !", AMBRE, 84),
                  (s(20), "VOUS PARTEZ", VERT_PALE, 76)])
    if t < s(19):
        trace(c, t, s(18), 0.7, perso("perso_enleve", 540, 560), VERT_PALE, 1.2, bip=1100)
        if t > s(18) + 0.5:
            trace(c, t, s(18) + 0.5, 0.3, [cercle_pts(395, SOL - 205, 70, 30)], AMBRE, 1.6, bip=1700)
        return
    if t < s(20):                                                             # le lancer, à l'opposé du bord
        corps = [l for l in perso("perso_lance", 600, 470, miroir=True)                # sans la chaussure du dessin
                 if not (max(p[0] for p in l) < 388 + 0.3 * 423 and max(p[1] for p in l) < SOL - 470 + 0.11 * 423)]
        trace(c, t, s(19), 0.4, corps, VERT_PALE, 1.2, bip=1100)
        u = max(0.0, t - s(19) - 0.6)
        x = 420 - 560 * u
        if x > -120:
            faisceau(c, tourne(centre("chaussure", x, 900 + 60 * u * u, 120), x, 900, -u * 9), 1.0, AMBRE, 1.4)
        ecrit(c, t, s(19) + 1.4, "À L'OPPOSÉ DU BORD", W / 2, 1460, 46, VERT_PALE, True, 1.5)
        trace(c, t, s(19) + 1.6, 0.3, pointilles(880, SOL - 120, 1040, SOL - 120), VERT, 0.8, bip=0)
        ecrit(c, t, s(19) + 1.6, "BORD", 960, SOL - 140, 30, VERT)
        return
    u = t - s(20)                                                             # il glisse dans l'autre sens
    x = 420 + 90 * u
    faisceau(c, perso("perso_glisse_dos", x, 400), 1.0, VERT_PALE, 1.2)
    for k in range(4):
        faisceau(c, [[(x - 300 - 40 * k, SOL - 60 - 50 * k), (x - 200 - 40 * k, SOL - 60 - 50 * k)]], 1.0, VERT, 0.8, 0.6)
    trace(c, t, s(20) + 0.3, 0.3, fleche(x + 180, SOL - 420, x + 330, SOL - 420, 26), VERT_PALE, 2.0, bip=1500)
    ecrit(c, t, s(20) + 0.4, "DANS L'AUTRE SENS", W / 2, 1460, 54, AMBRE, True, 1.6)


def tab_newton(c, t):
    t0 = s(21)
    titres(c, t, [(t0, "ACTION = RÉACTION", AMBRE, 72), (t0 + 1.4, "3e LOI DE NEWTON", VERT_PALE, 66),
                  (s(22), "LENTEMENT…", VERT_PALE, 70), (s(22) + 1.4, "MAIS RIEN NE VOUS ARRÊTE", AMBRE, 52),
                  (s(23), "COMME UNE FUSÉE", AMBRE, 72)])
    if t < s(22):                                                             # le schéma : deux flèches opposées
        faisceau(c, [[(80, SOL), (1000, SOL)]], 1.0, VERT, 1.0, 0.6)
        faisceau(c, perso("perso_debout", 640, 480), 1.0, VERT_PALE, 1.1)
        faisceau(c, centre("chaussure", 220, SOL - 260, 170), 1.0, AMBRE, 1.3)
        trace(c, t, t0 + 0.1, 0.4, fleche(380, SOL - 300, 280, SOL - 300, 26) + [[(380, SOL - 330), (380, SOL - 270)]],
              AMBRE, 2.0, bip=800)
        ecrit(c, t, t0 + 0.2, "ACTION", 300, SOL - 360, 50, AMBRE, True, 1.4)
        trace(c, t, t0 + 0.6, 0.4, fleche(760, SOL - 300, 900, SOL - 300, 26), VERT_PALE, 2.0, bip=1600)
        ecrit(c, t, t0 + 0.7, "RÉACTION", 830, SOL - 360, 50, VERT_PALE, True, 1.4)
        ecrit(c, t, t0 + 2.0, "0,5 KG À 10 M/S → 70 KG À 7 CM/S", W / 2, 1460, 40, VERT)
        return
    if t < s(23):                                                             # la glisse lente jusqu'au bord
        lac(c, t, intense=0.45)
        u = ease((t - s(22)) / (s(23) - s(22)))
        x = 300 + 560 * u
        faisceau(c, perso("perso_glisse_dos", x, 330), 1.0, VERT_PALE, 1.1)
        trace(c, t, s(22) + 0.2, 0.3, pointilles(930, SOL - 240, 1060, SOL - 240), VERT, 0.8, bip=0)
        ecrit(c, t, s(22) + 0.2, "BORD", 990, SOL - 260, 30, VERT)
        ecrit(c, t, s(22) + 0.5, "7 CM/S", W / 2, 1460, 60, AMBRE, True, 1.6)
        if u > 0.97:
            trace(c, t, s(23) - 0.15, 0.2, [cercle_pts(960, SOL - 160, 70, 30)], AMBRE, 1.6, bip=1700)
        return
    u = max(0.0, t - s(23) - 0.4)                                             # la fusée : même principe
    y = 1000 - 120 * u * u
    trace(c, t, s(23), 0.6, centre("fusee", 540, y, 380), VERT_PALE, 1.2, bip=1100)
    trace(c, t, s(23) + 0.6, 0.3, fleche(380, y + 120, 380, y + 320, 24), AMBRE, 1.8, bip=800)
    ecrit(c, t, s(23) + 0.6, "GAZ", 300, y + 230, 36, AMBRE, True, 1.4)
    trace(c, t, s(23) + 1.0, 0.3, fleche(720, y + 120, 720, y - 80, 24), VERT_PALE, 1.8, bip=1600)
    ecrit(c, t, s(23) + 1.0, "FUSÉE", 800, y + 40, 36, VERT_PALE, True, 1.4)


def tab_fin(c, t):
    t0 = s(24)
    lac(c, t, intense=0.4)
    trace(c, t, t0, 0.6, perso("perso_victoire", 540, 520), VERT_PALE, 1.2, bip=1100)
    ecrit(c, t, t0 + 0.1, "VOUS AVIEZ", W / 2, 330, 96, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, t0 + 0.3, "TROUVÉ ?", W / 2, 440, 96, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, t0 + 0.9, "DITES-LE EN COMMENTAIRE", 500, 1420, 40, VERT_PALE, True, 1.5)
    b = 18 * abs(math.sin((t - t0) * 5))
    trace(c, t, t0 + 1.1, 0.25, fleche(800 + b, 1406, 960 + b, 1406, 26), AMBRE, 1.8, bip=1700)
    if t > s(25):
        ecrit(c, t, s(25), "+ ABONNEZ-VOUS", W / 2, 1500, 52, AMBRE, True, 1.6)
        ecrit(c, t, s(25) + 0.6, "PROCHAINE SITUATION IMPOSSIBLE", W / 2, 1560, 32, VERT)


def tableaux():
    return [(0.0, tab_accroche, None), (s(3) - 0.1, tab_essais, "neige"), (s(6) - 0.1, tab_defi, "glitch"),
            (s(8) - 0.1, tab_pistes, "balayage"), (s(11) - 0.1, tab_pousser, "neige"), (s(15) - 0.1, tab_station, "noir"),
            (s(18) - 0.1, tab_solution, "glitch"), (s(21) - 0.1, tab_newton, "balayage"), (s(24) - 0.1, tab_fin, "neige")]


def chocs():
    flashs = [s(1), s(6), s(14), s(18), s(19) + 0.6]
    secousses = [(s(1), 0.25), (s(5) + 0.6, 0.12), (s(13) + 0.5, 0.15), (s(18), 0.2), (s(19) + 0.6, 0.15)]
    return flashs, secousses


def effets(tabs):
    ev = [(0.0, Z.vent(s(3), 0.07, 120, 900)), (0.0, Z.grincement(1.2, 0.08)), (0.1, Z.craquement(0.25)),
          (s(1), Z.boom(0.55, 55)), (s(1) + 0.05, Z.snap(0.3)), (s(2) + 0.8, Z.craquement(0.35)),
          (s(2) + 1.8, Z.chirp(600, 300, 0.5, 0.06))]
    ev += [(s(i) + 0.9, Z.thump(0.3)) for _, i in ESSAIS]
    ev += [(s(3) + 0.1 * k, Z.chirp(1400, 900, 0.08, 0.05)) for k in range(0, 18, 3)]
    ev += [(s(4), Z.grincement(0.9, 0.08)), (s(5) + 0.2, Z.whoosh(0.4, 0.08)), (s(5) + 0.6, Z.thump(0.35)),
           (s(5) + 1.8, Z.thump(0.3))]
    ev += [(s(6), Z.boom(0.45, 70)), (s(6) + 0.8, Z.chirp(500, 900, 0.3, 0.06)), (s(7) + 0.4, Z.tictac(s(8) - s(7), 0.07, 0.5))]
    ev += [(s(8), Z.vibration(1.6, 0.08)), (s(8) + 1.2, Z.cloche(784, 0.08)), (s(9), Z.souffle(1.2, 0.12, False)),
           (s(9) + 1.4, Z.souffle(1.2, 0.10, False)), (s(9) + 3.0, Z.chirp(500, 250, 0.5, 0.06)),
           (s(10), Z.tictac(1.6, 0.08, 0.06)), (s(10) + 1.6, Z.cloche(440, 0.08))]
    ev += [(s(11), Z.whoosh(0.5, 0.08)), (s(11) + 1.6, Z.thump(0.35)), (s(12) + 0.2, Z.grincement(0.5, 0.08)),
           (s(12) + 2.2, Z.whoosh(0.4, 0.08)), (s(13) + 0.5, Z.boom(0.35, 60)), (s(13) + 0.5, Z.alarme(0.05, 1)),
           (s(14), Z.riser(1.0, 0.08)), (s(14) + 1.4, Z.scintillement(1.0, 0.05))]
    ev += [(s(15), Z.porte(1.2, 0.08)), (s(15), Z.vent(3.0, 0.05, 200, 700)), (s(16) + 1.2, Z.whoosh(0.5, 0.06)),
           (s(17), Z.tictac(s(18) - s(17), 0.09, 0.25)), (s(17) + 1.6, Z.riser(s(18) - s(17) - 1.6, 0.1))]
    ev += [(s(18), Z.boom(0.55, 60)), (s(18) + 0.5, Z.cloche(784, 0.1)), (s(19) + 0.6, Z.whoosh(0.6, 0.18)),
           (s(19) + 0.6, Z.snap(0.3)), (s(20), Z.grincement(1.2, 0.07)), (s(20) + 0.3, Z.chirp(600, 1200, 0.4, 0.07))]
    ev += [(s(21) + 0.1, Z.pince(523.3, 0.1)), (s(21) + 0.6, Z.pince(784, 0.1)), (s(21) + 1.4, Z.cloche(1046.5, 0.08)),
           (s(22), Z.vent(3.0, 0.05, 150, 600)), (s(23) - 0.15, Z.thump(0.35)), (s(23), Z.riser(1.4, 0.1)),
           (s(23) + 0.4, Z.boom(0.4, 50)), (s(23) + 0.5, Z.crepitement(1.6, 0.08, 60))]
    ev += [(s(24), Z.applaudissements(1.6, 0.08)), (s(24) + 1.1, Z.pince(784, 0.08)), (s(24) + 1.25, Z.pince(988, 0.08)),
           (s(24) + 1.4, Z.pince(1175, 0.08)), (s(25), Z.cloche(698.5, 0.1, 2.5))]
    for t0, _, tr in tabs[1:]:
        ev.append((t0, {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
                        "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}[tr]()))
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep25_oscillo.mp4")
