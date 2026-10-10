"""Épisode 32 — « Paris aurait dû s'effondrer » — style @alfred.explique, en bleu, 100 % code.

    python -m films.episodes.ep32_paris_vide.alfred_ep32 output/ep32.mp4 [t0 t1]
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
SOL = 300                                                        # la rue (en vrais pixels, toile 270 × 480)
RNG = np.random.default_rng(32)


def lisse(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def draw(img):
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    return d


# ------------------------------------------------------------------------------------------------ décor de Paris
def immeuble(d, x, w, etages=6, sol=SOL, t=0.0, graine=0, alerte=False):
    """Un immeuble haussmannien : pierre, fenêtres, balcons filants, toit en zinc et lucarnes."""
    he = 15
    haut = sol - etages * he
    pierre = ROUGE_F if alerte else B1
    d.rectangle((x, haut, x + w, sol), fill=pierre)
    d.rectangle((x, haut, x + 1, sol), fill=B2 if not alerte else ROUGE)
    d.polygon([(x - 2, haut), (x + 5, haut - 16), (x + w - 5, haut - 16), (x + w + 2, haut)], fill=GRIS_F)   # le toit
    for k in range(x + 8, x + w - 6, 14):                         # les lucarnes
        d.rectangle((k, haut - 12, k + 5, haut - 4), fill=B0)
        d.point((k + 2, haut - 13), fill=GRIS)
    d.rectangle((x + w - 10, haut - 22, x + w - 6, haut - 14), fill=GRIS_F)   # la cheminée
    rng = np.random.default_rng(graine)
    for e in range(etages):
        y = haut + e * he + 3
        for k in range(x + 4, x + w - 5, 9):
            allume = rng.uniform() < 0.35 and (int(t * 0.5 + rng.uniform() * 9) % 7)
            d.rectangle((k, y, k + 4, y + 8), fill=B3 if allume else B0)
            if allume:
                d.point((k + 1, y + 1), fill=B4)
        if e in (1, 4):                                            # les balcons filants
            d.line([(x + 2, y + 9), (x + w - 2, y + 9)], fill=B3 if not alerte else ROUGE)
            for k in range(x + 3, x + w - 2, 3):
                d.point((k, y + 8), fill=B2)
    d.rectangle((x + w // 2 - 4, sol - 11, x + w // 2 + 4, sol), fill=B0)   # la porte cochère


def reverbere(d, img, x, t, sol=SOL):
    d.line([(x, sol), (x, sol - 34)], fill=GRIS_F, width=2)
    d.rectangle((x - 3, sol - 40, x + 3, sol - 34), fill=B4 if int(t * 7 + x) % 23 else B3)
    d.line([(x - 4, sol - 41), (x + 4, sol - 41)], fill=GRIS_F)


def chaussee(d, x0, x1, sol=SOL):
    d.rectangle((x0, sol, x1, sol + 2), fill=B2)
    for y in range(sol + 3, sol + 12, 3):
        for x in range(x0 + (y % 6), x1, 6):
            d.rectangle((x, y, x + 3, y + 1), fill=B1)


def fiacre(d, x, y, t, ang=0.0):
    """Un fiacre et son cheval (vus de profil)."""
    roue = lambda cx, cy, r: (d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=GRIS, width=1),
                              d.line([(cx - r * math.cos(t * 6), cy - r * math.sin(t * 6)),
                                      (cx + r * math.cos(t * 6), cy + r * math.sin(t * 6))], fill=GRIS_F))
    d.rectangle((x, y - 22, x + 26, y - 6), fill=B0, outline=B2)
    d.rectangle((x + 4, y - 19, x + 12, y - 12), fill=B3)
    d.line([(x - 2, y - 23), (x + 28, y - 23)], fill=B2)
    roue(x + 5, y - 5, 5)
    roue(x + 21, y - 5, 5)
    cx = x + 40                                                    # le cheval
    d.ellipse((cx - 9, y - 22, cx + 9, y - 12), fill=GRIS)
    d.polygon([(cx + 6, y - 20), (cx + 13, y - 30), (cx + 17, y - 28), (cx + 11, y - 17)], fill=GRIS)
    d.point((cx + 14, y - 28), fill=NOIR)
    for k, dx in enumerate((-6, -3, 4, 7)):
        ph = math.sin(t * 9 + k * 1.6) * 2
        d.line([(cx + dx, y - 13), (cx + dx + ph, y - 1)], fill=GRIS_F if k % 2 else GRIS, width=2)
    d.line([(x + 26, y - 14), (cx - 8, y - 16)], fill=GRIS_F)


def rue(img, d, t, sol=SOL, alerte_idx=None):
    """La rue parisienne de nuit : 5 immeubles, réverbères, chaussée."""
    xs = [(-4, 52), (50, 50), (102, 56), (160, 50), (212, 62)]
    for i, (x, w) in enumerate(xs):
        immeuble(d, x, w, 6 + (i % 2), sol, t, i, alerte=(i == alerte_idx))
    chaussee(d, 0, 270, sol)
    for x in (30, 130, 230):
        reverbere(d, img, x, t, sol)


def coupe_sol(d, y0, y1, t=0.0, galeries=True, piliers_faibles=False, consolide=0.0):
    """Le sous-sol en coupe : couches de calcaire, galeries noires et piliers."""
    for y in range(y0, y1):
        c = B0 if ((y - y0) // 9) % 2 else (10, 30, 66)
        d.line([(0, y), (270, y)], fill=c)
    for k in range(60):                                            # cailloux
        x, y = (k * 53) % 270, y0 + (k * 37) % max(1, (y1 - y0))
        d.point((x, y), fill=B1)
    if not galeries:
        return
    for gx, gy, gw in ((10, y0 + 30, 110), (140, y0 + 22, 120), (40, y0 + 78, 180)):
        d.rectangle((gx, gy, gx + gw, gy + 26), fill=NOIR)
        d.line([(gx, gy), (gx + gw, gy)], fill=B2)
        for px in range(gx + 14, gx + gw - 6, 28):                 # piliers
            if piliers_faibles:
                d.polygon([(px, gy), (px + 4, gy), (px + 2, gy + 13), (px + 5, gy + 26), (px - 1, gy + 26), (px + 1, gy + 13)],
                          fill=GRIS_F)
            else:
                d.rectangle((px, gy, px + 5, gy + 26), fill=GRIS_F)
            if consolide > 0:
                h = int(26 * min(1, consolide * 1.5))
                d.rectangle((px - 2, gy + 26 - h, px + 7, gy + 26), fill=GRIS)
                for yy in range(gy + 26 - h, gy + 26, 4):
                    d.line([(px - 2, yy), (px + 7, yy)], fill=GRIS_F)


def plaque(d, x, y, l1, l2=None, w=None, col=B1):
    """Une plaque de rue parisienne : émail bleu, liseré blanc, texte blanc."""
    f = P.police(8)
    w = w or int(max(d.textlength(l1, font=f), d.textlength(l2 or "", font=f)) + 14)
    h = 26 if l2 else 16
    d.rounded_rectangle((x, y, x + w, y + h), 3, fill=col, outline=BLANC)
    d.rectangle((x + 2, y + 2, x + w - 2, y + h - 2), outline=B3)
    d.text((x + (w - d.textlength(l1, font=f)) / 2, y + 4), l1, font=f, fill=BLANC)
    if l2:
        d.text((x + (w - d.textlength(l2, font=f)) / 2, y + 14), l2, font=f, fill=BLANC)
    return w


def crane(d, x, y, col=B4):
    d.ellipse((x - 3, y - 3, x + 3, y + 2), fill=col)
    d.rectangle((x - 2, y + 2, x + 2, y + 4), fill=col)
    d.point((x - 1, y), fill=NOIR)
    d.point((x + 1, y), fill=NOIR)


def poussiere(d, x, y, t, t0, n=24, r=40, col=B3):
    u = (t - t0)
    if u < 0 or u > 1.6:
        return
    rng = np.random.default_rng(int(t0 * 100))
    for k in range(n):
        a = rng.uniform(math.pi, 2 * math.pi)
        v = rng.uniform(0.3, 1)
        px = x + math.cos(a) * r * v * min(1, u * 2)
        py = y + math.sin(a) * r * 0.5 * v * min(1, u * 2) + 10 * u * u
        if rng.uniform() > u / 1.6:
            d.rectangle((px, py, px + 1, py + 1), fill=col)


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
    d.rectangle((x - w / 2 - 4, y - 2, x + w / 2 + 4, y + taille + 4), fill=NOIR)       # lisible sur le décor
    d.text((x - w / 2, y), txt, font=f, fill=col)


def tampon(img, txt, t, t0, cx, cy, ang=-8, taille=14):
    if t < t0:
        return
    k = 1 + 1.2 * max(0.0, 1 - (t - t0) / 0.12)
    f = P.police(taille, pixel=False)
    tmp = Image.new("RGBA", (220, 60), (0, 0, 0, 0))
    dd = ImageDraw.Draw(tmp)
    dd.fontmode = "1"
    w = dd.textlength(txt, font=f)
    dd.rectangle((110 - w / 2 - 6, 30 - taille / 2 - 5, 110 + w / 2 + 6, 30 + taille / 2 + 6), outline=ROUGE, width=2)
    dd.text((110 - w / 2, 30 - taille / 2 - 1), txt, font=f, fill=ROUGE)
    tmp = tmp.rotate(ang, resample=Image.NEAREST).resize((int(220 * k), int(60 * k)), Image.NEAREST)
    img.paste(tmp, (int(cx - 110 * k), int(cy - 30 * k)), tmp)


OVER = []                                                        # ce qui se dessine par-dessus la caméra (textes, chiffres)


def over(fn, *args):
    OVER.append((fn, args))


# ------------------------------------------------------------------------------------------------ les scènes
def s_rue(img, d, t, s):
    """0 → « vous pensez » : la rue, l'effondrement (s = temps de l'histoire), le rembobinage, l'immeuble sur cinq."""
    to = T["souvre"]
    effond = max(0.0, s - to)
    vide_bas = SOL + 190
    if effond > 0:                                                 # le trou : le sous-sol apparaît sous la chaussée
        coupe_sol(d, SOL + 12, vide_bas, s, piliers_faibles=True)
        larg = min(1.0, effond / 0.8)
        x0, x1 = 135 - 70 * larg, 135 + 70 * larg
        d.rectangle((x0, SOL, x1, SOL + 120 * larg), fill=NOIR)
    rue(img, d, t, alerte_idx=None)
    if effond > 0:
        larg = min(1.0, effond / 0.8)
        x0, x1 = 135 - 70 * larg, 135 + 70 * larg
        d.rectangle((x0, SOL, x1, SOL + 14), fill=NOIR)
        for k in range(10):                                        # les pavés qui tombent
            u = effond - k * 0.05
            if u > 0:
                px = x0 + (x1 - x0) * ((k * 0.37) % 1)
                py = SOL + 4 + 90 * u * u
                if py < SOL + 120:
                    d.rectangle((px, py, px + 4, py + 3), fill=B2 if k % 2 else B1)
        poussiere(d, 135, SOL, s, to, 40, 70)
    fx = 20 + 40 * s if s < to else 20 + 40 * to
    fy = SOL + 2 + (0 if effond <= 0 else min(160, 140 * (effond - 0.2) ** 2 if effond > 0.2 else 0))
    if fy < SOL + 150:
        tmp = Image.new("RGBA", (80, 50), (0, 0, 0, 0))
        fiacre(draw(tmp), 10, 46, t)
        if effond > 0.2:
            tmp = tmp.rotate(-min(70, effond * 60), resample=Image.NEAREST)
        img.paste(tmp, (int(fx - 10), int(fy - 46)), tmp)
    for k, (x0, v, tn) in enumerate(((210, -14, "gris"), (250, -10, "clair"))):   # des passants
        x = x0 + v * s
        if effond > 0.4 and 60 < x < 210:
            continue
        P.personnage(img, (x, SOL + 1), 30, marche=s * 7 + k, tenue=tn, miroir=True)
    if T["immeuble"] - 0.2 <= t < T["vous"] - 0.1:                 # un immeuble sur cinq, au-dessus du vide
        u = lisse((t - T["immeuble"] + 0.2) / 0.5)
        d.rectangle((96, SOL + 30, 170, SOL + 58), fill=NOIR, outline=ROUGE if int(t * 4) % 2 else ROUGE_F)
        immeuble(d, 102, 56, 6, SOL, t, 2, alerte=True)
        over(P.cadre_texte, (108, SOL + 66), "VIDE", 8, ROUGE, ROUGE)
        over(compteur, 135, 150, 1, " / 5", 22, ROUGE)


def s_dessous(img, d, t):
    """« Vous pensez… » → « Pendant des siècles » : la caméra descend sous la rue ; 280 km."""
    rue(img, d, t)
    coupe_sol(d, SOL + 12, 470, t)
    tk = T["deux"]
    if t >= tk:
        v = 280 * lisse((t - tk) / 1.2)
        over(compteur, 135, 140, v, " KM", 26)
        over(P.cadre_texte, (100, 178), "DE GALERIES", 8, B4, B2)
    if t < T["sauf"]:
        over(P.cadre_texte, (12, SOL - 120), "DU SOLIDE ?", 8, B4, B2)


def s_carriers(img, d, t):
    """Les carriers sortent la pierre, qui devient la ville ; il reste des galeries sans plan."""
    coupe_sol(d, SOL + 12, 470, t, galeries=True, piliers_faibles=t >= T["piliers1"] - 0.2)
    chaussee(d, 0, 270)
    for i, x in enumerate((40, 120)):                              # deux carriers à la pioche
        ph = (t * 1.8 + i * 0.5) % 1.0
        coup = math.sin(ph * math.pi * 2)
        main = (x + 12 + 4 * coup, SOL + 52 - 8 * coup)
        P.personnage(img, (x, SOL + 68), 34, tronc=10 + 6 * coup, mains=main, tenue="gris" if i else "pull")
        d.line([main, (main[0] + 9, main[1] + 4 - 8 * coup)], fill=GRIS, width=2)
    d.rectangle((200, SOL - 2, 210, SOL + 68), fill=NOIR, outline=B2)     # le puits, et les blocs qui remontent
    for k in range(4):
        y = SOL + 60 - ((t * 30 + k * 18) % 70)
        d.rectangle((202, y, 208, y + 5), fill=B4)
    n = int(min(5, max(0, (t - T["monuments"]) * 2.2))) if t >= T["monuments"] else 0
    if t >= T["monuments"]:                                        # la ville qui sort du sol
        _notre_dame(d, 50, SOL, lisse((t - T["monuments"]) / 0.8))
    if t >= T["immeubles"]:
        for i in range(min(3, int((t - T["immeubles"]) * 3) + 1)):
            immeuble(d, 130 + i * 44, 40, 4 + i, SOL, t, 10 + i)
    if t >= T["sans"]:
        f = P.police(30, pixel=False)
        if int(t * 4) % 2 or t > T["sans"] + 1:
            d.text((120, SOL + 100), "?", font=f, fill=ROUGE)
    if t >= T["resultat"]:
        over(P.cadre_texte, (70, 160), "CARRIERES OUBLIEES", 8, B4, B2)


def _notre_dame(d, x, sol, u):
    """Une silhouette de cathédrale (deux tours, rosace, portails), qui monte du sol."""
    h = int(120 * u)
    if h <= 0:
        return
    top = sol - h
    d.rectangle((x - 30, top, x - 8, sol), fill=B1)
    d.rectangle((x + 8, top, x + 30, sol), fill=B1)
    d.rectangle((x - 8, top + 18, x + 8, sol), fill=B1)
    d.line([(x - 30, top), (x - 30, sol)], fill=B2)
    if u > 0.8:
        d.ellipse((x - 7, top + 26, x + 7, top + 40), outline=B3)
        for k in (-20, 0, 20):
            d.rectangle((x + k - 4, sol - 16, x + k + 4, sol), fill=B0)
        for k in (-26, -14, 12, 24):
            d.rectangle((x + k, top + 6, x + k + 3, top + 16), fill=B0)


def s_gruyere(img, d, t):
    """« Mais attendez » : la carte de Paris, des trous qui s'ouvrent partout."""
    cx, cy = 135, 290
    d.ellipse((cx - 110, cy - 80, cx + 110, cy + 80), outline=B2, width=2)        # le Paris d'avant (enceinte)
    pts = [(cx - 120 + k * 12, cy - 4 + 14 * math.sin(k * 0.55)) for k in range(21)]
    d.line(pts, fill=B3, width=4)                                  # la Seine
    for k in range(-90, 100, 22):
        d.line([(cx + k, cy - 70), (cx + k + 10, cy + 70)], fill=B0)
        d.line([(cx - 100, cy + k * 0.7), (cx + 100, cy + k * 0.7 + 6)], fill=B0)
    t0 = T["dautres"]
    rng = np.random.default_rng(7)
    for k in range(26):
        x, y = cx + rng.uniform(-90, 90), cy + rng.uniform(-60, 65)
        tk = t0 + k * 0.14
        if t >= tk:
            r = 2 + 3 * lisse((t - tk) / 0.3)
            d.ellipse((x - r, y - r, x + r, y + r), fill=NOIR, outline=ROUGE if int(t * 5 + k) % 2 else ROUGE_F)
    f = P.police(18, pixel=False)
    if t >= T["gruyere"]:
        w = d.textlength("GRUYÈRE", font=f)
        d.text((cx - w / 2, cy + 100), "GRUYÈRE", font=f, fill=BLANC)
    if t >= T["trous"]:
        over(P.cadre_texte, (70, cy - 120), "OU SONT LES TROUS ?", 8, ROUGE, ROUGE)
    over(tampon, "1774 : RUE D'ENFER", t, T["mais"], 135, 160, -6, 12)


def s_guillaumot(img, d, t):
    """1777 : Guillaumot et sa lanterne ; piliers, murs, remblais ; les noms de rues gravés."""
    coupe_sol(d, 140, 470, t, consolide=lisse((t - T["piliers"] + 0.1) / 1.2) if t >= T["piliers"] - 0.1 else 0)
    d.rectangle((0, 250, 270, 330), fill=NOIR)                     # une grande galerie, au premier plan
    d.line([(0, 250), (270, 250)], fill=B2)
    d.rectangle((0, 330, 270, 334), fill=B1)
    x = 40 + 30 * lisse((t - T["louis"]) / 3.0)
    lan = (x + 18, 288)
    halo = P.halo(img, lan[0], lan[1], 46 + 3 * math.sin(t * 9), B1, 0.75)          # la lumière de la lanterne
    img.paste(halo.crop((0, 240, 270, 334)), (0, 240))
    P.personnage(img, (x, 330), 78, mains=lan, tenue="clair", marche=t * 5 if t < T["louis"] + 3 else None)
    d.rectangle((lan[0] - 3, lan[1], lan[0] + 3, lan[1] + 7), fill=B4)
    d.line([(lan[0], lan[1] - 3), (lan[0], lan[1])], fill=GRIS)
    if t >= T["piliers"]:                                          # les piliers montés pierre par pierre
        for i, px in enumerate((150, 200, 245)):
            h = int(80 * lisse((t - T["piliers"] - 0.15 * i) / 0.6))
            for y in range(330 - h, 330, 6):
                d.rectangle((px, y, px + 14, y + 5), fill=GRIS)
                d.line([(px, y + 5), (px + 14, y + 5)], fill=GRIS_F)
    if t >= T["murs"]:
        w = int(60 * lisse((t - T["murs"]) / 0.6))
        for y in range(256, 330, 7):
            for k in range(0, w, 12):
                d.rectangle((95 + k + (y // 7 % 2) * 6, y, 95 + k + (y // 7 % 2) * 6 + 10, y + 5), fill=B1)
    if t >= T["graver"]:                                           # la plaque gravée, lettre par lettre
        txt = "RUE D'ENFER"
        k = int((t - T["graver"]) * 9)
        d.rectangle((150, 214, 250, 236), fill=GRIS_F, outline=GRIS)
        d.text((158, 220), txt[:k], font=P.police(8), fill=BLANC)
    if t >= T["guillaumot"]:
        over(P.cadre_texte, (12, 180), "C.-A. GUILLAUMOT", 8, B4, B2)


def s_ossuaire(img, d, t):
    """Les cimetières débordent ; 1786 : les ossements descendent dans les carrières ; 6 millions."""
    if t < T["dixsept2"] - 0.1:                                    # le cimetière des Innocents
        d.rectangle((0, SOL, 270, SOL + 12), fill=B0)
        for k in range(16):
            x = 10 + k * 16
            h = 14 + (k * 7) % 12
            d.rectangle((x, SOL - h, x + 8, SOL), fill=B1)
            d.rectangle((x + 3, SOL - h - 8, x + 5, SOL - h), fill=GRIS)
            d.rectangle((x, SOL - h - 5, x + 8, SOL - h - 3), fill=GRIS)
        for k in range(30):                                        # les ossements qui débordent
            u = lisse((t - T["debordent"]) / 1.0) if t >= T["debordent"] else 0
            if (k / 30) < u:
                crane(d, 12 + (k * 37) % 250, SOL - 2 - (k % 3) * 5, B4)
        over(P.cadre_texte, (90, 170), "LES INNOCENTS", 8, B4, B2)
        if t >= T["insalubre"]:
            over(tampon, "INSALUBRE", t, T["insalubre"], 135, 220, -7, 12)
        return
    coupe_sol(d, 200, 470, t, galeries=False)
    d.rectangle((120, 150, 150, 330), fill=NOIR, outline=B2)      # le puits
    for k in range(5):                                             # les charrettes qui descendent
        x = 20 + ((t * 30 + k * 60) % 110)
        y = 196
        d.rectangle((x, y - 8, x + 16, y), fill=B1, outline=B2)
        d.ellipse((x + 2, y - 2, x + 6, y + 2), fill=GRIS)
        d.ellipse((x + 10, y - 2, x + 14, y + 2), fill=GRIS)
        crane(d, x + 8, y - 10)
    d.line([(0, 200), (120, 200)], fill=B2)
    for k in range(6):                                             # les os qui tombent dans le puits
        y = 170 + ((t * 120 + k * 30) % 160)
        crane(d, 135, y)
    if t >= T["carrieres3"]:                                       # le mur d'ossements, rangée par rangée
        n = int(min(1.0, (t - T["carrieres3"]) / 3.0) * 14 * 6)
        for i in range(n):
            x, y = 165 + (i % 14) * 7, 400 - (i // 14) * 9
            crane(d, x, y, B4 if (i // 14) % 2 else B3)
            d.line([(x - 4, y + 5), (x + 4, y + 5)], fill=GRIS)
    if t >= T["six"]:
        v = 6_000_000 * lisse((t - T["six"]) / 1.2)
        over(compteur, 135, 132, v, "", 20, BLANC)
    if t >= T["catacombes1"]:
        over(P.cadre_texte, (96, 150), "CATACOMBES", 8, ROUGE, ROUGE)


def s_denfert(img, d, t):
    """L'entrée des catacombes, place Denfert-Rochereau… l'ancienne rue d'Enfer."""
    rue(img, d, t)
    d.rectangle((100, SOL - 40, 170, SOL), fill=B2, outline=B3)   # le pavillon d'entrée
    d.polygon([(96, SOL - 40), (135, SOL - 58), (174, SOL - 40)], fill=GRIS_F)
    d.rectangle((126, SOL - 22, 144, SOL), fill=NOIR)
    w = plaque(d, 40, 150, "PLACE", "DENFERT-ROCHEREAU")
    if t >= T["lancienne"]:
        u = lisse((t - T["lancienne"]) / 0.6)
        plaque(d, 40, int(150 + 40 * u), "RUE D'ENFER", None, w, ROUGE_F)
        over(tampon, "ICI", t, T["rue3"], 200, 210, -10, 14)


def s_clamart(img, d, t):
    """1961, Clamart : un quartier s'enfonce."""
    te = T["seffondre"]
    enf = 24 * lisse((t - te) / 1.0) if t >= te else 0
    coupe_sol(d, SOL + 12, 470, t, galeries=False)
    d.rectangle((60, SOL + 12, 210, SOL + 60), fill=NOIR)          # l'ancienne carrière de craie
    for k in range(70, 200, 22):
        d.rectangle((k, SOL + 12, k + 6, SOL + 60 - (enf > 0) * 30), fill=GRIS_F)
    chaussee(d, 0, 60)
    chaussee(d, 210, 270)
    for i, x in enumerate(range(64, 206, 28)):                     # les pavillons
        y = SOL + enf * (1 if 60 < x < 200 else 0) + (i % 2) * enf * 0.2
        d.rectangle((x, y - 22, x + 22, y), fill=B1, outline=B2)
        d.polygon([(x - 2, y - 22), (x + 11, y - 32), (x + 24, y - 22)], fill=GRIS_F)
        d.rectangle((x + 4, y - 16, x + 9, y - 10), fill=B3 if not enf else B0)
    if t >= te:
        poussiere(d, 135, SOL, t, te, 50, 80)
    over(P.cadre_texte, (100, 170), "CLAMART", 8, B4, B2)
    if t >= T["vingt"]:
        f = P.police(30, pixel=False)
        d.text((112, 200), "21", font=f, fill=ROUGE)
        over(P.cadre_texte, (100, 240), "MORTS", 8, ROUGE, ROUGE)


def s_aujourdhui(img, d, t):
    """Aujourd'hui : l'inspecteur dans les galeries ; une rue, un immeuble sur cinq."""
    if t < T["parce"] - 0.1:
        coupe_sol(d, 140, 470, t, consolide=1.0)
        d.rectangle((0, 250, 270, 330), fill=NOIR)
        d.line([(0, 250), (270, 250)], fill=B2)
        x = 20 + 50 * (t - T["aujourdhui3"])
        P.personnage(img, (x, 330), 56, marche=t * 6, tenue="clair")
        lamp = (x + 6, 284)
        d.polygon([lamp, (lamp[0] + 70, lamp[1] - 18), (lamp[0] + 70, lamp[1] + 18)], fill=(10, 28, 62))
        d.rectangle((lamp[0] - 1, lamp[1] - 1, lamp[0] + 1, lamp[1] + 1), fill=B4)
        if t >= T["deux3"]:
            over(compteur, 135, 140, 280 * lisse((t - T["deux3"]) / 1.0), " KM", 26)
        return
    k = int((t - T["immeuble3"]) * 3) % 5 if t >= T["immeuble3"] else -1
    rue(img, d, t, alerte_idx=2 if t >= T["immeuble3"] else None)
    coupe_sol(d, SOL + 12, 470, t)
    if t >= T["immeuble3"]:
        over(compteur, 135, 140, 1, " / 5", 26, ROUGE)


def s_fin(img, d, t):
    rue(img, d, t)
    P.personnage(img, (60 + 20 * (t - T["alors"]), SOL + 1), 34, marche=t * 6, tenue="pull")


def ecrans():
    return [(0.0, "rue"), (T["vous"] - 0.1, s_dessous), (T["pendant"] - 0.1, s_carriers), (T["mais"] - 0.1, s_gruyere),
            (T["louis"] - 0.1, s_guillaumot), (T["et3"] - 0.1, s_ossuaire), (T["et4"] - 0.1, s_denfert),
            (T["le7"] - 0.1, s_clamart), (T["aujourdhui3"] - 0.1, s_aujourdhui), (T["alors"] - 0.1, s_fin)]


def histoire(t):
    """L'accroche : la rue avance, s'effondre, puis rembobine jusqu'au début."""
    tr0, tr1 = T["trou"] + 0.55, T["trou"] + 1.45
    if t < tr0:
        return t, False
    if t < tr1:
        u = (t - tr0) / (tr1 - tr0)
        return tr0 * (1 - u) ** 1.4, True
    return 0.0 + (t - tr1) * 0.6, False


DATES = [("dixsept", "rue_fin", "1774"), ("louis", "et3", "1777"), ("dixsept2", "et4", "1786"), ("dixneuf", "aujourdhui3", "1961")]


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
    if scene == "rue":
        s, rembobine = histoire(t)
        s_rue(img, d, t, s)
    else:
        scene(img, d, t)
    z, cx, cy = 1.25, 135, 290                                      # la caméra : le sujet remplit l'écran
    if scene == "rue" and t < T["souvre"] + 1.2 and not rembobine:
        u = lisse((t - T["souvre"]) / 0.6)
        z, cx, cy = 1.25 + 0.25 * u, 135, 290 + 20 * u
    if scene is s_dessous:
        u = lisse((t - T["vous"]) / 1.6)
        cy = 290 + 70 * u
    w, h = P.LW / z, P.LH / z
    x0, y0 = min(max(0, cx - w / 2), P.LW - w), min(max(0, cy - h / 2), P.LH - h)
    img = img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((P.LW, P.LH), Image.NEAREST)
    dx = dy = 0
    for tc, amp in ((T["souvre"], 7), (T["mais"], 4), (T["seffondre"], 6)):
        if t >= tc:
            kk = math.exp(-6 * (t - tc)) * math.sin(60 * (t - tc))
            dx += int(amp * kk)
            dy += int(amp * 0.7 * kk)
    if dx or dy:
        img = Image.fromarray(np.roll(np.roll(np.asarray(img), dx, 1), dy, 0))
    d = draw(img)
    vide = 0.15 if t < T["souvre"] else (0.95 if t < T["vous"] else 0.7)            # la jauge VIDE
    if t >= T["louis"]:
        vide = 0.7 - 0.4 * lisse((t - T["piliers"]) / 2.0)
    if t >= T["le7"]:
        vide = 0.85
    if t >= T["aujourdhui3"]:
        vide = 0.5
    if scene == "rue" and rembobine:
        vide = 0.15
    if t < T["alors"]:
        P.jauge(d, t, vide, etiquette="VIDE", valeur="", alerte=vide > 0.8)
    if t < 2.4:                                                    # le titre
        f = P.police(16, pixel=False)
        d.text((10, 92), "PARIS", font=f, fill=BLANC)
    for fn, args in OVER:
        fn(img, *args) if fn is tampon else fn(d, *args)
    for a_, b_, txt in DATES:
        if T[a_] - 0.1 <= t < T[b_] - 0.1:
            date(d, txt, t, T[a_] - 0.1)
    if scene == "rue":
        if T["rue"] - 0.05 <= t < T["vous"]:
            plaque(d, 150, 140 if t < T["immeuble"] else 120, "RUE D'ENFER")
    a = np.asarray(P.agrandir(img))
    if rembobine:
        a = P.vhs(a, t)
        im = Image.fromarray(a)
        dd = ImageDraw.Draw(im)
        for k2 in range(2):
            x = 900 + 46 * k2
            dd.polygon([(x, 120), (x + 40, 96), (x + 40, 144)], fill=BLANC)
        a = np.asarray(im)
    if t < 0.1:
        a = (a.astype(np.float32) * (t / 0.1) + 255 * (1 - t / 0.1)).astype(np.uint8)
    return a


# ------------------------------------------------------------------------------------------------ son
def sons():
    f = J.fichier
    ev = [(0.0, f("boum_cine", 0.4, 2.0), "accent", 0.0)]
    to = T["souvre"]
    ev += [(to, f("boum_cine", 0.6, 3.0), "accent", 0.0), (to, f("boum_grave", 0.5), "accent", 0.0),
           (to + 0.1, Z.craquement(0.4), "effet", -0.3), (to + 0.2, f("souffle_sombre", 0.3), "ambiance", 0.2),
           (T["trou"] + 0.55, f("rembobine", 0.4, 1.0), "effet", 0.0), (T["trou"] + 0.55, f("glitch", 0.3), "effet", 0.0),
           (T["immeuble"], f("erreur", 0.3), "effet", 0.0), (T["vide"], f("impact", 0.3), "accent", 0.0)]
    ev += [(T["deux"] + 0.06 * i, J.tic_compteur(i), "interface", 0.0) for i in range(20)]
    ev += [(T["deux"] + 1.2, J.piece(), "effet", 0.0)]
    ev += [(T["pendant"] + 0.55 * i + 0.25, f("impact", 0.12), "effet", -0.4 if i % 2 else 0.2)
           for i in range(int((T["mais"] - T["pendant"]) / 0.55))]
    ev += [(T["sans"], f("question", 0.3), "effet", 0.0), (T["piliers1"], Z.craquement(0.3), "effet", 0.0),
           (T["mais"], f("arret", 0.3), "effet", 0.0), (T["mais"], f("impact", 0.3), "accent", 0.0)]
    ev += [(T["dautres"] + k * 0.14, J.trace(500 + 40 * (k % 6)), "interface", ((k * 37) % 10) / 10 - 0.5) for k in range(26)]
    ev += [(T["gruyere"], f("erreur", 0.25), "effet", 0.0), (T["louis"], J.selection(), "effet", 0.0),
           (T["louis"], f("mystere", 0.18, 3.0), "ambiance", 0.0)]
    ev += [(T["piliers"] + 0.15 * i, f("impact", 0.2), "effet", -0.3 + 0.3 * i) for i in range(3)]
    ev += [(T["murs"], f("porte_ferme", 0.2, 0.6), "effet", 0.0)]
    ev += [(T["graver"] + i / 9, J.lettre(0.05), "interface", 0.3) for i in range(11)]
    ev += [(T["debordent"], f("roulement", 0.12, 1.5), "ambiance", 0.0), (T["insalubre"], f("echec", 0.3), "effet", 0.0),
           (T["dixsept2"], f("boum_grave", 0.35), "accent", 0.0)]
    ev += [(T["six"] + 0.05 * i, J.tic_compteur(i), "interface", 0.0) for i in range(24)]
    ev += [(T["six"] + 1.2, J.piece(), "effet", 0.0), (T["catacombes1"], f("mystere", 0.2, 3.0), "ambiance", 0.0),
           (T["lancienne"], f("bascule", 0.3), "effet", 0.0), (T["rue3"], f("confirmation", 0.3), "effet", 0.0),
           (T["seffondre"], f("boum_cine", 0.55, 3.0), "accent", 0.0), (T["seffondre"], Z.craquement(0.4), "effet", 0.0),
           (T["vingt"], f("impact", 0.35), "accent", 0.0), (T["deux3"], J.piece(), "effet", 0.0),
           (T["immeuble3"], f("erreur", 0.25), "effet", 0.0), (T["que_fin"], f("arret", 0.35), "effet", 0.0)]
    dur = T["fin"] + 1
    mus = Z.musique(dur, [(0, "tension"), (to, "pulsation"), (T["trou"] + 0.55, "silence"), (T["vous"], "tension"),
                          (T["mais"], "silence"), (T["mais"] + 0.8, "pulsation"), (T["louis"], "reflexion"),
                          (T["et3"], "tension"), (T["le7"], "silence"), (T["le7"] + 1.0, "tension"),
                          (T["que_fin"], "silence")])
    mus = mus.mean(1) if mus.ndim == 2 else mus
    ev.append((0.0, mus, "ambiance", 0.0))
    return ev


REPERES = [("dixsept", "dixsept", None), ("rue", "rue", None), ("souvre", "souvre", None), ("trou", "trou", None),
           ("immeuble", "immeuble", None), ("vide", "vide", "immeuble"), ("vous", "vous", "vide"), ("sauf", "sauf", None),
           ("deux", "deux", "sauf"), ("pendant", "pendant", None), ("monuments", "monuments", None),
           ("immeubles", "immeubles", "monuments"), ("resultat", "resultat", None), ("sans", "sans", "resultat"),
           ("piliers1", "piliers", "resultat"), ("mais", "mais", "piliers1"), ("dautres", "dautres", None),
           ("gruyere", "gruyere", None), ("trous", "trous", None), ("louis", "louis", None),
           ("guillaumot", "guillaumot", None), ("piliers", "piliers", "guillaumot"), ("murs", "murs", None),
           ("graver", "graver", None), ("et3", "et", "audessus"), ("debordent", "debordent", None),
           ("insalubre", "insalubre", None), ("dixsept2", "dixsept", "insalubre"), ("carrieres3", "carrieres", "ossements"),
           ("six", "six", None), ("catacombes1", "catacombes", "six"), ("et4", "et", "catacombes1"),
           ("lancienne", "lancienne", None), ("rue3", "rue", "lancienne"), ("le7", "le", "rue3"), ("dixneuf", "dixneuf", None),
           ("seffondre", "seffondre", None), ("vingt", "vingt", "seffondre"), ("aujourdhui3", "aujourdhui", "vingt"),
           ("deux3", "deux", "aujourdhui3"), ("parce", "parce", None), ("immeuble3", "immeuble", "parce"),
           ("alors", "alors", "immeuble3")]


def preparer():
    global VOIX
    chemin = os.path.join(ICI, "audio", "voix.mp3")
    MV.charger(types.SimpleNamespace(SEGS=os.path.join(ICI, "audio", "voix.json"), VOIX=chemin))
    VOIX, _, _ = MI.tighten(MI.load_voice(chemin), max_gap=0.40, thr_db=-38.0)
    T.clear()
    aux = {"audessus": MV.mot("audessus", MV.mot("graver")), "ossements": MV.mot("ossements")}
    for nom, cle, apres in REPERES:
        base = T.get(apres, aux.get(apres, 0.0)) if apres else 0.0
        T[nom] = MV.mot(cle, base + 0.01 if apres else 0.0)
    T["rue_fin"] = T["vous"]
    T["que_fin"] = MV.MOTS[-1][1]
    T["fin"] = T["que_fin"] + 0.05
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
    f = P.police(18, pixel=False)
    w = d.textlength("LA SUITE DEMAIN", font=f)
    d.text(((P.LW - w) / 2, 220), "LA SUITE DEMAIN", font=f, fill=BLANC)
    x = (P.LW + w) / 2 + 6
    d.polygon([(x, 224), (x + 10, 230), (x, 236)], fill=ROUGE)
    return np.asarray(P.agrandir(img))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep32.mp4"
    if len(sys.argv) > 3:
        rendre(out, float(sys.argv[2]), float(sys.argv[3]))
    else:
        rendre(out)
