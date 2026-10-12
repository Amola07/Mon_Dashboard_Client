"""« Oscar », la mascotte TikTok d'ExaMaster : un petit oscilloscope qui parle. 100 % code, noir et blanc.

La tête est un écran (double cadre, quadrillage pâle), les oreilles sont deux boutons de réglage, l'antenne porte un point
lumineux ; la bouche est une onde : à plat quand il se tait, d'amplitude égale au volume quand il parle. Le corps est un
petit boîtier avec son mini-écran. Les bras sont à deux segments (cinématique inverse) : on donne seulement la position des mains.

    python -m films.examaster_tiktok.mascotte output/oscar_poses.png        # planche de 3 poses

Repère local : pieds en (0, 0), le haut de l'antenne vers y = −600, unités ≈ pixels pour k = 1.
"""
import math
import sys

import skia

from films.styles.oscillo_ascenseur import P, cercle_pts, faisceau

BLANC = (255, 255, 255)
GRIS = (150, 150, 150)

# Proportions (repère local)
TETE = dict(x0=-130, x1=130, y0=-560, y1=-300, r=50)
CORPS = dict(x0=-72, x1=72, y0=-300, y1=-150, r=26)
EPAULE_G, EPAULE_D = (-78, -250), (78, -250)
L1, L2 = 80, 75                                                              # bras, avant-bras


# ------------------------------------------------------------------------------------------------ géométrie
def arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def rrect(x0, y0, x1, y1, r, n=8):
    """Rectangle à coins arrondis, ligne fermée."""
    pts = []
    for cx, cy, a in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        pts += arc(cx, cy, r, r, a, a + 90, n)
    return pts + [pts[0]]


def ik(epaule, main):
    """Coude d'un bras à deux segments, de l'épaule à la main : des deux coudes possibles, le plus bas (le naturel)."""
    dx, dy = main[0] - epaule[0], main[1] - epaule[1]
    d = min(math.hypot(dx, dy), L1 + L2 - 1e-3)
    a = math.atan2(dy, dx)
    cosb = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    b = math.acos(max(-1.0, min(1.0, cosb)))
    coudes = [(epaule[0] + L1 * math.cos(a + s * b), epaule[1] + L1 * math.sin(a + s * b)) for s in (-1, 1)]
    main = (epaule[0] + d * math.cos(a), epaule[1] + d * math.sin(a))
    return max(coudes, key=lambda e: e[1]), main


# ------------------------------------------------------------------------------------------------ morceaux
def onde_bouche(volume, t, sourire):
    """La bouche : une onde de 140 px. volume 0 = ligne presque plate ; sourire > 0 = coins relevés."""
    pts = []
    for i in range(0, 57):
        x = -70 + 140 * i / 56
        fenetre = math.sin(math.pi * i / 56) ** 0.7
        y = -392 + sourire * (1 - (x / 70) ** 2)                              # centre plus bas que les coins : un sourire
        y += volume * fenetre * (math.sin(x * 0.21 + t * 22) * 0.7 + math.sin(x * 0.47 - t * 31) * 0.3)
        pts.append((x, y))
    return pts


def yeux(style):
    """Les yeux : (traits blancs, points brillants). style : normal, content, grand, cligne."""
    g, d = (-50, -462), (50, -462)
    if style == "content":                                                   # ^ ^
        return [arc(p[0], p[1] + 10, 20, 20, 200, 340) for p in (g, d)], []
    if style == "cligne":
        return [[(p[0] - 18, p[1]), (p[0] + 18, p[1])] for p in (g, d)], []
    r = 26 if style == "grand" else 19
    traits = [cercle_pts(p[0], p[1], r, 18) for p in (g, d)]
    points = [(p[0] + 4, p[1] + 2, 7 if style == "grand" else 8) for p in (g, d)]
    return traits, points


def quadrillage():
    """Le quadrillage de l'écran, pâle : 6 colonnes × 4 lignes dans le cadre intérieur."""
    x0, x1, y0, y1 = -102, 102, -536, -326
    lignes = []
    for i in range(1, 6):
        x = x0 + (x1 - x0) * i / 6
        lignes.append([(x, y0), (x, y1)])
    for j in range(1, 4):
        y = y0 + (y1 - y0) * j / 4
        lignes.append([(x0, y), (x1, y)])
    return lignes


POSES = {
    # mains en coordonnées locales ; yeux ; sourire ; volume de la bouche ; petits plus
    "salut": dict(main_g=(-132, -160), main_d=(188, -385), yeux="content", sourire=16, volume=5, inclinaison=-3, telephone=False, agite=True),
    "montre": dict(main_g=(-140, -215), main_d=(240, -262), yeux="normal", sourire=8, volume=12, inclinaison=4, telephone=True),
    "idee": dict(main_g=(-180, -372), main_d=(180, -372), yeux="grand", sourire=0, volume=0, inclinaison=0, telephone=False, rayons=True,
                 bouche_o=True),
}


# ------------------------------------------------------------------------------------------------ dessin
def oscar(c, pose, t=0.0, k=1.0, x=0.0, y=0.0, u=1.0, volume=None, col=BLANC):
    """Dessine Oscar (pieds en (x, y), échelle k). volume : amplitude de la bouche, None = celle de la pose."""
    p = POSES[pose] if isinstance(pose, str) else pose
    c.save()
    c.translate(x, y)
    c.scale(k, k)
    # jambes et pieds
    hanche = (0, -150)
    jambes = [[hanche, (-34, -70), (-38, -8)], [hanche, (34, -70), (38, -8)],
              [(-62, 0), (-16, 0)], [(16, 0), (62, 0)]]
    faisceau(c, jambes, u, col, 1.0, 1.0)
    # corps + mini-écran + boutons
    faisceau(c, [rrect(CORPS["x0"], CORPS["y0"], CORPS["x1"], CORPS["y1"], CORPS["r"])], u, col, 1.0, 1.0)
    mini = [(-44 + 88 * i / 30, -246 + 14 * math.sin(i * 0.9 + t * 6)) for i in range(31)]
    faisceau(c, [rrect(-52, -282, 52, -212, 12), mini], u, col, 0.7, 0.9)
    for bx in (-30, 0, 30):
        faisceau(c, [cercle_pts(bx, -182, 7, 10)], u, col, 0.7, 0.9)
    # bras (le bras gauche plie le coude vers le bas, le droit aussi) et mains
    main_d = p["main_d"]
    if p.get("agite"):                                                           # il fait coucou
        main_d = (main_d[0] + 14 * math.sin(t * 9), main_d[1] - 10 * math.cos(t * 9))
    for epaule, main in ((EPAULE_G, p["main_g"]), (EPAULE_D, main_d)):
        coude, m = ik(epaule, main)
        faisceau(c, [[epaule, coude, m]], u, col, 1.0, 1.0)
        faisceau(c, [cercle_pts(m[0], m[1], 14, 12)], u, col, 0.9, 1.0)
    if p.get("telephone"):                                                       # un téléphone dans la main gauche
        mx, my = ik(EPAULE_G, p["main_g"])[1]
        faisceau(c, [rrect(mx - 22, my - 62, mx + 22, my + 6, 8), rrect(mx - 16, my - 54, mx + 16, my - 10, 4)], u, col, 0.8, 1.0)
        faisceau(c, [[(mx - 10, my - 32), (mx - 4, my - 40), (mx + 2, my - 26), (mx + 10, my - 36)]], u, col, 0.6, 0.9)
    # tête, inclinée autour de son centre
    c.save()
    c.translate(0, -430)
    c.rotate(p.get("inclinaison", 0))
    c.translate(0, 430)
    T = TETE
    faisceau(c, [rrect(T["x0"], T["y0"], T["x1"], T["y1"], T["r"])], u, col, 1.1, 1.0)
    faisceau(c, [rrect(T["x0"] + 16, T["y0"] + 16, T["x1"] - 16, T["y1"] - 16, 34)], u, col, 0.8, 0.9)
    faisceau(c, quadrillage(), u, GRIS, 0.35, 0.35)
    for sx in (-1, 1):                                                           # boutons de réglage = oreilles
        cx, cy = sx * 152, -450
        faisceau(c, [cercle_pts(cx, cy, 20, 16), [(cx, cy), (cx + sx * 12, cy - 12)]], u, col, 0.9, 1.0)
    faisceau(c, [[(0, T["y0"]), (0, T["y0"] - 36)], cercle_pts(0, T["y0"] - 46, 9, 10)], u, col, 0.9, 1.0)
    traits, points = yeux(p["yeux"])
    faisceau(c, traits, u, col, 1.0, 1.0)
    for px, py, r in points:
        c.drawCircle(px, py, r, P(col, 0, 255, 6, fill=True))
    if p.get("bouche_o"):
        faisceau(c, [cercle_pts(0, -385, 15, 14)], u, col, 1.0, 1.0)
    else:
        v = p["volume"] if volume is None else volume
        faisceau(c, [onde_bouche(v, t, p["sourire"])], u, col, 1.2, 1.0)
    if p.get("rayons"):                                                          # « idée ! » : traits autour de la tête
        rayons = [[(sx * (150 + 10 * i), -560 - 30 * j), (sx * (176 + 10 * i), -574 - 40 * j)]
                  for sx in (-1, 1) for i, j in ((0, 0), (1, 1))]
        faisceau(c, rayons, u, col, 0.8, 0.9)
    c.restore()
    c.restore()


def planche(sortie, poses=("salut", "montre", "idee")):
    """Une planche de poses sur fond noir, avec lignes de balayage (pour juger le dessin)."""
    L, H = 560 * len(poses), 760
    surf = skia.Surface(L, H)
    c = surf.getCanvas()
    c.clear(skia.Color(4, 4, 4))
    for i, nom in enumerate(poses):
        oscar(c, nom, t=0.3, k=0.98, x=280 + 560 * i, y=720)
    for yy in range(0, H, 4):
        c.drawLine(0, yy, L, yy, P((0, 0, 0), 2, 70))
    surf.makeImageSnapshot().save(sortie)
    print("écrit :", sortie)


if __name__ == "__main__":
    planche(sys.argv[1] if len(sys.argv) > 1 else "output/oscar_poses.png")
