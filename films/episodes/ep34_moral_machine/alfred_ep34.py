"""Épisode 34 — « Votre voiture doit choisir qui meurt » (Moral Machine) — style @alfred.explique, en bleu, 100 % code.

    python -m films.episodes.ep34_moral_machine.alfred_ep34 output/ep34.mp4 [t0 t1]
"""
import math
import os
import subprocess
import sys
import tempfile
import types

import numpy as np
from PIL import Image, ImageDraw

from films import montage_ia as MI
from films.outils import mots_voix as MV
from films.styles import mixage_pro as MP
from films.styles import oscillo_son as Z
from films.styles import pixel_bleu as P
from films.styles import son_jeu as J
from films.episodes.ep34_moral_machine import decor34 as D
from films.styles.pixel_bleu import B0, B1, B2, B3, B4, BLANC, GRIS, GRIS_F, NOIR, ROUGE, ROUGE_F

ICI = os.path.dirname(os.path.abspath(__file__))
FPS = 30
T = {}
VOIX = None
PASSAGE = 236                                                    # le passage piéton (vue de dessus, toile 270 × 480)

P.TENUES.setdefault("vieux", {"haut": ((120, 128, 146), (78, 86, 104), (170, 178, 196)), "bas": (B0, (10, 30, 70), B1),
                              "cheveux": (226, 232, 244)})
P.TENUES.setdefault("robe", {"haut": (B3, B2, B4), "bas": (B3, B2, B4), "cheveux": (70, 52, 30)})
P.TENUES.setdefault("sport", {"haut": (ROUGE, ROUGE_F, (255, 140, 130)), "bas": (B0, (10, 30, 70), B1),
                              "cheveux": (12, 22, 48)})


def lisse(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def draw(img):
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    return d


def apres(cle, dt=0.0):
    return T.get(cle, 1e9) + dt


# ------------------------------------------------------------------------------------------------ les personnages
def enceinte(img, x, y, taille=40, miroir=False, marche=None, panique=False):
    s = taille / 92
    P.personnage(img, (x, y), taille, tenue="robe", miroir=miroir, marche=marche,
                 mains=(x + 10 * s, y - 98 * s) if panique else (x + 8 * s, y - 52 * s))
    d = draw(img)
    sx = -1 if miroir else 1
    cx, cy, r = x + sx * 7 * s, y - 52 * s, 7 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=B3, outline=P.CONTOUR)
    d.point((cx + sx * 2, cy - 2), fill=B4)


def vieux(img, x, y, taille=40, miroir=False, panique=False):
    s = taille / 92
    sx = -1 if miroir else 1
    P.personnage(img, (x, y), taille, tronc=14 if not panique else 2, flexion=0.3, tenue="vieux", miroir=miroir,
                 mains=(x + 8 * s, y - 96 * s) if panique else (x + 24 * s, y - 40 * s))
    if panique:
        return
    d = draw(img)
    cx = x + sx * 26 * s
    d.line([(cx, y), (cx, y - 40 * s)], fill=GRIS, width=max(1, int(2 * s)))     # la canne
    d.line([(cx, y - 40 * s), (cx - sx * 4 * s, y - 42 * s)], fill=GRIS, width=max(1, int(2 * s)))


def enfant(img, x, y, taille=30, tenue="clair", miroir=False):
    P.personnage(img, (x, y), taille, tenue=tenue, miroir=miroir)


def criminel(img, x, y, taille=40, miroir=False):
    s = taille / 92
    P.personnage(img, (x, y), taille, tenue="costume", miroir=miroir)
    d = draw(img)
    hy = y - 81 * s
    d.rectangle((x - 8 * s, hy - 2 * s, x + 8 * s, hy + 1 * s), fill=NOIR)          # le masque
    for yy in range(int(y - 68 * s), int(y - 44 * s), 3):                            # les rayures
        d.line([(x - 6 * s, yy), (x + 6 * s, yy)], fill=GRIS)


def sportif(img, x, y, taille=40, miroir=False, t=0.0):
    P.personnage(img, (x, y), taille, tenue="sport", miroir=miroir, marche=t * 9)


def surpoids(img, x, y, taille=40, miroir=False):
    s = taille / 92
    P.personnage(img, (x, y), taille, tenue="gris", miroir=miroir)
    d = draw(img)
    sx = -1 if miroir else 1
    cx, cy, r = x + sx * 5 * s, y - 50 * s, 10 * s
    d.ellipse((cx - r, cy - r * 0.9, cx + r, cy + r * 0.9), fill=GRIS, outline=P.CONTOUR)


def poussette(d, x, y, t=0.0):
    """Une poussette de profil, avec le bébé."""
    d.chord((x - 12, y - 24, x + 10, y - 4), 180, 360, fill=B2, outline=P.CONTOUR)
    d.rectangle((x - 12, y - 14, x + 10, y - 9), fill=B1)
    d.pieslice((x - 12, y - 26, x + 4, y - 10), 180, 270, fill=B3, outline=P.CONTOUR)    # la capote
    d.ellipse((x - 1, y - 20, x + 5, y - 14), fill=P.PEAU)                                 # le bébé
    d.line([(x + 10, y - 14), (x + 16, y - 24)], fill=GRIS, width=2)                      # la poignée
    for cx in (x - 8, x + 6):
        d.ellipse((cx - 3, y - 6, cx + 3, y), outline=GRIS, fill=NOIR)


def chat(d, x, y, t=0.0, col=GRIS):
    d.ellipse((x - 7, y - 8, x + 5, y - 1), fill=col, outline=P.CONTOUR)
    d.ellipse((x + 2, y - 13, x + 9, y - 6), fill=col, outline=P.CONTOUR)
    d.polygon([(x + 3, y - 12), (x + 4, y - 16), (x + 6, y - 12)], fill=col)
    d.polygon([(x + 6, y - 12), (x + 8, y - 16), (x + 9, y - 11)], fill=col)
    d.point((x + 7, y - 10), fill=NOIR)
    q = math.sin(t * 4) * 3
    d.line([(x - 7, y - 5), (x - 11, y - 10 + q), (x - 10, y - 14 + q)], fill=col, width=2)
    for k in (-5, -2, 1, 3):
        d.line([(x + k, y - 2), (x + k, y)], fill=col)


def chien(d, x, y, t=0.0, col=(176, 150, 120)):
    d.rounded_rectangle((x - 10, y - 12, x + 6, y - 4), 3, fill=col, outline=P.CONTOUR)
    d.ellipse((x + 3, y - 18, x + 13, y - 8), fill=col, outline=P.CONTOUR)
    d.rectangle((x + 10, y - 13, x + 15, y - 10), fill=col)
    d.ellipse((x + 3, y - 17, x + 7, y - 9), fill=(120, 96, 70))                          # l'oreille
    d.point((x + 10, y - 15), fill=NOIR)
    d.point((x + 15, y - 12), fill=NOIR)
    q = math.sin(t * 12) * 2
    d.line([(x - 10, y - 11), (x - 14, y - 15 + q)], fill=col, width=2)
    for k in (-8, -4, 1, 4):
        d.line([(x + k, y - 4), (x + k, y)], fill=col, width=2)


# ------------------------------------------------------------------------------------------------ interface
def date(d, txt, t, t0, x=262):
    if t < t0:
        return
    f = P.police(26, pixel=False)
    w = d.textlength(txt, font=f)
    k = int((t - t0) * 30)
    vis = txt[:max(1, min(len(txt), k // 2 + 1))]
    d.text((x - w, 86), vis, font=f, fill=BLANC)


def compteur(d, x, y, v, suffixe="", taille=16, col=BLANC):
    f = P.police(taille, pixel=False)
    txt = f"{v:,.0f}".replace(",", " ") + suffixe
    w = d.textlength(txt, font=f)
    d.rectangle((x - w / 2 - 4, y - 2, x + w / 2 + 4, y + taille + 4), fill=NOIR)
    d.text((x - w / 2, y), txt, font=f, fill=col)


def titre(d, x, y, txt, taille=14, col=BLANC, centre=True):
    f = P.police(taille, pixel=False)
    w = d.textlength(txt, font=f)
    d.text((x - w / 2 if centre else x, y), txt, font=f, fill=col)


def tampon(img, txt, t, t0, cx, cy, ang=-8, taille=14, col=ROUGE):
    if t < t0:
        return
    k = 1 + 1.2 * max(0.0, 1 - (t - t0) / 0.12)
    f = P.police(taille, pixel=False)
    tmp = Image.new("RGBA", (260, 60), (0, 0, 0, 0))
    dd = ImageDraw.Draw(tmp)
    dd.fontmode = "1"
    w = dd.textlength(txt, font=f)
    dd.rectangle((130 - w / 2 - 6, 30 - taille / 2 - 5, 130 + w / 2 + 6, 30 + taille / 2 + 6), outline=col, width=2,
                 fill=NOIR)
    dd.text((130 - w / 2, 30 - taille / 2 - 1), txt, font=f, fill=col)
    tmp = tmp.rotate(ang, resample=Image.NEAREST).resize((int(260 * k), int(60 * k)), Image.NEAREST)
    img.paste(tmp, (int(cx - 130 * k), int(cy - 30 * k)), tmp)


def bulle(d, x, y, txt, col=BLANC, bord=B2, queue=None):
    P.cadre_texte(d, (x, y), txt, 8, col, bord)
    if queue:
        d.polygon([(queue[0] - 3, y + 11), (queue[0] + 3, y + 11), queue], fill=bord)


OVER = []


def over(fn, *args):
    OVER.append((fn, args))


# ------------------------------------------------------------------------------------------------ véhicules, effets
def voiture_profil(d, x, y, col=B2, t=0.0, roule=True, phare=True):
    """Une voiture de profil, sans marque (avant vers la droite) : carrosserie ombrée, vitres, reflets, jantes."""
    sombre = tuple(int(c * 0.65) for c in col)
    clair = tuple(min(255, int(c * 1.3) + 20) for c in col)
    d.ellipse((x + 2, y - 3, x + 78, y + 3), fill=(3, 6, 14))                                    # ombre
    d.rounded_rectangle((x, y - 22, x + 78, y - 6), 5, fill=col, outline=P.CONTOUR)
    d.polygon([(x + 16, y - 22), (x + 26, y - 36), (x + 54, y - 36), (x + 66, y - 22)], fill=col, outline=P.CONTOUR)
    d.rectangle((x + 2, y - 11, x + 76, y - 7), fill=sombre)                                     # bas de caisse
    d.line([(x + 4, y - 20), (x + 74, y - 20)], fill=clair)                                       # ligne de lumière
    d.polygon([(x + 20, y - 23), (x + 28, y - 33), (x + 39, y - 33), (x + 39, y - 23)], fill=B0)
    d.polygon([(x + 42, y - 23), (x + 42, y - 33), (x + 53, y - 33), (x + 62, y - 23)], fill=B0)
    d.line([(x + 30, y - 31), (x + 26, y - 25)], fill=B2)                                         # reflets des vitres
    d.line([(x + 46, y - 31), (x + 44, y - 26)], fill=B2)
    d.line([(x + 40, y - 21), (x + 40, y - 9)], fill=sombre)                                      # la portière
    d.rectangle((x + 44, y - 18, x + 48, y - 17), fill=clair)
    d.polygon([(x + 62, y - 24), (x + 66, y - 26), (x + 66, y - 22)], fill=sombre)                # rétroviseur
    d.rectangle((x + 72, y - 18, x + 77, y - 14), fill=BLANC)
    d.rectangle((x + 1, y - 18, x + 4, y - 14), fill=ROUGE)
    for cx in (x + 17, x + 61):
        d.ellipse((cx - 9, y - 15, cx + 9, y + 3), fill=NOIR, outline=GRIS_F)
        d.ellipse((cx - 4, y - 10, cx + 4, y - 2), fill=GRIS_F, outline=GRIS)
        a = t * 12 if roule else 0
        for k in range(3):
            b = a + k * 2.1
            d.line([(cx, y - 6), (cx + 4 * math.cos(b), y - 6 + 4 * math.sin(b))], fill=GRIS)


def grand_profil(img, x, y, k=2, **kw):
    tmp = Image.new("RGBA", (84, 44), (0, 0, 0, 0))
    voiture_profil(draw(tmp), 2, 40, **kw)
    tmp = tmp.resize((84 * k, 44 * k), Image.NEAREST)
    img.paste(tmp, (int(x - 2 * k), int(y - 40 * k)), tmp)


def pluie(d, t, x0=0, x1=270, y0=0, y1=480, n=70):
    rng = np.random.default_rng(12)
    for _ in range(n):
        x, y, v = rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(0.7, 1.3)
        yy = y0 + (y - y0 + t * 420 * v) % (y1 - y0)
        xx = x + (yy - y0) * 0.12
        d.line([(xx, yy), (xx + 1, yy + 6)], fill=(60, 90, 150))


def gens(img, d, t, s, panique=False, taille=56):
    """La femme enceinte (voie de gauche) et les trois personnes âgées (voie de droite), sur le passage."""
    if s >= T["devant"] - 0.2:
        D.ombre(d, 80, PASSAGE + 6, 10)
        enceinte(img, 80, PASSAGE + 6, taille, panique=panique)
    for k, x in enumerate((164, 188, 212)):
        if s >= T["trois"] - 0.1 + 0.15 * k:
            D.ombre(draw(img), x, PASSAGE + 6, 9)
            vieux(img, x, PASSAGE + 6, taille - 4, miroir=True, panique=panique and k != 1)


GRAND = {}


def grand(img, fn, x, y, k=2, *args):
    """Dessine un petit sujet (animal, poussette) agrandi k fois, pieds en (x, y)."""
    tmp = Image.new("RGBA", (60, 40), (0, 0, 0, 0))
    fn(draw(tmp), 30, 36, *args)
    tmp = tmp.resize((60 * k, 40 * k), Image.NEAREST)
    img.paste(tmp, (int(x - 30 * k), int(y - 36 * k)), tmp)


def projecteurs(img, xs, y0, sol, col=(24, 46, 96), force=0.85, t=0.0):
    for k, x in enumerate(xs):
        bal = 10 * math.sin(t * 0.9 + k)
        D.cone(img, (x, y0), (x + bal, sol), 3, 34, col, force)
    return draw(img)


# ------------------------------------------------------------------------------------------------ les scènes
def s_route(img, d, t, s):
    """L'accroche (s = temps de l'histoire) : la voiture sans freins fonce vers le passage ; qui choisir ?"""
    d = D.route_nuit(img, s, PASSAGE)
    arrivee = T["rw0"]
    u = lisse((s - (T["choisir"] - 0.2)) / (arrivee - T["choisir"] + 0.2))
    cy = 400 - 20 * lisse(s / 1.2) - (380 - PASSAGE - 62) * u
    if s >= T["freins"]:                                          # les traces de freinage qui ne servent à rien
        D.traces(d, 135, cy + 34, 480)
    panique = s >= T["choisir"]
    gens(img, d, t, s, panique)
    d = draw(img)
    hes = lisse((s - T["choisir"]) / 0.6) if s > T["choisir"] else 0.0
    ang = 9 * math.sin(s * 3.1) * hes
    cx = 135 + 30 * math.sin(s * 3.1) * hes
    D.voiture_dessus(img, cx, cy, ang, alerte=s >= T["freins"], t=s,
                     toit=not (T["personne"] - 0.1 <= s < T["choisir"]), freinage=1.0 if s >= T["freins"] else 0.0)
    d = draw(img)
    if s >= T["freins"]:
        for k in range(6):                                        # étincelles sous la voiture
            if (int(s * 20) + k) % 3 == 0:
                d.point((cx - 18 + (k * 7) % 36, cy + 36 + (k * 5) % 6), fill=B4 if k % 2 else ROUGE)
    pluie(d, s)
    if s >= T["enceinte"]:
        over(bulle, *E(52, PASSAGE + 22), "ENCEINTE", BLANC, B2)
    if s >= T["agees"]:
        over(bulle, *E(166, PASSAGE + 22), "3 AGEES", BLANC, B2)
    if s >= T["freins"]:
        clign = int(s * 6) % 2
        over(P.cadre_texte, (92, 440), "FREINS : HS", 8, BLANC if clign else ROUGE, ROUGE, ROUGE_F if clign else NOIR)
    if T["personne"] - 0.1 <= s < T["choisir"]:
        over(P.cadre_texte, (70, 140), "CONDUCTEUR : AUCUN", 8, B4, B2)
    if panique:
        for x in (80, 164, 212):
            if int(s * 6 + x) % 2:
                over(lambda dd, p=E(x - 2, PASSAGE - 50): dd.text(p, "!", font=P.police(14, pixel=False), fill=ROUGE))
    if s >= T["alors"]:
        f = P.police(36, pixel=False)
        if int(s * 4) % 2 or s > T["alors"] + 0.6:
            over(lambda dd: dd.text((122, 300), "?", font=f, fill=ROUGE))


def s_mit(img, d, t):
    """« Cette question… » → « Résultat » : le bureau du chercheur, l'écran du jeu du MIT, 2016, Toulouse."""
    d = D.labo(img, t)
    ex, ey, ew, eh = 108, 222, 140, 96                            # le grand écran posé sur le bureau
    d.rectangle((ex - 5, ey - 5, ex + ew + 5, ey + eh + 5), fill=(30, 36, 56), outline=P.CONTOUR)
    d.rectangle((ex + ew / 2 - 6, ey + eh + 5, ex + ew / 2 + 6, 330), fill=(30, 36, 56))
    choix = int((t - T["lance"]) * 1.5) % 2 if t >= T["lance"] else None
    D.ecran_jeu(d, ex, ey, ew, eh, t, choix)
    D.lumiere(img, ex + ew / 2, ey + eh / 2, 110, 90, (26, 48, 96), 0.5)
    d = draw(img)
    D.ecran_jeu(d, ex, ey, ew, eh, t, choix)
    d.rectangle((150, 322, 200, 328), fill=GRIS_F, outline=P.CONTOUR)                           # le clavier
    for k in range(8):
        if int(t * 9 + k) % 3 == 0:
            d.point((153 + k * 6, 324), fill=B4)
    # le chercheur, assis, de profil, qui tape
    P.siege(d, 94, 420, 1.7)
    x = 76
    tape = math.sin(t * 14) * 2
    if t >= T["parmi"]:
        P.personnage(img, (x + 34, 420), 104, assis=True, tenue="costume", mains=(150 + tape, 318))
        D.lumiere(img, 120, 300, 30, 40, (40, 60, 110), 0.4)
    if t >= T["moral"]:
        over(P.cadre_texte, (120, 206), "MORAL MACHINE", 8, BLANC, ROUGE)
    if t >= T["toulouse"]:
        over(P.cadre_texte, (22, 444), "TOULOUSE", 8, BLANC, ROUGE)
    if t >= T["bonnefon"]:
        over(P.cadre_texte, (100, 444), "J.-F. BONNEFON", 8, B4, B2)
    if t >= T["mit"]:
        over(lambda dd: (dd.rectangle((14, 112, 70, 140), fill=ROUGE_F, outline=ROUGE),
                         dd.text((22, 114), "MIT", font=P.police(20, pixel=False), fill=BLANC)))


def s_planete(img, d, t):
    """« Résultat : 40 millions de décisions, 233 pays » : le globe tourne et s'allume de points."""
    d.rectangle((0, 0, 270, 480), fill=(4, 8, 20))
    D.etoiles(d, t, 90)
    D.lumiere(img, 135, 270, 140, 140, (12, 26, 60), 0.7)
    u = lisse((t - T["resultat"]) / 2.5)
    D.globe(img, 135, 270, 100, t * 0.35, (B2, B2, B2), points=200 * u, t=t)
    d = draw(img)
    for k in range(3):                                            # des satellites en orbite
        a = t * (0.8 + 0.3 * k) + k * 2
        x, y = 135 + 124 * math.cos(a), 270 + 40 * math.sin(a) - 20 * k
        if math.sin(a) > -0.2 or True:
            d.rectangle((x - 1, y - 1, x + 1, y + 1), fill=B4)
            d.line([(x - 4, y), (x + 4, y)], fill=B2)
    if t >= T["quarante"]:
        v = 40_000_000 * lisse((t - T["quarante"]) / 1.4)
        over(compteur, 135, 118, v, "", 20, BLANC)
        over(P.cadre_texte, (98, 146), "DECISIONS", 8, B4, B2)
    if t >= T["deux"]:
        v = 233 * lisse((t - T["deux"]) / 1.0)
        over(compteur, 135, 396, v, " PAYS", 16, B4)


def _contenu(*items):
    """Fabrique le contenu d'un plateau de balance : items = (fonction(img, x, y), décalage x)."""
    def f(img, x, y):
        for fn, dx in items:
            fn(img, x + dx, y)
    return f


def _p(tenue, taille=40, miroir=False):
    return lambda img, x, y: P.personnage(img, (x, y), taille, tenue=tenue, miroir=miroir)


def _salle(img, d, t):
    """Une salle sombre, un projecteur sur la balance."""
    d.rectangle((0, 0, 270, 480), fill=(6, 12, 28))
    for x in range(0, 270, 30):                                   # des colonnes dans l'ombre
        d.rectangle((x + 6, 120, x + 16, 440), fill=(10, 20, 44))
        d.rectangle((x + 4, 116, x + 18, 122), fill=(14, 26, 54))
    d.rectangle((0, 440, 270, 480), fill=(12, 22, 46))
    d = projecteurs(img, [135], 100, 440, (24, 44, 92), 0.9, t)
    D.lumiere(img, 135, 444, 110, 14, (24, 44, 92), 0.9)
    return draw(img)


def s_regles(img, d, t):
    """« Vous pensez… sauf que… trois règles » : une foule qui répond au hasard, puis trois balances."""
    if t < T["presque"]:
        d = D.ville_fond(img, t, 380, 6, 200)
        d.rectangle((0, 380, 270, 480), fill=(10, 20, 42))
        for x in (40, 230):
            D.lumiere(img, x, 380, 50, 20, (24, 44, 88), 0.8)
        d = draw(img)
        for k in range(5):
            x = 35 + k * 50
            D.ombre(d, x, 380, 10)
            P.personnage(img, (x, 380), 70, tenue=("pull", "gris", "clair", "costume", "sport")[k], miroir=k % 2,
                         tete=10 * math.sin(t * 3 + k))
            if int(t * 3 + k) % 2:
                over(P.cadre_texte, (x - 6, 250 + 12 * (k % 2)), "?!"[(k + int(t * 2)) % 2], 14, BLANC, B2)
        return
    d = _salle(img, d, t)
    if t < T["humains"] - 0.1:
        titre(d, 135, 200, "3 REGLES", 30, BLANC)
        titre(d, 135, 250, "PRESQUE PARTOUT", 12, B3)
        return
    if t < T["plus2"] - 0.1:
        cle, txt = "humains", "HUMAINS > ANIMAUX"
        g, dr = _contenu((_p("pull", 44), 0)), _contenu((lambda im, x, y: grand(im, chien, x, y, 2, t), 0))
    elif t < T["jeunes"] - 0.1:
        cle, txt = "plus2", "LE + DE VIES"
        g = _contenu(*[(_p(tn, 36), dx) for tn, dx in (("clair", -18), ("pull", -6), ("gris", 6), ("sport", 18))])
        dr = _contenu((_p("costume", 36), 0))
    else:
        cle, txt = "jeunes", "LES + JEUNES"
        g = _contenu((lambda im, x, y: enfant(im, x, y, 34, "robe"), 0))
        dr = _contenu((lambda im, x, y: vieux(im, x, y, 42, miroir=True), 0))
    u = lisse((t - T[cle]) / 0.5)
    ang = -16 * u + 2 * math.sin(t * 6) * (1 - u)                 # le côté épargné l'emporte
    D.balance(img, 135, 230, ang, t, g, dr)
    over(tampon, txt, t, T[cle], 135, 140, -4, 16, B4)
    over(P.cadre_texte, (40, 410), "EPARGNE", 8, B4, B2)
    over(P.cadre_texte, (180, 410), "SACRIFIE", 8, ROUGE, ROUGE_F)


PODIUM = [("bebe", "BEBE"), ("fille", "FILLETTE"), ("garcon", "GARCON"), ("enceinte2", "ENCEINTE")]


def s_classement(img, d, t, interdit=False):
    """« Les plus épargnés ? » : le podium sous les projecteurs ; en dessous, la cave : chien, criminel, chat."""
    d.rectangle((0, 0, 270, 480), fill=(6, 12, 28))
    d.rectangle((0, 120, 270, 290), fill=(10, 20, 44))
    for x in range(0, 270, 18):                                   # le rideau de scène
        d.line([(x, 120), (x + 4, 290)], fill=(16, 30, 62), width=3)
    d = projecteurs(img, [55, 115, 165, 225], 120, 286, (28, 52, 108), 0.9, t)
    sol = 290
    tops = D.podium(d, 135, sol, t)
    d.rectangle((0, sol, 270, 296), fill=GRIS_F)
    titre(d, 135, 126, "LES PLUS EPARGNES", 12, B4)
    for k, (cle, nom) in enumerate(PODIUM):
        if t < T[cle] - 0.1 and not interdit:
            continue
        x, y = tops[k]
        if k == 0:
            grand(img, poussette, x, y, 2, t)
        elif k == 1:
            enfant(img, x, y, 46, "robe")
        elif k == 2:
            enfant(img, x, y, 48, "pull")
        else:
            enceinte(img, x, y, 52)
        d = draw(img)
        if t < T[cle] + 0.5 and not interdit:                     # l'étincelle d'arrivée
            r = 18 * (t - T[cle] + 0.1) / 0.6
            for j in range(8):
                a = j * math.pi / 4
                d.point((x + r * math.cos(a), y - 30 + r * math.sin(a)), fill=BLANC)
    # la cave
    d.rectangle((0, 296, 270, 480), fill=(4, 8, 18))
    for y in range(300, 480, 10):
        for x in range((y // 10) % 2 * 12, 270, 24):
            d.rectangle((x, y, x + 22, y + 8), fill=(8, 14, 30))
    if t >= T["tout"] or interdit:
        titre(d, 135, 304, "TOUT EN BAS", 10, ROUGE)
        bas = [("chien", "CHIEN", 46, 356), ("criminel", "CRIMINEL", 120, 404), ("chat", "CHAT", 194, 452)]
        for cle, nom, x, y in bas:
            d.rectangle((x - 40, y, x + 40, y + 6), fill=(30, 40, 66), outline=P.CONTOUR)   # les marches qui descendent
            if t < T[cle] - 0.1 and not interdit:
                continue
            D.lumiere(img, x, y - 12, 34, 22, (20, 30, 56), 0.8)
            d = draw(img)
            if cle == "chat":
                grand(img, chat, x, y, 2, t)
            elif cle == "chien":
                grand(img, chien, x, y, 2, t)
            else:
                criminel(img, x, y, 46)
            d = draw(img)
            texte_ = P.police(8)
            d.text((x + 22, y - 14), nom, font=texte_, fill=GRIS)
        if t >= T["chien"] and not interdit:
            f = P.police(14, pixel=False)
            if int(t * 4) % 2:
                d.text((82, 384), "^", font=f, fill=B3)
                d.text((150, 432), "^", font=f, fill=B3)


def s_test(img, d, t):
    """La raison de suivre : le test en 13 situations dans un téléphone ; vous contre le monde ; PROCHAIN ÉPISODE."""
    d = D.ville_fond(img, t, 480, 8, 300)
    D.lumiere(img, 135, 280, 150, 200, (10, 20, 46), 0.8)
    d = draw(img)
    x0, y0, x1, y1 = D.telephone(img, d, 120, 270, 160, 290, t)
    D.lumiere(img, 120, 270, 120, 170, (30, 56, 110), 0.5)
    d = draw(img)
    d.rectangle((x0, y0, x1, y1), fill=NOIR)
    n = 1 + int(12 * lisse((t - T["treize"]) / 2.0)) if t >= T["treize"] else 1
    titre(d, (x0 + x1) / 2, y0 + 6, f"{n} / 13", 14, B4)
    for k in range(13):                                           # la barre de progression
        d.rectangle((x0 + 6 + k * 11.5, y0 + 26, x0 + 15 + k * 11.5, y0 + 29), fill=ROUGE if k < n else B0)
    D.ecran_jeu(d, x0 + 4, y0 + 34, x1 - x0 - 8, 110, t, (n + int(t * 1.5)) % 2)
    if t >= T["compare"]:
        u = lisse((t - T["compare"]) / 1.0)
        for k, (nom, v, c) in enumerate((("VOUS", 0.82, ROUGE), ("LE MONDE", 0.55, B3))):
            y = y0 + 160 + k * 38
            d.text((x0 + 8, y), nom, font=P.police(8), fill=BLANC)
            d.rectangle((x0 + 8, y + 12, x0 + 8 + 140 * v * u, y + 24), fill=c)
            d.rectangle((x0 + 8, y + 12, x0 + 148, y + 24), outline=B1)
    if t >= T["prochain"]:
        over(P.cadre_texte, (66, 446), "PROCHAIN EPISODE >", 8, BLANC, ROUGE)
    if t >= T["decouvrir"]:
        f = P.police(30, pixel=False)
        if int(t * 4) % 2 or t > T["decouvrir"] + 0.8:
            over(lambda dd: dd.text((212, 150), "?", font=f, fill=ROUGE))


def s_groupes(img, d, t):
    """« Mais attendez… trois grands groupes… la France est dans celui du Sud. »"""
    d.rectangle((0, 0, 270, 480), fill=(4, 8, 20))
    D.etoiles(d, t, 90, 5)
    u = t >= T["trois2"]
    cols = (B2, B4, (120, 140, 190)) if u else (B1, B1, B1)
    rot = 2.97 - 0.6 * (1 - lisse((t - T["mais"]) / 2.5)) + 0.04 * math.sin(t)
    D.lumiere(img, 135, 270, 140, 140, (12, 26, 60), 0.7)
    D.globe(img, 135, 270, 104, rot, cols, france=t >= T["france"], t=t)
    if u:
        for k, (nom, c, x) in enumerate((("OUEST", B2, 20), ("EST", B4, 115), ("SUD", (120, 140, 190), 196))):
            if t >= T["trois2"] + 0.25 * k:
                over(P.cadre_texte, (x, 400), nom, 8, NOIR, c, c)
    if t >= T["sud"]:
        over(P.cadre_texte, (98, 130), "FRANCE = SUD", 8, BLANC, ROUGE)


def s_sud(img, d, t):
    """« Dans ce groupe, on épargne davantage les femmes, et les sportifs plutôt que les personnes en surpoids. »"""
    d = _salle(img, d, t)
    if t < T["sportifs"] - 0.1:
        cle, txt = "femmes", "+ LES FEMMES"
        g = _contenu((_p("robe", 46), 0))
        dr = _contenu((_p("pull", 46, True), 0))
    else:
        cle, txt = "sportifs", "+ LES SPORTIFS"
        g = _contenu((lambda im, x, y: sportif(im, x, y, 46, t=t), 0))
        dr = _contenu((lambda im, x, y: surpoids(im, x, y, 46, miroir=True), 0))
    if t < T.get(cle, 0):
        ang = 2 * math.sin(t * 5)
    else:
        u = lisse((t - T[cle]) / 0.5)
        ang = -14 * u
    D.balance(img, 135, 230, ang, t, g, dr)
    if t >= T[cle]:
        over(tampon, txt, t, T[cle], 135, 140, -4, 16, B4)
    over(P.cadre_texte, (40, 410), "EPARGNE", 8, B4, B2)
    over(P.cadre_texte, (180, 410), "SACRIFIE", 8, ROUGE, ROUGE_F)
    over(P.cadre_texte, (102, 444), "GROUPE SUD", 8, BLANC, ROUGE)


def _rue_profil(img, t, sol=330):
    d = D.ville_fond(img, t, sol, 11, 230)
    d.rectangle((0, sol, 270, sol + 6), fill=GRIS_F)
    d.rectangle((0, sol + 6, 270, 480), fill=(10, 18, 38))
    for x in range(int(-t * 0) % 30, 270, 30):
        d.rectangle((x, sol + 40, x + 14, sol + 42), fill=B3)
    for x in (40, 200):                                           # réverbères
        d.line([(x, sol), (x, sol - 70)], fill=GRIS_F, width=2)
        d.line([(x, sol - 70), (x + 10, sol - 72)], fill=GRIS_F, width=2)
        D.cone(img, (x + 10, sol - 70), (x + 10, sol), 3, 30, (26, 48, 96), 0.8)
        d = draw(img)
        d.rectangle((x + 7, sol - 72, x + 13, sol - 68), fill=B4)
    return d


def s_paradoxe(img, d, t):
    """« La majorité veut des voitures qui sacrifient leur passager… mais pour les autres. »"""
    sol = 330
    d = _rue_profil(img, t, sol)
    if t < T["propre"] - 0.1:
        u = lisse((t - T["sacrifient"]) / 0.9)
        x = 10 + 70 * u
        for y in range(sol - 120, sol, 8):                        # le mur de briques
            for xx in range(206 + (y // 8) % 2 * 6, 252, 12):
                d.rectangle((xx, y, xx + 10, y + 6), fill=(70, 50, 60), outline=P.CONTOUR)
        choc = t >= T["sacrifient"] + 0.9
        grand_profil(img, x, sol, 2, col=B2, t=t, roule=not choc)
        d = draw(img)
        if choc:
            k = t - T["sacrifient"] - 0.9
            for j in range(16):
                a = -math.pi / 2 + (j - 8) * 0.2
                r = 50 * min(1.0, k * 3)
                if k < 1.4:
                    d.rectangle((206 + r * math.cos(a + math.pi), sol - 40 + r * math.sin(a) * 0.7 + 30 * k * k,
                                 209 + r * math.cos(a + math.pi), sol - 37 + r * math.sin(a) * 0.7 + 30 * k * k),
                                fill=(70, 50, 60) if j % 3 else B4)
        for k in range(3):                                        # les piétons sauvés, sur le trottoir d'en face
            P.personnage(img, (40 + 22 * k, 420), 50, tenue=("clair", "gris", "robe")[k],
                         mains=(40 + 22 * k + 6, 380) if choc else None)
        if choc:
            over(P.cadre_texte, (110, 410), "PIETONS SAUVES", 8, B4, B2)
        if t >= T["autres"]:
            over(P.cadre_texte, (20, 140), "LA VOITURE DES AUTRES :", 8, B4, B2)
            over(P.cadre_texte, (20, 160), "SACRIFIE LE PASSAGER", 8, BLANC, ROUGE)
    else:
        grand_profil(img, 90, sol, 2, col=B3, t=t, roule=False)
        d = draw(img)
        if t >= T["protege"]:                                     # le bouclier
            pul = 1 + 0.08 * math.sin(t * 8)
            cx, cy = 172, sol - 110
            pts = [(cx - 30 * pul, cy - 30 * pul), (cx + 30 * pul, cy - 30 * pul), (cx + 30 * pul, cy), (cx, cy + 36 * pul),
                   (cx - 30 * pul, cy)]
            d.polygon(pts, fill=B1, outline=B4)
            d.line([(cx, cy - 26), (cx, cy + 28)], fill=B4)
            d.line([(cx - 26, cy - 6), (cx + 26, cy - 6)], fill=B4)
        P.personnage(img, (70, sol + 2), 80, tenue="pull", mains=(104, sol - 50), tronc=6)
        over(P.cadre_texte, (20, 140), "MA VOITURE :", 8, B4, B2)
        if t >= T["protege"]:
            over(P.cadre_texte, (20, 160), "PROTEGE-MOI !", 8, BLANC, ROUGE)


def s_mercedes(img, d, t):
    """« La même année, un responsable de Mercedes le dit tout haut… »"""
    sol = 360
    d = D.salon(img, t, sol)
    grand_profil(img, 50, sol - 2, 2, col=GRIS, t=t, roule=False)
    d = draw(img)
    D.lumiere(img, 140, 300, 90, 30, (40, 60, 110), 0.4)
    x = 232
    P.personnage(img, (x, sol - 2), 104, tenue="costume", miroir=True,
                 mains=(x + 14, sol - 92) if t >= T["sauvez"] else None)
    d = draw(img)
    if t >= T["sauvez"]:                                          # le micro
        d.line([(x - 14, sol - 92), (x - 19, sol - 102)], fill=GRIS, width=2)
        d.ellipse((x - 24, sol - 108, x - 16, sol - 100), fill=GRIS_F, outline=P.CONTOUR)
        over(P.cadre_texte, (30, 150), "\"SAUVEZ CELUI QUI", 8, BLANC, B2)
        over(P.cadre_texte, (30, 168), "EST DANS LA VOITURE\"", 8, BLANC, B2)
    if t >= T["mercedes"]:
        over(P.cadre_texte, (24, 452), "MERCEDES, MONDIAL DE PARIS 2016", 8, B3, B1)


def s_allemagne(img, d, t):
    """« En 2017, l'Allemagne tranche : interdit de choisir selon l'âge ou le sexe. »"""
    if t < T["age"] - 0.1:
        d = D.bundestag(img, t)
        if t >= T["allemagne"]:
            over(P.cadre_texte, (92, 360), "ALLEMAGNE", 8, BLANC, ROUGE)
            over(P.cadre_texte, (40, 380), "COMMISSION D'ETHIQUE", 8, B4, B2)
        return
    s_classement(img, d, t, interdit=True)
    over(tampon, "INTERDIT : AGE / SEXE", t, T["age"], 135, 220, -10, 14)
    if t >= T["exactement"]:
        over(P.cadre_texte, (60, 300), "LE CHOIX DU MONDE ENTIER", 8, BLANC, ROUGE)


def s_fin(img, d, t):
    """« Alors, votre voiture : elle sauve qui ? Vous… ou eux ? »"""
    d = D.route_nuit(img, t, PASSAGE)
    D.traces(d, 135, PASSAGE + 96, 480)
    gens(img, d, t, 99.0, False)
    D.voiture_dessus(img, 135, PASSAGE + 62, 0, alerte=True, t=t, freinage=1.0)
    d = draw(img)
    pluie(d, t)
    if t >= T["vous3"]:
        sel = int(t * 2.5) % 2 if t < T["eux"] + 0.8 else 1
        for k, (nom, x) in enumerate((("VOUS", 50), ("EUX", 170))):
            c = ROUGE if sel == k else B1
            over(P.cadre_texte, (x, 420), f"  {nom}  ", 14, BLANC, c, ROUGE_F if sel == k else NOIR)


def ecrans():
    return [(0.0, "route"), (T["rw1"], s_mit), (T["resultat"] - 0.1, s_planete), (T["vous"] - 0.1, s_regles),
            (T["les"] - 0.1, s_classement), (T["ce"] - 0.1, s_test), (T["mais"] - 0.1, s_groupes),
            (T["dans"] - 0.1, s_sud), (T["et_fou"] - 0.1, s_paradoxe), (T["la_meme"] - 0.1, s_mercedes),
            (T["en"] - 0.1, s_allemagne), (T["alors2"] - 0.1, s_fin)]


def histoire(t):
    """L'accroche : la voiture fonce, fige devant le passage, puis rembobine jusqu'au début."""
    tr0, tr1 = T["rw0"], T["rw1"]
    if t < tr0:
        return t, False
    if t < tr1:
        u = (t - tr0) / (tr1 - tr0)
        return tr0 * (1 - u) ** 1.4, True
    return T["devant"] + 0.2 + (t - tr1) * 0.2, False


DATES = [("lance", "resultat", "2016"), ("en", "exactement", "2017")]


CAM = [0.0, 0.0, 1.0]


def E(x, y):
    """Point du décor → point à l'écran (après le cadrage de la caméra)."""
    return (x - CAM[0]) * CAM[2], (y - CAM[1]) * CAM[2]


def camera(t, scene):
    if scene == "route":
        s, rw = histoire(t)
        if rw:
            return 1.3, 135, PASSAGE + 50
        if T["personne"] - 0.1 <= s < T["choisir"]:                 # gros plan sur l'habitacle vide
            return 2.6, 135, 380
        if s >= T["choisir"]:
            u = lisse((s - T["choisir"]) / 1.5)
            return 1.3 + 0.35 * u, 135, PASSAGE + 50 - 15 * u
        return 1.3, 135, PASSAGE + 50
    if scene is s_fin:
        return 1.3, 135, PASSAGE + 50
    return 1.0, 135, 240


def image(t):
    OVER.clear()
    img, _ = P.toile()
    img = P.halo(img, 135, 300, 200, B0, 0.5)
    d = draw(img)
    P.poussieres(d, t)
    ec = ecrans()
    k = max(i for i, x in enumerate(ec) if x[0] <= t)
    scene = ec[k][1]
    rembobine = False
    z, cx, cy = camera(t, scene)
    CAM[:] = [min(max(0, cx - P.LW / z / 2), P.LW - P.LW / z), min(max(0, cy - P.LH / z / 2), P.LH - P.LH / z), z]
    if scene == "route":
        s, rembobine = histoire(t)
        s_route(img, d, t, s)
    else:
        scene(img, d, t)
    w, h = P.LW / z, P.LH / z
    x0, y0 = min(max(0, cx - w / 2), P.LW - w), min(max(0, cy - h / 2), P.LH - h)
    if z != 1.0:
        img = img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((P.LW, P.LH), Image.NEAREST)
    dx = dy = 0
    for tc, amp in ((T["rw0"] - 0.05, 7), (T["mais"], 4), (T["age"], 5)):
        if t >= tc:
            kk = math.exp(-6 * (t - tc)) * math.sin(60 * (t - tc))
            dx += int(amp * kk)
            dy += int(amp * 0.7 * kk)
    if dx or dy:
        img = Image.fromarray(np.roll(np.roll(np.asarray(img), dx, 1), dy, 0))
    d = draw(img)
    v = 0.15                                                        # la jauge DILEMME
    if scene == "route":
        s = histoire(t)[0]
        v = 0.15 + 0.8 * lisse((s - T["freins"]) / (T["tuer"] - T["freins"] + 0.5))
        if rembobine:
            v = 0.15
    elif scene in (s_mit, s_planete):
        v = 0.4
    elif scene in (s_regles, s_classement, s_test):
        v = 0.3
    elif scene in (s_groupes, s_sud):
        v = 0.6
    elif scene in (s_paradoxe, s_mercedes):
        v = 0.8
    elif scene is s_allemagne:
        v = 0.5
    elif scene is s_fin:
        v = 0.95
    P.jauge(d, t, v, etiquette="DILEMME", valeur="", alerte=v > 0.85)
    if t < 2.4:
        f = P.police(16, pixel=False)
        d.text((70, 290), "QUI SAUVER ?", font=f, fill=BLANC)
    for fn, args in OVER:
        fn(img, *args) if fn is tampon else fn(d, *args)
    for a_, b_, txt in DATES:
        if T[a_] - 0.1 <= t < T[b_] - 0.1:
            date(d, txt, t, T[a_] - 0.1)
    a = np.asarray(P.agrandir(img))
    if rembobine:
        a = P.vhs(a, t)
        im = Image.fromarray(a)
        dd = ImageDraw.Draw(im)
        for k2 in range(2):
            x = 900 + 46 * k2
            dd.polygon([(x + 40, 120), (x, 96), (x, 144)], fill=BLANC) if False else \
                dd.polygon([(x, 120), (x + 40, 96), (x + 40, 144)], fill=BLANC)
        a = np.asarray(im)
    if t < 0.1:
        a = (a.astype(np.float32) * (t / 0.1) + 255 * (1 - t / 0.1)).astype(np.uint8)
    return a


# ------------------------------------------------------------------------------------------------ son
def sons():
    f = J.fichier
    ev = [(0.0, f("boum_cine", 0.4, 2.0), "accent", 0.0), (T["freins"], J.alerte(3, 0.06), "interface", 0.0),
          (T["freins"] + 0.1, J.moteur(3.0, 0.03), "ambiance", 0.0),
          (T["enceinte"], J.selection(), "effet", -0.4), (T["agees"], J.selection(), "effet", 0.4),
          (T["personne"], f("mystere", 0.2, 2.0), "ambiance", 0.0), (T["choisir"], f("souffle_sombre", 0.3), "ambiance", 0.0),
          (T["rw0"] - 0.05, f("arret", 0.35), "accent", 0.0),
          (T["rw0"], f("rembobine", 0.4, 0.8), "effet", 0.0), (T["rw0"], f("glitch", 0.3), "effet", 0.0),
          (T["cette"], f("ouverture", 0.3), "effet", 0.0), (T["lance"], J.selection(), "effet", 0.0),
          (T["toulouse"], f("ping", 0.25), "effet", 0.0)]
    ev += [(T["quarante"] + 0.05 * i, J.tic_compteur(i), "interface", 0.0) for i in range(26)]
    ev += [(T["quarante"] + 1.4, J.piece(), "effet", 0.0), (T["deux"] + 1.0, J.piece(), "effet", 0.0)]
    ev += [(T["sauf"], f("arret", 0.3), "effet", 0.0)]
    ev += [(T[c], f("impact", 0.3), "accent", 0.0) for c in ("humains", "plus2", "jeunes")]
    ev += [(T[c], J.piece(), "effet", 0.0) for c, _ in PODIUM]
    ev += [(T["tout"], J.degat(), "effet", 0.0), (T["chat"], f("erreur", 0.25), "effet", 0.0),
           (T["criminel"], f("impact", 0.2), "effet", 0.0), (T["chien"], f("confirmation", 0.25), "effet", 0.0)]
    ev += [(T["treize"] + 0.16 * i, J.trace(600 + 30 * i), "interface", 0.0) for i in range(12)]
    ev += [(T["compare"], J.montee(1.0, 0.05), "effet", 0.0), (T["prochain"], f("reussite", 0.3), "effet", 0.0),
           (T["decouvrir"], f("question", 0.3), "effet", 0.0)]
    ev += [(T["mais"], f("arret", 0.3), "effet", 0.0), (T["mais"], f("impact", 0.3), "accent", 0.0),
           (T["trois2"], J.selection(), "effet", -0.4), (T["trois2"] + 0.25, J.selection(), "effet", 0.0),
           (T["trois2"] + 0.5, J.selection(), "effet", 0.4), (T["france"], J.alerte(2, 0.05), "interface", 0.0),
           (T["sud"], f("confirmation", 0.3), "effet", 0.0),
           (T["femmes"], f("bascule", 0.3), "effet", -0.3), (T["sportifs"], f("swoosh_court", 0.3), "effet", 0.3),
           (T["surpoids"], f("bascule", 0.3), "effet", 0.3)]
    ev += [(T["et_fou"], f("boum_grave", 0.35), "accent", 0.0), (T["sacrifient"] + 0.9, f("impact", 0.4), "accent", 0.3),
           (T["autres"], f("question", 0.25), "effet", 0.0), (T["protege"], f("erreur", 0.25), "effet", 0.0),
           (T["sauvez"], f("ping", 0.25), "effet", 0.0),
           (T["en"], f("boum_grave", 0.35), "accent", 0.0), (T["age"], f("boum_cine", 0.45, 2.0), "accent", 0.0),
           (T["exactement"], f("rayure", 0.3, 1.0), "effet", 0.0),
           (T["vous3"], J.alerte(2, 0.05), "interface", 0.0), (T["eux"], J.selection(), "effet", 0.0),
           (T["que_fin"] + 0.3, f("arret", 0.35), "effet", 0.0)]
    dur = T["fin"] + 1.8
    mus = Z.musique(dur, [(0, "tension"), (T["freins"], "pulsation"), (T["rw0"], "silence"),
                          (T["cette"], "reflexion"), (T["vous"], "tension"), (T["les"], "lumineux"),
                          (T["ce"], "lumineux"), (T["mais"], "silence"), (T["mais"] + 0.8, "pulsation"),
                          (T["et_fou"], "tension2"), (T["en"], "silence"), (T["en"] + 0.8, "tension"),
                          (T["alors2"], "pulsation"), (T["que_fin"] + 0.3, "silence")])
    mus = mus.mean(1) if mus.ndim == 2 else mus
    ev.append((0.0, mus, "ambiance", 0.0))
    ev.append((T["fin"] + 0.1, J.suite_demain(), "effet", 0.0))
    return ev


# (nom, mot cherché, repère après lequel le chercher)
REPERES = [("freins", "freins", None), ("devant", "devant", None), ("enceinte", "enceinte", "devant"),
           ("autre", "lautre", "enceinte"), ("trois", "trois", "autre"), ("agees", "agees", "trois"),
           ("personne", "personne", "agees"), ("choisir", "choisir", "personne"), ("alors", "alors", "choisir"),
           ("tuer", "tuer", "alors"), ("cette", "cette", "tuer"), ("lance", "lance", "cette"), ("mit", "mit", "cette"),
           ("moral", "moral", "lance"), ("parmi", "parmi", "moral"), ("toulouse", "toulouse", "parmi"),
           ("bonnefon", "bonnefon", "toulouse"), ("resultat", "resultat", "bonnefon"), ("quarante", "quarante", "resultat"),
           ("deux", "deux", "quarante"), ("vous", "vous", "deux"), ("sauf", "sauf", "vous"),
           ("presque", "presque", "sauf"), ("humains", "humains", "presque"), ("plus2", "plus", "animaux"),
           ("jeunes", "jeunes", "plus2"), ("les", "les", "jeunes"), ("bebe", "bebe", "les"), ("fille", "fille", "bebe"),
           ("garcon", "garcon", "fille"), ("enceinte2", "enceinte", "garcon"), ("tout", "tout", "enceinte2"),
           ("chat", "chat", "tout"), ("criminel", "criminel", "chat"), ("chien", "chien", "criminel"),
           ("ce", "ce", "chien"), ("treize", "treize", "ce"), ("compare", "compare", "treize"),
           ("prochain", "prochain", "compare"), ("decouvrir", "decouvrir", "prochain"), ("mais", "mais", "decouvrir"),
           ("trois2", "trois", "mais"), ("france", "france", "trois2"), ("sud", "sud", "france"),
           ("dans", "dans", "sud"), ("femmes", "femmes", "dans"), ("sportifs", "sportifs", "femmes"),
           ("surpoids", "surpoids", "sportifs"), ("et_fou", "et", "surpoids"), ("sacrifient", "sacrifient", "et_fou"),
           ("autres", "autres", "sacrifient"), ("propre", "propre", "autres"), ("protege", "protege", "propre"),
           ("la_meme", "la", "protege"), ("mercedes", "mercedes", "la_meme"), ("sauvez", "sauvez", "mercedes"),
           ("en", "en", "sauvez"), ("allemagne", "lallemagne", "en"), ("age", "lage", "allemagne"),
           ("exactement", "exactement", "age"), ("alors2", "alors", "exactement"), ("vous3", "vous", "alors2"),
           ("eux", "eux", "vous3")]
AUX = {"animaux": ("animaux", "humains")}


def preparer():
    global VOIX
    chemin = os.path.join(ICI, "audio", "voix.mp3")
    MV.charger(types.SimpleNamespace(SEGS=os.path.join(ICI, "audio", "voix.json"), VOIX=chemin))
    VOIX, _, _ = MI.tighten(MI.load_voice(chemin), max_gap=0.40, thr_db=-38.0)
    T.clear()
    for nom, cle, apres_ in REPERES:
        if apres_ in AUX:
            c, ap = AUX[apres_]
            T[apres_] = MV.mot(c, T[ap] + 0.01)
        base = T[apres_] + 0.01 if apres_ else 0.0
        T[nom] = MV.mot(cle, base)
    T["rw0"] = MV.mot("tuer", T["alors"], fin=True) + 0.05
    T["rw1"] = T["rw0"] + 0.8
    T["que_fin"] = MV.MOTS[-1][1]
    T["fin"] = T["que_fin"] + 0.6
    return VOIX


def rendre(sortie, t0=0.0, t1=None):
    voix = preparer()
    dur = T["fin"] + 1.8
    t1 = t1 or dur
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{P.W}x{P.H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    for f in range(int(t0 * FPS), int(t1 * FPS)):
        t = f / FPS
        a = image(t) if t < T["fin"] else _carton(t)
        ff.stdin.write(np.ascontiguousarray(a).tobytes())
    ff.stdin.close()
    ff.wait()
    MP.mixer(f"{tmp}/a.wav", voix[:int(T["fin"] * MI.SR)], dur, sons())
    filt = MP.loudnorm(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}",
                    "-i", f"{tmp}/a.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", filt, "-ar", "48000",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", sortie], check=True)
    print("OK", sortie)


def _carton(t):
    img, d = P.toile()
    f = P.police(16, pixel=False)
    for k, txt in enumerate(("PROCHAIN EPISODE :", "PASSEZ LE TEST")):
        w = d.textlength(txt, font=f)
        d.text(((P.LW - w) / 2, 206 + 26 * k), txt, font=f, fill=BLANC if k else B3)
    w = d.textlength("PASSEZ LE TEST", font=f)
    x = (P.LW + w) / 2 + 6
    d.polygon([(x, 236), (x + 10, 242), (x, 248)], fill=ROUGE)
    return np.asarray(P.agrandir(img))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep34.mp4"
    if len(sys.argv) > 3:
        rendre(out, float(sys.argv[2]), float(sys.argv[3]))
    else:
        rendre(out)
