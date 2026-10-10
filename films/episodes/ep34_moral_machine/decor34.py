"""Décors détaillés de l'épisode 34 (pixel bleu) : lumières tramées, rue de nuit vue de dessus, laboratoire, globe qui
tourne, balance, podium, salon automobile, Bundestag. Toile 270 × 480, palette de films.styles.pixel_bleu."""
import math

import numpy as np
from PIL import Image, ImageDraw

from films.styles import pixel_bleu as P
from films.styles.pixel_bleu import B0, B1, B2, B3, B4, BLANC, GRIS, GRIS_F, NOIR, ROUGE, ROUGE_F

LW, LH = P.LW, P.LH
_YY, _XX = np.mgrid[0:LH, 0:LW]
SEUIL = P.SEUIL
NUIT = (8, 16, 36)
BETON = (22, 34, 62)
CONTOUR = P.CONTOUR


def draw(img):
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    return d


def _appliquer(img, m, col):
    a = np.asarray(img).copy()
    a[m] = col
    img.paste(Image.fromarray(a))


def lumiere(img, cx, cy, rx, ry, col=B1, force=0.8):
    """Une flaque de lumière elliptique tramée (Bayer)."""
    w, h = img.size
    yy, xx = _YY[:h, :w], _XX[:h, :w]
    dist = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    _appliquer(img, (np.clip(1 - dist, 0, 1) * force) > SEUIL[:h, :w], col)


def cone(img, p0, p1, w0, w1, col=B1, force=0.7):
    """Un faisceau (phare, projecteur) de p0 (largeur w0) vers p1 (largeur w1), qui s'éteint en s'éloignant."""
    vx, vy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(vx, vy) + 1e-6
    ux, uy = vx / L, vy / L
    rx, ry = _XX - p0[0], _YY - p0[1]
    tt = (rx * ux + ry * uy) / L
    perp = np.abs(rx * -uy + ry * ux)
    larg = w0 + (w1 - w0) * tt
    v = np.where((tt >= 0) & (tt <= 1), np.clip(1 - perp / np.maximum(larg, 1e-3), 0, 1) ** 0.6 * (1 - tt) * force, 0)
    _appliquer(img, v > SEUIL, col)


def ombre(d, x, y, w=10):
    d.ellipse((x - w, y - 2, x + w, y + 2), fill=(4, 8, 20))


def texte(d, xy, txt, taille=8, col=BLANC, pixel=True, centre=False):
    f = P.police(taille, pixel=pixel)
    x, y = xy
    if centre:
        x -= d.textlength(txt, font=f) / 2
    d.text((x, y), txt, font=f, fill=col)


# ------------------------------------------------------------------------------------------------ rue de nuit (dessus)
def toits(d, x0, x1, t, graine=0):
    """Une rangée d'immeubles vus d'en haut : toits, climatiseurs, cheminées, verrières, petites lumières."""
    rng = np.random.default_rng(graine)
    y = -10
    while y < LH + 10:
        h = int(rng.integers(50, 90))
        c = (int(rng.integers(16, 26)), int(rng.integers(30, 44)), int(rng.integers(64, 86)))
        d.rectangle((x0, y, x1, y + h - 3), fill=c, outline=CONTOUR)
        d.rectangle((x0 + 2, y + 2, x1 - 2, y + 4), fill=tuple(min(255, v + 18) for v in c))     # le rebord éclairé
        for _ in range(int(rng.integers(1, 4))):                                                # climatiseurs
            ax, ay = rng.integers(x0 + 4, max(x0 + 5, x1 - 12)), rng.integers(y + 8, y + h - 16)
            d.rectangle((ax, ay, ax + 9, ay + 7), fill=GRIS_F, outline=CONTOUR)
            a = t * 9 + ax
            d.line([(ax + 4.5 - 3 * math.cos(a), ay + 3.5 - 3 * math.sin(a)),
                    (ax + 4.5 + 3 * math.cos(a), ay + 3.5 + 3 * math.sin(a))], fill=GRIS)
        if rng.uniform() < 0.5:                                                                 # une verrière éclairée
            vx, vy = rng.integers(x0 + 4, max(x0 + 5, x1 - 16)), rng.integers(y + 8, y + h - 18)
            d.rectangle((vx, vy, vx + 12, vy + 9), fill=B3 if int(t * 0.7 + vx) % 5 else B2, outline=CONTOUR)
            d.line([(vx + 6, vy), (vx + 6, vy + 9)], fill=B1)
        if rng.uniform() < 0.6:                                                                 # une cheminée
            cx, cy = rng.integers(x0 + 3, max(x0 + 4, x1 - 6)), y + h - 12
            d.rectangle((cx, cy, cx + 4, cy + 4), fill=GRIS_F)
            if int(t * 2 + cx) % 3 == 0:
                d.point((cx + 2, cy - 2), fill=ROUGE)                                           # balise rouge
        y += h


def route_nuit(img, t, passage, defile=0.0, feu_rouge=True):
    """Avenue de nuit vue de dessus : immeubles, trottoirs, lampadaires (flaques de lumière), marquages, passage."""
    d = draw(img)
    d.rectangle((0, 0, LW, LH), fill=NUIT)
    for y in range(0, LH, 2):                                                                    # grain de l'asphalte
        for x in range((y * 7) % 11, LW, 11):
            d.point((x, y), fill=(12, 22, 46))
    d.rectangle((38, 0, 46, LH), fill=BETON)                                                     # trottoirs
    d.rectangle((224, 0, 232, LH), fill=BETON)
    for y in range(0, LH, 8):
        d.line([(38, y), (46, y)], fill=(30, 44, 76))
        d.line([(224, y), (232, y)], fill=(30, 44, 76))
    d.line([(46, 0), (46, LH)], fill=GRIS_F)
    d.line([(224, 0), (224, LH)], fill=GRIS_F)
    toits(d, 0, 37, t, 1)
    toits(d, 233, LW, t, 2)
    for y in range(int(defile) % 30 - 30, LH, 30):                                               # ligne médiane
        if not (passage - 24 < y < passage + 24):
            d.rectangle((134, y, 136, y + 14), fill=B4)
    for x in (90, 180):                                                                          # lignes de voie
        for y in range(int(defile) % 20 - 20, LH, 20):
            if not (passage - 24 < y < passage + 24):
                d.rectangle((x, y, x + 1, y + 6), fill=(40, 56, 92))
    d.rectangle((47, passage + 26, 223, passage + 28), fill=B4)                                  # ligne d'arrêt
    for x in range(52, 222, 12):                                                                 # bandes du passage
        d.rectangle((x, passage - 18, x + 7, passage + 18), fill=(150, 168, 200))
        d.rectangle((x, passage - 18, x + 7, passage - 17), fill=BLANC)
    for y in (passage - 150, passage + 150):                                                     # lampadaires
        for x, sx in ((44, 1), (226, -1)):
            lumiere(img, x + sx * 26, y, 46, 38, (20, 40, 82), 0.85)
    d = draw(img)
    for y in (passage - 150, passage + 150):
        for x, sx in ((44, 1), (226, -1)):
            d.line([(x, y), (x + sx * 16, y)], fill=GRIS, width=2)
            d.ellipse((x + sx * 16 - 3, y - 3, x + sx * 16 + 3, y + 3), fill=B4, outline=GRIS_F)
    for x, sx in ((44, 1), (226, -1)):                                                           # feux tricolores
        fx, fy = x, passage - 30 * sx
        d.rectangle((fx - 3, fy - 8, fx + 3, fy + 8), fill=NOIR, outline=GRIS_F)
        on = feu_rouge and int(t * 2) % 2
        d.ellipse((fx - 2, fy - 7, fx + 2, fy - 3), fill=ROUGE if on else ROUGE_F)
        d.ellipse((fx - 2, fy + 3, fx + 2, fy + 7), fill=(20, 60, 40))
    return d


def voiture_dessus(img, cx, cy, ang=0.0, alerte=False, t=0.0, toit=True, phares=True, freinage=0.0):
    """La voiture autonome vue de dessus, avec le faisceau de ses phares."""
    from films.episodes.ep34_moral_machine import figures34 as F
    if phares:
        a = math.radians(ang)
        fx, fy = cx + 36 * math.sin(a), cy - 36 * math.cos(a)
        cone(img, (fx, fy), (fx + 150 * math.sin(a), fy - 150 * math.cos(a)), 14, 50, (40, 70, 130), 0.75)
    F.voiture_dessus(img, cx, cy, ang, B2, t, toit, alerte, freinage)


def traces(d, x, y0, y1, ecart=14):
    """Traces de pneus (freinage)."""
    for dx in (-ecart, ecart):
        for y in range(int(y0), int(y1), 2):
            d.point((x + dx + (y % 3 == 0), y), fill=(3, 6, 14))
            d.point((x + dx + 1, y), fill=(3, 6, 14))


# ------------------------------------------------------------------------------------------------ intérieurs et ville
def ville_fond(img, t, sol, graine=4, haut=150):
    """La ville de nuit en deux plans : immeubles aux façades détaillées (étages, encadrements, fenêtres allumées en
    grappes, quelques rideaux), toits avec réservoirs et antennes à balise, brume au pied des immeubles."""
    d = draw(img)
    rng = np.random.default_rng(graine)
    plans = (((12, 26, 58), 60, haut, (34, 66, 130), (60, 100, 180)), ((20, 40, 84), 40, haut - 40, (90, 140, 220), (170, 200, 245)))
    for plan, (col, hmin, hmax, fen, fen_c) in enumerate(plans):
        x = -10
        while x < LW + 10:
            w = int(rng.integers(28, 54))
            h = int(rng.integers(hmin, hmax))
            top = sol - h
            claire = tuple(min(255, c + 10) for c in col)
            sombre = tuple(max(0, c - 6) for c in col)
            d.rectangle((x, top, x + w, sol), fill=col)
            d.rectangle((x + w - max(3, w // 6), top, x + w, sol), fill=sombre)                 # la face à l'ombre
            d.line([(x, top), (x + w, top)], fill=claire)                                     # la corniche
            d.rectangle((x - 1, top - 2, x + w + 1, top), fill=sombre)
            if rng.uniform() < 0.35:                                                          # réservoir d'eau
                tx = x + int(rng.integers(4, max(5, w - 12)))
                d.rectangle((tx, top - 10, tx + 8, top - 3), fill=sombre)
                d.line([(tx + 1, top - 3), (tx + 1, top)], fill=sombre)
                d.line([(tx + 7, top - 3), (tx + 7, top)], fill=sombre)
            if rng.uniform() < 0.3:                                                           # antenne à balise
                ax_ = x + w // 2
                d.line([(ax_, top), (ax_, top - 16)], fill=GRIS_F)
                if int(t * 1.5 + ax_) % 3 == 0:
                    d.point((ax_, top - 17), fill=ROUGE)
            etage = 9 if plan == 0 else 8
            grappe = rng.uniform(0.15, 0.55)
            for yy in range(top + 6, sol - 8, etage):
                d.line([(x + 1, yy + 6), (x + w - 2, yy + 6)], fill=sombre)                    # dalle d'étage
                allume_etage = rng.uniform() < grappe * 1.6
                for xx in range(x + 4, x + w - 5, 6):
                    on = allume_etage and rng.uniform() < 0.7 or rng.uniform() < 0.08
                    if on:
                        c = fen_c if rng.uniform() < 0.25 else fen
                        d.rectangle((xx, yy, xx + 3, yy + 4), fill=c)
                        if rng.uniform() < 0.3:                                               # un rideau à moitié tiré
                            d.line([(xx, yy), (xx, yy + 4)], fill=col)
                    else:
                        d.rectangle((xx, yy, xx + 3, yy + 4), fill=sombre)
            x += w + int(rng.integers(0, 5))
    for k in range(3):                                                                        # brume au sol
        lumiere(img, LW / 2, sol - 4, LW * 0.8, 18 + 6 * k, (22, 40, 80), 0.35)
    return draw(img)


def labo(img, t):
    """Un bureau de chercheur la nuit : grande baie sur la ville, étagères, lampe, tableau couvert de flèches."""
    d = draw(img)
    d.rectangle((0, 0, LW, LH), fill=(10, 20, 44))
    d.rectangle((14, 104, 256, 300), fill=NUIT, outline=GRIS_F)                                      # la baie vitrée
    sous = Image.new("RGB", (240, 194), NUIT)
    ville_fond(sous, t, 194, 7, 120)
    img.paste(sous, (15, 105))
    d = draw(img)
    for x in (95, 175):
        d.line([(x, 104), (x, 300)], fill=GRIS_F, width=2)
    d.line([(14, 200), (256, 200)], fill=GRIS_F)
    d.rectangle((0, 300, LW, 306), fill=GRIS_F)
    d.rectangle((0, 306, LW, LH), fill=(16, 28, 56))                                                  # le sol
    for y in range(316, LH, 14):
        d.line([(0, y), (LW, y)], fill=(20, 34, 66))
    bois, bois_o, bois_c = (74, 54, 44), (44, 32, 28), (110, 84, 66)
    d.rectangle((140, 372, 266, 379), fill=bois, outline=CONTOUR)                                     # le plateau du bureau
    d.line([(141, 373), (265, 373)], fill=bois_c)
    d.rectangle((141, 377, 265, 379), fill=bois_o)
    d.rectangle((146, 379, 152, 432), fill=bois_o, outline=CONTOUR)                                   # pieds
    d.rectangle((222, 379, 262, 404), fill=bois, outline=CONTOUR)                                     # caisson à tiroirs
    d.rectangle((226, 383, 258, 392), outline=bois_o)
    d.rectangle((226, 395, 258, 402), outline=bois_o)
    d.rectangle((238, 387, 246, 388), fill=GRIS)
    d.rectangle((256, 404, 262, 432), fill=bois_o, outline=CONTOUR)
    d.line([(150, 432), (262, 432)], fill=(10, 18, 40))                                               # ombre au sol
    lumiere(img, 236, 370, 50, 22, (46, 56, 86), 0.9)                                                 # le halo de la lampe
    d = draw(img)
    d.line([(252, 371), (256, 352), (244, 340)], fill=GRIS, width=2)                                   # la lampe d'architecte
    d.ellipse((249, 368, 257, 372), fill=GRIS_F, outline=CONTOUR)
    d.polygon([(236, 336), (248, 336), (245, 344), (239, 344)], fill=GRIS_F, outline=CONTOUR)
    d.line([(239, 345), (245, 345)], fill=BLANC)
    for k in range(4):                                                                                 # des livres
        d.rectangle((210 + k * 5, 358 - k % 2 * 2, 214 + k * 5, 371), fill=((40, 60, 110), ROUGE_F, B1, GRIS_F)[k], outline=CONTOUR)
        d.line([(211 + k * 5, 361), (213 + k * 5, 361)], fill=GRIS)
    d.polygon([(228, 369), (246, 367), (248, 370), (230, 372)], fill=(220, 226, 240))                 # papiers
    return d


def ecran_jeu(d, ex, ey, ew, eh, t, choix=None):
    """L'écran de la Moral Machine : deux scénarios de route côte à côte, l'un entouré."""
    d.rectangle((ex, ey, ex + ew, ey + eh), fill=NOIR)
    for k in range(2):
        w = ew / 2 - 6
        x = ex + 4 + k * (w + 4)
        y0, y1 = ey + 16, ey + eh - 12
        d.rectangle((x, y0, x + w, y1), fill=B0, outline=ROUGE if choix == k else B1, width=2 if choix == k else 1)
        rx0, rx1 = x + w * 0.25, x + w * 0.75
        d.rectangle((rx0, y0 + 1, rx1, y1 - 1), fill=NUIT)
        for y in range(int(y0 + 3), int(y1 - 2), 8):
            d.line([((rx0 + rx1) / 2, y), ((rx0 + rx1) / 2, y + 3)], fill=B3)
        for x2 in range(int(rx0) + 1, int(rx1), 4):
            d.rectangle((x2, y0 + 14, x2 + 2, y0 + 20), fill=GRIS_F)
        cxv = (rx0 + rx1) / 2 + (-1 if k == 0 else 1) * (w * 0.12)
        d.rectangle((cxv - 3, y1 - 18, cxv + 3, y1 - 8), fill=B2)                                    # la voiture
        n = 1 if k == 0 else 3
        for j in range(n):
            px = rx0 + 3 + j * 5 if k == 0 else rx1 - 4 - j * 5
            d.rectangle((px, y0 + 13, px + 2, y0 + 19), fill=B4 if k == 0 else GRIS)
            d.point((px + 1, y0 + 11), fill=P.PEAU)
        if choix == k:
            d.line([(cxv, y1 - 18), (cxv + (6 if k else -6), y0 + 22)], fill=ROUGE)                  # la trajectoire
    texte(d, (ex + ew / 2, ey + 3), "QUE DOIT FAIRE LA VOITURE ?" if ew >= 150 else "QUE FAIRE ?", 8, B4, centre=True)


# ------------------------------------------------------------------------------------------------ le globe
def _carte_monde():
    """Masque grossier des continents (équirectangulaire 180 × 90) et groupes (0 ouest, 1 est, 2 sud)."""
    im = Image.new("L", (180, 90), 255)
    d = ImageDraw.Draw(im)
    S = lambda pts: [(x / 270 * 180, y / 190 * 90) for x, y in pts]
    zones = [
        ([(14, 40), (40, 28), (78, 30), (92, 46), (70, 70), (56, 92), (40, 80), (22, 62)], 0),   # Amérique du Nord
        ([(60, 96), (82, 102), (92, 124), (78, 160), (68, 176), (62, 150), (54, 118)], 2),     # Amérique du Sud
        ([(118, 36), (148, 30), (160, 42), (146, 58), (126, 62), (118, 54)], 0),                 # Europe
        ([(120, 70), (156, 68), (170, 92), (160, 130), (146, 150), (134, 122), (118, 92)], 2),   # Afrique
        ([(160, 30), (230, 26), (256, 48), (240, 74), (214, 92), (190, 84), (170, 70), (158, 50)], 1),   # Asie
        ([(160, 70), (184, 72), (182, 92), (166, 88)], 1),                                       # Moyen-Orient
        ([(214, 130), (246, 126), (250, 148), (224, 152)], 0),                                   # Océanie
        ([(70, 18), (96, 14), (100, 26), (80, 30)], 0),                                          # Groenland
        ([(222, 96), (236, 92), (240, 108), (226, 112)], 1),                                     # Asie du Sud-Est
        ([(122, 54), (132, 52), (134, 62), (124, 64)], 3),                                       # France
    ]
    for pts, g in zones:
        d.polygon(S(pts), fill=g)
    return np.asarray(im)


CARTE = _carte_monde()


def globe(img, cx, cy, r, rot, cols=None, france=False, points=0.0, t=0.0):
    """Un globe qui tourne : continents projetés, éclairage tramé, atmosphère, petits points (les décisions)."""
    cols = cols or (B2, B2, B2)
    a = np.asarray(img).copy()
    dx, dy = (_XX - cx) / r, (_YY - cy) / r
    rr = dx * dx + dy * dy
    dans = rr <= 1
    z = np.sqrt(np.clip(1 - rr, 0, 1))
    lat = np.arcsin(np.clip(-dy, -1, 1))
    lon = np.arctan2(dx, z) + rot
    u = ((lon / (2 * math.pi)) % 1 * 180).astype(int) % 180
    v = np.clip(((0.5 - lat / math.pi) * 90).astype(int), 0, 89)
    g = CARTE[v, u]
    lum = np.clip(0.25 + 0.75 * (dx * -0.5 + -dy * 0.4 + z * 0.75), 0, 1)
    a[dans] = (10, 26, 62)
    ocean_clair = dans & (lum > SEUIL * 1.4 + 0.35)
    a[ocean_clair] = (16, 40, 88)
    for k in range(4):
        col = cols[k] if k < 3 else (ROUGE if (france and int(t * 5) % 2) else (BLANC if france else cols[2]))
        m = dans & (g == k)
        a[m] = col
        sombre = m & (lum < SEUIL * 0.9 + 0.1)
        a[sombre] = tuple(int(c * 0.6) for c in col)
    bord = (rr > 1) & (rr < 1.12)
    a[bord & (SEUIL < 0.6)] = (30, 60, 120)
    img.paste(Image.fromarray(a))
    if points > 0:
        d = draw(img)
        rng = np.random.default_rng(int(t * 8))
        for _ in range(int(points)):
            x, y = rng.integers(cx - r, cx + r), rng.integers(cy - r, cy + r)
            if (x - cx) ** 2 + (y - cy) ** 2 < r * r * 0.9 and a[y, x].tolist() in [list(c) for c in cols]:
                d.rectangle((x, y, x + 1, y + 1), fill=BLANC)


def etoiles(d, t, n=60, graine=3):
    rng = np.random.default_rng(graine)
    for _ in range(n):
        x, y, ph = rng.integers(0, LW), rng.integers(0, LH), rng.uniform(0, 6)
        if math.sin(t * 2 + ph) > -0.3:
            d.point((x, y), fill=B3 if math.sin(t * 2 + ph) > 0.6 else B1)


# ------------------------------------------------------------------------------------------------ balance et podium
def balance(img, cx, cy, ang, t, contenu_g=None, contenu_d=None, larg=86):
    """Une balance de justice en métal poli : socle à degrés, colonne cylindrique ombrée, fléau mouluré, chaînes,
    plateaux creux. ang en degrés (positif = côté droit plus bas). contenu_* : fonction(img, x, y)."""
    d = draw(img)
    met, met_o, met_c, met_s = (150, 162, 190), (84, 94, 122), (226, 234, 250), (46, 54, 78)
    # le socle à deux degrés
    d.rounded_rectangle((cx - 34, cy + 142, cx + 34, cy + 152), 3, fill=met_o, outline=CONTOUR)
    d.line([(cx - 32, cy + 143), (cx + 30, cy + 143)], fill=met)
    d.rounded_rectangle((cx - 22, cy + 132, cx + 22, cy + 143), 3, fill=met, outline=CONTOUR)
    d.line([(cx - 20, cy + 133), (cx + 18, cy + 133)], fill=met_c)
    d.rectangle((cx + 8, cy + 134, cx + 21, cy + 142), fill=met_o)
    # la colonne : cylindre (lumière à gauche, ombre à droite), bagues
    d.rectangle((cx - 4, cy + 6, cx + 4, cy + 132), fill=met, outline=CONTOUR)
    d.line([(cx - 2, cy + 8), (cx - 2, cy + 130)], fill=met_c)
    d.rectangle((cx + 2, cy + 8, cx + 3, cy + 130), fill=met_o)
    for y in (cy + 40, cy + 100):
        d.rounded_rectangle((cx - 6, y, cx + 6, y + 4), 1, fill=met, outline=CONTOUR)
        d.line([(cx - 5, y + 1), (cx + 3, y + 1)], fill=met_c)
    a = math.radians(ang)
    pts = [(cx + sg * larg * math.cos(a), cy + sg * larg * math.sin(a)) for sg in (-1, 1)]
    # le fléau : une barre épaisse, effilée vers les bouts, liseré de lumière
    nx, ny = -math.sin(a), math.cos(a)
    for e, col in ((3, CONTOUR), (2, met), (0, met_c)):
        d.line([(pts[0][0] + nx * (e - 2) * 0, pts[0][1] - e * 0), (pts[1][0], pts[1][1])], fill=col, width=max(1, e * 2))
    d.line([(pts[0][0] - nx, pts[0][1] - ny), (pts[1][0] - nx, pts[1][1] - ny)], fill=met_c)
    d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=met, outline=CONTOUR)                 # le pivot
    d.ellipse((cx - 5, cy - 5, cx + 3, cy + 3), fill=met_c)
    d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=met_o)
    d.polygon([(cx - 3, cy - 8), (cx + 3, cy - 8), (cx, cy - 20)], fill=met, outline=CONTOUR)   # l'aiguille
    for k, (px, py) in enumerate(pts):
        d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=met, outline=CONTOUR)
        bas = py + 54
        for sg in (-1, 1):                                          # les chaînes (maillons)
            for j in range(9):
                u0, u1 = j / 9, (j + 0.6) / 9
                d.line([(px + sg * 27 * u0, py + 54 * u0), (px + sg * 27 * u1, py + 54 * u1)], fill=met if j % 2 else met_o)
        d.line([(px, py), (px, bas - 4)], fill=met_s)
        d.chord((px - 34, bas - 9, px + 34, bas + 12), 0, 180, fill=met_o, outline=CONTOUR)   # le plateau creux
        d.chord((px - 32, bas - 7, px + 32, bas + 8), 0, 180, fill=met)
        d.arc((px - 30, bas - 6, px + 30, bas + 7), 20, 90, fill=met_c)
        d.ellipse((px - 34, bas - 3, px + 34, bas + 3), fill=met_s, outline=CONTOUR)        # le dessus du plateau
        d.line([(px - 30, bas - 2), (px + 10, bas - 2)], fill=met_o)
        fn = contenu_g if k == 0 else contenu_d
        if fn:
            fn(img, px, bas)
        d = draw(img)


def podium(d, cx, sol, t):
    """Un podium en marches : 1 au centre, 2 à gauche, 3 à droite, 4 plus bas à droite. Renvoie le dessus de chaque marche."""
    marches = [(cx - 26, 70), (cx - 80, 48), (cx + 28, 34), (cx + 80, 20)]
    tops = []
    for k, (x, h) in enumerate(marches):
        d.rectangle((x, sol - h, x + 52, sol), fill=(24, 48, 100), outline=CONTOUR)
        d.rectangle((x, sol - h, x + 52, sol - h + 3), fill=B3)
        d.rectangle((x + 1, sol - h + 4, x + 3, sol), fill=(36, 70, 140))
        texte(d, (x + 26, sol - h + 6), str(k + 1), 12 if k == 3 else 16, B4, pixel=False, centre=True)
        tops.append((x + 26, sol - h))
    return tops


def salon(img, t, sol=360):
    """Un salon automobile : plateau tournant, projecteurs, public en silhouettes, flashs."""
    d = draw(img)
    d.rectangle((0, 0, LW, LH), fill=(6, 10, 24))
    for k in range(5):
        x = 20 + k * 58
        bal = 26 * math.sin(t * 0.8 + k)
        cone(img, (x, 96), (x + bal, sol), 3, 40, (22, 40, 84), 0.9)
    d = draw(img)
    for k in range(5):
        x = 20 + k * 58
        d.rectangle((x - 5, 90, x + 5, 98), fill=GRIS_F, outline=CONTOUR)
    d.rectangle((0, 86, LW, 90), fill=GRIS_F)
    d.ellipse((30, sol - 14, 240, sol + 14), fill=(22, 40, 84), outline=B2)                        # plateau tournant
    d.ellipse((40, sol - 9, 230, sol + 9), fill=(28, 52, 104))
    d.rectangle((0, sol + 40, LW, LH), fill=(4, 8, 18))
    rng = np.random.default_rng(9)
    for k in range(14):                                                                            # le public
        x = k * 20 + rng.integers(-4, 4)
        y = sol + 60 + rng.integers(0, 14)
        d.ellipse((x - 6, y - 22, x + 6, y - 10), fill=(10, 18, 40))
        d.rounded_rectangle((x - 10, y - 10, x + 10, y + 20), 5, fill=(10, 18, 40))
        if int(t * 3 + k * 1.7) % 9 == 0:                                                          # un flash
            d.rectangle((x - 3, y - 18, x + 3, y - 14), fill=BLANC)
            lumiere(img, x, y - 16, 22, 22, (60, 80, 120), 0.7)
            d = draw(img)
    return d


def bundestag(img, t):
    """Le Reichstag (Berlin) de nuit : façade à colonnes, coupole de verre, drapeaux."""
    d = draw(img)
    d.rectangle((0, 0, LW, LH), fill=(8, 14, 32))
    etoiles(d, t, 40)
    sol = 330
    d.rectangle((0, sol, LW, LH), fill=(10, 20, 40))
    d.rectangle((20, 220, 250, sol), fill=(40, 52, 82), outline=CONTOUR)                          # le corps du bâtiment
    for x0 in (20, 220):
        d.rectangle((x0, 190, x0 + 30, sol), fill=(48, 60, 92), outline=CONTOUR)                  # les tours d'angle
        d.rectangle((x0 + 4, 186, x0 + 26, 190), fill=GRIS_F)
    d.polygon([(90, 220), (135, 196), (180, 220)], fill=(52, 64, 98), outline=CONTOUR)            # le fronton
    for k in range(6):                                                                            # les colonnes
        x = 96 + k * 16
        d.rectangle((x, 222, x + 6, 300), fill=(84, 96, 128))
        d.line([(x + 1, 222), (x + 1, 300)], fill=(120, 132, 160))
    d.rectangle((90, 300, 180, 306), fill=GRIS_F)
    for y in range(236, 300, 18):                                                                 # fenêtres éclairées
        for x in list(range(28, 86, 12)) + list(range(186, 244, 12)):
            d.rectangle((x, y, x + 5, y + 9), fill=B3 if (x + y) % 5 else B2)
    d.chord((100, 150, 170, 220), 180, 360, fill=(30, 60, 120), outline=B3)                       # la coupole de verre
    for k in range(1, 6):
        x = 100 + k * 70 / 6
        d.line([(x, 185 - 30 * math.sin(math.pi * k / 6) + 30), (x, 185)], fill=B3)
    lumiere(img, 135, 180, 50, 40, (40, 80, 150), 0.6)
    d = draw(img)
    d.chord((100, 150, 170, 220), 180, 360, outline=B4)
    for x0 in (35, 235):                                                                          # les drapeaux
        d.line([(x0, 150), (x0, 190)], fill=GRIS)
        ond = math.sin(t * 4 + x0) * 2
        for k, c in enumerate(((10, 10, 10), ROUGE_F, (220, 180, 40))):
            d.polygon([(x0, 150 + 5 * k), (x0 + 20, 150 + 5 * k + ond), (x0 + 20, 155 + 5 * k + ond), (x0, 155 + 5 * k)], fill=c)
    lumiere(img, 135, sol + 6, 120, 20, (24, 40, 76), 0.8)
    return draw(img)


def telephone(img, d, cx, cy, w, h, t):
    """Une main gauche qui tient un smartphone, la nuit : seule la lumière de l'écran l'éclaire. Le pouce longe le bord
    gauche, le bout des quatre doigts dépasse du bord droit, la paume et le poignet sortent par le bas."""
    pb, po, pc = (132, 152, 198), (84, 100, 146), (180, 198, 236)
    x0, x1, y0, y1 = cx - w / 2 - 7, cx + w / 2 + 7, cy - h / 2 - 13, cy + h / 2 + 15
    # la paume et le poignet, sous le téléphone
    d.polygon([(x0 + 10, y1 - 40), (x1 + 6, y1 - 70), (x1 + 16, y1 + 10), (x1 + 6, LH + 2), (x0 + 30, LH + 2), (x0 - 4, y1 + 6)],
              fill=po, outline=CONTOUR)
    d.line([(x0 + 4, y1 + 4), (x0 + 30, LH)], fill=pb)                                                  # tranche éclairée
    # le téléphone : coque, bord métal, encoche, bouton
    d.rounded_rectangle((x0, y0, x1, y1), 13, fill=(26, 30, 44), outline=CONTOUR)
    d.rounded_rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), 12, outline=(110, 118, 142))
    d.line([(x0 + 2, y0 + 16), (x0 + 2, y1 - 16)], fill=(160, 168, 192))
    d.rounded_rectangle((cx - 14, y0 + 5, cx + 14, y0 + 9), 2, fill=NOIR)
    d.point((cx + 8, y0 + 7), fill=(40, 60, 110))
    d.rectangle((x1, cy - h * 0.3, x1 + 2, cy - h * 0.18), fill=(90, 96, 120))
    # le bout des quatre doigts sur le bord droit : arrondis, ongle, séparés par une ombre
    for k in range(4):
        y = cy + h * 0.02 + k * 17
        d.rounded_rectangle((x1 - 6, y, x1 + 7, y + 15), 7, fill=pb, outline=CONTOUR)
        d.rectangle((x1 + 2, y + 2, x1 + 6, y + 13), fill=po)                                            # côté à l'ombre
        d.rounded_rectangle((x1 - 5, y + 3, x1 - 1, y + 11), 2, fill=pc)                                  # l'ongle
        d.line([(x1 - 4, y + 4), (x1 - 4, y + 9)], fill=BLANC)
    # le pouce, posé le long du bord gauche
    d.rounded_rectangle((x0 - 9, cy + h * 0.06, x0 + 8, cy + h * 0.44), 8, fill=pb, outline=CONTOUR)
    d.rectangle((x0 - 8, cy + h * 0.08, x0 - 4, cy + h * 0.42), fill=po)
    d.rounded_rectangle((x0 + 1, cy + h * 0.07, x0 + 6, cy + h * 0.15), 2, fill=pc)                       # l'ongle du pouce
    d.line([(x0 + 3, cy + h * 0.2), (x0 + 3, cy + h * 0.4)], fill=pc)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def teinte_(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)
