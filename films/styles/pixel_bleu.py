"""Style @alfred.explique, en bleu, entièrement dessiné par le code (aucune planche).

Toile de 270 × 480 « vrais pixels » (dessin sans anticrénelage), agrandie ×4 au plus proche → 1080 × 1920.
Palette stricte : 5 bleus, gris, blanc, rouge d'alerte. Ombres en 3-4 tons et tramage de Bayer, halo bleu, poussières
qui flottent. Les personnages ont un squelette : leurs poses se calculent à chaque image (mouvement continu).
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
LW, LH, K = 270, 480, 4
W, H = LW * K, LH * K

NOIR = (3, 5, 12)
B0 = (14, 42, 92)          # bleu très sombre
B1 = (27, 79, 156)         # bleu sombre
B2 = (47, 127, 224)        # bleu
B3 = (111, 178, 255)       # bleu clair
B4 = (207, 230, 255)       # bleu très clair
GRIS = (138, 148, 166)
GRIS_F = (78, 86, 104)
BLANC = (242, 246, 255)
ROUGE = (232, 65, 58)
ROUGE_F = (140, 30, 30)

POLICES = os.path.join(ICI, "..", "fonts")


def police(taille, gras=True, pixel=True):
    nom = ("Silkscreen-Bold.ttf" if gras else "Silkscreen-Regular.ttf") if pixel else "Montserrat-ExtraBold.ttf"
    return ImageFont.truetype(os.path.join(POLICES, nom), taille)


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16
SEUIL = np.tile(BAYER, (LH // 4 + 1, LW // 4 + 1))[:LH, :LW]
_YY, _XX = np.mgrid[0:LH, 0:LW]
POUSSIERES = np.random.default_rng(11).uniform(0, 1, (55, 4))


def toile():
    img = Image.new("RGB", (LW, LH), NOIR)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"                                       # texte sans anticrénelage : de vrais pixels
    return img, d


def halo(img, cx, cy, r, col=B0, force=0.9):
    """Un halo de couleur tramé (Bayer) : la lumière ambiante, sans dégradé lisse."""
    a = np.asarray(img).copy()
    dist = np.sqrt(((_XX - cx) / r) ** 2 + ((_YY - cy) / r) ** 2)
    m = (np.clip(1 - dist, 0, 1) * force) > SEUIL
    a[m] = col
    return Image.fromarray(a)


def poussieres(d, t, col=B2):
    for x, y, v, ph in POUSSIERES:
        yy = (y * LH - t * (4 + 8 * v)) % LH
        xx = x * LW + 3 * math.sin(t * 0.7 + ph * 6)
        if (int(t * 3 + ph * 10) % 5):
            d.point((int(xx), int(yy)), fill=col if v > 0.3 else B1)


def tramer(d, x0, y0, x1, y1, col_a, col_b, part=0.5):
    """Remplit un rectangle avec deux couleurs mêlées par tramage (part de col_b)."""
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            d.point((x, y), fill=col_b if BAYER[y % 4, x % 4] < part else col_a)


def sol(d, y, x0=8, x1=262):
    d.rectangle((x0, y, x1, y + 2), fill=B2)
    d.rectangle((x0, y + 3, x1, y + 14), fill=B0)
    for x in range(x0, x1, 3):                              # la texture de la terre / du plancher
        if (x * 7) % 5 < 2:
            d.point((x, y + 5 + (x * 3) % 7), fill=B1)


# ------------------------------------------------------------------------------------------------ personnages
def _seg(d, p, q, w, col):
    d.line([p, q], fill=col, width=w)
    r = w // 2
    if r > 0:
        d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=col)


def bonhomme(d, pieds, taille=64, tronc=0.0, bras=None, genou=0.0, tete_ang=None, assis=False, couleur=B2):
    """Un personnage pixel à squelette. pieds = (x, y) ; tronc = inclinaison en degrés (négatif = vers l'arrière,
    à gauche) ; bras = point visé par les deux mains (ou None : bras le long du corps) ; genou = flexion 0..1.
    Renvoie la position des épaules."""
    x, y = pieds
    s = taille / 64
    jambe = 26 * s
    if assis:
        bassin = (x - 10 * s, y - 14 * s)
        genoux = (x + 6 * s, y - 14 * s)
        _seg(d, (int(bassin[0]), int(bassin[1])), (int(genoux[0]), int(genoux[1])), max(3, int(5 * s)), GRIS_F)
        _seg(d, (int(genoux[0]), int(genoux[1])), (int(x + 6 * s), int(y)), max(3, int(5 * s)), GRIS_F)
    else:
        kx = 6 * s * genou
        bassin = (x - 4 * s * genou - 2, y - jambe * (1 - 0.25 * genou))
        for dx, col in ((-3 * s, GRIS_F), (3 * s, GRIS)):  # les deux jambes (l'arrière plus sombre)
            g = (x + dx + kx, y - jambe * 0.5)
            _seg(d, (int(bassin[0] + dx / 2), int(bassin[1])), (int(g[0]), int(g[1])), max(3, int(5 * s)), col)
            _seg(d, (int(g[0]), int(g[1])), (int(x + dx), int(y)), max(3, int(5 * s)), col)
            d.rectangle((int(x + dx - 2), int(y - 1), int(x + dx + 4 * s), int(y + 1)), fill=B0)
    a = math.radians(tronc)
    lg = 24 * s
    epaule = (bassin[0] + lg * math.sin(a), bassin[1] - lg * math.cos(a))
    _seg(d, (int(bassin[0]), int(bassin[1])), (int(epaule[0]), int(epaule[1])), max(5, int(10 * s)), couleur)
    _seg(d, (int(bassin[0] + 2), int(bassin[1] - 2)), (int(epaule[0] + 2), int(epaule[1] + 2)), max(1, int(2 * s)), B3)
    ta = a if tete_ang is None else math.radians(tete_ang)
    tc = (epaule[0] + 8 * s * math.sin(ta), epaule[1] - 8 * s * math.cos(ta))
    r = 6 * s
    d.ellipse((tc[0] - r, tc[1] - r, tc[0] + r, tc[1] + r), fill=B4)
    d.chord((tc[0] - r, tc[1] - r - 1, tc[0] + r, tc[1] + r), 180, 360, fill=B0)   # les cheveux
    for k, col in ((0, B1), (1, couleur)):                  # les bras (l'arrière plus sombre)
        if bras is None:
            main = (epaule[0] + 4 * s * (k - 0.5), epaule[1] + 20 * s)
        else:
            main = (bras[0], bras[1] + k)
        _seg(d, (int(epaule[0]), int(epaule[1] + 2)), (int(main[0]), int(main[1])), max(2, int(4 * s)), col)
        d.ellipse((main[0] - 2, main[1] - 2, main[0] + 2, main[1] + 2), fill=B4)
    return epaule


def siege(d, x, y, s=1.0):
    """Un siège d'avion vu de profil (dossier à gauche), pieds au sol y."""
    d.rectangle((int(x - 14 * s), int(y - 46 * s), int(x - 8 * s), int(y - 12 * s)), fill=B1)
    d.rectangle((int(x - 14 * s), int(y - 46 * s), int(x - 12 * s), int(y - 12 * s)), fill=B2)
    d.rectangle((int(x - 14 * s), int(y - 16 * s), int(x + 10 * s), int(y - 11 * s)), fill=B1)
    d.rectangle((int(x - 14 * s), int(y - 16 * s), int(x + 10 * s), int(y - 15 * s)), fill=B3)
    d.rectangle((int(x - 4 * s), int(y - 11 * s), int(x - 1 * s), int(y)), fill=GRIS_F)


# ------------------------------------------------------------------------------------------------ interface
def jauge(d, t, v, x=34, y=58, etiquette="PRESSION", valeur="", alerte=False):
    """Le cadran à aiguille persistant (en haut à gauche). v : 0..1."""
    r = 22
    for k in range(0, 181, 6):                              # l'arc gradué, rouge au bout
        a = math.radians(180 + k)
        col = ROUGE if k > 140 else (B2 if k % 30 == 0 else B1)
        r0 = r - (4 if k % 30 == 0 else 2)
        d.line([(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a))], fill=col)
    d.arc((x - r - 2, y - r - 2, x + r + 2, y + r + 2), 180, 360, fill=GRIS_F)
    a = math.radians(180 + 180 * max(0.0, min(1.0, v)) + 2 * math.sin(t * 40) * (v > 0.85))
    d.line([(x, y), (x + (r - 5) * math.cos(a), y + (r - 5) * math.sin(a))], fill=BLANC, width=2)
    d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=B3)
    f = police(8)
    clign = alerte and int(t * 6) % 2
    lg = d.textlength(etiquette, font=f)
    d.rectangle((x + r + 6, y - 20, x + r + 10 + lg, y - 8), outline=ROUGE, fill=ROUGE_F if clign else NOIR)
    d.text((x + r + 8, y - 19), etiquette, font=f, fill=BLANC if clign else ROUGE)
    if valeur:
        d.text((x - 10, y + 3), valeur, font=police(8), fill=B3)


def cadre_texte(d, xy, txt, taille=8, col=B4, bord=B2, fond=NOIR):
    f = police(taille)
    lg = d.textlength(txt, font=f)
    x, y = xy
    d.rectangle((x - 3, y - 3, x + lg + 3, y + taille + 3), outline=bord, fill=fond)
    d.text((x, y), txt, font=f, fill=col)


def agrandir(img):
    return img.resize((W, H), Image.NEAREST)


def vhs(a, t, force=1.0):
    """Rembobinage VHS sur l'image finale (numpy H×W×3) : bandes de neige, décalage des lignes, couleurs lavées."""
    rng = np.random.default_rng(int(t * 997))
    a = a.astype(np.int16)
    for _ in range(int(6 * force)):
        y = rng.integers(0, H - 40)
        h = rng.integers(8, 40)
        a[y:y + h] = np.roll(a[y:y + h], rng.integers(-60, 60), axis=1)
        bruit = rng.integers(0, 255, (h, W // 4, 1)).repeat(4, 1)
        m = rng.uniform(0, 1, (h, W // 4, 1)).repeat(4, 1) < 0.35 * force
        a[y:y + h] = np.where(m, bruit, a[y:y + h])
    a[..., 2] = np.clip(a[..., 2] + 20 * force, 0, 255)
    return np.clip(a, 0, 255).astype(np.uint8)
