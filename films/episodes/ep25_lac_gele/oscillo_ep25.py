"""Épisode 25 — « Surtout… ne marchez pas » (coincé sur un lac gelé parfaitement lisse) — style oscilloscope.

Format énigme : la solution (lancer sa chaussure, troisième loi de Newton) n'arrive qu'à la fin.
Réalisation : découpage plan par plan (decoupage.md), animation à 24 images/s sans boucle (feuilles de 24 cases,
films/episodes/ep25_lac_gele/feuilles.py), mouvements de caméra faits au montage sur les traits.
Le bord est à gauche : il lance sa chaussure vers la droite et glisse vers la gauche.

    python -m films.episodes.ep25_lac_gele.oscillo_ep25 output/ep25_oscillo.mp4
"""
import json
import math
import os
import sys

import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, P, W, cercle_pts, ease, ecrit, faisceau,
                                                         fleche, pointilles, trace)
from films.outils.feuille_animation import duree, plan
from films.outils.image_en_traits import DOSSIER, dessin
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
M.SEGS = os.path.join(HERE, "audio", "voix.json")
M.FPS = 24
s, e = M.s, M.e
SOL = 1330                                                                    # niveau des pieds sur la glace
HAUT = 560                                                                    # taille d'un personnage debout
BORD_X = 150                                                                  # le bord du lac, à gauche


def ratio(nom):
    return json.load(open(os.path.join(DOSSIER, nom + ".json")))["ratio"]


def centre(nom, cx, cy, largeur, miroir=False):
    return dessin(nom, cx - largeur / 2, cy - largeur * ratio(nom) / 2, largeur, miroir)


def bouge(traits, dx=0.0, dy=0.0):
    return [[(x + dx, y + dy) for x, y in l] for l in traits]


def camera(traits, zoom, fx, fy, cx=W / 2, cy=960):
    """Mouvement de caméra : le point (fx, fy) de la scène vient en (cx, cy), avec un grossissement `zoom`."""
    return [[(cx + (x - fx) * zoom, cy + (y - fy) * zoom) for x, y in l] for l in traits]


def recentre(traits, cx, cy):
    xs = [p[0] for l in traits for p in l]
    ys = [p[1] for l in traits for p in l]
    return bouge(traits, cx - (min(xs) + max(xs)) / 2, cy - (min(ys) + max(ys)) / 2)


_LAC = []


def lac(c, cam=None, intense=0.5):
    if not _LAC:
        _LAC.append(dessin("lac", -70, 650, 1220))
    faisceau(c, camera(_LAC[0], *cam) if cam else _LAC[0], 1.0, VERT, 0.9, intense)


def perso(noms, u, x=W / 2, haut=HAUT, pied=SOL, miroir=False, vitesse=1.0):
    return plan(noms, u, x, pied, haut, miroir=miroir, vitesse=vitesse)


def croix(cx, cy, r=34):
    return [[(cx - r, cy - r), (cx + r, cy + r)], [(cx + r, cy - r), (cx - r, cy + r)]]


def vitesse_traits(x, y, sens, t, n=4):
    """Traits de vitesse derrière un personnage qui glisse (sens = direction du mouvement)."""
    tr = []
    for k in range(n):
        dx = -sens * (120 + 50 * k + 25 * math.sin(t * 9 + k))
        tr.append([(x + dx, y - 40 * k), (x + dx - sens * (90 + 20 * k), y - 40 * k)])
    return tr


def neige_qui_tombe(t, n=40):
    """Une vraie chute de neige, régulière."""
    return [cercle_pts((k * 173.3) % W + 30 * math.sin(t * 1.3 + k), 300 + ((k * 97.1 + t * 120) % 1150), 4, 6)
            for k in range(n)]


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


def bord(c, t, t0, x=BORD_X, y=SOL - 60):
    trace(c, t, t0, 0.4, pointilles(x, y - 220, x, y + 120), VERT, 0.9, bip=1500)
    ecrit(c, t, t0 + 0.2, "BORD", x + 10, y - 240, 32, VERT, True, 1.2)


def titre_accroche(c, t, k=1.0):
    ecrit(c, t, -1.0, "SURTOUT…", W / 2, 300, 70, VERT_PALE, True, 1.8, vitesse=0.0)
    ecrit(c, t, -1.0, "NE MARCHEZ", W / 2, 420, int(118 * k), AMBRE, True, 2.4, vitesse=0.0)
    ecrit(c, t, -1.0, "PAS", W / 2, 540, int(118 * k), AMBRE, True, 2.4, vitesse=0.0)


# ------------------------------------------------------------------------------------------------ plans
def p01(c, t):
    """Plan d'ensemble, zoom avant lent ; il tourne la tête, inquiet. Le titre est là dès l'image 0."""
    z = 0.75 + 0.25 * ease(t / 2.2)
    cam = (z, W / 2, SOL - 250, W / 2, SOL - 250 + 120 * (1 - z))
    lac(c, cam, 0.55)
    faisceau(c, camera(perso("p01", t - 0.4), *cam), 1.0, VERT_PALE, 1.3)
    titre_accroche(c, t)


GEL = 3.15                                                                    # arrêt sur image sur « ne marchez pas »


def p02(c, t):
    """Plan moyen : il lève le pied… arrêt sur image, le pied en l'air."""
    fige = t >= GEL
    lac(c, None, 0.5)
    faisceau(c, perso("p02", min(t, GEL) - s(1) - 0.2, haut=640), 1.0, AMBRE if fige else VERT_PALE, 1.4 if fige else 1.2)
    titre_accroche(c, t, 1 + 0.05 * abs(math.sin(t * 6)) if fige else 1.0)
    if fige:
        trace(c, t, GEL, 0.2, croix(W / 2 + 140, SOL - 40, 50), AMBRE, 2.4, bip=500)


def p03(c, t):
    """Insert sur les pieds posés sur la glace, puis dézoom jusqu'au plan d'ensemble : le bord est très loin."""
    u = ease((t - s(2) - 0.8) / 2.2)
    z = 3.2 - 2.55 * u
    cam = (z, W / 2 - 220 * u, SOL - 40 - 300 * u, W / 2, 1150)
    lac(c, cam, 0.55)
    faisceau(c, camera(perso("p01", 0.0, haut=640), *cam), 1.0, VERT_PALE, 1.2)
    for k in range(4):                                                        # un reflet passe sur la glace lisse
        x = W / 2 - 200 + ((t - s(2)) * 160 + k * 60) % 500
        faisceau(c, camera([[(x, SOL + 20 + 8 * k), (x + 40, SOL + 20 + 8 * k)]], *cam), 1.0, VERT, 0.8, 0.5)
    ecrit(c, t, s(2) + 0.2, "GLACE PARFAITEMENT LISSE", W / 2, 330, 52, VERT_PALE, True, 1.6)
    ecrit(c, t, s(2) + 1.0, "FROTTEMENT = 0", W / 2, 420, 70, AMBRE, True, 2.0)
    if u > 0.6:
        trace(c, t, s(2) + 2.4, 0.5, camera(pointilles(W / 2 - 60, SOL - 120, BORD_X, SOL - 120), *cam), VERT, 0.8,
              bip=1500)
        ecrit(c, t, s(2) + 2.7, "LE BORD", 200, 1500, 40, VERT, True, 1.3)


ESSAIS = [("MARCHER", 3), ("RAMPER", 4), ("SAUTER", 5)]


def liste_essais(c, t):
    for k, (nom, i) in enumerate(ESSAIS):
        if t > s(i):
            x = 210 + 330 * k
            ecrit(c, t, s(i), nom, x, 330, 56, VERT_PALE, True, 1.4, vitesse=0.0)
            if t > s(i) + 0.9:
                trace(c, t, s(i) + 0.9, 0.2, croix(x, 312, 40), AMBRE, 2.0, bip=500)


def p04(c, t):
    """Plan moyen de profil : un pas, le pied part en arrière, les bras moulinent, il se rattrape au même endroit."""
    lac(c, None, 0.45)
    liste_essais(c, t)
    faisceau(c, perso(["p04_1", "p04_2"], t - s(3) - 0.1, haut=600), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(3) + 0.9, "LES PIEDS GLISSENT SUR PLACE", W / 2, 1480, 38, VERT)


def p05(c, t):
    """Plan large bas : à quatre pattes, la main glisse, il s'écrase sur le ventre."""
    lac(c, (1.15, W / 2, SOL - 100, W / 2, SOL - 60), 0.45)
    liste_essais(c, t)
    faisceau(c, perso("p05", t - s(4) - 0.05, haut=640), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(4) + 0.6, "PAREIL", W / 2, 1480, 52, AMBRE, True, 1.6)


def p06(c, t):
    """Plan moyen : il saute et retombe exactement sur la marque."""
    lac(c, None, 0.45)
    liste_essais(c, t)
    faisceau(c, [[(W / 2 - 70, SOL + 14), (W / 2 + 70, SOL + 14)]], 1.0, AMBRE, 1.6)
    faisceau(c, perso(["p06_1", "p06_2"], t - s(5) - 0.25, haut=600), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(5) + 1.9, "MÊME ENDROIT", W / 2, 1480, 52, AMBRE, True, 1.6)


def p07(c, t):
    """Plan rapproché : il se relève et se tourne vers nous. Zoom avant rapide."""
    z = 1.0 + 0.15 * ease((t - s(6)) / 0.4)
    faisceau(c, camera(perso("p07", t - s(6), haut=900, pied=1500), z, W / 2, 1100, W / 2, 1100), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(6), "UN SEUL GESTE", W / 2, 360, 92, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, s(6) + 0.5, "PEUT VOUS SAUVER", W / 2, 460, 64, VERT_PALE, True, 1.6)


def p08(c, t):
    """Plan moyen : il s'assoit sur la glace et attend. Le chronomètre démarre."""
    lac(c, None, 0.45)
    faisceau(c, perso("p08", t - s(7) - 0.2, haut=600), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(7), "TROUVEZ-LE AVANT LA FIN", W / 2, 360, 52, VERT_PALE, True, 1.5)
    ecrit(c, t, s(7) + 1.0, "→ EN COMMENTAIRE", W / 2, 450, 50, AMBRE, True, 1.6)
    compteur(c, t, s(7) + 0.4, 900, 620)


def p09(c, t):
    """Plan moyen de face : il se tortille de plus en plus fort, puis s'arrête, épuisé. Le centre de gravité reste fixe."""
    lac(c, None, 0.4)
    compteur(c, t, s(7) + 0.4, 960, 230)
    ecrit(c, t, s(8), "SE TORTILLER ?", W / 2, 330, 66, VERT_PALE, True, 1.6)
    faisceau(c, perso(["p09_1", "p09_2", "p09_3", "p09_4"], t - s(8) - 0.3, haut=600), 1.0, VERT_PALE, 1.2)
    if t > s(8) + 1.4:
        g = (W / 2, SOL - 300)
        trace(c, t, s(8) + 1.4, 0.3, [cercle_pts(*g, 16, 20), [(g[0] - 34, g[1]), (g[0] + 34, g[1])],
                                      [(g[0], g[1] - 34), (g[0], g[1] + 34)]], AMBRE, 1.6, bip=1700)
        ecrit(c, t, s(8) + 1.7, "CENTRE DE GRAVITÉ", W / 2, 1450, 44, AMBRE, True, 1.5)
        ecrit(c, t, s(8) + 2.8, "DÉPLACEMENT : 0 MM", W / 2, 1515, 40, VERT_PALE)


def p10(c, t):
    """Profil : il inspire, souffle de toutes ses forces ; puis insert sur les pieds : ils ont avancé d'un rien."""
    u = t - s(9)
    ecrit(c, t, s(9), "SOUFFLER ?", W / 2, 330, 66, VERT_PALE, True, 1.6)
    if u < 2.9:
        lac(c, None, 0.4)
        compteur(c, t, s(7) + 0.4, 960, 230)
        faisceau(c, perso(["p10_1", "p10_2"], u - 0.2, haut=600), 1.0, VERT_PALE, 1.2)
        ecrit(c, t, s(9) + 1.4, "À PEINE…", W / 2, 1450, 52, AMBRE, True, 1.6)
        return
    cam = (3.0, W / 2, SOL - 30, W / 2, 1100)                                  # insert sur les pieds + règle graduée
    faisceau(c, camera(perso(["p10_1", "p10_2"], 9.0, x=W / 2 - 2, haut=600), *cam), 1.0, VERT_PALE, 1.2)
    regle = [[(W / 2 - 120 + 10 * k, SOL + 30), (W / 2 - 120 + 10 * k, SOL + (48 if k % 5 == 0 else 40))] for k in range(25)]
    faisceau(c, camera(regle + [[(W / 2 - 120, SOL + 30), (W / 2 + 120, SOL + 30)]], *cam), 1.0, VERT, 0.8)
    ecrit(c, t, s(9) + 3.0, "1 MM", W / 2, 1320, 52, AMBRE, True, 1.6)
    ecrit(c, t, s(9) + 3.3, "IL FAUDRAIT DES HEURES", W / 2, 1480, 44, VERT_PALE, True, 1.4)


def p11(c, t):
    """Plan large, accéléré : il grelotte, la neige le recouvre ; le compteur des jours défile."""
    u = t - s(10)
    lac(c, None, 0.4)
    faisceau(c, perso(["p11_1", "p11_2"], u, haut=520), 1.0, VERT_PALE, 1.2)
    faisceau(c, neige_qui_tombe(t * 3), 1.0, VERT_PALE, 0.6, 0.7)
    ecrit(c, t, s(10), "ATTENDRE ?", W / 2, 330, 66, VERT_PALE, True, 1.6)
    ecrit(c, t, s(10), f"JOUR {int(1 + 180 * ease(u / 2.0))}", W / 2, 470, 100, AMBRE, True, 2.0, vitesse=0.0)
    ecrit(c, t, s(10) + 1.6, "DES MOIS", W / 2, 1480, 60, AMBRE, True, 1.8)


def p12(c, t):
    """Sur un sol normal : un vrai pas. Pour avancer, il faut pousser quelque chose."""
    faisceau(c, [[(60, SOL), (1020, SOL)]], 1.0, VERT, 1.2, 0.9)
    faisceau(c, perso("p12", t - s(11) - 0.3, x=W / 2 - 80, haut=600), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(11), "POUR AVANCER…", W / 2, 330, 66, VERT_PALE, True, 1.6)
    ecrit(c, t, s(11) + 1.6, "IL FAUT POUSSER", W / 2, 430, 72, AMBRE, True, 1.8)
    compteur(c, t, s(7) + 0.4, 960, 200)


def p13(c, t):
    """Gros plan sur le pied qui pousse le sol (ralenti) : action et réaction."""
    faisceau(c, [[(60, 1260), (1020, 1260)]], 1.0, VERT, 1.4, 0.9)
    faisceau(c, perso("p13", t - s(12), haut=760, pied=1260, vitesse=0.5), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(12) + 0.4, "VOUS POUSSEZ LE SOL", W / 2, 1400, 46, AMBRE, True, 1.5)
    trace(c, t, s(12) + 0.4, 0.4, fleche(W / 2 + 60, 1300, W / 2 - 220, 1300, 30), AMBRE, 2.2, bip=800)
    if t > s(12) + 2.2:
        ecrit(c, t, s(12) + 2.2, "LE SOL VOUS POUSSE", W / 2, 400, 46, VERT_PALE, True, 1.5)
        trace(c, t, s(12) + 2.2, 0.4, fleche(W / 2 - 160, 560, W / 2 + 200, 560, 34), VERT_PALE, 2.4, bip=1300)


def p14(c, t):
    """Même gros plan, sur la glace : le pied glisse dans le vide (ralenti)."""
    faisceau(c, [[(60, 1260), (1020, 1260)]], 1.0, VERT, 1.0, 0.6)
    faisceau(c, perso("p14", t - s(13), haut=760, pied=1260, vitesse=0.5), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(13), "SANS FROTTEMENT", W / 2, 330, 72, AMBRE, True, 1.8)
    faisceau(c, fleche(W / 2 - 160, 560, W / 2 + 200, 560, 34), 1.0, VERT_PALE, 1.2, 0.3)
    trace(c, t, s(13) + 0.6, 0.2, croix(W / 2 + 20, 560, 70), AMBRE, 2.6, bip=500)
    ecrit(c, t, s(13) + 1.0, "PLUS RIEN À POUSSER", W / 2, 1400, 46, AMBRE, True, 1.5)


def p15(c, t):
    """Plan fixe en pied ; panoramique vertical lent du bonnet aux chaussures : l'indice."""
    u = ease((t - s(14) - 0.6) / 1.8)
    fy = (SOL - HAUT + 60) + (HAUT - 120) * u
    faisceau(c, camera(perso("p01", 0.0), 2.2, W / 2, fy, W / 2, 960), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(14), "RIEN…", W / 2, 330, 96, AMBRE, True, 2.0, vitesse=0.0)
    ecrit(c, t, s(14) + 0.9, "SAUF CE QUE VOUS", W / 2, 1420, 56, VERT_PALE, True, 1.6)
    ecrit(c, t, s(14) + 1.3, "AVEZ SUR VOUS", W / 2, 1500, 60, AMBRE, True, 1.8)
    if u > 0.95:
        ecrit(c, t, s(14) + 2.3, "?", W / 2 + 200, 1150 + 10 * math.sin(t * 4), 90, AMBRE, True, 2.0, vitesse=0.0)


def module(c, z, intense=0.35):
    faisceau(c, camera(centre("module", W / 2, 960, 1060), z, W / 2, 960), 1.0, VERT, 0.7, intense)


def p16(c, t):
    """Les astronautes : travelling avant dans le module."""
    module(c, 1.0 + 0.5 * ease((t - s(15)) / 2.0))
    c.drawRect(skia.Rect(0, 230, W, 400), P((2, 8, 4), 0, 220, fill=True))
    ecrit(c, t, s(15), "LES ASTRONAUTES", W / 2, 330, 66, VERT_PALE, True, 1.6)


def p17(c, t):
    """Plan moyen : l'astronaute brasse le vide, tend la main vers une paroi trop loin, n'avance pas."""
    module(c, 1.5)
    astro = recentre(perso(["p17_1", "p17_2", "p17_3"], t - s(16), x=0, haut=430, pied=0, vitesse=0.7), W / 2, 980)
    faisceau(c, astro, 1.0, VERT_PALE, 1.2)
    c.drawRect(skia.Rect(0, 230, W, 400), P((2, 8, 4), 0, 220, fill=True))
    ecrit(c, t, s(16), "LOIN DES PAROIS", W / 2, 330, 72, AMBRE, True, 1.8)
    if t > s(16) + 1.6:
        for x0, x1 in ((W / 2 - 230, 70), (W / 2 + 230, W - 70)):
            trace(c, t, s(16) + 1.6, 0.4, fleche(x0, 980, x1, 980, 24), AMBRE, 1.2, bip=1500)
        ecrit(c, t, s(16) + 2.6, "RIEN POUR S'AGRIPPER", W / 2, 1420, 44, VERT_PALE, True, 1.5)


NOIR = 54.1                                                                   # coupe au noir sur « … trouvée ? »


def p18(c, t):
    """Plan rapproché : l'astronaute s'immobilise et tourne la tête vers nous. Coupe au noir sur la question."""
    if t >= NOIR:
        compteur(c, t, s(7) + 0.4, W / 2, 960)
        ecrit(c, t, NOIR + 0.1, "VOUS L'AVEZ TROUVÉE ?", W / 2, 1150, 60, AMBRE, True, 2.0)
        return
    module(c, 2.2, 0.25)
    faisceau(c, recentre(perso("p18", t - s(17), x=0, haut=900, pied=0), W / 2, 1000), 1.0, VERT_PALE, 1.3)
    ecrit(c, t, s(17), "LA MÊME SOLUTION", W / 2, 330, 72, AMBRE, True, 1.8)


def p19(c, t):
    """Plan moyen : il enlève sa chaussure en équilibre sur un pied."""
    lac(c, None, 0.45)
    faisceau(c, perso(["p19_1", "p19_2"], t - s(18), haut=600, vitesse=1.4), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(18), "ENLEVEZ VOTRE CHAUSSURE", W / 2, 330, 58, AMBRE, True, 1.8)


ELAN = 22 / 24                                                                # durée de l'élan (feuille 1)


def p20(c, t):
    """Plan moyen : élan au ralenti, lancer à vitesse réelle ; la chaussure sort du cadre, à l'opposé du bord."""
    u = t - s(19) - 0.1
    v = u * 0.5 if u < 2 * ELAN else ELAN + (u - 2 * ELAN)                    # ralenti puis vitesse réelle
    lac(c, None, 0.45)
    faisceau(c, perso(["p20_1", "p20_2"], v, x=W / 2 - 60, haut=600), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(19), "LANCEZ-LA !", W / 2, 330, 84, AMBRE, True, 2.0)
    if v > ELAN + 0.3:
        ecrit(c, t, s(19) + 2.4, "À L'OPPOSÉ DU BORD", W / 2, 1480, 46, VERT_PALE, True, 1.5)
        bord(c, t, s(19) + 2.4)


def p21(c, t):
    """Plan large : le recul le fait tomber sur le dos et glisser vers le bord ; la caméra le suit."""
    u = t - s(20)
    x = 620 - 90 * max(0.0, u - 0.5)
    cam = (1.0, x - 80, SOL - 200, W / 2, SOL - 200)                          # la caméra suit (travelling latéral)
    lac(c, cam, 0.45)
    faisceau(c, camera(perso("p21", u, x=x, haut=600), *cam), 1.0, VERT_PALE, 1.2)
    if u > 0.8:
        faisceau(c, camera(vitesse_traits(x + 260, SOL - 30, -1, t), *cam), 1.0, VERT, 0.9, 0.7)
    ecrit(c, t, s(20) + 0.3, "VOUS PARTEZ", W / 2, 330, 76, VERT_PALE, True, 1.8)
    ecrit(c, t, s(20) + 0.6, "DANS L'AUTRE SENS", W / 2, 430, 64, AMBRE, True, 1.8)


def p22(c, t):
    """Écran partagé : la chaussure part à droite, lui à gauche. Action, réaction."""
    t0 = s(21)
    faisceau(c, [[(W / 2, 520), (W / 2, 1560)]], 1.0, VERT, 1.0, 0.6)
    faisceau(c, perso("p21", 9.0, x=W / 4 + 40, haut=420), 1.0, VERT_PALE, 1.1)
    faisceau(c, centre("chaussure", 3 * W / 4 + 30 * (t - t0), SOL - 260, 200), 1.0, AMBRE, 1.4)
    trace(c, t, t0 + 0.1, 0.4, fleche(3 * W / 4 - 60, SOL - 420, 3 * W / 4 + 160, SOL - 420, 30), AMBRE, 2.2, bip=800)
    ecrit(c, t, t0 + 0.2, "ACTION", 3 * W / 4, SOL - 470, 50, AMBRE, True, 1.4)
    trace(c, t, t0 + 0.6, 0.4, fleche(W / 4 + 120, SOL - 420, W / 4 - 100, SOL - 420, 30), VERT_PALE, 2.2, bip=1600)
    ecrit(c, t, t0 + 0.7, "RÉACTION", W / 4, SOL - 470, 50, VERT_PALE, True, 1.4)
    ecrit(c, t, t0 + 1.3, "3e LOI DE NEWTON", W / 2, 360, 66, AMBRE, True, 1.8)
    ecrit(c, t, t0 + 2.0, "0,5 KG À 10 M/S → 70 KG À 7 CM/S", W / 2, 1480, 38, VERT)


def p23(c, t):
    """Plan large : il glisse lentement et touche la rive."""
    u = ease((t - s(22)) / (s(23) - s(22) - 0.3))
    x = 760 - (760 - BORD_X - 130) * u
    lac(c, None, 0.45)
    bord(c, t, s(22))
    faisceau(c, perso("p21", 9.0, x=x, haut=600), 1.0, VERT_PALE, 1.2)
    if u < 0.98:
        faisceau(c, vitesse_traits(x + 260, SOL - 30, -1, t, 3), 1.0, VERT, 0.8, 0.5)
    ecrit(c, t, s(22), "LENTEMENT…", W / 2, 330, 70, VERT_PALE, True, 1.6)
    ecrit(c, t, s(22) + 1.4, "MAIS RIEN NE L'ARRÊTE", W / 2, 430, 56, AMBRE, True, 1.6)
    ecrit(c, t, s(22) + 0.5, "7 CM/S", W / 2, 1480, 60, AMBRE, True, 1.6)
    if u >= 0.98:
        trace(c, t, s(23) - 0.3, 0.2, [cercle_pts(BORD_X + 40, SOL - 60, 80, 30)], AMBRE, 1.6, bip=1700)


def p24(c, t):
    """Raccord de mouvement : la glissade devient le décollage d'une fusée."""
    u = max(0.0, t - s(23) - 0.3)
    y = 1050 - 140 * u * u
    trace(c, t, s(23), 0.5, centre("fusee", W / 2, y, 380), VERT_PALE, 1.2, bip=1100)
    trace(c, t, s(23) + 0.5, 0.3, fleche(W / 2 - 160, y + 120, W / 2 - 160, y + 330, 26), AMBRE, 1.8, bip=800)
    ecrit(c, t, s(23) + 0.5, "GAZ", W / 2 - 250, y + 240, 38, AMBRE, True, 1.4)
    trace(c, t, s(23) + 0.9, 0.3, fleche(W / 2 + 190, y + 120, W / 2 + 190, y - 90, 26), VERT_PALE, 1.8, bip=1600)
    ecrit(c, t, s(23) + 0.9, "FUSÉE", W / 2 + 280, y + 40, 38, VERT_PALE, True, 1.4)
    ecrit(c, t, s(23), "COMME UNE FUSÉE", W / 2, 330, 72, AMBRE, True, 1.8)


def p25(c, t):
    """Sur la rive : la joie (en attendant sa feuille, les bras levés de la feuille « se tortiller »)."""
    u = t - s(24)
    lac(c, None, 0.4)
    bord(c, t, -1.0)
    faisceau(c, perso("p09_2", 0.5 + u * 0.8, x=BORD_X + 260), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(24) + 0.1, "VOUS AVIEZ", W / 2, 330, 96, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, s(24) + 0.3, "TROUVÉ ?", W / 2, 440, 96, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, s(24) + 0.9, "DITES-LE EN COMMENTAIRE", 500, 1480, 40, VERT_PALE, True, 1.5)
    b = 18 * abs(math.sin(u * 5))
    trace(c, t, s(24) + 1.1, 0.25, fleche(800 + b, 1466, 960 + b, 1466, 26), AMBRE, 1.8, bip=1700)


def p26(c, t):
    """Plan large : il s'éloigne et sort du cadre ; fin sur le lac vide."""
    u = t - s(25)
    lac(c, None, 0.45)
    x = BORD_X + 260 - 230 * max(0.0, u - 0.2)
    if x > -150:
        faisceau(c, perso("p12", (u * 0.9) % duree("p12"), x=x, miroir=True), 1.0, VERT_PALE, 1.2)
    ecrit(c, t, s(25), "+ ABONNEZ-VOUS", W / 2, 400, 64, AMBRE, True, 1.8)
    ecrit(c, t, s(25) + 0.6, "PROCHAINE SITUATION IMPOSSIBLE", W / 2, 1480, 36, VERT)


def tableaux():
    # coupes franches (raccords dans le mouvement) ; un effet de transition seulement aux changements de partie
    return [(0.0, p01, None), (s(1), p02, None), (s(2), p03, None), (s(3) - 0.1, p04, "neige"), (s(4), p05, None),
            (s(5), p06, None), (s(6) - 0.1, p07, "glitch"), (s(7), p08, None), (s(8) - 0.1, p09, "balayage"),
            (s(9), p10, None), (s(10), p11, None), (s(11) - 0.1, p12, "neige"), (s(12), p13, None), (s(13), p14, None),
            (s(14), p15, None), (s(15) - 0.1, p16, "noir"), (s(16), p17, None), (s(17), p18, None),
            (s(18) - 0.1, p19, "glitch"), (s(19), p20, None), (s(20), p21, None), (s(21), p22, "balayage"),
            (s(22), p23, None), (s(23), p24, None), (s(24) - 0.1, p25, "neige"), (s(25), p26, None)]


def chocs():
    lancer = s(19) + 0.1 + 2 * ELAN + 0.1
    flashs = [GEL, s(6), s(14), s(18), lancer]
    secousses = [(GEL, 0.25), (s(5) + 1.3, 0.12), (s(13) + 0.6, 0.15), (s(18), 0.2), (s(20) + 0.6, 0.2)]
    return flashs, secousses


def effets(tabs):
    lancer = s(19) + 0.1 + 2 * ELAN
    ev = [(0.0, Z.vent(s(3), 0.07, 120, 900)), (0.0, Z.grincement(1.2, 0.08)), (0.1, Z.craquement(0.25)),
          (GEL, Z.boom(0.55, 55)), (GEL, Z.snap(0.3)), (s(2), Z.whoosh(0.5, 0.06)), (s(2) + 1.0, Z.craquement(0.35)),
          (s(2) + 2.4, Z.chirp(600, 300, 0.5, 0.06))]
    ev += [(s(i) + 0.9, Z.thump(0.3)) for _, i in ESSAIS]
    ev += [(s(3) + 0.5, Z.grincement(0.8, 0.08)), (s(3) + 1.0, Z.whoosh(0.5, 0.08)), (s(4) + 0.7, Z.thump(0.4)),
           (s(5) + 0.4, Z.whoosh(0.4, 0.08)), (s(5) + 1.3, Z.thump(0.35))]
    ev += [(s(6), Z.boom(0.45, 70)), (s(7) + 0.4, Z.tictac(s(8) - s(7), 0.07, 0.5))]
    ev += [(s(8) + 0.4, Z.vibration(3.0, 0.08)), (s(8) + 1.4, Z.cloche(784, 0.08)), (s(9) + 0.3, Z.souffle(1.0, 0.10, True)),
           (s(9) + 1.2, Z.souffle(1.6, 0.14, False)), (s(9) + 3.0, Z.cloche(1318.5, 0.06)),
           (s(10), Z.tictac(2.0, 0.08, 0.06)), (s(10), Z.vent(2.5, 0.06, 200, 900)), (s(10) + 1.6, Z.cloche(440, 0.08))]
    ev += [(s(11) + 0.3, Z.thump(0.25)), (s(11) + 0.8, Z.thump(0.25)), (s(12) + 0.4, Z.grincement(0.6, 0.08)),
           (s(12) + 2.2, Z.whoosh(0.4, 0.08)), (s(13) + 0.3, Z.whoosh(0.8, 0.07)), (s(13) + 0.6, Z.alarme(0.05, 1)),
           (s(14), Z.riser(2.0, 0.07)), (s(14) + 2.3, Z.scintillement(1.0, 0.05))]
    ev += [(s(15), Z.porte(1.2, 0.08)), (s(15), Z.vent(4.0, 0.05, 200, 700)), (s(16) + 1.6, Z.whoosh(0.5, 0.06)),
           (s(17), Z.riser(NOIR - s(17), 0.1)), (NOIR, Z.boom(0.4, 55)), (NOIR + 0.2, Z.tictac(s(18) - NOIR, 0.1, 0.25))]
    ev += [(s(18), Z.boom(0.5, 60)), (s(18) + 0.3, Z.grincement(0.8, 0.07)), (s(19) + 0.1, Z.riser(2 * ELAN, 0.08)),
           (lancer, Z.whoosh(0.6, 0.2)), (lancer, Z.snap(0.3)), (s(20) + 0.5, Z.thump(0.4)),
           (s(20) + 0.7, Z.grincement(1.5, 0.07))]
    ev += [(s(21) + 0.1, Z.pince(523.3, 0.1)), (s(21) + 0.6, Z.pince(784, 0.1)), (s(21) + 1.3, Z.cloche(1046.5, 0.08)),
           (s(22), Z.vent(3.5, 0.05, 150, 600)), (s(23) - 0.3, Z.thump(0.35)), (s(23), Z.riser(1.2, 0.1)),
           (s(23) + 0.3, Z.boom(0.4, 50)), (s(23) + 0.4, Z.crepitement(1.6, 0.08, 60))]
    ev += [(s(24), Z.applaudissements(1.6, 0.08)), (s(24) + 1.1, Z.pince(784, 0.08)), (s(24) + 1.25, Z.pince(988, 0.08)),
           (s(24) + 1.4, Z.pince(1175, 0.08)), (s(25), Z.cloche(698.5, 0.1, 2.5))]
    sons = {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
            "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}
    ev += [(t0, sons[tr]()) for t0, _, tr in tabs[1:] if tr]
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep25_oscillo.mp4")
