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
