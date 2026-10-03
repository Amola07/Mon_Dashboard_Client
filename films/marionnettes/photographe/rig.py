"""Marionnette du photographe (pièces découpées par decoupe.py) : assemblage, articulations, visage animé.

Coordonnées : celles de chaque pièce (pixels de la planche). Le torse sert de repère ; la manche droite (à l'écran)
est effacée du torse et remplacée par le bras articulé (bras_d_haut + avbras_d) pour pouvoir faire coucou.
"""
import math
import os

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))


def _img(nom):
    return skia.Image.open(os.path.join(HERE, "pieces", f"{nom}.png"))


def _torse_sans_manche():
    """Torse dont la manche de droite (à l'écran) est effacée : elle sera redessinée articulée."""
    import cv2
    t = cv2.imread(os.path.join(HERE, "pieces", "torse.png"), cv2.IMREAD_UNCHANGED)
    h, w = t.shape[:2]
    m = np.zeros((h, w), np.uint8)
    pts = np.array([[246, 300], [246, 120], [250, 60], [262, 30], [w, 30], [w, h], [246, h]], np.int32)
    cv2.fillPoly(m, [pts], 255)
    t[:, :, 3] = np.where(m > 0, 0, t[:, :, 3])
    return skia.Image.fromarray(np.ascontiguousarray(cv2.cvtColor(t, cv2.COLOR_BGRA2RGBA)))


class Photographe:
    def __init__(self):
        self.p = {n: _img(n) for n in ("tete", "bras_d_haut", "avbras_d", "avbras_g", "jambe_g", "jambe_d",
                                       "bouche_fermee", "bouche_mi", "bouche_ouverte")}
        self.torse = _torse_sans_manche()
        px = self.p["tete"].toarray(colorType=skia.kRGBA_8888_ColorType)
        self.peau = tuple(int(v) for v in np.median(px[118:135, 75:95, :3].reshape(-1, 3), axis=0))

    def _draw(self, c, nom, ox, oy, piv=(0, 0), ang=0.0, img=None):
        """Dessine la pièce avec son pivot (coordonnées de la pièce) placé en (ox, oy), tournée de ang degrés."""
        im = img or self.p[nom]
        c.save()
        c.translate(ox, oy)
        c.rotate(ang)
        c.drawImage(im, -piv[0], -piv[1], skia.SamplingOptions(skia.FilterMode.kLinear))
        c.restore()

    def visage(self, c, bouche, cligne):
        peau = skia.Paint(AntiAlias=True, Color=skia.Color(*self.peau))
        ink = skia.Paint(AntiAlias=True, Color=skia.Color(25, 15, 15), Style=skia.Paint.kStroke_Style, StrokeWidth=3.2,
                         StrokeCap=skia.Paint.kRound_Cap)
        if cligne > 0:
            for (x0, y0, x1, y1) in ((68, 96, 101, 114), (119, 93, 143, 110)):
                hh = (y1 - y0) * cligne
                c.drawOval(skia.Rect(x0 - 1, y0 - 2, x1 + 1, y0 + hh + 1), peau)
                p = skia.Path()
                p.moveTo(x0 + 2, y0 + hh - 1)
                p.quadTo((x0 + x1) / 2, y0 + hh + 4, x1 - 2, y0 + hh - 2)
                c.drawPath(p, ink)
        if bouche != "repos":
            c.drawOval(skia.Rect(97, 143, 130, 160), peau)
            im = self.p[{"fermee": "bouche_fermee", "mi": "bouche_mi", "ouverte": "bouche_ouverte"}[bouche]]
            s = 0.36
            c.save()
            c.translate(113, 152)
            c.rotate(-3)
            c.scale(s, s)
            c.drawImage(im, -im.width() / 2, -im.height() * (0.35 if bouche == "ouverte" else 0.5),
                        skia.SamplingOptions(skia.FilterMode.kLinear))
            c.restore()

    def draw(self, c, pose):
        """pose : dict d'angles (degrés) et d'états. Repère : torse, coin haut-gauche = (0, 0)."""
        g = pose.get
        respire = g("respire", 0.0)
        # jambes (derrière le torse)
        self._draw(c, "jambe_g", 128, 300, piv=(135, 22), ang=g("jambe_g", 0.0))
        self._draw(c, "jambe_d", 192, 300, piv=(32, 22), ang=g("jambe_d", 0.0))
        c.save()
        c.translate(0, -respire)
        # main gauche (sous la manche figée du torse)
        self._draw(c, "avbras_g", 68, 262, piv=(35, 100), ang=g("main_g", 0.0))
        # bras articulé : épaule → coude → main
        sh = (250, 112)
        a1 = 6 + g("epaule_d", 0.0)
        self._draw(c, "bras_d_haut", *sh, piv=(46, 34), ang=a1)
        r = math.radians(a1)
        coude = (sh[0] - 166 * math.sin(r), sh[1] + 166 * math.cos(r))
        self._draw(c, "avbras_d", *coude, piv=(52, 20), ang=a1 + g("coude_d", 0.0))
        c.drawImage(self.torse, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
        bord = skia.Path()                                       # contour du flanc là où la manche a été retirée
        bord.moveTo(247, 300)
        bord.lineTo(247, 122)
        bord.quadTo(249, 80, 262, 62)
        c.drawPath(bord, skia.Paint(AntiAlias=True, Color=skia.Color(30, 30, 34), Style=skia.Paint.kStroke_Style,
                                    StrokeWidth=3.0))
        # tête
        c.save()
        c.translate(163, 40)
        c.rotate(g("tete", 0.0))
        c.translate(-78, -192)
        c.drawImage(self.p["tete"], 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
        self.visage(c, g("bouche", "repos"), g("cligne", 0.0))
        c.restore()
        c.restore()
