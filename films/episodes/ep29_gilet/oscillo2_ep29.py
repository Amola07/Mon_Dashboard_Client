"""Épisode 29 — « Le gilet de sauvetage » — en « oscilloscope 2.0 », complet (≈ 1 min 25).

Style : films/styles/oscillo2.py (quadrillage, hachures de faisceau, texte au faisceau, chiffres en segments, image
nette et calme). Les quatre écrans d'Archimède viennent du test oscillo2_archimede.py ; les dessins viennent des
icônes générées (px_* pour le personnage et les petits objets, vx_* pour les objets isolés), converties en vecteurs.
Même voix et mêmes instants (calés au mot). Entre deux écrans, un dessin se transforme en un autre.

    python -m films.episodes.ep29_gilet.oscillo2_ep29 output/ep29_osc2_complet.mp4
    python -m films.episodes.ep29_gilet.oscillo2_ep29 output/extrait.mp4 40 60      (un extrait)
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import montage_ia as MI
from films.episodes.ep29_gilet import oscillo2_archimede as Q
from films.styles import anim_pro as A
from films.styles import oscillo2 as O
from films.styles import oscillo_son as Z
from films.styles.oscillo2 import AMBRE, VERT, VERT_PALE, VERT_SOMBRE, W, H

M, MV = Q.M, Q.MV
FPS = 30
s, e, w = M.s, M.e, Q.w
phrase, eau, fleche_haut, rect = Q.phrase, Q.eau, Q.fleche_haut, Q.rect


def icone(c, nom, cx, bas, h, a=1.0, u=1.0, hach=("ambre",)):
    return O.dessiner_icone_sobre(c, nom, cx, bas, h, a, u, hach)


def pose(c, t, tab, cx, bas, h, a=1.0, d=0.35, hach=("ambre",)):
    """Un personnage qui change de pose : sa silhouette se transforme, les deux poses se fondent."""
    cour = [(t0, n) for t0, n in tab if t >= t0]
    if not cour:
        return
    t0, nom = cour[-1]
    k = (t - t0) / d
    if len(cour) > 1 and k < 1:
        av = cour[-2][1]
        c.saveLayerAlpha(None, int(255 * (1 - A.lisse(k)) * a))
        icone(c, av, cx, bas, h, 1.0, 1.0, hach)
        c.restore()
        c.saveLayerAlpha(None, int(255 * A.lisse(k) * a))
        icone(c, nom, cx, bas, h, 1.0, 1.0, hach)
        c.restore()
        for tr, it in A.flux(("pose", av, nom, cx, bas, h), O.silhouette(av, cx, bas, h), O.silhouette(nom, cx, bas, h), k):
            O.dessiner(c, tr, VERT_PALE, 2.8, it * a)
        return
    icone(c, nom, cx, bas, h, a, (t - t0) / 0.6 if len(cour) == 1 and t0 > 0 else 1.0, hach)


def tampon(c, t, t0, txt, cx, cy, ang=-7, h=46):
    if t < t0:
        return
    k = 1 + 1.2 * max(0.0, 1 - (t - t0) / 0.12)
    lg = O.largeur_texte(txt, h) + 60
    c.save()
    c.translate(cx, cy)
    c.rotate(ang)
    c.scale(k, k)
    O.dessiner(c, [rect(-lg / 2, -h, lg / 2, h * 0.7)], AMBRE, 3.4)
    O.dessiner(c, O.texte(txt, 0, h * 0.35, h, gras=True), AMBRE, 2.8)
    c.restore()


def croix(cx, cy, r=40):
    return [[(cx - r, cy - r), (cx + r, cy + r)], [(cx + r, cy - r), (cx - r, cy + r)]]


def coche(cx, cy, r=36):
    return [[(cx - r, cy), (cx - r * 0.3, cy + r * 0.7), (cx + r, cy - r * 0.8)]]


def chaleur(c, t, cx, cy, n, r0, r1, a=1.0):
    """De petites flèches ondulées qui quittent le corps : la chaleur perdue."""
    tr = []
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * (i + 0.5) / n
        ph = (t * 0.8 + i * 0.37) % 1.0
        if ph > 0.85:
            continue
        r = r0 + (r1 - r0) * ph
        pts = []
        for j in range(8):
            rr = r + j * 7
            o = 7 * math.sin(j * 1.4 + 7 * t)
            pts.append((cx + rr * math.cos(ang) - o * math.sin(ang), cy + rr * math.sin(ang) + o * math.cos(ang)))
        tr.append(pts)
    O.dessiner(c, tr, AMBRE, 2.4, 0.85 * a)


# ------------------------------------------------------------------------------------------------ 1. l'accroche
def e1(c, t, a=1.0):
    phrase(c, t, -1.0, ["Votre avion s'est", "posé sur *l'eau*"], t1=s(2))
    phrase(c, t, s(2), ["Un geste peut", "vous *noyer*"], t1=s(3))
    phrase(c, t, s(3), ["Le gonfler", "*tout de suite*"])
    houle = 6 * math.sin(1.4 * t)
    h = O.hauteur_pour("vx_avion", 760)
    icone(c, "vx_avion", 540, 700 + houle, h, a, hach=("ambre", "vert"))
    eau(c, 80, 1000, 680 + houle, 820, t, a)
    pose(c, t, [(-1.0, "px_gilet_plat"), (w("gonfler", 3), "px_gonfle")], 540, 1560, 640, a)
    tampon(c, t, w("suite", 3) + 0.1, "PAS TOUT DE SUITE", 540, 1180)


# ------------------------------------------------------------------------------------------------ 3. la cabine
CAB_L = 940
CAB_X0 = W / 2 - CAB_L / 2
CAB_Y0 = 1180 - O.hauteur_pour("vx_cabine", CAB_L) if os.path.exists(os.path.join(O._DOSSIER_PX, "vx_cabine.png")) else 600
INT = (CAB_X0 + 0.07 * CAB_L, CAB_X0 + 0.9 * CAB_L)               # l'intérieur, en x
PORTE = (CAB_X0 + 0.71 * CAB_L, CAB_X0 + 0.83 * CAB_L)


def cab_y(f):
    return CAB_Y0 + f * (1180 - CAB_Y0)


def niveau(t):
    u1 = A.lisse((t - w("monte", 14)) / 1.6)
    u2 = A.lisse((t - s(17)) / 2.0)
    yb, yh, yp = cab_y(0.92), cab_y(0.3), cab_y(0.2)
    return yb - (yb - yh) * u1 - (yh - yp) * u2


def plafond_y(t):
    return max(cab_y(0.17), niveau(t) - 60)


def e3(c, t, a=1.0):
    ta = w("arrivez", 20)
    phrase(c, t, s(13), ["Mais dans la cabine,", "l'eau *monte*"], t1=s(15))
    phrase(c, t, s(15), ["Les sorties sont", "*sous l'eau*"], t1=s(17))
    phrase(c, t, s(17), ["Pour sortir,", "il faut *plonger*"], t1=s(19))
    phrase(c, t, s(19), ["Avec *16 kg*", "vers le plafond…"], t1=ta)
    phrase(c, t, ta, ["*Impossible*"])
    icone(c, "vx_cabine", W / 2, 1180, 1180 - CAB_Y0, a)
    niv = niveau(t)
    tp = w("monte", 14) + 0.7
    if t >= tp:                                            # le passager, soulevé par son gilet
        py = plafond_y(t)
        icone(c, "px_plafond", 420, py + 300, 300, a * A.lisse((t - tp) / 0.3))
    c.save()
    c.clipRect(skia.Rect(INT[0], CAB_Y0, INT[1], 1180))
    eau(c, INT[0], INT[1], niv, cab_y(0.95), t, a)
    c.restore()
    ts = w("sorties", 15)
    if t >= ts and (int((t - ts) * 4) % 2 == 0 or t >= ts + 1.5):
        O.dessiner(c, [rect(PORTE[0] - 8, cab_y(0.42), PORTE[1] + 8, cab_y(0.92))], AMBRE, 3.4, a)
        O.dessiner(c, O.texte("SORTIE", (PORTE[0] + PORTE[1]) / 2, cab_y(1.0) + 60, 34), AMBRE, 2, a)
    if t >= s(17):                                         # le chemin vers la porte, en pointillés
        py = plafond_y(t) + 120
        pts = O.lisser([(470, py), (560, cab_y(0.75)), (700, cab_y(0.82)), (PORTE[0], cab_y(0.7))], 3)
        tirets = [pts[i:i + 3] for i in range(0, len(pts) - 2, 6)]
        O.dessiner(c, tirets, VERT_PALE, 3, a, (t - s(17)) / 0.8)
    tk = w("seize", 19)
    if t >= tk:
        v = A.sortie((t - tk) / 0.4)
        for dx in (-120, 0, 120):
            O.dessiner(c, fleche_haut(420 + dx, plafond_y(t) + 150, 70 * v, 18), AMBRE, 4, a)
        O.dessiner(c, O.segments(f"{round(16 * A.sortie((t - tk) / 0.6, 2.5)):2d}", 470, 1420, 120), AMBRE, 5, a)
        O.dessiner(c, O.texte("KG", 590, 1420, 76, centre=False, gras=True), AMBRE, 3, a)
    if t >= ta:
        O.dessiner(c, croix(640, cab_y(0.8), 50), AMBRE, 6, a, (t - ta) / 0.2)


# ------------------------------------------------------------------------------------------------ 4. Comores 1996
def mini(x, y):
    tete = skia.Path()
    tete.addCircle(x, y - 22, 9)
    return O.contours(tete, 4) + [[(x, y - 13), (x, y + 10)], [(x - 12, y - 4), (x + 12, y - 4)],
                                  [(x, y + 10), (x - 8, y + 26)], [(x, y + 10), (x + 8, y + 26)]]


def e4(c, t, a=1.0):
    tg = w("gonflé", 24)
    phrase(c, t, s(21), ["*1996*, près", "des Comores"], t1=s(22))
    phrase(c, t, s(22), ["Beaucoup ont", "*survécu* au choc"], t1=s(24))
    phrase(c, t, s(24), ["Mais leur gilet", "était *gonflé*"])
    if t < s(22):
        k = A.lisse((t - s(21)) / 1.2)
        icone(c, "vx_avion_pique", 420 + 60 * k, 1000 + 80 * k, 460, a, hach=("ambre", "vert"))
        icone(c, "vx_ile", 860, 1210, 230, a, hach=("ambre", "vert"))
        eau(c, 80, 1000, 1190, 1450, t, a)
        O.dessiner(c, O.texte("OCÉAN INDIEN", W / 2, 1520, 34), VERT, 1.8, 0.8 * a, (t - w("détourné", 21)) / 0.5)
        return
    x0, y0, x1, y1 = 140, 640, 940, 1320                  # la cabine en coupe
    O.dessiner(c, [rect(x0, y0, x1, y1)], VERT_PALE, 4, a, (t - s(22)) / 0.4)
    niv = y1 - 20 - 380 * A.lisse((t - tg) / 2.0)
    c.save()
    c.clipRect(skia.Rect(x0 + 4, y0, x1 - 4, y1))
    eau(c, x0 + 4, x1 - 4, niv, y1 - 4, t, a)
    c.restore()
    for i in range(4):
        for j in range(8):
            x = x0 + 70 + j * 95
            yb = y0 + 150 + i * 150
            d = 0.1 * (j + 2 * i)
            u = A.lisse((t - tg - d) / 0.9)
            y = yb + (y0 + 60 - yb) * u
            if t < s(22) + 0.03 * (j + 8 * i):
                continue
            O.dessiner(c, mini(x, y), VERT_PALE, 2.2, a)
            if t >= tg + d:                               # le gilet gonflé
                g = skia.Path()
                g.addOval(skia.Rect(x - 16, y - 14, x + 16, y + 6))
                O.hachures(c, g, AMBRE, 5, -35, 1.4, 0.9 * a)
                O.dessiner(c, O.contours(g, 4), AMBRE, 2.2, a)
    if t >= tg:
        O.dessiner(c, O.texte("GILETS GONFLÉS DANS LA CABINE", W / 2, 1420, 38), AMBRE, 2, a, (t - tg) / 0.6)


# ------------------------------------------------------------------------------------------------ 5. le bon geste
def e5a(c, t, a=1.0):
    phrase(c, t, s(25), ["Le *bon* geste"])
    icone(c, "px_gilet_plat", 270, 1560, 760, a, (t - s(25)) / 0.6)
    lignes = [("ENFILÉ", w("enfilé", 26), True), ("SERRÉ", w("serrées", 27), True), ("GONFLÉ", w("gonflé", 29), False)]
    for k, (txt, t0, oui) in enumerate(lignes):
        if t < t0:
            continue
        y = 860 + 200 * k
        O.dessiner(c, O.texte(txt, 520, y, 76, centre=False, gras=True), VERT_PALE if oui else AMBRE, 3, a,
                   (t - t0) / 0.35)
        O.dessiner(c, coche(985, y - 30) if oui else croix(985, y - 30, 34), VERT_PALE if oui else AMBRE, 6, a,
                   (t - t0 - 0.2) / 0.2)


def e5b(c, t, a=1.0):
    tg = w("remplit", 32)
    phrase(c, t, s(30), ["On tire la languette", "*à la porte*"], t1=s(31))
    phrase(c, t, s(31), ["*une fois dehors*"], t1=s(32))
    phrase(c, t, s(32), ["Une cartouche de gaz", "le *gonfle*"], t1=s(33))
    phrase(c, t, s(33), ["en *quelques secondes*"])
    icone(c, "vx_porte", 540, 1540, 900, 0.55 * a)
    pose(c, t, [(s(30) - 0.3, "px_tire"), (tg, "px_gonfle")], 540, 1500, 700, a, 0.25)
    tc = w("cartouche", 32)
    if t >= tc:
        icone(c, "px_cartouche", 900, 900, 230, a, (t - tc) / 0.4)
        O.dessiner(c, O.texte("CO2", 900, 980, 50, gras=True), AMBRE, 2.4, a)
    if tg <= t < tg + 0.5:                                  # le gaz qui gonfle
        f = (t - tg) / 0.5
        tr = []
        for i in range(14):
            ang = 2 * math.pi * i / 14
            r0, r1 = 160 + 100 * f, 210 + 160 * f
            tr.append([(540 + r0 * math.cos(ang), 1150 + r0 * math.sin(ang)), (540 + r1 * math.cos(ang), 1150 + r1 * math.sin(ang))])
        O.dessiner(c, tr, VERT_PALE, 3, (1 - f) * a)


# ------------------------------------------------------------------------------------------------ 6. le froid
def e6a(c, t, a=1.0):
    tx, tv = w("vingt", 36), w("vole", 36)
    phrase(c, t, s(34), ["Deuxième ennemi :", "le *froid*"], t1=s(36))
    phrase(c, t, s(36), ["L'eau vole la chaleur", "*25 fois* plus vite"])
    icone(c, "px_grelotte", 540, 1520, 760, a, hach=("ambre", "vert"))
    if t >= tv:
        chaleur(c, t, 540, 1220, 4 + int(18 * A.lisse((t - tv) / 1.0)), 230, 380, a)
    if t >= tx:
        O.dessiner(c, croix(420, 610, 26), AMBRE, 5, a)
        O.dessiner(c, O.segments(f"{round(1 + 24 * A.sortie((t - tx) / 0.7, 2.5)):2d}", 600, 660, 130), AMBRE, 6, a)


def e6b(c, t, a=1.0):
    td, tc = w("deux", 37) + 0.25, w("cent", 39)
    phrase(c, t, s(37), ["L'Hudson, *2009*"], t1=s(38))
    phrase(c, t, s(38), ["Secours en", "*quelques minutes*"], t1=s(39))
    phrase(c, t, s(39), ["*155 sur 155*", "ont survécu"])
    riviere = skia.Path()
    riviere.addRect(skia.Rect(100, 560, 980, 1180))
    O.hachures(c, riviere, VERT, 13, 0, 1.2, 0.3 * a)
    O.dessiner(c, [rect(100, 560, 980, 1180)], VERT_SOMBRE, 2, a)
    icone(c, "vx_avion_dessus", 460, 1150, 560, a, hach=("ambre", "vert"))
    fx = 860 - 60 * A.lisse((t - s(37)) / 3.0)
    icone(c, "vx_ferry", fx, 760, 130, a, hach=("ambre", "vert"))
    if s(37) <= t < s(39) and t >= td:
        icone(c, "px_thermometre", 230, 1560, 320, a, (t - td) / 0.3)
        deg = round(15 - 13 * A.sortie((t - td) / 0.8, 2.5))
        O.dessiner(c, O.segments(f"{deg:2d}", 520, 1520, 130), AMBRE, 6, a)
        rond = skia.Path()
        rond.addCircle(660, 1380, 12)
        O.dessiner(c, O.contours(rond, 4) + O.texte("C", 720, 1520, 110, gras=True), AMBRE, 4, a)
    if s(38) <= t < s(39):
        icone(c, "px_chrono", 880, 1420, 170, a, (t - s(38)) / 0.4)
    if t >= tc:
        n = round(155 * A.sortie((t - tc) / 1.2, 2))
        tr = []
        for i in range(160):
            x, y = 180 + (i % 20) * 37, 1270 + (i // 20) * 30
            if i < n:
                tr.append(rect(x, y, x + 24, y + 18))
        O.dessiner(c, tr, VERT_PALE, 1.8, a)
        O.dessiner(c, O.segments(f"{n:3d}", 470, 1600, 70), AMBRE, 4, a)
        O.dessiner(c, O.texte("/ 155", 580, 1600, 60, centre=False), AMBRE, 2.6, a)


# ------------------------------------------------------------------------------------------------ 7. la position
def e7(c, t, a=1.0):
    tb, tg, ts = w("remonte", 44), w("colle", 46), w("surface", 47)
    phrase(c, t, s(40), ["On ne *nage* pas"], t1=w("bouger", 42))
    phrase(c, t, w("bouger", 42), ["Bouger fait fuir", "la *chaleur*"], t1=tb)
    phrase(c, t, tb, ["Genoux *remontés*,", "bras serrés"], t1=tg)
    phrase(c, t, tg, ["On se *colle*", "aux autres"], t1=ts)
    phrase(c, t, ts, ["Moins de *surface*,", "moins de chaleur perdue"])
    pose(c, t, [(s(40) - 0.3, "px_nage"), (tb, "px_boule"), (tg, "px_groupe")], 540, 1400, 600, a, 0.35,
         hach=("ambre", "vert"))
    n = (10 + int(10 * A.lisse((t - w("bouger", 42)) / 0.8))) if t < tb else (9 if t < tg else 4)
    chaleur(c, t, 540, 1100, n, 330, 470, a)
    tn = w("nage", 41)
    if tn <= t < tb:
        O.dessiner(c, croix(880, 760, 44), AMBRE, 6, a, (t - tn) / 0.2)


# ------------------------------------------------------------------------------------------------ 8. le toboggan et la fin
def e8(c, t, a=1.0):
    te = w("enlever", 51)
    phrase(c, t, s(49), ["Et avant", "le *toboggan*…"], t1=te)
    phrase(c, t, te, ["une chose", "à *enlever*"])
    icone(c, "vx_toboggan", 430, 1300, 640, a)
    O.dessiner(c, [[(100, 1300), (980, 1300)]], VERT_SOMBRE, 2, a)
    if t >= te:
        icone(c, "px_talon", 800, 1560, 230, a, (t - te) / 0.4)
        if int((t - te) * 3) % 2 == 0 or t > te + 1.5:
            O.dessiner(c, O.texte("?", 860, 1100, 220, gras=True), AMBRE, 5, a)


def fin(c, t, a=1.0):
    O.dessiner(c, [rect(80, 560, 1000, 1420)], AMBRE, 3, a)
    O.dessiner(c, O.texte("AVANT LE TOBOGGAN :", W / 2, 780, 50, gras=True), VERT_PALE, 3, a)
    O.dessiner(c, O.texte("LA CHOSE À ENLEVER", W / 2, 870, 50, gras=True), AMBRE, 3, a)
    dx = 6 * abs(math.sin(t * 5))
    O.dessiner(c, O.texte("LA SUITE DEMAIN", W / 2 - 30 + dx, 1100, 56, gras=True), VERT_PALE, 3.4, a)
    xt = W / 2 + O.largeur_texte("LA SUITE DEMAIN", 56) / 2 - 10 + dx
    O.dessiner(c, [[(xt, 1050), (xt + 40, 1075), (xt, 1100), (xt, 1050)]], AMBRE, 4, a)
    O.dessiner(c, O.texte("INFORMATION GÉNÉRALE - SUIVEZ L'ÉQUIPAGE", W / 2, 1360, 26), VERT, 1.4, 0.8 * a)


# ------------------------------------------------------------------------------------------------ montage
def ecrans():
    return [(0.0, e1), (s(5) - 0.25, Q.ecran_a), (s(7), Q.ecran_b), (s(9), Q.ecran_c), (s(11), Q.ecran_d),
            (s(13), e3), (s(21), e4), (s(25), e5a), (s(30), e5b), (s(34), e6a), (s(37), e6b), (s(40), e7),
            (s(49), e8), (e(57) + 0.05, fin)]


def heros(i):
    """Le dessin qui se transforme à l'enchaînement i (écran i-1 → écran i), ou None (simple fondu)."""
    sil = O.silhouette
    if i in (2, 3, 4):
        return Q.heros(i - 1, 0)
    return {5: (lambda: O.contours(Q.gilet_chemin(540, 1040 + 120, 3.0), 8), lambda: sil("px_plafond", 420, plafond_y(s(13)) + 300, 300)),
            6: (lambda: sil("vx_cabine", W / 2, 1180, 1180 - CAB_Y0), lambda: sil("vx_avion_pique", 420, 1000, 460)),
            7: (lambda: [rect(140, 640, 940, 1320)], lambda: sil("px_gilet_plat", 270, 1560, 760)),
            8: (lambda: sil("px_gilet_plat", 270, 1560, 760), lambda: sil("px_tire", 540, 1500, 700)),
            9: (lambda: sil("px_gonfle", 540, 1500, 700), lambda: sil("px_grelotte", 540, 1520, 760)),
            10: (lambda: sil("px_grelotte", 540, 1520, 760), lambda: sil("vx_avion_dessus", 460, 1150, 560)),
            11: (lambda: sil("vx_avion_dessus", 460, 1150, 560), lambda: sil("px_nage", 540, 1400, 600)),
            12: (lambda: sil("px_groupe", 540, 1400, 600), lambda: sil("vx_toboggan", 430, 1300, 640))}.get(i)


_HEROS = {}


def image(c, t):
    O.ecran(c, t)
    ec = ecrans()
    k = max(i for i, x in enumerate(ec) if x[0] <= t)
    for i in range(1, len(ec) - 1):                        # enchaînement (sauf vers le carton de fin : coupe)
        b = ec[i][0]
        if b - 0.25 <= t < b + 0.25:
            u = (t - b + 0.25) / 0.5
            c.saveLayerAlpha(None, int(255 * (1 - A.lisse(u / 0.6))))
            ec[i - 1][1](c, t)
            c.restore()
            c.saveLayerAlpha(None, int(255 * A.lisse((u - 0.4) / 0.6)))
            ec[i][1](c, t)
            c.restore()
            h = heros(i)
            if h:
                if i not in _HEROS:
                    _HEROS[i] = (h[0](), h[1]()) if callable(h[0]) else h
                ha, hb = _HEROS[i]
                for tr, it in A.flux(("ep29", i), ha, hb, u):
                    O.dessiner(c, tr, AMBRE, 3.2, it)
            break
    else:
        z = 1.0                                           # coups de caméra sur quelques mots forts
        for tw in [w("seize", 10), w("arrivez", 20), w("vingt", 36), w("cent", 39)]:
            if t >= tw:
                z += 0.05 * math.exp(-6 * (t - tw))
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        ec[k][1](c, t)
        c.restore()
    if ec[k][1] is not fin:
        Q.sous_titre(c, t)


def sons():
    debuts = [x[0] for x in ecrans()[1:]]
    ev = [(b - 0.25, Z.whoosh(0.5, 0.07)) for b in debuts]
    ev += [(t, Z.thump(0.35)) for t in [w("seize", 9), w("plafond", 19), w("arrivez", 20), w("gonflé", 29),
                                        w("remplit", 32), w("vingt", 36), w("cent", 39), w("nage", 41)]]
    ev += [(t, Z.boom(0.45, 70)) for t in [w("noyer", 2), w("seize", 10), w("gonflé", 24), w("froid", 35),
                                           w("enlever", 51)]]
    ev += [(w("suite", 3) + 0.1, Z.snap(0.3)), (w("monte", 14), Z.bulles(2.0, 0.1)), (w("tout", 8), Z.bulles(1.6, 0.08)),
           (w("gonflé", 24), Z.bulles(2.0, 0.1)), (w("remplit", 32), Z.souffle(0.5, 0.15, False)),
           (w("vole", 36), Z.vent(2.5, 0.05, 150, 900)), (w("archimède", 6), Z.pince(659.3, 0.1)),
           (w("effort", 12), Z.pince(1046.5, 0.08)), (w("sorties", 15), Z.pince(880, 0.07)),
           (w("poids", 8), Z.chirp(400, 900, 0.4, 0.06)), (e(57) + 0.05, Z.boom(0.6, 50)), (e(57) + 0.05, Z.riser(0.8, 0.07))]
    for mot, i in [("enfilé", 26), ("serrées", 27), ("cartouche", 32), ("l'hudson", 37), ("minutes", 38),
                   ("remonte", 44), ("colle", 46), ("surface", 47), ("toboggan", 49)]:
        ev.append((w(mot, i), Z.pince(784, 0.07)))
    ev += [(w("seize", 9) + 0.06 * i, Z.pince(523.3 * 2 ** (i / 12), 0.05, 0.25)) for i in range(16)]
    ev += [(w("cent", 39) + 0.06 * i, Z.pince(440 * 2 ** (i / 12), 0.04, 0.2)) for i in range(20)]
    return ev


def mixage(chemin, voix, dur):
    n = int(dur * MI.SR)
    v = np.zeros(n)
    v[:min(n, len(voix))] = voix[:n]
    v *= 10 ** (-16 / 20) / (np.sqrt((v[np.abs(v) > 0.01] ** 2).mean()) + 1e-9)
    nappe = MI.bed(dur + 1)[:n]
    nappe = nappe.mean(1) if nappe.ndim == 2 else nappe
    nappe = nappe / (np.abs(nappe).max() + 1e-9) * 10 ** (-24 / 20)
    tt = np.arange(n) / MI.SR
    for tc in [w("seize", 10), w("vingt", 36), w("enlever", 51)]:     # la nappe se coupe avant les révélations
        nappe *= np.clip(np.maximum(np.abs(tt - (tc - 0.45)) / 0.45, (tt > tc + 0.3) | (tt < tc - 0.9)), 0, 1)
    a = v + nappe
    for t0, snd in sons():
        i = int(t0 * MI.SR)
        k = min(n - i, len(snd))
        if k > 0 and i >= 0:
            a[i:i + k] += 0.6 * snd[:k]
    a *= np.minimum(1, (n - np.arange(n)) / (0.6 * MI.SR))
    a = a / max(1.0, np.abs(a).max() / 0.95)
    with wave.open(chemin, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(MI.SR)
        f.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def rendre(sortie, t0=0.0, t1=None):
    voix = Q.preparer()
    dur = M.SEG[-1][1] + 1.8
    t1 = dur if t1 is None else t1
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    for f in range(int(t0 * FPS), int(t1 * FPS)):
        t = f / FPS
        c = surf.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        image(c, t)
        if prec is not None:                               # traînée très brève du phosphore
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=0.35, BlendMode=skia.BlendMode.kLighten))
        prec = surf.makeImageSnapshot()
        ff.stdin.write(O.finition(prec.toarray(), t, FPS).tobytes())
        if f % 300 == 0:
            print(f"{t:5.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()
    mixage(f"{tmp}/a.wav", voix, dur)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}",
                    "-i", f"{tmp}/a.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", M.volume_cible(f"{tmp}/a.wav"), "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", sortie], check=True)
    print("OK", sortie)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep29_osc2_complet.mp4"
    if len(sys.argv) > 3:
        rendre(out, float(sys.argv[2]), float(sys.argv[3]))
    else:
        rendre(out)
