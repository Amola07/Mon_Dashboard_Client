"""« Oscilloscope 2.0 » : notre style à nous, rendu plus beau avec des idées tirées des vrais écrans vectoriels.

  - le quadrillage de l'écran (graticule) : fin, discret, avec ses graduations ; il structure l'image ;
  - des volumes en hachures de faisceau : les objets importants sont remplis de lignes parallèles serrées ;
  - un texte écrit par le faisceau (police Hershey à un seul trait) ; les chiffres en segments, comme un instrument ;
  - une hiérarchie de traits : le sujet épais et brillant, le décor fin et sombre, une seule chose en ambre ;
  - une image nette : cœur de trait net, halo court, traînée très brève, lignes de balayage presque invisibles.

    pip install Hershey-Fonts
"""
import math
import unicodedata

import numpy as np
import skia
from HersheyFonts import HersheyFonts

W, H = 1080, 1920
VERT = (90, 255, 140)
VERT_SOMBRE = (30, 110, 64)
VERT_PALE = (200, 255, 215)
AMBRE = (255, 196, 90)
FOND_CENTRE, FOND_BORD = (8, 26, 16), (1, 6, 3)


def peinture(col, w, a=1.0, flou=0.0, plein=False):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*col, int(255 * max(0.0, min(1.0, a)))))
    if not plein:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if flou:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, flou))
    return p


# ------------------------------------------------------------------------------------------------ traits
def chemin(traits):
    p = skia.Path()
    for l in traits:
        if len(l) < 2:
            continue
        p.moveTo(*l[0])
        for q in l[1:]:
            p.lineTo(*q)
    return p


def lisser(l, n=2):
    """Courbe lissée (Chaikin) : les lignes brisées deviennent des courbes."""
    for _ in range(n):
        if len(l) < 3:
            return l
        m = [l[0]]
        for a, b in zip(l, l[1:]):
            m += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        m.append(l[-1])
        l = m
    return l


def partiel(traits, u):
    """Les traits tracés jusqu'à la fraction u de leur longueur totale (dans l'ordre), et la position du faisceau."""
    if u >= 1:
        return traits, None
    longs = [sum(math.dist(p, q) for p, q in zip(l, l[1:])) for l in traits]
    reste = sum(longs) * max(0.0, u)
    out, tete = [], None
    for l, L in zip(traits, longs):
        if reste <= 0:
            break
        if reste >= L:
            out.append(l)
            reste -= L
            continue
        m = [l[0]]
        for p, q in zip(l, l[1:]):
            d = math.dist(p, q)
            if reste >= d:
                m.append(q)
                reste -= d
            else:
                k = reste / d if d else 0
                tete = (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)
                m.append(tete)
                reste = 0
                break
        out.append(m)
    return out, tete


def dessiner(c, traits, col=VERT, w=3.0, a=1.0, u=1.0):
    """Un trait de faisceau net : halo court, trait, cœur presque blanc ; point brillant en tête si u < 1."""
    traits, tete = partiel(traits, u)
    p = chemin(traits)
    c.drawPath(p, peinture(col, w * 3.2, 0.28 * a, flou=w * 1.6))
    c.drawPath(p, peinture(col, w, a))
    blanc = tuple(int(v + (255 - v) * 0.65) for v in col)
    c.drawPath(p, peinture(blanc, max(1.0, w * 0.38), 0.85 * a))
    if tete:
        c.drawCircle(*tete, w * 2.2, peinture((255, 255, 255), 0, 0.9 * a, flou=w, plein=True))


def contours(path, pas=5.0):
    """Les contours d'un chemin skia en lignes brisées (pour les tracer au faisceau ou les transformer)."""
    out = []
    m = skia.PathMeasure(path, False)
    while True:
        L = m.getLength()
        if L > 0:
            n = max(2, int(L / pas))
            pts = []
            for i in range(n + 1):
                pos = m.getPosTan(L * i / n)[0]
                pts.append((pos.x(), pos.y()))
            out.append(pts)
        if not m.nextContour():
            break
    return out


def hachures(c, path, col=AMBRE, pas=7.0, angle=-35, w=1.6, a=0.8, u=1.0):
    """Remplit le chemin de lignes parallèles serrées (comme un écran vectoriel) ; u : le balayage avance."""
    if u <= 0:
        return
    b = path.computeTightBounds()
    cx, cy = b.centerX(), b.centerY()
    R = math.hypot(b.width(), b.height()) / 2 + pas
    ang = math.radians(angle)
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    lignes = skia.Path()
    n = int(2 * R / pas)
    for i in range(int(n * min(1.0, u)) + 1):
        o = -R + i * pas
        lignes.moveTo(cx + nx * o - dx * R, cy + ny * o - dy * R)
        lignes.lineTo(cx + nx * o + dx * R, cy + ny * o + dy * R)
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    c.drawPath(lignes, peinture(col, w * 2.6, 0.18 * a, flou=w * 1.4))
    c.drawPath(lignes, peinture(col, w, a))
    c.restore()


# ------------------------------------------------------------------------------------------------ texte au faisceau
_POLICE = HersheyFonts()
_POLICE.load_default_font("futural")
_POLICE.normalize_rendering(100)
ACCENTS = {"́": "aigu", "̀": "grave", "̂": "circ", "̈": "trema", "̧": "cedille"}


def _avance(txt):
    """Avance horizontale (unités Hershey) du texte : position de début d'un « I » placé après."""
    ref = max(p[0] for l in _POLICE.strokes_for_text("I") for p in l)
    return max(p[0] for l in _POLICE.strokes_for_text(txt + "I") for p in l) - ref     # le « I » est le dernier tracé


def texte(txt, x, y, h=60, centre=True, gras=False):
    """Le texte en traits (police Hershey à un seul trait), ligne de base en y, hauteur des capitales h."""
    k = h / 75.0
    base = ""
    marques = []
    for ch in txt:
        dec = unicodedata.normalize("NFD", ch)
        lettre = dec[0]
        for m in dec[1:]:
            if m in ACCENTS:
                marques.append((len(base), lettre, ACCENTS[m]))
        base += lettre
    largeur = _avance(base) * k
    x0 = x - largeur / 2 if centre else x
    traits = [[(x0 + px * k, y - (py - 25) * k) for px, py in l] for l in _POLICE.strokes_for_text(base)]
    for i, lettre, genre in marques:                      # les accents, que la police n'a pas
        a0, a1 = _avance(base[:i]) * k, _avance(base[:i + 1]) * k
        cxl = x0 + (a0 + a1) / 2
        haut = y - (75 if lettre.isupper() else 50) * k - 8 * k
        e = 9 * k
        if genre == "aigu":
            traits.append([(cxl - e * 0.3, haut), (cxl + e * 0.7, haut - e)])
        elif genre == "grave":
            traits.append([(cxl + e * 0.3, haut), (cxl - e * 0.7, haut - e)])
        elif genre == "circ":
            traits.append([(cxl - e, haut), (cxl, haut - e), (cxl + e, haut)])
        elif genre == "trema":
            traits += [[(cxl - e * 0.6, haut - e * 0.5), (cxl - e * 0.6, haut - e * 0.3)],
                       [(cxl + e * 0.6, haut - e * 0.5), (cxl + e * 0.6, haut - e * 0.3)]]
        elif genre == "cedille":
            traits.append([(cxl, y), (cxl + e * 0.5, y + e * 0.6), (cxl - e * 0.3, y + e * 1.1)])
    if gras:                                              # gras : le même tracé doublé et décalé d'un pixel
        traits = traits + [[(px + 1.6, py) for px, py in l] for l in traits]
    return traits


def largeur_texte(txt, h=60):
    return _avance(unicodedata.normalize("NFD", txt).encode("ascii", "ignore").decode()) * h / 75.0


# ------------------------------------------------------------------------------------------------ chiffres en segments
SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
       "8": "abcdefg", "9": "abcdfg", "-": "g", " ": ""}


def segments(txt, x, y, h=120, centre=True):
    """Chiffres d'afficheur à 7 segments (penchés), y = bas des chiffres."""
    lw = h * 0.5
    pas = lw * 1.45
    total = pas * len(txt) - (pas - lw)
    x0 = x - total / 2 if centre else x
    out = []
    pente = 0.12
    for i, ch in enumerate(txt):
        ox = x0 + i * pas
        def P(u, v):                                      # u : 0..1 de gauche à droite ; v : 0 en bas, 1 en haut
            return (ox + u * lw + v * h * pente, y - v * h)
        g = 0.06
        segs = {"a": [P(g, 1), P(1 - g, 1)], "b": [P(1, 1 - g), P(1, 0.5 + g)], "c": [P(1, 0.5 - g), P(1, g)],
                "d": [P(g, 0), P(1 - g, 0)], "e": [P(0, 0.5 - g), P(0, g)], "f": [P(0, 1 - g), P(0, 0.5 + g)],
                "g": [P(g, 0.5), P(1 - g, 0.5)]}
        if ch == ".":
            out.append([P(0.4, 0), P(0.45, 0.04)])
            continue
        for s in SEG.get(ch, ""):
            out.append(segs[s])
    return out


def largeur_segments(txt, h=120):
    lw = h * 0.5
    return lw * 1.45 * len(txt) - lw * 0.45


# ------------------------------------------------------------------------------------------------ l'écran
MARGE, COLS, LIGNES = 60, 8, 14


def ecran(c, t):
    """Fond (dégradé sombre), quadrillage de l'oscilloscope avec graduations sur les axes centraux."""
    g = skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.42), 1250,
                                       [skia.Color(*FOND_CENTRE), skia.Color(*FOND_BORD)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))
    x0, y0, x1, y1 = MARGE, MARGE * 2, W - MARGE, H - MARGE * 2
    dx, dy = (x1 - x0) / COLS, (y1 - y0) / LIGNES
    fin = peinture(VERT_SOMBRE, 1.2, 0.22)
    for i in range(COLS + 1):
        c.drawLine(x0 + i * dx, y0, x0 + i * dx, y1, fin)
    for j in range(LIGNES + 1):
        c.drawLine(x0, y0 + j * dy, x1, y0 + j * dy, fin)
    gr = peinture(VERT_SOMBRE, 1.4, 0.4)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for i in range(COLS * 5 + 1):
        x = x0 + i * dx / 5
        c.drawLine(x, cy - 7, x, cy + 7, gr)
    for j in range(LIGNES * 5 + 1):
        y = y0 + j * dy / 5
        c.drawLine(cx - 7, y, cx + 7, y, gr)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 - 14, y0 - 14, x1 + 14, y1 + 14), 36, 36), peinture(VERT_SOMBRE, 2, 0.3))


_YY, _XX = np.mgrid[0:H, 0:W]
_VIGN = (1 - 0.38 * (((_XX - W / 2) / (W / 2)) ** 2 + ((_YY - H / 2) / (H / 2)) ** 2)).clip(0.45, 1).astype(np.float32)


def finition(img, t, fps=30):
    """Vignette, lignes de balayage presque invisibles, grain fin (sur un tableau numpy RGBA ou BGRA)."""
    a = img.astype(np.float32)
    a[..., :3] *= _VIGN[..., None]
    a[::3, :, :3] *= 0.94
    g = np.random.default_rng(int(t * fps)).normal(0, 2.5, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    a[..., :3] += g
    return np.clip(a, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------------------------------------ icônes → vecteurs
# Les icônes pixel générées (films/illustrations_pixel/px_*.png, palette pixel_info.PALETTE_ICONES) deviennent des
# formes vectorielles lissées, remplies de hachures : orange → ambre, bleu-vert → vert, blanc et gris → vert pâle ;
# les tons sombres reçoivent des hachures croisées (le volume), les tons clairs des hachures plus espacées.
import os as _os

_ICI = _os.path.dirname(_os.path.abspath(__file__))
_DOSSIER_PX = _os.path.join(_ICI, "..", "illustrations_pixel")
# (famille, ton) pour chaque couleur de la palette des icônes, dans l'ordre de PALETTE_ICONES
_FAMILLES = {(40, 175, 175): ("vert", 1), (26, 110, 112): ("vert", 2), (14, 52, 56): ("vert", 3),
             (128, 214, 214): ("vert", 0), (255, 138, 61): ("ambre", 1), (255, 196, 140): ("ambre", 0),
             (168, 72, 26): ("ambre", 2), (236, 242, 240): ("pale", 0), (120, 130, 132): ("pale", 2),
             (188, 198, 198): ("pale", 1), (66, 76, 80): ("pale", 3)}
COULEURS = {"vert": VERT, "ambre": AMBRE, "pale": VERT_PALE}
_VECT = {}


def _contours_masque(m, ech, lisse_n=2):
    import cv2
    grand = cv2.resize(m.astype(np.uint8) * 255, (m.shape[1] * 8, m.shape[0] * 8), interpolation=cv2.INTER_NEAREST)
    grand = cv2.GaussianBlur(grand, (0, 0), 4)
    _, grand = cv2.threshold(grand, 127, 255, cv2.THRESH_BINARY)
    cs, _ = cv2.findContours(grand, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    for cnt in cs:
        if cv2.contourArea(cnt) < 40:
            continue
        cnt = cv2.approxPolyDP(cnt, 2.5, True)[:, 0, :].astype(float) / 8 * ech
        pts = [tuple(p) for p in cnt] + [tuple(cnt[0])]
        out.append(lisser(pts, lisse_n))
    return out


_DOSSIER_VX = _os.path.join(_ICI, "..", "illustrations_vecteur")


def icone_vecteur(nom):
    """{famille: {ton: [contours]}}, contour de la silhouette, (largeur, hauteur) en pixels de l'icône.
    Prend la version précise (films/illustrations_vecteur, tirée de la planche en pleine définition) si elle existe."""
    if nom not in _VECT and _os.path.exists(_os.path.join(_DOSSIER_VX, nom + ".json")):
        import json as _json
        d = _json.load(open(_os.path.join(_DOSSIER_VX, nom + ".json")))
        zones = {f: {int(t): [[tuple(p) for p in l] for l in ls] for t, ls in z.items()} for f, z in d["zones"].items()}
        _VECT[nom] = (zones, [[tuple(p) for p in l] for l in d["silhouette"]], tuple(d["taille"]))
    if nom not in _VECT:
        from PIL import Image
        a = np.asarray(Image.open(_os.path.join(_DOSSIER_PX, nom + ".png")).convert("RGBA"))
        rgb, al = a[..., :3], a[..., 3] > 0
        zones = {}
        for col, (fam, ton) in _FAMILLES.items():
            m = al & np.all(rgb == np.array(col, np.uint8), axis=2)
            if m.sum() >= 3:
                zones.setdefault(fam, {})[ton] = _contours_masque(m, 1.0)
        _VECT[nom] = (zones, _contours_masque(al, 1.0, 3), (a.shape[1], a.shape[0]))
    return _VECT[nom]


def _place(traits, x0, y0, k):
    return [[(x0 + px * k, y0 + py * k) for px, py in l] for l in traits]


def _chemin_plein(traits):
    p = chemin([l for l in traits])
    p.close()
    p.setFillType(skia.PathFillType.kEvenOdd)
    return p


ANGLES = {"vert": 0, "ambre": -35, "pale": 35}


def silhouette(nom, cx, bas, hauteur):
    """Le contour extérieur de l'icône, placé (pour les transformations d'un dessin en un autre)."""
    zones, sil, (lw, lh) = icone_vecteur(nom)
    k = hauteur / lh
    return _place(sil, cx - lw * k / 2, bas - hauteur, k)


def hauteur_pour(nom, largeur):
    _, _, (lw, lh) = icone_vecteur(nom)
    return largeur * lh / lw


def dessiner_icone_sobre(c, nom, cx, bas, hauteur, a=1.0, u=1.0, hach=("ambre",)):
    """Version sobre : silhouette au faisceau, contours des grandes zones en trait fin, hachures sur les familles
    de couleur de `hach` (l'ambre seulement par défaut)."""
    zones, sil, (lw, lh) = icone_vecteur(nom)
    k = hauteur / lh
    x0, y0 = cx - lw * k / 2, bas - hauteur
    pas = max(6.0, hauteur / 40)
    for fam, tons in zones.items():
        traits = [l for tr in tons.values() for l in tr if _aire(l) * k * k > 900]
        if not traits:
            continue
        pl = _place(traits, x0, y0, k)
        if fam in hach:
            hachures(c, _chemin_plein(pl), COULEURS[fam], pas, ANGLES[fam] or -35, 1.6,
                     (0.8 if fam == "ambre" else 0.45) * a, u)
            dessiner(c, pl, COULEURS[fam], 2.2 if fam == "ambre" else 1.6, a, u)
        else:
            dessiner(c, pl, COULEURS[fam], 1.3, 0.4 * a, u)
    contour = _place(sil, x0, y0, k)
    dessiner(c, contour, VERT_PALE, 2.8, a, u)
    return contour


def _aire(l):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(l, l[1:]))) / 2


def dessiner_icone(c, nom, cx, bas, hauteur, a=1.0, u=1.0, miroir=False):
    """Une icône en vecteurs : zones hachurées par couleur et par ton, silhouette au faisceau. Renvoie la silhouette."""
    zones, sil, (lw, lh) = icone_vecteur(nom)
    k = hauteur / lh
    x0, y0 = cx - lw * k / 2, bas - hauteur
    pas_base = max(5.0, hauteur / 46)
    for fam, tons in zones.items():
        col = COULEURS[fam]
        for ton, traits in tons.items():
            p = _chemin_plein(_place(traits, x0, y0, k))
            pas = pas_base * (1.7 if ton == 0 else 1.0)
            O_a = (0.55 if ton == 0 else 0.75) * a
            hachures(c, p, col, pas, ANGLES[fam], 1.5, O_a, u)
            if ton >= 2:                                   # l'ombre : hachures croisées
                hachures(c, p, col, pas * 1.3, ANGLES[fam] + 90, 1.3, 0.55 * a, u)
            dessiner(c, _place(traits, x0, y0, k), col, 1.4, 0.45 * a, u)
    contour = _place(sil, x0, y0, k)
    dessiner(c, contour, VERT_PALE, 2.6, a, u)
    return contour
