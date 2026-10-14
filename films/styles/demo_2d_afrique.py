"""Démo : huit TECHNIQUES d'animation 2D différentes (pas seulement des rendus différents), sur des thèmes africains.

  1. ombres chinoises : marionnettes articulées en silhouette (à la Lotte Reiniger), rivets visibles
  2. animation de sable : une table lumineuse, le sable balayé fait apparaître le dessin
  3. tableau blanc : une main dessine au feutre, trait après trait
  4. papier découpé en stop-motion : couches de papier, ombres portées, 12 images/s, léger tremblé
  5. morphing : une forme se transforme en une autre (contours rééchantillonnés et interpolés)
  6. particules : des milliers de grains portés par un flux se rassemblent en une forme, puis s'envolent
  7. caméra multiplane : plans à différentes profondeurs, parallaxe et flou de profondeur
  8. typographie cinétique : les mots sont l'animation (rebonds, glissés, balayages)

    python -m films.styles.demo_2d_afrique output/demo_2d_afrique.mp4
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from films import montage_ia as MI
from films.styles import oscillo_son as Z
from films.styles import son_jeu as J

W, H = 540, 960
FPS = 30
DUREE = 4.6
POL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")


def police(n, t):
    return ImageFont.truetype(os.path.join(POL, n), t)


def lisse(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def rebond(u):
    """Arrivée avec dépassement (ressort amorti)."""
    u = max(0.0, u)
    return 1 - math.exp(-6 * u) * math.cos(9 * u)


# ------------------------------------------------------------------------------------------------ formes communes
AFRIQUE_LL = [(-6, 35.8), (10, 37), (11, 33), (20, 31), (25, 31.5), (32, 31.2), (33, 30), (35, 24), (38, 18), (43, 12),
              (51, 12), (51, 10), (48, 5), (45, 2), (42, -1), (40, -3), (39, -7), (40, -10), (40, -15), (35, -20),
              (35, -24), (33, -26), (32, -29), (28, -33), (25, -34), (20, -35), (18, -33), (15, -27), (12, -18),
              (12, -13), (13, -9), (12, -5), (9, -1), (9, 1), (9, 4), (6, 4), (3, 6), (0, 5.5), (-3, 5), (-7.5, 4.4),
              (-11, 6.5), (-13, 8), (-15, 11), (-17.2, 14.7), (-16.5, 19), (-17, 21), (-14, 26), (-10, 29), (-9.5, 32)]


def afrique(cx, cy, k):
    """Contour de l'Afrique (approché), centré, k pixels par degré."""
    return [(cx + (lon - 17) * k, cy - (lat - 1) * k) for lon, lat in AFRIQUE_LL]


def baobab(cx, base, k):
    """Silhouette de baobab : tronc large, branches courtes en couronne."""
    pts = [(-1.6, 0), (-1.3, -2), (-1.1, -4), (-1.2, -5.2), (-2.6, -6.4), (-3.2, -7.4), (-2.4, -7.1), (-1.4, -6.2),
           (-1.2, -7.2), (-1.7, -8.4), (-0.9, -7.6), (-0.4, -6.4), (0.1, -8.2), (0.6, -6.4), (1.1, -7.8), (1.5, -6.6),
           (1.2, -5.6), (2.4, -6.8), (3.3, -7.2), (2.6, -6.2), (1.3, -4.9), (1.1, -4), (1.3, -2), (1.6, 0)]
    return [(cx + x * k, base + y * k) for x, y in pts]


def reechantillonner(pts, n):
    """n points régulièrement espacés le long d'un contour fermé."""
    p = np.array(pts + [pts[0]], float)
    seg = np.hypot(*(p[1:] - p[:-1]).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, cum[-1], n, endpoint=False)
    x = np.interp(s, cum, p[:, 0])
    y = np.interp(s, cum, p[:, 1])
    return np.stack([x, y], 1)


def aligner(a, b):
    """Décale b pour que ses points correspondent au mieux à ceux de a (morphing sans croisement)."""
    best, k_best = 1e18, 0
    for k in range(0, len(b), 2):
        e = ((a - np.roll(b, k, 0)) ** 2).sum()
        if e < best:
            best, k_best = e, k
    return np.roll(b, k_best, 0)


def masque(poly, taille=(W, H)):
    m = Image.new("L", taille, 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    return np.asarray(m) > 0


def bandeau(img, num, nom):
    """Le titre de la technique, en haut."""
    d = ImageDraw.Draw(img)
    f1, f2 = police("Montserrat-ExtraBold.ttf", 22), police("Montserrat-Bold.ttf", 15)
    d.rounded_rectangle((24, 40, 24 + 46, 40 + 46), 10, fill=(255, 255, 255))
    d.text((24 + 23, 40 + 23), str(num), font=f1, fill=(20, 20, 20), anchor="mm")
    d.text((84, 46), nom, font=f1, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    return d


# ------------------------------------------------------------------------------------------------ 1. ombres chinoises
def _membre(d, a, ang, l, w, col=(0, 0, 0)):
    b = (a[0] + l * math.sin(ang), a[1] + l * math.cos(ang))
    d.line([a, b], fill=col, width=int(w))
    d.ellipse((b[0] - w / 2, b[1] - w / 2, b[0] + w / 2, b[1] + w / 2), fill=col)
    return b


def _rivet(d, p):
    d.ellipse((p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2), fill=(120, 40, 10))


def s_ombres(t):
    img = Image.new("RGB", (W, H))
    a = np.zeros((H, W, 3), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot((xx - W / 2) / W, (yy - H * 0.45) / H)
    for c, (v0, v1) in enumerate(((255, 120), (170, 30), (60, 10))):
        a[..., c] = v0 + (v1 - v0) * np.clip(r * 1.8, 0, 1)
    img = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.ellipse((W / 2 - 90, 250, W / 2 + 90, 430), fill=(255, 214, 140))                     # le soleil
    sol = 760
    d.polygon([(0, sol)] + [(x, sol - 14 * math.sin(x / 60) - 6 * math.sin(x / 23)) for x in range(0, W + 10, 10)] + [(W, H), (0, H)],
              fill=(0, 0, 0))
    for x0, h, s in ((60, 300, 1), (470, 260, -1)):                                          # acacias en dentelle
        d.line([(x0, sol), (x0 + 10 * s, sol - h)], fill=(0, 0, 0), width=10)
        for k in range(9):
            bx = x0 + 10 * s + (k - 4) * 34
            by = sol - h - 10 + abs(k - 4) * 6
            d.line([(x0 + 10 * s, sol - h + 30), (bx, by)], fill=(0, 0, 0), width=4)
            d.ellipse((bx - 26, by - 10, bx + 26, by + 8), fill=(0, 0, 0))
    for k in range(70):                                                                       # herbes
        x = (k * 37) % W
        d.line([(x, sol + 4), (x + 6 * math.sin(t * 2 + k), sol - 18 - (k % 5) * 4)], fill=(0, 0, 0), width=2)
    # la marionnette : une femme portant une jarre, qui marche (pièces articulées, rivets visibles)
    x = 120 + 70 * t
    ph = t * 4.2
    hanche = (x, sol - 132 - 4 * abs(math.sin(ph)))
    for k, sg in enumerate((1, -1)):                                                          # jambes
        g = _membre(d, hanche, 0.35 * sg * math.sin(ph), 68, 16)
        _rivet(d, g)
        p = _membre(d, g, 0.35 * sg * math.sin(ph) - 0.3 * max(0, -sg * math.cos(ph)), 64, 12)
        d.polygon([(p[0] - 6, p[1] - 4), (p[0] + 18, p[1]), (p[0] + 18, p[1] + 6), (p[0] - 6, p[1] + 6)], fill=(0, 0, 0))
    d.polygon([(hanche[0] - 30, hanche[1] + 50), (hanche[0] + 30, hanche[1] + 50), (hanche[0] + 16, hanche[1] - 70),
               (hanche[0] - 16, hanche[1] - 70)], fill=(0, 0, 0))                              # la robe et le buste
    ep = (hanche[0] + 4, hanche[1] - 70)
    tete = (ep[0] + 4, ep[1] - 30)
    d.ellipse((tete[0] - 17, tete[1] - 20, tete[0] + 17, tete[1] + 18), fill=(0, 0, 0))
    d.polygon([(tete[0] + 12, tete[1] - 2), (tete[0] + 24, tete[1] + 6), (tete[0] + 12, tete[1] + 10)], fill=(0, 0, 0))
    jarre = (tete[0], tete[1] - 50)                                                           # la jarre sur la tête
    d.ellipse((jarre[0] - 30, jarre[1] - 26, jarre[0] + 30, jarre[1] + 30), fill=(0, 0, 0))
    d.rectangle((jarre[0] - 12, jarre[1] - 40, jarre[0] + 12, jarre[1] - 20), fill=(0, 0, 0))
    for k in range(5):                                                                        # dentelle découpée dans la jarre
        a2 = k / 5 * math.pi * 2
        px, py = jarre[0] + 16 * math.cos(a2), jarre[1] + 6 + 14 * math.sin(a2)
        d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=(230, 110, 40))
    bras = _membre(d, ep, math.pi + 0.15, 58, 10)                                             # bras levé qui tient la jarre
    _rivet(d, ep)
    _membre(d, bras, math.pi - 0.1, 30, 8)
    _membre(d, ep, 0.25 * math.sin(ph + 1), 60, 10)
    _rivet(d, hanche)
    for k in range(2):                                                                        # des oiseaux qui battent des ailes
        bx, by = 600 - 90 * t - 80 * k, 200 + 30 * k
        ail = 18 * math.sin(t * 11 + k)
        d.line([(bx - 22, by - ail), (bx, by), (bx + 22, by - ail)], fill=(0, 0, 0), width=5)
    bandeau(img, 1, "OMBRES CHINOISES")
    return img


# ------------------------------------------------------------------------------------------------ 2. sable
_GRAIN = np.random.default_rng(1).uniform(0, 1, (H, W)).astype(np.float32)


def s_sable(t):
    lum = np.array([255, 196, 110], np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    m = masque(afrique(W / 2 - 10, 520, 7.4)).astype(np.float32)
    m2 = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    # le pinceau de doigt balaie l'écran en zigzag : là où il est passé, le sable a été tiré vers le dessin
    u = lisse(t / 3.6)
    ligne = (yy - 180) / 640
    balaye = np.clip((u * 1.15 - ligne) * 6 + 0.3 * np.sin(xx / 30 + yy / 50), 0, 1)
    dens = 0.85 * (1 - balaye) + balaye * (0.08 + 0.9 * (1 - m2) * 0.0 + 0.92 * m2)
    dens = np.clip(dens + (_GRAIN - 0.5) * 0.35, 0, 1)
    rives = np.abs(np.gradient(m2)[0]) + np.abs(np.gradient(m2)[1])                           # bourrelets de sable
    dens = np.clip(dens + rives * 3 * balaye, 0, 1)
    a = lum[None, None, :] * (1 - 0.93 * dens[..., None])
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    fx = 120 + 300 * (0.5 + 0.5 * math.sin(t * 2.4))                                          # le bout du doigt
    fy = 180 + 640 * u
    d.ellipse((fx - 24, fy - 30, fx + 24, fy + 30), fill=(70, 40, 30))
    d.rounded_rectangle((fx - 22, fy - 200, fx + 22, fy - 10), 18, fill=(70, 40, 30))
    bandeau(img, 2, "ANIMATION DE SABLE")
    return img


# ------------------------------------------------------------------------------------------------ 3. tableau blanc
def _traits_tableau():
    tr = []
    tr.append([(70 + i * 8, 760) for i in range(52)])                                         # le sol
    tr.append(baobab(260, 760, 34) + [baobab(260, 760, 34)[0]])
    tr.append([(420 + 46 * math.cos(a), 260 + 46 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)])
    for k in range(8):
        a = k / 8 * 2 * math.pi
        tr.append([(420 + 58 * math.cos(a), 260 + 58 * math.sin(a)), (420 + 80 * math.cos(a), 260 + 80 * math.sin(a))])
    return tr


TRAITS_TB = _traits_tableau()


def s_tableau(t):
    img = Image.new("RGB", (W, H), (248, 248, 244))
    d = ImageDraw.Draw(img)
    total = sum(len(s) for s in TRAITS_TB)
    n = int(total * lisse(t / 3.4))
    pointe = None
    for s in TRAITS_TB:
        if n <= 0:
            break
        k = min(len(s), n)
        if k >= 2:
            d.line(s[:k], fill=(20, 20, 26), width=5, joint="curve")
        pointe = s[k - 1]
        n -= len(s)
    if t > 3.5:
        f = police("Caveat.ttf", 64)
        txt = "Le baobab"[:int((t - 3.5) * 14)]
        d.text((150, 800), txt, font=f, fill=(200, 40, 40))
        pointe = (150 + d.textlength(txt, font=f), 840)
    if pointe:                                                                                # la main et le feutre
        x, y = pointe
        d.polygon([(x, y), (x + 14, y - 10), (x + 70, y - 70), (x + 56, y - 84), (x + 4, y - 22)], fill=(30, 30, 40))
        d.polygon([(x + 50, y - 64), (x + 130, y - 120), (x + 170, y - 70), (x + 150, y - 20), (x + 70, y - 30)],
                  fill=(110, 70, 50))
        d.ellipse((x + 40, y - 70, x + 90, y - 30), fill=(120, 78, 56))
    bandeau(img, 3, "TABLEAU BLANC")
    return img


# ------------------------------------------------------------------------------------------------ 4. papier découpé
_PAPIER = np.random.default_rng(4).normal(0, 1, (H, W)).astype(np.float32)


def _couche(base, poly, col, ombre=8):
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).polygon(poly, fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    base.paste((0, 0, 0), (ombre // 2, ombre), sh)
    ImageDraw.Draw(base).polygon(poly, fill=col)


def s_papier(t):
    t = math.floor(t * 12) / 12                                                               # 12 images par seconde
    rng = np.random.default_rng(int(t * 12))
    j = lambda: rng.uniform(-1.5, 1.5)
    img = Image.new("RGB", (W, H), (244, 170, 60))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 60):                                                                 # un fond façon tissu wax
        for x in range(0, W, 60):
            o = 30 if (y // 60) % 2 else 0
            d.ellipse((x + o - 20, y - 20, x + o + 20, y + 20), fill=(214, 90, 40))
            d.ellipse((x + o - 9, y - 9, x + o + 9, y + 9), fill=(40, 90, 150))
    sol = 720
    _couche(img, [(W / 2 + 90 * math.cos(a) + j(), 400 + 90 * math.sin(a) + j()) for a in np.linspace(0, 6.28, 30)], (250, 210, 60))
    _couche(img, [(0, 600)] + [(x, 560 - 60 * math.sin(x / 120) + j()) for x in range(0, W + 30, 30)] + [(W, H), (0, H)], (150, 90, 40))
    _couche(img, [(0, sol)] + [(x, sol - 26 * math.sin(x / 70 + 1) + j()) for x in range(0, W + 30, 30)] + [(W, H), (0, H)], (90, 60, 30))
    # un éléphant en papier, articulé, qui avance par à-coups
    x = 40 + 90 * t
    ph = t * 5
    corps = [(x - 70, sol - 150), (x + 50, sol - 160), (x + 80, sol - 120), (x + 70, sol - 70), (x - 70, sol - 70), (x - 85, sol - 110)]
    for k, dx in enumerate((-55, -25, 25, 55)):
        lev = 10 * max(0, math.sin(ph + k * 1.6))
        _couche(img, [(x + dx - 13, sol - 90), (x + dx + 13, sol - 90), (x + dx + 12, sol - lev), (x + dx - 12, sol - lev)],
                (130, 136, 150) if k % 2 else (150, 156, 170), 6)
    _couche(img, [(p[0] + j(), p[1] + j()) for p in corps], (160, 166, 180))
    tete = [(x + 50, sol - 180), (x + 110, sol - 170), (x + 120, sol - 120), (x + 75, sol - 100), (x + 45, sol - 130)]
    _couche(img, tete, (170, 176, 190))
    tr = 0.3 * math.sin(ph)
    _couche(img, [(x + 105, sol - 135), (x + 122, sol - 130), (x + 128 + 20 * tr, sol - 40), (x + 112 + 20 * tr, sol - 40)], (160, 166, 180), 4)
    _couche(img, [(x + 40, sol - 170), (x + 75, sol - 175), (x + 70, sol - 110), (x + 35, sol - 120)], (140, 146, 162), 5)   # oreille
    ImageDraw.Draw(img).ellipse((x + 92, sol - 160, x + 100, sol - 152), fill=(20, 20, 20))
    a = np.asarray(img).astype(np.float32) * (1 + 0.035 * _PAPIER[..., None])               # grain du papier
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    bandeau(img, 4, "PAPIER DECOUPE (STOP-MOTION)")
    return img


# ------------------------------------------------------------------------------------------------ 5. morphing
N_M = 400
F_AFR = reechantillonner(afrique(W / 2 - 10, 500, 7.0), N_M)
F_BAO = aligner(F_AFR, reechantillonner(baobab(W / 2, 760, 52), N_M))
F_DJE = aligner(F_BAO, reechantillonner([(W / 2 - 110, 300), (W / 2 + 110, 300), (W / 2 + 70, 520), (W / 2 + 40, 560),
                                        (W / 2 + 70, 780), (W / 2 - 70, 780), (W / 2 - 40, 560), (W / 2 - 70, 520)], N_M))


def s_morph(t):
    img = Image.new("RGB", (W, H), (16, 14, 20))
    etapes = [(F_AFR, (230, 140, 50), "AFRIQUE"), (F_BAO, (120, 170, 80), "BAOBAB"), (F_DJE, (200, 70, 60), "DJEMBE")]
    seg = min(1.999, t / 2.0)
    i = int(seg)
    u = lisse((seg - i - 0.35) / 0.65)
    a, ca, na = etapes[i]
    b, cb, nb = etapes[i + 1]
    p = a * (1 - u) + b * u
    col = tuple(int(x * (1 - u) + y * u) for x, y in zip(ca, cb))
    d = ImageDraw.Draw(img)
    d.polygon([tuple(q) for q in p], fill=col)
    d.line([tuple(q) for q in p] + [tuple(p[0])], fill=(255, 255, 255), width=3)
    f = police("Montserrat-ExtraBold.ttf", 40)
    d.text((W / 2, 860), na if u < 0.5 else nb, font=f, fill=(255, 255, 255), anchor="mm")
    bandeau(img, 5, "MORPHING")
    return img


# ------------------------------------------------------------------------------------------------ 6. particules
N_P = 5000
_RNG = np.random.default_rng(6)
_M_AFR = masque(afrique(W / 2 - 10, 500, 7.0))
_CIBLES = np.argwhere(_M_AFR)[_RNG.choice(_M_AFR.sum(), N_P)][:, ::-1].astype(np.float32)
_DEPART = np.stack([_RNG.uniform(0, W, N_P), _RNG.uniform(0, H, N_P)], 1).astype(np.float32)
_PHASE = _RNG.uniform(0, 6.28, N_P).astype(np.float32)


def s_particules(t):
    img = Image.new("RGB", (W, H), (6, 6, 14))
    a = np.asarray(img).copy()
    u = lisse((t - 0.4) / 2.0)
    v = lisse((t - 3.4) / 1.2)
    tour = np.stack([np.sin(_DEPART[:, 1] / 60 + t * 1.5 + _PHASE), np.cos(_DEPART[:, 0] / 60 + t * 1.3 + _PHASE)], 1) * 40
    p = (_DEPART + tour) * (1 - u) + _CIBLES * u
    p += np.stack([np.cos(_PHASE), np.sin(_PHASE)], 1) * (v * 500)                            # l'explosion finale
    p[:, 1] -= v * v * 200
    x, y = p[:, 0].astype(int), p[:, 1].astype(int)
    ok = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
    col = np.stack([255 * np.ones(N_P), 150 + 80 * np.sin(_PHASE), 60 + 40 * np.cos(_PHASE)], 1).astype(np.uint8)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        a[y[ok] + dy, x[ok] + dx] = col[ok]
    img = Image.fromarray(a)
    halo = img.filter(ImageFilter.GaussianBlur(6))
    img = Image.fromarray(np.clip(np.asarray(img, np.int16) + np.asarray(halo, np.int16), 0, 255).astype(np.uint8))
    bandeau(img, 6, "PARTICULES")
    return img


# ------------------------------------------------------------------------------------------------ 7. multiplane
def _plan(poly_fn, col, decal, flou):
    lay = Image.new("RGBA", (W + 600, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon(poly_fn(), fill=col)
    for k in range(int(decal)):
        pass
    if flou:
        lay = lay.filter(ImageFilter.GaussianBlur(flou))
    return lay


def _girafe(d, x, sol, h, col):
    d.polygon([(x - 40, sol - h * 0.55), (x + 30, sol - h * 0.6), (x + 40, sol - h * 0.45), (x - 40, sol - h * 0.4)], fill=col)
    for dx in (-34, -20, 18, 32):
        d.line([(x + dx, sol - h * 0.45), (x + dx, sol)], fill=col, width=6)
    d.line([(x + 30, sol - h * 0.58), (x + 70, sol - h)], fill=col, width=12)
    d.polygon([(x + 62, sol - h - 6), (x + 96, sol - h + 4), (x + 90, sol - h + 14), (x + 66, sol - h + 8)], fill=col)


def s_multiplane(t):
    cam = 60 * t
    img = Image.new("RGB", (W, H))
    a = np.zeros((H, W, 3), np.float32)
    g = np.linspace(0, 1, H)[:, None]
    for c, (v0, v1) in enumerate(((255, 120), (150, 40), (60, 50))):
        a[..., c] = v0 + (v1 - v0) * (1 - g)
    img = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.ellipse((300 - cam * 0.05, 420, 420 - cam * 0.05, 540), fill=(255, 230, 160))
    plans = [(0.15, (190, 90, 60), 560, 0), (0.35, (130, 60, 50), 620, 1), (0.7, (70, 34, 30), 700, 2), (1.6, (20, 10, 10), 820, 6)]
    for k, (prof, col, sol, flou) in enumerate(plans):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        o = -cam * prof
        dl.polygon([(0, H), (0, sol)] + [(x, sol - 30 * math.sin((x - o) / (90 + 40 * k)) - 12 * math.sin((x - o) / 31))
                                          for x in range(0, W + 10, 10)] + [(W, H)], fill=col)
        if k == 1:
            for gx in (180, 520, 860):
                _girafe(dl, gx + o % 1100 - 300, sol + 10, 230, col)
        if k == 2:
            for ax in range(-200, 1400, 330):                                                 # acacias
                x = ax + o
                dl.line([(x, sol + 20), (x + 6, sol - 160)], fill=col, width=9)
                dl.ellipse((x - 110, sol - 200, x + 120, sol - 140), fill=col)
        if k == 3:
            for hx in range(-100, 1600, 40):                                                  # herbes au premier plan
                x = hx + o
                dl.polygon([(x, H), (x + 10, sol - 90 - (hx * 7) % 60), (x + 22, H)], fill=col)
        if flou:
            lay = lay.filter(ImageFilter.GaussianBlur(flou))
        img.paste(lay, (0, 0), lay)
    bandeau(img, 7, "CAMERA MULTIPLANE")
    return img


# ------------------------------------------------------------------------------------------------ 8. typographie cinétique
def s_typo(t):
    img = Image.new("RGB", (W, H), (240, 196, 60))
    d = ImageDraw.Draw(img)
    u = lisse(t / 0.5)
    d.rectangle((0, 0, W * u, H), fill=(20, 20, 24))                                          # balayage
    mots = [(0.4, "1324", 150, (240, 196, 60), 300), (1.2, "MANSA", 92, (255, 255, 255), 470),
            (1.6, "MOUSSA", 92, (255, 255, 255), 570), (2.4, "PART POUR", 46, (240, 196, 60), 680),
            (2.8, "LA MECQUE", 64, (255, 255, 255), 750)]
    for t0, m, taille, col, y in mots:
        if t < t0:
            continue
        k = rebond((t - t0) * 1.4)
        f = police("Montserrat-ExtraBold.ttf", max(4, int(taille * (0.4 + 0.6 * k))))
        x = W / 2 + (1 - lisse((t - t0) / 0.35)) * (W if mots.index((t0, m, taille, col, y)) % 2 else -W)
        d.text((x, y), m, font=f, fill=col, anchor="mm")
    if t > 3.5:
        d.rectangle((60, 800, 60 + (W - 120) * lisse((t - 3.5) / 0.4), 808), fill=(240, 196, 60))
    bandeau(img, 8, "TYPOGRAPHIE CINETIQUE")
    return img


SCENES = [s_ombres, s_sable, s_tableau, s_papier, s_morph, s_particules, s_multiplane, s_typo]


def image(t):
    k = min(len(SCENES) - 1, int(t / DUREE))
    im = SCENES[k](t - k * DUREE)
    fin = (k + 1) * DUREE - t
    if fin < 0.12 and k < len(SCENES) - 1:                                                    # petit flash entre les plans
        im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), 1 - fin / 0.12)
    return im.resize((W * 2, H * 2), Image.LANCZOS)


def rendre(sortie):
    dur = DUREE * len(SCENES)
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W * 2}x{H * 2}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", f"{tmp}/v.mp4"],
                          stdin=subprocess.PIPE)
    for f in range(int(dur * FPS)):
        ff.stdin.write(np.asarray(image(f / FPS)).tobytes())
    ff.stdin.close()
    ff.wait()
    n = int(dur * MI.SR)
    mus = Z.musique(dur, [(0, "chaleur"), (DUREE * 4, "pulsation"), (DUREE * 7, "tension2")])
    mus = mus.mean(1) if mus.ndim == 2 else mus
    a = np.zeros(n)
    a[:min(n, len(mus))] += 0.5 * mus[:n]
    for k in range(1, len(SCENES)):
        s = J.fichier("swoosh", 0.4)
        i = int((k * DUREE - 0.15) * MI.SR)
        a[i:i + len(s)] += s[:n - i]
    MI.write_wav(f"{tmp}/a.wav", a) if hasattr(MI, "write_wav") else None
    if not os.path.exists(f"{tmp}/a.wav"):
        import wave
        with wave.open(f"{tmp}/a.wav", "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(MI.SR)
            w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", sortie], check=True)
    print("OK", sortie)


if __name__ == "__main__":
    rendre(sys.argv[1] if len(sys.argv) > 1 else "output/demo_2d_afrique.mp4")
