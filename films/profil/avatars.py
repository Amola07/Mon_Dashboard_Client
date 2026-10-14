"""Photos de profil (style oscilloscope « papier » : encre noire sur blanc), autour de la carte de l'Afrique.

Le contour de l'Afrique vient des vraies frontières (world-atlas, Natural Earth 1:50 m) : tous les pays africains sont
réunis en une seule forme (union de chemins skia).

    python -m films.profil.avatars DOSSIER_WORLD_ATLAS   → films/profil/avatar_*.png + films/profil/apercu.png
"""
import json
import math
import os
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

ICI = os.path.dirname(os.path.abspath(__file__))
S = 1080
ENCRE, GRIS, PAPIER = (18, 18, 18), (205, 205, 200), (252, 251, 247)
AFRIQUE = {12, 24, 72, 108, 120, 132, 140, 148, 174, 178, 180, 204, 226, 231, 232, 262, 266, 270, 288, 324, 384, 404,
           426, 430, 434, 450, 454, 466, 478, 504, 508, 516, 562, 566, 624, 646, 678, 686, 694, 706, 710, 716, 728,
           729, 732, 748, 768, 788, 800, 818, 834, 854, 894}


def arcs(topo):
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    out = []
    for a in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        out.append(pts)
    return out


def anneau(ids, A):
    pts = []
    for i in ids:
        seg = A[i] if i >= 0 else A[~i][::-1]
        pts += seg if not pts else seg[1:]
    return pts


def afrique(dossier, cx, cy, hauteur):
    topo = json.load(open(os.path.join(dossier, "countries-50m.json")))
    A = arcs(topo)
    union = skia.Path()
    lon0, lat0, lon1, lat1 = -18, -35, 52, 38
    k = hauteur / (lat1 - lat0)
    for g in topo["objects"]["countries"]["geometries"]:
        nom = g.get("properties", {}).get("name", "")
        if not (str(g.get("id", "")).isdigit() and int(g["id"]) in AFRIQUE) and nom not in ("Somaliland", "W. Sahara"):
            continue
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        for poly in polys:
            ring = anneau(poly[0], A)
            if len(ring) < 8:
                continue
            p = skia.Path()
            for j, (lon, lat) in enumerate(ring):
                x, y = cx + (lon - (lon0 + lon1) / 2) * k, cy - (lat - (lat0 + lat1) / 2) * k
                p.moveTo(x, y) if j == 0 else p.lineTo(x, y)
            p.close()
            union = skia.Op(union, p, skia.PathOp.kUnion_PathOp) or union
    return union


def peinture(col, w, plein=False):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*col))
    if not plein:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def fond(c, grille=True):
    c.clear(skia.Color(*PAPIER))
    if grille:
        for i in range(0, S + 1, 90):
            c.drawLine(i, 0, i, S, peinture(GRIS, 1.4))
            c.drawLine(0, i, S, i, peinture(GRIS, 1.4))
        for i in range(0, S + 1, 18):                                    # graduations sur les axes centraux
            c.drawLine(i, S / 2 - 7, i, S / 2 + 7, peinture(GRIS, 1.4))
            c.drawLine(S / 2 - 7, i, S / 2 + 7, i, peinture(GRIS, 1.4))


def hachures(c, path, pas=13, angle=-35, w=2.4):
    b = path.computeTightBounds()
    R = math.hypot(b.width(), b.height())
    a = math.radians(angle)
    dx, dy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    L = skia.Path()
    for i in range(int(2 * R / pas) + 1):
        o = -R + i * pas
        L.moveTo(b.centerX() + nx * o - dx * R, b.centerY() + ny * o - dy * R)
        L.lineTo(b.centerX() + nx * o + dx * R, b.centerY() + ny * o + dy * R)
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    c.drawPath(L, peinture(ENCRE, w))
    c.restore()


def onde(x0, x1, y, amp, f, phase=0.0, enveloppe=None, pas=3):
    p = skia.Path()
    for i, x in enumerate(np.arange(x0, x1 + pas, pas)):
        u = (x - x0) / (x1 - x0)
        e = enveloppe(u) if enveloppe else 1.0
        yy = y - amp * e * math.sin(2 * math.pi * f * u + phase)
        p.moveTo(x, yy) if i == 0 else p.lineTo(x, yy)
    return p


def avatar_a(dossier):
    """A : l'Afrique hachurée, traversée par l'onde de l'oscilloscope."""
    surf = skia.Surface(S, S)
    c = surf.getCanvas()
    fond(c)
    af = afrique(dossier, S / 2, S / 2, 760)
    c.drawPath(af, peinture(PAPIER, 0, True))
    hachures(c, af)
    c.drawPath(af, peinture(ENCRE, 9))
    env = lambda u: math.exp(-((u - 0.5) / 0.22) ** 2)
    c.drawPath(onde(60, S - 60, S / 2 + 10, 150, 7, 0.4, env), peinture(PAPIER, 26))
    c.drawPath(onde(60, S - 60, S / 2 + 10, 150, 7, 0.4, env), peinture(ENCRE, 10))
    return surf


def avatar_b(dossier):
    """B : l'Afrique faite de lignes d'onde empilées (comme un relevé de signal)."""
    surf = skia.Surface(S, S)
    c = surf.getCanvas()
    fond(c, grille=False)
    af = afrique(dossier, S / 2, S / 2 + 10, 820)
    rng = np.random.default_rng(3)
    b = af.computeTightBounds()
    c.save()
    c.clipPath(af, skia.ClipOp.kIntersect, True)
    for y in np.arange(b.top() + 8, b.bottom() + 40, 22):
        ph, f = rng.uniform(0, 6.28), rng.uniform(5, 9)
        env = lambda u, c0=rng.uniform(0.3, 0.7): 0.25 + math.exp(-((u - c0) / 0.12) ** 2)
        p = onde(b.left() - 20, b.right() + 20, y, 16, f, ph, env)
        c.drawPath(p, peinture(PAPIER, 12))
        c.drawPath(p, peinture(ENCRE, 4.2))
    c.restore()
    c.drawPath(af, peinture(ENCRE, 7))
    return surf


def avatar_c(dossier):
    """C : un écran rond d'oscilloscope ; l'Afrique tracée à la plume, le point de la plume en tête du tracé."""
    surf = skia.Surface(S, S)
    c = surf.getCanvas()
    c.clear(skia.Color(*PAPIER))
    R = 470
    c.drawCircle(S / 2, S / 2, R, peinture(ENCRE, 18))
    c.save()
    cercle = skia.Path()
    cercle.addCircle(S / 2, S / 2, R - 20)
    c.clipPath(cercle, skia.ClipOp.kIntersect, True)
    for i in range(0, S + 1, 80):
        c.drawLine(i, 0, i, S, peinture(GRIS, 1.6))
        c.drawLine(0, i, S, i, peinture(GRIS, 1.6))
    c.drawLine(0, S / 2, S, S / 2, peinture((150, 150, 146), 2))
    c.drawLine(S / 2, 0, S / 2, S, peinture((150, 150, 146), 2))
    c.restore()
    af = afrique(dossier, S / 2, S / 2, 640)
    hachures(c, af, pas=16, angle=35, w=2.2)
    c.drawPath(af, peinture(ENCRE, 10))
    m = skia.PathMeasure(af, False)                                       # le point de la plume, au bout du tracé
    pos = m.getPosTan(m.getLength() * 0.62)
    if pos:
        (px, py), _ = pos
        c.drawCircle(px, py, 18, peinture(ENCRE, 0, True))
        c.drawCircle(px, py, 30, peinture(ENCRE, 4))
    return surf


def sauver(surf, chemin):
    a = surf.makeImageSnapshot().toarray()[:, :, [2, 1, 0]]
    Image.fromarray(a).save(chemin)
    return Image.fromarray(a)


def apercu(images, chemin):
    """Chaque avatar tel que TikTok l'affiche : en grand dans un rond, puis tout petit (à côté d'un commentaire)."""
    W = 420 * len(images)
    ap = Image.new("RGB", (W, 620), (255, 255, 255))
    d = ImageDraw.Draw(ap)
    for i, (nom, im) in enumerate(images):
        for taille, y in ((360, 30), (110, 430), (44, 560)):
            v = im.resize((taille, taille), Image.LANCZOS)
            m = Image.new("L", (taille, taille), 0)
            ImageDraw.Draw(m).ellipse((0, 0, taille - 1, taille - 1), fill=255)
            x = i * 420 + (420 - taille) // 2
            ap.paste(v, (x, y), m)
            d.ellipse((x, y, x + taille, y + taille), outline=(200, 200, 200))
        d.text((i * 420 + 200, 600), nom, fill=(0, 0, 0))
    ap.save(chemin)


if __name__ == "__main__":
    dossier = sys.argv[1]
    ims = []
    for nom, f in (("A", avatar_a), ("B", avatar_b), ("C", avatar_c)):
        ims.append((nom, sauver(f(dossier), os.path.join(ICI, f"avatar_{nom}.png"))))
    apercu(ims, os.path.join(ICI, "apercu.png"))
    print("OK")
