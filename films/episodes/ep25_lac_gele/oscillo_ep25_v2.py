"""Épisode 25 v2 — « Surtout… ne marchez pas » — style oscilloscope, découpage enchaîné (script_v2.md).

Chaque écran naît du précédent : la ligne de glace (toujours en bas), le compteur « 50 M » jusqu'au bord, la flèche
de poussée et le chronomètre de l'énigme reviennent d'un bout à l'autre. Le bord est à gauche : il lance sa chaussure
vers la droite et glisse vers la gauche. Fin coupée au milieu d'une phrase + « LA SUITE DEMAIN ▶ ».

    python -m films.episodes.ep25_lac_gele.oscillo_ep25_v2 output/ep25_v2.mp4
"""
import json
import math
import os
import sys

import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, P, W, cercle_pts, ease, ecrit, faisceau,
                                                         fleche, pointilles, trace)
from films.outils.image_en_traits import DOSSIER, dessin
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "audio", "voix_v2.mp3")
M.SEGS = os.path.join(HERE, "audio", "voix_v2.json")
s, e = M.s, M.e
SOL = 1330                                                                    # la ligne de glace
X0 = 700                                                                      # où il est coincé
BORD = 110                                                                    # le bord, à gauche
HAUT = 520


# ------------------------------------------------------------------------------------------------ outils
def ratio(nom):
    return json.load(open(os.path.join(DOSSIER, nom + ".json")))["ratio"]


def centre(nom, cx, cy, largeur, miroir=False):
    return dessin(nom, cx - largeur / 2, cy - largeur * ratio(nom) / 2, largeur, miroir)


def perso(nom, cx, haut=HAUT, pied=SOL, miroir=False):
    larg = haut / ratio(nom)
    return dessin(nom, cx - larg / 2, pied - haut, larg, miroir)


def bouge(tr, dx=0.0, dy=0.0):
    return [[(x + dx, y + dy) for x, y in l] for l in tr]


def tourne(tr, cx, cy, a):
    ca, sa = math.cos(a), math.sin(a)
    return [[(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in l] for l in tr]


def camera(tr, z, fx, fy, cx=W / 2, cy=960):
    return [[(cx + (x - fx) * z, cy + (y - fy) * z) for x, y in l] for l in tr]


def croix(cx, cy, r=34):
    return [[(cx - r, cy - r), (cx + r, cy + r)], [(cx + r, cy - r), (cx - r, cy + r)]]


def u(t, t0, d):
    return ease(max(0.0, min(1.0, (t - t0) / d)))


def glace(c, t, x0=40, x1=1040, intense=0.9, lisse=True, cam=None):
    """Le fil conducteur : la ligne de glace, avec ses reflets qui défilent (glace) ou ses hachures (sol normal)."""
    tr = [[(x0, SOL), (x1, SOL)]]
    if lisse:
        for k in range(6):
            x = x0 + ((k * 173 + t * 60) % (x1 - x0 - 80))
            tr.append([(x, SOL + 18 + 7 * (k % 3)), (x + 40 + 8 * k, SOL + 18 + 7 * (k % 3))])
    else:
        tr += [[(x, SOL), (x - 26, SOL + 26)] for x in range(x0 + 30, x1, 46)]
    faisceau(c, camera(tr, *cam) if cam else tr, 1.0, VERT, 1.1, intense)


def bord(c, t, t0, x=BORD, cam=None):
    tr = [[(x, SOL - 260), (x, SOL + 40)]] + [[(x - 60 + 12 * k, SOL - 120 + 30 * k), (x, SOL - 140 + 30 * k)] for k in range(5)]
    if t >= t0:
        faisceau(c, camera(tr, *cam) if cam else tr, ease((t - t0) / 0.4), VERT_PALE, 1.1)
        if not cam:
            ecrit(c, t, t0 + 0.2, "BORD", x + 20, SOL - 290, 34, VERT, True, 1.2)


def compteur_bord(c, t, t0, metres, x=None, y=SOL + 90, taille=60, col=AMBRE):
    """Le compteur de distance au bord, posé sur la ligne de glace."""
    if t < t0:
        return
    x = (BORD + X0) / 2 if x is None else x
    trace(c, t, t0, 0.3, [[(BORD + 10, y - 60), (X0 - 60, y - 60)]] + fleche(X0 - 60, y - 60, BORD + 10, y - 60, 18),
          VERT, 0.8, 0.7, bip=1500)
    ecrit(c, t, t0, f"{metres:.0f} M" if metres >= 1 else f"{metres * 100:.0f} CM", x, y, taille, col, True, 1.6,
          vitesse=0.0)


CHRONO = (960, 230)


def chrono(c, t, t0=None, x=CHRONO[0], y=CHRONO[1], r=46):
    """Le chronomètre de l'énigme : il tourne de « un seul geste » jusqu'à la solution."""
    t0 = s(8) if t0 is None else t0
    if t < t0:
        return
    k = min(1.0, (t - t0) / (s(22) - t0))
    faisceau(c, [cercle_pts(x, y, r, 40)], 1.0, VERT, 0.8, 0.6)
    a = -math.pi / 2 + 2 * math.pi * k
    pts = [(x + r * math.cos(-math.pi / 2 + (a + math.pi / 2) * j / 30), y + r * math.sin(-math.pi / 2 + (a + math.pi / 2) * j / 30))
           for j in range(31)]
    faisceau(c, [pts], 1.0, AMBRE, 1.6)
    faisceau(c, [[(x, y), (x + 0.8 * r * math.cos(a), y + 0.8 * r * math.sin(a))]], 1.0, AMBRE, 1.2)


def horloge(c, x, y, r, tours, col=VERT_PALE):
    """Une horloge dont les aiguilles tournent `tours` fois (le temps qui passe en accéléré)."""
    faisceau(c, [cercle_pts(x, y, r, 40)], 1.0, col, 1.0, 0.8)
    for k in range(12):
        a = k * math.pi / 6
        faisceau(c, [[(x + 0.85 * r * math.cos(a), y + 0.85 * r * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a))]],
                 1.0, col, 0.8, 0.6)
    for lg, v in ((0.5, 1 / 12), (0.8, 1.0)):
        a = -math.pi / 2 + 2 * math.pi * tours * v
        faisceau(c, [[(x, y), (x + lg * r * math.cos(a), y + lg * r * math.sin(a))]], 1.0, AMBRE, 1.6)


def grille(n, x0, y0, cote, par_ligne, gap=6):
    """n carrés : la masse rendue visible."""
    return [[(x0 + (k % par_ligne) * (cote + gap) + a, y0 + (k // par_ligne) * (cote + gap) + b)
             for a, b in ((0, 0), (cote, 0), (cote, cote), (0, cote), (0, 0))] for k in range(n)]


# ------------------------------------------------------------------------------------------------ écrans
def e01(c, t):
    """Plan d'ensemble, zoom avant lent : il est minuscule au milieu du lac. Le titre est là dès l'image 0."""
    z = 0.8 + 0.2 * u(t, 0, 2.5)
    cam = (z, X0, SOL - 200, X0 - (X0 - W / 2) * (1 - z), SOL - 200)
    faisceau(c, camera(dessin("lac", -70, 650, 1220), *cam), 1.0, VERT, 0.9, 0.5)
    faisceau(c, camera(perso("perso_debout", X0 + 5 * math.sin(t * 9) * (1 - u(t, 0, 3))), *cam), 1.0, VERT_PALE, 1.3)
    k = 1 + 0.05 * abs(math.sin(t * 6)) if t > s(1) else 1.0
    ecrit(c, t, -1.0, "SURTOUT…", W / 2, 300, 70, VERT_PALE, True, 1.8, vitesse=0.0)
    ecrit(c, t, -1.0, "NE MARCHEZ", W / 2, 420, int(118 * k), AMBRE, True, 2.4, vitesse=0.0)
    ecrit(c, t, -1.0, "PAS", W / 2, 540, int(118 * k), AMBRE, True, 2.4, vitesse=0.0)


def e02(c, t):
    """Le lac s'efface : il ne reste que la ligne de glace sous ses pieds."""
    v = u(t, s(2), 0.8)
    faisceau(c, dessin("lac", -70, 650, 1220), 1.0, VERT, 0.9, 0.5 * (1 - v))
    glace(c, t, X0 - 340 * v - 60, X0 + 340 * v + 60, 0.4 + 0.5 * v)
    faisceau(c, perso("perso_debout", X0), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(2) + 0.2, "GLACE PARFAITEMENT LISSE", W / 2, 330, 52, VERT_PALE, True, 1.6)
    ecrit(c, t, s(2) + 1.0, "FROTTEMENT = 0", W / 2, 430, 74, AMBRE, True, 2.0)


def e03(c, t):
    """La ligne file vers la gauche jusqu'au bord ; le compteur 50 M se pose dessus."""
    v = u(t, s(3), 0.7)
    glace(c, t, X0 - 400 - (X0 - 400 - 40) * v, 1040)
    faisceau(c, perso("perso_debout", X0), 1.0, VERT_PALE, 1.3)
    bord(c, t, s(3) + 0.6)
    compteur_bord(c, t, s(3) + 0.8, 50)


ESSAIS = [("MARCHER", 4), ("RAMPER", 5), ("SAUTER", 6)]


def liste_essais(c, t):
    for k, (nom, i) in enumerate(ESSAIS):
        if t > s(i):
            x = 210 + 330 * k
            ecrit(c, t, s(i), nom, x, 330, 56, VERT_PALE, True, 1.4, vitesse=0.0)
            if t > e(i) - 0.4:
                trace(c, t, e(i) - 0.4, 0.2, croix(x, 312, 40), AMBRE, 2.0, bip=500)


def e04(c, t):
    """Les trois essais sur la même ligne ; le compteur reste bloqué à 50 M."""
    glace(c, t)
    bord(c, t, -1)
    liste_essais(c, t)
    if t < s(5):
        w = t - s(4)
        faisceau(c, perso("perso_glisse", X0 + 16 * math.sin(w * 12)), 1.0, VERT_PALE, 1.3)
    elif t < s(6):
        faisceau(c, perso("perso_rampe", X0 + 12 * math.sin((t - s(5)) * 12), 300), 1.0, VERT_PALE, 1.3)
    else:
        h = 240 * abs(math.sin((t - s(6)) * 2.4))
        faisceau(c, perso("perso_saut", X0, HAUT, SOL - h), 1.0, VERT_PALE, 1.3)
        faisceau(c, croix(X0, SOL + 4, 16), 1.0, AMBRE, 1.4)
    flash = any(e(i) - 0.4 < t < e(i) - 0.1 for _, i in ESSAIS)                # le compteur clignote : toujours 50 M
    compteur_bord(c, t, -1, 50, col=VERT_PALE if flash else AMBRE)


def e05(c, t):
    """Le compteur monte dans le coin et devient le chronomètre de l'énigme."""
    glace(c, t)
    bord(c, t, -1)
    faisceau(c, perso("perso_reflechit", X0, 560), 1.0, VERT_PALE, 1.3)
    v = u(t, s(8) - 0.3, 0.5)
    if v < 1:
        x = (BORD + X0) / 2 + (CHRONO[0] - (BORD + X0) / 2) * v
        y = SOL + 90 + (CHRONO[1] + 20 - SOL - 90) * v
        ecrit(c, t, -1, "50 M", x, y, int(60 - 30 * v), AMBRE, True, 1.6, vitesse=0.0)
    chrono(c, t)
    ecrit(c, t, s(7), "UN SEUL GESTE", W / 2, 400, 92, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, s(8), "AVANT LA FIN DE LA VIDÉO", W / 2, 500, 50, VERT_PALE, True, 1.5)


def e06(c, t):
    """Il se tortille ; la croix de son centre reste fixe sur la ligne."""
    glace(c, t)
    bord(c, t, -1)
    chrono(c, t)
    w = t - s(9)
    corps = tourne(perso("perso_debout", X0), X0, SOL - 240, 0.22 * math.sin(w * 7))
    faisceau(c, bouge(corps, -25 * math.sin(w * 7)), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(9), "SE TORTILLER ?", W / 2, 330, 66, VERT_PALE, True, 1.6)
    if t > s(9) + 1.2:
        g = (X0, SOL - 250)
        trace(c, t, s(9) + 1.2, 0.3, [cercle_pts(*g, 16, 20), [(g[0] - 34, g[1]), (g[0] + 34, g[1])],
                                      [(g[0], g[1] - 34), (g[0], g[1] + 34)]], AMBRE, 1.6, bip=1700)
        trace(c, t, s(9) + 1.6, 0.3, pointilles(g[0], g[1] + 34, g[0], SOL), AMBRE, 1.0, bip=0)
        ecrit(c, t, s(9) + 2.6, "0 MM", g[0], SOL + 90, 64, AMBRE, True, 1.8, vitesse=0.0)


def e07(c, t):
    """La croix devient le zéro d'une règle ; il souffle et avance d'un trait ; l'horloge s'emballe."""
    glace(c, t)
    bord(c, t, -1)
    chrono(c, t)
    w = t - s(10)
    dx = -6 * u(t, s(10) + 0.4, 1.4)
    faisceau(c, perso("perso_debout", X0 + dx, miroir=True), 1.0, VERT_PALE, 1.3)
    regle = [[(X0 - 200 + 8 * k, SOL + 40), (X0 - 200 + 8 * k, SOL + (64 if k % 5 == 0 else 52))] for k in range(51)]
    faisceau(c, regle + [[(X0 - 200, SOL + 40), (X0 + 200, SOL + 40)]], 1.0, VERT, 0.8)
    faisceau(c, croix(X0, SOL + 30, 10), 1.0, AMBRE, 1.4)
    for k in range(4):
        ph = (w * 1.6 + k / 4) % 1
        x0 = X0 + 70 + 260 * ph
        faisceau(c, [[(x0, SOL - 450 + 24 * k), (x0 + 80, SOL - 450 + 24 * k)]], 1.0, VERT_PALE, 1.2, 1 - ph)
    ecrit(c, t, s(10), "SOUFFLER ?", W / 2, 330, 66, VERT_PALE, True, 1.6)
    ecrit(c, t, s(10) + 1.0, "1 MM", X0 - 60, SOL + 130, 56, AMBRE, True, 1.6)
    if t > s(11):
        horloge(c, 300, 700, 120, 30 * u(t, s(11), e(11) - s(11)))
        ecrit(c, t, s(11) + 1.0, "DES HEURES", 300, 900, 56, AMBRE, True, 1.6)


def pas_normal(c, t, x, cam=None):
    faisceau(c, camera(perso("perso_debout", x, 560), *cam) if cam else perso("perso_debout", x, 560), 1.0, VERT_PALE, 1.3)


def e08(c, t):
    """La glace redevient un sol normal : on pousse derrière soi."""
    glace(c, t, lisse=False)
    pas_normal(c, t, X0 - 40 * u(t, s(13), 1.2))
    ecrit(c, t, s(12), "IL FAUT COMPRENDRE UN TRUC", W / 2, 330, 48, VERT_PALE, True, 1.4)
    ecrit(c, t, s(13), "ON NE POUSSE PAS DEVANT", W / 2, 430, 52, VERT_PALE, True, 1.5)
    if t > s(13) + 1.9:
        ecrit(c, t, s(13) + 1.9, "ON POUSSE DERRIÈRE", W / 2, 520, 64, AMBRE, True, 1.8)


def e09(c, t):
    """Flèche ambre : le pied pousse le sol vers l'arrière. Elle rebondit : flèche verte, le sol le pousse en avant."""
    glace(c, t, lisse=False)
    x = X0 - 40 - 40 * u(t, s(15), 1.4)
    pas_normal(c, t, x)
    trace(c, t, s(14) + 0.6, 0.4, fleche(x - 20, SOL - 20, x - 260, SOL - 20, 28), AMBRE, 2.2, bip=800)
    ecrit(c, t, s(14) + 0.6, "LE PIED POUSSE LE SOL", x - 150, SOL + 80, 36, AMBRE, True, 1.4)
    if t > s(15):
        trace(c, t, s(15), 0.4, fleche(x + 60, SOL - 300, x - 240, SOL - 300, 30), VERT_PALE, 2.4, bip=1300)
        ecrit(c, t, s(15) + 0.2, "LE SOL VOUS POUSSE", W / 2, 520, 52, VERT_PALE, True, 1.6)


def e10(c, t):
    """Le sol redevient glace : la flèche ambre glisse dans le vide, la verte est barrée."""
    glace(c, t)
    x = X0 - 80
    faisceau(c, perso("perso_glisse", x, HAUT), 1.0, VERT_PALE, 1.3)
    v = u(t, s(16) + 0.3, 1.5)
    faisceau(c, fleche(x - 20 - 300 * v, SOL - 20, x - 260 - 300 * v, SOL - 20, 28), 1.0, AMBRE, 2.0, 1 - 0.7 * v)
    faisceau(c, fleche(x + 60, SOL - 300, x - 240, SOL - 300, 30), 1.0, VERT_PALE, 1.4, 0.4)
    trace(c, t, s(16) + 1.6, 0.2, croix(x - 90, SOL - 300, 60), AMBRE, 2.6, bip=500)
    ecrit(c, t, s(16) + 2.0, "PLUS RIEN À POUSSER", W / 2, 430, 56, AMBRE, True, 1.6)


def e11(c, t):
    """La caméra remonte des pieds au bonnet ; des « ? » se posent sur lui ; on redescend sur la chaussure."""
    w = t - s(17)
    fy = SOL - 40 - 420 * u(t, s(17) + 0.4, 1.0) + 420 * u(t, s(17) + 1.6, 0.6)
    cam = (1.6, X0, fy, W / 2, 1000)
    glace(c, t, cam=cam)
    faisceau(c, camera(perso("perso_debout", X0), *cam), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(17), "RIEN…", W / 2, 330, 96, AMBRE, True, 2.0, vitesse=0.0)
    ecrit(c, t, s(17) + 0.7, "SAUF CE QUE VOUS AVEZ SUR VOUS", W / 2, 1560, 44, VERT_PALE, True, 1.5)
    if w > 1.9:
        cx, cy = camera([[(X0 - 40, SOL - 22)]], *cam)[0][0]
        trace(c, t, s(17) + 1.9, 0.3, [cercle_pts(cx, cy, 120, 36)], AMBRE, 2.0, bip=1700)
        ecrit(c, t, s(17) + 2.0, "?", cx + 160, cy - 110, 110, AMBRE, True, 2.0, vitesse=0.0)


def e12(c, t):
    """La glace s'efface, il se met à flotter… et devient l'astronaute dans la station."""
    v = u(t, s(18), 1.0)
    if v < 1:
        glace(c, t, intense=0.9 * (1 - v))
        faisceau(c, tourne(perso("perso_debout", X0, HAUT, SOL - 200 * v), X0, SOL - 260, 0.5 * v), 1.0, VERT_PALE, 1.3, 1 - v)
    m = u(t, s(18) + 0.6, 1.4)
    faisceau(c, camera(centre("module", W / 2, 960, 1060), 0.8 + 0.6 * m, W / 2, 960), 1.0, VERT, 0.7, 0.35 * m)
    if m > 0:
        a = 0.2 * math.sin((t - s(18)) * 0.9)
        astro = tourne(centre("astronaute_flotte", W / 2, 980 + 15 * math.sin(t * 1.3), 420), W / 2, 980, a)
        faisceau(c, astro, 1.0, VERT_PALE, 1.2, m)
    c.drawRect(skia.Rect(0, 230, W, 400), P((2, 8, 4), 0, 220, fill=True))
    ecrit(c, t, s(18), "LES ASTRONAUTES", W / 2, 330, 66, VERT_PALE, True, 1.6)
    if t > s(19) + 1.6:
        for x0, x1 in ((W / 2 - 230, 70), (W / 2 + 230, W - 70)):
            trace(c, t, s(19) + 1.6, 0.4, fleche(x0, 980, x1, 980, 24), AMBRE, 1.2, bip=1500)
        ecrit(c, t, s(19) + 2.4, "RIEN POUR S'AGRIPPER", W / 2, 1420, 44, VERT_PALE, True, 1.5)
    chrono(c, t)


def e13(c, t):
    """Coupe au noir : seul reste le chronomètre, qui arrive au bout."""
    ecrit(c, t, s(20), "LA MÊME SOLUTION", W / 2, 700, 72, AMBRE, True, 1.8)
    chrono(c, t, x=W / 2, y=960, r=90)
    ecrit(c, t, s(21), "VOUS L'AVEZ TROUVÉE ?", W / 2, 1200, 64, AMBRE, True, 2.0)


def e14(c, t):
    """Retour sur la glace : il enlève sa chaussure, elle s'allume ; il la lance vers la droite."""
    glace(c, t)
    bord(c, t, -1)
    compteur_bord(c, t, -1, 50, col=VERT)
    if t < s(23):
        faisceau(c, perso("perso_enleve", X0, 560), 1.0, VERT_PALE, 1.3)
        if t > s(22) + 0.5:
            trace(c, t, s(22) + 0.5, 0.3, [cercle_pts(X0 - 120, SOL - 205, 70, 30)], AMBRE, 1.8, bip=1700)
        ecrit(c, t, s(22), "ENLEVEZ VOTRE CHAUSSURE", W / 2, 330, 58, AMBRE, True, 1.8)
        return
    corps = [l for l in perso("perso_lance", X0, 470)
             if not (min(p[0] for p in l) > X0 + 0.2 * 423 and max(p[1] for p in l) < SOL - 470 + 0.11 * 423)]
    faisceau(c, corps, 1.0, VERT_PALE, 1.3)
    w = max(0.0, t - s(23) - 0.6)
    x = X0 + 200 + 620 * w
    if x < 1200:
        faisceau(c, tourne(centre("chaussure", x, 900 + 50 * w * w, 120), x, 900, w * 9), 1.0, AMBRE, 1.5)
    ecrit(c, t, s(23), "LANCEZ-LA !", W / 2, 330, 84, AMBRE, True, 2.0)
    ecrit(c, t, s(23) + 1.6, "À L'OPPOSÉ DU BORD →", W / 2, 430, 46, VERT_PALE, True, 1.5)


def glisse_x(t):
    """Sa position quand il glisse vers le bord (à gauche), du lancer jusqu'à l'arrivée."""
    if t < s(24):
        return X0
    x29 = X0 - 4 * (s(29) - s(24))                                            # 7 cm/s : il bouge à peine
    if t < s(29):
        return X0 - 4 * (t - s(24))
    return x29 - (x29 - BORD - 120) * u(t, s(29) + 0.3, e(30) - s(29) - 0.8)


def e15(c, t):
    """Il part dans l'autre sens ; la flèche revient : ambre sur la chaussure, verte sur lui."""
    glace(c, t)
    bord(c, t, -1)
    x = glisse_x(t)
    faisceau(c, perso("perso_glisse_dos", x, 400, miroir=True), 1.0, VERT_PALE, 1.3)
    faisceau(c, centre("chaussure", 960, 900, 110), 1.0, AMBRE, 1.4)
    trace(c, t, s(24) + 0.2, 0.4, fleche(840, 1040, 1020, 1040, 26), AMBRE, 2.2, bip=800)
    trace(c, t, s(24) + 0.5, 0.4, fleche(x - 40, SOL - 460, x - 220, SOL - 460, 26), VERT_PALE, 2.2, bip=1300)
    ecrit(c, t, s(24), "VOUS PARTEZ DANS L'AUTRE SENS", W / 2, 330, 46, VERT_PALE, True, 1.5)
    compteur_bord(c, t, -1, 50, col=VERT)


def e16(c, t):
    """Les flèches se figent en schéma : action, réaction."""
    glace(c, t, intense=0.5)
    x = glisse_x(t)
    faisceau(c, perso("perso_glisse_dos", x, 400, miroir=True), 1.0, VERT_PALE, 1.1, 0.8)
    faisceau(c, centre("chaussure", 960, 900, 110), 1.0, AMBRE, 1.4)
    faisceau(c, fleche(840, 1040, 1020, 1040, 26), 1.0, AMBRE, 2.2)
    faisceau(c, fleche(x - 40, SOL - 460, x - 220, SOL - 460, 26), 1.0, VERT_PALE, 2.2)
    ecrit(c, t, s(25), "VOUS POUSSEZ LA CHAUSSURE", W / 2, 330, 48, AMBRE, True, 1.5)
    ecrit(c, t, s(25) + 1.3, "LA CHAUSSURE VOUS POUSSE", W / 2, 410, 48, VERT_PALE, True, 1.5)
    ecrit(c, t, s(26), "3e LOI DE NEWTON", W / 2, 560, 72, AMBRE, True, 2.0)


def e17(c, t):
    """Les masses en carrés : 1 pour la chaussure, 140 pour lui ; les vitesses en compteur sous chaque flèche."""
    v = u(t, s(27), 0.6)
    faisceau(c, grille(1, 820, 760, 26, 1), v, AMBRE, 1.6)
    ecrit(c, t, s(27) + 0.2, "0,5 KG", 833, 850, 40, AMBRE, True, 1.4)
    trace(c, t, s(27) + 0.6, 0.4, fleche(860, 773, 1040, 773, 24), AMBRE, 2.4, bip=800)
    vit = 10 * u(t, s(27) + 1.2, 1.0)
    ecrit(c, t, s(27) + 1.2, f"{vit:.0f} M/S", 950, 720, 52, AMBRE, True, 1.6, vitesse=0.0)
    if t > s(28):
        n = int(140 * u(t, s(28), 1.4))
        faisceau(c, grille(n, 120, 700, 26, 14), 1.0, VERT_PALE, 1.0)
        ecrit(c, t, s(28) + 0.4, "70 KG", 300, 1160, 52, VERT_PALE, True, 1.6)
        trace(c, t, s(28) + 1.6, 0.3, fleche(110, 660, 60, 660, 16), VERT_PALE, 2.0, bip=1300)
        ecrit(c, t, s(28) + 1.8, "7 CM/S", 300, 620, 56, VERT_PALE, True, 1.6)
        ecrit(c, t, s(28) + 2.4, "140 FOIS PLUS LOURD → 140 FOIS PLUS LENT", W / 2, 1300, 32, VERT)


def e18(c, t):
    """La grille se replie en lui ; le compteur 50 M se remet enfin à défiler ; il touche le bord."""
    glace(c, t)
    bord(c, t, -1)
    x = glisse_x(t)
    faisceau(c, perso("perso_glisse_dos", x, 400, miroir=True), 1.0, VERT_PALE, 1.3)
    if x > BORD + 125:
        faisceau(c, [[(x + 200 + 40 * k, SOL - 60 - 40 * k), (x + 290 + 40 * k, SOL - 60 - 40 * k)] for k in range(3)],
                 1.0, VERT, 0.8, 0.6)
    x29 = glisse_x(s(29))
    reste = max(0.0, (x - BORD - 120) / (x29 - BORD - 120) * 50)
    ecrit(c, t, -1, f"{reste:.0f} M", W / 2, SOL + 110, 72, AMBRE, True, 1.8, vitesse=0.0)
    ecrit(c, t, s(29), "C'EST LENT…", W / 2, 330, 64, VERT_PALE, True, 1.6)
    ecrit(c, t, s(29) + 1.0, "MAIS RIEN NE VOUS ARRÊTE", W / 2, 430, 52, AMBRE, True, 1.6)
    if t > s(30):
        horloge(c, 880, 700, 90, 12 * u(t, s(30), e(30) - s(30) - 0.6))
        ecrit(c, t, s(30) + 0.8, "12 MIN", 880, 860, 52, AMBRE, True, 1.6)
    if reste < 0.5:
        trace(c, t, e(30) - 0.5, 0.2, [cercle_pts(BORD + 40, SOL - 80, 90, 30)], AMBRE, 1.8, bip=1700)


def e19(c, t):
    """Arrêt sur le geste du lancer… qui se change en astronaute en sortie dans l'espace."""
    v = u(t, s(31) + 0.6, 1.2)
    faisceau(c, perso("perso_lance", W / 2, 520), 1.0, AMBRE, 1.3, 1 - v)
    faisceau(c, centre("astronaute_safer", W / 2, 1000, 420), 1.0, VERT_PALE, 1.3, v)
    ecrit(c, t, s(31), "MAIS ATTENDEZ…", W / 2, 330, 72, AMBRE, True, 2.0)


def e20(c, t):
    """Les astronautes portent ce geste sur le dos : le sac de secours lance du gaz derrière eux."""
    w = t - s(32)
    x = W / 2 - 60 + 40 * u(t, s(33) + 1.0, 3.0)
    faisceau(c, centre("astronaute_safer", x, 1000, 420), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(32), "SORTIE DANS L'ESPACE", W / 2, 330, 58, VERT_PALE, True, 1.6)
    if t > s(33):
        for k in range(3):
            ph = (w * 1.5 + k / 3) % 1
            faisceau(c, [cercle_pts(x - 250 - 160 * ph, 900 + 40 * k, 14 + 18 * ph, 14)], 1.0, AMBRE, 1.0, 1 - ph)
        trace(c, t, s(33) + 0.6, 0.4, fleche(x - 230, 1220, x - 430, 1220, 26), AMBRE, 2.2, bip=800)
        trace(c, t, s(33) + 1.0, 0.4, fleche(x + 230, 1220, x + 430, 1220, 26), VERT_PALE, 2.2, bip=1300)
        ecrit(c, t, s(33) + 0.4, "UN SAC DE SECOURS", W / 2, 430, 50, AMBRE, True, 1.5)
        ecrit(c, t, s(33) + 1.4, "QUI LANCE DU GAZ DERRIÈRE", W / 2, 1360, 40, VERT_PALE, True, 1.4)


def e21(c, t):
    """Trois dessins sur la même flèche : la chaussure, le sac, la fusée."""
    faisceau(c, fleche(100, 1250, 980, 1250, 30), 1.0, AMBRE, 2.0)
    trace(c, t, s(34), 0.4, centre("chaussure", 220, 1000, 200), AMBRE, 1.4, bip=1500)
    trace(c, t, s(34) + 0.5, 0.5, centre("astronaute_safer", 540, 960, 260), VERT_PALE, 1.2, bip=1700)
    trace(c, t, s(34) + 1.6, 0.5, centre("fusee", 860, 960, 230), VERT_PALE, 1.2, bip=1900)
    ecrit(c, t, s(34), "LE MÊME GESTE", W / 2, 330, 72, AMBRE, True, 2.0)


def e22(c, t):
    """Retour sur la glace : la chaussure et le sac se barrent ; il reste seul, à 50 M du bord."""
    glace(c, t)
    bord(c, t, -1)
    faisceau(c, perso("perso_debout", X0), 1.0, VERT_PALE, 1.3)
    compteur_bord(c, t, -1, 50)
    ecrit(c, t, s(35), "JE SAIS CE QUE VOUS ALLEZ ME DIRE", W / 2, 330, 40, VERT_PALE, True, 1.4)
    if t > s(36):
        ecrit(c, t, s(36), "ET S'IL N'A RIEN SUR LUI ?", W / 2, 440, 54, AMBRE, True, 1.8)
        for k, (nom, x) in enumerate((("chaussure", 250), ("sac", 470))):
            tb = s(36) + 1.0 + 0.5 * k
            trace(c, t, tb - 0.4, 0.3, centre(nom, x, 700, 150 if nom == "chaussure" else 100), VERT_PALE, 1.2, bip=1500)
            trace(c, t, tb, 0.2, croix(x, 700, 75), AMBRE, 2.6, bip=500)
    if t > s(37):
        ecrit(c, t, s(37) + 0.2, "LA PROCHAINE SITUATION IMPOSSIBLE", W / 2, 1520, 36, AMBRE, True, 1.5)


def e23(c, t):
    """Coupé au milieu de la phrase : la suite demain."""
    c.drawRect(skia.Rect(0, 0, W, M.H), P((40, 18, 4), 0, 255, fill=True))
    ecrit(c, t, -1, "ET S'IL N'A RIEN", W / 2, 820, 76, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, -1, "SUR LUI ?", W / 2, 910, 76, AMBRE, True, 2.2, vitesse=0.0)
    b = 14 * abs(math.sin(t * 5))
    ecrit(c, t, -1, "LA SUITE DEMAIN ▶", W / 2 + b, 1120, 64, VERT_PALE, True, 2.0, vitesse=0.0)


def tableaux():
    return [(0.0, e01, None), (s(2), e02, None), (s(3), e03, None), (s(4), e04, None), (s(7), e05, None),
            (s(9), e06, None), (s(10), e07, None), (s(12), e08, "balayage"), (s(14), e09, None), (s(16), e10, None),
            (s(17), e11, None), (s(18), e12, None), (s(20), e13, "noir"), (s(22), e14, "glitch"), (s(24), e15, None),
            (s(25), e16, None), (s(27), e17, None), (s(29), e18, None), (s(31), e19, None), (s(32), e20, None),
            (s(34), e21, None), (s(35), e22, None), (e(38) + 0.05, e23, None)]


def chocs():
    lancer = s(23) + 0.6
    flashs = [s(1) + 0.9, s(7), s(17), s(22), lancer, s(31), e(38) + 0.05]
    secousses = [(s(1) + 0.9, 0.25), (s(16) + 1.6, 0.15), (lancer, 0.2), (s(31), 0.2), (e(38) + 0.05, 0.3)]
    return flashs, secousses


def effets(tabs):
    lancer = s(23) + 0.6
    ev = [(0.0, Z.vent(s(4), 0.07, 120, 900)), (0.0, Z.grincement(1.2, 0.08)), (0.1, Z.craquement(0.25)),
          (s(1) + 0.9, Z.boom(0.55, 55)), (s(1) + 0.9, Z.snap(0.3)), (s(2), Z.whoosh(0.5, 0.06)),
          (s(2) + 1.0, Z.craquement(0.35)), (s(3), Z.whoosh(0.6, 0.07)), (s(3) + 0.8, Z.cloche(523.3, 0.08))]
    ev += [(e(i) - 0.4, Z.thump(0.3)) for _, i in ESSAIS]
    ev += [(s(4) + 0.3, Z.grincement(0.8, 0.08)), (s(5) + 0.3, Z.grincement(0.6, 0.07)), (s(6) + 0.5, Z.thump(0.3)),
           (s(6) + 1.8, Z.thump(0.3))]
    ev += [(s(7), Z.boom(0.45, 70)), (s(8), Z.tictac(s(22) - s(8), 0.05, 0.5))]
    ev += [(s(9), Z.vibration(2.0, 0.08)), (s(9) + 1.2, Z.cloche(784, 0.08)), (s(10), Z.souffle(1.4, 0.13, False)),
           (s(10) + 1.0, Z.chirp(500, 300, 0.4, 0.05)), (s(11), Z.tictac(1.6, 0.08, 0.05))]
    ev += [(s(13) + 0.3, Z.thump(0.25)), (s(13) + 0.9, Z.thump(0.25)), (s(14) + 0.6, Z.grincement(0.6, 0.08)),
           (s(15), Z.whoosh(0.4, 0.08)), (s(16) + 0.3, Z.whoosh(0.8, 0.07)), (s(16) + 1.6, Z.alarme(0.05, 1)),
           (s(17), Z.riser(1.9, 0.07)), (s(17) + 1.9, Z.cloche(988, 0.08))]
    ev += [(s(18), Z.vent(3.5, 0.05, 200, 700)), (s(19) + 1.6, Z.whoosh(0.5, 0.06)), (s(20), Z.riser(e(21) - s(20), 0.1)),
           (s(21), Z.boom(0.4, 55))]
    ev += [(s(22), Z.boom(0.5, 60)), (s(22) + 0.5, Z.grincement(0.8, 0.07)), (lancer, Z.whoosh(0.6, 0.2)),
           (lancer, Z.snap(0.3)), (s(24), Z.grincement(1.5, 0.06))]
    ev += [(s(25) + 0.1, Z.pince(523.3, 0.1)), (s(25) + 1.3, Z.pince(784, 0.1)), (s(26), Z.cloche(1046.5, 0.08))]
    ev += [(s(28) + 0.1 * k, Z.cliquet(0.04)) for k in range(14)]
    ev += [(s(29), Z.vent(4.0, 0.05, 150, 600)), (s(30), Z.tictac(e(30) - s(30), 0.07, 0.06)), (e(30) - 0.5, Z.thump(0.4)),
           (e(30) - 0.4, Z.cloche(698.5, 0.1))]
    ev += [(s(31), Z.boom(0.5, 55)), (s(31) + 0.6, Z.scintillement(1.2, 0.05)), (s(33), Z.souffle(2.5, 0.08, False)),
           (s(34), Z.pince(659.3, 0.08)), (s(34) + 0.5, Z.pince(784, 0.08)), (s(34) + 1.6, Z.pince(1046.5, 0.08)),
           (s(34) + 1.6, Z.riser(0.8, 0.06))]
    ev += [(s(36) + 1.0, Z.thump(0.3)), (s(36) + 1.5, Z.thump(0.3)), (s(37), Z.riser(e(38) - s(37), 0.1)),
           (e(38) + 0.05, Z.boom(0.6, 50)), (e(38) + 0.05, Z.arret_bande(0.5, 0.2))]
    sons = {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
            "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}
    ev += [(t0, sons[tr]()) for t0, _, tr in tabs[1:] if tr]
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep25_v2.mp4")
