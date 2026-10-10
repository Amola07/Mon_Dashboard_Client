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
def enceinte(img, x, y, taille=40, miroir=False, marche=None):
    s = taille / 92
    P.personnage(img, (x, y), taille, tenue="robe", miroir=miroir, marche=marche)
    d = draw(img)
    sx = -1 if miroir else 1
    cx, cy, r = x + sx * 7 * s, y - 52 * s, 7 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=B3, outline=P.CONTOUR)
    d.point((cx + sx * 2, cy - 2), fill=B4)


def vieux(img, x, y, taille=40, miroir=False):
    s = taille / 92
    sx = -1 if miroir else 1
    P.personnage(img, (x, y), taille, tronc=14, flexion=0.3, tenue="vieux", miroir=miroir,
                 mains=(x + 24 * s, y - 40 * s) if not miroir else None)
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


# ------------------------------------------------------------------------------------------------ la route (dessus)
def route(d, t, defile=0.0):
    """La route vue de dessus : deux voies, trottoirs, passage piéton."""
    d.rectangle((0, 0, 270, 480), fill=(8, 16, 36))
    d.rectangle((0, 0, 36, 480), fill=B0)                                             # trottoirs
    d.rectangle((234, 0, 270, 480), fill=B0)
    for y in range(int(-defile) % 16 - 16, 480, 16):
        d.line([(36, y), (36, y + 14)], fill=B1)
        d.line([(234, y), (234, y + 14)], fill=B1)
    for y in range(int(defile * 1.0) % 30 - 30, 480, 30):                              # la ligne médiane
        if not (PASSAGE - 22 < y < PASSAGE + 22):
            d.rectangle((134, y, 136, y + 14), fill=B3)
    for x in range(42, 230, 12):                                                      # les bandes du passage
        d.rectangle((x, PASSAGE - 18, x + 6, PASSAGE + 18), fill=(40, 60, 100))
    for k in range(5):                                                                # des arbres sur le trottoir
        yy = (k * 110 + defile) % 560 - 40
        for xx in (16, 252):
            d.ellipse((xx - 12, yy - 12, xx + 12, yy + 12), fill=B1, outline=B0)
            d.ellipse((xx - 6, yy - 8, xx + 4, yy + 2), fill=B2)


def voiture_dessus(img, cx, cy, ang=0.0, alerte=False, t=0.0, toit=True):
    """La voiture autonome vue de dessus (avant vers le haut)."""
    w, h = 40, 66
    cal = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    d = draw(cal)
    ox, oy = 12, 12
    d.rounded_rectangle((ox, oy, ox + w, oy + h), 9, fill=B2, outline=P.CONTOUR)
    d.rounded_rectangle((ox + 3, oy + 4, ox + w - 3, oy + h - 4), 7, fill=B3)
    d.polygon([(ox + 6, oy + 18), (ox + w - 6, oy + 18), (ox + w - 9, oy + 26), (ox + 9, oy + 26)], fill=B0)   # pare-brise
    if toit:
        d.rectangle((ox + 8, oy + 26, ox + w - 8, oy + 48), fill=B2)
    else:                                                                              # l'habitacle vide
        d.rectangle((ox + 8, oy + 26, ox + w - 8, oy + 48), fill=B0)
        for sx in (ox + 10, ox + w - 18):
            d.rounded_rectangle((sx, oy + 30, sx + 8, oy + 40), 2, fill=GRIS_F)
        cx_, cy_ = ox + 14, oy + 28                                                    # le volant qui tourne seul
        d.ellipse((cx_ - 4, cy_ - 2, cx_ + 4, cy_ + 2), outline=GRIS)
        a = t * 5
        d.line([(cx_ - 4 * math.cos(a), cy_ - 2 * math.sin(a)), (cx_ + 4 * math.cos(a), cy_ + 2 * math.sin(a))], fill=GRIS)
    d.polygon([(ox + 9, oy + 48), (ox + w - 9, oy + 48), (ox + w - 6, oy + 55), (ox + 6, oy + 55)], fill=B0)   # lunette
    d.rectangle((ox + 16, oy + 6, ox + w - 16, oy + 12), fill=B1)                    # le capteur sur le capot
    for x in (ox + 4, ox + w - 8):
        d.rectangle((x, oy + 1, x + 4, oy + 3), fill=B4)                              # phares
    feu = ROUGE if (alerte and int(t * 8) % 2) else ROUGE_F
    for x in (ox + 4, ox + w - 8):
        d.rectangle((x, oy + h - 3, x + 4, oy + h - 1), fill=feu)
    for x, y in ((ox - 2, oy + 10), (ox + w - 1, oy + 10), (ox - 2, oy + h - 20), (ox + w - 1, oy + h - 20)):
        d.rectangle((x, y, x + 3, y + 10), fill=NOIR)
    cal = cal.rotate(-ang, resample=Image.NEAREST, expand=True)
    img.paste(cal, (int(cx - cal.width / 2), int(cy - cal.height / 2)), cal)


def voiture_profil(d, x, y, col=B2, t=0.0, roule=True):
    """Une voiture de profil, sans marque (avant vers la droite)."""
    d.rounded_rectangle((x, y - 22, x + 78, y - 6), 5, fill=col, outline=P.CONTOUR)
    d.polygon([(x + 16, y - 22), (x + 26, y - 36), (x + 54, y - 36), (x + 66, y - 22)], fill=col, outline=P.CONTOUR)
    d.polygon([(x + 20, y - 23), (x + 28, y - 33), (x + 39, y - 33), (x + 39, y - 23)], fill=B0)
    d.polygon([(x + 42, y - 23), (x + 42, y - 33), (x + 53, y - 33), (x + 62, y - 23)], fill=B0)
    d.rectangle((x + 72, y - 18, x + 77, y - 14), fill=B4)
    d.rectangle((x + 1, y - 18, x + 4, y - 14), fill=ROUGE_F)
    for cx in (x + 17, x + 61):
        d.ellipse((cx - 8, y - 14, cx + 8, y + 2), fill=NOIR, outline=GRIS_F)
        a = t * 12 if roule else 0
        d.line([(cx - 5 * math.cos(a), y - 6 - 5 * math.sin(a)), (cx + 5 * math.cos(a), y - 6 + 5 * math.sin(a))], fill=GRIS)


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


# ------------------------------------------------------------------------------------------------ les scènes
def s_route(img, d, t, s):
    """L'accroche (s = temps de l'histoire) : la voiture sans freins fonce vers le passage ; qui choisir ?"""
    route(d, t, defile=0.0)
    gauche = s >= T["devant"] - 0.2
    droite = s >= T["autre"] - 0.2
    if gauche:                                                    # la femme enceinte, voie de gauche
        enceinte(img, 80, PASSAGE + 6, 50)
        if s >= T["enceinte"]:
            over(bulle, *E(54, PASSAGE + 22), "ENCEINTE", BLANC, B2)
    if droite:                                                    # trois personnes âgées, voie de droite
        for k, x in enumerate((162, 184, 206)):
            if s >= T["trois"] - 0.1 + 0.15 * k:
                vieux(img, x, PASSAGE + 6, 46, miroir=True)
        if s >= T["agees"]:
            over(bulle, *E(164, PASSAGE + 22), "3 AGEES", BLANC, B2)
    v = 0.0 if s < T["freins"] else min(1.0, (s - T["freins"]) / 2.0)
    arrivee = T["rw0"]
    u = lisse((s - (T["choisir"] - 0.2)) / (arrivee - T["choisir"] + 0.2))
    cy = 400 - 20 * lisse(s / 1.2) - (380 - PASSAGE - 62) * u                      # la voiture avance (s'arrête juste avant le passage)
    ang = 9 * math.sin(s * 3.1) * lisse((s - T["choisir"]) / 0.6) if s > T["choisir"] else 0.0   # elle hésite
    cx = 135 + 30 * math.sin(s * 3.1) * lisse((s - T["choisir"]) / 0.6) if s > T["choisir"] else 135
    voiture_dessus(img, cx, cy, ang, alerte=s >= T["freins"], t=s, toit=not (T["personne"] - 0.1 <= s < T["choisir"]))
    if s >= T["freins"]:
        clign = int(s * 6) % 2
        over(P.cadre_texte, (98, 440), "FREINS : HS", 8, BLANC if clign else ROUGE, ROUGE, ROUGE_F if clign else NOIR)
    if T["personne"] - 0.1 <= s < T["choisir"]:
        over(P.cadre_texte, (70, 140), "CONDUCTEUR : AUCUN", 8, B4, B2)
    if s >= T["alors"]:
        f = P.police(36, pixel=False)
        if int(s * 4) % 2 or s > T["alors"] + 0.6:
            over(lambda dd: dd.text((122, 130), "?", font=f, fill=ROUGE))


def s_mit(img, d, t):
    """« Cette question… » → « Résultat » : le jeu en ligne du MIT, 2016, Bonnefon à Toulouse."""
    img.paste(Image.new("RGB", (1, 1)), (0, 0))
    ex, ey, ew, eh = 20, 150, 230, 170                            # l'écran d'ordinateur
    d.rectangle((ex - 6, ey - 6, ex + ew + 6, ey + eh + 6), fill=GRIS_F, outline=P.CONTOUR)
    d.rectangle((ex, ey, ex + ew, ey + eh), fill=NOIR)
    d.rectangle((ex + ew / 2 - 20, ey + eh + 6, ex + ew / 2 + 20, ey + eh + 18), fill=GRIS_F)
    d.rectangle((ex + ew / 2 - 40, ey + eh + 18, ex + ew / 2 + 40, ey + eh + 22), fill=GRIS_F)
    u = lisse((t - T["cette"]) / 0.6)
    if u > 0:
        titre(d, 135, ey + 8, "MORAL MACHINE", 12, B4)
        for k, x in enumerate((ex + 8, ex + ew / 2 + 4)):        # deux scénarios côte à côte, l'un choisi
            w = ew / 2 - 12
            choisi = t >= T["lance"] and (int((t - T["lance"]) * 1.5) % 2 == k)
            d.rectangle((x, ey + 30, x + w, ey + 150), fill=B0, outline=ROUGE if choisi else B1, width=2 if choisi else 1)
            d.rectangle((x + w / 2 - 12, ey + 30, x + w / 2 + 12, ey + 150), fill=(8, 16, 36))
            for y in range(int(ey + 40), int(ey + 150), 14):
                d.line([(x + w / 2, y), (x + w / 2, y + 6)], fill=B3)
            d.rectangle((x + w / 2 - 8 + (k * 2 - 1) * 4, ey + 110, x + w / 2 + 8 + (k * 2 - 1) * 4, ey + 135), fill=B2)
            for j in range(3 if k else 1):
                px = x + 10 + j * 9 if k == 0 else x + w - 12 - j * 9
                d.ellipse((px - 3, ey + 62, px + 3, ey + 68), fill=P.PEAU)
                d.rectangle((px - 3, ey + 68, px + 3, ey + 80), fill=B3 if k == 0 else GRIS)
            d.text((x + w / 2 - 14, ey + 137), "CHOISIR", font=P.police(8), fill=B4)
    if t >= T["parmi"]:                                           # le chercheur de Toulouse
        x = 50 + 20 * lisse((t - T["parmi"]) / 0.5)
        P.personnage(img, (x, 460), 110, tenue="costume", mains=None if t < T["bonnefon"] else (x + 30, 380))
        if t >= T["toulouse"]:
            over(P.cadre_texte, (130, 390), "TOULOUSE", 8, BLANC, ROUGE)
        if t >= T["bonnefon"]:
            over(P.cadre_texte, (130, 400), "J.-F. BONNEFON", 8, B4, B2)
    if t >= T["mit"]:
        over(lambda dd: (dd.rectangle((14, 112, 70, 140), fill=ROUGE_F, outline=ROUGE),
                         dd.text((22, 114), "MIT", font=P.police(20, pixel=False), fill=BLANC)))


def _continents(d, cols, t=0.0, france=False):
    """Une carte du monde très grossière (pixel) ; cols : couleur par groupe (ouest, est, sud)."""
    o, e, s = cols
    poly = {
        "amn": ([(14, 40), (40, 28), (78, 30), (92, 46), (70, 70), (56, 92), (40, 80), (22, 62)], o),
        "ams": ([(60, 96), (82, 102), (92, 124), (78, 160), (68, 176), (62, 150), (54, 118)], s),
        "eur": ([(118, 36), (148, 30), (160, 42), (146, 58), (126, 62), (118, 54)], o),
        "fr": ([(122, 54), (132, 52), (134, 62), (124, 64)], s),
        "afr": ([(120, 70), (156, 68), (170, 92), (160, 130), (146, 150), (134, 122), (118, 92)], s),
        "asi": ([(160, 30), (230, 26), (256, 48), (240, 74), (214, 92), (190, 84), (170, 70), (158, 50)], e),
        "moy": ([(160, 70), (184, 72), (182, 92), (166, 88)], e),
        "oce": ([(214, 130), (246, 126), (250, 148), (224, 152)], o),
    }
    for k, (pts, c) in poly.items():
        if k == "fr" and france:
            c = ROUGE if int(t * 5) % 2 else BLANC
        d.polygon(pts, fill=c, outline=P.CONTOUR)


def carte(img, d, t, x0, y0, cols, france=False, eclat=1.0):
    tmp = Image.new("RGB", (270, 190), NOIR)
    dd = draw(tmp)
    for y in range(0, 190, 10):
        dd.line([(0, y), (270, y)], fill=(10, 20, 44))
    for x in range(0, 270, 10):
        dd.line([(x, 0), (x, 190)], fill=(10, 20, 44))
    _continents(dd, cols, t, france)
    img.paste(tmp, (x0, y0))


def s_planete(img, d, t):
    """« Résultat : 40 millions de décisions, 233 pays » : la carte s'allume, le compteur monte."""
    u = lisse((t - T["resultat"]) / 2.2)
    carte(img, d, t, 0, 170, (B2, B2, B2))
    rng = np.random.default_rng(5)
    for k in range(int(260 * u)):                                 # les décisions qui tombent partout
        x, y = rng.uniform(10, 260), rng.uniform(180, 350)
        if np.asarray(img)[int(y), int(x)].sum() > 150:
            d.point((x, y), fill=B4 if k % 3 else BLANC)
    if t >= T["quarante"]:
        v = 40_000_000 * lisse((t - T["quarante"]) / 1.4)
        over(compteur, 135, 118, v, "", 20, BLANC)
        over(P.cadre_texte, (88, 146), "DECISIONS", 8, B4, B2)
    if t >= T["deux"]:
        v = 233 * lisse((t - T["deux"]) / 1.0)
        over(compteur, 135, 380, v, " PAYS", 16, B4)


def grand(img, fn, x, y, k=2, *args):
    """Dessine un petit sujet (animal, poussette) agrandi k fois, pieds en (x, y)."""
    tmp = Image.new("RGBA", (60, 40), (0, 0, 0, 0))
    fn(draw(tmp), 30, 36, *args)
    tmp = tmp.resize((60 * k, 40 * k), Image.NEAREST)
    img.paste(tmp, (int(x - 30 * k), int(y - 36 * k)), tmp)


def s_regles(img, d, t):
    """« Vous pensez… sauf que… trois règles » : une foule qui répond au hasard, puis trois tampons."""
    if t < T["presque"]:
        for k in range(5):
            x = 35 + k * 50
            P.personnage(img, (x, 360), 64, tenue=("pull", "gris", "clair", "costume", "sport")[k], miroir=k % 2)
            if int(t * 3 + k) % 2:
                over(P.cadre_texte, (x - 6, 230 + 12 * (k % 2)), "?!"[(k + int(t * 2)) % 2], 14, BLANC, B2)
        return
    if t < T["humains"] - 0.1:
        titre(d, 135, 200, "3 REGLES", 30, BLANC)
        titre(d, 135, 250, "PRESQUE PARTOUT", 12, B3)
        return
    lignes = [("humains", "HUMAINS > ANIMAUX", 140), ("plus2", "LE + DE VIES", 250), ("jeunes", "LES + JEUNES", 360)]
    for cle, txt, y in lignes:
        if t >= T[cle]:
            over(tampon, txt, t, T[cle], 135, y, -4, 14, B4)
    P.personnage(img, (60, 220), 64, tenue="pull")
    grand(img, chien, 210, 216, 2, t)
    if t >= T["plus2"]:
        for k in range(4):
            P.personnage(img, (160 + 22 * k, 330), 50, tenue="clair")
        P.personnage(img, (60, 330), 50, tenue="gris")
    if t >= T["jeunes"]:
        enfant(img, 210, 440, 46)
        vieux(img, 60, 440, 56)


PODIUM = [("bebe", "BEBE"), ("fille", "FILLETTE"), ("garcon", "GARCON"), ("enceinte2", "ENCEINTE")]


def s_classement(img, d, t, interdit=False):
    """« Les plus épargnés ? » : le classement, du bébé (en haut) au chat (en bas)."""
    titre(d, 135, 116, "LES PLUS EPARGNES", 12, B4)
    for k, (cle, nom) in enumerate(PODIUM):
        if t < T[cle] - 0.1 and not interdit:
            continue
        y = 170 + k * 46
        d.rectangle((20, y - 34, 250, y + 4), fill=B0, outline=B1)
        d.text((28, y - 26), f"{k + 1}", font=P.police(14, pixel=False), fill=B3)
        d.text((120, y - 20), nom, font=P.police(8), fill=BLANC)
        if k == 0:
            grand(img, poussette, 70, y, 2, t) if False else poussette(d, 70, y, t)
        elif k == 1:
            enfant(img, 70, y, 30, "robe")
        elif k == 2:
            enfant(img, 70, y, 32, "pull")
        else:
            enceinte(img, 70, y, 36)
    if t >= T["tout"] or interdit:                                # le bas du classement
        d.line([(20, 360), (250, 360)], fill=GRIS_F)
        d.text((108, 356), "...", font=P.police(8), fill=GRIS)
        bas = [("chien", "CHIEN", 380), ("criminel", "CRIMINEL", 414), ("chat", "CHAT", 448)]
        for cle, nom, y in bas:
            if t < T[cle] - 0.1 and not interdit:
                continue
            d.rectangle((20, y - 26, 250, y + 4), fill=(10, 18, 40), outline=ROUGE_F)
            d.text((120, y - 16), nom, font=P.police(8), fill=GRIS)
            if cle == "chat":
                chat(d, 70, y, t)
            elif cle == "chien":
                chien(d, 70, y, t)
            else:
                criminel(img, 70, y, 28)
        if t >= T["chien"] and not interdit:
            d.text((200, 370), "^", font=P.police(14, pixel=False), fill=B3)


def s_test(img, d, t):
    """La raison de suivre : le test en 13 situations, comparé au reste du monde ; PROCHAIN ÉPISODE."""
    ex, ey, ew, eh = 50, 120, 170, 290                            # un téléphone
    d.rounded_rectangle((ex - 6, ey - 10, ex + ew + 6, ey + eh + 10), 12, fill=GRIS_F, outline=P.CONTOUR)
    d.rectangle((ex, ey, ex + ew, ey + eh), fill=NOIR)
    n = 1 + int(12 * lisse((t - T["treize"]) / 2.0)) if t >= T["treize"] else 1
    titre(d, 135, ey + 8, f"{n} / 13", 14, B4)
    for k in range(2):                                            # deux petites scènes
        x = ex + 8 + k * 80
        d.rectangle((x, ey + 34, x + 74, ey + 120), fill=B0, outline=B1)
        d.rectangle((x + 30, ey + 34, x + 44, ey + 120), fill=(8, 16, 36))
        d.rectangle((x + 32, ey + 96, x + 42, ey + 114), fill=B2)
        for j in range(1 + (n + k) % 3):
            px = x + 8 + j * 7 if k == 0 else x + 66 - j * 7
            d.ellipse((px - 2, ey + 50, px + 2, ey + 54), fill=P.PEAU)
            d.rectangle((px - 2, ey + 54, px + 2, ey + 64), fill=B3 if (j + n) % 2 else GRIS)
    if t >= T["compare"]:                                         # VOUS contre LE MONDE
        u = lisse((t - T["compare"]) / 1.0)
        for k, (nom, v, c) in enumerate((("VOUS", 0.82, ROUGE), ("MONDE", 0.55, B3))):
            y = ey + 140 + k * 40
            d.text((ex + 8, y), nom, font=P.police(8), fill=BLANC)
            d.rectangle((ex + 8, y + 12, ex + 8 + 150 * v * u, y + 22), fill=c)
            d.rectangle((ex + 8, y + 12, ex + 158, y + 22), outline=B1)
    if t >= T["prochain"]:
        over(P.cadre_texte, (66, 430), "PROCHAIN EPISODE >", 8, BLANC, ROUGE)
    if t >= T["decouvrir"]:
        f = P.police(30, pixel=False)
        if int(t * 4) % 2 or t > T["decouvrir"] + 0.8:
            d.text((ex + ew / 2 - 8, ey + 236), "?", font=f, fill=ROUGE)


def s_groupes(img, d, t):
    """« Mais attendez… trois grands groupes… la France est dans celui du Sud. »"""
    u = t >= T["trois2"]
    cols = ((B2, B3, (90, 110, 150)) if u else (B1, B1, B1))
    carte(img, d, t, 0, 160, cols, france=t >= T["france"])
    if u:
        for k, (nom, c, x) in enumerate((("OUEST", B2, 20), ("EST", B3, 110), ("SUD", (150, 170, 210), 190))):
            if t >= T["trois2"] + 0.25 * k:
                over(P.cadre_texte, (x, 370), nom, 8, NOIR, c, c)
    if t >= T["sud"]:
        over(P.cadre_texte, (110, 120), "FRANCE = SUD", 8, BLANC, ROUGE)


def s_sud(img, d, t):
    """« Dans ce groupe, on épargne davantage les femmes, et les sportifs plutôt que les personnes en surpoids. »"""
    titre(d, 70, 130, "EPARGNE", 10, B3)
    titre(d, 200, 130, "SACRIFIE", 10, ROUGE)
    d.line([(135, 150), (135, 430)], fill=B1)
    if t >= T["femmes"]:
        enceinte(img, 50, 260, 50) if False else P.personnage(img, (50, 260), 50, tenue="robe")
        P.personnage(img, (210, 260), 50, tenue="pull", miroir=True)
        over(P.cadre_texte, (30, 272), "FEMME", 8, B4, B2)
        over(P.cadre_texte, (186, 272), "HOMME", 8, GRIS, B1)
    if t >= T["sportifs"]:
        sportif(img, 60, 400, 50, t=t)
        over(P.cadre_texte, (30, 412), "SPORTIF", 8, B4, B2)
    if t >= T["surpoids"]:
        surpoids(img, 210, 400, 50, miroir=True)
        over(P.cadre_texte, (176, 412), "SURPOIDS", 8, GRIS, B1)


def s_paradoxe(img, d, t):
    """« La majorité veut des voitures qui sacrifient leur passager… mais pour les autres. »"""
    d.rectangle((0, 300, 270, 304), fill=B1)
    if t < T["propre"] - 0.1:
        u = lisse((t - T["sacrifient"]) / 0.9)
        x = 20 + 125 * u                                          # la voiture des autres va dans le mur, les piétons vivent
        d.rectangle((222, 210, 236, 300), fill=GRIS_F, outline=P.CONTOUR)
        for y in range(214, 300, 8):
            d.line([(222, y), (236, y)], fill=P.CONTOUR)
        voiture_profil(d, x, 300, B2, t)
        for k in range(3):
            P.personnage(img, (160 + 14 * k, 380), 34, tenue="clair")
        d.rectangle((0, 380, 270, 383), fill=B1)
        if t >= T["sacrifient"] + 0.9:                            # le choc contre le mur
            k = t - T["sacrifient"] - 0.9
            for j in range(12):
                a = j * 0.52
                r = 30 * min(1.0, k * 3)
                if k < 1.2:
                    d.rectangle((222 + r * math.cos(a), 270 + r * math.sin(a) * 0.6,
                                 224 + r * math.cos(a), 272 + r * math.sin(a) * 0.6), fill=B4 if j % 2 else ROUGE)
            over(P.cadre_texte, (150, 400), "PIETONS SAUVES", 8, B4, B2)
        if t >= T["autres"]:
            over(P.cadre_texte, (20, 140), "LA VOITURE DES AUTRES :", 8, B4, B2)
            over(P.cadre_texte, (20, 160), "SACRIFIE LE PASSAGER", 8, BLANC, ROUGE)
    else:
        voiture_profil(d, 120, 300, B3, t, roule=False)
        P.personnage(img, (80, 302), 60, tenue="pull", mains=(116, 268))
        over(P.cadre_texte, (20, 140), "MA VOITURE :", 8, B4, B2)
        if t >= T["protege"]:
            over(P.cadre_texte, (20, 160), "PROTEGE-MOI !", 8, BLANC, ROUGE)
            over(bulle, 30, 200, "MOI D'ABORD", BLANC, B2, (80, 230))


def s_mercedes(img, d, t):
    """« La même année, un responsable de Mercedes le dit tout haut… »"""
    d.rectangle((0, 330, 270, 334), fill=B1)
    for k in range(6):                                            # un salon automobile : spots
        x = 20 + k * 46
        d.polygon([(x, 100), (x - 18, 330), (x + 18, 330)], fill=(10, 22, 50))
    voiture_profil(d, 96, 330, GRIS, t, roule=False)
    P.personnage(img, (60, 332), 66, tenue="costume", mains=(80, 280) if t >= T["sauvez"] else None)
    if t >= T["sauvez"]:
        over(P.cadre_texte, (40, 150), "\"SAUVEZ CELUI QUI", 8, BLANC, B2)
        over(P.cadre_texte, (40, 168), "EST DANS LA VOITURE\"", 8, BLANC, B2)
        over(P.cadre_texte, (40, 380), "MERCEDES, 2016", 8, B3, B1)


def s_allemagne(img, d, t):
    """« En 2017, l'Allemagne tranche : interdit de choisir selon l'âge ou le sexe. »"""
    s_classement(img, d, t, interdit=True)
    if t >= T["age"]:
        over(tampon, "INTERDIT : AGE / SEXE", t, T["age"], 135, 250, -10, 14)
    if t >= T["allemagne"]:
        over(P.cadre_texte, (24, 136), "ALLEMAGNE", 8, BLANC, ROUGE)


def s_fin(img, d, t):
    """« Alors, votre voiture : elle sauve qui ? Vous… ou eux ? »"""
    route(d, t)
    enceinte(img, 80, PASSAGE + 6, 50)
    for x in (162, 184, 206):
        vieux(img, x, PASSAGE + 6, 46, miroir=True)
    voiture_dessus(img, 135, PASSAGE + 62, 0, alerte=True, t=t)
    if t >= T["vous3"]:
        sel = int(t * 2.5) % 2 if t < T["eux"] + 0.8 else 1
        for k, (nom, x) in enumerate((("VOUS", 50), ("EUX", 170))):
            c = ROUGE if sel == k else B1
            over(P.cadre_texte, (x, 420), f" {nom} ", 8, BLANC, c, ROUGE_F if sel == k else NOIR)


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
            return 1.6, 135, PASSAGE + 40
        if T["personne"] - 0.1 <= s < T["choisir"]:                 # gros plan sur l'habitacle vide
            return 2.6, 135, 380
        if s >= T["choisir"]:
            u = lisse((s - T["choisir"]) / 1.5)
            return 1.6 + 0.3 * u, 135, PASSAGE + 40 - 10 * u
        return 1.6, 135, PASSAGE + 40
    if scene is s_fin:
        return 1.6, 135, PASSAGE + 40
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
