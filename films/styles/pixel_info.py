"""Style « infographie pixel » (bleu-vert + orange sur noir) : boîte à outils commune aux scènes de ce style.

Principes (d'après l'analyse de films/styles/analyse_archibald.md et la comparaison du 8 octobre) :
  - les objets sont des icônes PLEINES en gros pixels, avec 2 ou 3 nuances (lumière, ombre), peu de détails ;
  - l'image est dessinée sur une petite toile (270 × 480) puis agrandie ×4 sans lissage : de vrais pixels nets ;
  - deux polices : la phrase en grotesque blanche grasse (pleine définition), les chiffres et mots-clés en police
    pixel de couleur ;
  - fond presque noir, trame de points, halo lent, quelques poussières, grain léger ; pas de lignes de balayage ;
  - mouvement utile seulement : un élément apparaît (fondu en trame de pixels), un compteur défile, un objet suit
    sa physique ; entre deux apparitions, l'image est calme.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

LW, LH, K = 270, 480, 4                                    # toile basse définition et facteur d'agrandissement
W, H = LW * K, LH * K
ICI = os.path.dirname(os.path.abspath(__file__))
POLICES = os.path.join(ICI, "..", "fonts")

# palette maison
NOIR = (6, 10, 12)
BV = (40, 175, 175)                                        # bleu-vert vif
BV_MOYEN = (26, 110, 112)
BV_SOMBRE = (14, 52, 56)
ORANGE = (255, 138, 61)
ORANGE_CLAIR = (255, 196, 140)
ORANGE_SOMBRE = (168, 72, 26)
BLANC = (236, 242, 240)
GRIS = (120, 130, 132)


def pixel(taille, gras=True):
    return ImageFont.truetype(os.path.join(POLICES, "Silkscreen-Bold.ttf" if gras else "Silkscreen-Regular.ttf"), taille)


F8, F16, F24, F32 = pixel(8, False), pixel(16), pixel(24), pixel(32)
GROTESQUE = ImageFont.truetype(os.path.join(POLICES, "Montserrat-ExtraBold.ttf"), 84)


def lisse(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def sortie(u, p=3.0):
    return 1 - (1 - min(1.0, max(0.0, u))) ** p


# ------------------------------------------------------------------------------------------------ apparition en trame
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16
SEUIL = np.tile(BAYER, (LH // 4 + 1, LW // 4 + 1))[:LH, :LW]


def calque():
    """Une image transparente de la taille de la toile, pour un élément."""
    return Image.new("RGBA", (LW, LH), (0, 0, 0, 0))


def poser(toile, cal, u):
    """Pose le calque sur la toile ; u de 0 à 1 : il apparaît pixel par pixel (trame de Bayer)."""
    if u <= 0:
        return
    a = np.asarray(cal)
    vis = (a[..., 3] > 0) & (SEUIL < min(1.0, u) - 1e-6)
    t = np.asarray(toile).copy()
    t[vis] = a[vis][:, :3]
    toile.paste(Image.fromarray(t))


def apparition(t, t0, d=0.3):
    return 0.0 if t < t0 else min(1.0, (t - t0) / d)


# ------------------------------------------------------------------------------------------------ dessins de base
def texte(d, xy, s, f=F8, col=BLANC, centre=True):
    x, y = xy
    if centre:
        x -= d.textlength(s, font=f) / 2
    d.text((round(x), round(y)), s, font=f, fill=col)


def tape(s, u):
    return s[:int(len(s) * min(1.0, max(0.0, u)))]


def fleche_haut(d, cx, y_bas, long, larg=6, col=ORANGE, ombre=ORANGE_SOMBRE):
    """Une grosse flèche pleine vers le haut (pixel)."""
    if long < 4:
        return
    tete = min(long, larg * 2 + 4)
    yh = y_bas - long
    d.rectangle([cx - larg // 2, yh + tete, cx + larg // 2, y_bas], fill=col)
    d.rectangle([cx + larg // 2 - 1, yh + tete, cx + larg // 2, y_bas], fill=ombre)
    d.polygon([(cx - larg - 4, yh + tete), (cx + larg + 4, yh + tete), (cx, yh)], fill=col)


def coche(d, x, y, col=BV, e=2):
    d.line([(x, y + 4), (x + 4, y + 8), (x + 12, y - 2)], fill=col, width=e)


def eau(d, x0, x1, y_surface, y_bas, t, vif=BV, fond=BV_SOMBRE):
    """De l'eau en trame (un pixel sur deux), une surface qui ondule, quelques reflets."""
    for y in range(int(y_surface) + 2, int(y_bas)):
        prof = (y - y_surface) / max(1, y_bas - y_surface)
        pas = 2 if prof < 0.55 else (3 if prof < 0.8 else 5)  # l'eau s'éteint vers le bas, sans bord net
        for x in range(int(x0) + (y % pas), int(x1), pas):
            d.point((x, y), fill=fond)
    for x in range(int(x0), int(x1)):
        y = y_surface + round(1.2 * math.sin(x / 9 + 2.2 * t))
        d.point((x, y), fill=vif)
        d.point((x, y + 1), fill=BV_MOYEN)
    for k in range(4):                                     # reflets qui glissent
        rx = x0 + ((k * 53 + t * 14) % max(1, (x1 - x0 - 10)))
        ry = y_surface + 6 + 9 * k
        if ry < y_bas - 2:
            d.line([(rx, ry), (rx + 6, ry)], fill=BV_MOYEN)


# ------------------------------------------------------------------------------------------------ fond et finition
_YY, _XX = np.mgrid[0:H, 0:W]
TRAME = (((_XX % K) == K // 2) & ((_YY % K) == K // 2)).astype(np.float32)
VIGNETTE = (1 - 0.45 * (((_XX - W / 2) / (W / 2)) ** 2 + ((_YY - H / 2) / (H / 2)) ** 2)).clip(0.4, 1)[..., None]
_LY, _LX = np.mgrid[0:LH, 0:LW]
POUSSIERES = np.random.default_rng(5).uniform(0, 1, (40, 4))


def fond(t):
    """La toile de départ : presque noire, un halo bleu-vert qui dérive lentement, quelques poussières."""
    cx = LW * (0.5 + 0.25 * math.sin(t * 0.13))
    cy = LH * (0.38 + 0.12 * math.sin(t * 0.09 + 1))
    r2 = ((_LX - cx) / (LW * 0.55)) ** 2 + ((_LY - cy) / (LH * 0.35)) ** 2
    halo = np.exp(-r2)[..., None] * np.array([6, 18, 18], np.float32)
    a = np.array(NOIR, np.float32) + halo
    for x0, y0, v, ph in POUSSIERES:                       # poussières qui dérivent
        x = int((x0 * LW + t * 3 * (v - 0.5)) % LW)
        y = int((y0 * LH - t * 4 * v) % LH)
        a[y, x] += 14 + 30 * (0.5 + 0.5 * math.sin(t * 2 + ph * 6))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def finition(toile, t, fps=30, neige=0.0):
    """Agrandit ×4 sans lissage, trame de points sur le fond, halo des couleurs vives, grain, vignette.
    neige > 0 : transition « télé » (bruit blanc mêlé à l'image)."""
    grand = toile.resize((W, H), Image.NEAREST)
    a = np.asarray(grand, np.float32)
    lum = a.max(axis=2, keepdims=True)
    a = a + (lum < 24).astype(np.float32) * TRAME[..., None] * np.array([10, 22, 22], np.float32)
    halo = np.asarray(grand.resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
                      .resize((W, H), Image.BILINEAR), np.float32)
    a = a + 0.45 * halo
    rng = np.random.default_rng(int(t * fps))
    a = a + rng.normal(0, 3.5, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)
    if neige > 0:
        n = rng.uniform(0, 255, (H // 8, W // 8, 1)).repeat(8, 0).repeat(8, 1)
        a = a * (1 - neige) + n * neige * np.array([0.8, 1.0, 1.0])
    a = a * VIGNETTE
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def phrase(img, lignes, y, t, t0, taille=84, t1=None):
    """La phrase en grotesque blanche, pleine définition, centrée ; *mot* = en orange. Arrive en glissant (0,15 s)."""
    if t < t0 or (t1 is not None and t >= t1):
        return
    u = sortie((t - t0) / 0.18)
    f = GROTESQUE if taille == 84 else ImageFont.truetype(os.path.join(POLICES, "Montserrat-ExtraBold.ttf"), taille)
    d = ImageDraw.Draw(img)
    dy = round(18 * (1 - u))
    alpha = u
    for i, ligne in enumerate(lignes):
        mots = ligne.split(" ")
        largeurs = [d.textlength(m.strip("*") + " ", font=f) for m in mots]
        x = (W - sum(largeurs) + d.textlength(" ", font=f)) / 2
        for m, lw in zip(mots, largeurs):
            col = ORANGE if m.startswith("*") else BLANC
            col = tuple(int(c * alpha + NOIR[k] * (1 - alpha)) for k, c in enumerate(col))
            d.text((x, y + i * taille * 1.18 + dy), m.strip("*"), font=f, fill=col)
            x += lw


# ------------------------------------------------------------------------------------------------ sons 8 bits
SR = 48000


def bip(f=1320, d=0.06, amp=0.12):
    """Un bip carré très court, façon console 8 bits."""
    n = int(d * SR)
    t = np.arange(n) / SR
    return amp * np.sign(np.sin(2 * math.pi * f * t)) * np.exp(-t / (d * 0.35))


def rafale(f0, n, pas=0.05, amp=0.1):
    return [(i * pas, bip(f0 + 60 * i, 0.05, amp)) for i in range(n)]
