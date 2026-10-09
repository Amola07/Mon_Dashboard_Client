"""Épisode 31 — « La porte d'avion ouverte en plein vol » — format jeu vidéo (comme l'ép. 21, la plus vue).

Sprites animés (feuilles 24-26 → films/outils/planche_sprites.py), sons 8 bits (films/styles/son_jeu.py), écran de
jeu : NIVEAU, altimètre et jauge de pression, barres « VS », bandeaux, ⏸ arrêt sur image, sous-titres tapés.

    python -m films.episodes.ep31_porte_avion.jeu_ep31 output/ep31.mp4 [t0 t1]
"""
import json
import math
import os
import sys
import types

import numpy as np
import skia

from films import montage_ia as MI
from films.episodes.ep30_foret import oscillo2_ep30 as B          # outils communs (phrase, tampon, rendre…)
from films.outils import mots_voix as MV
from films.styles import anim_pro as A
from films.styles import oscillo2 as O
from films.styles import oscillo_son as Z
from films.styles import son_jeu as J
from films.styles.oscillo2 import AMBRE, VERT, VERT_PALE, VERT_SOMBRE, W, H

ICI = os.path.dirname(os.path.abspath(__file__))
T = B.T                                   # on réutilise le moteur de l'ép. 30 : mêmes globales T et VOIX
rect, croix = B.rect, B.croix
SONS = {}
_T0 = [0.0]


def ajoute(cle, t0, fab):
    if cle not in SONS and t0 >= 0:
        SONS[cle] = (t0, fab)


def phrase(c, t, t0, lignes, t1=None):
    n = min(12, sum(len(l.replace("*", "").replace(" ", "")) for l in lignes))
    for i in range(n):
        ajoute(("lettre", round(t0, 2), i), t0 + 0.4 * i / n, J.lettre)
    B.phrase(c, t, t0, lignes, t1)


def tampon(c, t, t0, txt, cx, cy, ang=-7, h=46, son=None):
    ajoute(("tampon", round(t0, 2)), t0, son or J.niveau)
    ajoute(("tampon_x", round(t0, 2)), t0, lambda: J.explosion(0.12, 0.3))
    B.tampon(c, t, t0, txt, cx, cy, ang, h)


def compteur(c, t, t0, v0, v1, x, y, h, d=0.9, fmt="{:.0f}", col=AMBRE, a=1.0):
    for i in range(int(d / 0.06)):
        ajoute(("compte", round(t0, 2), i), t0 + 0.06 * i, (lambda i: lambda: J.tic_compteur(i))(i))
    ajoute(("compte_fin", round(t0, 2)), t0 + d, J.piece)
    B.compteur(c, t, t0, v0, v1, x, y, h, d, fmt, col, a)


def sprite(c, t, t0, nom, cx, bas, h, a=1.0, trace=0.45, hach=("ambre", "vert")):
    """Une image de sprite ; à sa première apparition (t0), le faisceau la trace avec ses bips."""
    if t < t0:
        return
    for i in range(int(trace / 0.13) + 1):
        ajoute(("trace", nom, round(t0, 2), i), t0 + 0.13 * i,
               (lambda f: lambda: J.trace(f))(600 + (sum(map(ord, nom)) % 7) * 90 + 120 * (i % 3)))
    u = (t - t0) / trace if trace > 0 else 1.0
    O.dessiner_icone_sobre(c, nom, cx, bas, h, a, u, hach)


def anime(c, t, t0, base, cx, bas, h, fps=8, images=(1, 2, 3, 4), a=1.0, trace=0.0, hach=("ambre", "vert"),
          fondu=0.45, balance=0.0, souffle=0.0):
    """Un sprite animé, fluide : entre deux images on fond l'une dans l'autre (sur la fin de l'intervalle), le
    corps se balance autour des pieds (balance, en degrés) et respire (souffle : écrasement-étirement)."""
    if t < t0:
        return
    f = (t - t0) * fps
    i = int(f)
    fr = f - i
    k0, k1 = images[i % len(images)], images[(i + 1) % len(images)]
    ang = balance * math.sin(2 * math.pi * f / len(images))
    sy = 1 + souffle * math.sin(2 * math.pi * f / len(images) * 2)
    c.save()
    c.translate(cx, bas)
    c.rotate(ang)
    c.scale(1 / math.sqrt(sy), sy)
    c.translate(-cx, -bas)
    u = A.lisse((fr - (1 - fondu)) / fondu) if fondu > 0 else 0.0
    if u <= 0:
        sprite(c, t, t0, f"{base}_{k0}", cx, bas, h, a, trace if (t - t0) < trace else 0.0, hach)
    else:
        c.saveLayerAlpha(None, int(255 * (1 - u) * a))
        sprite(c, t, t0, f"{base}_{k0}", cx, bas, h, 1.0, 0.0, hach)
        c.restore()
        c.saveLayerAlpha(None, int(255 * u * a))
        sprite(c, t, t0, f"{base}_{k1}", cx, bas, h, 1.0, 0.0, hach)
        c.restore()
    c.restore()


def lampe(c, t, x, y, a=1.0):
    """Un voyant d'alarme qui clignote, avec ses rayons."""
    if int(t * 4) % 2:
        return
    p = skia.Path()
    p.addCircle(x, y, 22)
    O.hachures(c, p, AMBRE, 5, -35, 1.6, a)
    O.dessiner(c, O.contours(p, 4), AMBRE, 3, a)
    O.dessiner(c, [[(x + 34 * math.cos(k), y + 34 * math.sin(k)), (x + 56 * math.cos(k), y + 56 * math.sin(k))]
                   for k in [i * math.pi / 4 for i in range(8)]], AMBRE, 3, a)


def suite_images(c, t, etapes, base, cx, bas, h, a=1.0, hach=("ambre", "vert")):
    """Des images qui se succèdent à des instants donnés : [(t0, k)]."""
    cour = [(t0, k) for t0, k in etapes if t >= t0]
    if cour:
        t0, k = cour[-1]
        sprite(c, t, etapes[0][0], f"{base}_{k}", cx, bas, h, a, 0.45 if t0 == etapes[0][0] else 0.0, hach)


def fleches_pression(c, t, x0, x1, ys, a=1.0, sens=1):
    """Des flèches qui avancent en boucle : l'air de la cabine qui pousse."""
    tr = []
    for i, y in enumerate(ys):
        ph = (t * 1.2 + i * 0.37) % 1.0
        x = x0 + (x1 - x0) * ph
        tr += [[(x - 40 * sens, y), (x, y)], [(x - 14 * sens, y - 12), (x, y), (x - 14 * sens, y + 12)]]
    O.dessiner(c, tr, AMBRE, 3, a)


def vent(c, t, x0, x1, y0, y1, a=1.0, n=14):
    tr = []
    for i in range(n):
        ph = (t * 2.2 + i * 0.29) % 1.0
        y = y0 + (y1 - y0) * ((i * 0.618) % 1)
        x = x1 - (x1 - x0) * ph
        tr.append([(x, y), (x - 90, y + 4 * math.sin(i))])
    O.dessiner(c, tr, VERT, 2.2, 0.8 * a)


def sol_defile(c, t, y, v=300, a=1.0):
    O.dessiner(c, [[(80, y), (1000, y)]], VERT_PALE, 2.4, a)
    O.dessiner(c, [[(x, y + 26), (x + 60, y + 26)] for x in ((i * 180 - v * t) % 1260 - 120 for i in range(8))], VERT, 2.4, a)


def nuages(c, t, a=0.7):
    tr = []
    for i in range(5):
        x = (i * 330 - 120 * t) % 1500 - 200
        y = 760 + 180 * ((i * 0.43) % 1)
        p = skia.Path()
        for dx, r in ((0, 26), (30, 34), (66, 24)):
            p.addCircle(x + dx, y, r)
        tr += O.contours(p, 6)
    O.dessiner(c, tr, VERT_SOMBRE if O.PAPIER else VERT, 1.6, a * 0.5)


# ------------------------------------------------------------------------------------------------ les écrans
PORTE_X = 840


def s1(c, t, a=1.0):
    """L'accroche : dès l'image 0, le passager arrache la poignée, l'alarme hurle, la porte tremble."""
    phrase(c, t, -1.0, ["Ouvrir la porte", "*en plein vol* ?"])
    nuages(c, t)
    x = 100 + (t * 160) % 1100                                    # l'avion qui traverse, en haut
    sprite(c, t, -1.0, "sp_avion_1", x, 760 + 6 * math.sin(2.5 * t), 90, a, 0)
    O.dessiner(c, [[(80, 1580), (1000, 1580)]], VERT_PALE, 2.4, a)    # le plancher de la cabine
    tremble = 5 * math.sin(55 * t) * (0.4 + 0.6 * abs(math.sin(3 * t)))
    lampe(c, t, 718, 850, a)
    fps = 9 if t < T["aspire"] else 12                           # il tire de plus en plus vite
    anime(c, t, -1.0, "sp_effort", 540 + tremble, 1580, 700, fps, tuple(range(2, 13)), a=a, fondu=0.5)
    if t >= T["aspire"] - 0.2:                                    # l'air aspiré vers la porte
        vent(c, -t, PORTE_X - 260, PORTE_X - 40, 1080, 1500, a * A.lisse((t - T["aspire"] + 0.2) / 0.3), 10)
    if t >= T["aspire"]:
        O.dessiner(c, O.texte("?", 470, 1010, 120, gras=True), AMBRE, 4, a)


def s2(c, t, a=1.0):
    tn = T["non"]
    c.saveLayerAlpha(None, 70)                                    # l'image figée, assombrie
    s1(c, tn - 0.05)
    c.restore()
    if int((t - tn) * 5) % 2 == 0 or t > tn + 1.0:
        k = 1 + 0.4 * max(0.0, 1 - (t - tn) / 0.12)
        c.save()
        c.translate(W / 2, 1060)
        c.scale(k, k)
        O.dessiner(c, O.texte("NON", 0, 0, 300, gras=True), AMBRE, 10, a)
        c.restore()
    if t >= T["ouvrir"]:
        O.dessiner(c, O.texte("IL NE PEUT MÊME PAS L'OUVRIR", W / 2, 1260, 40, gras=True), VERT_PALE, 2.4, a,
                   (t - T["ouvrir"]) / 0.4)
    if t >= T["surprendre"]:
        O.dessiner(c, O.texte("ET LA RAISON VA VOUS SURPRENDRE", W / 2, 1340, 34), AMBRE, 2, a, (t - T["surprendre"]) / 0.4)


def s3(c, t, a=1.0):
    phrase(c, t, T["onze"], ["L'air *pousse*", "sur la porte"], t1=T["cinq"])
    phrase(c, t, T["cinq"], ["*5 tonnes*", "par mètre carré"], t1=T["toute"])
    phrase(c, t, T["toute"], ["Sur toute la porte :", "*10 tonnes*"], t1=T["poids"])
    phrase(c, t, T["poids"], ["Deux *éléphants*"])
    sprite(c, t, T["onze"] - 0.1, "sp_porte_1", 420, 1600, 760, a, 0.5)
    fleches_pression(c, t, 60, 200, [900, 1050, 1200, 1350, 1500], a * A.lisse((t - T["cabine"]) / 0.4) if t >= T["cabine"] else 0)
    if T["cinq"] <= t < T["toute"]:                                # un mètre carré sur la porte
        O.dessiner(c, [rect(290, 1080, 550, 1340)], AMBRE, 3, a, (t - T["cinq"]) / 0.3)
        O.dessiner(c, O.texte("1 M2", 420, 1390, 34, gras=True), AMBRE, 2, a)
        compteur(c, t, T["cinq"], 0, 5, 790, 1250, 130, 0.8, "{:.0f}", AMBRE, a)
        O.dessiner(c, O.texte("T", 870, 1250, 80, centre=False, gras=True), AMBRE, 3, a)
    if t >= T["toute"]:
        compteur(c, t, T["toute"], 5, 10, 820, 1250, 150, 0.8, "{:.0f}", AMBRE, a)
        O.dessiner(c, O.texte("TONNES", 830, 1350, 56, gras=True), AMBRE, 3, a)
    te = T["elephants"] - 0.1
    for i, x in enumerate((300, 760)):                             # les deux éléphants tombent
        ti = te + 0.25 * i
        if t >= ti:
            y = 620 + 230 * min(1.0, ((t - ti) / 0.35) ** 2)
            ajoute(("boum_el", i), ti + 0.35, lambda: J.fichier("boum_grave", 0.45))
            ajoute(("impact_el", i), ti + 0.35, lambda: J.fichier("impact", 0.2))
            sprite(c, t, ti, f"sp_elephant_{1 + (int(t * 4) % 2 if t > ti + 0.5 else 0)}", x, y, 210, a, 0.2)


def s4(c, t, a=1.0):
    phrase(c, t, T["bouchon"], ["La porte est", "un *bouchon*"], t1=T["louvrir2"])
    phrase(c, t, T["louvrir2"], ["Il faut la tirer", "*vers l'intérieur*"], t1=T["contre"])
    phrase(c, t, T["contre"], ["*Contre 10 tonnes*"])
    xc = 700                                                      # la coupe : le mur, et la porte plus large que le trou
    mur = [[(xc + 40, 820), (xc + 40, 1000)], [(xc + 40, 1280), (xc + 40, 1640)],
           [(xc + 80, 820), (xc + 80, 1000)], [(xc + 80, 1280), (xc + 80, 1640)]]
    O.dessiner(c, mur, VERT_PALE, 4, a, (t - T["bouchon"] + 0.25) / 0.6)
    bouchon = skia.Path()
    bouchon.addPoly([skia.Point(xc, 950), skia.Point(xc + 40, 1010), skia.Point(xc + 40, 1270), skia.Point(xc, 1330)], True)
    O.hachures(c, bouchon, AMBRE, 7, -35, 1.6, 0.8 * a)
    O.dessiner(c, O.contours(bouchon, 6), AMBRE, 3.4, a)
    fleches_pression(c, t, 360, 640, [1050, 1140, 1230], a)
    O.dessiner(c, O.texte("CABINE", 380, 880, 34), VERT, 1.8, a)
    O.dessiner(c, O.texte("DEHORS", 940, 880, 34), VERT, 1.8, a)
    if t >= T["grande"]:
        O.curseur(c, 950, xc - 20, xc + 140, "", AMBRE, a, (t - T["grande"]) / 0.3)
        O.curseur(c, 1330, xc - 20, xc + 140, "", AMBRE, a, (t - T["grande"]) / 0.3)
    if t >= T["louvrir2"]:
        anime(c, t, T["louvrir2"], "sp_tire", 300, 1640, 380, 5, (2, 3, 4, 3), a=a)
    if t >= T["tirer"]:                                           # les barres « VS » d'un jeu de combat
        u = A.sortie((t - T["tirer"]) / 0.6)
        O.dessiner(c, O.texte("PASSAGER  50 KG", 110, 640, 30, centre=False, gras=True), VERT_PALE, 1.8, a)
        O.dessiner(c, [rect(110, 655, 110 + 20 * u, 685)], VERT, 3, a)
        txt = "10 000 KG  PRESSION"
        O.dessiner(c, O.texte(txt, 970 - O.largeur_texte(txt, 30), 735, 30, centre=False, gras=True), AMBRE, 1.8, a)
        O.dessiner(c, [rect(970 - 860 * u, 750, 970, 780)], AMBRE, 3, a)
        O.dessiner(c, O.texte("VS", W / 2, 715, 44, gras=True), AMBRE, 3, a)
    if t >= T["contre"]:
        tampon(c, t, T["contre"] + 0.3, "ÉCHEC", 330, 900, -8, 70, lambda: J.fichier("erreur", 0.35))


ALT_CROISIERE = 11000


def s5(c, t, a=1.0):
    phrase(c, t, T["attention"], ["*Mais attention*"], t1=T["descend"])
    phrase(c, t, T["descend"], ["Plus l'avion *descend*…"], t1=T["sol"])
    phrase(c, t, T["sol"], ["Au sol :", "*zéro*"])
    u = A.lisse((t - T["descend"]) / max(0.5, T["zero"] - T["descend"]))
    sprite(c, t, T["attention"] - 0.1, "sp_avion_3", 300 + 440 * u, 900 + 650 * u, 200, a, 0.4)
    O.dessiner(c, [[(80, 1660), (1000, 1660)]], VERT_PALE, 3, a)
    alt = ALT_CROISIERE * (1 - u)
    O.dessiner(c, O.segments(f"{alt:5.0f}", 400, 1100, 110), AMBRE, 5, a)
    O.dessiner(c, O.texte("M", 640, 1100, 70, gras=True), AMBRE, 3, a)
    O.dessiner(c, O.texte("FORCE SUR LA PORTE", 120, 720, 30, centre=False), VERT, 1.6, a)
    O.dessiner(c, [rect(120, 740, 960, 780)], VERT_PALE, 2, a)
    n = int(40 * (1 - u))
    O.dessiner(c, [rect(126 + i * 20.8, 746, 140 + i * 20.8, 774) for i in range(n)], AMBRE, 2.4, a)
    if t >= T["descend"]:
        ajoute(("descente",), T["descend"], lambda: J.carre(np.geomspace(900, 150, int(2.2 * MI.SR)), 2.2, 0.05, 0.25))


def s6(c, t, a=1.0):
    phrase(c, t, T["coree"], ["Corée du Sud", "*2023*"], t1=T["deux"])
    phrase(c, t, T["deux"], ["*200 m* du sol", "2 minutes avant"], t1=T["secours"])
    phrase(c, t, T["secours"], ["La porte", "*s'ouvre*"], t1=T["personne"])
    phrase(c, t, T["personne"], ["Personne", "n'est *aspiré*"])
    if t < T["secours"] - 0.1:                                    # l'approche
        u = A.lisse((t - T["coree"]) / 5.0)
        sprite(c, t, T["coree"] - 0.1, "sp_avion_4", 260 + 420 * u, 1250 + 250 * u, 220, a, 0.4)
        O.dessiner(c, [[(80, 1620), (1000, 1620)]], VERT_PALE, 3, a)
        for i in range(8):
            O.dessiner(c, [[(120 + i * 110, 1640), (170 + i * 110, 1640)]], VERT, 3, a)
        if t >= T["deux"]:
            O.ecart(c, 900, 1280 + 250 * u, 1620, "200 M", AMBRE, a)
        return
    O.dessiner(c, [[(80, 1580), (1000, 1580)]], VERT_PALE, 2.4, a)   # dans la cabine
    suite_images(c, t, [(T["secours"] - 0.1, 2), (T["secours"] + 0.6, 3)], "sp_porte", 900, 1580, 400, a)
    for i, x in enumerate((150, 360, 570)):
        k = 3 if T["vent"] <= t < T["personne"] + 0.8 else 1
        sprite(c, t, T["secours"] + 0.1 * i, f"sp_assis_{k}", x, 1580, 300, a, 0.4)
    if t >= T["vent"]:
        vent(c, t, 80, 840, 900, 1500, a)
        ajoute(("vent",), T["vent"], lambda: Z.vent(2.5, 0.12, 300, 2500))
    if t >= T["personne"]:
        tampon(c, t, T["personne"] + 0.3, "0 ASPIRÉ", 540, 820, -6, 64, lambda: J.fichier("confirmation", 0.3))


def s7(c, t, a=1.0):
    phrase(c, t, T["alors"], ["Et si elle", "*s'arrache* ?"], t1=T["arrive"])
    phrase(c, t, T["arrive"], ["Janvier *2024*", "5 000 m"], t1=T["souffle"])
    phrase(c, t, T["souffle"], ["Le souffle"], t1=T["telephones"])
    phrase(c, t, T["telephones"], ["Un téléphone", "retrouvé *intact*"])
    if t < T["souffle"]:
        nuages(c, t)
        tp = T["panneau"]
        sprite(c, t, T["alors"] - 0.1, "sp_avion_1" if t < tp else "sp_avion_2", W / 2, 1300, 300, a, 0.4)
        if t >= tp:                                               # le panneau qui s'envole en tournoyant
            ajoute(("panneau",), tp, lambda: J.fichier("boum_cine", 0.5, 3.0))
            u = (t - tp) / 1.6
            k = 3 + int((t - tp) * 6) % 2
            c.save()
            c.translate(470 - 300 * u, 1240 + 500 * u * u)
            c.rotate(200 * u)
            sprite(c, t, tp, f"sp_porte_{k}", 0, 60, 120, a, 0)
            c.restore()
        return
    if t < T["telephones"]:
        suite_images(c, t, [(T["souffle"] - 0.1, 2), (T["souffle"] + 0.5, 3)], "sp_souffle", 420, 1600, 520, a)
        vent(c, t, 200, 1000, 900, 1500, a)
        u = (t - T["tshirt"]) / 1.2
        if u > 0:
            c.save()
            c.translate(560 + 500 * u, 1060 - 200 * u)
            c.rotate(-90 * u)
            sprite(c, t, T["tshirt"], "sp_tshirt", 0, 60, 120, a, 0.2)
            c.restore()
            ajoute(("tshirt",), T["tshirt"], J.saut)
        return
    ti = T["intact"]                                              # le téléphone qui tombe… et atterrit
    if t < ti:
        u = (t - T["telephones"]) / max(0.5, ti - T["telephones"])
        anime(c, t, T["telephones"], "sp_tel", 540 + 80 * math.sin(4 * u), 700 + 900 * u, 260, 10, a=a)
        ajoute(("chute_tel",), T["telephones"], lambda: J.carre(np.geomspace(1500, 200, int(2.0 * MI.SR)), 2.0, 0.04, 0.25))
    else:
        sprite(c, t, ti, "sp_tel_1", 540, 1620, 260, a, 0)
        tampon(c, t, ti, "INTACT", 540, 1150, -6, 70, lambda: J.fichier("reussite", 0.3))
    O.dessiner(c, [[(80, 1620), (1000, 1620)]], VERT_PALE, 2.4, a)


def siege(cx, bas, lg=200, h=330):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(cx - lg / 2, bas - h, cx + lg / 2, bas - 120), 30, 30))
    q = skia.Path()
    q.addRRect(skia.RRect.MakeRectXY(skia.Rect(cx - lg / 2 - 10, bas - 140, cx + lg / 2 + 10, bas - 70), 20, 20))
    return O.contours(p, 6) + O.contours(q, 6) + [[(cx, bas - 70), (cx, bas)]]


def s8(c, t, a=1.0):
    phrase(c, t, T["sieges"], ["Les deux sièges", "à côté du trou ?"], t1=T["vides"])
    phrase(c, t, T["vides"], ["*VIDES*"])
    O.dessiner(c, [rect(860, 900, 1000, 1300)], AMBRE, 3, a)      # le trou
    vent(c, t, 860, 1000, 920, 1280, a, 6)
    for i, x in enumerate((360, 620)):
        O.dessiner(c, siege(x, 1500), VERT_PALE, 3, a, (t - T["sieges"] - 0.15 * i) / 0.5)
        O.dessiner(c, O.texte(f"26{'AB'[i]}", x, 1580, 40, gras=True), VERT, 2, a)
    if t >= T["vides"]:
        tampon(c, t, T["vides"], "VIDES", 490, 1000, -8, 80, lambda: J.fichier("confirmation", 0.3))
    if t >= T["assis"]:
        O.dessiner(c, O.texte("171 PASSAGERS - 7 SIÈGES LIBRES", W / 2, 1680, 34), VERT_PALE, 1.8, a, (t - T["assis"]) / 0.5)


def s9(c, t, a=1.0):
    phrase(c, t, T["celebre"], ["Le plus célèbre", "à avoir *sauté*"], t1=T["cooper"])
    phrase(c, t, T["cooper"], ["D. B. Cooper", "*1971*"], t1=T["jamais"])
    phrase(c, t, T["jamais"], ["*Jamais* retrouvé"], t1=T["depuis"])
    phrase(c, t, T["depuis"], ["Une *palette*", "bloque l'escalier"])
    sprite(c, t, T["celebre"] - 0.1, "sp_727", W / 2, 1000, 230, a, 0.5)
    if T["cooper"] <= t < T["depuis"]:
        etapes = [(T["cooper"], 1), (T["cooper"] + 0.6, 2), (T["cooper"] + 1.2, 3), (T["lescalier"] + 0.4, 4)]
        cour = [e for e in etapes if t >= e[0]][-1]
        u = A.lisse((t - T["cooper"] - 0.6) / 3.0)
        suite_images(c, t, etapes, "sp_cooper", 640 - 200 * u, 1300 + 300 * u, 420, a)
        if cour[1] == 4:
            ajoute(("parachute",), cour[0], lambda: J.carre(np.geomspace(300, 120, int(0.5 * MI.SR)), 0.5, 0.06))
    if t >= T["jamais"] and t < T["depuis"]:
        if int((t - T["jamais"]) * 3) % 2 == 0:
            O.dessiner(c, O.texte("?", 860, 1450, 220, gras=True), AMBRE, 6, a)
    if t >= T["palette"]:                                         # la palette « Cooper vane » sous la queue
        x, y = W / 2 - 150, 1000
        O.dessiner(c, [rect(x - 30, y - 10, x + 30, y + 40)], AMBRE, 4, a, (t - T["palette"]) / 0.3)
        O.dessiner(c, croix(x - 60, y + 60, 30), AMBRE, 6, a, (t - T["palette"] - 0.3) / 0.2)
        O.dessiner(c, O.texte("COOPER VANE", x, y + 140, 32, gras=True), AMBRE, 2, a)
        ajoute(("vane",), T["palette"], lambda: J.fichier("bascule", 0.35))


def s10(c, t, a=1.0):
    phrase(c, t, T["prochaine"], ["La prochaine fois…"], t1=T["calme"])
    phrase(c, t, T["calme"], ["Restez *calme*"], t1=T["ceinture"])
    phrase(c, t, T["ceinture"], ["Gardez votre", "*ceinture attachée*"])
    O.dessiner(c, [[(80, 1560), (1000, 1560)]], VERT_PALE, 2.4, a)
    k = 2 if t < T["ceinture"] else 4
    sprite(c, t, T["prochaine"] - 0.1, f"sp_assis_{k}", 460, 1560, 520, a, 0.5 if k == 2 else 0)
    sprite(c, t, T["prochaine"], "sp_porte_1", 880, 1560, 420, 0.6 * a, 0.4)
    if t >= T["ceinture"]:
        ajoute(("clic",), T["ceinture"] + 0.3, lambda: J.fichier("boucle_ceinture", 0.5))
        tampon(c, t, T["protege"], "PROTECTION MAX", 520, 860, -6, 56, J.niveau)


def fin(c, t, a=1.0):
    O.dessiner(c, [rect(80, 640, 1000, 1300)], AMBRE, 3, a)
    O.dessiner(c, O.texte("NIVEAU TERMINÉ", W / 2, 860, 70, gras=True), AMBRE, 4, a)
    O.dessiner(c, O.texte("ATTACHEZ VOTRE CEINTURE", W / 2, 1020, 44, gras=True), VERT_PALE, 2.6, a)
    O.dessiner(c, O.texte("SOURCES : NTSB, AP, FBI", W / 2, 1200, 26), VERT, 1.4, 0.8 * a)


def ecrans():
    return [(0.0, s1), (T["non"], s2), (T["onze"] - 0.1, s3), (T["bouchon"] - 0.1, s4), (T["attention"] - 0.1, s5),
            (T["coree"] - 0.1, s6), (T["alors"] - 0.1, s7), (T["sieges"] - 0.1, s8), (T["lhomme"] - 0.1, s9),
            (T["prochaine"] - 0.1, s10), (T["fin"], fin)]


# ------------------------------------------------------------------------------------------------ l'écran de jeu
def altitude(t):
    if t < T["attention"]:
        return ALT_CROISIERE
    if t < T["coree"]:
        return ALT_CROISIERE * (1 - A.lisse((t - T["descend"]) / max(0.5, T["zero"] - T["descend"])))
    if t < T["alors"]:
        return 200 * (1 - A.lisse((t - T["secours"]) / 4.0))
    if t < T["lhomme"]:
        return 4900
    return None


def hud(c, t, k):
    O.dessiner(c, O.texte(f"NIVEAU {k}", 90, 190, 30, centre=False, gras=True), VERT, 1.8, 0.9)
    alt = altitude(t)
    if alt is not None:
        txt = f"ALT {alt:,.0f} M".replace(",", " ")
        O.dessiner(c, O.texte(txt, 990 - O.largeur_texte(txt, 30), 190, 30, centre=False, gras=True), VERT, 1.8, 0.9)


BANDEAUX = [("debut", 0.0, 2.6, "! ALERTE : PORTE"), ("aspire", 0.0, 1.2, "! PORTE EN DANGER"), ("elephants", 0.2, 1.4, "x2 ÉLÉPHANTS"),
            ("zero", 0.0, 1.2, "PRESSION : 0"), ("secours", 0.0, 1.4, "! PORTE OUVERTE"),
            ("panneau", 0.0, 1.6, "! PANNEAU ARRACHÉ"), ("cooper", 0.0, 1.4, "AFFAIRE NON RÉSOLUE")]


def bandeaux(c, t):
    for rep, dt, d, txt in BANDEAUX:
        t0 = T[rep] + dt
        if t0 <= t < t0 + d and (int((t - t0) * 6) % 2 == 0 or t - t0 > 0.5):
            lg = O.largeur_texte(txt, 34) + 50
            O.dessiner(c, [rect(W / 2 - lg / 2, 560, W / 2 + lg / 2, 612)], AMBRE, 2.4)
            O.dessiner(c, O.texte(txt, W / 2, 600, 34, gras=True), AMBRE, 2.2)
            ajoute(("bandeau", rep), t0, lambda: J.alerte(1, 0.05))


AFFICHE = """Si un passager ouvre la porte|de l'avion en plein vol,|est-ce que|tout le monde est aspiré dehors ?|La réponse est non.|Il ne pourrait même pas l'ouvrir.|Et la raison va vous surprendre.|À 11 000 mètres,|l'air de la cabine|pousse sur la porte.|Environ 5 tonnes|par mètre|carré.|Sur toute la porte ?|À peu près 10 tonnes.|Le poids de|deux éléphants.|Et cette porte est un bouchon.|Elle est plus grande que son trou.|Pour l'ouvrir,|il faut d'abord la tirer vers l'intérieur.|Contre 10 tonnes.|Mais attention.|Plus l'avion descend,|plus cette force diminue.|Au sol,|elle tombe à zéro.|Corée du Sud,|2023.|À 200 mètres du sol, 2 minutes avant l'atterrissage,|un passager ouvre la porte de secours.|Le vent s'engouffre dans la cabine.|Personne n'est aspiré.|L'avion se pose.|Alors…|et si la porte s'arrache toute seule,|en altitude ?|C'est arrivé.|Janvier 2024,|à 5 000 mètres.|Un panneau de porte s'arrache d'un Boeing.|Le souffle arrache le t-shirt d'un adolescent.|Des téléphones s'envolent.|L'un d'eux est retrouvé par terre…|intact.|Et les deux sièges juste à côté du trou ? Vides.|Ce jour-là,|personne n'y était assis.|Et l'homme le plus célèbre à avoir sauté d'un avion de ligne en vol ?|D. B. Cooper,|1971,|par l'escalier arrière.|On ne l'a jamais retrouvé.|Depuis, une|petite|palette bloque cet escalier en vol.|Alors la prochaine fois qu'un passager regarde la porte d'un peu trop|près,|restez calme.|Et gardez votre ceinture attachée.|C'est elle qui vous|protège,|pas la porte.""".split("|")
MORCEAUX = []


def lignes_st(txt, larg=880, h=36):
    out, cour = [], ""
    for m in txt.split():
        essai = (cour + " " + m).strip()
        if O.largeur_texte(essai, h) > larg and cour:
            out.append(cour)
            cour = m
        else:
            cour = essai
    return out + [cour] if cour else out


def sous_titres(c, t):
    for a, b, txt in MORCEAUX:
        if a - 0.05 <= t < b + 0.35 and txt:
            u = min(1.0, (t - a + 0.05) / max(0.3, b - a))
            ls = lignes_st(txt.upper())
            k = int(sum(len(l) for l in ls) * u + 0.999)
            for i, l in enumerate(ls):
                vis = l[:max(0, k)]
                k -= len(l)
                if vis:
                    x = W / 2 - O.largeur_texte(l, 36) / 2
                    O.dessiner(c, O.texte(vis, x, 1745 + i * 50 - 50 * (len(ls) - 1), 36, centre=False), VERT_PALE, 1.8, 0.9)
            return


def image(c, t):
    O.ecran(c, t)
    ec = ecrans()
    k = max(i for i, x in enumerate(ec) if x[0] <= t)
    for i in range(1, len(ec) - 1):                               # enchaînement : fondu rapide (pas vers s2 : coupe)
        b = ec[i][0]
        if b - 0.2 <= t < b + 0.2 and ec[i][1] is not s2 and ec[i - 1][1] is not s2:
            u = (t - b + 0.2) / 0.4
            c.saveLayerAlpha(None, int(255 * (1 - A.lisse(u / 0.6))))
            ec[i - 1][1](c, t)
            c.restore()
            c.saveLayerAlpha(None, int(255 * A.lisse((u - 0.4) / 0.6)))
            ec[i][1](c, t)
            c.restore()
            ajoute(("whoosh", i), b - 0.2, lambda: J.fichier("swoosh_court", 0.18))
            break
    else:
        z, dx, dy = 1.0, 0.0, 0.0
        for tw in (0.0, T["non"], T["toute"], T["contre"], T["panneau"], T["vides"]):
            if t >= tw:
                z += 0.05 * math.exp(-6 * (t - tw))
                dx += 26 * A.secousse(t - tw, 7, 7)                # la caméra encaisse le choc
                dy += 14 * A.secousse(t - tw, 9, 7)
        c.save()
        c.translate(W / 2 + dx, H / 2 + dy)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        ec[k][1](c, t)
        c.restore()
    if ec[k][1] is s2 and t < T["onze"] - 0.1:                    # ⏸ arrêt sur image
        O.dessiner(c, [rect(90, 660, 104, 700), rect(116, 660, 130, 700)], VERT_PALE, 3)
        O.dessiner(c, O.texte("ARRÊT SUR IMAGE", 150, 692, 30, centre=False), VERT_PALE, 1.6)
        if t < T["non"] + 0.12:
            rng = np.random.default_rng(int(t * 1000))
            O.dessiner(c, [[(x, y), (x + 3, y)] for x, y in rng.uniform(0, 1, (900, 2)) * (W, H)], VERT_PALE, 2, 0.8)
    if t < 0.15:                                                  # flash blanc de l'image 0
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(255, 255, 255, int(200 * (1 - t / 0.15)))))
    if ec[k][1] is not fin:
        hud(c, t, k + 1)
        bandeaux(c, t)
        sous_titres(c, t)
        if B.VOIX is not None:
            O.oscillogramme(c, B.VOIX, MI.SR, t, y=470, x0=220, x1=860, ampli=30)


def sons_fixes():
    return [(0.0, lambda: J.fichier("boum_cine", 0.55, 2.5)), (0.0, lambda: J.fichier("glitch", 0.35)),
            (0.02, lambda: J.fichier("impact", 0.3))] + [(0.15 + 0.5 * i, lambda: J.alerte(1, 0.05))
                                                           for i in range(int(T["non"] / 0.5))] + [
            (T["non"], lambda: J.fichier("arret", 0.3)),
            (T["non"] + 0.05, lambda: J.fichier("erreur", 0.35)), (T["non"], lambda: J.fichier("boum_cine", 0.35, 2.0)),
            (T["non"], lambda: Z.neige(0.22, 0.2)), (T["surprendre"], lambda: J.fichier("question", 0.28)),
            (T["cabine"], lambda: J.fichier("souffle_sombre", 0.18)), (T["toute"] + 0.8, lambda: J.fichier("impact", 0.25)),
            (T["zero"], lambda: J.fichier("reussite", 0.25)), (T["secours"], lambda: J.fichier("porte", 0.4)),
            (T["vent"], lambda: J.fichier("swoosh", 0.25)), (T["lavion"], lambda: J.fichier("atterrissage", 0.2, 2.5)),
            (T["panneau"], lambda: J.fichier("glitch", 0.3)), (T["intact"], lambda: J.fichier("chute", 0.45)),
            (T["cooper"], lambda: J.fichier("roulement", 0.15, 1.6)), (T["jamais"], lambda: J.fichier("mystere", 0.22, 3.0)),
            (T["palette"] + 0.3, lambda: J.fichier("reussite", 0.25)), (T["fin"], lambda: J.fichier("ouverture", 0.3)), (T["louvrir2"], lambda: J.carre(np.linspace(120, 100, int(2 * MI.SR)), 2.0, 0.03, 0.25)),
            (T["zero"], J.piece), (T["coree"], lambda: J.fichier("selection", 0.25)), (T["arrive"], lambda: J.alerte(2)),
            (T["souffle"], lambda: Z.vent(2.0, 0.14, 300, 3000)), (T["celebre"], J.selection),
            (T["calme"], lambda: J.fichier("selection", 0.25)), (T["fin"] + 0.3, J.niveau)]


def famille(snd):
    """Range un bruitage dans une famille de mixage d'après sa forme : bip court, accent grave, ambiance longue…"""
    from scipy.signal import butter, sosfiltfilt
    d = len(snd) / MI.SR
    e = np.sqrt(np.mean(snd ** 2)) + 1e-12
    grave = np.sqrt(np.mean(sosfiltfilt(butter(2, 200, fs=MI.SR, output="sos"), snd) ** 2)) / e
    crete = 20 * np.log10(np.abs(snd).max() / e + 1e-12)
    if grave > 0.55 and crete > 10:
        return "accent"
    if d < 0.12:
        return "interface"
    if d > 1.5:
        return "ambiance"
    return "effet"


def mixage(chemin, voix, dur):
    from films.styles import mixage_pro as MP
    ev = []
    for cle, (t0, fab) in list(SONS.items()) + [((("fixe", i),), x) for i, x in enumerate(sons_fixes())]:
        snd = np.asarray(fab(), float)
        if snd.ndim > 1:
            snd = snd.mean(1)
        fam = famille(snd)
        pan = ((hash(str(cle)) % 100) / 100 - 0.5) * 0.5 if fam == "interface" else 0.0
        ev.append((t0, snd, fam, pan))
    MP.mixer(chemin, voix, dur, ev)


REPERES = [("porte", "porte", None), ("aspire", "aspire", None), ("non", "non", None), ("ouvrir", "louvrir", None),
           ("surprendre", "surprendre", None), ("onze", "onze", None), ("cabine", "cabine", None),
           ("cinq", "cinq", "cabine"), ("toute", "toute", "cinq"), ("poids", "poids", None),
           ("elephants", "elephants", None), ("bouchon", "bouchon", None), ("grande", "grande", "bouchon"),
           ("louvrir2", "louvrir", "grande"), ("tirer", "tirer", None), ("contre", "contre", None),
           ("attention", "attention", None), ("descend", "descend", None), ("sol", "sol", "descend"),
           ("zero", "zero", None), ("coree", "coree", None), ("deux", "cents", "coree"), ("secours", "secours", None),
           ("vent", "vent", "secours"), ("personne", "personne", "vent"), ("lavion", "lavion", "personne"),
           ("alors", "alors", "lavion"), ("arrive", "arrive", None), ("panneau", "panneau", None),
           ("souffle", "souffle", None), ("tshirt", "tshirt", None), ("telephones", "telephones", None),
           ("intact", "intact", None), ("sieges", "sieges", "intact"), ("vides", "vides", None),
           ("assis", "assis", "vides"), ("lhomme", "lhomme", None), ("celebre", "celebre", None),
           ("cooper", "cooper", None), ("lescalier", "lescalier", None), ("jamais", "jamais", None),
           ("depuis", "depuis", None), ("palette", "palette", None), ("prochaine", "prochaine", None),
           ("calme", "calme", None), ("ceinture", "ceinture", None), ("protege", "protege", None)]


def preparer():
    chemin = os.path.join(ICI, "audio", "voix.mp3")
    MV.charger(types.SimpleNamespace(SEGS=os.path.join(ICI, "audio", "voix.json"), VOIX=chemin))
    B.VOIX, N, _ = MI.tighten(MI.load_voice(chemin), max_gap=0.40, thr_db=-38.0)
    T.clear()
    T["debut"] = 0.0
    for nom, cle, apres in REPERES:
        T[nom] = MV.mot(cle, T[apres] + 0.01 if apres else 0.0)
    T["fin"] = MV.MOTS[-1][1] + 0.6
    d = json.load(open(os.path.join(ICI, "audio", "voix.json")))
    MORCEAUX[:] = [(N(a), N(b), txt) for (a, b, _), txt in zip(d, AFFICHE)]
    return B.VOIX


# le moteur de rendu de l'ép. 30, branché sur cet épisode
B.preparer, B.image, B.mixage = preparer, image, mixage
B.FPS = 60                                                         # 60 images/s : mouvement plus fluide

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep31.mp4"
    if len(sys.argv) > 3:
        B.rendre(out, float(sys.argv[2]), float(sys.argv[3]))
    else:
        B.rendre(out)
