"""Épisode 21 — « Sauter dans un ascenseur qui chute » — style oscilloscope, calé sur la voix (≈ 80 s).

Tout est tracé au faisceau (films/styles/oscillo_ascenseur.py) : vert phosphore, ambre pour ce qui compte, persistance,
lignes de balayage. Un tableau par idée, un nouvel élément environ chaque seconde, transitions variées (neige, noir,
balayage, glitch). Son : un bip par élément tracé, frappe des textes, impacts graves aux révélations, nappe coupée
juste avant chaque révélation, mixage à −14 LUFS.

    python -m films.episodes.ep21_ascenseur.oscillo_ep21 output/ep21_oscillo.mp4
"""
import json
import re
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1
from films.styles import oscillo_son as Z
from films.styles.oscillo_ascenseur import AMBRE, MONO, VERT, VERT_PALE, P, cercle_pts, ease, faisceau, rect_pts

W, H, FPS = 1080, 1920, 30
ALPHA_PERSISTANCE = 150   # part de l'image précédente gardée à chaque image (traînée phosphore)
HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.mp3")
SEGS = os.path.join(HERE, "audio", "voix.json")
G = 9.81
RNG = np.random.default_rng(21)

SEG = []          # [(début, fin, texte)] après resserrement
SONS = {}         # sons déclenchés pendant le rendu : clé → (t, type, paramètres)
MOTS = []


def s(i):
    return SEG[i][0]


def e(i):
    return SEG[i][1]


def son(cle, t0, kind, *args):
    SONS.setdefault(cle, (t0, kind, args))


# ------------------------------------------------------------------------------------------------ primitives
def trace(c, t, t0, d, traits, col=VERT, w=1.0, intense=1.0, bip=1300):
    """Tracé au faisceau entre t0 et t0+d (bip au départ, cliquetis pendant le tracé)."""
    if t < t0:
        return 0.0
    u = ease((t - t0) / d) if d > 0 else 1.0
    if bip:
        son(("tr", round(t0, 3), bip), t0, "trace", bip, d)
    faisceau(c, traits, u, col, w, intense)
    return u


def ecrit(c, t, t0, txt, x, y, taille, col=VERT_PALE, centre=True, halo=1.0, vitesse=0.035):
    """Texte tapé lettre par lettre (bips de frappe) avec halo phosphore."""
    if t < t0:
        return
    d = min(0.7, max(0.15, len(txt) * vitesse))
    n = int(len(txt) * min(1.0, (t - t0) / d))
    if n <= 0:
        return
    son(("ty", round(t0, 3), txt), t0, "frappe", len(txt), d)
    f = skia.Font(MONO, taille)
    if centre:
        x -= f.measureText(txt) / 2
    if halo > 1.0:
        c.drawString(txt[:n], x, y, f, P(col, 0, 120, 22, fill=True))
    c.drawString(txt[:n], x, y, f, P(col, 0, 255, 7 * halo, fill=True))
    c.drawString(txt[:n], x, y, f, P(col, 0, 255, fill=True))


def titres(c, t, liste, y=330, taille=62, halo=1.6):
    """Une seule ligne de titre : on affiche le dernier titre commencé."""
    cour = [x for x in liste if x[0] <= t]
    if cour:
        t0, txt, col = cour[-1][:3]
        tl = cour[-1][3] if len(cour[-1]) > 3 else taille
        ecrit(c, t, t0, txt, W / 2, y, tl, col, True, halo)


def fleche(x0, y0, x1, y1, tete=26):
    a = math.atan2(y1 - y0, x1 - x0)
    return [[(x0, y0), (x1, y1)],
            [(x1 + tete * math.cos(a + 2.6), y1 + tete * math.sin(a + 2.6)), (x1, y1),
             (x1 + tete * math.cos(a - 2.6), y1 + tete * math.sin(a - 2.6))]]


def pointilles(x0, y0, x1, y1, pas=22):
    n = max(1, int(math.dist((x0, y0), (x1, y1)) / pas))
    return [[(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n),
             (x0 + (x1 - x0) * (i + 0.5) / n, y0 + (y1 - y0) * (i + 0.5) / n)] for i in range(0, n, 1)]


POSES = {  # articulations (dx, dy) pour une hauteur ≈ 76 à l'échelle 1, pieds en (0, 0)
    "debout": dict(tete=(0, -76), cou=(0, -64), bassin=(0, -30), mg=(-17, -34), md=(17, -34),
                   gg=(-7, -15), gd=(7, -15), pg=(-10, 0), pd=(10, 0)),
    "flotte": dict(tete=(0, -76), cou=(0, -64), bassin=(0, -30), mg=(-27, -92), md=(27, -92),
                   gg=(-15, -16), gd=(13, -15), pg=(-9, -2), pd=(10, -3)),
    "saut": dict(tete=(2, -58), cou=(2, -47), bassin=(2, -22), mg=(-24, -26), md=(26, -26),
                 gg=(-17, -13), gd=(19, -13), pg=(-10, 0), pd=(10, 0)),
    "allonge": dict(tete=(-42, -9), cou=(-31, -8), bassin=(8, -7), mg=(-8, -3), md=(-5, -13),
                    gg=(27, -6), gd=(27, -10), pg=(47, -4), pd=(47, -12)),
}


def bonhomme(x, y, ech=1.0, pose="debout", pose2=None, k=0.0, chapeau=False):
    a = POSES[pose]
    b = POSES[pose2] if pose2 else a
    j = {n: (x + ech * (a[n][0] + (b[n][0] - a[n][0]) * k), y + ech * (a[n][1] + (b[n][1] - a[n][1]) * k)) for n in a}
    ep = (j["cou"][0] + (j["bassin"][0] - j["cou"][0]) * 0.2, j["cou"][1] + (j["bassin"][1] - j["cou"][1]) * 0.2)
    tr = [cercle_pts(*j["tete"], 9 * ech), [j["cou"], j["bassin"]], [j["mg"], ep, j["md"]],
          [j["pg"], j["gg"], j["bassin"], j["gd"], j["pd"]]]
    if chapeau:
        hx, hy = j["tete"]
        r = 9 * ech
        tr.append([(hx - 1.5 * r, hy - r), (hx + 1.5 * r, hy - r)])
        tr.append(rect_pts(hx - 0.9 * r, hy - 2.6 * r, hx + 0.9 * r, hy - r))
    return tr


def immeuble(x0, x1, y0, y1, n, g0, g1, fenetres=True):
    tr = [rect_pts(x0, y0, x1, y1), [(g0, y0), (g0, y1)], [(g1, y0), (g1, y1)], [(x0 - 120, y1), (x1 + 120, y1)],
          rect_pts(g0 + 16, y0 - 50, g1 - 16, y0)]
    et = []
    for k in range(1, n):
        y = y0 + k * (y1 - y0) / n
        et += [[(x0, y), (g0, y)], [(g1, y), (x1, y)]]
        if fenetres:
            hh = (y1 - y0) / n
            for wx in list(range(int(x0) + 24, int(g0) - 20, 44)) + list(range(int(g1) + 20, int(x1) - 26, 44)):
                et.append(rect_pts(wx, y - hh * 0.75, wx + 20, y - hh * 0.4))
    return tr, et


def chute(frac):
    """Vitesse (km/h) après une chute de frac × 30 m."""
    return math.sqrt(2 * G * 30 * max(0.0, frac)) * 3.6


# ------------------------------------------------------------------------------------------------ tableaux
def tab_accroche(c, t):
    X0, X1, Y0, Y1, G0, G1, CAB = 330, 750, 520, 1420, 470, 610, 100
    tr, et = immeuble(X0, X1, Y0, Y1, 10, G0, G1)
    trace(c, t, -0.45, 0.9, tr, bip=0)
    trace(c, t, 0.05, 0.9, et, VERT, 0.55, 0.55, bip=1500)
    trace(c, t, 0.4, 0.4, [[(X0 - 60, Y0), (X0 - 60, Y1)]], VERT, 0.5, 0.6, bip=1100)
    ecrit(c, t, 0.6, "30 m", X0 - 150, (Y0 + Y1) / 2, 34, VERT, False)
    t_r = e(0) - 0.55                                                       # le câble casse sur « qui chute »
    t_f = e(1) - 0.15                                                       # arrêt sur image juste avant l'impact
    frac = 0.0 if t < t_r else 0.94 * min(1.0, ((t - t_r) / (t_f - t_r)) ** 2)
    yh, yb = Y0 + 6, Y1 - 8 - CAB
    y = yh + (yb - yh) * frac
    cm = (G0 + G1) / 2
    col = AMBRE if t >= t_r else VERT
    if t < t_r:
        trace(c, t, 0.35, 0.3, [[(cm, Y0 - 50), (cm, y)]], VERT, 0.8, bip=0)
    else:
        bout = max(2, 50 - (t - t_r) * 150)
        trace(c, t, 0.35, 0.3, [[(cm, Y0 - 50), (cm + 5, Y0 - 50 + bout)]], VERT, 0.8, bip=0)
    trace(c, t, 0.3, 0.35, [rect_pts(G0 + 12, y, G1 - 12, y + CAB)], col, 1.2, bip=900)
    k = ease((t - t_r) / 0.5)
    trace(c, t, 0.5, 0.35, bonhomme(cm, y + CAB - 8 - 14 * k, 1.05, "debout", "flotte", k), col, 0.9, bip=0)
    if t_r <= t < t_f:                                                      # étincelles contre la gaine
        for _ in range(3):
            ETINCELLES.append([G0 + 12 if RNG.random() < 0.5 else G1 - 12, y + RNG.uniform(0, CAB),
                               RNG.uniform(-4, 4), RNG.uniform(-9, -2), 1.0])
    # lectures
    etage = 10 * (1 - frac)
    ecrit(c, t, 0.7, f"ÉTAGE {etage:04.1f}", 780, 640, 30, VERT)
    ecrit(c, t, 0.8, f"{chute(frac):3.0f} km/h", 780, 700, 44, AMBRE if frac > 0 else VERT_PALE)
    if t_r <= t < t_r + 0.7 and int(t * 12) % 2 == 0:
        ecrit(c, t, t_r, "! CÂBLE ROMPU", W / 2, 455, 44, AMBRE, vitesse=0.0)
    titres(c, t, [(-1.0, "ASCENSEUR EN CHUTE", VERT_PALE, 66), (s(1), "SAUTER AU DERNIER MOMENT ?", VERT_PALE, 46),
                  (s(2) + 0.2, "PEUT-ON L'ÉVITER ?", AMBRE, 66)])
    if t > s(1) + 0.5:                                                      # le saut envisagé
        trace(c, t, s(1) + 0.5, 0.3, fleche(cm + 70, y + CAB - 10, cm + 70, y - 60), VERT_PALE, 1.0, bip=1700)
        ecrit(c, t, s(1) + 0.7, "SAUT", cm + 140, y + 20, 32, VERT_PALE, False)
    if t > s(1) + 1.2:
        clign = 1.0 if int(t * 6) % 2 == 0 or t > t_f else 0.35
        trace(c, t, s(1) + 1.2, 0.3, [[(X0 - 40, Y1 + 4), (X1 + 40, Y1 + 4)]], AMBRE, 1.4, clign, bip=600)
        ecrit(c, t, s(1) + 1.3, "IMPACT", W / 2, Y1 + 70, 40, AMBRE)
    if t >= t_f:
        ecrit(c, t, t_f, "|| ARRÊT SUR IMAGE", 60, 455, 26, VERT, False, vitesse=0.0)
    if t >= s(3):                                                           # « La réponse est non. »
        c.drawRect(skia.Rect(0, 560, W, 1200), P((2, 8, 4), 0, 200, fill=True))
        ecrit(c, t, s(3) + 0.05, "NON", W / 2, 960, 300, AMBRE, True, 2.2, vitesse=0.0)
    if t >= s(4):
        ecrit(c, t, s(4) + 0.3, "ET LA RAISON", W / 2, 1080, 52, VERT_PALE)
        ecrit(c, t, s(4) + 0.8, "VA VOUS SURPRENDRE", W / 2, 1150, 52, VERT_PALE)


def tab_vitesse(c, t):
    t0 = s(5)
    X0, X1, Y0, Y1, G0, G1, CAB = 90, 450, 520, 1420, 200, 340, 90
    tr, et = immeuble(X0, X1, Y0, Y1, 10, G0, G1, fenetres=False)
    trace(c, t, t0, 0.6, tr, bip=1200)
    trace(c, t, t0 + 0.3, 0.6, et, VERT, 0.55, 0.55, bip=0)
    ecrit(c, t, t0 + 0.4, "10 ÉTAGES", (X0 + X1) / 2, Y0 - 80, 36, VERT)
    titres(c, t, [(t0, "APRÈS 10 ÉTAGES DE CHUTE", VERT_PALE, 52), (s(7), "ET VOUS AUSSI.", AMBRE, 66)])
    # chute (temps physique étiré sur la phrase)
    tc0, tc1 = t0 + 0.6, e(6) - 0.5
    tr_reel = math.sqrt(2 * 30 * 0.97 / G)
    tau = min(1.0, max(0.0, (t - tc0) / (tc1 - tc0)))
    frac = 0.97 * tau ** 2
    y = Y0 + 6 + (Y1 - 8 - CAB - Y0 - 6) * frac
    cm = (G0 + G1) / 2
    col = AMBRE if t > tc0 else VERT
    trace(c, t, t0 + 0.4, 0.3, [rect_pts(G0 + 10, y, G1 - 10, y + CAB)], col, 1.1, bip=900)
    vous = t >= s(7)
    trace(c, t, t0 + 0.5, 0.3, bonhomme(cm, y + CAB - 22, 0.9, "flotte"), AMBRE if vous else col, 1.4 if vous else 0.9, bip=0)
    # graphe vitesse / temps
    GX0, GX1, GY0, GY1 = 530, 1000, 650, 1150
    trace(c, t, t0 + 0.5, 0.5, [rect_pts(GX0, GY0, GX1, GY1)], VERT, 0.5, 0.7, bip=1500)
    if t > t0 + 0.8:
        for i in range(1, 6):
            x = GX0 + (GX1 - GX0) * i / 6
            c.drawLine(x, GY0, x, GY1, P(VERT, 1, 35))
        for i in range(1, 5):
            yy = GY0 + (GY1 - GY0) * i / 5
            c.drawLine(GX0, yy, GX1, yy, P(VERT, 1, 35))
    ecrit(c, t, t0 + 0.7, "VITESSE (km/h)", GX0, GY0 - 20, 26, VERT, False)
    ecrit(c, t, t0 + 0.9, "TEMPS (s)", GX1 - 150, GY1 + 40, 24, VERT, False)
    pts = []
    for i in range(0, 121):
        ti = tau * i / 120
        pts.append((GX0 + (GX1 - GX0) * ti, GY1 - (GY1 - GY0) * min(1, chute(0.97 * ti ** 2) / 100)))
    if t > tc0 and len(pts) > 1:
        faisceau(c, [pts], 1.0, AMBRE, 1.2)
        c.drawCircle(*pts[-1], 8, P((255, 240, 210), 0, 220, 6, fill=True))
        son(("courbe", round(tc0, 3)), tc0, "montee", tc1 - tc0)
    if vous:                                                                # deuxième courbe, identique : vous
        trace(c, t, s(7) + 0.1, 0.5, [pts], VERT_PALE, 0.7, bip=1900)
        ecrit(c, t, s(7) + 0.2, "CABINE = VOUS", GX0 + 10, GY0 + 50, 30, VERT_PALE, False)
    v = chute(frac)
    ecrit(c, t, t0 + 0.6, f"{v:2.0f} km/h", (GX0 + GX1) / 2, 1320, 96, AMBRE if v > 1 else VERT_PALE, True, 1.6,
          vitesse=0.0)
    ecrit(c, t, t0 + 0.6, f"t = {tau * tr_reel:3.1f} s", (GX0 + GX1) / 2, 1390, 32, VERT, vitesse=0.0)
    if t > tc1:
        ecrit(c, t, tc1 + 0.05, "≈ 90 km/h", (GX0 + GX1) / 2, 1460, 44, VERT_PALE)


def tab_saut(c, t):
    t0 = s(8)
    BASE, K = 1400, 8.2
    trace(c, t, t0, 0.4, [[(120, BASE), (960, BASE)]], VERT, 0.7, bip=1200)
    titres(c, t, [(t0, "LE MEILLEUR SAUT HUMAIN", VERT_PALE, 54), (s(9) + 0.3, "MÊME SYNCHRONISÉ…", VERT_PALE, 54),
                  (s(10), "ÇA NE CHANGE PRESQUE RIEN", AMBRE, 50)])
    # barre « sans saut » : 87 km/h
    h1 = 87 * K * ease((t - t0 - 0.2) / 0.8)
    trace(c, t, t0 + 0.2, 0.0, [rect_pts(200, BASE - h1, 420, BASE)], AMBRE, 1.1, bip=700)
    ecrit(c, t, t0 + 0.3, f"{87 * ease((t - t0 - 0.2) / 0.8):2.0f}", 310, BASE - h1 - 30, 64, AMBRE, vitesse=0.0)
    ecrit(c, t, t0 + 0.5, "SANS SAUT", 310, BASE + 60, 34, VERT)
    # le saut : flèche verte vers le haut, 10 km/h
    ts = t0 + 1.4
    trace(c, t, ts, 0.35, fleche(540, BASE - 10, 540, BASE - 10 - 10 * K - 30, 20), VERT_PALE, 1.2, bip=1800)
    ecrit(c, t, ts + 0.3, "+10 km/h", 540, BASE - 10 * K - 80, 34, VERT_PALE)
    ecrit(c, t, ts + 0.5, "VERS LE HAUT", 540, BASE - 10 * K - 130, 26, VERT)
    # barre « avec saut » : 77 ≈ 80
    if t > s(9):
        q = ease((t - s(9) - 0.2) / 1.6)
        h2 = (87 - 10 * q) * K * ease((t - s(9)) / 0.5)
        trace(c, t, s(9), 0.0, [rect_pts(660, BASE - h2, 880, BASE)], AMBRE, 1.1, bip=700)
        ecrit(c, t, s(9) + 0.1, f"{(87 - 10 * q) * ease((t - s(9)) / 0.5):2.0f}", 770, BASE - h2 - 30, 64, AMBRE,
              vitesse=0.0)
        ecrit(c, t, s(9) + 0.3, "AVEC SAUT", 770, BASE + 60, 34, VERT)
    if t > s(9) + 2.6:
        ecrit(c, t, s(9) + 2.6, "≈ 80 km/h AU SOL", 770, BASE - 77 * K - 110, 32, VERT_PALE)
    if t > s(10):                                                           # écart : -11 %
        y1, y2 = BASE - 87 * K, BASE - 77 * K
        trace(c, t, s(10) + 0.2, 0.3, [[(420, y1), (940, y1)]], VERT, 0.5, 0.7, bip=1500)
        trace(c, t, s(10) + 0.4, 0.2, fleche(920, y1 + 4, 920, y2 - 4, 12), VERT_PALE, 0.8, bip=0)
        ecrit(c, t, s(10) + 0.6, "-11 %", 960, (y1 + y2) / 2 + 12, 30, VERT_PALE, False)


def tab_flotte(c, t):
    t0 = s(11)
    CX0, CX1, CY0, CY1 = 270, 810, 480, 1140
    titres(c, t, [(t0, "LE VRAI PROBLÈME", AMBRE, 62), (s(12), "MÊME VITESSE QUE LA CABINE", VERT_PALE, 46),
                  (s(13), "VOUS FLOTTEZ", AMBRE, 66), (s(14), "AUCUN APPUI", AMBRE, 66),
                  (s(15), "DEVINER L'INSTANT DU CHOC", VERT_PALE, 46)])
    # parois de la gaine qui défilent vers le haut (on tombe)
    if t > t0 + 0.2:
        dec = ((t - t0) * 900) % 120
        for xg in (190, 890):
            traits = [[(xg - 18, y), (xg + 18, y)] for y in np.arange(440 - dec + 120, 1200, 120)]
            faisceau(c, traits, 1.0, VERT, 0.5, 0.5)
    trace(c, t, t0, 0.5, [rect_pts(CX0, CY0, CX1, CY1)], VERT, 1.2, bip=1000)
    trace(c, t, t0 + 0.2, 0.4, [[(CX0, CY1 - 4), (CX1, CY1 - 4)]], VERT, 1.6, bip=0)
    cx = 540
    k_saut = ease((t - t0 - 1.6) / 0.4) * (1 - ease((t - t0 - 2.4) / 0.4))
    lev = 70 * ease((t - s(13)) / 1.0) + (8 * math.sin((t - s(13)) * 3) if t > s(13) else 0)
    k_fl = ease((t - s(12) - 1.0) / 1.2)
    pose, pose2, k = ("debout", "saut", k_saut) if k_fl == 0 else ("debout", "flotte", k_fl)
    yp = CY1 - 6 - lev
    trace(c, t, t0 + 0.4, 0.5, bonhomme(cx, yp, 3.4, pose, pose2, k), VERT_PALE, 1.3, bip=1400)
    if s(12) <= t:                                                          # deux flèches identiques
        trace(c, t, s(12) + 1.0, 0.3, fleche(130, 600, 130, 900), AMBRE, 1.1, bip=800)
        ecrit(c, t, s(12) + 1.1, "CABINE", 130, 560, 26, AMBRE)
        trace(c, t, s(12) + 2.4, 0.3, fleche(cx + 170, 600, cx + 170, 900), AMBRE, 1.1, bip=800)
        ecrit(c, t, s(12) + 2.5, "VOUS", cx + 170, 560, 26, AMBRE)
    if t > s(14):                                                           # le vide sous les pieds
        clign = 1.0 if int(t * 5) % 2 == 0 else 0.4
        trace(c, t, s(14) + 0.1, 0.4, pointilles(cx - 90, yp + 4, cx + 90, yp + 4), AMBRE, 0.9, clign, bip=600)
        trace(c, t, s(14) + 0.3, 0.3, [[(cx + 120, yp + 4), (cx + 120, CY1 - 6)]], VERT_PALE, 0.7, bip=0)
        ecrit(c, t, s(14) + 0.4, "APPUI = 0", cx + 140, (yp + CY1) / 2 + 12, 32, AMBRE, False)
    if t > s(15):                                                           # la fenêtre d'une milliseconde
        LX0, LX1, LY = 130, 950, 1420
        trace(c, t, s(15) + 0.1, 0.5, [[(LX0, LY), (LX1, LY)]], VERT, 0.8, bip=1200)
        xi = 820
        trace(c, t, s(15) + 0.4, 0.2, [[(xi, LY - 90), (xi, LY + 20)]], AMBRE, 1.4, bip=500)
        ecrit(c, t, s(15) + 0.5, "CHOC", xi, LY - 110, 28, AMBRE)
        if t > s(15) + 0.7:                                                 # curseur qui cherche, et manque
            u = (t - s(15) - 0.7) * 1.3
            xc = LX0 + (LX1 - LX0) * (0.5 + 0.45 * math.sin(u * 2.2))
            faisceau(c, [[(xc, LY - 50), (xc, LY + 50)]], 1.0, VERT_PALE, 0.9)
        ecrit(c, t, s(15) + 2.2, "FENÊTRE : 0,001 s", W / 2, LY + 90, 40, VERT_PALE)


def tab_solution(c, t):
    t0 = s(16)
    titres(c, t, [(t0, "ALORS, QUE FAIRE ?", VERT_PALE, 66), (s(17) + 1.6, "S'ALLONGER À PLAT", AMBRE, 62),
                  (s(18), "LE CHOC SE RÉPARTIT", VERT_PALE, 56)])
    SOL = 1180
    trace(c, t, s(17) + 0.2, 0.5, [[(80, SOL), (1000, SOL)]], VERT, 0.8, bip=1200)
    # allongé (à droite) — la bonne position
    trace(c, t, s(17) + 0.6, 0.5, bonhomme(800, SOL - 4, 2.6, "allonge"), VERT_PALE, 1.3, bip=1500)
    ecrit(c, t, s(17) + 1.0, "ALLONGÉ", 800, SOL + 80, 36, VERT_PALE)
    # debout (à gauche) — pour comparer
    trace(c, t, s(17) + 2.2, 0.5, bonhomme(280, SOL - 4, 2.6, "debout"), VERT, 1.1, 0.8, bip=1500)
    ecrit(c, t, s(17) + 2.5, "DEBOUT", 280, SOL + 80, 36, VERT)
    if t > s(18):
        for i in range(9):                                                  # beaucoup de petites forces
            x = 700 + i * 26
            trace(c, t, s(18) + 0.3 + i * 0.06, 0.15, fleche(x, SOL + 160, x, SOL + 120, 12), VERT_PALE, 0.8,
                  bip=1700 + 60 * i if i % 3 == 0 else 0)
        ecrit(c, t, s(18) + 0.9, "RÉPARTI", 800, SOL + 210, 32, VERT_PALE)
        for x in (254, 306):                                                # deux grosses forces
            trace(c, t, s(18) + 2.0, 0.3, fleche(x, SOL + 220, x, SOL + 10, 28), AMBRE, 1.6, bip=600)
        ecrit(c, t, s(18) + 2.2, "JAMBES", 120, SOL - 80, 30, AMBRE, False)
        trace(c, t, s(18) + 3.0, 0.3, [[(280, SOL - 4 - 64 * 2.6), (280, SOL - 4 - 30 * 2.6)]], AMBRE, 2.0, bip=500)
        ecrit(c, t, s(18) + 3.1, "COLONNE", 120, SOL - 140 - 64, 30, AMBRE, False)


def tab_rassure(c, t):
    t0 = s(19)
    ecrit(c, t, t0 + 0.1, "RASSUREZ-VOUS", W / 2, 760, 46, VERT)
    ecrit(c, t, t0 + 0.9, "PRESQUE", W / 2, 900, 110, VERT_PALE, True, 1.8)
    ecrit(c, t, t0 + 1.3, "JAMAIS", W / 2, 1020, 110, VERT_PALE, True, 1.8)
    if t > t0 + 0.4:                                                        # tracé calme
        ph = (t - t0) * 2.0
        pts = [(x, 1250 + 40 * math.sin(x / 90 + ph)) for x in range(80, 1001, 10)]
        faisceau(c, [pts], ease((t - t0 - 0.4) / 0.8), VERT, 0.8, 0.8)


def tab_otis(c, t):
    t0 = s(20)
    RG, RD, RY0, RY1 = 360, 720, 440, 1230
    titres(c, t, [(t0, "1854 · NEW YORK", AMBRE, 60), (s(21), "IL FAIT COUPER LE CÂBLE", AMBRE, 50),
                  (s(22), "ELLE NE TOMBE PAS", VERT_PALE, 60), (s(23), "FREIN DE SÉCURITÉ", AMBRE, 62)])
    dents = []
    for x, sg in ((RG, 1), (RD, -1)):
        pts = [(x, RY0)]
        for y in range(RY0, RY1, 30):
            pts += [(x + sg * 14, y + 6), (x, y + 30)]
        dents.append(pts)
        dents.append([(x - sg * 14, RY0), (x - sg * 14, RY1)])
    trace(c, t, t0, 0.8, dents, VERT, 0.7, 0.8, bip=1200)
    trace(c, t, t0 + 0.5, 0.4, [[(RG - 30, RY0 - 20), (RD + 30, RY0 - 20)], cercle_pts(540, RY0 + 6, 22)], VERT,
          0.9, bip=1000)
    t_coupe = s(21) + 0.55
    py = 760.0
    if t > t_coupe:
        py += 22 * ease((t - t_coupe) / 0.15)
    trace(c, t, t0 + 0.9, 0.4, [rect_pts(RG + 14, py, RD - 14, py + 22)], VERT_PALE, 1.2, bip=900)
    if t < t_coupe:
        trace(c, t, t0 + 0.8, 0.3, [[(540, RY0 + 28), (540, py)]], VERT, 0.9, bip=0)
    else:                                                                   # le câble coupé
        r = (t - t_coupe) * 600
        faisceau(c, [[(540, RY0 + 28), (540, max(RY0 + 28, 600 - r))], [(540, min(py - 2, 640 + r * 0.5)), (540, py)]],
                 1.0, AMBRE, 0.9)
        if t < t_coupe + 0.8 and int(t * 12) % 2 == 0:
            ecrit(c, t, t_coupe, "✕", 540, 640, 60, AMBRE, vitesse=0.0)
    trace(c, t, t0 + 1.4, 0.5, bonhomme(540, py, 1.7, "debout", chapeau=True), VERT_PALE, 1.0, bip=1500)
    ecrit(c, t, t0 + 1.9, "ELISHA OTIS", 540, py - 175, 34, VERT_PALE)
    # cliquets : repliés, puis enclenchés dans les dents
    kq = ease((t - t_coupe) / 0.12)
    for x, sg in ((RG + 14, -1), (RD - 14, 1)):
        bx, by = x - sg * 30, py + 11
        tx, ty = x + sg * (-8 + 18 * kq), py + 11 - 4 - 10 * kq
        trace(c, t, t0 + 1.1, 0.2, [[(bx, by), (tx, ty)]], AMBRE if kq > 0 else VERT, 1.2, bip=0)
    # la foule
    if t > t0 + 2.6:
        foule = []
        for i in range(9):
            x = 150 + i * 98 + (14 if i % 2 else 0)
            y = 1380 + (18 if i % 2 else 0)
            foule += [cercle_pts(x, y, 14, 16), [(x - 30, y + 60), (x - 22, y + 26), (x, y + 18), (x + 22, y + 26),
                                                 (x + 30, y + 60)]]
        trace(c, t, t0 + 2.6, 0.9, foule, VERT, 0.8, 0.7, bip=1100)
        ecrit(c, t, t0 + 3.2, "LA FOULE", 540, 1520, 26, VERT)
    if t > s(22) + 0.3:
        ecrit(c, t, s(22) + 0.3, "BLOQUÉE", 860, py + 20, 34, AMBRE, False, 1.4)
    if t > s(23):                                                           # loupe sur un cliquet
        LX, LY, R = 830, 1080, 140
        trace(c, t, s(23) + 0.1, 0.3, [[(RD, py + 14), (LX - R * 0.7, LY - R * 0.7)]], VERT, 0.5, 0.7, bip=0)
        trace(c, t, s(23) + 0.1, 0.4, [cercle_pts(LX, LY, R, 48)], VERT_PALE, 1.0, bip=1600)
        z = [(LX + 40, LY - 120)]
        for y in range(-120, 120, 48):
            z += [(LX + 40 - 34, LY + y + 12), (LX + 40, LY + y + 48)]
        trace(c, t, s(23) + 0.4, 0.4, [z, [(LX + 70, LY - 120), (LX + 70, LY + 120)]], VERT, 1.0, bip=1300)
        trace(c, t, s(23) + 0.7, 0.3, [[(LX - 110, LY + 30), (LX + 8, LY - 4), (LX - 110, LY + 6)]], AMBRE, 1.6, bip=500)


def tab_moderne(c, t):
    t0 = s(24)
    titres(c, t, [(t0, "TOUS LES ASCENSEURS", VERT_PALE, 60), (s(25), "+ PLUSIEURS CÂBLES", AMBRE, 60)])
    RG, RD = 330, 750
    trace(c, t, t0, 0.5, [[(RG, 440), (RG, 1400)], [(RD, 440), (RD, 1400)], [(RG - 40, 440), (RD + 40, 440)]], VERT,
          0.8, 0.8, bip=1200)
    CY0, CY1 = 820, 1200
    trace(c, t, t0 + 0.3, 0.5, [rect_pts(380, CY0, 700, CY1), [(540, CY0 + 20), (540, CY1 - 20)]], VERT_PALE, 1.2,
          bip=900)
    for x, sg in ((RG, 1), (RD, -1)):                                      # freins de sécurité
        trace(c, t, t0 + 0.9, 0.3, [rect_pts(x + sg * 6, CY0 - 10, x + sg * 50, CY0 + 50)], AMBRE, 1.3, bip=700)
    ecrit(c, t, t0 + 1.2, "FREIN", 230, CY0 + 30, 26, AMBRE)
    ecrit(c, t, t0 + 1.2, "FREIN", 850, CY0 + 30, 26, AMBRE)
    if t > s(25) - 0.3:
        for i in range(6):
            x = 470 + i * 28
            trace(c, t, s(25) - 0.3 + i * 0.1, 0.25, [[(x, 440), (x, CY0)]], VERT_PALE, 0.8, bip=1500 + 90 * i)
        ecrit(c, t, s(25) + 0.4, "x 6", 680, 620, 44, VERT_PALE, False)


def esb():
    """Silhouette à gradins de l'Empire State Building (102 étages, y = 1450 − 8 × étage)."""
    gr = [(0, 210), (5, 170), (30, 150), (72, 120), (81, 90), (86, 60), (102, 34)]
    def y(f):
        return 1450 - 8 * f
    g, d = [], []
    for (f0, hw), (f1, _) in zip(gr, gr[1:] + [(104, 0)]):
        g += [(540 - hw, y(f0)), (540 - hw, y(f1))]
        d += [(540 + hw, y(f0)), (540 + hw, y(f1))]
    contour = g + [(540, y(104) - 160)] + d[::-1]
    return [contour, [(80, 1450), (1000, 1450)]]


def tab_oliver(c, t):
    t0 = s(26)
    titres(c, t, [(t0, "1945 · EMPIRE STATE BUILDING", AMBRE, 44)])
    trace(c, t, t0, 0.9, esb(), VERT, 1.0, bip=1100)
    y75 = 1450 - 8 * 75
    trace(c, t, t0 + 2.2, 0.4, [[(300, y75), (780, y75)]], AMBRE, 0.8, bip=1500)
    ecrit(c, t, t0 + 2.3, "75e", 230, y75 + 12, 36, AMBRE)
    ecrit(c, t, t0 + 1.0, "BETTY LOU", 900, 800, 36, VERT_PALE)
    ecrit(c, t, t0 + 1.3, "OLIVER", 900, 846, 36, VERT_PALE)
    trace(c, t, t0 + 1.6, 0.3, [[(522, y75), (522, 1450)], [(558, y75), (558, 1450)]], VERT, 0.5, 0.7, bip=0)
    tc0, tc1 = t0 + 2.8, e(26) - 0.25
    q = min(1.0, max(0.0, (t - tc0) / (tc1 - tc0))) ** 2
    y = y75 + (1450 - 20 - y75) * q
    trace(c, t, t0 + 2.4, 0.2, [rect_pts(526, y, 554, y + 18)], AMBRE, 1.2, bip=900)
    if t > tc0:
        ecrit(c, t, tc0, f"ÉTAGE {75 * (1 - q):3.0f}", 900, 960, 34, AMBRE, vitesse=0.0)


def tab_survie(c, t):
    t0 = s(27)
    ecrit(c, t, t0 + 0.2, "ELLE A SURVÉCU", W / 2, 700, 72, VERT_PALE, True, 1.8)
    if t > t0:                                                              # électrocardiogramme
        BASE, X0, X1 = 1000, 60, 1020
        per = 0.85
        def ecg(tt):
            ph = (tt % per) / per
            if 0.30 < ph < 0.34:
                return -40 * math.sin((ph - 0.30) / 0.04 * math.pi)
            if 0.36 < ph < 0.38:
                return 50 * (ph - 0.36) / 0.02
            if 0.38 < ph < 0.40:
                return 50 - 260 * (ph - 0.38) / 0.02
            if 0.40 < ph < 0.43:
                return -210 + 240 * (ph - 0.40) / 0.03
            if 0.55 < ph < 0.68:
                return -50 * math.sin((ph - 0.55) / 0.13 * math.pi)
            return 0.0
        vit = 900                                                           # px/s
        tete = X0 + ((t - t0) * vit) % (X1 - X0)
        pts = []
        for i in range(160):
            x = tete - i * 4
            if x < X0:
                break
            tt = t - i * 4 / vit
            pts.append((x, BASE + ecg(tt - t0)))
        if len(pts) > 1:
            faisceau(c, [pts[::-1]], 1.0, VERT_PALE, 1.1)
        k = int((t - t0) / per)
        son(("coeur", k), t0 + k * per + 0.38 * per, "bip_coeur")
    if t > s(28):
        ecrit(c, t, s(28) + 0.1, "RECORD DU MONDE", W / 2, 1260, 72, AMBRE, True, 1.8)
        ecrit(c, t, s(28) + 0.6, "75 ÉTAGES · PLUS DE 300 m", W / 2, 1340, 34, VERT_PALE)


def tab_fin(c, t):
    t0 = s(29)
    FX0, FX1, FY0, FY1 = 330, 750, 640, 1300
    trace(c, t, t0, 0.5, [rect_pts(FX0 - 20, FY0 - 20, FX1 + 20, FY1)], VERT, 1.0, bip=1100)
    ouv = 150 * ease((t - s(30) - 0.2) / 1.6)
    trace(c, t, t0 + 0.3, 0.4, [rect_pts(FX0, FY0, 540 - ouv, FY1), rect_pts(540 + ouv, FY0, FX1, FY1)], VERT_PALE,
          1.0, bip=900)
    trace(c, t, t0 + 0.6, 0.3, [rect_pts(470, FY0 - 90, 610, FY0 - 40)], VERT, 0.8, bip=1500)
    etg = max(0, 7 - int((t - t0 - 0.6) * 4)) if t > t0 + 0.6 else 7
    ecrit(c, t, t0 + 0.6, f"▼ {etg}", 540, FY0 - 52, 32, AMBRE, vitesse=0.0)
    trace(c, t, t0 + 0.8, 0.3, [cercle_pts(830, 960, 20), cercle_pts(830, 1020, 20)], VERT, 0.8, bip=1700)
    if ouv > 30:                                                            # quelqu'un, calme, dans la cabine
        faisceau(c, bonhomme(540, FY1 - 10, 3.0, "debout"), min(1.0, (ouv - 30) / 60), VERT_PALE, 1.1)
    if t > s(30):                                                           # respiration
        a = 60 * ease((t - s(30)) / 1.0)
        pts = [(x, 1440 + a * math.sin((x - 80) / 920 * 2 * math.pi) * math.sin((t - s(30)) * 1.6))
               for x in range(80, 1001, 10)]
        faisceau(c, [pts], 1.0, VERT, 0.8, 0.9)
    titres(c, t, [(t0, "LA PROCHAINE FOIS…", VERT_PALE, 62), (s(30), "RESPIREZ.", VERT_PALE, 72)])
    if t > s(31):
        c.drawRect(skia.Rect(0, 230, W, 560), P((2, 8, 4), 0, 230, fill=True))
        ecrit(c, t, s(31), "LA PHYSIQUE EST", W / 2, 400, 74, AMBRE, True, 2.0)
        ecrit(c, t, s(31) + 0.5, "DE VOTRE CÔTÉ", W / 2, 490, 74, AMBRE, True, 2.0)


# ------------------------------------------------------------------------------------------------ montage
ETINCELLES = []


def tableaux():
    """(début, fonction, transition d'entrée)"""
    return [(0.0, tab_accroche, None), (s(5) - 0.1, tab_vitesse, "neige"), (s(8) - 0.1, tab_saut, "balayage"),
            (s(11) - 0.1, tab_flotte, "glitch"), (s(16) - 0.1, tab_solution, "noir"),
            (s(19) - 0.1, tab_rassure, "neige"), (s(20) - 0.1, tab_otis, "balayage"),
            (s(24) - 0.1, tab_moderne, "glitch"), (s(26) - 0.1, tab_oliver, "neige"),
            (s(27) - 0.05, tab_survie, "noir"), (s(29) - 0.1, tab_fin, "balayage")]


def preparer_mots():
    for a, b, txt in SEG:
        ws = txt.replace("…", "").split()
        lens = [len(w) + 1.5 for w in ws]
        tt = a
        for j, (w, ln) in enumerate(zip(ws, lens)):
            d = (b - a) * ln / sum(lens)
            MOTS.append((w.upper(), tt, tt + d, len(MOTS) - j, j))
            tt += d


def sous_titres(c, t):
    i = max([k for k, m in enumerate(MOTS) if m[1] <= t + 0.03] + [-1])
    if i < 0 or t > MOTS[i][2] + 0.4:
        return
    deb, rang = MOTS[i][3], MOTS[i][4]
    g0 = deb + (rang // 3) * 3
    grp = [m for m in MOTS[g0:g0 + 3] if m[3] == deb]
    taille = 58
    f = skia.Font(MONO, taille)
    sp = f.measureText(" ")
    tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    while tot > W - 140:
        taille -= 4
        f = skia.Font(MONO, taille)
        sp = f.measureText(" ")
        tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    x = (W - tot) / 2
    for k, m in enumerate(grp):
        col = AMBRE if g0 + k == i else VERT_PALE
        c.drawString(m[0], x, 1650, f, P((0, 0, 0), 10, 220))
        c.drawString(m[0], x, 1650, f, P(col, 0, 200, 8, fill=True))
        c.drawString(m[0], x, 1650, f, P(col, 0, 255, fill=True))
        x += f.measureText(m[0]) + sp


def neige(c):
    bruit = RNG.integers(0, 255, (240, 135), dtype=np.uint8)
    rgba = np.dstack([bruit, np.minimum(255, bruit.astype(int) + 30).astype(np.uint8), bruit,
                      np.full_like(bruit, 200)])
    img = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType)
    c.drawImageRect(img, skia.Rect(0, 0, W, H))


def ecran(c, t, flashs):
    for y in range(0, H, 4):
        c.drawLine(0, y, W, y, P((0, 0, 0), 2, 80))
    g = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1150, [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 220)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))
    for tf in flashs:
        if tf <= t < tf + 0.1:
            c.drawRect(skia.Rect(0, 0, W, H), P((200, 255, 215), 0, 80, fill=True))


def chocs():
    """Instants de flash blanc et de secousse de l'image (les autres épisodes remplacent cette fonction)."""
    t_rupture = e(0) - 0.55
    flashs = [t_rupture, s(3) + 0.05, s(21) + 0.55, e(26) - 0.25]
    secousses = [(t_rupture, 0.25), (s(3) + 0.05, 0.2), (s(21) + 0.55, 0.2), (e(26) - 0.25, 0.35)]
    return flashs, secousses


def preparer():
    v, N, _ = MI.tighten(MI.load_voice(VOIX), max_gap=0.40, thr_db=-38.0)
    SEG[:] = [(N(a), N(b), txt) for a, b, txt in json.load(open(SEGS))]
    preparer_mots()
    return v


def render(out):
    voix = preparer()
    dur = SEG[-1][1] + 1.8
    tabs = tableaux()
    flashs, secousses = chocs()
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-preset", "medium", f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    for fr in range(int(dur * FPS)):
        t = fr / FPS
        k = max(i for i, x in enumerate(tabs) if x[0] <= t)
        t_tab, fn, trans = tabs[k]
        dt = t - t_tab
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        if trans == "noir" and dt < 0.05:
            prec = None
        if prec is not None:
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), P((0, 0, 0), 0, ALPHA_PERSISTANCE, fill=True))
        c.save()
        for ts, d in secousses:
            if ts <= t < ts + d:
                c.translate(RNG.normal(0, 7), RNG.normal(0, 3))
        if trans == "balayage" and dt < 0.35:                             # le nouveau tableau apparaît sous la ligne
            yb = H * ease(dt / 0.35)
            c.clipRect(skia.Rect(0, 0, W, yb))
        fn(c, t)
        for p in ETINCELLES:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.8
            p[4] -= 0.05
        ETINCELLES[:] = [p for p in ETINCELLES if p[4] > 0]
        for p in ETINCELLES:
            c.drawCircle(p[0], p[1], 3, P(AMBRE, 0, 255 * p[4], 3, fill=True))
        c.restore()
        if trans == "balayage" and dt < 0.35:
            yb = H * ease(dt / 0.35)
            c.drawLine(0, yb, W, yb, P(VERT_PALE, 6, 230, 6))
            c.drawLine(0, yb, W, yb, P((255, 255, 255), 2, 255))
        if trans == "glitch" and dt < 0.25:
            img = surf.makeImageSnapshot()
            for _ in range(10):
                y0 = RNG.uniform(0, H - 60)
                hh = RNG.uniform(10, 90)
                dx = RNG.normal(0, 60)
                c.drawImageRect(img, skia.Rect(0, y0, W, y0 + hh), skia.Rect(dx, y0, W + dx, y0 + hh))
        prec = surf.makeImageSnapshot()
        sous_titres(c, t)
        if trans == "neige" and dt < 0.14:
            neige(c)
        if trans == "noir" and dt < 0.3:
            c.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0, 255 * (1 - dt / 0.3), fill=True))
        ecran(c, t, flashs)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
        if fr % 300 == 0:
            print(f"{t:5.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()
    mixage(f"{tmp}/a.wav", voix, dur, tabs)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", volume_cible(f"{tmp}/a.wav"), "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK", out)


# ------------------------------------------------------------------------------------------------ son
def _rs(snd):
    return np.interp(np.arange(int(len(snd) * MI.SR / E1.SR)) * E1.SR / MI.SR, np.arange(len(snd)), snd)


def bruit_blanc(d, amp):
    n = int(d * E1.SR)
    return RNG.normal(0, amp, n) * np.linspace(1, 0, n) ** 2


def effets(tabs):
    """Effets sonores variés, placés sur l'image (t, son)."""
    t_r, t_f = e(0) - 0.55, e(1) - 0.15
    ev = [(0.0, Z.allumage(0.35)), (0.0, Z.crepitement(0.4, 0.05)),
          (t_r, Z.snap(0.55)), (t_r, Z.boom(0.45, 80)), (t_r + 0.05, Z.vent(t_f - t_r - 0.05, 0.28)),
          (t_r + 0.1, Z.crepitement(t_f - t_r - 0.1, 0.10, 50)), (t_f, Z.arret_bande(0.6, 0.3)),
          (s(1) + 1.2, Z.alarme(0.08, 2)), (s(2) + 0.2, Z.chirp(500, 1100, 0.25, 0.08)),
          (s(3) - 0.9, Z.riser(0.9, 0.12)), (s(3) + 0.05, Z.boom(0.75, 55)), (s(3) + 0.05, Z.clang(110, 0.2, 2.0)),
          (s(4) + 0.3, Z.whoosh(0.4, 0.12))]
    # vitesse
    tc0, tc1 = s(5) + 0.6, e(6) - 0.5
    ev += [(tc0, Z.vent(tc1 - tc0, 0.22)), (tc0, Z.sifflement(tc1 - tc0, 0.05, 400, 1600)),
           (s(7), Z.boom(0.4, 70)), (s(7) + 0.1, Z.chirp(1200, 1900, 0.4, 0.07))]
    ev += [(tc0 + i * 0.07, Z.cliquet(0.04)) for i in range(int((tc1 - tc0) / 0.07))]
    # saut
    ev += [(s(8) + 0.2, Z.chirp(180, 900, 0.8, 0.10)), (s(8) + 1.4, Z.chirp(500, 1500, 0.22, 0.12)),
           (s(9), Z.chirp(180, 820, 0.5, 0.10)), (s(9) + 0.3, Z.chirp(820, 700, 1.4, 0.04)),
           (s(10), Z.thump(0.35)), (s(10) + 0.4, Z.chirp(900, 450, 0.25, 0.08))]
    # apesanteur
    ev += [(s(11) + 0.2, Z.vent(s(16) - s(11) - 0.3, 0.10, 120, 700)), (s(12) + 1.0, Z.whoosh(0.35, 0.10, False)),
           (s(12) + 2.4, Z.whoosh(0.35, 0.10, False)), (s(13), Z.scintillement(2.6, 0.08)),
           (s(14) + 0.1, Z.alarme(0.09, 3)), (s(15) + 0.4, Z.clang(1200, 0.08, 0.6)),
           (s(15) + 0.7, Z.tictac(e(15) - s(15) - 0.7, 0.07)), (s(15) + 2.2, Z.chirp(2000, 2000, 0.08, 0.06))]
    # que faire
    ev += [(s(17) + 0.6, Z.thump(0.3)), (s(17) + 2.2, Z.thump(0.3)), (s(17) + 1.6, Z.whoosh(0.3, 0.08))]
    ev += [(s(18) + 0.3 + 0.06 * i, Z.pince(1046.5 * 2 ** (i / 12 * 2), 0.04, 0.3)) for i in range(9)]
    ev += [(s(18) + 2.0, Z.boom(0.4, 90)), (s(18) + 2.05, Z.craquement(0.15)), (s(18) + 3.0, Z.thump(0.35)),
           (s(18) + 3.0, Z.craquement(0.2))]
    # rassurez-vous
    ev += [(s(19) + 0.9, Z.cloche(523.3, 0.12)), (s(19) + 1.3, Z.cloche(659.3, 0.12)),
           (s(19) + 1.7, Z.cloche(784, 0.10))]
    # Otis
    t_coupe = s(21) + 0.55
    ev += [(s(20) + 0.1, Z.cliquet(0.06)), (s(20) + 2.6, Z.foule(t_coupe - s(20) - 2.4, 0.07)),
           (t_coupe - 0.3, Z.riser(0.3, 0.06)), (t_coupe, Z.snap(0.5)), (t_coupe + 0.12, Z.exclamation(0.13)),
           (t_coupe + 0.05, Z.cliquet(0.2)), (t_coupe + 0.12, Z.cliquet(0.16)), (t_coupe + 0.15, Z.clang(300, 0.22)),
           (s(22) + 0.3, Z.boom(0.3, 70)), (s(22) + 0.5, Z.applaudissements(2.4, 0.09)),
           (s(23) + 0.1, Z.whoosh(0.35, 0.08)), (s(23) + 0.7, Z.cliquet(0.15)), (s(23) + 0.78, Z.cliquet(0.12))]
    # ascenseur moderne
    ev += [(s(24) + 0.9, Z.clang(250, 0.16, 0.8)), (s(24) + 0.95, Z.clang(262, 0.12, 0.8))]
    ev += [(s(25) - 0.3 + i * 0.1, Z.pince(f, 0.08)) for i, f in enumerate((349.2, 392, 440, 523.3, 587.3, 698.5))]
    # Empire State Building
    tc0, tc1 = s(26) + 2.8, e(26) - 0.25
    ev += [(s(26) + 2.2, Z.chirp(1500, 1500, 0.1, 0.05)), (tc0, Z.vent(tc1 - tc0, 0.24)),
           (tc0, Z.sifflement(tc1 - tc0, 0.06)), (tc1 - 1.2, Z.riser(1.2, 0.08)),
           (tc1, Z.boom(0.8, 50)), (tc1, Z.clang(140, 0.25, 1.8)), (tc1, Z.crepitement(0.5, 0.2, 150))]
    ev += [(tc0 + i * 0.09, Z.cliquet(0.035)) for i in range(int((tc1 - tc0) / 0.09))]
    # survie : battements
    k = 0
    while s(27) + k * 0.85 + 0.32 < s(29) - 0.2:
        ev.append((s(27) + k * 0.85 + 0.30, Z.coeur(0.22)))
        k += 1
    ev += [(s(28) + 0.1, Z.boom(0.4, 70)), (s(28) + 0.15, Z.cloche(1046.5, 0.12)), (s(28) + 0.15, Z.cloche(1318.5, 0.09))]
    # fin
    ev += [(s(29) + 0.6, Z.cliquet(0.05)), (s(30) - 0.6, Z.ding_ascenseur(0.18)), (s(30) + 0.2, Z.porte(1.6, 0.08)),
           (s(30), Z.souffle(1.0, 0.07, True)), (s(30) + 1.1, Z.souffle(1.3, 0.06, False)),
           (s(31), Z.boom(0.3, 60)), (s(31) + 0.6, Z.cloche(698.5, 0.14, 3.0)), (s(31) + 0.6, Z.cloche(880, 0.10, 3.0))]
    # transitions
    for t0, _, tr in tabs[1:]:
        ev.append((t0, {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
                        "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}[tr]()))
    return ev


def mixage(path, voix, dur, tabs):
    n = int(dur * MI.SR)
    v = np.zeros(n)
    v[:min(n, len(voix))] = voix[:n]
    v *= 10 ** (-16 / 20) / (np.sqrt((v[np.abs(v) > 0.01] ** 2).mean()) + 1e-9)
    a = v                                                                  # pas de musique de fond
    ev = []
    for t0, kind, args in SONS.values():                                   # bips du faisceau et frappe
        if kind == "trace":
            f0, d = args
            ev.append((t0, E1.pop_s(f0, 0.04)))
            for i in range(1, int(d / 0.13)):
                ev.append((t0 + 0.13 * i, E1.pop_s(f0 + 150 * (i % 3), 0.010)))
        elif kind == "frappe":
            nb, d = args
            for i in range(min(nb, 12)):
                ev.append((t0 + d * i / max(1, min(nb, 12)), E1.pop_s(1800 + 40 * (i % 4), 0.014)))
        elif kind == "bip_coeur":
            ev.append((t0, E1.tone(1000, 0.12, 0.08, 0.002, 0.08)))
    ev += effets(tabs)
    fx = np.zeros(n)
    for t0, snd in ev:
        i = int(t0 * MI.SR)
        k = min(n - i, len(snd))
        if k > 0 and i >= 0:
            fx[i:i + k] += snd[:k]
    a = a + fx * 0.6
    a *= np.minimum(1, (n - np.arange(n)) / (0.6 * MI.SR))
    a = a / max(1.0, np.abs(a).max() / 0.95)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(MI.SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def volume_cible(wav, cible=-14.0):
    """Filtre ffmpeg qui amène le mixage à la sonie cible (mesure EBU R128, puis limiteur)."""
    log = subprocess.run(["ffmpeg", "-i", wav, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", log)[-1])
    return f"volume={cible - i + 1.0:.2f}dB,alimiter=limit=0.89:level=disabled"


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep21_oscillo.mp4")
