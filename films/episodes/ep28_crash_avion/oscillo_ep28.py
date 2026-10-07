"""Épisode 28 — « Si vous êtes dans un avion sur le point de s'écraser… » (la physique du crash) — style oscilloscope.

Une seule voix. 6 lois de physique (inertie, distance, temps, F = m·a, fumée, eau) : le tableau des lois en haut de
l'écran s'allume au fil de la vidéo. Fin coupée + « LA SUITE DEMAIN ▶ ».
Découpage : script.md. Dessins : films/illustrations (as_*, ev_*, pe_*, av_*, cab_*, si_*, ph_*, sac_*, ex_*, fe_*,
eau_*, gr_*), outil planche_en_traits.

    python -m films.episodes.ep28_crash_avion.oscillo_ep28 output/ep28.mp4
"""
import json
import math
import os
import sys

import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, P, W, cercle_pts, ease, ecrit, faisceau,
                                                         fleche, trace)
from films.outils.image_en_traits import DOSSIER, dessin
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
M.SEGS = os.path.join(HERE, "audio", "voix.json")
M.FPS = 24
s, e = M.s, M.e

LOIS = ["INERTIE", "DISTANCE", "TEMPS", "F = m·a", "FUMÉE", "EAU"]


def TL():
    return [s(8), s(15), s(21), s(31), s(41), s(50)]


# ------------------------------------------------------------------------------------------------ outils
_INFO = {}


def info(nom):
    if nom not in _INFO:
        _INFO[nom] = json.load(open(os.path.join(DOSSIER, nom + ".json")))
    return _INFO[nom]


def pose(nom, cx, bas, k, miroir=False):
    """Un dessin de planche à l'échelle commune k (pixels d'écran par pixel de planche), posé en (cx, bas)."""
    d = info(nom)
    w = d["px"][0] * k
    return dessin(nom, cx - w / 2, bas - w * d["ratio"], w, miroir)


def objet(nom, cx, cy, larg, miroir=False):
    d = info(nom)
    return dessin(nom, cx - larg / 2, cy - larg * d["ratio"] / 2, larg, miroir)


def boite(nom, cx, cy, larg):
    """Rectangle (x0, y0, x1, y1) occupé par objet(nom, cx, cy, larg)."""
    h = larg * info(nom)["ratio"]
    return cx - larg / 2, cy - h / 2, cx + larg / 2, cy + h / 2


def u(t, t0, d):
    return ease(max(0.0, min(1.0, (t - t0) / d)))


def croix(cx, cy, r=34):
    return [[(cx - r, cy - r), (cx + r, cy + r)], [(cx + r, cy - r), (cx - r, cy + r)]]


def coche(cx, cy, r=34):
    return [[(cx - 0.8 * r, cy), (cx - 0.2 * r, cy + 0.7 * r), (cx + r, cy - 0.7 * r)]]


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]


def suite(c, t, tab, cx, bas, k, col=VERT_PALE, bip=1100, miroir=False):
    """Un dessin qui change de pose : tab = [(t0, nom ou None), …] ; chaque nouvelle pose se retrace."""
    nom, t0 = None, 0.0
    for tt, n in tab:
        if t >= tt:
            nom, t0 = n, tt
    if nom:
        trace(c, t, t0, 0.35, pose(nom, cx, bas + 1.5 * math.sin(t * 2.0), k, miroir), col, 1.2, 1.0, bip=bip)


def apres(c, t, t0, nom, cx, cy, larg, col=VERT_PALE, d=0.5, bip=1500, miroir=False, intense=1.0, t1=None):
    if t < t0 or (t1 is not None and t >= t1):
        return
    trace(c, t, t0, d, objet(nom, cx, cy, larg, miroir), col, 1.2, intense, bip=bip)


def tampon(c, t, t0, lignes, cx, cy, ang=-8, taille=74, col=AMBRE, t1=None):
    """Un tampon qui s'écrase sur l'écran (grossi, puis à sa taille)."""
    if t < t0 or (t1 is not None and t > t1):
        return
    k = 1 + 1.3 * max(0.0, 1 - (t - t0) / 0.14)
    wb = max(len(l) for l in lignes) * taille * 0.62 + 56
    hb = len(lignes) * taille * 1.12 + 34
    c.save()
    c.translate(cx, cy)
    c.rotate(ang)
    c.scale(k, k)
    faisceau(c, [rect(-wb / 2, -hb / 2, wb, hb)], 1.0, col, 2.4, 1.0)
    faisceau(c, [rect(-wb / 2 + 10, -hb / 2 + 10, wb - 20, hb - 20)], 1.0, col, 1.0, 0.6)
    for i, l in enumerate(lignes):
        ecrit(c, t, t0, l, 0, -hb / 2 + 18 + taille * (0.9 + 1.12 * i), taille, col, True, 2.0, vitesse=0.0)
    c.restore()


def titre(c, t, t0, txt, col=VERT_PALE, y=300, taille=58):
    ecrit(c, t, t0, txt, W / 2, y, taille, col, True, 1.6)


def tableau_lois(c, t):
    """Les 6 lois, en haut de l'écran : elles s'allument l'une après l'autre ; la loi du moment est en ambre."""
    t0 = s(6)
    if t < t0:
        return
    tl = TL()
    cour = max([i for i in range(6) if tl[i] <= t] + [-1])
    for i, nom in enumerate(LOIS):
        x0 = 30 + 170 * i
        box = [rect(x0, 120, 155, 84)]
        v = u(t, t0 + 0.1 * i, 0.3)
        if t >= tl[i]:
            col = AMBRE if i == cour else VERT_PALE
            flash = tl[i] <= t < tl[i] + 0.2
            faisceau(c, box, 1.0, col, 2.0 if flash else 1.5, 1.0)
            ecrit(c, t, tl[i], nom, x0 + 77, 174, 27, col, True, 1.4, vitesse=0.0)
        elif v > 0:
            faisceau(c, box, v, VERT, 0.8, 0.4)
            ecrit(c, t, t0, str(i + 1), x0 + 77, 178, 46, VERT, True, 1.0, vitesse=0.0)


def mini_perso(x, y, r=10):
    """Une petite silhouette : tête + corps (pour la grille des 100 passagers)."""
    return [cercle_pts(x, y, r, 10), [(x, y + r), (x, y + 3.2 * r)], [(x - 1.4 * r, y + 1.8 * r), (x + 1.4 * r, y + 1.8 * r)],
            [(x, y + 3.2 * r), (x - r, y + 4.8 * r)], [(x, y + 3.2 * r), (x + r, y + 4.8 * r)]]


# ------------------------------------------------------------------------------------------------ écrans
def e1(c, t):
    """Image 0 : la cabine qui clignote, le passager ; les masques tombent ; l'avion pique du nez ; le chronomètre."""
    vac = 0.55 + 0.45 * abs(math.sin(t * 17.0) * math.sin(t * 5.3))
    if t < s(1):
        faisceau(c, objet("cab_clignote", W / 2, 640, 900), 1.0, VERT_PALE, 1.2, vac)
    elif t < s(2):
        apres(c, t, s(1), "cab_masques", W / 2, 640, 900, VERT_PALE, 0.5, 1500, intense=vac)
    else:
        apres(c, t, s(2), "av_descente", W / 2, 590, 940, VERT_PALE, 0.7, 1300)
        ecrit(c, t, s(2) + 0.4, "?", 140, 1300, 190, AMBRE, True, 2.4, vitesse=0.0)
    suite(c, t, [(0.0, "as_regarde_haut")], W / 2, 1500, 1.45)
    if t >= s(1):
        apres(c, t, s(1), "ex_chrono", 915, 1210, 200, VERT_PALE, 0.4, 1700)
        a = -math.pi / 2 + 2 * math.pi * ((t - s(1)) / 3.0 % 1.0)
        faisceau(c, [[(915, 1235), (915 + 62 * math.cos(a), 1235 + 62 * math.sin(a))]], 1.0, AMBRE, 2.0)
    if t >= s(0) + 0.3:
        ecrit(c, t, 0.3, "AVION EN DÉTRESSE", W / 2, 1570, 38, AMBRE, True, 1.6)


def e2(c, t):
    """95 passagers sur 100 : la grille de 100 petits passagers se remplit jusqu'à 95."""
    pas, x0, y0 = 66, 207, 360
    n = int(95 * u(t, s(5), 2.4))
    if t >= s(3):
        ecrit(c, t, s(3), "ÉTATS-UNIS · AVIONS DE LIGNE", W / 2, 320, 36, VERT_PALE, True, 1.4)
    if t >= s(4):
        ecrit(c, t, s(4), "ACCIDENTS 1983-2000", W / 2, 360, 32, VERT, True, 1.2)
    for k in range(100):
        r, q = divmod(k, 10)
        x, y = x0 + pas * q, y0 + 40 + pas * r * 1.12
        v = u(t, s(3) + 0.012 * k, 0.3)
        if v <= 0:
            continue
        if t >= s(5) and k < n:
            faisceau(c, mini_perso(x, y), 1.0, VERT_PALE, 1.4, 1.0)
        elif t >= s(5) + 2.5 and k >= 95:
            faisceau(c, mini_perso(x, y), 1.0, AMBRE, 1.4, 0.8)
            faisceau(c, croix(x, y + 26, 14), 1.0, AMBRE, 1.8)
        else:
            faisceau(c, mini_perso(x, y), v, VERT, 0.8, 0.5)
    if t >= s(5):
        ecrit(c, t, s(5), "95 %", W / 2, 1370, 210, AMBRE, True, 2.4, vitesse=0.0)
    if t >= s(5) + 2.6:
        ecrit(c, t, s(5) + 2.6, "ONT SURVÉCU", W / 2, 1450, 54, VERT_PALE, True, 1.6)
    if t >= s(6):
        ecrit(c, t, s(6), "LES GESTES QUI SAUVENT", W / 2, 1530, 48, AMBRE, True, 1.8)


def e4(c, t):
    """1. L'inertie : l'avion s'arrête, le corps continue ; la ceinture le retient ; sans elle, le dossier ou le mur."""
    titre(c, t, s(7), "1 · L'INERTIE")
    apres(c, t, s(7) + 0.2, "av_piste", W / 2, 540, 900, VERT_PALE, 0.6, 1300)
    if t >= s(9) and t < s(9) + 1.0:                                              # l'avion freine : traits de vitesse
        for k in range(3):
            faisceau(c, [[(60, 470 + 40 * k), (180, 470 + 40 * k)]], 1.0, AMBRE, 1.6, 1 - (t - s(9)))
    if t >= s(9):
        ecrit(c, t, s(9), "AVION : STOP", 270, 760, 40, VERT_PALE, True, 1.4)
    tab = [(s(8), "as_neutre"), (s(10), "as_serre_ceinture"), (s(10) + 1.6, "as_attache"), (s(11), "as_neutre")]
    suite(c, t, tab, 560, 1500, 1.5)
    if t >= s(9) and t < s(10):                                                  # le corps veut continuer
        v = u(t, s(9) + 0.3, 1.0)
        faisceau(c, fleche(460, 1180, 460 + 280 * v, 1180, 30), 1.0, AMBRE, 2.4)
        ecrit(c, t, s(9) + 0.5, "LE CORPS CONTINUE", 590, 1560, 36, AMBRE, True, 1.6)
    if t >= s(10):
        apres(c, t, s(10), "si_ceinture_fermee", 175, 1000, 270, VERT_PALE, 0.5, 1700)
    if s(10) + 1.6 <= t < s(11):
        faisceau(c, fleche(460, 1180, 520, 1180, 30), 1.0, VERT_PALE, 2.4)
        ecrit(c, t, s(10) + 1.7, "RETENU", 560, 1560, 40, VERT_PALE, True, 1.6)
        trace(c, t, s(10) + 1.7, 0.3, coche(175, 1130, 36), VERT_PALE, 3.0, bip=1600)
    if t >= s(11):
        trace(c, t, s(11), 0.2, croix(175, 1000, 130), AMBRE, 2.8, bip=500)
        v = u(t, s(11) + 0.3, 0.8)
        faisceau(c, fleche(480, 1180, 480 + 270 * v, 1180, 30), 1.0, AMBRE, 2.4)
    if t >= s(12):
        ecrit(c, t, s(12), "OU LE MUR", 800, 780, 40, AMBRE, True, 1.6)
        trace(c, t, s(12), 0.4, [[(940, 820), (940, 1500)], [(940, 900), (1000, 860)], [(940, 1000), (1000, 960)],
                                 [(940, 1100), (1000, 1060)], [(940, 1200), (1000, 1160)]], AMBRE, 2.0, bip=900)
    if t >= s(13):
        tampon(c, t, s(13), ["SANS CEINTURE"], 540, 840, 7, 52, AMBRE, t1=s(14))


def e5(c, t):
    """2. La distance : la position de sécurité ; moins de distance, moins de vitesse, moins de force."""
    titre(c, t, s(14), "2 · LA DISTANCE")
    if t < s(19):
        suite(c, t, [(s(15), "as_brace")], 540, 1480, 1.9)
        w = 322 * 1.9
        h = w * info("as_brace")["ratio"]
        x0, y0 = 540 - w / 2, 1480 - h
        tx, ty = x0 + 0.78 * w, y0 + 0.12 * h                                    # la tête
        if t >= s(16):
            trace(c, t, s(16), 0.4, fleche(tx + 60, ty - 120, tx + 12, ty - 14, 24), AMBRE, 2.2, bip=1500)
            ecrit(c, t, s(16), "TÊTE PENCHÉE", 330, ty - 130, 40, AMBRE, True, 1.6)
        if t >= s(17):
            ecrit(c, t, s(17), "PRÈS DU SIÈGE", 330, ty - 70, 40, VERT_PALE, True, 1.6)
            trace(c, t, s(17), 0.3, fleche(tx + 10, ty + 60, tx + 70, ty + 60, 18), VERT_PALE, 2.0, bip=1500)
        if t >= s(18):
            bx, by = x0 + 0.52 * w, y0 + 0.78 * h                                # les bras
            trace(c, t, s(18), 0.4, fleche(bx - 130, by + 100, bx - 30, by + 20, 24), AMBRE, 2.2, bip=1500)
            ecrit(c, t, s(18), "BRAS BAS", bx - 190, by + 130, 40, AMBRE, True, 1.6)
    else:
        suite(c, t, [(s(19), "as_attache")], 270, 1300, 1.45)
        suite(c, t, [(s(19) + 0.3, "as_brace")], 810, 1300, 1.45)
        wl, wr = 317 * 1.45, 322 * 1.45
        hl, hr = wl * info("as_attache")["ratio"], wr * info("as_brace")["ratio"]
        xl, yl = 270 - wl / 2, 1300 - hl
        xr, yr = 810 - wr / 2, 1300 - hr
        trace(c, t, s(19) + 0.4, 0.5, fleche(xl + 0.30 * wl, yl + 0.16 * hl, xl + 0.9 * wl, yl + 0.16 * hl, 20) +
              fleche(xl + 0.9 * wl, yl + 0.16 * hl, xl + 0.30 * wl, yl + 0.16 * hl, 20), VERT_PALE, 1.8, bip=1500)
        ecrit(c, t, s(19) + 0.5, "LOIN", 270, 680, 56, VERT_PALE, True, 1.6)
        trace(c, t, s(19) + 0.9, 0.3, fleche(xr + 0.74 * wr, yr + 0.20 * hr, xr + 0.9 * wr, yr + 0.20 * hr, 14), VERT_PALE, 1.8, bip=1500)
        ecrit(c, t, s(19) + 0.9, "PRÈS", 810, 680, 56, VERT_PALE, True, 1.6)
        ecrit(c, t, s(20), "FORCE", 540, 1420, 34, VERT, True, 1.2)
        vl, vr = u(t, s(20), 0.6), u(t, s(20) + 0.3, 0.6)
        faisceau(c, [rect(130, 1450, 280 * vl, 36)], 1.0, AMBRE, 2.2)
        faisceau(c, [rect(670, 1450, 70 * vr, 36)], 1.0, VERT_PALE, 2.0)
        ecrit(c, t, s(20) + 0.4, "FORT", 270, 1540, 44, AMBRE, True, 1.6)
        ecrit(c, t, s(20) + 0.7, "FAIBLE", 810, 1540, 44, VERT_PALE, True, 1.6)


def e6a(c, t):
    """3. Le temps : une vitesse à perdre ; choc court = force haute, choc long = force basse."""
    titre(c, t, s(21), "3 · LE TEMPS")
    if t < s(24):
        apres(c, t, s(23) - 0.3, "ph_balles", W / 2, 760, 940, VERT_PALE, 0.7, 1300)
        if t >= s(23):
            ecrit(c, t, s(23), "VITESSE  →  0", W / 2, 1230, 60, AMBRE, True, 1.8)
            trace(c, t, s(23) + 0.4, 0.4, fleche(250, 1310, 830, 1310, 30), AMBRE, 2.2, bip=1500)
        return
    x0, y0, x1, y1 = 140, 1180, 960, 480                                          # le graphe force / temps
    trace(c, t, s(24), 0.5, [[(x0, y1 - 20), (x0, y0)], [(x0, y0), (x1, y0)]], VERT, 1.4, 0.9, bip=1300)
    ecrit(c, t, s(24), "FORCE", x0 + 10, y1 - 30, 34, VERT_PALE, False, 1.4)
    ecrit(c, t, s(24), "TEMPS", x1, y0 + 56, 34, VERT_PALE, True, 1.4)
    n = 60
    court = [(x0 + 70 + 12 * i, y0 - 590 * math.exp(-((i - 7) ** 2) / 14)) for i in range(0, 22)]
    long_ = [(x0 + 70 + 12 * i, y0 - 200 * math.exp(-((i - 24) ** 2) / 190)) for i in range(0, 61)]
    trace(c, t, s(24) + 0.3, 0.9, [court], AMBRE, 2.6, bip=1200)
    ecrit(c, t, s(24) + 0.9, "COURT : FORCE HAUTE", 560, 640, 38, AMBRE, True, 1.6)
    trace(c, t, s(24) + 1.0, 1.4, [long_], VERT_PALE, 2.6, bip=1200)
    ecrit(c, t, s(25), "LONG : FORCE BASSE", 640, 960, 38, VERT_PALE, True, 1.6)


def e6b(c, t):
    """Tout est fait pour freiner en écrasant : la structure, le sol, les sièges."""
    titre(c, t, s(21), "3 · LE TEMPS")
    apres(c, t, s(27), "ph_accordeon", 290, 620, 480, VERT_PALE, 0.6, 1300)
    if t >= s(27) + 0.4:
        trace(c, t, s(27) + 0.4, 0.3, fleche(60, 620, 110, 620, 20) + fleche(520, 620, 470, 620, 20), AMBRE, 2.2, bip=1500)
    ecrit(c, t, s(28), "STRUCTURE", 290, 820, 42, VERT_PALE, True, 1.6)
    apres(c, t, s(28) + 0.5, "ph_ressort", 790, 620, 340, VERT_PALE, 0.6, 1300)
    ecrit(c, t, s(28) + 0.7, "SOL", 790, 820, 42, VERT_PALE, True, 1.6)
    apres(c, t, s(28) + 1.1, "si_siege_coupe", 540, 1180, 330, VERT_PALE, 0.7, 1300)
    ecrit(c, t, s(28) + 1.3, "SIÈGES", 540, 1470, 42, VERT_PALE, True, 1.6)


def e6c(c, t):
    """Testés à 16 g : seize fois le poids."""
    titre(c, t, s(21), "3 · LE TEMPS")
    apres(c, t, s(29), "ph_mannequin", 340, 880, 560, VERT_PALE, 0.7, 1300)
    ecrit(c, t, s(29), "16 G", 800, 700, 200, AMBRE, True, 2.6, vitesse=0.0)
    tampon(c, t, s(29) + 0.2, ["TESTÉS"], 800, 480, -6, 56, VERT_PALE, t1=s(31))
    if t >= s(30):
        apres(c, t, s(30), "ph_poids16", 820, 1230, 190, VERT_PALE, 0.7, 1500)
        trace(c, t, s(30) + 0.3, 0.4, fleche(520, 1230, 680, 1230, 26), AMBRE, 2.4, bip=1500)
        ecrit(c, t, s(30) + 0.3, "16 × SON POIDS", 400, 1480, 44, AMBRE, True, 1.8)


def e7(c, t):
    """4. F = m × a : un sac de 7 kg devient 112 kg à 16 g."""
    titre(c, t, s(31), "4 · F = m × a")
    apres(c, t, s(31), "cab_coffre_ouvert", W / 2, 590, 920, VERT_PALE, 0.7, 1300)
    if t >= s(31) + 0.6:
        ecrit(c, t, s(31) + 0.6, "VOTRE SAC", W / 2, 910, 56, AMBRE, True, 1.8)
    if t >= s(32):
        apres(c, t, s(32), "sac_dos", 230, 1150, 220, VERT_PALE, 0.5, 1500)
        ecrit(c, t, s(32), "7 KG", 230, 1370, 56, VERT_PALE, True, 1.6)
    if t >= s(32) + 1.2:
        trace(c, t, s(32) + 1.2, 0.5, fleche(380, 1150, 600, 1150, 28), AMBRE, 2.4, bip=1500)
        ecrit(c, t, s(32) + 1.2, "× 16", 490, 1110, 56, AMBRE, True, 1.8)
    if t >= s(32) + 2.0:
        apres(c, t, s(32) + 2.0, "ph_kettlebell", 800, 1150, 290, VERT_PALE, 0.6, 1700)
        ecrit(c, t, s(32) + 2.2, "112 KG", 800, 1440, 64, AMBRE, True, 2.0)


def e7b(c, t):
    """Le sac qui part : il fonce vers le passager."""
    titre(c, t, s(31), "4 · F = m × a")
    suite(c, t, [(s(32) + 3.2, "as_regarde_haut")], 270, 1500, 1.15)
    v = u(t, s(32) + 3.5, 1.1)
    faisceau(c, objet("sac_vol", 940 - 560 * v, 900, 360), 1.0, AMBRE, 2.2, 1.0)
    ecrit(c, t, s(32) + 3.6, "112 KG", 700, 760, 90, AMBRE, True, 2.2)
    for k in range(3):
        faisceau(c, [[(1000 - 560 * v, 980 + 24 * k), (1060 - 560 * v + 20 * k, 980 + 24 * k)]], 1.0, AMBRE, 1.5, 0.7)


def e8a(c, t):
    """Puis l'avion s'arrête : le chronomètre de 90 secondes, l'incendie qui s'étend."""
    titre(c, t, s(33), "LE CHRONOMÈTRE", AMBRE)
    apres(c, t, s(33), "av_arrete", W / 2, 560, 940, VERT_PALE, 0.7, 1300)
    apres(c, t, s(34), "ex_chrono", 290, 1030, 400, VERT_PALE, 0.6, 1700)
    a = -math.pi / 2 + 2 * math.pi * (max(0.0, t - s(34)) / 90.0 * 12)           # accéléré pour la lecture
    if t >= s(34):
        faisceau(c, [[(290, 1065), (290 + 120 * math.cos(a), 1065 + 120 * math.sin(a))]], 1.0, AMBRE, 2.4)
    if t >= s(35):
        ecrit(c, t, s(35), "90 S", 290, 1330, 96, AMBRE, True, 2.4)
    if t >= s(36):
        g = 0.4 + 0.6 * u(t, s(36), 2.4)
        apres(c, t, s(36), "fe_flammes", 790, 1090, 440 * g, AMBRE, 0.5, 1500)
        ecrit(c, t, s(36) + 0.6, "L'INCENDIE S'ÉTEND", 790, 1380, 36, AMBRE, True, 1.6)


def e8b(c, t):
    """On laisse le sac ; Dubaï : près de 7 minutes, certains avec leurs bagages."""
    titre(c, t, s(37), "LAISSEZ LE SAC", AMBRE)
    if t < s(38):
        suite(c, t, [(s(37), "ev_sac")], 290, 1400, 1.5)
        trace(c, t, s(37) + 0.5, 0.2, croix(290, 1130, 150), AMBRE, 2.8, bip=500)
        apres(c, t, s(37) + 0.3, "sac_tas", 790, 1110, 400, VERT_PALE, 0.6, 1500)
        trace(c, t, s(37) + 0.9, 0.2, croix(790, 1110, 150), AMBRE, 2.8, bip=500)
        return
    apres(c, t, s(38), "gr_file", W / 2, 700, 900, VERT_PALE, 0.7, 1300)
    ecrit(c, t, s(38), "DUBAÏ · 2016", W / 2, 1100, 56, AMBRE, True, 1.8)
    if t >= s(39):
        faisceau(c, [rect(140, 1200, 171, 40)], 1.0, VERT_PALE, 2.0)
        ecrit(c, t, s(39), "90 S : LA RÈGLE", 140, 1285, 34, VERT_PALE, False, 1.4)
        v = u(t, s(39) + 0.3, 1.2)
        faisceau(c, [rect(140, 1330, 800 * v, 40)], 1.0, AMBRE, 2.4)
        ecrit(c, t, s(39) + 1.2, "PRÈS DE 7 MIN", 140, 1415, 38, AMBRE, False, 1.8)
    if t >= s(40):
        ecrit(c, t, s(40), "CERTAINS AVEC LEURS BAGAGES", W / 2, 1500, 38, AMBRE, True, 1.6)


def e9(c, t):
    """5. La fumée : elle tue le plus, elle est chaude donc elle monte, restez bas."""
    titre(c, t, s(41), "5 · LA FUMÉE")
    if t < s(43):
        apres(c, t, s(41), "fe_fumee", W / 2, 900, 520, VERT_PALE, 0.8, 1300)
        return
    apres(c, t, s(43), "fe_plafond", W / 2, 740, 960, VERT_PALE, 0.8, 1300)
    ecrit(c, t, s(43) + 0.5, "1RE CAUSE DE MORT", W / 2, 1115, 48, AMBRE, True, 1.8)
    if t >= s(44):
        for k in range(5):
            x = 200 + 170 * k
            v = u(t, s(44) + 0.1 * k, 0.7)
            faisceau(c, fleche(x, 970, x, 970 - 150 * v, 22), 1.0, AMBRE, 2.2, 1.0)
        ecrit(c, t, s(44), "CHAUD  →  ÇA MONTE", W / 2, 1185, 46, AMBRE, True, 1.8)
    if t >= s(45):
        suite(c, t, [(s(45), "ev_rampe")], W / 2, 1565, 1.2)
        ecrit(c, t, s(45) + 0.2, "RESTEZ BAS", W / 2, 1265, 60, VERT_PALE, True, 1.8)


def e10(c, t):
    """Compter les rangées avec les mains jusqu'à la sortie ; la simulation de Galea : 5 rangées ou moins."""
    titre(c, t, s(46), "5 · LA FUMÉE")
    apres(c, t, s(46) - 0.2, "ex_panneau", W / 2, 480, 130, VERT_PALE, 0.5, 1700)
    apres(c, t, s(46), "cab_dessus", W / 2, 840, 440, VERT_PALE, 0.7, 1300)
    for k in range(3):
        if t >= s(46) + 0.4 + 0.4 * k:
            faisceau(c, [cercle_pts(540 - 148, 690 + 150 * k, 22, 16)], 1.0, AMBRE, 2.0)
            ecrit(c, t, s(46) + 0.4 + 0.4 * k, str(k + 1), 540 - 148, 700 + 150 * k, 30, AMBRE, True, 1.6, vitesse=0.0)
    if s(47) <= t < s(48):
        apres(c, t, s(47), "fe_main", W / 2, 1380, 440, VERT_PALE, 0.5, 1500)
    if t >= s(48):
        apres(c, t, s(48), "gr_rangs", W / 2, 1370, 620, VERT_PALE, 0.6, 1500)
        ecrit(c, t, s(48), "SIMULATION · ED GALEA", W / 2, 1195, 38, VERT_PALE, True, 1.6)
    if t >= s(49):
        ecrit(c, t, s(49), "≤ 5 RANGÉES", W / 2, 1560, 84, AMBRE, True, 2.4)


def e11(c, t):
    """6. L'eau : l'avion sur l'eau, le gilet, la cabine qui se remplit ; phrase coupée."""
    titre(c, t, s(50), "6 · L'EAU")
    apres(c, t, s(50), "av_eau", W / 2, 580, 940, VERT_PALE, 0.7, 1300)
    if t >= s(51):
        apres(c, t, s(51), "eau_gilet_vide", 280, 1120, 340, VERT_PALE, 0.6, 1500, t1=s(52) + 1.2)
        apres(c, t, s(52) + 1.2, "eau_gilet_gonfle", 280, 1120, 400, VERT_PALE, 0.5, 1500)
    if t >= s(52) + 0.4:
        trace(c, t, s(52) + 0.4, 0.4, fleche(420, 1120, 560, 1120, 24), AMBRE, 2.2, bip=1500)
        ecrit(c, t, s(52) + 0.5, "?", 780, 1340, 240, AMBRE, True, 2.6, vitesse=0.0)
    if t >= s(53):
        apres(c, t, s(53), "pe_plafond", 780, 960, 420, VERT_PALE, 0.7, 1300)
        ecrit(c, t, s(53), "LA PHYSIQUE, ENCORE", W / 2, 1480, 44, AMBRE, True, 1.8)


def e12(c, t):
    """Coupé au milieu de la phrase : la suite demain."""
    c.drawRect(skia.Rect(0, 0, W, M.H), P((40, 18, 4), 0, 255, fill=True))
    ecrit(c, t, -1, "LE GILET DE SAUVETAGE :", W / 2, 760, 56, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, -1, "LE GESTE À NE PAS FAIRE", W / 2, 840, 56, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, -1, "TROP TÔT", W / 2, 920, 56, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, -1, "LA SUITE DEMAIN ▶", W / 2 + 14 * abs(math.sin(t * 5)), 1110, 62, VERT_PALE, True, 2.0, vitesse=0.0)
    ecrit(c, t, -1, "INFORMATION GÉNÉRALE · SUIVEZ LES CONSIGNES DE L'ÉQUIPAGE", W / 2, 1450, 26, VERT, True, 1.2, vitesse=0.0)


def avec_lois(fn):
    def g(c, t):
        fn(c, t)
        tableau_lois(c, t)
    return g


def tableaux():
    return [(0.0, e1, None), (s(3) - 0.1, avec_lois(e2), None), (s(7), avec_lois(e4), None), (s(14), avec_lois(e5), None),
            (s(21), avec_lois(e6a), None), (s(26) - 0.05, avec_lois(e6b), "glitch"), (s(29) - 0.05, avec_lois(e6c), None),
            (s(31), avec_lois(e7), "balayage"), (s(32) + 3.0, avec_lois(e7b), None), (s(33), avec_lois(e8a), "noir"),
            (s(37), avec_lois(e8b), None), (s(41), avec_lois(e9), "balayage"), (s(46), avec_lois(e10), None),
            (s(50), avec_lois(e11), "glitch"), (e(56) + 0.05, e12, None)]


def chocs():
    tl = TL()
    flashs = [s(5) + 2.4, s(13), s(29), s(32) + 2.0, s(36)] + tl[1:] + [e(56) + 0.05]
    secousses = [(t, 0.2) for t in [s(5) + 2.4, s(13), s(29), s(32) + 2.0]] + [(e(56) + 0.05, 0.3)]
    return flashs, secousses


def effets(tabs):
    tl = TL()
    ev = [(0.0, Z.vibration(1.4, 0.1)), (0.0, Z.craquement(0.3)), (0.05, Z.boom(0.5, 60)),
          (0.0, Z.scintillement(2.8, 0.05)), (s(1), Z.thump(0.35)), (s(1), Z.tictac(1.6, 0.06, 0.3)),
          (s(2), Z.whoosh(0.6, 0.07)), (s(2), Z.alarme(0.04, 1)), (s(3), Z.cloche(784, 0.08)),
          (s(5), Z.chirp(300, 900, 2.4, 0.06)), (s(5) + 2.4, Z.boom(0.5, 70)), (s(5) + 2.4, Z.snap(0.35)),
          (s(6), Z.riser(0.7, 0.07))]
    ev += [(s(6) + 0.1 * i, Z.pince(523.3 * 2 ** (i * 2 / 12), 0.07)) for i in range(6)]
    ev += [(t, Z.cloche(880, 0.08)) for t in tl]
    ev += [(s(9), Z.whoosh(0.5, 0.08)), (s(10) + 1.7, Z.thump(0.3)), (s(11), Z.thump(0.4)), (s(13), Z.boom(0.5, 70)),
           (s(13), Z.snap(0.35))]
    ev += [(s(16), Z.pince(659.3, 0.08)), (s(17), Z.pince(784, 0.08)), (s(18), Z.pince(880, 0.08)),
           (s(19) + 0.5, Z.pince(587.3, 0.08)), (s(20), Z.chirp(900, 300, 0.6, 0.06))]
    ev += [(s(23), Z.thump(0.35)), (s(24) + 0.3, Z.chirp(300, 1100, 0.9, 0.06)), (s(24) + 1.0, Z.chirp(300, 700, 1.4, 0.05)),
           (s(27), Z.craquement(0.3)), (s(28) + 0.5, Z.cloche(698.5, 0.08)), (s(29), Z.boom(0.6, 60)),
           (s(30), Z.riser(0.8, 0.07))]
    ev += [(s(31), Z.whoosh(0.5, 0.08)), (s(32), Z.cloche(587.3, 0.08)), (s(32) + 1.2, Z.pince(988, 0.08)),
           (s(32) + 2.0, Z.thump(0.45)), (s(32) + 3.5, Z.whoosh(1.0, 0.1)), (s(32) + 4.6, Z.thump(0.4))]
    ev += [(s(34), Z.tictac(2.4, 0.06, 0.3)), (s(35), Z.cloche(880, 0.08)), (s(36), Z.vent(10.0, 0.04, 100, 500)),
           (s(36), Z.riser(2.0, 0.07)), (s(37) + 0.5, Z.thump(0.4)), (s(37) + 0.9, Z.thump(0.4)),
           (s(38), Z.cloche(587.3, 0.08)), (s(39) + 0.3, Z.chirp(300, 900, 1.2, 0.06)), (s(40), Z.alarme(0.04, 1))]
    ev += [(s(41), Z.vent(10.0, 0.04, 100, 500)), (s(43), Z.cloche(440, 0.08)), (s(44), Z.riser(1.0, 0.07)),
           (s(45), Z.thump(0.3)), (s(46), Z.cloche(784, 0.08))]
    ev += [(s(46) + 0.4 + 0.4 * k, Z.pince(659.3 * 2 ** (k * 2 / 12), 0.08)) for k in range(3)]
    ev += [(s(48), Z.cloche(698.5, 0.08)), (s(49), Z.boom(0.5, 70)), (s(49), Z.snap(0.35))]
    ev += [(s(50), Z.whoosh(0.5, 0.08)), (s(51), Z.pince(880, 0.08)), (s(52) + 1.2, Z.thump(0.35)),
           (s(52) + 0.5, Z.chirp(400, 800, 0.4, 0.07)), (s(53), Z.riser(e(54) - s(53), 0.08)),
           (e(56) + 0.05, Z.boom(0.6, 50)), (e(56) + 0.05, Z.arret_bande(0.5, 0.2))]
    sons = {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
            "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}
    ev += [(t0, sons[tr]()) for t0, _, tr in tabs[1:] if tr]
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep28.mp4")
