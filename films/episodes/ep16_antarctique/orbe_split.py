"""Épisode 16 — « L'air de l'Antarctique » : vraies images en plein écran, l'Orbe (petit) fixe en haut à droite.

Montage : un plan toutes les 2 à 3 s ; chaque plan a son mouvement de caméra (panoramique ou zoom) ; les images
basse définition ou à voir en entier (cartes, microscope, archives) sont posées en « carte » sur un fond flou ;
transitions variées : coupe sèche avec petit coup de zoom, filé horizontal (whip), zoom flouté, flash blanc sur les
révélations. Version retenue sans l'Orbe (ORBE=1 pour le remettre, fixe en haut à droite). Accroche discrète en haut au début, sous-titres karaoké en bas.

Les images (NASA, Wikimedia Commons) ne sont pas versionnées : voir images/CREDITS.md et images/telecharger.py.

    python -m films.episodes.ep16_antarctique.orbe_split output/ep16_antarctique.mp4
"""
import math
import os
import re
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia
from PIL import Image, ImageFilter

from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1
from films.persos import levres as LV
from films.persos.orbe import Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
VOIX = os.path.join(HERE, "audio", "voix.mp3")
VOIX2 = os.path.join(HERE, "audio", "voix_serree.wav")
FONT = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "..", "fonts", "Montserrat-ExtraBold.ttf"))
T_HOOK = 5.7
TR = 0.26                                                          # durée des transitions (s)
Y_SUB = 1500                                                       # ligne des sous-titres
ECHELLE_ORBE = 0.8

# phrases (temps de la voix d'origine, minutage ASR ; texte = ce que dit vraiment la voix)
SEG = [
    (0.00, 1.30, "Si tu casses ce glaçon,"),
    (1.68, 5.69, "tu respirerais un air que personne n'a respiré depuis 2 millions d'années."),
    (6.60, 7.16, "Vu d'en haut,"), (7.58, 10.15, "l'Antarctique n'est qu'une immense tache blanche."),
    (10.52, 11.17, "En réalité,"), (11.58, 13.77, "c'est la plus grande archive de la planète."),
    (14.48, 15.16, "Chaque année,"), (15.51, 16.61, "la neige s'entasse."),
    (17.05, 18.14, "Sous son propre poids,"), (18.38, 19.59, "elle devient de la glace…"),
    (20.05, 22.24, "et enferme de minuscules bulles d'air."), (22.83, 24.24, "Couche après couche."),
    (24.79, 27.92, "Les scientifiques forent à plus de 3 km de profondeur."),
    (28.35, 30.61, "Ils remontent de longs cylindres de glace :"), (31.09, 31.88, "des carottes."),
    (32.40, 33.17, "À l'intérieur,"), (33.53, 34.88, "l'atmosphère de la Terre,"),
    (35.32, 36.84, "bien avant les premiers humains."), (37.61, 38.33, "Mais le plus fou,"),
    (38.71, 41.00, "c'est que l'Antarctique n'a pas toujours été gelé."),
    (41.38, 42.97, "Il y a 90 millions d'années,"), (43.36, 44.36, "il y poussait des forêts."),
    (44.86, 46.06, "Des dinosaures y vivaient."), (46.69, 48.13, "Alors pourquoi tout a gelé ?"),
    (49.11, 51.45, "L'Amérique du Sud et l'Australie se sont éloignées."),
    (51.75, 54.96, "Un courant marin géant s'est formé tout autour du continent…"),
    (55.34, 56.55, "et l'a coupé des eaux chaudes."), (57.17, 58.80, "Il y a 34 millions d'années,"),
    (59.19, 61.00, "la glace a tout recouvert."), (61.73, 62.50, "Et ce n'est pas tout."),
    (62.73, 63.59, "Sur cette glace,"), (63.83, 65.75, "la moindre pierre noire se voit de loin."),
    (66.13, 69.49, "C'est le meilleur endroit au monde pour trouver des météorites."), (70.44, 71.82, "En 1984,"),
    (72.16, 74.65, "une chercheuse ramasse un caillou de 2 kilos."), (75.13, 76.17, "Il vient de Mars."),
    (76.76, 78.13, "En 1996,"), (78.49, 82.26, "on y découvre des formes minuscules qui ressemblent à des bactéries fossiles."),
    (82.77, 87.57, "Le président Bill Clinton annonce à la télévision une possible trace de vie sur Mars."),
    (88.24, 89.09, "Aujourd'hui encore,"), (89.44, 91.33, "le doute n'a jamais été totalement levé."),
    (91.86, 93.28, "Ce désert blanc n'est pas vide."), (93.70, 95.48, "C'est la mémoire de la Terre."),
]

# plans : (début en temps d'origine, image, mode, mire début → fin (0..1), zoom début → fin, transition d'entrée)
#   mode « plein » : l'image couvre l'écran ; « carte » : image entière posée sur son propre fond flou
#   transitions : coupe, filé, zoom, flash
PLANS = [
    (0.00, "05_bulles2", "plein", (0.68, 0.30), (0.64, 0.36), (1.25, 1.10), "coupe"),
    (2.90, "05_bulles2", "plein", (0.62, 0.36), (0.60, 0.38), (1.45, 1.7), "zoom"),
    (6.60, "02_antarctique", "carte", (0.5, 0.5), (0.5, 0.5), (0.92, 1.0), "filé"),
    (8.80, "nasa_GSFC_20171208_Archive_e001267", "plein", (0.4, 0.5), (0.6, 0.5), (1.0, 1.08), "coupe"),
    (10.52, "09_stock", "plein", (0.45, 0.45), (0.55, 0.45), (1.0, 1.12), "filé"),
    (14.48, "nasa_GSFC_20171208_Archive_e000911", "plein", (0.62, 0.5), (0.38, 0.5), (1.0, 1.05), "zoom"),
    (17.05, "13_glace", "plein", (0.35, 0.55), (0.6, 0.55), (1.0, 1.05), "coupe"),
    (18.38, "04_lame", "plein", (0.5, 0.5), (0.5, 0.45), (1.0, 1.2), "coupe"),
    (20.05, "05_bulles2", "plein", (0.62, 0.36), (0.6, 0.4), (1.6, 1.35), "zoom"),
    (22.83, "01_bulles", "plein", (0.25, 0.5), (0.55, 0.5), (1.0, 1.05), "filé"),
    (24.79, "06_forage", "plein", (0.5, 0.5), (0.45, 0.55), (1.0, 1.15), "flash"),
    (28.35, "07_camp", "plein", (0.25, 0.5), (0.7, 0.45), (1.0, 1.05), "filé"),
    (31.09, "07_camp", "plein", (0.62, 0.32), (0.6, 0.35), (1.3, 1.45), "coupe"),
    (32.40, "09_stock", "plein", (0.5, 0.45), (0.5, 0.5), (1.5, 1.1), "zoom"),
    (33.53, "05_bulles2", "plein", (0.6, 0.35), (0.62, 0.32), (1.7, 1.5), "coupe"),
    (35.32, "04_lame", "plein", (0.4, 0.5), (0.6, 0.5), (1.3, 1.1), "coupe"),
    (37.61, "nasa_PIA14557", "carte", (0.5, 0.5), (0.5, 0.5), (0.95, 1.05), "flash"),
    (38.71, "02_antarctique", "plein", (0.5, 0.5), (0.5, 0.5), (1.5, 1.15), "coupe"),
    (41.38, "10b_foret", "plein", (0.3, 0.5), (0.6, 0.5), (1.0, 1.05), "filé"),
    (43.36, "10_foret", "carte", (0.5, 0.5), (0.5, 0.5), (0.95, 1.05), "coupe"),
    (44.86, "11_dino", "plein", (0.22, 0.45), (0.5, 0.45), (1.1, 1.15), "flash"),
    (46.69, "nasa_GSFC_20171208_Archive_e001867", "plein", (0.3, 0.5), (0.7, 0.5), (1.0, 1.05), "filé"),
    (49.11, "12_courant", "carte", (0.5, 0.5), (0.5, 0.5), (0.95, 1.05), "coupe"),
    (51.75, "12_courant", "plein", (0.5, 0.45), (0.5, 0.48), (1.0, 1.3), "zoom"),
    (55.34, "nasa_GSFC_20171208_Archive_e000910", "plein", (0.35, 0.5), (0.65, 0.5), (1.0, 1.05), "filé"),
    (57.17, "13_glace", "plein", (0.65, 0.6), (0.45, 0.6), (1.1, 1.0), "coupe"),
    (59.19, "02_antarctique", "carte", (0.5, 0.5), (0.5, 0.5), (1.2, 0.95), "zoom"),
    (61.73, "nasa_GSFC_20171208_Archive_e000911", "plein", (0.4, 0.5), (0.6, 0.5), (1.15, 1.0), "filé"),
    (63.83, "15_meteorite", "plein", (0.35, 0.55), (0.32, 0.6), (1.0, 1.15), "flash"),
    (66.13, "15_meteorite", "plein", (0.32, 0.62), (0.33, 0.62), (1.45, 1.3), "coupe"),
    (70.44, "nasa_S85-39565", "plein", (0.4, 0.55), (0.55, 0.55), (1.0, 1.08), "filé"),
    (72.16, "nasa_ARC-1996-AC96-0345-1", "plein", (0.5, 0.45), (0.5, 0.5), (1.15, 1.0), "coupe"),
    (75.13, "nasa_PIA00407", "plein", (0.5, 0.5), (0.5, 0.5), (1.35, 1.0), "flash"),
    (76.76, "nasa_PIA00288", "carte", (0.5, 0.5), (0.5, 0.5), (0.95, 1.05), "filé"),
    (78.49, "nasa_ARC-1996-AC96-0345-11", "plein", (0.48, 0.47), (0.52, 0.5), (2.6, 2.2), "zoom"),
    (80.40, "nasa_PIA00290", "carte", (0.5, 0.5), (0.5, 0.5), (0.95, 1.05), "coupe"),
    (82.77, "16_clinton", "carte", (0.5, 0.5), (0.5, 0.5), (0.95, 1.05), "flash"),
    (85.40, "16b_clinton", "carte", (0.5, 0.5), (0.5, 0.5), (1.0, 1.1), "coupe"),
    (88.24, "nasa_PIA00283", "carte", (0.5, 0.5), (0.5, 0.5), (0.95, 1.05), "filé"),
    (91.86, "nasa_GSFC_20171208_Archive_e000910", "plein", (0.65, 0.5), (0.35, 0.5), (1.05, 1.0), "filé"),
    (93.70, "02_antarctique", "carte", (0.5, 0.5), (0.5, 0.5), (1.15, 0.9), "zoom"),
]

ORBE_XY = (890, 330)                                               # fixe, en haut à droite
AVEC_ORBE = os.environ.get("ORBE", "0") == "1"                     # version retenue : sans l'Orbe

# humeurs de l'Orbe (temps d'origine) : (yeux, palette)
MOODS = [(0.0, "surpris", "surprise"), (6.6, "parle", "calme"), (24.79, "parle", "reflexion"),
         (37.61, "surpris", "surprise"), (41.38, "parle", "joie"), (46.69, "parle", "reflexion"),
         (61.73, "surpris", "surprise"), (66.13, "parle", "idee"), (75.13, "surpris", "surprise"),
         (76.76, "parle", "calme"), (82.77, "parle", "idee"), (88.24, "parle", "reflexion"),
         (91.86, "parle", "calme")]


# ------------------------------------------------------------------------------------------------ voix
def construire_voix():
    """Silences ramenés à 0,40 s au plus. Renvoie (durée, temps d'origine → temps nouveau)."""
    v, f, _ = MI.tighten(MI.load_voice(VOIX), max_gap=0.40, thr_db=-38.0)
    with wave.open(VOIX2, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(MI.SR)
        w.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes())
    return len(v) / MI.SR, f



def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


# ------------------------------------------------------------------------------------------------ images
_CACHE = {}
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def _sk(im):
    return skia.Image.fromarray(np.array(im.convert("RGBA")), colorType=skia.kRGBA_8888_ColorType).withDefaultMipmaps()


def charger(nom):
    """(image nette, fond flou assombri) pour un nom d'image du dossier images/."""
    if nom not in _CACHE:
        path = next(os.path.join(IMG, nom + e) for e in (".jpg", ".jpeg", ".png") if
                    os.path.exists(os.path.join(IMG, nom + e)))
        im = Image.open(path).convert("RGB")
        s = max(W / im.width, H / im.height) / 6                   # flou calculé petit puis agrandi
        small = im.resize((max(8, int(im.width * s)), max(8, int(im.height * s))), Image.BILINEAR)
        small = small.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.55))
        _CACHE[nom] = (_sk(im), _sk(small))
    return _CACHE[nom]


def couvrir(c, img, fx, fy, z):
    s = max(W / img.width(), H / img.height()) * z
    hw, hh = W / 2 / s, H / 2 / s
    cx = min(max(fx * img.width(), hw), img.width() - hw)
    cy = min(max(fy * img.height(), hh), img.height() - hh)
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(s, s)
    c.translate(-cx, -cy)
    c.drawImage(img, 0, 0, SAMP)
    c.restore()


def carte(c, img, z):
    """Image entière posée au centre (coins arrondis, ombre)."""
    s = min(1000 / img.width(), 1000 / img.height()) * z
    w, h = img.width() * s, img.height() * s
    r = skia.Rect(W / 2 - w / 2, 970 - h / 2, W / 2 + w / 2, 970 + h / 2)
    rr = skia.RRect.MakeRectXY(r, 34, 34)
    sh = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 170),
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30))
    c.drawRRect(rr.makeOffset(0, 18) if hasattr(rr, "makeOffset") else rr, sh)
    c.save()
    c.clipRRect(rr, doAntiAlias=True)
    c.drawImageRect(img, r, SAMP)
    c.restore()
    c.drawRRect(rr, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255, 60), Style=skia.Paint.kStroke_Style,
                               StrokeWidth=3))


def plan(c, plans, k, t):
    """Dessine le plan k à l'instant t (mouvement de caméra propre au plan)."""
    t0, nom, mode, f0, f1, (z0, z1), _ = plans[k]
    t1 = plans[k + 1][0] if k + 1 < len(plans) else t0 + 3
    u = min(1.0, max(0.0, (t - t0) / max(0.1, t1 - t0)))
    u = 0.65 * u + 0.35 * ease(u)
    img, flou = charger(nom)
    z = z0 + (z1 - z0) * u
    if mode == "plein":
        couvrir(c, img, f0[0] + (f1[0] - f0[0]) * u, f0[1] + (f1[1] - f0[1]) * u, z)
    else:
        couvrir(c, flou, 0.5, 0.5, 1.15 + 0.05 * u)
        carte(c, img, z)


def montage(c, plans, t):
    k = max(i for i, p in enumerate(plans) if p[0] <= t)
    a = t - plans[k][0]
    tr = plans[k][6]
    u = a / TR
    if k == 0 or u >= 1 or tr == "coupe":
        p = 1 + 0.045 * math.exp(-a * 10) if tr == "coupe" and k else 1.0   # petit coup de zoom à la coupe
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(p, p)
        c.translate(-W / 2, -H / 2)
        plan(c, plans, k, t)
        c.restore()
        if tr == "flash" and k and a < 0.35:
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(255, 255, 255, int(235 * (1 - a / 0.35) ** 2))))
        return k
    e = ease(u)
    if tr == "filé":
        flou = skia.Paint(ImageFilter=skia.ImageFilters.Blur(70 * math.sin(math.pi * u) + 0.1, 0.1))
        c.saveLayer(None, flou)
        c.save()
        c.translate(-W * e, 0)
        plan(c, plans, k - 1, t)
        c.restore()
        c.save()
        c.translate(W * (1 - e), 0)
        plan(c, plans, k, t)
        c.restore()
        c.restore()
    elif tr == "zoom":
        sig = 28 * math.sin(math.pi * u) + 0.1
        c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sig, sig)))
        c.save()
        s = 1.35 - 0.35 * e
        c.translate(W / 2, H / 2)
        c.scale(s, s)
        c.translate(-W / 2, -H / 2)
        plan(c, plans, k, t)
        c.restore()
        c.saveLayerAlpha(None, int(255 * (1 - e)))
        s = 1 + 0.8 * e
        c.translate(W / 2, H / 2)
        c.scale(s, s)
        c.translate(-W / 2, -H / 2)
        plan(c, plans, k - 1, t)
        c.restore()
        c.restore()
    else:                                                            # flash
        plan(c, plans, k, t)
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(255, 255, 255, int(235 * (1 - min(1, a / 0.35)) ** 2))))
    return k


def voiles(c):
    """Assombrit le haut (accroche) et le bas (sous-titres, interface TikTok) pour la lisibilité."""
    g = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 420)],
                                       [skia.Color(0, 0, 0, 120), skia.Color(0, 0, 0, 0)])
    c.drawRect(skia.Rect(0, 0, W, 420), skia.Paint(Shader=g))
    g = skia.GradientShader.MakeLinear([skia.Point(0, 1300), skia.Point(0, H)],
                                       [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 170)])
    c.drawRect(skia.Rect(0, 1300, W, H), skia.Paint(Shader=g))


# ------------------------------------------------------------------------------------------------ texte
def ligne(c, txt, y, taille, col, k):
    f = skia.Font(FONT, taille)
    w = f.measureText(txt)
    s = E1.pop(k) if k < 0.5 else 1.0
    if s <= 0:
        return
    c.save()
    c.translate(W / 2, y)
    c.scale(s, s)
    c.drawString(txt, -w / 2, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0),
                                                Style=skia.Paint.kStroke_Style, StrokeWidth=taille * 0.16,
                                                StrokeJoin=skia.Paint.kRound_Join))
    c.drawString(txt, -w / 2, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(*col)))
    c.restore()


def accroche(c, t, t_hook):
    a = 1 - min(1, max(0, (t - t_hook) / 0.25))
    if a <= 0:
        return
    c.saveLayerAlpha(None, int(255 * a))
    y0 = 560 if AVEC_ORBE else 330
    ligne(c, "CET AIR A", y0, 58, (255, 255, 255), t / 0.3)
    ligne(c, "2 MILLIONS D'ANNÉES", y0 + 90, 78, (120, 220, 255), (t - 0.2) / 0.3)
    c.restore()


MOTS = []


def preparer_mots(segs):
    MOTS.clear()
    for a, b, txt in segs:
        ws = txt.split()
        lens = [len(re.sub(r"\W", "", w)) + 1.5 for w in ws]
        t = a
        for j, (w, l) in enumerate(zip(ws, lens)):
            d = (b - a) * l / sum(lens)
            MOTS.append((w.upper(), t, t + d, len(MOTS) - j, j))
            t += d



def sous_titres(c, t):
    i = max([k for k, m in enumerate(MOTS) if m[1] <= t + 0.03] + [-1])
    if i < 0 or t > MOTS[i][2] + 0.4:
        return
    deb, rang = MOTS[i][3], MOTS[i][4]
    g0 = deb + (rang // 3) * 3
    grp = [m for m in MOTS[g0:g0 + 3] if m[3] == deb]
    size = 70
    f = skia.Font(FONT, size)
    sp = f.measureText(" ")
    tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    while tot > W - 120:
        size -= 4
        f = skia.Font(FONT, size)
        sp = f.measureText(" ")
        tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    age = t - MOTS[g0][1]
    pop = 1 + 0.12 * math.exp(-age * 12) * math.cos(age * 28) if age < 0.4 else 1.0
    c.save()
    c.translate(W / 2, Y_SUB)
    c.scale(pop, pop)
    x = -tot / 2
    for k, m in enumerate(grp):
        wd = f.measureText(m[0])
        on = g0 + k == i
        c.drawString(m[0], x, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0),
                                               Style=skia.Paint.kStroke_Style, StrokeWidth=13,
                                               StrokeJoin=skia.Paint.kRound_Join))
        c.drawString(m[0], x, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(255, 214, 10) if on else
                                               skia.Color(255, 255, 255)))
        x += wd + sp
    c.restore()


# ------------------------------------------------------------------------------------------------ Orbe
def orbe(c, t, sync, moods, plans):
    """L'Orbe reste fixe en haut à droite ; seuls la bouche, les yeux et les couleurs changent."""
    k = max(i for i, m in enumerate(moods) if m[0] <= t)
    tc, yeux, hum = moods[k]
    hum0 = moods[k - 1][2] if k else hum
    e = Etat(expr="parle", age=t - tc, levres=sync(t), yeux=yeux, humeur=hum, humeur_avant=hum0,
             humeur_mix=min(1.0, (t - tc) / 0.5))
    e.cligne = (t % 3.7) < 0.11
    x, y = ORBE_XY
    d = (W / 2 - x, 900 - y)                                         # il regarde l'image
    n = math.hypot(*d)
    e.regard = (0.5 * d[0] / n, 0.5 * d[1] / n)
    s = ECHELLE_ORBE * (E1.pop(t - 0.3) if t < 0.9 else 1.0)
    if s <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    draw_orbe(c, t, e)
    c.restore()


# ------------------------------------------------------------------------------------------------ rendu
def preparer():
    dur_v, N = construire_voix()
    preparer_mots([(N(a), N(b), txt) for a, b, txt in SEG])
    plans = [(N(p[0]),) + tuple(p[1:]) for p in PLANS]
    moods = [(N(t0), y, h) for t0, y, h in MOODS]
    return dur_v + 0.6, plans, moods, N(T_HOOK)


def image(c, t, plans, moods, sync, t_hook):
    c.clear(skia.Color(0, 0, 0))
    k = montage(c, plans, t)
    voiles(c)
    accroche(c, t, t_hook)
    if t >= t_hook - 0.1:
        sous_titres(c, t)
    if AVEC_ORBE:
        orbe(c, t, sync, moods, plans)
    return k


def render(out):
    dur, plans, moods, t_hook = preparer()
    sync = LV.Synchro(VOIX2)
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(dur * FPS)):
        image(surf.getCanvas(), f / FPS, plans, moods, sync, t_hook)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    fx = [(0.0, E1.swell(0.12), 1.0)]
    for p in plans[1:]:
        if p[6] in ("filé", "zoom"):
            fx.append((p[0] - 0.08, E1.swell(0.07), 1.0))
        elif p[6] == "flash":
            fx.append((p[0], E1.pop_s(780, 0.10), 1.0))
        else:
            fx.append((p[0], E1.pop_s(520, 0.04), 1.0))
    MI.soundtrack(f"{tmp}/a.wav", MI.load_voice(VOIX2), dur, fx)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out, f"{dur:.1f} s")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep16_antarctique.mp4")
