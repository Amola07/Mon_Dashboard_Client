"""Épisode 23 — « Voiture tombée à l'eau » — style oscilloscope, calé sur la voix (≈ 76 s).

Moteur de l'épisode 21 (faisceau, persistance, transitions, sous-titres, mixage) ; seuls les tableaux, les
flashs/secousses et les effets sonores sont propres à l'épisode.

    python -m films.episodes.ep23_voiture_eau.oscillo_ep23 output/ep23_oscillo.mp4
"""
import math
import os
import sys

import numpy as np
import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, P, W, bonhomme, cercle_pts, ease,
                                                         ecrit, faisceau, fleche, pointilles, rect_pts, titres, trace)
from films.styles import mouvement as MV
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
M.SEGS = os.path.join(HERE, "audio", "voix.json")
s, e = M.s, M.e
RNG = np.random.default_rng(23)


# ------------------------------------------------------------------------------------------------ dessins
def tf(pts, cx, by, ech=1.0, ang=0.0):
    """Repère voiture (origine au milieu du bas de caisse, y vers le haut négatif) → écran, rotation autour du centre."""
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for x, y in pts:
        y0 = y + 90
        out.append((cx + ech * (x * ca - y0 * sa), by - 90 * ech + ech * (x * sa + y0 * ca)))
    return out


def cote(cx, by, ech=1.0, ang=0.0):
    """Voiture vue de côté (avant à droite). Renvoie un dict de lignes brisées déjà placées."""
    T = lambda pts: tf(pts, cx, by, ech, ang)
    return {
        "caisse": [T([(-280, 0), (-285, -80), (-200, -95), (-140, -180), (90, -180), (170, -100), (280, -85), (285, 0),
                      (-280, 0)])],
        "vitre_ar": [T([(-185, -100), (-135, -168), (-30, -168), (-30, -100), (-185, -100)])],
        "vitre_av": [T([(-15, -100), (-15, -168), (80, -168), (140, -100), (-15, -100)])],
        "pare_brise": [T([(90, -180), (170, -100)])],
        "porte": [T([(-15, -100), (150, -100), (150, -10), (-15, -10)])],
        "roues": [T(cercle_pts(-170, 0, 46, 24)), T(cercle_pts(175, 0, 46, 24))],
        "T": T,
    }


def face(cx, by, ech=1.0):
    """Voiture vue de face (coupe) : bas de caisse = portières, habitacle vitré au-dessus."""
    T = lambda pts: [(cx + ech * x, by + ech * y) for x, y in pts]
    return {
        "bas": [T([(-220, 0), (220, 0), (225, -150), (-225, -150), (-220, 0)])],
        "haut": [T([(-190, -150), (-140, -280), (140, -280), (190, -150)])],
        "roues": [T(rect_pts(-215, 0, -150, 35)), T(rect_pts(150, 0, 215, 35))],
        "tete": [T(cercle_pts(-70, -205, 26, 20)), T([(-120, -150), (-110, -170), (-30, -170), (-20, -150)])],
        "porte_g": [T([(-225, -150), (-220, 0)])],
        "porte_d": [T([(225, -150), (220, 0)])],
    }


def eau(c, y, t, x0=40, x1=1040, amp=7, intense=1.0, fond=1500):
    vag = [[(x, y + amp * math.sin(x / 34 + t * 4)) for x in range(int(x0), int(x1) + 1, 10)]]
    faisceau(c, vag, 1.0, VERT_PALE, 1.2, intense)
    lignes = [[(x, yy + 3 * math.sin(x / 50 + t * 2 + yy)) for x in range(int(x0) + 30, int(x1) - 29, 60)][::1]
              for yy in np.arange(y + 70, fond, 90)]
    tirets = []
    for ln in lignes:
        tirets += [[p, (p[0] + 26, p[1])] for p in ln]
    if tirets:
        faisceau(c, tirets, 1.0, VERT, 0.5, 0.35 * intense)


def croix(x, y, r):
    return [[(x - r, y - r), (x + r, y + r)], [(x + r, y - r), (x - r, y + r)]]


def telephone(x, y, ech=1.0):
    return [rect_pts(x - 45 * ech, y - 80 * ech, x + 45 * ech, y + 80 * ech), [(x - 15 * ech, y + 62 * ech), (x + 15 * ech, y + 62 * ech)],
            rect_pts(x - 35 * ech, y - 62 * ech, x + 35 * ech, y + 45 * ech)]


def marteau(x, y, ech=1.0):
    return [[(x, y), (x, y + 130 * ech)], [(x - 55 * ech, y - 6 * ech), (x - 70 * ech, y + 6 * ech), (x + 50 * ech, y + 6 * ech),
                                           (x + 50 * ech, y - 18 * ech), (x - 55 * ech, y - 6 * ech)]]


def fleches_pression(niveau, xg, xd, y_haut, y_bas, k=0.35, pas=34):
    """Flèches horizontales qui poussent sur les deux portières, plus longues avec la profondeur."""
    tr = []
    for y in np.arange(y_bas - 10, y_haut, -pas):
        p = y - niveau
        if p <= 0:
            continue
        L = min(170, 18 + k * p)
        tr += fleche(xg - 14 - L, y, xg - 14, y, 10) + fleche(xd + 14 + L, y, xd + 14, y, 10)
    return tr


# ------------------------------------------------------------------------------------------------ tableaux
def tab_accroche(c, t):
    gras = 1.0 + 0.8 * (1 - ease(t / 2.0))
    NIV = 1080
    plonge = ease(t / 0.45)
    by = 980 + 150 * plonge + 8 * math.sin(t * 2.2) * plonge
    ang = 0.32 * plonge - 0.05 * math.sin(t * 1.7) * plonge
    v = cote(520, by, 1.35, ang)
    for k in ("caisse", "vitre_ar", "vitre_av", "roues"):
        faisceau(c, v[k], 1.0, VERT_PALE, 1.3 * gras)
    px, py = v["T"]([(45, -62)])[0]
    MV.dessiner(c, MV.corps("assis_panique", t, px, py, 1.35 * 110, 1, rot=ang, boucle="aller-retour"), VERT_PALE,
             1.1 * gras)
    eau(c, NIV, t, amp=7 + 18 * max(0.0, 1 - t / 1.2), intense=gras)
    if t < 0.5:                                                             # gerbe d'eau à l'impact
        for _ in range(10):
            M.ETINCELLES.append([RNG.uniform(250, 820), NIV, RNG.uniform(-7, 7), RNG.uniform(-22, -9), 1.0])
    if t < s(1):                                                            # la surprise affirmée dès l'image 0
        ecrit(c, t, -1.0, "N'OUVREZ PAS", W / 2, 300, 88, AMBRE, True, 2.2, vitesse=0.0)
        ecrit(c, t, -1.0, "LA PORTIÈRE", W / 2, 400, 88, AMBRE, True, 2.2, vitesse=0.0)
        ecrit(c, t, -1.0, "VOITURE À L'EAU", W / 2, 470, 40, VERT_PALE, vitesse=0.0)
    titres(c, t, [(s(1), "N'APPELEZ PAS !", AMBRE, 80)], halo=2.0)
    tp = s(0) + 2.6                                                         # « … ouvrir la portière »
    if t > tp:
        faisceau(c, v["porte"], 1.0, AMBRE, 1.8, 0.7 + 0.3 * math.sin(t * 10))
        cx, cy = v["T"]([(65, -55)])[0]
        trace(c, t, tp + 0.2, 0.2, croix(cx, cy, 70), AMBRE, 2.4, bip=500)
    if t > s(1):
        trace(c, t, s(1) + 0.1, 0.3, telephone(880, 640, 1.0), VERT_PALE, 1.2, bip=1600)
        trace(c, t, s(1) + 0.9, 0.2, croix(880, 640, 75), AMBRE, 2.2, bip=500)
        ecrit(c, t, s(1) + 1.2, "PAS TOUT DE SUITE", W / 2, 470, 50, VERT_PALE)


def tab_pression(c, t):
    t0 = s(2)
    titres(c, t, [(t0, "POURQUOI PAS LA PORTIÈRE ?", VERT_PALE, 50), (s(3), "LA PRESSION DE L'EAU", AMBRE, 58),
                  (s(5), "SOUS L'EAU…", AMBRE, 70), (s(6), "PERSONNE NE PEUT POUSSER ÇA", VERT_PALE, 46)])
    CX, BY, K = 540, 1330, 1.45
    f = face(CX, BY, K)
    trace(c, t, t0, 0.5, f["bas"] + f["haut"] + f["roues"], VERT_PALE, 1.3, bip=1100)
    pousse = t > s(6)
    if t > t0 + 0.3:
        tr = 3 * math.sin(t * 50) if pousse else 0.0
        fig = (MV.corps("pousse_assis", t - s(6), CX - 110 * K + tr, BY - 110 * K, 260, -1, fin=1.6, boucle="aller-retour")
               if pousse else MV.corps("assis_panique", t - t0, CX - 60 * K, BY - 110 * K, 260, -1, boucle="aller-retour"))
        MV.dessiner(c, fig, VERT_PALE, 1.2)
    y_vitre, y_toit = BY - 150 * K, BY - 280 * K
    q1 = ease((t - s(4)) / 2.6)
    q2 = ease((t - s(5) - 0.3) / 1.6)
    niveau = BY + 60 - (BY + 60 - y_vitre) * q1 - (y_vitre - (y_toit - 260)) * q2
    if t > s(3) - 0.2:
        eau(c, niveau, t, amp=6)
    if t > s(4) + 0.2:
        faisceau(c, fleches_pression(niveau, CX - 225 * K, CX + 225 * K, y_vitre, BY, 0.55), 1.0, AMBRE, 1.0)
        M.son(("p", 0), s(4) + 0.2, "trace", 900, 2.0)
    if t > s(4) + 0.5:
        kg = 200 * ease((t - s(4) - 0.5) / 3.3) + 900 * q2
        txt = f"{kg:4.0f} kg" if kg < 1000 else f"{kg / 1000:3.1f} t"
        ecrit(c, t, s(4) + 0.5, "FORCE SUR LA PORTIÈRE", W / 2, 470, 34, VERT)
        ecrit(c, t, s(4) + 0.5, txt, W / 2, 580, 100, AMBRE, True, 1.8, vitesse=0.0)
    if t > s(6):                                                            # quelqu'un pousse, rien ne bouge
        ecrit(c, t, s(6) + 0.3, "IMPOSSIBLE", CX, BY - 40, 54, AMBRE, True, 1.6)


def tab_minute(c, t):
    t0 = s(7)
    titres(c, t, [(t0, "BONNE NOUVELLE", VERT_PALE, 66), (s(8), "LA VOITURE FLOTTE", VERT_PALE, 60),
                  (s(9), "≈ 1 MINUTE D'AIR", AMBRE, 62), (s(10), "PAS DE TÉLÉPHONE", AMBRE, 64)])
    NIV = 1180
    enf = ease((t - t0) / 8.0)
    v = cote(520, NIV + 70 + 40 * enf + 6 * math.sin(t * 2), 1.25, 0.05 + 0.12 * enf)
    trace(c, t, t0, 0.5, v["caisse"] + v["vitre_ar"] + v["vitre_av"] + v["roues"], VERT_PALE, 1.2, bip=1100)
    eau(c, NIV, t)
    if t > s(8) + 0.3:
        bx, by_ = v["T"]([(-40, -135)])[0]
        ecrit(c, t, s(8) + 0.4, "AIR", bx, by_ + 12, 40, VERT_PALE)
        trace(c, t, s(8) + 0.5, 0.3, fleche(860, 1460, 860, 1260, 22), VERT_PALE, 1.1, bip=1700)
        ecrit(c, t, s(8) + 0.6, "FLOTTE", 860, 1500, 28, VERT_PALE)
    if t > s(9):                                                            # compte à rebours
        CX, CY, R = 540, 680, 130
        reste = max(0.0, 60 - (t - s(9)) * 4)
        arc = [(CX + R * math.sin(2 * math.pi * u), CY - R * math.cos(2 * math.pi * u))
               for u in np.linspace(0, reste / 60, max(2, int(60 * reste / 60) + 2))]
        trace(c, t, s(9), 0.3, [cercle_pts(CX, CY, R + 14, 60)], VERT, 0.6, 0.6, bip=1200)
        faisceau(c, [arc], 1.0, AMBRE, 1.6)
        ecrit(c, t, s(9), f"{reste:2.0f} s", CX, CY + 28, 72, AMBRE, vitesse=0.0)
    if t > s(10) + 1.0:
        trace(c, t, s(10) + 1.0, 0.3, telephone(880, 680, 0.8), VERT_PALE, 1.1, bip=1600)
        trace(c, t, s(10) + 1.6, 0.2, croix(880, 680, 62), AMBRE, 2.2, bip=500)


GESTES = (("1", "CEINTURE"), ("2", "VITRE"), ("3", "ENFANTS"), ("4", "SORTEZ"))


def tab_gestes(c, t):
    t0 = s(11)
    titres(c, t, [(t0, "4 GESTES", AMBRE, 76)])
    debuts = [s(12), s(13), s(17), s(19)]
    for i, ((n, mot), td) in enumerate(zip(GESTES, debuts)):
        y = 470 + i * 82
        actif = td <= t < (debuts[i + 1] if i < 3 else 1e9)
        fait = i < 3 and t >= debuts[i + 1]
        col = AMBRE if actif else (VERT_PALE if fait else VERT)
        trace(c, t, t0 + 0.6 + 0.25 * i, 0.2, [rect_pts(170, y - 48, 224, y + 6)], col, 1.1, bip=1500 + 100 * i)
        if fait:
            trace(c, t, debuts[i + 1] - 0.1, 0.15, [[(180, y - 20), (196, y - 4), (218, y - 40)]], VERT_PALE, 1.6, bip=0)
        ecrit(c, t, t0 + 0.7 + 0.25 * i, f"{n} · {mot}", 250, y, 54 if actif else 46, col, False, 1.6 if actif else 1.0)
    # la voiture, vitre au ras de l'eau
    NIV = 1225 - 25 * ease((t - t0) / 22)
    v = cote(470, 1380, 1.35, 0.0)
    trace(c, t, t0, 0.5, v["caisse"] + v["vitre_ar"] + v["roues"], VERT_PALE, 1.2, bip=0)
    T = v["T"]
    # vitre avant : verre qui descend (commande) puis éclate (brise-vitre)
    t_cmd, t_coin = s(14) + 0.4, s(15) + 1.6
    ouv = 0.4 * ease((t - t_cmd) / 1.2)
    casse = t >= t_coin
    faisceau(c, v["vitre_av"], 1.0, AMBRE if s(13) <= t < s(16) else VERT_PALE, 1.2)
    if not casse:
        yt = -168 + 68 * ouv
        verre = [T([(-15, yt), (80 + 60 * (yt + 168) / 68, yt)]), T([(10, yt + 10), (30, -105)]), T([(40, yt + 10), (60, -105)])]
        faisceau(c, verre, 1.0, VERT_PALE, 0.7, 0.7)
    elif t < t_coin + 1.2:                                                  # éclats
        u = t - t_coin
        cx, cy = T([(120, -110)])[0]
        fis = [[(cx, cy), (cx + 160 * math.cos(a) * min(1, u * 6), cy + 160 * math.sin(a) * min(1, u * 6))]
               for a in np.linspace(math.pi * 0.9, math.pi * 1.6, 7)]
        faisceau(c, fis, 1.0, AMBRE, 1.0, max(0.0, 1 - u))
        pts = [(cx - 90 + 60 * math.sin(i * 7.1), cy - 30 + 25 * math.cos(i * 3.3) + 500 * u ** 2) for i in range(26)]
        p = skia.Path()
        for x, y in pts:
            p.addCircle(x, y, 3)
        c.drawPath(p, P(VERT_PALE, 0, 255 * max(0, 1 - u), fill=True))
    if s(14) <= t < s(15):                                                  # bouton de lève-vitre
        trace(c, t, s(14) + 0.1, 0.3, [rect_pts(820, 950, 960, 1050)], VERT_PALE, 1.0, bip=1500)
        ecrit(c, t, s(14) + 0.2, "▼", 890, 1018, 60, AMBRE if t > t_cmd else VERT_PALE, vitesse=0.0)
    if s(15) <= t < s(16) + 0.3:
        hx, hy = T([(130, -110)])[0]
        avance = ease((t - s(15) - 0.6) / 1.0)
        trace(c, t, s(15) + 0.3, 0.3, marteau(hx + 150 - 110 * avance, hy - 120 + 90 * avance, 0.9), VERT_PALE, 1.3, bip=1300)
        ecrit(c, t, s(15) + 0.6, "DANS UN COIN", 860, 1000, 34, AMBRE)
    if s(16) <= t < s(17):
        faisceau(c, v["pare_brise"], 1.0, AMBRE, 2.4, 0.7 + 0.3 * math.sin(t * 10))
        mx, my = T([(130, -140)])[0]
        trace(c, t, s(16) + 0.2, 0.2, croix(mx + 10, my, 45), AMBRE, 2.2, bip=500)
        ecrit(c, t, s(16) + 0.4, "PARE-BRISE :", 820, 980, 36, AMBRE)
        ecrit(c, t, s(16) + 1.2, "FEUILLETÉ", 820, 1030, 36, AMBRE)
    # conducteur, ceinture, puis les enfants et vous qui sortez
    hx, hy = T([(60, -130)])[0]
    sortie = ease((t - s(19) - 0.5) / 1.0)
    E = 1.35 * 110                                                         # pixels par mètre dans la voiture
    if t < s(19) + 0.5:
        px, py = T([(45, -62)])[0]
        MV.dessiner(c, MV.corps("assis_sangle", t - s(12), px, py, E, 1, boucle="aller-retour"), VERT_PALE, 1.1)
    retire = ease((t - s(12) - 0.7) / 0.5)
    if retire < 1:
        a, b = T([(72, -150)])[0], T([(28, -68)])[0]
        faisceau(c, [[a, (a[0] + (b[0] - a[0]) * (1 - retire), a[1] + (b[1] - a[1]) * (1 - retire))]], 1.0, AMBRE, 1.6)
    if s(17) <= t:                                                          # l'enfant sort par la fenêtre
        u = ease((t - s(18)) / 1.4)
        x0, y0 = T([(-60, -62)])[0]
        x1, y1 = T([(10, -180)])[0]
        y1 -= 0.9 * E * 0.62
        if t < s(18):
            fig = MV.corps("assis_panique", t, x0, y0, E * 0.62, 1, boucle="aller-retour")
        else:
            fig = MV.corps("grimpe", t - s(18), x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, E * 0.62, 1, debut=0.8, fin=4.0)
        MV.dessiner(c, fig, VERT_PALE, 1.1)
        if t < s(19):
            trace(c, t, s(18), 0.3, fleche(x0 + 40, y0 - 30, x1 + 40, y1 - 90, 18), AMBRE, 1.1, bip=1700)
    if t > s(19) + 0.5:                                                     # vous, sur le toit, puis vers la rive
        px, py = T([(45, -62)])[0]
        tx, ty = T([(-60, -180)])[0]
        ty -= 0.9 * E
        t_plonge = s(20) + 1.0
        if t < t_plonge:                                                    # il grimpe sur le toit
            fig = MV.corps("grimpe", t - s(19) - 0.5, px + (tx - px) * sortie, py + (ty - py) * sortie, E, 1,
                            debut=0.8, fin=4.0)
        else:                                                               # puis nage vers la rive
            k = ease((t - t_plonge) / 2.4)
            fig = MV.corps("nage", t - t_plonge, 640 + 230 * k, NIV + 6, E * 0.9, 1, fin=2.0, boucle="aller-retour")
        MV.dessiner(c, fig, AMBRE, 1.3)
    if t > s(20) + 0.6:
        trace(c, t, s(20) + 0.6, 0.5, [[(860, NIV), (920, NIV - 40), (1060, NIV - 70)]], VERT_PALE, 1.4, bip=1100)
        ecrit(c, t, s(20) + 0.9, "RIVE", 960, NIV - 100, 34, VERT_PALE)
    eau(c, NIV, t, amp=6)


def tab_portiere(c, t):
    t0 = s(21)
    titres(c, t, [(t0, "ET LA PORTIÈRE ?", VERT_PALE, 64), (s(22) + 1.6, "SEULEMENT PLEINE D'EAU", AMBRE, 52),
                  (s(23), "NOIR · SOUS L'EAU · SANS AIR", AMBRE, 46)])
    CX, BY, K = 540, 1330, 1.45
    f = face(CX, BY, K)
    trace(c, t, t0, 0.5, f["bas"] + f["haut"] + f["roues"], VERT_PALE, 1.3, bip=1100)
    MV.dessiner(c, MV.corps("assis_panique", t - t0, CX - 60 * K, BY - 110 * K, 260, -1, boucle="aller-retour"),
             VERT_PALE, 1.2)
    eau(c, 560, t, amp=5)
    interieur = BY - (280 * K - 4) * ease((t - s(22) - 1.4) / 2.0)
    if t > s(22) + 1.4:                                                     # l'habitacle se remplit
        def demi(y):
            h = (BY - y) / K
            return K * (218 if h <= 150 else 188 - 48 * (h - 150) / 130)
        faisceau(c, [[(CX - demi(interieur) + 6, interieur), (CX + demi(interieur) - 6, interieur)]], 1.0, VERT_PALE, 1.1)
        for y in np.arange(interieur + 40, BY - 10, 60):
            faisceau(c, [[(CX - demi(y) + 20, y), (CX + demi(y) - 20, y)]], 1.0, VERT, 0.4, 0.4)
    pleine = ease((t - s(22) - 3.3) / 0.4)
    ext = fleches_pression(560, CX - 225 * K, CX + 225 * K, BY - 150 * K, BY, 0.12 * (1 - 0.0))
    faisceau(c, ext, 1.0, AMBRE, 0.9, 0.6 if pleine else 1.0)
    if pleine > 0:                                                          # pressions égales : la portière s'ouvre
        dedans = []
        for y in np.arange(BY - 10, BY - 150 * K, -34):
            dedans += fleche(CX - 150 * K, y, CX - 222 * K + 6, y, 10) + fleche(CX + 150 * K, y, CX + 222 * K - 6, y, 10)
        faisceau(c, dedans, pleine, VERT_PALE, 0.9)
        ecrit(c, t, s(22) + 3.4, "ÉQUILIBRE", W / 2, BY + 120, 44, VERT_PALE)
    if t > s(23):                                                           # le noir
        nuit = ease((t - s(23)) / 1.2) * (1 - ease((t - s(23) - 2.0) / 0.3))
        c.drawRect(skia.Rect(0, 400, W, 1560), P((0, 0, 0), 0, 210 * nuit, fill=True))
        ecrit(c, t, s(23) + 1.4, "AIR : 0 %", W / 2, 1000, 72, AMBRE, True, 1.8, vitesse=0.0)


def tab_fenetre(c, t):
    t0 = s(24)
    titres(c, t, [(t0, "PAR LA FENÊTRE", AMBRE, 72)])
    NIV = 1240
    v = cote(470, 1380, 1.35, 0.0)
    trace(c, t, t0, 0.5, v["caisse"] + v["vitre_ar"] + v["vitre_av"] + v["roues"], VERT_PALE, 1.2, bip=1100)
    eau(c, NIV, t)
    faisceau(c, v["vitre_av"], 1.0, AMBRE, 2.0, 0.7 + 0.3 * math.sin(t * 8))
    hx, hy = v["T"]([(60, -134)])[0]
    u = ease((t - t0 - 0.6) / 1.4)
    E = 1.35 * 110
    MV.dessiner(c, MV.corps("grimpe", t - t0 - 0.6, hx - 15 + 135 * u, hy + 95 - 260 * u, E, 1, debut=0.8, fin=4.0),
             VERT_PALE, 1.3)
    trace(c, t, t0 + 0.4, 0.3, fleche(hx + 30, hy - 20, hx + 150, hy - 220, 22), AMBRE, 1.4, bip=1700)
    ecrit(c, t, t0 + 1.4, "AU-DESSUS DE L'EAU", W / 2, 470, 44, VERT_PALE)


def tab_recap(c, t):
    t0 = s(25)
    for i, (dt, mot) in enumerate(zip((0.0, 0.84, 1.49, 2.15), ("CEINTURE", "VITRE", "ENFANTS", "SORTEZ"))):
        ecrit(c, t, t0 + dt, mot, W / 2, 600 + 130 * i, 96, AMBRE if i == 3 else VERT_PALE, True, 1.8, vitesse=0.0)
    ecrit(c, t, s(26), "1 MINUTE · 4 GESTES", W / 2, 1200, 56, AMBRE, True, 1.6)
    ecrit(c, t, s(27) + 0.2, "VOUS LES CONNAISSEZ.", W / 2, 1300, 40, VERT_PALE)


def tab_question(c, t):
    t0 = s(28)
    ecrit(c, t, t0, "ET VOUS ?", W / 2, 640, 140, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, t0 + 0.5, "VOUS AVEZ UN", W / 2, 800, 58, VERT_PALE)
    ecrit(c, t, t0 + 0.9, "BRISE-VITRE ?", W / 2, 875, 58, VERT_PALE)
    trace(c, t, t0 + 0.3, 0.4, marteau(540, 940, 1.1), VERT_PALE, 1.3, bip=1300)
    if t > s(29):
        ecrit(c, t, s(29), "DITES-LE EN COMMENTAIRE", 500, 1190, 40, VERT_PALE, True, 1.5)
        b = 18 * abs(math.sin((t - s(29)) * 5))
        trace(c, t, s(29) + 0.2, 0.25, fleche(800 + b, 1176, 960 + b, 1176, 26), AMBRE, 1.8, bip=1700)


def tableaux():
    return [(0.0, tab_accroche, None), (s(2) - 0.1, tab_pression, "neige"), (s(7) - 0.1, tab_minute, "balayage"),
            (s(11) - 0.1, tab_gestes, "glitch"), (s(21) - 0.1, tab_portiere, "noir"), (s(24) - 0.1, tab_fenetre, "balayage"),
            (s(25) - 0.1, tab_recap, "neige"), (s(28) - 0.1, tab_question, "glitch")]


def chocs():
    t_coin = s(15) + 1.6
    flashs = [s(0) + 2.8, s(5) + 1.9, t_coin, s(23) + 1.4]
    secousses = [(0.4, 0.3), (s(5) + 1.9, 0.25), (t_coin, 0.15)]
    return flashs, secousses


def effets(tabs):
    tp = s(0) + 2.6
    ev = [(0.0, Z.whoosh(0.4, 0.14, False)), (0.4, Z.boom(0.55, 70)), (0.4, Z.crepitement(0.8, 0.2, 160)),
          (0.45, Z.bulles(2.2, 0.14)), (0.4, Z.vent(1.6, 0.06, 120, 500)),
          (tp + 0.2, Z.alarme(0.08, 1)), (tp + 0.2, Z.thump(0.35)),
          (s(1) + 0.1, Z.chirp(1400, 1400, 0.12, 0.06)), (s(1) + 0.3, Z.chirp(1400, 1400, 0.12, 0.06)),
          (s(1) + 0.9, Z.thump(0.35)), (s(1) + 0.9, Z.glitch(0.15, 0.08))]
    # pression
    ev += [(s(3), Z.vibration(1.2, 0.12)), (s(4), Z.bulles(3.0, 0.08)), (s(4) + 0.2, Z.grincement(3.4, 0.10)),
           (s(4) + 3.8, Z.boom(0.4, 80)), (s(5) + 0.2, Z.vent(1.6, 0.10, 100, 600)), (s(5) + 1.9, Z.boom(0.75, 50)),
           (s(5) + 1.9, Z.clang(110, 0.2, 1.8)), (s(6), Z.grincement(1.0, 0.1)), (s(6) + 0.3, Z.thump(0.3))]
    ev += [(s(4) + 0.5 + 0.08 * i, Z.cliquet(0.03)) for i in range(40)]
    # une minute
    ev += [(s(7), Z.cloche(523.3, 0.10)), (s(7) + 0.3, Z.cloche(659.3, 0.08)), (s(8), Z.bulles(1.5, 0.08)),
           (s(8) + 0.5, Z.chirp(400, 900, 0.4, 0.07)), (s(9), Z.tictac(s(11) - s(9) - 0.2, 0.06, 0.25)),
           (s(10) + 1.0, Z.chirp(1400, 1400, 0.12, 0.06)), (s(10) + 1.2, Z.chirp(1400, 1400, 0.12, 0.06)),
           (s(10) + 1.6, Z.thump(0.3)), (s(10) + 1.6, Z.alarme(0.06, 1))]
    # quatre gestes
    t_coin = s(15) + 1.6
    ev += [(s(11) + 0.6 + 0.25 * i, Z.pince(523.3 * 2 ** (i * 4 / 12), 0.07)) for i in range(4)]
    ev += [(s(12) + 0.7, Z.cliquet(0.2)), (s(12) + 0.75, Z.whoosh(0.3, 0.07)), (s(13) - 0.1, Z.cloche(784, 0.08)),
           (s(14) + 0.3, Z.cliquet(0.12)), (s(14) + 0.4, Z.porte(1.3, 0.08)), (s(15) + 0.6, Z.whoosh(0.5, 0.08)),
           (t_coin, Z.craquement(0.4)), (t_coin, Z.crepitement(0.9, 0.22, 200)), (t_coin + 0.02, Z.cloche(2637, 0.12, 0.6)),
           (s(16) + 0.2, Z.alarme(0.07, 1)), (s(17) - 0.1, Z.cloche(880, 0.08)), (s(18), Z.whoosh(0.8, 0.08)),
           (s(18) + 0.3, Z.chirp(500, 1100, 0.6, 0.06)), (s(19) - 0.1, Z.cloche(988, 0.08)), (s(19) + 0.5, Z.whoosh(0.8, 0.09)),
           (s(19) + 0.6, Z.bulles(0.8, 0.07)), (s(20) + 0.6, Z.chirp(300, 800, 0.5, 0.06)),
           (s(20) + 1.0, Z.whoosh(0.4, 0.1, False)), (s(20) + 1.3, Z.crepitement(0.5, 0.15, 150)),
           (s(20) + 1.3, Z.bulles(1.5, 0.1)), (s(20) + 1.0, Z.cloche(1046.5, 0.1))]
    # la portière
    ev += [(s(22) + 1.4, Z.bulles(2.2, 0.1)), (s(22) + 1.4, Z.vent(2.0, 0.08, 100, 500)),
           (s(22) + 3.4, Z.grincement(0.8, 0.1)), (s(23), Z.boom(0.4, 50)), (s(23) + 0.4, Z.coeur(0.2)),
           (s(23) + 1.25, Z.coeur(0.2)), (s(23) + 1.4, Z.clang(140, 0.12, 1.2))]
    # la fenêtre, récap, question
    ev += [(s(24), Z.chirp(300, 1100, 0.6, 0.08)), (s(24) + 0.6, Z.whoosh(1.0, 0.09)), (s(24) + 1.4, Z.cloche(784, 0.1))]
    ev += [(s(25) + dt, Z.pince(f, 0.1)) for dt, f in zip((0.0, 0.84, 1.49, 2.15), (523.3, 659.3, 784, 1046.5))]
    ev += [(s(26), Z.boom(0.3, 70)), (s(26) + 0.05, Z.cloche(698.5, 0.1, 2.5)), (s(26) + 0.05, Z.cloche(880, 0.08, 2.5)),
           (s(28), Z.boom(0.35, 70)), (s(28), Z.chirp(500, 1000, 0.3, 0.07)), (s(29) + 0.2, Z.pince(784, 0.08)),
           (s(29) + 0.35, Z.pince(988, 0.08)), (s(29) + 0.5, Z.pince(1175, 0.08))]
    for t0, _, tr in tabs[1:]:
        ev.append((t0, {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
                        "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}[tr]()))
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep23_oscillo.mp4")
