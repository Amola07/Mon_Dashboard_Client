"""Épisode 29 — « Le gilet de sauvetage : le geste qui peut vous noyer » (suite de l'épisode 28) — style oscilloscope animé.

Écrit directement en version animée : il reprend la mécanique de films/episodes/ep28_crash_avion/oscillo_ep28_pro.py
(caméras, rebonds, compteurs, accents calés au mot, enchaînements par transformation, 60 i/s) et n'écrit que ce qui
est propre à l'épisode : les écrans, les caméras, les accents, les enchaînements, les sons. Découpage : script.md.
Les instants viennent des mots (audio/mots.json) : chaque apparition est posée sur le mot qu'elle illustre.

    python -m films.episodes.ep29_gilet.oscillo_ep29 output/ep29.mp4
    python -m films.episodes.ep29_gilet.oscillo_ep29 output/ep29_extrait.mp4 30 50      (un extrait)
"""
import math
import os
import sys

import skia

from films.episodes.ep28_crash_avion import oscillo_ep28 as E
from films.episodes.ep28_crash_avion import oscillo_ep28_pro as P
from films.episodes.ep28_crash_avion.oscillo_ep28 import (AMBRE, VERT, VERT_PALE, W, Z, coche, croix, faisceau,
                                                         fleche, objet, tampon, trace)
from films.outils import mots_voix as MV
from films.outils.extrait import rendre_extrait
from films.styles import anim_pro as A
from films.styles.oscillo_ascenseur import P as peinture

M = P.M
H = M.H
HERE = os.path.dirname(os.path.abspath(__file__))
s, e = M.s, M.e
ecrit, titre, apres, suite = P.ecrit, P.titre, P.apres, P.suite


def w(mot, i):
    """Instant du mot (le premier qui commence par `mot` à partir de la phrase i)."""
    return MV.mot(mot, s(i))


def grand(c, t, t0, txt, x, y, taille, col=AMBRE, t1=None, halo=2.4):
    """Un texte en grand, sans compteur automatique (il est déjà calculé), avec rebond d'arrivée."""
    if t < t0 or (t1 is not None and t >= t1):
        return
    k = A.pop(t, t0, 0.3)
    c.save()
    c.translate(x, y - taille * 0.35)
    c.scale(k, k)
    c.translate(-x, -(y - taille * 0.35))
    P._ecrit(c, t, t0, txt, x, y, taille, col, True, halo, vitesse=0.0)
    c.restore()


def compte(t, t0, d, de, a):
    """Valeur d'un compteur qui va de `de` à `a` en d secondes à partir de t0."""
    return round(de + (a - de) * A.sortie((t - t0) / d, 2.5)) if t >= t0 else de


def vague(x0, x1, y, t, amp=7, lg=90, vit=2.0):
    n = int((x1 - x0) / 12) + 1
    return [[(x0 + i * 12, y + amp * math.sin((x0 + i * 12) / lg * 2 * math.pi + vit * t)) for i in range(n)]]


def chaleur(c, t, cx, cy, n, r0=90, r1=230, col=AMBRE, intense=1.0, haut=None):
    """Des flèches ondulées qui quittent le corps : la chaleur perdue (n flèches, qui partent sans cesse)."""
    for i in range(n):
        a = -math.pi / 2 + 2 * math.pi * (i + 0.5) / n
        ph = (t * 0.9 + i * 0.37) % 1.0
        r = r0 + (r1 - r0) * ph
        L = 46
        pts = []
        for j in range(7):
            rr = r + L * j / 6
            ondule = 6 * math.sin(j * 1.6 + 6 * t)
            pts.append((cx + rr * math.cos(a) - ondule * math.sin(a), cy + rr * math.sin(a) + ondule * math.cos(a)))
        if haut is not None and pts[-1][1] < haut:
            continue
        tete = fleche(pts[-2][0], pts[-2][1], pts[-1][0], pts[-1][1], 12)[1]
        faisceau(c, [pts, tete], 1.0, col, 1.8, intense * math.sin(math.pi * ph))


def tableau_lois(c, t):
    """Les 3 lois de l'épisode, en haut : elles s'allument au fil de la vidéo ; celle du moment est en ambre."""
    t0 = s(5)
    if t < t0:
        return
    lois = ["ARCHIMÈDE", "LE FROID", "LA SURFACE"]
    tl = [w("archimède", 6), w("froid", 35), w("surface", 47)]
    cour = max([i for i in range(3) if tl[i] <= t] + [-1])
    for i, nom in enumerate(lois):
        x0 = 60 + 330 * i
        box = [E.rect(x0, 120, 300, 84)]
        v = A.lisse((t - t0 - 0.1 * i) / 0.3)
        if t >= tl[i]:
            col = AMBRE if i == cour else VERT_PALE
            faisceau(c, box, 1.0, col, 2.0 if tl[i] <= t < tl[i] + 0.2 else 1.5, 1.0)
            P._ecrit(c, t, tl[i], nom, x0 + 150, 174, 34, col, True, 1.4, vitesse=0.0)
        elif v > 0:
            faisceau(c, box, v, VERT, 0.8, 0.4)
            P._ecrit(c, t, t0, str(i + 1), x0 + 150, 178, 46, VERT, True, 1.0, vitesse=0.0)


# ------------------------------------------------------------------------------------------------ 1. l'accroche
def e1(c, t):
    """L'avion sur l'eau, le passager et son gilet ; « le gonfler tout de suite » : non."""
    ecrit(c, t, -1, "LE GESTE", W / 2, 440, 88, AMBRE, True, 2.4, vitesse=0.0)
    ecrit(c, t, -1, "QUI PEUT NOYER", W / 2, 535, 88, AMBRE, True, 2.4, vitesse=0.0)
    apres(c, t, -1, "av_eau", W / 2, 720, 640, VERT_PALE, 0.01)
    tg = w("gonfler", 3)
    suite(c, t, [(-1.0, "pe_gilet"), (tg, "pe_tire_cordon")], 470, 1580, 1.6)
    if t >= tg:
        apres(c, t, tg, "eau_gilet_gonfle", 850, 1180, 270, VERT_PALE, 0.4)
        trace(c, t, w("suite", 3), 0.2, croix(850, 1180, 120), AMBRE, 3.0, bip=500)
    tampon(c, t, w("suite", 3) + 0.15, ["PAS TOUT DE SUITE"], 540, 960, -6, 56, AMBRE)


# ------------------------------------------------------------------------------------------------ 2. Archimède
CUVE = (240, 760, 840, 1400)
NIVEAU0, COTE = 1060, 200


def cube_descente(t):
    """(y du haut du cube, fraction immergée)."""
    t0 = w("tout", 8)
    u = A.lisse((t - t0) / 1.6)
    y = 640 + 8 * math.sin(2.2 * t) * (1 - u) + (NIVEAU0 + 70 - 640) * u
    niveau = NIVEAU0 - 67 * immerge(y)
    return y, immerge(y), niveau


def immerge(y):
    return A.borne((y + COTE - NIVEAU0) / COTE)


def cube_traits(t):
    y, _, _ = cube_descente(t)
    x = (CUVE[0] + CUVE[2]) / 2 - COTE / 2
    return [E.rect(x, y, COTE, COTE), [(x + 30, y + 30), (x + COTE - 30, y + 30)]]


def e2a(c, t):
    """Une cuve d'eau ; un cube y descend ; l'eau monte ; la poussée vers le haut grandit."""
    titre(c, t, s(5), "1 · ARCHIMÈDE")
    ecrit(c, t, w("archimède", 6), "ARCHIMÈDE", W / 2, 540, 92, AMBRE, True, 2.4, vitesse=0.0)
    x0, y0, x1, y1 = CUVE
    faisceau(c, [[(x0, y0), (x0, y1), (x1, y1), (x1, y0)]], 1.0, VERT_PALE, 1.6)
    y, f, niveau = cube_descente(t)
    for k in range(4):                                                    # l'eau
        faisceau(c, vague(x0 + 8, x1 - 8, niveau + 70 * k, t + k, 6 if k == 0 else 4), 1.0, VERT, 1.3,
                 1.0 if k == 0 else 0.5)
    tp = w("poids", 8)
    if t >= tp:                                                           # l'eau déplacée
        v = A.lisse((t - tp) / 0.4)
        for k in range(6):
            yy = NIVEAU0 - 4 - k * 11
            if yy > niveau:
                faisceau(c, [[(x0 + 10, yy), (x0 + 10 + (x1 - x0 - 20) * v, yy)]], 1.0, AMBRE, 1.4, 0.8)
        grand(c, t, tp + 0.2, "L'EAU DÉPLACÉE", W / 2, 1490, 46, AMBRE)
    faisceau(c, A.vivant(cube_traits(t), t, 0.6), 1.0, VERT_PALE, 1.8)
    if f > 0:                                                             # la poussée
        cx, cy = (x0 + x1) / 2, y + COTE / 2
        faisceau(c, fleche(cx, cy + 60, cx, cy + 60 - 260 * f, 30), 1.0, AMBRE, 3.0)
        grand(c, t, w("haut", 8), "POUSSÉE", cx + 190, cy - 120, 44, AMBRE)


def e2b(c, t):
    """Un gilet gonflé : environ 16 litres d'air, donc environ 16 kilos vers le haut."""
    titre(c, t, s(5), "1 · ARCHIMÈDE")
    apres(c, t, s(9) - 0.3, "eau_gilet_gonfle", 330, 1040, 360, VERT_PALE, 0.3)
    tl = w("seize", 9)
    apres(c, t, w("litres", 9) - 0.3, "fr_bouteille", 780, 1000, 150, VERT_PALE if t < s(10) else VERT, 0.5)
    if t >= tl:
        grand(c, t, tl, f"{compte(t, tl, 0.8, 0, 16)} L", 780, 1400, 84, VERT_PALE)
    tk = w("seize", 10)
    if t >= tk:
        v = A.rebond((t - tk) / 0.5)
        faisceau(c, fleche(330, 800, 330, 800 - 260 * v, 34), 1.0, AMBRE, 3.2)
        grand(c, t, tk, f"{compte(t, tk, 0.8, 0, 16)} KG", 330, 470, 96, AMBRE)
        grand(c, t, w("haut", 10), "VERS LE HAUT", 330, 1340, 44, AMBRE)


def e2c(c, t):
    """Dehors : la tête reste hors de l'eau, sans effort."""
    titre(c, t, s(5), "1 · ARCHIMÈDE")
    apres(c, t, s(11) - 0.3, "fr_flotte", W / 2, 1050, 640, VERT_PALE, 0.3)
    v = A.lisse((t - s(11)) / 0.5)
    faisceau(c, fleche(560, 1250, 560, 1250 - 150 * v, 26), 1.0, AMBRE, 2.6, 0.8)
    grand(c, t, w("dehors", 11), "DEHORS : PARFAIT", W / 2, 520, 64, VERT_PALE)
    te = w("effort", 12)
    if t >= te:
        trace(c, t, te, 0.25, coche(300, 1460, 34), VERT_PALE, 3.0, bip=1600)
        grand(c, t, te, "SANS EFFORT", 590, 1480, 56, VERT_PALE)


# ------------------------------------------------------------------------------------------------ 3. la cabine
CAB = (70, 560, 1010, 1060)                                               # l'intérieur de la cabine (à peu près)


def niveau_cabine(t):
    t0 = w("monte", 14)
    u1 = A.lisse((t - t0) / 1.6)
    u2 = A.lisse((t - s(17)) / 2.0)
    return 1040 - (1040 - 720) * u1 - (720 - 640) * u2


def passager_cabine(t):
    """Le passager au gilet gonflé suit l'eau, jusqu'au plafond."""
    y = max(615, niveau_cabine(t) - 26)
    return objet("pe_plafond", 430, y + A.doux(1.5 * t) * 3, 400)


def e3(c, t):
    """L'eau monte dans la cabine ; la porte passe sous l'eau ; il faudrait plonger ; le gilet le plaque au plafond."""
    titre(c, t, s(5), "1 · ARCHIMÈDE")
    apres(c, t, s(13) - 0.3, "eau_cabine_pleine", W / 2, 810, 960, VERT_PALE, 0.4)
    niv = niveau_cabine(t)
    c.save()
    c.clipRect(skia.Rect(CAB[0] + 20, CAB[1], CAB[2] - 30, CAB[3]))
    for k in range(6):
        faisceau(c, vague(CAB[0], CAB[2], niv + 60 * k, t + k, 6 if k == 0 else 4), 1.0, VERT, 1.4,
                 1.0 if k == 0 else 0.45)
    c.restore()
    faisceau(c, A.vivant(passager_cabine(t), t, 0.6), 1.0, VERT_PALE, 1.3)
    porte = (880, 760, 960, 1010)
    ts = w("sorties", 15)
    if t >= ts:
        k = A.pop(t, ts, 0.3)
        faisceau(c, [A.echelle([E.rect(porte[0], porte[1], porte[2] - porte[0], porte[3] - porte[1])], k, 920, 885)[0]],
                 1.0, AMBRE, 2.6)
        grand(c, t, w("sous", 16), "LA SORTIE : SOUS L'EAU", W / 2, 1250, 56, AMBRE, t1=s(17))
    tp = w("plonger", 18)
    if t >= s(17):
        v = A.lisse((t - s(17)) / 0.9)
        chemin = [(470, 690), (560, 900), (720, 960), (880, 900)]
        pts = [chemin[0]]
        for a, b in zip(chemin, chemin[1:]):
            pts += [(a[0] + (b[0] - a[0]) * j / 8, a[1] + (b[1] - a[1]) * j / 8) for j in range(1, 9)]
        n = max(2, int(len(pts) * v))
        faisceau(c, [[pts[i], pts[i + 1]] for i in range(0, n - 1, 2)], 1.0, VERT_PALE, 2.0)
        grand(c, t, tp, "IL FAUT PLONGER", W / 2, 1250, 56, VERT_PALE, t1=w("arrivez", 20))
    tk = w("seize", 19)
    if t >= tk:
        v = A.rebond((t - tk) / 0.4)
        for dx in (-120, 0, 120):
            faisceau(c, fleche(430 + dx, 700, 430 + dx, 700 - 90 * v, 18), 1.0, AMBRE, 2.4)
        grand(c, t, tk, "16 KG", 430, 470, 84, AMBRE)
    ta = w("arrivez", 20)
    if t >= ta:
        trace(c, t, ta, 0.2, croix(700, 940, 80), AMBRE, 3.4, bip=500)
        grand(c, t, ta, "IMPOSSIBLE", W / 2, 1260, 92, AMBRE)


# ------------------------------------------------------------------------------------------------ 4. Comores, 1996
def e4(c, t):
    """L'avion détourné pique vers l'océan, près d'une île ; dans la cabine, les gilets gonflés montent au plafond."""
    titre(c, t, s(21), "COMORES · 1996", AMBRE)
    apres(c, t, s(21) - 0.3, "av_descente", 470, 600, 700, VERT_PALE, 0.4)
    faisceau(c, vague(60, 1020, 860, t, 5, 120), 1.0, VERT, 1.4)
    ile = [(760, 862), (800, 830), (860, 812), (920, 820), (980, 850), (1010, 862)]
    faisceau(c, [ile], 1.0, VERT_PALE, 1.6)
    grand(c, t, w("détourné", 21), "AVION DÉTOURNÉ", W / 2, 960, 50, VERT_PALE)
    tv = w("passagers", 23)
    if t < s(22):
        return
    x0, y0, x1, y1 = 120, 1080, 960, 1470                                 # la cabine en coupe
    faisceau(c, [E.rect(x0, y0, x1 - x0, y1 - y0)], A.lisse((t - s(22)) / 0.4), VERT_PALE, 1.6)
    tg = w("gonflé", 24)
    niv = y1 - 20 - 260 * A.lisse((t - tg) / 2.0)
    c.save()
    c.clipRect(skia.Rect(x0 + 2, y0, x1 - 2, y1))
    faisceau(c, vague(x0, x1, niv, t, 5, 70), 1.0, VERT, 1.3)
    c.restore()
    for i in range(3):
        for j in range(8):
            x = x0 + 70 + j * 104
            yb = y0 + 110 + i * 110
            d = 0.12 * (j + 3 * i)
            u = A.lisse((t - tg - d) / 0.9)
            y = yb + (y0 + 26 - yb) * u
            if t < tv + 0.05 * (j + 8 * i):
                continue
            faisceau(c, P.mini_perso(x, y, 11), 1.0, VERT_PALE, 1.4)
            if t >= tg + d:
                faisceau(c, [E.cercle_pts(x, y + 22, 15, 14)], 1.0, AMBRE, 1.8)
    grand(c, t, tv, "SURVIVANTS DU CHOC", W / 2, 1050, 40, VERT_PALE, t1=tg)
    grand(c, t, tg, "GILETS GONFLÉS DANS LA CABINE", W / 2, 1550, 42, AMBRE)


# ------------------------------------------------------------------------------------------------ 5. le bon geste
def e5a(c, t):
    """Gilet enfilé, sangles serrées, mais pas gonflé."""
    titre(c, t, s(25), "LE BON GESTE", AMBRE)
    suite(c, t, [(s(25) - 0.3, "pe_gilet")], 300, 1560, 1.6)
    lignes = [("ENFILÉ", w("enfilé", 26), True), ("SERRÉ", w("serrées", 27), True), ("GONFLÉ", w("gonflé", 29), False)]
    for k, (txt, t0, oui) in enumerate(lignes):
        y = 820 + 190 * k
        grand(c, t, t0, txt, 700, y, 70, VERT_PALE if oui else AMBRE)
        if t >= t0:
            trace(c, t, t0 + 0.1, 0.2, coche(960, y - 26, 36) if oui else croix(960, y - 26, 36),
                  VERT_PALE if oui else AMBRE, 3.2, bip=1600 if oui else 500)


def e5b(c, t):
    """À la porte, une fois dehors : on tire la languette ; une cartouche de gaz le gonfle en quelques secondes."""
    titre(c, t, s(25), "LE BON GESTE", AMBRE)
    tg = w("remplit", 32)
    suite(c, t, [(s(30) - 0.3, "fr_tire"), (tg, "fr_gonfle")], W / 2, 1510, 1.6)
    grand(c, t, w("porte", 30), "À LA PORTE", W / 2, 520, 64, VERT_PALE, t1=w("une", 31))
    grand(c, t, w("dehors", 31), "UNE FOIS DEHORS", W / 2, 520, 64, AMBRE)
    tc = w("cartouche", 32)
    if t >= tc:
        apres(c, t, tc, "fr_cartouche", 880, 720, 230, AMBRE, 0.3)
        grand(c, t, tc + 0.2, "CO2", 880, 860, 44, AMBRE)
    if tg <= t < tg + 0.6:                                                # le gaz qui gonfle
        f = (t - tg) / 0.6
        for i in range(10):
            a = 2 * math.pi * i / 10
            r0, r1 = 120 + 80 * f, 160 + 140 * f
            faisceau(c, [[(560 + r0 * math.cos(a), 1050 + r0 * math.sin(a)),
                          (560 + r1 * math.cos(a), 1050 + r1 * math.sin(a))]], 1.0, VERT_PALE, 2.0, 1 - f)
    grand(c, t, w("secondes", 33), "QUELQUES SECONDES", W / 2, 1580, 44, VERT_PALE)


# ------------------------------------------------------------------------------------------------ 6. le froid
def e6a(c, t):
    """L'eau vole la chaleur environ 25 fois plus vite que l'air."""
    titre(c, t, s(34), "2 · LE FROID")
    grand(c, t, w("froid", 35), "DEUXIÈME ENNEMI", W / 2, 520, 60, AMBRE, t1=w("vingt", 36))
    apres(c, t, s(34) - 0.3, "fr_flotte", W / 2, 1060, 640, VERT_PALE, 0.3)
    tv = w("vole", 36)
    if t >= tv:
        n = 4 + int(14 * A.lisse((t - tv) / 1.2))
        chaleur(c, t, 560, 1150, n, 170, 330, AMBRE, 1.0)
        chaleur(c, t, 560, 860, 2, 110, 200, VERT_PALE, 0.7)                # dans l'air : presque rien
        grand(c, t, tv, "AIR", 220, 760, 44, VERT_PALE)
        grand(c, t, tv, "EAU", 220, 1420, 44, AMBRE)
    tx = w("vingt", 36)
    if t >= tx:
        grand(c, t, tx, f"× {compte(t, tx, 0.7, 1, 25)}", W / 2, 540, 120, AMBRE)


def e6b(c, t):
    """L'Hudson, 2009 : l'eau à 2 °C, les secours en quelques minutes, 155 survivants sur 155."""
    titre(c, t, s(34), "2 · LE FROID")
    apres(c, t, s(37) - 0.3, "fr_hudson", W / 2, 860, 820, VERT_PALE, 0.4)
    grand(c, t, w("l'hudson", 37), "HUDSON · 2009", W / 2, 1290, 56, VERT_PALE, t1=s(38))
    td = w("deux", 37) + 0.25
    if t >= td:
        apres(c, t, td - 0.1, "fr_thermometre", 860, 1440, 230, AMBRE, 0.3)
        grand(c, t, td, f"{compte(t, td, 0.8, 15, 2)} °C", 450, 1460, 110, AMBRE, t1=s(39))
    grand(c, t, w("minutes", 38) - 0.3, "SECOURS : QUELQUES MINUTES", W / 2, 1290, 44, VERT_PALE)
    tc = w("cent", 39)
    if t >= tc:
        n = compte(t, tc, 1.2, 0, 155)
        grand(c, t, tc, f"{n} / 155", 450, 1460, 100, AMBRE)
        grand(c, t, w("survécu", 39), "SURVIVANTS", 450, 1550, 40, VERT_PALE)


# ------------------------------------------------------------------------------------------------ 7. la posture
def e7(c, t):
    """On ne nage pas ; on se met en boule ; on se colle aux autres : moins de surface, moins de chaleur perdue."""
    tsurf = w("surface", 47)
    titre(c, t, s(34), "2 · LE FROID")
    if t >= tsurf:
        titre(c, t, tsurf, "3 · LA SURFACE")
    tb, tg = w("remonte", 44), w("colle", 46)
    suite(c, t, [(s(40) - 0.3, "fr_nage"), (tb, "fr_boule"), (tg, "fr_groupe")], W / 2, 1300, 1.5)
    cx, cy = 540, 1060
    if t < tb:
        n = 10 + int(10 * A.lisse((t - w("bouger", 42)) / 0.8))
    elif t < tg:
        n = 8
    else:
        n = 4 + int(2 * (1 - A.lisse((t - tg) / 1.0)))
    chaleur(c, t, cx, cy, n, 260, 400, AMBRE, 0.9)
    tn = w("nage", 41)
    if tn <= t < tb:
        trace(c, t, tn, 0.2, croix(900, 820, 60), AMBRE, 3.2, bip=500)
        grand(c, t, tn, "ON NE NAGE PAS", W / 2, 520, 64, AMBRE, t1=tb)
    grand(c, t, tb, "EN BOULE", W / 2, 520, 64, VERT_PALE, t1=tg)
    grand(c, t, tg, "SERRÉS", W / 2, 520, 64, VERT_PALE, t1=tsurf)
    grand(c, t, tsurf, "MOINS DE SURFACE", W / 2, 1460, 60, AMBRE)
    grand(c, t, w("chaleur", 48), "MOINS DE CHALEUR PERDUE", W / 2, 1550, 42, VERT_PALE)


# ------------------------------------------------------------------------------------------------ 8. le teaser
def e8(c, t):
    """Le toboggan ; une chose à enlever (un talon) ; la physique, encore."""
    titre(c, t, s(49), "ET LE TOBOGGAN ?", AMBRE)
    apres(c, t, s(49) - 0.3, "ex_toboggan", 420, 960, 560, VERT_PALE, 0.4)
    te = w("enlever", 51)
    if t >= te:
        apres(c, t, te, "fr_talon", 800, 1330, 300, AMBRE, 0.4)
        grand(c, t, te + 0.2, "?", 860, 1120, 220, AMBRE)


def e9(c, t):
    """Coupé au milieu de la phrase : la suite demain."""
    c.drawRect(skia.Rect(0, 0, W, H), peinture((40, 18, 4), 0, 255, fill=True))
    for k, l in enumerate(["AVANT LE TOBOGGAN :", "LA CHOSE", "À ENLEVER"]):
        P._ecrit(c, t, -1, l, W / 2, 760 + 80 * k, 56, AMBRE, True, 2.2, vitesse=0.0)
    P._ecrit(c, t, -1, "LA SUITE DEMAIN ▶", W / 2 + 14 * abs(math.sin(t * 5)), 1110, 62, VERT_PALE, True, 2.0,
             vitesse=0.0)
    P._ecrit(c, t, -1, "INFORMATION GÉNÉRALE · SUIVEZ LES CONSIGNES DE L'ÉQUIPAGE", W / 2, 1450, 26, VERT, True, 1.2,
             vitesse=0.0)


# ------------------------------------------------------------------------------------------------ mouvements propres
_mouvement = P.mouvement


def mouvement(nom, tr, t, t0, cx, cy, larg):
    dt = t - t0
    if nom in ("fr_flotte", "pe_flotte"):                                # on flotte : la houle
        return A.deplace(A.tourne(tr, 1.5 * math.sin(1.6 * t), cx, cy), 0, 8 * math.sin(1.6 * t + 0.8))
    if nom == "fr_hudson":
        return A.deplace(A.tourne(tr, 0.8 * math.sin(1.2 * t), cx, cy), 0, 5 * math.sin(1.2 * t + 1))
    if nom == "fr_thermometre":
        return A.deplace(tr, 0, 3 * math.sin(3 * t))
    if nom == "fr_cartouche":
        return A.tourne(tr, 4 * math.sin(5 * t) * math.exp(-1.5 * dt), cx, cy)
    if nom == "fr_bouteille":
        return A.vivant(tr, t, 1.0, 14, 9)                               # les bulles qui bougent
    if nom == "ex_toboggan":
        return A.deplace(tr, 0, 3 * math.sin(2 * t))
    if nom == "fr_talon":
        return A.tourne(tr, 6 * math.sin(2.5 * t), cx, cy)
    return _mouvement(nom, tr, t, t0, cx, cy, larg)


# ------------------------------------------------------------------------------------------------ montage
def debuts():
    return [0.0, s(5), s(9), s(11), s(13), s(21), s(25), s(30), s(34), s(37), s(40), s(49), e(57) + 0.05]


ECRANS = [e1, e2a, e2b, e2c, e3, e4, e5a, e5b, e6a, e6b, e7, e8, e9]


def cameras():
    T = debuts()
    tp = w("plafond", 19)
    return {
        T[0]: A.Camera([(0.0, 1.06, 540, 980), (s(3), 1.0, 540, 960), (s(5), 1.04, 540, 940)]),
        T[4]: A.Camera([(s(13), 1.0, 540, 900), (s(15), 1.04, 620, 880), (s(17), 1.06, 640, 860),
                        (tp, 1.14, 500, 760, 0.4), (s(21), 1.12, 520, 800)]),
        T[5]: A.Camera([(s(21), 1.0, 540, 900), (s(22), 1.04, 540, 860), (s(23), 1.0, 540, 1000, 0.5),
                        (s(25), 1.06, 540, 1180)]),
        T[9]: A.Camera([(s(37), 1.0, 540, 900), (s(39), 1.04, 540, 1000), (s(40), 1.08, 540, 1150)]),
    }


def heros():
    """Les enchaînements : (dessin qui part, dessin qui arrive, début, fin) ou ("plongee", P, Q)."""
    T = debuts()
    ob, po = objet, E.pose
    return {
        T[1]: ("plongee", (540, 820), (540, 1060)),
        T[2]: (lambda t: cube_traits(t), lambda t: ob("eau_gilet_gonfle", 330, 1040, 360), T[2] - 0.3, T[2] + 0.4),
        T[3]: (lambda t: ob("eau_gilet_gonfle", 330, 1040, 360), lambda t: ob("fr_flotte", W / 2, 1050, 640),
               T[3] - 0.3, T[3] + 0.4),
        T[4]: (lambda t: ob("fr_flotte", W / 2, 1050, 640), lambda t: passager_cabine(T[4] + 0.4), T[4] - 0.3, T[4] + 0.4),
        T[5]: (lambda t: ob("eau_cabine_pleine", W / 2, 810, 960), lambda t: ob("av_descente", 470, 600, 700),
               T[5] - 0.3, T[5] + 0.4),
        T[6]: ("plongee", (540, 1300), (300, 1250)),
        T[7]: (lambda t: po("pe_gilet", 300, 1560, 1.6), lambda t: po("fr_tire", W / 2, 1510, 1.6), T[7] - 0.3, T[7] + 0.4),
        T[8]: (lambda t: po("fr_gonfle", W / 2, 1510, 1.6), lambda t: ob("fr_flotte", W / 2, 1060, 640),
               T[8] - 0.3, T[8] + 0.4),
        T[9]: ("plongee", (540, 1200), (540, 860)),
        T[10]: (lambda t: ob("fr_hudson", W / 2, 860, 820), lambda t: po("fr_nage", W / 2, 1300, 1.5),
                T[10] - 0.3, T[10] + 0.4),
        T[11]: (lambda t: po("fr_groupe", W / 2, 1300, 1.5), lambda t: ob("ex_toboggan", 420, 960, 560),
                T[11] - 0.3, T[11] + 0.4),
    }


def accents():
    return [(w("noyer", 2), "arret"), (w("archimède", 6), "pop"), (w("haut", 8), "pop"), (w("seize", 9), "choc"),
            (w("seize", 10), "pop"), (w("sorties", 15), "pop"), (w("plafond", 19), "choc"), (w("arrivez", 20), "choc"),
            (w("comores", 21), "pop"), (w("gonflé", 24), "arret"), (w("enfilé", 26), "pop"), (w("serrées", 27), "pop"),
            (w("gonflé", 29), "choc"), (w("dehors", 31), "pop"), (w("remplit", 32), "choc"), (w("froid", 35), "arret"),
            (w("vingt", 36), "choc"), (w("deux", 37), "arret"), (w("cent", 39), "choc"), (w("nage", 41), "choc"),
            (w("remonte", 44), "pop"), (w("colle", 46), "pop"), (w("surface", 47), "pop"), (w("enlever", 51), "arret"),
            (w("physique", 54), "pop")]


def tableaux():
    T = debuts()
    P.preparer_calage(T)                                                  # charge aussi l'instant des mots
    cams = cameras()
    P.CAMS.clear()
    out = []
    for i, (t0, fn) in enumerate(zip(T, ECRANS)):
        fin = T[i + 1] if i + 1 < len(T) else t0 + 5
        cam = None if fn is e9 else cams.get(t0) or A.Camera([(t0, 1.0, 540, 960), (fin, 1.05, 540, 940)])
        g = P.avec_camera(fn, cam, lois=tableau_lois if fn not in (e1, e9) else False,
                          haut=215 if fn is e1 else P.HAUT)                # e1 n'a pas de titre
        out.append((t0, g, None))
        P.CAMS.append(cam)
    return P.enchainements(out)


def chocs():
    return [tw for tw, genre in P.ACC if genre == "choc"], []


def effets(tabs):
    ev = [(0.0, Z.vent(3.0, 0.05, 100, 600)), (0.0, Z.bulles(1.5, 0.08)), (w("suite", 3) + 0.15, Z.boom(0.5, 70)),
          (w("tout", 8), Z.bulles(1.6, 0.1)), (w("seize", 9), Z.bulles(1.0, 0.08)), (w("monte", 14), Z.bulles(2.0, 0.1)),
          (w("monte", 14), Z.vent(3.0, 0.04, 80, 400)), (w("plonger", 18), Z.whoosh(0.6, 0.07)),
          (w("détourné", 21), Z.whoosh(1.0, 0.08)), (w("gonflé", 24), Z.bulles(2.0, 0.1)),
          (w("remplit", 32), Z.souffle(0.6, 0.15, False)), (w("cartouche", 32), Z.snap(0.3)),
          (w("vole", 36), Z.vent(3.0, 0.05, 150, 900)), (w("cent", 39), Z.chirp(300, 900, 1.2, 0.06)),
          (w("enlever", 51), Z.cloche(880, 0.08)), (e(57) + 0.05, Z.boom(0.6, 50)), (e(57) + 0.05, Z.arret_bande(0.5, 0.2))]
    ev += [(t0, Z.cloche(880, 0.08)) for t0 in [w("archimède", 6), w("froid", 35), w("surface", 47)]]
    ev += [(d, Z.whoosh(0.6, 0.08)) for d, f in P.TRANSFOS]
    ev += [(tw, Z.thump(0.3)) for tw, genre in P.ACC if genre == "choc"]
    ev += [(tw, Z.boom(0.45, 70)) for tw, genre in P.ACC if genre == "arret"]
    return ev


def installer():
    P.installer()                                                         # outils animés, 60 i/s
    M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
    M.SEGS = os.path.join(HERE, "audio", "voix.json")
    P.accents, P.recalages, P.heros, P.mouvement = accents, (lambda: []), heros, mouvement
    P.FIXES[:] = [e9]
    P.COMPTEURS.clear()
    M.tableaux, M.chocs, M.effets = tableaux, chocs, effets


if __name__ == "__main__":
    installer()
    sortie = sys.argv[1] if len(sys.argv) > 1 else "output/ep29.mp4"
    if len(sys.argv) > 3:
        rendre_extrait(M, float(sys.argv[2]), float(sys.argv[3]), sortie)
    else:
        M.render(sortie)
