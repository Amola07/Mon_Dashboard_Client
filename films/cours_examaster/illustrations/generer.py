"""Génère les illustrations du cours ExaMaster (style oscilloscope).

    python -m films.cours_examaster.illustrations.generer
"""
import math
import os
import subprocess

import skia

from films.styles.oscillo_ascenseur import AMBRE, MONO, VERT, VERT_PALE, P, cercle_pts, ease, faisceau, rect_pts

ICI = os.path.dirname(os.path.abspath(__file__))


def fond(w, h):
    s = skia.Surface(w, h)
    c = s.getCanvas()
    c.clear(skia.Color(2, 8, 4))
    return s, c


def texte(c, txt, x, y, taille, col=VERT_PALE, centre=False):
    f = skia.Font(MONO, taille)
    if centre:
        x -= f.measureText(txt) / 2
    c.drawString(txt, x, y, f, P(col, 0, 255, 6, fill=True))
    c.drawString(txt, x, y, f, P(col, 0, 255, fill=True))


def fleche(x0, y0, x1, y1, t=18):
    a = math.atan2(y1 - y0, x1 - x0)
    return [[(x0, y0), (x1, y1)], [(x1 + t * math.cos(a + 2.6), y1 + t * math.sin(a + 2.6)), (x1, y1),
                                   (x1 + t * math.cos(a - 2.6), y1 + t * math.sin(a - 2.6))]]


def finir(s, nom):
    c = s.getCanvas()
    for y in range(0, s.height(), 4):
        c.drawLine(0, y, s.width(), y, P((0, 0, 0), 2, 60))
    s.makeImageSnapshot().save(os.path.join(ICI, nom), skia.kJPEG, 88)


def coordonnees():
    """L'écran 1080 × 1920 réduit, avec les axes et les zones."""
    k = 0.42
    W, H = int(1080 * k) + 360, int(1920 * k) + 120
    s, c = fond(W, H)
    x0, y0 = 220, 60
    ew, eh = 1080 * k, 1920 * k
    c.drawRect(skia.Rect(x0, y0 + 280 * k, x0 + ew, y0 + 1500 * k), P(VERT, 0, 28, fill=True))
    c.drawRect(skia.Rect(x0, y0 + 1600 * k, x0 + ew, y0 + 1700 * k), P(AMBRE, 0, 30, fill=True))
    faisceau(c, [rect_pts(x0, y0, x0 + ew, y0 + eh)], 1.0, VERT_PALE, 1.2)
    faisceau(c, fleche(x0, y0, x0 + ew + 60, y0), 1.0, AMBRE, 1.2)
    faisceau(c, fleche(x0, y0, x0, y0 + eh + 40), 1.0, AMBRE, 1.2)
    texte(c, "x", x0 + ew + 70, y0 + 10, 30, AMBRE)
    texte(c, "y", x0 + 14, y0 + eh + 44, 30, AMBRE)
    texte(c, "(0, 0)", x0 - 120, y0 + 8, 22, VERT_PALE)
    texte(c, "1080", x0 + ew - 30, y0 - 14, 20, VERT)
    texte(c, "1920", x0 - 80, y0 + eh, 20, VERT)
    texte(c, "ZONE UTILE", x0 + ew / 2, y0 + 900 * k, 26, VERT_PALE, True)
    texte(c, "y = 280 → 1500", x0 + ew / 2, y0 + 900 * k + 36, 20, VERT, True)
    texte(c, "SOUS-TITRES", x0 + ew / 2, y0 + 1665 * k, 20, AMBRE, True)
    texte(c, "INTERFACE TIKTOK", x0 + ew / 2, y0 + 150 * k, 18, VERT, True)
    # un point exemple
    px, py = x0 + 540 * k, y0 + 900 * k + 120
    faisceau(c, [cercle_pts(px, py, 8, 16)], 1.0, AMBRE, 1.4)
    texte(c, "(540, 1185)", px + 16, py + 8, 20, AMBRE)
    finir(s, "coordonnees.jpg")


def courbe_ease():
    W, H = 900, 560
    s, c = fond(W, H)
    gx0, gy0, gx1, gy1 = 110, 60, 840, 460
    faisceau(c, [[(gx0, gy1), (gx1, gy1)], [(gx0, gy1), (gx0, gy0)]], 1.0, VERT, 1.0)
    pts = [(gx0 + (gx1 - gx0) * i / 100, gy1 - (gy1 - gy0) * ease(i / 100)) for i in range(101)]
    faisceau(c, [[(gx0 - 60, gy1)] + pts + [(gx1 + 40, gy0)]], 1.0, AMBRE, 1.5)
    faisceau(c, [[(gx0, gy0), (gx1, gy0)]], 1.0, VERT, 0.5, 0.5)
    texte(c, "DÉBUT", gx0 - 40, gy1 + 40, 22, VERT_PALE)
    texte(c, "DÉBUT + DURÉE", gx1 - 110, gy1 + 40, 22, VERT_PALE)
    texte(c, "k = 0", 20, gy1 + 6, 22, VERT)
    texte(c, "k = 1", 20, gy0 + 6, 22, VERT)
    texte(c, "temps →", W / 2 - 50, gy1 + 80, 22, VERT)
    texte(c, "k = ease((t - DÉBUT) / DURÉE)", W / 2, 40, 26, AMBRE, True)
    finir(s, "ease.jpg")


def images_video(src, instants, nom):
    filtre = "+".join(f"eq(n\\,{int(t * 30)})" for t in instants)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
                    f"select='{filtre}',scale=360:640,tile={len(instants)}x1", "-frames:v", "1", "-q:v", "3",
                    os.path.join(ICI, nom)], check=True)


if __name__ == "__main__":
    coordonnees()
    courbe_ease()
    images_video("output/ep23_oscillo_envoi.mp4", [0.5, 12.0, 41.5], "exemple_ep23.jpg")
    images_video("output/modele.mp4", [0.3, 2.0, 5.5, 8.5], "modele.jpg")
    print("ok")
