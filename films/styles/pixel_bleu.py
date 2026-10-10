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


# ------------------------------------------------------------------------------------------------ personnages détaillés
# Un vrai sprite : membres en deux segments (coude, genou par cinématique inverse), vêtements ombrés en 3-4 tons,
# chaussures, ceinture, col, cheveux, oreille, nez ; contour sombre d'un pixel calculé automatiquement autour de tout.
CONTOUR = (4, 8, 22)
PEAU, PEAU_O = (214, 232, 255), (150, 186, 236)
TENUES = {
    "pull": {"haut": (B2, B1, B3), "bas": (B0, (10, 30, 70), B1), "cheveux": (12, 22, 48)},
    "gris": {"haut": (GRIS, GRIS_F, (190, 198, 214)), "bas": (B1, B0, B2), "cheveux": (40, 34, 30)},
    "clair": {"haut": (B3, B2, B4), "bas": (GRIS_F, (50, 56, 70), GRIS), "cheveux": (70, 52, 30)},
    "costume": {"haut": ((24, 30, 52), (12, 16, 30), (52, 62, 96)), "bas": ((24, 30, 52), (12, 16, 30), (52, 62, 96)),
                "cheveux": (12, 22, 48)},
}


def _ik(a, cible, l1, l2, sens=1):
    """Cinématique inverse à deux segments : renvoie l'articulation (coude ou genou) entre a et cible."""
    dx, dy = cible[0] - a[0], cible[1] - a[1]
    dist = max(1e-6, min(l1 + l2 - 1e-3, math.hypot(dx, dy)))
    ang = math.atan2(dy, dx)
    c = max(-1.0, min(1.0, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)))
    b = ang - sens * math.acos(c)
    return a[0] + l1 * math.cos(b), a[1] + l1 * math.sin(b)


def _membre(d, p, q, w0, w1, cols):
    """Un segment de membre fuselé et ombré : base, ombre côté dos, reflet côté face."""
    base, ombre, reflet = cols
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    nx, ny = -math.sin(ang), math.cos(ang)
    pts = [(p[0] + nx * w0 / 2, p[1] + ny * w0 / 2), (q[0] + nx * w1 / 2, q[1] + ny * w1 / 2),
           (q[0] - nx * w1 / 2, q[1] - ny * w1 / 2), (p[0] - nx * w0 / 2, p[1] - ny * w0 / 2)]
    d.polygon(pts, fill=base)
    for (x, y), w in ((p, w0), (q, w1)):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=base)
    d.line([(p[0] - nx * (w0 / 2 - 1), p[1] - ny * (w0 / 2 - 1)), (q[0] - nx * (w1 / 2 - 1), q[1] - ny * (w1 / 2 - 1))],
           fill=ombre, width=max(1, int(w0 / 3)))
    d.line([(p[0] + nx * (w0 / 2 - 1), p[1] + ny * (w0 / 2 - 1)), (q[0] + nx * (w1 / 2 - 1), q[1] + ny * (w1 / 2 - 1))],
           fill=reflet, width=1)


def personnage(img, pieds, taille=92, tronc=0.0, mains=None, flexion=0.0, tete=None, assis=False, tenue="pull",
               rotation=0.0, sens=1, marche=None, miroir=False):
    """Dessine un personnage détaillé, pieds au point `pieds` (sur `img`, image PIL RGB).
    tronc : inclinaison en degrés (négatif = penché en arrière vers la gauche) ; mains : (x, y) visé par les deux
    mains, ou None (bras ballants) ; flexion : 0..1 (jambes) ; rotation : tout le corps tourne (vol)."""
    from PIL import ImageDraw
    s = taille / 92
    T_ = TENUES[tenue]
    L = int(taille * 2.2)
    cal = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(cal)
    ox, oy = L / 2 - pieds[0], L * 0.78 - pieds[1]               # repère local : pieds vers le bas du calque
    P_ = lambda x, y: (x + ox, y + oy)
    px, py = pieds
    cuisse, tibia, buste, bras1, bras2 = 22 * s, 21 * s, 28 * s, 14 * s, 13 * s
    if assis:
        hanche = (px - 16 * s, py - 24 * s)
        pied_av, pied_ar = (px + 12 * s, py), (px + 7 * s, py)
    elif marche is not None:                                     # la marche : les pieds alternent, le corps rebondit
        ph = marche
        hanche = (px, py - (cuisse + tibia) * (0.9 + 0.04 * abs(math.cos(ph))))      # le corps monte et descend
        pied_av = (px + 15 * s * math.sin(ph), py - 8 * s * max(0.0, math.cos(ph)))  # le pied qui passe se lève
        pied_ar = (px - 15 * s * math.sin(ph), py - 8 * s * max(0.0, -math.cos(ph)))
        tronc = tronc + 4                                                             # léger penché vers l'avant
    else:
        hanche = (px - 9 * s * flexion - 1, py - (cuisse + tibia) * (0.97 - 0.2 * flexion))
        pied_av, pied_ar = (px + 7 * s, py), (px - 9 * s, py)
    a = math.radians(tronc)
    epaule = (hanche[0] + buste * math.sin(a), hanche[1] - buste * math.cos(a))
    ta = a if tete is None else math.radians(tete)
    cou = (epaule[0] + 3 * s * math.sin(a), epaule[1] - 3 * s * math.cos(a))
    tc = (cou[0] + 8 * s * math.sin(ta), cou[1] - 8 * s * math.cos(ta))
    if mains is None:
        bal = 7 * s * math.sin(-marche) if marche is not None else 0.0
        main_av = (epaule[0] + 4 * s + bal, epaule[1] + 24 * s)
        main_ar = (epaule[0] - 1 * s - bal, epaule[1] + 24 * s)
    else:
        main_av, main_ar = mains, (mains[0] - 2 * s, mains[1] + 2 * s)
    h, b = T_["haut"], T_["bas"]
    sombre = lambda c: tuple(int(v * 0.72) for v in c)
    # le côté éloigné (plus sombre) : jambe arrière, bras arrière
    g = _ik(hanche, pied_ar, cuisse, tibia, sens=1)
    _membre(d, P_(*hanche), P_(*g), 9 * s, 7.5 * s, tuple(sombre(c) for c in b))
    _membre(d, P_(*g), P_(*pied_ar), 7.5 * s, 6 * s, tuple(sombre(c) for c in b))
    _chaussure(d, P_(*pied_ar), s, sombre((30, 36, 56)))
    c_ = _ik(epaule, main_ar, bras1, bras2, sens=1)
    _membre(d, P_(*epaule), P_(*c_), 7 * s, 6 * s, tuple(sombre(c) for c in h))
    _membre(d, P_(*c_), P_(*main_ar), 6 * s, 5 * s, tuple(sombre(c) for c in h))
    _main(d, P_(*main_ar), s, PEAU_O)
    # le buste : pull ombré, ceinture, col
    _membre(d, P_(*hanche), P_(*epaule), 15 * s, 17 * s, h)
    d.line([P_(hanche[0] - 6 * s * math.cos(a), hanche[1] - 6 * s * math.sin(a) - 1),
            P_(hanche[0] + 7 * s * math.cos(a), hanche[1] + 7 * s * math.sin(a) - 1)], fill=CONTOUR, width=max(1, int(2 * s)))
    # la jambe avant
    g = _ik(hanche, pied_av, cuisse, tibia, sens=1)
    _membre(d, P_(*hanche), P_(*g), 10 * s, 8 * s, b)
    _membre(d, P_(*g), P_(*pied_av), 8 * s, 6.5 * s, b)
    _chaussure(d, P_(*pied_av), s, (30, 36, 56))
    # la tête : cou, visage, cheveux, oreille, nez
    _membre(d, P_(*epaule), P_(*cou), 6 * s, 6 * s, (PEAU_O, PEAU_O, PEAU))
    r = 8 * s
    X, Y = P_(*tc)
    d.ellipse((X - r, Y - r * 1.05, X + r, Y + r * 1.05), fill=PEAU)
    d.ellipse((X - r, Y - r * 1.05, X + r * 0.2, Y + r * 1.05), fill=PEAU_O)
    d.ellipse((X - r * 0.3, Y - r * 1.05, X + r, Y + r * 0.9), fill=PEAU)
    nx_, ny_ = X + r * math.cos(ta) * 1.0, Y + r * math.sin(ta) * 1.0 + 1
    d.polygon([(nx_ - 1, ny_ - 2), (nx_ + 2 * s, ny_ + 1), (nx_ - 1, ny_ + 2)], fill=PEAU)
    cheveux = T_["cheveux"]
    d.chord((X - r - 1, Y - r * 1.15 - 1, X + r + 1, Y + r * 0.6), 150 + math.degrees(ta), 360 + math.degrees(ta) - 10,
            fill=cheveux)
    d.ellipse((X - r * 0.35, Y - 2 * s, X + r * 0.1, Y + 2 * s), fill=PEAU_O)       # l'oreille
    # le bras avant, par-dessus tout
    c_ = _ik(epaule, main_av, bras1, bras2, sens=1)
    _membre(d, P_(*epaule), P_(*c_), 8 * s, 7 * s, h)
    _membre(d, P_(*c_), P_(*main_av), 7 * s, 5.5 * s, h)
    _main(d, P_(*main_av), s, PEAU)
    # le contour d'un pixel, puis la pose sur l'image
    al = np.asarray(cal)[..., 3] > 0
    bord = np.zeros_like(al)
    for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bord |= np.roll(np.roll(al, dx_, 1), dy_, 0)
    arr = np.asarray(cal).copy()
    arr[bord & ~al] = (*CONTOUR, 255)
    cal = Image.fromarray(arr)
    if miroir:
        cal = cal.transpose(Image.FLIP_LEFT_RIGHT)
    if rotation:
        cal = cal.rotate(-rotation, resample=Image.NEAREST, center=(L / 2, L * 0.6))
    img.paste(cal, (int(pieds[0] - L / 2), int(pieds[1] - L * 0.78)), cal)


def _chaussure(d, p, s, col):
    x, y = p
    d.rounded_rectangle((x - 4 * s, y - 4 * s, x + 7 * s, y), max(1, int(2 * s)), fill=col)
    d.line([(x - 4 * s, y - 1), (x + 7 * s, y - 1)], fill=GRIS, width=1)


def _main(d, p, s, col):
    x, y = p
    d.ellipse((x - 2.6 * s, y - 2.6 * s, x + 2.6 * s, y + 2.6 * s), fill=col)


def pieds_pour_saisir(cible, sol, taille, tronc, flexion, marge=0.99):
    """Où poser les pieds pour que les mains atteignent `cible` bras presque tendus (pas de bras élastiques)."""
    s = taille / 92
    a = math.radians(tronc)
    epaule_dx = -9 * s * flexion - 1 + 28 * s * math.sin(a)
    epaule_y = sol - 43 * s * (0.97 - 0.2 * flexion) - 28 * s * math.cos(a)
    portee = marge * 27 * s
    dy = cible[1] - epaule_y
    dx = math.sqrt(max(0.0, portee ** 2 - dy ** 2))
    return cible[0] - dx - epaule_dx
