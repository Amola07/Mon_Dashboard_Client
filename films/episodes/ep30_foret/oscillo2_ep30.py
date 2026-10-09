"""Épisode 30 — « La forêt française a doublé » — en « oscilloscope 2.0 » (≈ 1 min 55).

Ton et rythme des vidéos de référence (films/styles/analyse_archibald.md) : une idée par tableau, chaque élément naît
du précédent, chiffres construits à l'écran, tampons, « MAIS ATTENDEZ », fin coupée. Dessins : planches 21-23
(films/planches_ia/planche2[123]_*.webp → films/illustrations_vecteur/vx_*.json). Cartes : vraies frontières
(world-atlas, Natural Earth 1:50 m) → films/illustrations_vecteur/carte_france_autriche.json.

    python -m films.episodes.ep30_foret.oscillo2_ep30 output/ep30.mp4
    python -m films.episodes.ep30_foret.oscillo2_ep30 output/extrait.mp4 40 60      (un extrait)
    OSC_THEME=papier python -m …                                                     (noir sur papier)
"""
import json
import math
import os
import subprocess
import sys
import tempfile
import types
import wave

import numpy as np
import skia

from films import montage_ia as MI
from films.outils import mots_voix as MV
from films.styles import anim_pro as A
from films.styles import oscillo2 as O
from films.styles import oscillo_son as Z
from films.styles.oscillo2 import AMBRE, VERT, VERT_PALE, VERT_SOMBRE, W, H

ICI = os.path.dirname(os.path.abspath(__file__))
FPS = 30
VOIX = None                               # la voix (silences resserrés)
T = {}                                    # les instants des mots-repères (calculés par preparer)
_T, _T0 = 0.0, 0.0                        # l'instant courant et le début de l'écran en cours


# ------------------------------------------------------------------------------------------------ outils
def phrase(c, t, t0, lignes, t1=None, y=300, h=64):
    """La phrase en haut, écrite par le faisceau ; *…* = en ambre."""
    if t < t0 or (t1 is not None and t >= t1):
        return
    u = (t - t0) / 0.45
    for i, ligne in enumerate(lignes):
        larg = O.largeur_texte(ligne.replace("*", ""), h)
        x = W / 2 - larg / 2
        for j, m in enumerate(ligne.split("*")):
            if m:
                O.dessiner(c, O.texte(m, x, y + i * h * 1.45, h, centre=False, gras=True), AMBRE if j % 2 else VERT_PALE,
                           5.0 if O.PAPIER and j % 2 else 3.2, 1.0, u)
            x += O.largeur_texte(m, h)


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def croix(cx, cy, r=40):
    return [[(cx - r, cy - r), (cx + r, cy + r)], [(cx + r, cy - r), (cx - r, cy + r)]]


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


def icone(c, nom, cx, bas, h, a=1.0, u=None, hach=("ambre", "vert")):
    """Un dessin ; sans u, il se trace au faisceau à l'ouverture de son écran."""
    if u is None:
        u = 1.0 if _T0 <= 0 else (_T - _T0 + 0.25) / 0.9
    if u <= 0:
        return None
    return O.dessiner_icone_sobre(c, nom, cx, bas, h, a, u, hach)


def apparait(c, t, t0, nom, cx, bas, h, a=1.0, d=0.6, hach=("ambre", "vert")):
    """Un dessin qui se trace au faisceau à partir de t0 (avec un petit rebond d'échelle)."""
    if t < t0:
        return
    k = A.rebond(min(1.0, (t - t0) / 0.35)) if t - t0 < 0.35 else 1.0
    c.save()
    c.translate(cx, bas)
    c.scale(0.85 + 0.15 * k, 0.85 + 0.15 * k)
    c.translate(-cx, -bas)
    O.dessiner_icone_sobre(c, nom, cx, bas, h, a, (t - t0) / d, hach)
    c.restore()


def fondu(t, t0, t1=None, d=0.3):
    a = A.lisse((t - t0) / d)
    if t1 is not None:
        a *= 1 - A.lisse((t - t1) / d)
    return a


def compteur(c, t, t0, v0, v1, x, y, h, d=0.9, fmt="{:.0f}", col=AMBRE, a=1.0):
    v = v0 + (v1 - v0) * A.sortie((t - t0) / d, 2.5)
    O.dessiner(c, O.segments(fmt.format(v), x, y, h), col, max(3, h / 22), a)


def arbre_glyphe(x, y, s=1.0):
    """Un petit arbre au trait (houppier rond + tronc), pour peupler les cartes."""
    p = skia.Path()
    p.addCircle(x, y - 13 * s, 9 * s)
    return O.contours(p, 4) + [[(x, y - 4 * s), (x, y + 6 * s)]]


# ------------------------------------------------------------------------------------------------ les cartes
_CARTES = json.load(open(os.path.join(ICI, "..", "..", "illustrations_vecteur", "carte_france_autriche.json")))
_COS = math.cos(math.radians(46.5))
_FR_LON, _FR_LAT = (-4.8 + 9.6) / 2, (41.3 + 51.1) / 2       # le centre de la France métropolitaine


def proj(lon, lat, cx, cy, k):
    return cx + (lon - _FR_LON) * _COS * k, cy - (lat - _FR_LAT) * k


def carte(pays, cx, cy, k, dx=0.0, dy=0.0):
    return [[(x + dx, y + dy) for x, y in (proj(lon, lat, cx, cy, k) for lon, lat in r)] for r in _CARTES[pays]]


def chemin_carte(traits):
    p = skia.Path()
    for l in traits:
        p.addPoly([skia.Point(x, y) for x, y in l], True)
    return p


FR_CX, FR_CY, FR_K = 540, 1080, 78                            # la carte en grand
_FR = carte("France", FR_CX, FR_CY, FR_K)
_FR_P = chemin_carte(_FR)
_RNG = np.random.default_rng(30)
_PTS = []                                                     # des points au hasard dans la France (les arbres)
while len(_PTS) < 200:
    x, y = _RNG.uniform(220, 860), _RNG.uniform(680, 1480)
    if _FR_P.contains(x, y):
        _PTS.append((x, y))
_PTS.sort(key=lambda p: _RNG.uniform())


def foret_carte(c, t, t0, n, a=1.0, d=1.2):
    """n arbres qui poussent en rafale dans la carte à partir de t0."""
    tr = []
    for i, (x, y) in enumerate(_PTS[:n]):
        ti = t0 + d * i / max(1, n)
        if t >= ti:
            tr += arbre_glyphe(x, y, 0.6 + 0.4 * A.rebond(min(1.0, (t - ti) / 0.3)))
    O.dessiner(c, tr, VERT, 1.8, 0.9 * a)


# ------------------------------------------------------------------------------------------------ 1. l'accroche
def e1(c, t, a=1.0):
    phrase(c, t, -1.0, ["Une forêt grande", "comme *l'Autriche*"], t1=T["personne"] - 0.4)
    phrase(c, t, T["personne"] - 0.4, ["Et presque *personne*", "n'est au courant"])
    O.dessiner(c, _FR, VERT_PALE, 3.2, a, (t + 0.4) / 1.2)
    foret_carte(c, t, 0.4, 110, a, 1.6)
    ta = T["autriche"] - 0.1
    if t >= ta:                                                # l'Autriche, à la même échelle, glisse dans la France
        u = A.lisse((t - ta) / 0.9)
        dx, dy = (1 - u) * 520 - 150 * u, (1 - u) * -60 + 120 * u
        au = carte("Austria", FR_CX, FR_CY, FR_K, dx - 640, dy + 60)
        p = chemin_carte(au)
        O.hachures(c, p, AMBRE, 6, -35, 1.6, 0.8 * a)
        O.dessiner(c, au, AMBRE, 3.4, a)
        if u >= 1:
            O.dessiner(c, O.texte("AUTRICHE", 330, 1300, 34, gras=True), AMBRE, 2.2, a, (t - ta - 0.9) / 0.3)
    if t >= T["personne"]:
        O.dessiner(c, O.texte("+ 8 MILLIONS D'HECTARES", W / 2, 1600, 44, gras=True), AMBRE, 2.6, a,
                   (t - T["personne"]) / 0.5)


# ------------------------------------------------------------------------------------------------ 2. le cliché
def e2(c, t, a=1.0):
    phrase(c, t, T["quand"], ["Vous pensez", "sûrement *à ça*"], t1=T["normal"])
    phrase(c, t, T["normal"], ["*Normal.*", "Moi aussi."])
    apparait(c, t, T["coupes"] - 0.15, "vx_tronconneuse", 330, 960, 170, a)
    apparait(c, t, T["coupes"] + 0.2, "vx_souches", 760, 1020, 260, a)
    apparait(c, t, T["incendies"] - 0.1, "vx_arbre_feu", 330, 1500, 420, a)
    if t >= T["incendies"]:
        for i in range(6):                                     # la fumée qui monte
            ph = (t * 0.6 + i / 6) % 1
            y = 1080 - 220 * ph
            O.dessiner(c, [[(330 + 30 * math.sin(6 * ph + i) + dx, y + dy) for dx, dy in ((-18, 0), (0, -10), (18, 0))]],
                       VERT, 2, (1 - ph) * a)
    td = T["disparaissent"] - 0.1
    if t >= td:                                                # un arbre qui s'efface trait par trait
        O.dessiner_icone_sobre(c, "vx_chene", 760, 1500, 400, a * (1 - 0.75 * A.lisse((t - td - 0.3) / 0.8)),
                               min(1.0, (t - td) / 0.5), ("ambre", "vert"))
    tampon(c, t, T["normal"], "CLICHÉ", 540, 1260, -8, 70)


# ------------------------------------------------------------------------------------------------ 3. la vraie courbe
LANDES = proj(-0.9, 44.1, FR_CX, FR_CY, FR_K)


def e3(c, t, a=1.0):
    phrase(c, t, T["sauf"], ["*1830*"], t1=T["aujourdhui"])
    phrase(c, t, T["aujourdhui"], ["*Aujourd'hui*"], t1=T["tiers"])
    phrase(c, t, T["tiers"], ["*Un tiers* du pays"], t1=T["double"] - 0.2)
    phrase(c, t, T["double"] - 0.2, ["Elle a presque", "*doublé*"])
    O.dessiner(c, _FR, VERT_PALE, 3.2, a, (t - T["sauf"] + 0.25) / 0.8)
    n = 90 if t < T["aujourdhui"] else 90 + int(85 * A.sortie((t - T["aujourdhui"]) / 1.2, 2))
    foret_carte(c, t, T["neuf"] - 0.3, n, a, n / 90)
    an = 1830 if t < T["aujourdhui"] else 1830 + 196 * A.sortie((t - T["aujourdhui"]) / 1.0, 2)
    O.dessiner(c, O.segments(f"{an:4.0f}", 860, 640, 70), VERT, 3.2, a)
    if t >= T["neuf"] - 0.2:
        v = 9.0 if t < T["dixsept"] else 9.0 + 8.5 * A.sortie((t - T["dixsept"]) / 1.0, 2.5)
        O.dessiner(c, O.segments(f"{v:4.1f}", 390, 1660, 120), AMBRE, 5.5, a)
        O.dessiner(c, O.texte("MILLIONS", 650, 1600, 40, centre=False, gras=True), AMBRE, 2.4, a)
        O.dessiner(c, O.texte("D'HECTARES", 650, 1660, 40, centre=False, gras=True), AMBRE, 2.4, a)
    if t >= T["double"]:
        tampon(c, t, T["double"], "x 2", 820, 820, 8, 70)
    tl = T["landes1"]
    if t >= tl:                                                # les Landes : un cercle qui pulse
        r = 46 + 10 * math.sin(6 * (t - tl))
        p = skia.Path()
        p.addCircle(*LANDES, r)
        O.dessiner(c, O.contours(p, 5), AMBRE, 4, a, (t - tl) / 0.4)
        O.dessiner(c, O.texte("LANDES", LANDES[0] - 70, LANDES[1] + 100, 34, gras=True), AMBRE, 2.2, a, (t - tl) / 0.4)


# ------------------------------------------------------------------------------------------------ 4. l'exode rural
def champ(c, t, t0, x0, x1, y0, y1, a=1.0):
    """Les sillons d'un champ, en perspective."""
    tr = [[(x0 + (x1 - x0) * i / 11, y1), (x0 + (x1 - x0) * (0.3 + 0.4 * i / 11), y0)] for i in range(12)]
    O.dessiner(c, tr, VERT, 1.6, 0.7 * a, (t - t0) / 0.6)


def e4(c, t, a=1.0):
    phrase(c, t, T["comment"], ["Comment c'est", "*possible ?*"], t1=T["paysans"])
    phrase(c, t, T["paysans"], ["L'exode *rural*"], t1=T["champs"])
    phrase(c, t, T["champs"], ["Les champs", "redeviennent des *bois*"], t1=T["seuls"])
    phrase(c, t, T["seuls"], ["*Tout seuls*"])
    O.dessiner(c, [[(80, 1460), (1000, 1460)]], VERT_SOMBRE, 2, a)
    if t >= T["paysans"] - 0.2:                                 # le paysan part vers la ville
        apparait(c, t, T["paysans"] + 0.3, "vx_ville_1850", 860, 1460, 300, a)
        apparait(c, t, T["paysans"] - 0.2, "vx_ferme", 230, 1460, 230, a * (1 - 0.5 * A.lisse((t - T["champs"]) / 0.5)))
        px = 300 + 380 * A.lisse((t - T["paysans"] - 0.2) / 2.2)
        if t < T["champs"] + 0.6:
            icone(c, "vx_paysan", px, 1460, 300, a * (1 - A.lisse((t - T["champs"]) / 0.6)), 1.0)
    if t >= T["champs"]:                                       # le champ abandonné : les arbres reviennent
        champ(c, t, T["champs"], 120, 700, 1480, 1640, a)
        for i, x in enumerate((180, 320, 460, 600)):
            ti = T["redevenus"] + 0.18 * i
            if t < ti:
                continue
            u = A.lisse((t - ti) / 1.0)
            nom = "vx_pousse" if u < 0.5 else "vx_chene"
            O.dessiner_icone_sobre(c, nom, x, 1640, 110 + 190 * u, a, 1.0 if u > 0.05 else u * 20, ("ambre", "vert"))


# ------------------------------------------------------------------------------------------------ 5. les Landes
def marais(c, t, a=1.0, x0=100, x1=980, y0=1380, y1=1640):
    p = skia.Path()
    p.addRect(skia.Rect(x0, y0, x1, y1))
    O.hachures(c, p, VERT, 14, 0, 1.2, 0.35 * a)
    for j in range(3):
        y = y0 + 20 + 80 * j
        O.dessiner(c, [[(x, y + 5 * math.sin(x / 70 + 2 * t + j)) for x in range(x0, x1 + 1, 12)]], VERT, 2, 0.7 * a)


def e5(c, t, a=1.0):
    tl, tp = T["dixhuit2"], T["planter"]
    phrase(c, t, T["landes2"], ["Les Landes,", "il y a *170 ans*"], t1=T["bergers"])
    phrase(c, t, T["bergers"], ["Des bergers", "sur des *échasses*"], t1=tl)
    phrase(c, t, tl, ["*1857*"], t1=T["resultat"])
    phrase(c, t, T["resultat"], ["*1 million* d'hectares", "de pins"])
    ab = 1 - A.lisse((t - tp - 0.3) / 0.6)                     # le marais et le berger s'en vont quand on plante
    if ab > 0:
        marais(c, t, a * ab)
        apparait(c, t, T["landes2"] + 0.1, "vx_mouton", 300, 1420, 180, a * ab)
        apparait(c, t, T["bergers"] - 0.2, "vx_berger_echasses", 640, 1430, 720, a * ab)
    if tl <= t:
        O.dessiner(c, O.segments("1857", W / 2, 700, 130), AMBRE, 6, a * (1 - A.lisse((t - tp) / 0.4)))
    if t >= tl + 0.6:
        O.dessiner(c, O.texte("LOI : LES COMMUNES DOIVENT PLANTER", W / 2, 790, 36), VERT_PALE, 2, a * (1 - A.lisse((t - tp - 0.2) / 0.4)),
                   (t - tl - 0.6) / 0.6)
    if t >= tp:                                                # des rangées de pins, en rafale
        for r, (y, h, n) in enumerate([(1180, 300, 6), (1420, 380, 5), (1660, 460, 4)]):
            for i in range(n):
                ti = tp + 0.12 * (i + n * r) * 0.6
                if t >= ti:
                    x = 140 + (800 / (n - 1)) * i + (40 if r % 2 else 0)
                    apparait(c, t, ti, "vx_pin", x, y, h, a * (0.55 + 0.15 * r), 0.4)


# ------------------------------------------------------------------------------------------------ 6. la route des vacances
def e6(c, t, a=1.0):
    phrase(c, t, T["cette"], ["La route", "des *vacances*"], t1=T["plantee"] - 0.1)
    phrase(c, t, T["plantee"] - 0.1, ["Plantée par", "*l'homme*"])
    dt = t - T["cette"]
    for r, (y, h, ec, v) in enumerate([(1180, 330, 230, 90), (1580, 440, 300, 220)]):   # deux rangées, parallaxe
        for i in range(7):
            x = (i * ec - v * dt) % (7 * ec) - 150
            O.dessiner_icone_sobre(c, "vx_pin", x, y, h, a * (0.5 + 0.25 * r), 1.0, ("vert",))
    O.dessiner(c, [[(60, 1600), (1020, 1600)]], VERT_PALE, 3, a)
    for i in range(8):                                         # le marquage au sol qui défile
        x = (i * 160 - 420 * dt) % 1280 - 100
        O.dessiner(c, [[(x, 1640), (x + 70, 1640)]], VERT, 3, a)
    rebond = 4 * abs(math.sin(9 * t))
    icone(c, "vx_voiture_vacances", 540, 1600 - rebond, 230, a, 1.0)
    tampon(c, t, T["plantee"] + 0.3, "PLANTÉE", 540, 800, -6, 70)


# ------------------------------------------------------------------------------------------------ 7. le biais
def e7a(c, t, a=1.0):
    phrase(c, t, T["alors"], ["Pourquoi on croit", "qu'elle *recule* ?"], t1=T["truc"])
    phrase(c, t, T["truc"], ["Notre *cerveau*"], t1=T["degrade"])
    phrase(c, t, T["degrade"], ["Biais de", "*négativité*"])
    if t < T["degrade"] + 0.2:
        apparait(c, t, T["alors"] - 0.1, "vx_cerveau", 540, 1420, 560, a)
        return
    u = A.lisse((t - T["degrade"]) / 0.6)                      # la balance penche : le négatif pèse plus
    icone(c, "vx_cerveau", 540, 900, 260, a, 1.0)
    ang = -14 * A.ressort(t - T["ameliore"]) if t >= T["ameliore"] else 0
    c.save()
    c.translate(540, 1430)
    c.rotate(ang * u if t >= T["ameliore"] else -6 * u)
    c.translate(-540, -1430)
    icone(c, "vx_balance", 540, 1560, 430, a, 1.0)
    c.restore()
    O.dessiner(c, O.texte("SE DÉGRADE", 330, 1640, 36, gras=True), AMBRE, 2.4, a, (t - T["degrade"]) / 0.4)
    if t >= T["ameliore"]:
        O.dessiner(c, O.texte("S'AMÉLIORE", 760, 1640, 36, gras=True), VERT, 2.2, a, (t - T["ameliore"]) / 0.4)


def e7b(c, t, a=1.0):
    phrase(c, t, T["incendie"], ["Au journal", "de *20 heures*"], t1=T["arbre2"])
    phrase(c, t, T["arbre2"], ["Un arbre", "qui pousse"], t1=T["jamais"])
    phrase(c, t, T["jamais"], ["*Jamais.*"])
    icone(c, "vx_tele", 540, 1540, 760, a)
    cx, cy = 505, 1210                                         # l'écran de la télé
    if t < T["arbre2"]:
        apparait(c, t, T["incendie"] + 0.2, "vx_arbre_feu", cx, cy + 150, 290, a)
    else:
        apparait(c, t, T["arbre2"], "vx_pousse", cx, cy + 140, 230, a)
    if t >= T["jamais"]:
        O.dessiner(c, croix(cx, cy, 160), AMBRE, 8, a, (t - T["jamais"]) / 0.2)


# ------------------------------------------------------------------------------------------------ 8. mais attendez
def e8(c, t, a=1.0):
    k = 1 + 0.3 * max(0.0, 1 - (t - T["attendez"] + 0.2) / 0.15)
    c.save()
    c.translate(W / 2, 960)
    c.scale(k, k)
    O.dessiner(c, O.texte("MAIS", 0, -40, 130, gras=True), VERT_PALE, 5, a)
    O.dessiner(c, O.texte("ATTENDEZ.", 0, 120, 130, gras=True), VERT_PALE, 5, a)
    c.restore()
    if t >= T["inquietant"] - 0.1:
        O.dessiner(c, O.texte("ÇA DEVIENT INQUIÉTANT", W / 2, 1260, 44, gras=True), AMBRE, 2.6, a,
                   (t - T["inquietant"] + 0.1) / 0.5)


# ------------------------------------------------------------------------------------------------ 9. l'éponge à CO2
def fleches_co2(c, t, cx, cy, n, r0, r1, a=1.0, entrant=True):
    """Des molécules de CO2 qui convergent vers (cx, cy)."""
    tr = []
    for i in range(n):
        ang = 2 * math.pi * (i + 0.5) / n + 0.3
        ph = (t * 0.7 + i * 0.29) % 1.0
        r = r1 - (r1 - r0) * ph if entrant else r0 + (r1 - r0) * ph
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        for ox in (-16, 0, 16):
            p = skia.Path()
            p.addCircle(x + ox * math.cos(ang + 1.57), y + ox * math.sin(ang + 1.57), 7 if ox else 9)
            tr += O.contours(p, 4)
    O.dessiner(c, tr, VERT, 2, 0.8 * a)


def barre(c, t, t0, x, val, label, col, a=1.0, d=0.8, ech=9.0, bas=1560):
    if t < t0:
        return
    v = val * A.sortie((t - t0) / d, 2.5)
    p = skia.Path()
    p.addRect(skia.Rect(x - 90, bas - v * ech, x + 90, bas))
    O.hachures(c, p, col, 8, -35, 1.6, 0.8 * a)
    O.dessiner(c, [rect(x - 90, bas - v * ech, x + 90, bas)], col, 3, a)
    O.dessiner(c, O.segments(f"{v:2.0f}", x, bas - v * ech - 30, 80), col, 4, a)
    O.dessiner(c, O.texte(label, x, bas + 60, 32), VERT_PALE, 1.8, a)


def e9(c, t, a=1.0):
    te, tb = T["eponge"], T["entre"]
    phrase(c, t, T["foret3"], ["Une éponge", "à *CO2*"], t1=tb)
    phrase(c, t, tb, ["Millions de tonnes", "de CO2 *par an*"], t1=T["avis"])
    phrase(c, t, T["avis"], ["*À votre avis ?*"], t1=T["trente"])
    phrase(c, t, T["trente"], ["*- 40 %*", "en dix ans"])
    if t < tb:
        if t < te:
            icone(c, "vx_chene", 540, 1480, 640, a)
        else:
            k = A.lisse((t - te) / 0.5)
            c.saveLayerAlpha(None, int(255 * (1 - k) * a))
            icone(c, "vx_chene", 540, 1480, 640, 1.0, 1.0)
            c.restore()
            c.saveLayerAlpha(None, int(255 * k * a))
            icone(c, "vx_eponge", 540, 1420, 520, 1.0, 1.0)
            c.restore()
            for tr, it in A.flux(("ep30_eponge",), O.silhouette("vx_chene", 540, 1480, 640),
                                 O.silhouette("vx_eponge", 540, 1420, 520), k):
                O.dessiner(c, tr, AMBRE, 3, it * a)
            if t >= T["co"]:
                fleches_co2(c, t, 540, 1160, 10, 300, 470, a * A.lisse((t - T["co"]) / 0.4))
        return
    O.dessiner(c, [[(120, 1560), (960, 1560)]], VERT_PALE, 2.4, a)
    barre(c, t, T["cinq"], 300, 63, "2005-2013", VERT, a)
    if T["avis"] <= t < T["trente"]:
        if int((t - T["avis"]) * 4) % 2 == 0:
            O.dessiner(c, O.texte("?", 760, 1400, 220, gras=True), AMBRE, 6, a)
    barre(c, t, T["trente"], 760, 39, "2014-2022", AMBRE, a)
    if t >= T["quarante"]:                                     # les curseurs : l'écart entre les deux barres
        u = A.lisse((t - T["quarante"]) / 0.4)
        O.curseur(c, 1560 - 63 * 9, 220, 960, "", VERT_PALE, a, u)
        O.curseur(c, 1560 - 39 * 9, 680, 960, "", AMBRE, a, u)
        if u >= 1:
            O.ecart(c, 920, 1560 - 63 * 9, 1560 - 39 * 9, "", AMBRE, a)


# ------------------------------------------------------------------------------------------------ 10. les arbres meurent
def e10a(c, t, a=1.0):
    phrase(c, t, T["pourquoi"], ["Les arbres", "*meurent*"], t1=T["fois"] - 0.3)
    phrase(c, t, T["fois"] - 0.3, ["*2 fois* plus", "qu'il y a 15 ans"], t1=T["secheresse"])
    phrase(c, t, T["secheresse"], ["La *sécheresse*"])
    tm = T["meurent"]
    if t < tm:
        icone(c, "vx_chene", 540, 1500, 680, a)
    else:
        k = A.lisse((t - tm) / 0.7)
        c.saveLayerAlpha(None, int(255 * (1 - k) * a))
        icone(c, "vx_chene", 540, 1500, 680, 1.0, 1.0)
        c.restore()
        c.saveLayerAlpha(None, int(255 * k * a))
        icone(c, "vx_chene_mort", 540, 1500, 680, 1.0, 1.0)
        c.restore()
        if k < 1:                                              # les feuilles qui tombent
            tr = []
            for i in range(26):
                x0 = 300 + (i * 37) % 480
                y = 900 + (i * 53) % 300 + 600 * k * (0.6 + 0.4 * ((i * 7) % 5) / 5)
                tr.append([(x0 - 8 + 20 * k * math.sin(i), y), (x0 + 8 + 20 * k * math.sin(i), y + 6)])
            O.dessiner(c, tr, VERT, 2.4, (1 - k) * a)
    if t >= T["fois"]:
        O.dessiner(c, O.texte("x", 745, 780, 80, gras=True), AMBRE, 4, a)
        compteur(c, t, T["fois"], 1, 2.3, 920, 790, 110, 0.8, "{:.1f}", AMBRE, a)
    ts = T["secheresse"]
    if t >= ts:
        apparait(c, t, ts - 0.1, "vx_soleil", 200, 840, 230, a)
        apparait(c, t, ts + 0.2, "vx_sol_sec", 540, 1700, 190, a)


def e10b(c, t, a=1.0):
    phrase(c, t, T["insecte"], ["Un *insecte*", "finit le travail"], t1=T["scolyte"])
    phrase(c, t, T["scolyte"], ["Le *scolyte*"], t1=T["tue"])
    phrase(c, t, T["tue"], ["Il tue des épicéas", "de *30 mètres*"])
    if t < T["tue"] - 0.1:                                     # la loupe sur le scolyte
        apparait(c, t, T["insecte"], "vx_loupe", 700, 1440, 560, 0.6 * a)
        apparait(c, t, T["scolyte"] - 0.1, "vx_scolyte", 540, 1420, 470, a)
        if t >= T["cinq2"]:
            O.curseur(c, 950, 300, 780, "", AMBRE, a, (t - T["cinq2"]) / 0.3)
            O.curseur(c, 1430, 300, 780, "", AMBRE, a, (t - T["cinq2"]) / 0.3)
            O.ecart(c, 860, 950, 1430, "", AMBRE, a)
            O.dessiner(c, O.segments("5", 880, 1250, 90), AMBRE, 4, a)
            O.dessiner(c, O.texte("MM", 925, 1250, 50, centre=False, gras=True), AMBRE, 2.6, a)
        return
    tt = T["tue"] - 0.1                                        # l'épicéa de 30 m, et le scolyte minuscule à son pied
    nom = "vx_epicea" if t < T["metres"] + 0.3 else "vx_epicea_mort"
    if t < T["metres"] + 0.3:
        apparait(c, t, tt, "vx_epicea", 500, 1640, 1000, a)
    else:
        k = A.lisse((t - T["metres"] - 0.3) / 0.6)
        c.saveLayerAlpha(None, int(255 * (1 - k) * a))
        icone(c, "vx_epicea", 500, 1640, 1000, 1.0, 1.0)
        c.restore()
        c.saveLayerAlpha(None, int(255 * k * a))
        icone(c, nom, 500, 1640, 1000, 1.0, 1.0)
        c.restore()
    O.dessiner(c, [[(560, 1634), (566, 1630)]], AMBRE, 5, a)                    # le scolyte, à l'échelle : un point
    if t >= T["trente2"]:
        u = (t - T["trente2"]) / 0.4
        O.curseur(c, 640, 680, 940, "", VERT_PALE, a, u)
        O.curseur(c, 1640, 680, 940, "", VERT_PALE, a, u)
        if u >= 1:
            O.ecart(c, 880, 640, 1640, "30 M", AMBRE, a)


# ------------------------------------------------------------------------------------------------ 11. le paradoxe
def e11(c, t, a=1.0):
    tp = T["pourtant"]
    phrase(c, t, tp, ["Et *pourtant*"], t1=T["dixsept2"])
    phrase(c, t, T["dixsept2"], ["Le carbone stocké :", "*+ 17 %*"], t1=T["respire"])
    phrase(c, t, T["respire"], ["Elle *respire*", "de plus en plus mal"], t1=T["alors2"])
    phrase(c, t, T["alors2"], ["Peur de la", "*bonne chose* ?"], t1=T["probleme"])
    phrase(c, t, T["probleme"], ["Elle ne disparaît pas", "Elle *s'épuise*"])
    if t < T["alors2"]:
        g = 1 + 0.17 * A.lisse((t - T["carbone"]) / 2.0)        # la forêt grossit…
        icone(c, "vx_chene_centenaire", 360, 1560, 520 * g, a, 1.0 if t > tp + 0.3 else (t - tp + 0.25) / 0.9)
        if t >= T["dixsept2"]:
            O.dessiner(c, O.texte("+", 640, 900, 90, gras=True), AMBRE, 3.4, a)
            compteur(c, t, T["dixsept2"], 0, 17, 780, 900, 110, 1.0, "{:.0f}", AMBRE, a)
            O.dessiner(c, O.texte("%", 900, 900, 90, gras=True), AMBRE, 3.4, a)
        if t >= T["respire"] - 0.2:                            # … mais respire mal : les poumons qui faiblissent
            amp = 0.12 * (1 - 0.8 * A.lisse((t - T["respire"]) / 2.0))
            k = 1 + amp * math.sin(2 * math.pi * 0.8 * (t - T["respire"]))
            c.save()
            c.translate(800, 1350)
            c.scale(k, k)
            c.translate(-800, -1350)
            apparait(c, t, T["respire"] - 0.2, "vx_poumons", 800, 1520, 330, a)
            c.restore()
        return
    O.dessiner(c, O.texte("DISPARAÎT", W / 2, 1000, 90, gras=True), VERT, 3.4, a, (t - T["probleme"]) / 0.4)
    if t >= T["disparait"] + 0.3:
        O.dessiner(c, [[(250, 970), (830, 970)]], AMBRE, 7, a, (t - T["disparait"] - 0.3) / 0.25)
    if t >= T["epuise"] - 0.2:
        O.dessiner(c, O.texte("S'ÉPUISE", W / 2, 1300, 120, gras=True), AMBRE, 5, a, (t - T["epuise"] + 0.2) / 0.4)
    if T["alors2"] <= t < T["probleme"]:
        icone(c, "vx_balance", 540, 1500, 520, a)


# ------------------------------------------------------------------------------------------------ 12. planter, la suite
def e12(c, t, a=1.0):
    tj = T["justement"]
    phrase(c, t, T["sais"], ["« Il suffit de", "*planter* »"], t1=tj)
    phrase(c, t, tj, ["*Justement.*"], t1=T["cent"])
    phrase(c, t, T["cent"], ["*100 ans*", "en 2125"], t1=T["climat"])
    phrase(c, t, T["climat"], ["Un climat qui", "*n'existe pas encore*"], t1=T["forestiers"])
    phrase(c, t, T["forestiers"], ["Les forestiers", "ont une *idée*…"])
    if t < tj:
        apparait(c, t, T["sais"], "vx_main_pousse", 540, 1500, 600, a)
        return
    if t < T["forestiers"]:                                    # la frise : la pousse devient un chêne centenaire
        O.dessiner(c, [[(120, 1600), (960, 1600)]], VERT_PALE, 3, a, (t - tj) / 0.5)
        O.dessiner(c, O.texte("2025", 170, 1680, 44, gras=True), VERT, 2.4, a)
        O.dessiner(c, O.texte("2125", 720, 1680, 44, gras=True), AMBRE, 2.4, a, (t - tj - 0.3) / 0.4)
        u = A.lisse((t - T["cent"]) / 2.0)
        x = 190 + 520 * u
        if t >= T["cent"]:
            O.dessiner(c, [[(190, 1600), (x, 1600)]], AMBRE, 5, a)
        nom = "vx_pousse" if u < 0.35 else ("vx_chene" if u < 0.75 else "vx_chene_centenaire")
        icone(c, nom, x, 1590, 130 + 400 * u, a, 1.0)
        tc = T["climat"]
        if t >= tc:                                            # le thermomètre qui monte en même temps
            icone(c, "px_thermometre", 170, 1450, 420, a, (t - tc) / 0.4)
            y = 1350 - 260 * A.lisse((t - tc - 0.4) / 2.0)          # le climat qui monte : une flèche
            O.dessiner(c, [[(290, y + 40), (290, y - 40)], [(270, y - 20), (290, y - 40), (310, y - 20)]], AMBRE, 4, a)
        return
    apparait(c, t, T["forestiers"] - 0.1, "vx_forestier", 540, 1500, 560, a)
    if t >= T["idee"]:
        if int((t - T["idee"]) * 3) % 2 == 0 or t > T["idee"] + 1.2:
            O.dessiner(c, O.texte("?", 860, 900, 200, gras=True), AMBRE, 5, a)


def fin(c, t, a=1.0):
    O.dessiner(c, [rect(80, 640, 1000, 1300)], AMBRE, 3, a)
    O.dessiner(c, O.texte("L'IDÉE DES FORESTIERS", W / 2, 860, 50, gras=True), VERT_PALE, 3, a)
    dx = 6 * abs(math.sin(t * 5))
    O.dessiner(c, O.texte("LA SUITE DEMAIN", W / 2 - 30 + dx, 1080, 64, gras=True), AMBRE, 3.6, a)
    xt = W / 2 + O.largeur_texte("LA SUITE DEMAIN", 64) / 2 - 10 + dx
    O.dessiner(c, [[(xt, 1024), (xt + 44, 1052), (xt, 1080), (xt, 1024)]], AMBRE, 4, a)
    O.dessiner(c, O.texte("SOURCES : IGN, INVENTAIRE FORESTIER", W / 2, 1240, 24), VERT, 1.4, 0.8 * a)


# ------------------------------------------------------------------------------------------------ montage
def ecrans():
    return [(0.0, e1), (T["quand"] - 0.1, e2), (T["sauf"] - 0.1, e3), (T["comment"] - 0.1, e4), (T["landes2"] - 0.1, e5),
            (T["cette"] - 0.1, e6), (T["alors"] - 0.1, e7a), (T["incendie"] - 0.1, e7b), (T["attendez"] - 0.2, e8),
            (T["foret3"] - 0.1, e9), (T["pourquoi"] - 0.1, e10a), (T["insecte"] - 0.1, e10b), (T["pourtant"] - 0.1, e11),
            (T["sais"] - 0.1, e12), (T["fin"], fin)]


def heros(i):
    """Le dessin qui se transforme d'un écran au suivant (enchaînement i : écran i-1 → écran i), ou None."""
    sil = O.silhouette
    return {2: (lambda: sil("vx_chene", 760, 1500, 400), lambda: _FR),
            3: (lambda: _FR, lambda: sil("vx_ferme", 230, 1460, 230)),
            4: (lambda: sil("vx_chene", 600, 1640, 380), lambda: sil("vx_mouton", 300, 1420, 180)),
            6: (lambda: sil("vx_voiture_vacances", 540, 1600, 230), lambda: sil("vx_cerveau", 540, 1420, 560)),
            7: (lambda: sil("vx_balance", 540, 1560, 430), lambda: sil("vx_tele", 540, 1540, 760)),
            11: (lambda: sil("vx_chene_mort", 540, 1500, 680), lambda: sil("vx_loupe", 700, 1440, 560)),
            12: (lambda: sil("vx_epicea_mort", 500, 1640, 1000), lambda: sil("vx_chene_centenaire", 360, 1560, 520)),
            13: (lambda: [rect(250, 900, 830, 1320)], lambda: sil("vx_main_pousse", 540, 1500, 600))}.get(i)


_HEROS = {}


def appeler(fn, c, t, t0):
    global _T, _T0
    _T, _T0 = t, t0
    fn(c, t)


def coups():
    return [T["autriche"], T["double"], T["planter"], T["jamais"], T["attendez"] - 0.2, T["trente"], T["fois"],
            T["metres"], T["dixsept2"], T["epuise"]]


def image(c, t):
    O.ecran(c, t)
    ec = ecrans()
    k = max(i for i, x in enumerate(ec) if x[0] <= t)
    for i in range(1, len(ec) - 1):                            # enchaînement (vers le carton de fin : coupe)
        b = ec[i][0]
        if b - 0.25 <= t < b + 0.25 and ec[i][1] is not e8 and ec[i - 1][1] is not e8:
            u = (t - b + 0.25) / 0.5
            c.saveLayerAlpha(None, int(255 * (1 - A.lisse(u / 0.6))))
            appeler(ec[i - 1][1], c, t, ec[i - 1][0])
            c.restore()
            c.saveLayerAlpha(None, int(255 * A.lisse((u - 0.4) / 0.6)))
            appeler(ec[i][1], c, t, ec[i][0])
            c.restore()
            h = heros(i)
            if h:
                if i not in _HEROS:
                    _HEROS[i] = (h[0](), h[1]())
                ha, hb = _HEROS[i]
                for tr, it in A.flux(("ep30", i), ha, hb, u):
                    O.dessiner(c, tr, AMBRE, 3.2, it)
            break
    else:
        z = 1.0                                                # petits coups de caméra sur les mots forts
        for tw in coups():
            if t >= tw:
                z += 0.05 * math.exp(-6 * (t - tw))
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        appeler(ec[k][1], c, t, ec[k][0])
        c.restore()
    if ec[k][1] in (e8,) and t < ec[k][0] + 0.12:              # « MAIS ATTENDEZ » : flash de neige
        rng = np.random.default_rng(int(t * 1000))
        pts = rng.uniform(0, 1, (900, 2)) * (W, H)
        O.dessiner(c, [[(x, y), (x + 3, y)] for x, y in pts], VERT_PALE, 2, 0.8)
    if ec[k][1] is not fin and VOIX is not None:               # la voix du narrateur, sous la phrase
        O.oscillogramme(c, VOIX, MI.SR, t, y=470, x0=220, x1=860, ampli=30)


# ------------------------------------------------------------------------------------------------ son
def sons():
    debuts = [x[0] for x in ecrans()[1:-1]]
    ev = [(b - 0.25, Z.whoosh(0.5, 0.07)) for b in debuts if abs(b - (T["attendez"] - 0.2)) > 0.01]
    ev += [(T["attendez"] - 0.2, Z.neige(0.22, 0.25)), (T["attendez"] - 0.2, Z.boom(0.55, 60))]
    ev += [(t, Z.thump(0.35)) for t in [T["double"], T["jamais"], T["trente"], T["fois"], T["metres"], T["epuise"]]]
    ev += [(t, Z.boom(0.45, 70)) for t in [T["autriche"], T["planter"], T["dixsept2"]]]
    ev += [(T["normal"], Z.snap(0.3)), (T["double"], Z.snap(0.3)), (T["plantee"] + 0.3, Z.snap(0.3)),
           (T["incendies"], Z.crepitement(1.2, 0.08)), (T["coupes"], Z.vibration(0.8, 0.08)),
           (T["co"], Z.souffle(0.8, 0.12, True)), (T["respire"], Z.souffle(1.2, 0.1, True)),
           (T["respire"] + 1.3, Z.souffle(1.2, 0.07, False)), (T["fin"], Z.boom(0.6, 50)), (T["fin"], Z.riser(0.8, 0.07))]
    ev += [(0.4 + 1.6 * i / 22, Z.pince(523.3 * 2 ** ((i % 12) / 12), 0.04, 0.25)) for i in range(22)]   # arbres en rafale
    ev += [(T["planter"] + 0.07 * i, Z.pince(440 * 2 ** (i / 12), 0.045, 0.25)) for i in range(15)]
    ev += [(T["aujourdhui"] + 0.06 * i, Z.pince(587.3 * 2 ** (i / 12), 0.04, 0.2)) for i in range(16)]
    for mot in ["coupes", "incendies", "disparaissent", "paysans", "champs", "redevenus", "bergers", "dixhuit2",
                "cerveau", "degrade", "ameliore", "incendie", "arbre2", "eponge", "cinq", "secheresse", "scolyte",
                "cinq2", "pourtant", "cent", "climat", "forestiers"]:
        ev.append((T[mot], Z.pince(784, 0.07)))
    return ev


def coupures():
    """La nappe se coupe juste avant les révélations."""
    return [T["sauf"], T["attendez"] - 0.2, T["trente"], T["pourtant"], T["fin"]]


def mixage(chemin, voix, dur):
    n = int(dur * MI.SR)
    v = np.zeros(n)
    v[:min(n, len(voix))] = voix[:n]
    v *= 10 ** (-16 / 20) / (np.sqrt((v[np.abs(v) > 0.01] ** 2).mean()) + 1e-9)
    nappe = MI.bed(dur + 1)[:n]
    nappe = nappe.mean(1) if nappe.ndim == 2 else nappe
    nappe = nappe / (np.abs(nappe).max() + 1e-9) * 10 ** (-24 / 20)
    tt = np.arange(n) / MI.SR
    for tc in coupures():
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


# ------------------------------------------------------------------------------------------------ préparation
REPERES = [  # (nom, début du mot (sans accent, sans espace), repère après lequel le chercher)
    ("autriche", "lautriche", None), ("personne", "personne", None), ("quand", "quand", None),
    ("coupes", "coupes", None), ("incendies", "incendies", None), ("disparaissent", "disparaissent", None),
    ("normal", "normal", None), ("sauf", "sauf", None), ("neuf", "neuf", "sauf"), ("aujourdhui", "aujourdhui", "sauf"),
    ("dixsept", "dixsept", "aujourdhui"), ("tiers", "tiers", None), ("double", "double", None),
    ("landes1", "landes", "double"), ("comment", "comment", None), ("paysans", "paysans", None),
    ("champs", "champs", None), ("redevenus", "redevenus", None), ("seuls", "seuls", None),
    ("landes2", "landes", "seuls"), ("bergers", "bergers", None), ("dixhuit2", "dixhuit", "bergers"),
    ("planter", "planter", "dixhuit2"), ("resultat", "resultat", None), ("cette", "cette", None),
    ("plantee", "plantee", None), ("alors", "alors", "plantee"), ("truc", "truc", None), ("cerveau", "cerveau", None),
    ("degrade", "degrade", None), ("ameliore", "sameliore", None), ("incendie", "incendie", "ameliore"),
    ("arbre2", "arbre", "incendie"), ("jamais", "jamais", None), ("attendez", "attendez", None),
    ("inquietant", "inquietant", None), ("foret3", "foret", "inquietant"), ("eponge", "eponge", None),
    ("co", "co", "eponge"), ("entre", "entre", None), ("cinq", "cinq", "entre"), ("avis", "avis", None),
    ("trente", "trente", "avis"), ("quarante", "quarante", None), ("pourquoi", "pourquoi", "quarante"),
    ("meurent", "meurent", None), ("fois", "fois", "meurent"), ("secheresse", "secheresse", None),
    ("insecte", "insecte", None), ("scolyte", "scolyte", None), ("cinq2", "cinq", "scolyte"), ("tue", "tue", "scolyte"),
    ("trente2", "trente", "tue"), ("metres", "metres", "trente2"), ("pourtant", "pourtant", None),
    ("carbone", "carbone", None), ("dixsept2", "dixsept", "carbone"), ("respire", "respire", None),
    ("alors2", "alors", "respire"), ("probleme", "probleme", None), ("disparait", "disparait", "probleme"),
    ("epuise", "sepuise", None), ("sais", "sais", None), ("justement", "justement", None), ("cent", "cent", "justement"),
    ("climat", "climat", None), ("forestiers", "forestiers", None), ("idee", "idee", "forestiers")]


def preparer():
    global VOIX
    chemin = os.path.join(ICI, "audio", "voix.mp3")
    MV.charger(types.SimpleNamespace(SEGS=os.path.join(ICI, "audio", "voix.json"), VOIX=chemin))
    VOIX, _, _ = MI.tighten(MI.load_voice(chemin), max_gap=0.40, thr_db=-38.0)
    for nom, cle, apres in REPERES:
        T[nom] = MV.mot(cle, T[apres] + 0.01 if apres else 0.0)
    T["que"] = MV.mot("voir", T["idee"], fin=True)
    T["fin"] = T["que"] + 0.35                                 # coupé net après « que… »
    return VOIX


def rendre(sortie, t0=0.0, t1=None):
    voix = preparer()
    dur = T["fin"] + 2.6
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
        if prec is not None and not O.PAPIER:                  # traînée très brève du phosphore
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=0.35, BlendMode=skia.BlendMode.kLighten))
        prec = surf.makeImageSnapshot()
        ff.stdin.write(O.finition(prec.toarray(), t, FPS).tobytes())
        if f % 300 == 0:
            print(f"{t:5.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()
    voix_coupee = voix[:int(T["fin"] * MI.SR)]                 # la voix s'arrête net sur « que… »
    mixage(f"{tmp}/a.wav", voix_coupee, dur)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}",
                    "-i", f"{tmp}/a.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", sortie], check=True)
    print("OK", sortie)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep30.mp4"
    if len(sys.argv) > 3:
        rendre(out, float(sys.argv[2]), float(sys.argv[3]))
    else:
        rendre(out)
