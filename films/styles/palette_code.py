"""Planche de styles 100 % code : la même scène (ascenseur en coupe, personne en chute libre dans la cabine) rendue dans
cinq styles différents, pour choisir une direction visuelle.

    python -m films.styles.palette_code output/palette_code.png
"""
import math
import os
import sys

import numpy as np
import skia
from PIL import Image, ImageFilter

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")


def tf(nom):
    return skia.Typeface.MakeFromFile(os.path.join(FONTS, nom))


MONO = tf("JetBrainsMono.ttf")
CRAIE = tf("Caveat.ttf")
GRAS = tf("Montserrat-ExtraBold.ttf")
FIN = tf("Montserrat-Medium.ttf")


# ------------------------------------------------------------------------------------------------ la scène
def scene():
    """Primitives : (type, rôle, données). Rôles : 'struct' (bâtiment), 'detail', 'accent' (cabine, vitesse), 'cote'."""
    p = []
    x0, x1, y0, y1 = 300, 780, 430, 1610
    g0, g1 = 470, 610
    p.append(("rect", "struct", (x0, y0, x1, y1)))
    for e in range(1, 10):
        y = y0 + e * (y1 - y0) / 10
        p.append(("line", "detail", [(x0, y), (g0, y)]))
        p.append(("line", "detail", [(g1, y), (x1, y)]))
        for wx in range(x0 + 30, g0 - 20, 46):
            p.append(("rect", "detail", (wx, y - 70, wx + 22, y - 40)))
        for wx in range(g1 + 24, x1 - 30, 46):
            p.append(("rect", "detail", (wx, y - 70, wx + 22, y - 40)))
    p.append(("line", "struct", [(g0, y0), (g0, y1)]))
    p.append(("line", "struct", [(g1, y0), (g1, y1)]))
    p.append(("rect", "struct", (g0 + 20, y0 - 60, g1 - 20, y0)))                     # salle des machines
    p.append(("circle", "accent", ((g0 + g1) / 2, y0 - 30, 16)))
    p.append(("line", "accent", [((g0 + g1) / 2, y0 - 14), ((g0 + g1) / 2, y0 + 40)]))  # câble rompu
    p.append(("line", "accent", [((g0 + g1) / 2 - 8, y0 + 40), ((g0 + g1) / 2 + 6, y0 + 52)]))
    cy = 940
    p.append(("rect", "accent", (g0 + 14, cy, g1 - 14, cy + 112)))                     # cabine
    cx = (g0 + g1) / 2
    hy = cy + 30                                                                         # personne qui flotte
    p.append(("circle", "accent", (cx, hy, 9)))
    p.append(("line", "accent", [(cx, hy + 10), (cx, hy + 44)]))
    p.append(("line", "accent", [(cx - 20, hy + 6), (cx, hy + 18), (cx + 20, hy + 6)]))
    p.append(("line", "accent", [(cx - 14, hy + 62), (cx, hy + 44), (cx + 16, hy + 60)]))
    for k in range(3):                                                                   # flèche de vitesse
        p.append(("line", "accent", [(g1 + 40 + k * 0, cy - 60 + k * 0), (g1 + 40, cy + 150)]))
    p.append(("line", "accent", [(g1 + 26, cy + 128), (g1 + 40, cy + 152), (g1 + 54, cy + 128)]))
    p.append(("text", "accent", (g1 + 70, cy + 60, "87 km/h")))
    p.append(("text", "detail", (g1 + 70, cy + 100, "chute libre")))
    p.append(("line", "cote", [(x0 - 60, y0), (x0 - 60, y1)]))                          # cote de hauteur
    p.append(("line", "cote", [(x0 - 74, y0), (x0 - 46, y0)]))
    p.append(("line", "cote", [(x0 - 74, y1), (x0 - 46, y1)]))
    p.append(("text", "cote", (x0 - 160, (y0 + y1) / 2, "30 m")))
    p.append(("line", "struct", [(140, y1), (940, y1)]))
    p.append(("title", "", (W / 2, 220, "SAUTER AU DERNIER")))
    p.append(("title", "", (W / 2, 310, "MOMENT ?")))
    p.append(("text", "accent", (W / 2 - 150, 1760, "saut : +11 km/h")))
    return p


def chemin(prim, jitter=0.0, rng=None):
    kind, _, d = prim
    path = skia.Path()

    def j(x, y):
        if not jitter:
            return x, y
        return x + rng.normal(0, jitter), y + rng.normal(0, jitter)
    if kind == "line":
        pts = d
        if jitter:                                                                     # trait « à la main »
            pts2 = []
            for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
                n = max(2, int(math.hypot(xb - xa, yb - ya) / 40))
                pts2 += [j(xa + (xb - xa) * i / n, ya + (yb - ya) * i / n) for i in range(n)]
            pts2.append(j(*pts[-1]))
            pts = pts2
        path.moveTo(*pts[0])
        for q in pts[1:]:
            path.lineTo(*q)
    elif kind == "rect":
        x0, y0, x1, y1 = d
        if jitter:
            for seg in ([(x0, y0), (x1, y0)], [(x1, y0), (x1, y1)], [(x1, y1), (x0, y1)], [(x0, y1), (x0, y0)]):
                path.addPath(chemin(("line", "", seg), jitter, rng))
        else:
            path.addRect(skia.Rect(x0, y0, x1, y1))
    elif kind == "circle":
        path.addCircle(d[0], d[1], d[2])
    return path


def P(col, w=0.0, a=255, blur=0.0, fill=False):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*col, int(a)))
    if not fill:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def texte(c, x, y, s, typeface, size, paint, centre=False):
    f = skia.Font(typeface, size)
    if centre:
        x -= f.measureText(s) / 2
    c.drawString(s, x, y, f, paint)


# ------------------------------------------------------------------------------------------------ 1. plan d'ingénieur
def plan(c):
    c.clear(skia.Color(14, 52, 102))
    for x in range(0, W, 30):
        c.drawLine(x, 0, x, H, P((255, 255, 255), 1, 18 if x % 150 else 40))
    for y in range(0, H, 30):
        c.drawLine(0, y, W, y, P((255, 255, 255), 1, 18 if y % 150 else 40))
    for pr in scene():
        k, role, d = pr
        if k == "title":
            texte(c, d[0], d[1], d[2], MONO, 64, P((255, 255, 255), fill=True), True)
        elif k == "text":
            col = (255, 214, 120) if role == "accent" else (210, 230, 255)
            texte(c, d[0], d[1], d[2], MONO, 34, P(col, fill=True))
        else:
            w = {"struct": 3, "detail": 1.5, "accent": 3.5, "cote": 2}[role]
            col = (255, 214, 120) if role == "accent" else (235, 244, 255)
            pa = P(col, w, 255 if role != "detail" else 150)
            if role == "cote":
                pa.setPathEffect(skia.DashPathEffect.Make([14, 8], 0))
            c.drawPath(chemin(pr), pa)
    texte(c, 60, 1860, "FIG. 1 — CABINE EN CHUTE LIBRE  ·  ÉCHELLE 1:200", MONO, 26, P((210, 230, 255), fill=True))


# ------------------------------------------------------------------------------------------------ 2. oscilloscope
def oscillo(c):
    c.clear(skia.Color(2, 8, 4))
    vert = (90, 255, 140)
    for passe, (w, a, b) in enumerate(((14, 40, 18), (6, 110, 6), (2.2, 255, 0))):        # halo phosphore
        for pr in scene():
            k, role, d = pr
            if k in ("title", "text"):
                continue
            ww = w * (1.5 if role in ("accent", "struct") else 0.7)
            c.drawPath(chemin(pr), P(vert, ww, a * (1 if role != "detail" else 0.6), b))
    for pr in scene():
        k, role, d = pr
        if k == "title":
            texte(c, d[0], d[1], d[2], MONO, 64, P(vert, fill=True, blur=6), True)
            texte(c, d[0], d[1], d[2], MONO, 64, P((210, 255, 220), fill=True), True)
        elif k == "text":
            texte(c, d[0], d[1], d[2], MONO, 34, P(vert, fill=True, blur=4))
            texte(c, d[0], d[1], d[2], MONO, 34, P((210, 255, 220), fill=True))
    for y in range(0, H, 4):                                                              # lignes de balayage
        c.drawLine(0, y, W, y, P((0, 0, 0), 2, 90))
    g = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1150,
                                       [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 230)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))


# ------------------------------------------------------------------------------------------------ 3. motion design plat
def plat(c):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                        [skia.Color(255, 236, 214), skia.Color(255, 205, 178)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    c.drawCircle(900, 620, 130, P((255, 170, 120), fill=True))                             # soleil décoratif
    x0, x1, y0, y1 = 300, 780, 430, 1610
    ombre = P((120, 60, 50), fill=True, a=60, blur=30)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 + 24, y0 + 30, x1 + 24, y1 + 10), 26, 26), ombre)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), 26, 26), P((52, 63, 102), fill=True))
    c.drawRect(skia.Rect(470, y0, 610, y1), P((34, 41, 70), fill=True))
    for pr in scene():
        k, role, d = pr
        if k == "rect" and role == "detail":
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(*d), 5, 5), P((255, 212, 120), fill=True))
        elif k == "rect" and role == "accent":
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(*d), 14, 14), P((255, 110, 90), fill=True))
        elif k == "circle" and role == "accent" and d[2] < 12:
            c.drawCircle(d[0], d[1], d[2] + 4, P((255, 255, 255), fill=True))
        elif k == "line" and role == "accent":
            c.drawPath(chemin(pr), P((255, 255, 255), 9))
        elif k == "title":
            texte(c, d[0], d[1], d[2], GRAS, 82, P((52, 63, 102), fill=True), True)
        elif k == "text":
            sur_tour = 300 < d[0] < 780 and 430 < d[1] < 1610
            texte(c, d[0], d[1], d[2], GRAS, 40, P((255, 255, 255) if sur_tour else (52, 63, 102), fill=True))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(140, 1610, 940, 1640), 15, 15), P((52, 63, 102), fill=True))


# ------------------------------------------------------------------------------------------------ 4. craie
def craie(c):
    c.clear(skia.Color(36, 44, 40))
    rng = np.random.default_rng(3)
    for pr in scene():
        k, role, d = pr
        if k == "title":
            texte(c, d[0], d[1], d[2], CRAIE, 96, P((245, 245, 235), fill=True, a=235), True)
            continue
        if k == "text":
            col = (255, 200, 120) if role == "accent" else (235, 235, 225)
            texte(c, d[0], d[1], d[2], CRAIE, 54, P(col, fill=True, a=230))
            continue
        col = (255, 200, 120) if role == "accent" else (240, 240, 230)
        w = {"struct": 5, "detail": 2.5, "accent": 6, "cote": 3}[role]
        for passe in range(2):                                                            # double trait de craie
            c.drawPath(chemin(pr, 1.6, rng), P(col, w * (1 - 0.35 * passe), 170 - 50 * passe))


def texture_craie(a):
    rng = np.random.default_rng(5)
    bruit = rng.random(a.shape[:2])[..., None]
    trait = a.astype(np.float32).mean(2, keepdims=True) > 90
    a = a.astype(np.float32)
    a = np.where(trait, a * (0.55 + 0.45 * bruit), a + (bruit - 0.5) * 10)                # craie granuleuse + poussière
    return np.clip(a, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------------------------------------ 5. nuage de points
def nuage(c):
    c.clear(skia.Color(4, 6, 14))
    rng = np.random.default_rng(1)
    for pr in scene():
        k, role, d = pr
        if k == "title":
            texte(c, d[0], d[1], d[2], FIN, 70, P((220, 235, 255), fill=True), True)
            continue
        if k == "text":
            texte(c, d[0], d[1], d[2], FIN, 38, P((255, 170, 90) if role == "accent" else (150, 190, 255), fill=True))
            continue
        path = chemin(pr)
        mesure = skia.PathMeasure(path, False)
        L = mesure.getLength()
        dens = {"struct": 0.9, "detail": 0.35, "accent": 1.4, "cote": 0.3}[role]
        for i in range(int(L * dens)):
            pos, _ = mesure.getPosTan(rng.uniform(0, L))
            x, y = pos.x() + rng.normal(0, 1.5), pos.y() + rng.normal(0, 1.5)
            prof = y / H
            if role == "accent":
                col = (255, int(150 + 60 * rng.random()), 80)
            else:
                col = (int(80 + 80 * prof), int(140 + 60 * (1 - prof)), 255)
            c.drawCircle(x, y, rng.uniform(0.8, 2.2), P(col, fill=True, a=rng.uniform(120, 255)))
    for _ in range(1600):                                                                 # poussière lointaine
        c.drawCircle(rng.uniform(0, W), rng.uniform(0, H), 0.8, P((120, 150, 255), fill=True, a=rng.uniform(20, 90)))


STYLES = [("PLAN D'INGÉNIEUR", plan), ("OSCILLOSCOPE", oscillo), ("MOTION DESIGN PLAT", plat),
          ("CRAIE", craie), ("NUAGE DE POINTS", nuage)]


def render(out):
    vignettes = []
    for nom, f in STYLES:
        surf = skia.Surface(W, H)
        f(surf.getCanvas())
        a = surf.makeImageSnapshot().toarray()[:, :, [2, 1, 0]]
        if f is craie:
            a = texture_craie(a)
        if f is nuage:                                                                    # halo doux
            im = Image.fromarray(a)
            halo = np.asarray(im.resize((W // 6, H // 6)).filter(ImageFilter.GaussianBlur(4)).resize((W, H)), np.float32)
            a = np.clip(a.astype(np.float32) + 0.8 * halo, 0, 255).astype(np.uint8)
        Image.fromarray(a).save(os.path.join(os.path.dirname(out), f"style_{len(vignettes) + 1}.png"))
        vignettes.append(Image.fromarray(a).resize((360, 640), Image.LANCZOS))
    planche = Image.new("RGB", (360 * len(vignettes), 640))
    for k, v in enumerate(vignettes):
        planche.paste(v, (360 * k, 0))
    planche.save(out)
    print("OK", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/palette_code.png")
