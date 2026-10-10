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
    dist = np.sqrt(((_XX - cx) / rx) ** 2 + ((_YY - cy) / ry) ** 2)
    _appliquer(img, (np.clip(1 - dist, 0, 1) * force) > SEUIL, col)


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
    """La voiture autonome vue de dessus (avant vers le haut), avec capteur, phares et faisceaux."""
    if phares:
        a = math.radians(ang)
        fx, fy = cx + 30 * math.sin(a), cy - 30 * math.cos(a)
        cone(img, (fx, fy), (fx + 150 * math.sin(a), fy - 150 * math.cos(a)), 12, 46, (40, 70, 130), 0.75)
    w, h = 42, 70
    cal = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    d = draw(cal)
    ox, oy = 12, 12
    d.rounded_rectangle((ox + 2, oy + 3, ox + w + 2, oy + h + 3), 10, fill=(4, 8, 20, 200))                   # ombre
    d.rounded_rectangle((ox, oy, ox + w, oy + h), 10, fill=B2, outline=CONTOUR)
    d.rounded_rectangle((ox + 3, oy + 4, ox + w - 3, oy + h - 4), 8, fill=B3)
    d.line([(ox + 5, oy + 6), (ox + 5, oy + h - 8)], fill=B4)                                                  # reflet
    d.polygon([(ox + 6, oy + 19), (ox + w - 6, oy + 19), (ox + w - 9, oy + 28), (ox + 9, oy + 28)], fill=B0)  # pare-brise
    d.line([(ox + 9, oy + 21), (ox + 15, oy + 21)], fill=B2)
    if toit:
        d.rounded_rectangle((ox + 8, oy + 28, ox + w - 8, oy + 51), 3, fill=B2)
        d.rectangle((ox + 17, oy + 33, ox + w - 17, oy + 45), fill=(30, 60, 120))                              # le lidar
        a2 = t * 8
        d.line([(ox + 21, oy + 39), (ox + 21 + 5 * math.cos(a2), oy + 39 + 5 * math.sin(a2))], fill=B4)
    else:
        d.rectangle((ox + 8, oy + 28, ox + w - 8, oy + 51), fill=(6, 14, 34))
        for sx in (ox + 10, ox + w - 19):
            d.rounded_rectangle((sx, oy + 32, sx + 9, oy + 44), 2, fill=GRIS_F, outline=CONTOUR)
            d.rectangle((sx + 1, oy + 32, sx + 8, oy + 34), fill=GRIS)
        cx_, cy_ = ox + 15, oy + 30
        d.ellipse((cx_ - 5, cy_ - 2, cx_ + 5, cy_ + 3), outline=GRIS, width=1)
        a2 = t * 5
        d.line([(cx_ - 4 * math.cos(a2), cy_ - 2 * math.sin(a2)), (cx_ + 4 * math.cos(a2), cy_ + 2 * math.sin(a2))], fill=B4)
    d.polygon([(ox + 9, oy + 51), (ox + w - 9, oy + 51), (ox + w - 6, oy + 59), (ox + 6, oy + 59)], fill=B0)
    for x in (ox + 3, ox + w - 9):
        d.rectangle((x, oy + 1, x + 6, oy + 3), fill=BLANC)
    feu = ROUGE if (alerte and int(t * 8) % 2) or freinage > 0 else ROUGE_F
    for x in (ox + 3, ox + w - 9):
        d.rectangle((x, oy + h - 3, x + 6, oy + h - 1), fill=feu)
    for x, y in ((ox - 2, oy + 10), (ox + w - 1, oy + 10), (ox - 2, oy + h - 22), (ox + w - 1, oy + h - 22)):
        d.rectangle((x, y, x + 3, y + 12), fill=NOIR)
    cal = cal.rotate(-ang, resample=Image.NEAREST, expand=True)
    img.paste(cal, (int(cx - cal.width / 2), int(cy - cal.height / 2)), cal)


def traces(d, x, y0, y1, ecart=14):
    """Traces de pneus (freinage)."""
    for dx in (-ecart, ecart):
        for y in range(int(y0), int(y1), 2):
            d.point((x + dx + (y % 3 == 0), y), fill=(3, 6, 14))
            d.point((x + dx + 1, y), fill=(3, 6, 14))


# ------------------------------------------------------------------------------------------------ intérieurs et ville
def ville_fond(img, t, sol, graine=4, haut=150):
    """Silhouettes d'immeubles de nuit (deux plans), fenêtres allumées."""
    d = draw(img)
    rng = np.random.default_rng(graine)
    for plan, (col, hmin, hmax, fen) in enumerate(((B0, 60, haut, (20, 46, 96)), ((10, 24, 56), 40, haut - 40, B2))):
        x = -10
        while x < LW + 10:
            w = int(rng.integers(26, 50))
            h = int(rng.integers(hmin, hmax))
            d.rectangle((x, sol - h, x + w, sol), fill=col)
            if plan == 0 and rng.uniform() < 0.3:
                d.line([(x + w // 2, sol - h), (x + w // 2, sol - h - 14)], fill=GRIS_F)
                if int(t * 2) % 2:
                    d.point((x + w // 2, sol - h - 15), fill=ROUGE)
            for yy in range(sol - h + 6, sol - 6, 8):
                for xx in range(x + 4, x + w - 4, 7):
                    if rng.uniform() < (0.25 if plan == 0 else 0.45):
                        d.rectangle((xx, yy, xx + 2, yy + 3), fill=fen)
            x += w + int(rng.integers(0, 6))
    return d


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
    d.rectangle((150, 330, 262, 340), fill=(60, 44, 34), outline=CONTOUR)                             # le bureau
    d.rectangle((156, 340, 162, 420), fill=(48, 34, 26))
    d.rectangle((250, 340, 256, 420), fill=(48, 34, 26))
    lumiere(img, 236, 334, 60, 26, (40, 50, 80), 0.9)
    d = draw(img)
    d.line([(244, 330), (238, 306), (226, 300)], fill=GRIS, width=2)                                   # la lampe
    d.polygon([(220, 296), (234, 296), (230, 304), (224, 304)], fill=GRIS_F)
    for k in range(4):                                                                                 # des livres
        d.rectangle((160 + k * 6, 318, 164 + k * 6, 330), fill=(B1, ROUGE_F, B2, GRIS_F)[k], outline=CONTOUR)
    d.rectangle((190, 324, 214, 330), fill=BLANC)                                                      # papiers
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
    texte(d, (ex + ew / 2, ey + 3), "QUE DOIT FAIRE LA VOITURE ?", 8, B4, centre=True)


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
    """Une balance de justice : socle, fléau incliné (ang en degrés, positif = côté droit plus bas), deux plateaux.
    contenu_* : fonction(img, x, y) qui pose quelque chose sur le plateau (pieds en x, y)."""
    d = draw(img)
    d.polygon([(cx - 26, cy + 150), (cx + 26, cy + 150), (cx + 14, cy + 140), (cx - 14, cy + 140)], fill=GRIS_F, outline=CONTOUR)
    d.rectangle((cx - 3, cy, cx + 3, cy + 140), fill=GRIS, outline=CONTOUR)
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=B4, outline=CONTOUR)
    a = math.radians(ang)
    pts = []
    for s in (-1, 1):
        px, py = cx + s * larg * math.cos(a), cy + s * larg * math.sin(a)
        pts.append((px, py))
    d.line([pts[0], pts[1]], fill=B4, width=3)
    for k, (px, py) in enumerate(pts):
        bas = py + 54
        d.line([(px, py), (px - 26, bas)], fill=GRIS)
        d.line([(px, py), (px + 26, bas)], fill=GRIS)
        d.chord((px - 32, bas - 8, px + 32, bas + 10), 0, 180, fill=B2, outline=CONTOUR)
        d.line([(px - 30, bas), (px + 30, bas)], fill=B4)
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
    """Une main qui tient un téléphone (écran renvoyé en coordonnées)."""
    d.rounded_rectangle((cx - w / 2 - 6, cy - h / 2 - 12, cx + w / 2 + 6, cy + h / 2 + 14), 12, fill=(30, 36, 56), outline=CONTOUR)
    d.rounded_rectangle((cx - w / 2 - 4, cy - h / 2 - 10, cx + w / 2 + 4, cy + h / 2 + 12), 10, outline=GRIS_F)
    d.rectangle((cx - 12, cy - h / 2 - 7, cx + 12, cy - h / 2 - 5), fill=NOIR)
    d.rounded_rectangle((cx - 10, cy + h / 2 + 4, cx + 10, cy + h / 2 + 8), 2, fill=GRIS_F)
    for k in range(4):                                                                            # les doigts
        y = cy - 20 + k * 22
        d.rounded_rectangle((cx + w / 2 + 2, y, cx + w / 2 + 16, y + 16), 6, fill=P.PEAU, outline=CONTOUR)
    d.rounded_rectangle((cx - w / 2 - 22, cy + 30, cx - w / 2 + 6, cy + 54), 9, fill=P.PEAU, outline=CONTOUR)   # le pouce
    d.rounded_rectangle((cx + w / 2 - 6, cy + 40, cx + w / 2 + 40, cy + h / 2 + 80), 18, fill=P.PEAU_O, outline=CONTOUR)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
