"""Épisode 26 — « Six mois de suspension du permis… » (téléphone au volant, VRAI ou BLUFF) — style oscilloscope.

Une seule voix : le narrateur lit les phrases du policier (bulles) et rend un verdict par un tampon. Les 5 verdicts
se remplissent dans un tableau en haut de l'écran, du début à la fin. Fin coupée + « LA SUITE DEMAIN ▶ ».
Découpage : script.md. Dessins : films/illustrations (pol_*, cond_*, objets), outil planche_en_traits.

    python -m films.episodes.ep26_telephone_volant.oscillo_ep26 output/ep26.mp4
"""
import json
import math
import os
import sys

import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, P, W, cercle_pts, ease, ecrit, faisceau,
                                                         trace)
from films.outils.image_en_traits import DOSSIER, dessin
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
M.SEGS = os.path.join(HERE, "audio", "voix.json")
M.FPS = 24
s, e = M.s, M.e

SOL = 1500                                                                    # le sol
OFF_X, OFF_K = 830, 1.25                                                      # le policier
DRV_X, DRV_BAS, DRV_K = 330, 1400, 1.05                                       # le conducteur, dans la voiture
SLOTS = [("PAS", "FORCÉMENT"), ("VRAI",), ("VRAI SI", "NOTIFIÉ"), ("BLUFF",), ("PIÈGE",)]


# ------------------------------------------------------------------------------------------------ outils
_INFO = {}


def info(nom):
    if nom not in _INFO:
        _INFO[nom] = json.load(open(os.path.join(DOSSIER, nom + ".json")))
    return _INFO[nom]


def pose(nom, cx, bas, k):
    """Un personnage de la planche, à l'échelle commune k (pixels d'écran par pixel de planche), posé en (cx, bas)."""
    d = info(nom)
    w = d["px"][0] * k
    return dessin(nom, cx - w / 2, bas - w * d["ratio"], w)


def objet(nom, cx, cy, larg):
    d = info(nom)
    return dessin(nom, cx - larg / 2, cy - larg * d["ratio"] / 2, larg)


def u(t, t0, d):
    return ease(max(0.0, min(1.0, (t - t0) / d)))


def croix(cx, cy, r=34):
    return [[(cx - r, cy - r), (cx + r, cy + r)], [(cx + r, cy - r), (cx - r, cy + r)]]


def coche(cx, cy, r=34):
    return [[(cx - 0.8 * r, cy), (cx - 0.2 * r, cy + 0.7 * r), (cx + r, cy - 0.7 * r)]]


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]


def qui(tab, t):
    nom = None
    for t0, n in tab:
        if t >= t0:
            nom = n
    return nom


def tampon(c, t, t0, lignes, cx, cy, ang=-8, taille=74, col=AMBRE, t1=None):
    """Un tampon qui s'écrase sur l'écran (grossi, puis à sa taille) : VRAI, BLUFF…"""
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


def bulle(c, t, t0, t1, lignes, x, y, w, tx, ty, col=VERT_PALE, taille=38):
    """Une bulle de dialogue dont la queue pointe vers celui qui parle."""
    if t < t0 or t > t1:
        return
    h = 56 * len(lignes) + 36
    y = 905 - h                                                                # la bulle se pose au-dessus de la scène
    bx = min(max(tx, x + 50), x + w - 50)
    box = [rect(x, y, w, h), [(bx - 30, y + h), (tx, ty), (bx + 30, y + h)]]
    trace(c, t, t0, 0.25, box, col, 1.2, 0.9, bip=1100)
    for i, l in enumerate(lignes):
        ecrit(c, t, t0 + 0.15, l, x + w / 2, y + 20 + taille + 56 * i - 8, taille, col, True, 1.4, vitesse=0.02)


# ------------------------------------------------------------------------------------------------ le monde commun
def poses_pol():
    return [(s(3), "pol_index"), (s(6), "pol_pointe"), (s(8), "pol_bras"), (s(13), "pol_note"), (s(17), "pol_pointe"),
            (s(20), "pol_tend"), (s(22), "pol_debout"), (s(24), "pol_stop"), (s(25) + 0.6, "pol_debout"),
            (s(30), "pol_phone"), (s(38), None)]


def poses_cond():
    return [(s(3), "cond_regarde"), (s(6), "cond_surpris"), (s(8), "cond_volant"), (s(12), "cond_montre"),
            (s(14), "cond_volant"), (s(17) + 0.5, "cond_pense"), (s(22), "cond_volant"), (s(24), "cond_tend"),
            (s(25) + 0.3, "cond_coude"), (s(30), "cond_volant"), (s(32), "cond_hausse"), (s(34), "cond_pense")]


def tableau_verdicts(c, t):
    """Le tableau des 5 verdicts, en haut, du début à la fin : il se remplit tampon après tampon."""
    t0 = s(3)
    T = [s(7), s(13), s(20), s(25), s(33)]
    for i, lg in enumerate(SLOTS):
        x0 = 50 + 200 * i
        box = [rect(x0, 120, 180, 96)]
        v = u(t, t0 + 0.12 * i, 0.3)
        flash = s(38) + 0.25 * i <= t < s(38) + 0.25 * i + 0.25
        if t >= T[i]:
            col = AMBRE if i in (0, 3, 4) else VERT_PALE
            faisceau(c, box, 1.0, col, 1.8 if flash else 1.4, 1.0)
            for j, l in enumerate(lg):
                y = 178 if len(lg) == 1 else 164 + 30 * j
                ecrit(c, t, T[i], l, x0 + 90, y, 24, col, True, 1.4, vitesse=0.0)
        elif v > 0:
            faisceau(c, box, v, VERT, 0.8, 0.4)
            ecrit(c, t, t0, str(i + 1), x0 + 90, 186, 50, VERT, True, 1.0, vitesse=0.0)
        if s(4) + 0.2 * i <= t < s(4) + 0.2 * i + 0.2:                             # « voilà comment les reconnaître »
            faisceau(c, box, 1.0, VERT_PALE, 2.2, 1.0)


def monde(c, t):
    """La fenêtre de la voiture, le sol, le conducteur, le policier et le tableau des verdicts."""
    t0 = s(3)
    if t < t0:
        return
    fen = [[(70, 1400), (125, 1055), (570, 1055), (625, 1400)], [(35, 1400), (660, 1400)], [(35, 1400), (35, SOL)],
           [(660, 1400), (660, SOL)], [(0, SOL), (1080, SOL)]]
    trace(c, t, t0, 0.7, fen, VERT, 1.0, 0.8, bip=900)
    cn, pn = qui(poses_cond(), t), qui(poses_pol(), t)
    if cn:
        trace(c, t, t0 + 0.3, 0.8, pose(cn, DRV_X, DRV_BAS + 2 * math.sin(t * 2.2), DRV_K), VERT_PALE, 1.2, 1.0, bip=1100)
    if pn:
        k = 0.35 if s(26) <= t < s(30) else 1.0                                  # le policier n'a plus la main : le préfet
        trace(c, t, t0 + 0.5, 0.9, pose(pn, OFF_X + 3 * math.sin(t * 1.7), SOL, OFF_K), VERT_PALE, 1.2, k, bip=1300)
    tableau_verdicts(c, t)


# ------------------------------------------------------------------------------------------------ écrans
def e1(c, t):
    """Image 0 pleine : « 6 MOIS DE SUSPENSION » en grand et le téléphone en main ; le marteau barré, le calendrier."""
    f = 1 - u(t, s(3) - 0.4, 0.4)
    ecrit(c, t, -1.0, "6 MOIS", W / 2, 400, 170, AMBRE, True, 2.4, vitesse=0.0)
    ecrit(c, t, -1.0, "DE SUSPENSION", W / 2, 520, 84, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, -1.0, "DU PERMIS", W / 2, 610, 70, VERT_PALE, True, 1.8, vitesse=0.0)
    if f <= 0:
        return
    faisceau(c, objet("main_tel", W / 2, 1000, 420), 1.0, VERT_PALE, 1.3, f)
    if t >= s(1):
        trace(c, t, s(1), 0.5, objet("marteau", 250, 1420, 380), VERT_PALE, 1.2, f, bip=1500)
        trace(c, t, s(1) + 1.0, 0.2, croix(250, 1420, 120), AMBRE, 2.6, bip=500)
    if t >= s(2):
        trace(c, t, s(2), 0.5, objet("calendrier", 830, 1420, 330), VERT_PALE, 1.2, f, bip=1700)
        ecrit(c, t, s(2) + 0.3, "29 SEPT.", 830, 1230, 52, AMBRE, True, 1.6)


def e2(c, t):
    monde(c, t)
    ecrit(c, t, s(3) + 0.2, "VRAI OU BLUFF ?", W / 2, 400, 100, AMBRE, True, 2.2)
    if t > s(4):
        ecrit(c, t, s(4), "5 PHRASES DU POLICIER", W / 2, 500, 44, VERT_PALE, True, 1.5)


def e3(c, t):
    monde(c, t)
    ecrit(c, t, s(5), "PHRASE 1 / 5", W / 2, 330, 60, VERT_PALE, True, 1.6)
    bulle(c, t, s(6), s(8) + 0.2, ["VOUS ALLEZ PERDRE", "6 MOIS DE PERMIS"], 500, 600, 540, OFF_X, 950)
    tampon(c, t, s(7), ["PAS", "FORCÉMENT"], W / 2, 760, -9, 74, AMBRE, t1=s(8) + 0.4)
    if t >= s(8):
        y, x0, x1 = 800, 140, 940
        ticks = [[(x0 + (x1 - x0) * k / 6, y - 14), (x0 + (x1 - x0) * k / 6, y + 14)] for k in range(7)]
        trace(c, t, s(8), 0.5, [[(x0, y), (x1, y)]] + ticks, VERT, 1.2, 0.9, bip=1300)
        ecrit(c, t, s(8) + 0.2, "15 J", x0, y + 70, 44, VERT_PALE, True)
        ecrit(c, t, s(8) + 0.4, "6 MOIS", x1, y + 70, 44, AMBRE, True, 1.6)
        if t > s(8) + 0.9:
            ecrit(c, t, s(8) + 0.9, "MAXIMUM", x1, y - 50, 40, AMBRE, True, 1.6)
        sx = x0 + (x1 - x0) * u(t, s(9), e(9) - s(9))
        faisceau(c, [cercle_pts(sx, y, 18, 16)], 1.0, AMBRE, 2.0)
    if t >= s(10):
        trace(c, t, s(10), 0.6, objet("prefecture", W / 2, 610, 300), VERT_PALE, 1.2, bip=1500)
        ecrit(c, t, s(10) + 0.3, "LE PRÉFET DÉCIDE", W / 2, 940, 44, AMBRE, True, 1.6)


def barre_suspension(c, t, t0, y=600):
    x0, x1 = 140, 940
    ticks = [[(x0 + (x1 - x0) * k / 6, y - 10), (x0 + (x1 - x0) * k / 6, y + 10)] for k in range(7)]
    trace(c, t, t0, 0.4, [[(x0, y), (x1, y)]] + ticks, VERT, 1.0, 0.8, bip=1300)
    faisceau(c, [cercle_pts(x1, y, 14, 16)], 1.0, AMBRE, 1.8)


def e4(c, t):
    monde(c, t)
    ecrit(c, t, s(11), "PHRASE 2 / 5", W / 2, 330, 60, VERT_PALE, True, 1.6)
    bulle(c, t, s(12), s(13) + 0.3, ["ET LES", "3 POINTS ?"], 40, 620, 500, DRV_X, 1100)
    tampon(c, t, s(13), ["VRAI"], W / 2, 760, 7, 100, VERT_PALE, t1=s(14) + 0.1)
    if t >= s(14):
        trace(c, t, s(14), 0.5, objet("permis", 300, 760, 400), VERT_PALE, 1.2, bip=1500)
        trace(c, t, s(14) + 0.2, 0.5, objet("billets", 790, 760, 340), VERT_PALE, 1.2, bip=1700)
        ecrit(c, t, s(14) + 0.5, "135 €", 790, 930, 56, AMBRE, True, 1.6)
        n = 12
        for k in range(n):
            cx = 140 + 34 * k
            mort = k >= n - 3 and t >= s(14) + 1.3 + 0.12 * (k - (n - 3))
            faisceau(c, [cercle_pts(cx, 930, 13, 12)], 1.0, AMBRE if mort else VERT_PALE, 1.4, 0.5 if mort else 1.0)
            if mort:
                faisceau(c, croix(cx, 930, 10), 1.0, AMBRE, 1.8)
        ecrit(c, t, s(14) + 1.3, "- 3 POINTS", 300, 990, 40, AMBRE, True, 1.4)
    if t >= s(15):
        ecrit(c, t, s(15), "+ EN PLUS : LA SUSPENSION", W / 2, 540, 46, AMBRE, True, 1.6)
        barre_suspension(c, t, s(15) + 0.2)


def e5(c, t):
    monde(c, t)
    ecrit(c, t, s(16), "PHRASE 3 / 5", W / 2, 330, 60, VERT_PALE, True, 1.6)
    bulle(c, t, s(17), s(18) + 0.2, ["SI VOUS REPRENEZ", "LE VOLANT : 2 ANS", "DE PRISON"], 500, 560, 540, OFF_X, 950)
    tampon(c, t, s(18), ["VRAI"], 540, 820, -6, 100, VERT_PALE, t1=s(19) + 0.5)
    if s(19) <= t < s(21):
        trace(c, t, s(19), 0.6, objet("prison", 250, 760, 260), VERT_PALE, 1.2, 0.35 if t < s(20) else 1.0, bip=1500)
        ecrit(c, t, s(19) + 0.3, "2 ANS", 760, 780, 84, AMBRE, True, 1.8)
        ecrit(c, t, s(19) + 0.9, "4 500 €", 760, 870, 66, AMBRE, True, 1.6)
    if s(20) <= t < s(21):
        trace(c, t, s(20), 0.5, objet("lettre", 800, 590, 240), VERT_PALE, 1.2, bip=1900)
        tampon(c, t, s(20) + 0.6, ["SI NOTIFIÉ"], 500, 975, -5, 54, AMBRE, t1=s(21))
    if t >= s(21):
        trace(c, t, s(21), 0.5, objet("voiture", W / 2, 700, 380), VERT_PALE, 1.3, bip=1100)
        trace(c, t, s(21) + 1.4, 0.2, croix(W / 2, 700, 140), AMBRE, 2.8, bip=500)
        ecrit(c, t, s(21) + 1.6, "ON NE CONDUIT PAS", W / 2, 880, 50, AMBRE, True, 1.8)


def e6a(c, t):
    monde(c, t)
    ecrit(c, t, s(22), "PHRASE 4 / 5", W / 2, 330, 60, VERT_PALE, True, 1.6)
    ecrit(c, t, s(23), "LA GROSSE", W / 2, 440, 76, AMBRE, True, 2.0)
    bulle(c, t, s(24), s(25) + 0.6, ["VOTRE PERMIS EST", "SUSPENDU,", "LÀ, MAINTENANT"], 500, 560, 540, OFF_X, 950)


def e6b(c, t):
    monde(c, t)
    ecrit(c, t, s(22), "PHRASE 4 / 5", W / 2, 330, 60, VERT_PALE, True, 1.6)
    bulle(c, t, s(24), s(25) + 0.6, ["VOTRE PERMIS EST", "SUSPENDU,", "LÀ, MAINTENANT"], 500, 560, 540, OFF_X, 950)
    tampon(c, t, s(25), ["BLUFF"], W / 2, 770, 8, 150, AMBRE, t1=s(26) + 0.9)
    trace(c, t, s(26) + 0.3, 0.2, croix(OFF_X, 1230, 100), AMBRE, 2.6, bip=500)
    if t >= s(26) + 1.2:
        trace(c, t, s(26) + 1.2, 0.6, objet("prefecture", W / 2, 740, 280), VERT_PALE, 1.2, bip=1500)
        ecrit(c, t, s(26) + 1.5, "LE PRÉFET", W / 2, 905, 50, AMBRE, True, 1.6)
    if t >= s(27):
        v = u(t, s(27) + 0.3, 1.4)                                                # la lettre voyage jusqu'à la fenêtre
        cx, cy = W / 2 + (330 - W / 2) * v, 740 + (960 - 740) * v
        trace(c, t, s(27), 0.4, objet("lettre", cx, cy, 200), VERT_PALE, 1.3, bip=1900)
        if t < s(27) + 1.8:
            ecrit(c, t, s(27) + 0.1, "IL VOUS PRÉVIENT", W / 2, 990, 44, VERT_PALE, True, 1.4)
        else:
            ecrit(c, t, s(27) + 1.8, "VOUS RÉPONDEZ", W / 2, 990, 44, AMBRE, True, 1.6)
    if t >= s(28):
        ecrit(c, t, s(28), "CONSEIL D'ÉTAT", W / 2, 450, 48, VERT_PALE, True, 1.5)
        ecrit(c, t, s(28) + 0.4, "24 MAI 2024", W / 2, 520, 58, AMBRE, True, 1.6)
    if t >= s(29):
        ecrit(c, t, s(29), "SAUF URGENCE", W / 2, 590, 40, VERT, True, 1.3)


def e7(c, t):
    monde(c, t)
    ecrit(c, t, s(30), "PHRASE 5 / 5", W / 2, 330, 60, VERT_PALE, True, 1.6)
    ecrit(c, t, s(31), "LA TENTATION", W / 2, 440, 72, AMBRE, True, 2.0)
    bulle(c, t, s(32), s(33) + 0.3, ["JE L'AI JUSTE TOUCHÉ,", "PAS TENU"], 40, 600, 540, DRV_X, 1100)
    tampon(c, t, s(33), ["PIÈGE"], W / 2, 760, -8, 130, AMBRE, t1=s(34) + 0.3)
    if t >= s(34) + 0.3:
        f = 1 - u(t, s(35), 0.4)
        if f > 0:
            ecrit(c, t, s(34) + 0.3, "TENU EN MAIN", 310, 545, 42, VERT_PALE, True, 1.4)
            faisceau(c, objet("main_tel", 310, 790, 290), 1.0, VERT_PALE, 1.3, f)
            trace(c, t, s(34) + 1.2, 0.2, croix(310, 790, 110), AMBRE, 2.6, bip=500)
    if t >= s(35):
        ecrit(c, t, s(35), "SUR UN SUPPORT", 310, 545, 42, VERT_PALE, True, 1.4)
        trace(c, t, s(35), 0.5, objet("tel_support", 310, 790, 380), VERT_PALE, 1.3, bip=1700)
        trace(c, t, s(35) + 1.0, 0.3, coche(500, 640, 40), VERT_PALE, 3.0, bip=1600)
    if t >= s(36):
        lignes = [("SUPPORT", s(35) + 1.0, True, 700), ("NAVIGATION", s(36) + 1.9, True, 790),
                  ("ÉCRAN : AUTRE USAGE", s(36) + 1.0, False, 880)]
        for txt, tl, ok, y in lignes:
            if t >= tl:
                col = VERT_PALE if ok else AMBRE
                ecrit(c, t, tl, txt, 625, y, 34, col, False, 1.4)
                trace(c, t, tl, 0.25, coche(590, y - 12, 22) if ok else croix(590, y - 12, 20), col, 2.4, bip=1700 if ok else 500)
    if t >= s(37):
        ecrit(c, t, s(37), "UNE AUTRE INFRACTION", 420, 1010, 44, AMBRE, True, 1.6)


def e8(c, t):
    monde(c, t)
    trace(c, t, s(38), 0.6, objet("lettre", W / 2, 760, 440), VERT_PALE, 1.4, bip=1900)
    ecrit(c, t, s(38) + 0.6, "?", W / 2, 800, 190, AMBRE, True, 2.4, vitesse=0.0)
    ecrit(c, t, s(38), "LA LETTRE DU PRÉFET", W / 2, 330, 56, VERT_PALE, True, 1.6)
    if t >= s(39):
        ecrit(c, t, s(39), "L'ERREUR QUE PRESQUE", W / 2, 420, 54, VERT_PALE, True, 1.6)
        ecrit(c, t, s(39) + 0.6, "TOUT LE MONDE COMMET", W / 2, 490, 54, AMBRE, True, 1.8)
    if t >= s(40):
        ecrit(c, t, s(40), "ELLE PEUT COÛTER LES 6 MOIS", W / 2, 1010, 40, AMBRE, True, 1.6)
    if t >= s(41):
        ecrit(c, t, s(41), "PROCHAINE VIDÉO ▶", W / 2, 560, 52, AMBRE, True, 1.8)


def e9(c, t):
    """Coupé au milieu de la phrase : la suite demain."""
    c.drawRect(skia.Rect(0, 0, W, M.H), P((40, 18, 4), 0, 255, fill=True))
    ecrit(c, t, -1, "ET QUAND LA LETTRE", W / 2, 800, 66, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, -1, "DU PRÉFET ARRIVE ?", W / 2, 890, 66, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, -1, "LA SUITE DEMAIN ▶", W / 2 + 14 * abs(math.sin(t * 5)), 1110, 62, VERT_PALE, True, 2.0, vitesse=0.0)
    ecrit(c, t, -1, "INFORMATION GÉNÉRALE, PAS UN CONSEIL JURIDIQUE", W / 2, 1450, 24, VERT, True, 1.2, vitesse=0.0)


def tableaux():
    return [(0.0, e1, None), (s(3) - 0.1, e2, None), (s(5), e3, None), (s(11), e4, None), (s(16), e5, None),
            (s(22), e6a, None), (s(25) - 0.05, e6b, "glitch"), (s(30), e7, None), (s(38), e8, "balayage"),
            (e(42) + 0.05, e9, None)]


def chocs():
    T = [s(7), s(13), s(18), s(25), s(33)]
    flashs = T + [s(20) + 0.6, e(42) + 0.05]
    secousses = [(t, 0.2) for t in T] + [(s(20) + 0.6, 0.12), (e(42) + 0.05, 0.3)]
    return flashs, secousses


def effets(tabs):
    ev = [(0.0, Z.vibration(1.4, 0.1)), (0.0, Z.craquement(0.3)), (0.05, Z.boom(0.5, 60)), (s(1), Z.craquement(0.3)),
          (s(1) + 1.0, Z.thump(0.35)), (s(2), Z.cloche(784, 0.08)), (s(2) + 0.3, Z.pince(988, 0.08)),
          (s(3), Z.whoosh(0.6, 0.07)), (s(3), Z.vent(10.0, 0.04, 100, 500)), (s(3) + 0.8, Z.cliquet(0.1))]
    ev += [(s(4) + 0.2 * i, Z.pince(523.3 * 2 ** (i * 2 / 12), 0.08)) for i in range(5)]
    T = [s(7), s(13), s(18), s(25), s(33)]
    for t in T:
        ev += [(t, Z.boom(0.5, 70)), (t, Z.snap(0.35))]
    ev += [(s(7) + 0.1, Z.pince(523.3, 0.1)), (s(13) + 0.1, Z.pince(659.3, 0.1)), (s(20) + 0.6, Z.pince(784, 0.1)),
           (s(25) + 0.1, Z.pince(392, 0.1)), (s(33) + 0.1, Z.pince(988, 0.1))]
    ev += [(s(8), Z.tictac(1.6, 0.06, 0.3)), (s(9), Z.chirp(300, 900, e(9) - s(9), 0.06)), (s(10), Z.cloche(698.5, 0.08))]
    ev += [(s(14) + 1.3 + 0.12 * k, Z.cliquet(0.1)) for k in range(3)] + [(s(15), Z.riser(0.7, 0.07))]
    ev += [(s(19), Z.thump(0.35)), (s(20), Z.whoosh(0.5, 0.08)), (s(20) + 0.6, Z.thump(0.4)),
           (s(21) + 1.4, Z.thump(0.4)), (s(21) + 1.6, Z.alarme(0.05, 1))]
    ev += [(s(24) - 0.2, Z.riser(e(24) - s(24) + 0.2, 0.07)), (s(26) + 0.3, Z.thump(0.4)), (s(26) + 1.2, Z.cloche(587.3, 0.08)),
           (s(27), Z.whoosh(0.7, 0.1)), (s(28), Z.pince(659.3, 0.08)), (s(29), Z.scintillement(0.8, 0.05))]
    ev += [(s(34) + 1.2, Z.thump(0.35)), (s(35), Z.whoosh(0.4, 0.08)), (s(35) + 1.0, Z.cloche(880, 0.08)),
           (s(36) + 1.0, Z.thump(0.3)), (s(36) + 1.9, Z.cloche(880, 0.08)), (s(37), Z.riser(e(37) - s(37), 0.07))]
    ev += [(s(38), Z.whoosh(0.5, 0.08)), (s(38) + 0.6, Z.chirp(400, 800, 0.4, 0.07)), (s(39), Z.riser(e(40) - s(39), 0.08)),
           (e(42) + 0.05, Z.boom(0.6, 50)), (e(42) + 0.05, Z.arret_bande(0.5, 0.2))]
    sons = {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
            "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}
    ev += [(t0, sons[tr]()) for t0, _, tr in tabs[1:] if tr]
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep26.mp4")
