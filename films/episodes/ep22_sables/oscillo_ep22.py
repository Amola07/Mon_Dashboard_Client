"""Épisode 22 — « Les sables mouvants » — style oscilloscope, calé sur la voix (≈ 79 s).

Réutilise le moteur de l'épisode 21 (faisceau, persistance, transitions, sous-titres, mixage) et ne remplace que les
tableaux, les flashs/secousses et les effets sonores.
Leçons de l'épisode 21 : image 0 pleine et déjà en mouvement, traits plus épais au départ, question finale à l'écran.

    python -m films.episodes.ep22_sables.oscillo_ep22 output/ep22_oscillo.mp4
"""
import math
import os
import sys

import numpy as np
import skia

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, P, W, bonhomme, cercle_pts, ease,
                                                         ecrit, faisceau, fleche, pointilles, rect_pts, titres, trace)
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
M.SEGS = os.path.join(HERE, "audio", "voix.json")
s, e = M.s, M.e

_SEMIS = {}


def semis(cle, x0, x1, y0, y1, n):
    if cle not in _SEMIS:
        r = np.random.default_rng(abs(hash(cle)) % 2 ** 32)
        _SEMIS[cle] = np.c_[r.uniform(x0, x1, n), r.uniform(y0, y1, n)]
    return _SEMIS[cle]


def grains(c, pts, t, col=VERT, a=170, r=2.8, agite=0.0):
    path = skia.Path()
    for i, (x, y) in enumerate(pts):
        if agite:
            x += agite * math.sin(t * 37 + i * 1.7)
            y += agite * math.cos(t * 41 + i * 2.3)
        path.addCircle(float(x), float(y), r)
    c.drawPath(path, P(col, 0, a * 0.6, r * 1.6, fill=True))
    c.drawPath(path, P(col, 0, a, fill=True))


def surface(x0, x1, y, t, amp=0.0):
    return [[(x, y + amp * math.sin(x / 38 + t * 6)) for x in range(int(x0), int(x1) + 1, 12)]]


def ondes(cx, y, t, periode=1.1, rmax=260):
    tr = []
    for k in range(3):
        u = ((t / periode) + k / 3) % 1
        r = 40 + rmax * u
        tr.append([(cx + r * math.cos(a), y + 0.14 * r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)])
    return tr


def lerp_traits(A, B, k):
    return [[(pa[0] + (pb[0] - pa[0]) * k, pa[1] + (pb[1] - pa[1]) * k) for pa, pb in zip(ta, tb)] for ta, tb in zip(A, B)]


def hachures(c, x0, y0, x1, y1, col=VERT, a=1.0, pas=26):
    c.save()
    c.clipRect(skia.Rect(x0, y0, x1, y1))
    traits = [[(x, y0), (x - (y1 - y0), y1)] for x in range(int(x0), int(x1 + (y1 - y0)), pas)]
    faisceau(c, traits, 1.0, col, 0.6, 0.6 * a)
    c.restore()
    faisceau(c, [rect_pts(x0, y0, x1, y1)], 1.0, col, 0.9, a)


# ------------------------------------------------------------------------------------------------ tableaux
def tab_accroche(c, t):
    SURF = 1000
    gras = 1.0 + 0.8 * (1 - ease(t / 2.0))                                # traits épais pendant les 2 premières secondes
    faisceau(c, surface(60, 1020, SURF, t, 3), 1.0, VERT, 1.2 * gras)
    grains(c, semis("a", 70, 1010, SURF + 14, 1460, 420), t, VERT, 150, 2.8, 1.5)
    faisceau(c, ondes(540, SURF, t), 1.0, VERT, 0.6, 0.6)
    pieds = SURF + 30 + 72 * ease(t / 1.6) + (5 * math.sin(t * 2.6) if t > 1.6 else 0)
    jambes_amb = s(3) <= t
    faisceau(c, bonhomme(540, pieds, 3.4, "flotte"), 1.0, VERT_PALE, 1.5 * gras)
    if jambes_amb:                                                          # le vrai danger : les jambes
        clign = 0.6 + 0.4 * math.sin(t * 9)
        faisceau(c, [[(540, pieds - 102), (510, pieds - 51), (509, pieds - 7)],
                     [(540, pieds - 102), (584, pieds - 51), (574, pieds - 10)]], 1.0, AMBRE, 2.0, clign)
        ecrit(c, t, s(3) + 0.4, "?", 700, pieds - 20, 110, AMBRE, False, 1.8, vitesse=0.0)
    if t < s(3):                                                            # la surprise affirmée dès l'image 0
        ecrit(c, t, -1.0, "VOUS NE POUVEZ", W / 2, 300, 88, AMBRE, True, 2.2, vitesse=0.0)
        ecrit(c, t, -1.0, "PAS COULER", W / 2, 400, 88, AMBRE, True, 2.2, vitesse=0.0)
        ecrit(c, t, -1.0, "SABLES MOUVANTS", W / 2, 470, 40, VERT_PALE, vitesse=0.0)
    titres(c, t, [(s(3), "LE VRAI DANGER ?", AMBRE, 76)], halo=2.0)
    if s(2) + 0.5 <= t < s(3):
        trace(c, t, s(2) + 0.5, 0.0, [rect_pts(170, 560, 910, 720)], AMBRE, 1.6, bip=0)
        ecrit(c, t, s(2) + 0.5, "IMPOSSIBLE", W / 2, 680, 120, AMBRE, True, 2.0, vitesse=0.0)


def tab_composition(c, t):
    t0 = s(4)
    LX, LY, R = 540, 760, 290
    titres(c, t, [(t0, "SABLE + ARGILE + EAU", VERT_PALE, 56), (s(5), "AU REPOS : SOLIDE", VERT_PALE, 60),
                  (s(6), "LA VIBRATION…", AMBRE, 64), (s(7), "LE SOL DEVIENT LIQUIDE", AMBRE, 54),
                  (s(8), "VOUS VOUS ENFONCEZ", VERT_PALE, 58)])
    trace(c, t, t0, 0.5, [cercle_pts(LX, LY, R, 64)], VERT_PALE, 1.2, bip=1100)
    # structure en château de cartes, qui s'effondre
    rg = np.random.default_rng(5)
    lache = [(LX + rg.uniform(-200, 200), LY + rg.uniform(-200, 200)) for _ in range(16)]
    tasse = [(LX - 210 + (i % 7) * 70 + (35 if (i // 7) % 2 else 0), LY + 210 - (i // 7) * 58) for i in range(16)]
    kc = ease((t - s(6) - 1.3) / 1.0)
    ag = 5.0 if s(6) + 0.3 <= t < s(7) + 0.5 else 0.0
    pos = [(a[0] + (b[0] - a[0]) * kc + ag * math.sin(t * 40 + i), a[1] + (b[1] - a[1]) * kc + ag * math.cos(t * 37 + i))
           for i, (a, b) in enumerate(zip(lache, tasse))]
    c.save()
    c.clipPath(skia.Path().addCircle(LX, LY, R - 4))
    if t > t0 + 2.6:                                                        # eau salée : petites vagues pâles
        vag = [[(x, y + 6 * math.sin(x / 20 + t * 3)) for x in range(LX - R, LX + R, 10)] for y in range(LY - 240, LY + 260, 60)]
        faisceau(c, vag, ease((t - t0 - 2.6) / 0.5), VERT, 0.4, 0.35)
    if t > t0 + 0.9:
        trace(c, t, t0 + 0.9, 0.5, [cercle_pts(x, y, 30, 18) for x, y in pos], VERT_PALE, 1.0, bip=0)
    if t > t0 + 1.9:                                                        # argile : ponts entre les grains
        ponts = [(0, 3), (3, 7), (7, 11), (2, 5), (5, 9), (9, 14), (1, 6), (6, 12), (4, 10)]
        ka = 1 - kc
        if ka > 0.02:
            tr = [[pos[i], (pos[i][0] + (pos[j][0] - pos[i][0]) * ka, pos[i][1] + (pos[j][1] - pos[i][1]) * ka)] for i, j in ponts]
            trace(c, t, t0 + 1.9, 0.5, tr, AMBRE if kc > 0 else VERT, 0.9, bip=0)
    c.restore()
    ecrit(c, t, t0 + 1.0, "SABLE", 150, 520, 34, VERT_PALE)
    ecrit(c, t, t0 + 1.9, "ARGILE", 935, 560, 34, AMBRE if t > s(6) + 1.3 else VERT_PALE)
    ecrit(c, t, t0 + 2.7, "EAU SALÉE", 540, 1100, 34, VERT_PALE)
    # le sol, avec quelqu'un dessus
    SURF2 = 1300
    liq = ease((t - s(7)) / 0.4)
    trace(c, t, t0 + 0.4, 0.6, surface(100, 980, SURF2, t, 4 * liq), VERT, 1.0, bip=0)
    grains(c, semis("b", 110, 970, SURF2 + 12, 1470, 220), t, AMBRE if liq > 0.5 else VERT, 140, 2.4, 2.5 * liq)
    pieds = SURF2 + 45 * ease((t - s(8)) / 0.9)
    trace(c, t, t0 + 0.6, 0.4, bonhomme(540, pieds, 1.5, "debout", "flotte", ease((t - s(8)) / 0.6)), VERT_PALE, 1.0,
          bip=1500)
    trace(c, t, t0 + 0.8, 0.3, pointilles(540, LY + R, 540, SURF2 - 130), VERT, 0.5, 0.6, bip=0)
    if s(6) + 0.3 <= t < s(8) + 0.5:
        faisceau(c, ondes(540, SURF2 + 20, t, 0.7, 340), 1.0, AMBRE, 0.7, 0.8)


def tab_densite(c, t):
    t0 = s(9)
    titres(c, t, [(t0, "2 FOIS PLUS DENSE", AMBRE, 66), (s(10), "VOUS FLOTTEZ", VERT_PALE, 70)])
    a = 0.16 * ease((t - t0 - 1.2) / 0.8)
    PX, PY, L = 540, 470, 320
    gx, gy = PX - L * math.cos(a), PY + L * math.sin(a)
    dx, dy = PX + L * math.cos(a), PY - L * math.sin(a)
    trace(c, t, t0, 0.5, [[(PX, PY), (PX, 860)], [(440, 860), (640, 860)], [(gx, gy), (dx, dy)]], VERT, 1.0, bip=1200)
    for x, y in ((gx, gy), (dx, dy)):
        bas = y + 150
        plateau = [[(x - 80, bas), (x, y), (x + 80, bas)],
                   [(x - 90 + 180 * i / 20, bas + 26 * math.sin(math.pi * i / 20)) for i in range(21)]]
        trace(c, t, t0 + 0.3, 0.4, plateau, VERT, 0.8, bip=0)
    trace(c, t, t0 + 0.6, 0.3, [rect_pts(gx - 55, gy + 70, gx + 55, gy + 150)], AMBRE, 1.0, bip=900)
    if t > t0 + 0.7:
        grains(c, semis("d", 0, 100, 0, 70, 70) + [gx - 50, gy + 76], t, AMBRE, 200, 3.0)
    trace(c, t, t0 + 0.8, 0.3, bonhomme(dx, dy + 150, 0.95, "debout"), VERT_PALE, 1.0, bip=1500)
    ecrit(c, t, t0 + 1.0, "SABLE MOUVANT", gx, gy + 220, 30, AMBRE)
    ecrit(c, t, t0 + 1.2, "≈ 2 kg/L", gx, gy + 262, 34, AMBRE)
    ecrit(c, t, t0 + 1.6, "VOUS", dx, dy + 220, 30, VERT_PALE)
    ecrit(c, t, t0 + 1.8, "≈ 1 kg/L", dx, dy + 262, 34, VERT_PALE)
    if t > s(10):                                                           # la poussée équilibre le poids
        SURF = 1150
        trace(c, t, s(10), 0.5, surface(120, 960, SURF, t, 3), VERT, 1.0, bip=1100)
        grains(c, semis("d2", 130, 950, SURF + 14, 1460, 240), t, VERT, 140, 2.6, 1.0)
        bob = 6 * math.sin((t - s(10)) * 2.4)
        trace(c, t, s(10) + 0.2, 0.4, bonhomme(540, SURF + 60 + bob, 2.0, "flotte"), VERT_PALE, 1.2, bip=0)
        trace(c, t, s(10) + 0.7, 0.3, fleche(680, SURF + 230, 680, SURF + 30), AMBRE, 1.3, bip=1700)
        ecrit(c, t, s(10) + 0.8, "POUSSÉE", 720, SURF + 150, 30, AMBRE, False)
        trace(c, t, s(10) + 1.1, 0.3, fleche(400, SURF - 150, 400, SURF - 10), VERT_PALE, 1.1, bip=900)
        ecrit(c, t, s(10) + 1.2, "POIDS", 230, SURF - 70, 30, VERT_PALE, False)


def tab_experience(c, t):
    t0 = s(11)
    titres(c, t, [(t0, "TESTÉ EN 2005", VERT_PALE, 66)])
    CX0, CX1, CY0, CY1, SURF = 260, 820, 560, 1180, 800
    trace(c, t, t0, 0.5, [[(CX0, CY0), (CX0, CY1), (CX1, CY1), (CX1, CY0)]], VERT_PALE, 1.2, bip=1100)
    trace(c, t, t0 + 0.2, 0.4, surface(CX0, CX1, SURF, t, 2), VERT, 1.0, bip=0)
    grains(c, semis("e", CX0 + 8, CX1 - 8, SURF + 12, CY1 - 6, 260), t, VERT, 150, 2.6, 0.6)
    for i, x in enumerate((370, 540, 710)):                                 # billes de la densité du corps
        tb = t0 + 0.5 + 0.35 * i
        if t < tb:
            continue
        u = t - tb
        y = 430 + min(1.0, (u / 0.45) ** 2) * (SURF - 430)
        if u > 0.45:
            y = SURF + 10 * math.exp(-(u - 0.45) * 5) * math.cos((u - 0.45) * 14)
        faisceau(c, [cercle_pts(x, y, 34, 30)], 1.0, VERT_PALE, 1.2)
        M.son(("bille", i), tb, "trace", 1500 - 200 * i, 0.4)
    ecrit(c, t, t0 + 1.6, "ARRÊT À MI-HAUTEUR", W / 2, 1260, 40, AMBRE)
    ecrit(c, t, t0 + 0.3, "« NATURE » · 2005", W / 2, 1330, 28, VERT)


def tab_limite(c, t):
    t0 = s(12)
    titres(c, t, [(t0, "PAS PLUS LOIN QUE LA TAILLE", AMBRE, 48)])
    SURF = 1000
    faisceau(c, surface(60, 1020, SURF, t, 2), 1.0, VERT, 1.0)
    grains(c, semis("a", 70, 1010, SURF + 14, 1460, 420), t, VERT, 150, 2.8, 1.0)
    pieds = SURF + 102 + 4 * math.sin(t * 2.6)
    faisceau(c, bonhomme(540, pieds, 3.4, "flotte"), 1.0, VERT_PALE, 1.4)
    trace(c, t, t0 + 0.2, 0.4, pointilles(140, SURF, 940, SURF), AMBRE, 1.2, bip=1600)
    ecrit(c, t, t0 + 0.6, "LIMITE", 150, SURF - 24, 36, AMBRE, False)
    trace(c, t, t0 + 0.3, 0.4, [[(240, pieds - 258), (240, pieds)]] + [[(225, y), (255, y)] for y in (pieds - 258, SURF, pieds)],
          VERT, 0.8, 0.8, bip=0)


def tab_piege(c, t):
    t0 = s(13)
    titres(c, t, [(t0, "LE VRAI PIÈGE", AMBRE, 70), (s(14), "L'EAU S'ÉCHAPPE", VERT_PALE, 60),
                  (s(14) + 1.8, "LE SABLE SE TASSE", AMBRE, 60), (s(15), "PRIS DANS DU BÉTON", AMBRE, 60)])
    SURF = 560
    trace(c, t, t0, 0.5, surface(60, 1020, SURF, t, 0), VERT, 1.0, bip=1100)
    jambes = [[(540, 440), (470, 840), (460, 1250)], [(540, 440), (610, 840), (620, 1250)]]
    trace(c, t, t0 + 0.2, 0.5, jambes, VERT_PALE, 2.4, bip=1300)

    def xjambe(y):
        k = min(1.0, max(0.0, (y - 440) / 400))
        return 540 - 70 * k, 540 + 70 * k

    base = semis("p", 70, 1010, SURF + 14, 1460, 520)
    kt = ease((t - s(14) - 1.8) / 1.2)
    pts, col_pts = [], []
    for x, y in base:
        g, d = xjambe(y)
        cible = g if abs(x - g) < abs(x - d) else d
        dist = abs(x - cible)
        if dist < 160:
            x = x + (cible - x) * 0.45 * kt * (1 - dist / 160)
        pts.append((x, y))
        col_pts.append(dist < 160)
    proche = np.array([p for p, k in zip(pts, col_pts) if k])
    loin = np.array([p for p, k in zip(pts, col_pts) if not k])
    grains(c, loin, t, VERT, 140, 2.6)
    grains(c, proche, t, AMBRE if kt > 0.3 else VERT, 150 + 80 * kt, 2.6 + 0.8 * kt)
    if s(14) <= t:                                                          # gouttes d'eau chassées vers l'extérieur
        u = min(1.0, (t - s(14)) / 2.2)
        gt = []
        for i, y in enumerate(range(640, 1260, 70)):
            g, d = xjambe(y)
            for sg, x in ((-1, g), (1, d)):
                gt.append(cercle_pts(x + sg * (20 + 230 * u), y + 10 * math.sin(i), 6, 10))
        faisceau(c, gt, 1.0, VERT_PALE, 0.8, 1 - 0.6 * u)
    if t > s(15):
        hachures(c, 380, 760, 700, 1300, AMBRE, 1.0)
        ecrit(c, t, s(15) + 0.3, "BÉTON", 860, 1040, 44, AMBRE, True, 1.6)


def tab_tirer(c, t):
    t0 = s(16)
    titres(c, t, [(t0, "ET SI VOUS TIREZ ?", AMBRE, 64), (s(17), "1 cm PAR SECONDE…", VERT_PALE, 58),
                  (s(18), "= SOULEVER UNE VOITURE", AMBRE, 50)])
    SURF = 1100
    faisceau(c, surface(60, 1020, SURF, t, 0), 1.0, VERT, 1.0)
    grains(c, semis("t", 70, 1010, SURF + 14, 1460, 360), t, VERT, 140, 2.6)
    hachures(c, 440, 1130, 640, 1300, AMBRE, 0.7)
    tremble = 4 * math.sin(t * 60) if t > t0 + 0.4 else 0
    faisceau(c, bonhomme(540 + tremble, SURF + 90, 3.0, "flotte"), 1.0, VERT_PALE, 1.4)
    trace(c, t, t0 + 0.4, 0.3, fleche(540, 900, 540, 680, 30), AMBRE, 1.8, bip=700)
    if t > s(17):
        ecrit(c, t, s(17) + 0.2, "FORCE", 860, 720, 32, VERT)
        q = ease((t - s(17) - 0.3) / (s(18) + 0.8 - s(17) - 0.3))
        f = 10 ** (2 + 4 * q)
        ecrit(c, t, s(17) + 0.2, f"{f:,.0f} N".replace(",", " "), 860, 790, 46 if f < 1e5 else 40, AMBRE, vitesse=0.0)
    if t > s(18) + 0.4:                                                     # la voiture soulevée
        lv = -40 * ease((t - s(18) - 1.0) / 0.8)
        car = [[(300, 600), (300, 550), (380, 540), (440, 490), (620, 490), (690, 540), (780, 550), (780, 600), (300, 600)],
               cercle_pts(380, 600, 30), cercle_pts(700, 600, 30)]
        car = [[(x, y + lv) for x, y in tr] for tr in car]
        trace(c, t, s(18) + 0.4, 0.6, car, VERT_PALE, 1.3, bip=900)


def tab_solution(c, t):
    t0 = s(19)
    titres(c, t, [(t0, "COMMENT S'EN SORTIR ?", VERT_PALE, 60), (s(20), "NE TIREZ PAS", AMBRE, 76),
                  (s(21), "PETITS CERCLES", VERT_PALE, 64), (s(22), "LE SABLE SE RAMOLLIT", VERT_PALE, 56),
                  (s(23), "EN ARRIÈRE, BRAS ÉCARTÉS", AMBRE, 50), (s(24), "VOUS REMONTEZ", VERT_PALE, 64),
                  (s(25), "VERS LE SOL FERME", VERT_PALE, 60)])
    SURF, X = 1000, 400
    trace(c, t, t0, 0.5, surface(60, 780, SURF, t, 0), VERT, 1.0, bip=1100)
    mou = ease((t - s(22)) / 1.5)
    grains(c, semis("s", 70, 770, SURF + 14, 1460, 320), t, VERT, 140, 2.6, 0.5 + 2.5 * mou)
    trace(c, t, t0 + 0.3, 0.5, [[(780, SURF), (1020, SURF)]], VERT_PALE, 1.2, bip=0)
    if t > t0 + 0.3:
        hachures(c, 780, SURF, 1020, 1460, VERT, ease((t - t0 - 0.3) / 0.5))
    ecrit(c, t, s(25), "SOL FERME", 900, SURF - 30, 32, VERT_PALE)
    # le corps : enfoncé → allongé en arrière → remonte → rampe
    k = ease((t - s(23) - 0.2) / 1.4)
    monte = 12 * ease((t - s(24) - 0.3) / 1.2)
    glisse = 240 * ease((t - s(25) - 0.2) / 2.6)
    A = bonhomme(X, SURF + 90, 3.0, "flotte")
    B = bonhomme(X + 40 + glisse, SURF + 12 - monte, 3.0, "allonge")
    faisceau(c, lerp_traits(A, B, k), 1.0, VERT_PALE, 1.4)
    if s(20) <= t < s(21):                                                  # « ne tirez pas »
        trace(c, t, s(20), 0.25, fleche(X + 200, 900, X + 200, 640, 30), AMBRE, 1.6, bip=700)
        trace(c, t, s(20) + 0.3, 0.2, [[(X + 120, 700), (X + 280, 860)], [(X + 280, 700), (X + 120, 860)]], AMBRE, 2.2, bip=400)
    if s(21) <= t < s(23) + 0.4:                                            # petits cercles aux pieds
        for fx in (X - 27, X + 30):
            a0 = (t - s(21)) * 5
            arc = [(fx + 34 * math.cos(a0 + i * 0.2), SURF + 84 + 14 * math.sin(a0 + i * 0.2)) for i in range(22)]
            faisceau(c, [arc], 1.0, AMBRE, 1.0)
    if s(22) <= t < s(23) + 0.5:                                            # l'eau revient vers les jambes
        u = min(1.0, (t - s(22)) / 2.0)
        gt = []
        for i, y in enumerate(range(1030, 1100, 30)):
            for sg in (-1, 1):
                gt.append(cercle_pts(X + sg * (260 - 200 * u), y, 6, 10))
        faisceau(c, gt, 1.0, VERT_PALE, 0.8, 1 - 0.5 * u)
    if s(24) <= t < s(25) + 0.5:                                            # poids réparti
        for i in range(8):
            x = X - 90 + i * 30
            trace(c, t, s(24) + 0.3 + i * 0.05, 0.15, fleche(x, SURF + 110, x, SURF + 40, 12), VERT_PALE, 0.8,
                  bip=1700 + 60 * i if i % 3 == 0 else 0)


def tab_temps(c, t):
    t0 = s(26)
    titres(c, t, [(t0, "LE VRAI DANGER…", VERT_PALE, 62), (s(27), "LE TEMPS", AMBRE, 96), (s(28), "LA MARÉE MONTE", AMBRE, 64)],
           halo=2.0)
    CX, CY, R = 540, 700, 190
    trace(c, t, t0 + 0.2, 0.5, [cercle_pts(CX, CY, R, 60)] + [[(CX + (R - 22) * math.cos(a), CY + (R - 22) * math.sin(a)),
                                                               (CX + R * math.cos(a), CY + R * math.sin(a))]
                                                              for a in np.arange(0, 2 * math.pi, math.pi / 6)],
          VERT_PALE, 1.2, bip=1100)
    if t > t0 + 0.6:
        am = (t - t0) * 5 - math.pi / 2
        ah = (t - t0) * 0.42 - math.pi / 2
        faisceau(c, [[(CX, CY), (CX + 150 * math.cos(am), CY + 150 * math.sin(am))],
                     [(CX, CY), (CX + 95 * math.cos(ah), CY + 95 * math.sin(ah))]], 1.0, AMBRE, 1.4)
    if t > s(28) - 0.1:
        SURF = 1180
        trace(c, t, s(28) - 0.1, 0.4, surface(80, 1000, SURF, t, 0), VERT, 1.0, bip=0)
        grains(c, semis("m", 90, 990, SURF + 14, 1460, 260), t, VERT, 140, 2.4)
        faisceau(c, bonhomme(700, SURF + 48, 1.6, "flotte"), 1.0, VERT_PALE, 1.1)
        u = ease((t - s(28)) / 2.6)
        niveau = SURF + 40 - 110 * u
        front = 80 + 700 * u
        vag = [[(x, niveau + 8 * math.sin(x / 30 + t * 5)) for x in range(80, int(front), 10)]]
        if len(vag[0]) > 1:
            faisceau(c, vag, 1.0, VERT_PALE, 1.3)
            faisceau(c, [[(x, niveau + 40 + 6 * math.sin(x / 26 + t * 4)) for x in range(80, int(front), 10)]], 1.0,
                     VERT_PALE, 0.7, 0.6)


def tab_recap(c, t):
    t0 = s(29)
    ecrit(c, t, t0 + 0.1, "VOUS SAVEZ QUOI FAIRE :", W / 2, 520, 46, VERT)
    for i, (dt, txt, col) in enumerate(((0.0, "LENTEMENT", VERT_PALE), (0.9, "EN ARRIÈRE", VERT_PALE),
                                        (1.9, "VOUS FLOTTEZ", AMBRE))):
        y = 700 + i * 140
        ta = s(30) + dt
        trace(c, t, ta, 0.2, [rect_pts(150, y - 52, 214, y + 12)], col, 1.2, bip=0)
        trace(c, t, ta + 0.2, 0.15, [[(160, y - 20), (180, y), (206, y - 44)]], col, 1.6, bip=0)
        ecrit(c, t, ta, txt, 250, y, 64, col, False, 1.6)


def tab_question(c, t):
    t0 = s(31)
    ecrit(c, t, t0, "ET VOUS ?", W / 2, 640, 140, AMBRE, True, 2.2, vitesse=0.0)
    ecrit(c, t, t0 + 0.4, "VOUS AURIEZ TIRÉ", W / 2, 800, 58, VERT_PALE)
    ecrit(c, t, t0 + 0.9, "SUR VOTRE JAMBE ?", W / 2, 875, 58, VERT_PALE)
    if t > s(32):
        ecrit(c, t, s(32), "DITES-LE EN COMMENTAIRE", 500, 1190, 40, VERT_PALE, True, 1.5)
        b = 18 * abs(math.sin((t - s(32)) * 5))
        trace(c, t, s(32) + 0.2, 0.25, fleche(800 + b, 1176, 960 + b, 1176, 26), AMBRE, 1.8, bip=1700)


def tableaux():
    return [(0.0, tab_accroche, None), (s(4) - 0.1, tab_composition, "neige"), (s(9) - 0.1, tab_densite, "balayage"),
            (s(11) - 0.1, tab_experience, "neige"), (s(12) - 0.1, tab_limite, "glitch"), (s(13) - 0.1, tab_piege, "noir"),
            (s(16) - 0.1, tab_tirer, "balayage"), (s(19) - 0.1, tab_solution, "neige"), (s(26) - 0.1, tab_temps, "glitch"),
            (s(29) - 0.1, tab_recap, "balayage"), (s(31) - 0.1, tab_question, "neige")]


def chocs():
    flashs = [s(2) + 0.5, s(15), s(18) + 0.4, s(20)]
    secousses = [(s(2) + 0.5, 0.2), (s(15), 0.2), (s(16) + 0.4, 0.3), (s(18) + 0.4, 0.3), (s(20), 0.15)]
    return flashs, secousses


def effets(tabs):
    ev = [(0.0, Z.thump(0.4)), (0.0, Z.bulles(1.8, 0.14)), (0.0, Z.whoosh(0.5, 0.12, False)),
          (s(1), Z.chirp(700, 1100, 0.2, 0.06)), (s(2) + 0.5, Z.boom(0.6, 60)), (s(2) + 0.5, Z.clang(140, 0.18, 1.6)),
          (s(3) - 0.5, Z.riser(0.5, 0.08)), (s(3) + 0.4, Z.alarme(0.06, 1))]
    # composition
    ev += [(s(4) + 1.0, Z.pince(392, 0.10)), (s(4) + 1.9, Z.pince(494, 0.10)), (s(4) + 2.7, Z.pince(587, 0.10)),
           (s(5), Z.cloche(523.3, 0.08)), (s(6) + 0.3, Z.vibration(1.6, 0.22)), (s(6) + 1.3, Z.crepitement(1.0, 0.14, 70)),
           (s(7), Z.whoosh(0.5, 0.12, False)), (s(7) + 0.1, Z.bulles(1.2, 0.12)), (s(8), Z.chirp(600, 150, 0.6, 0.1)),
           (s(8) + 0.1, Z.bulles(1.0, 0.14))]
    # densité
    ev += [(s(9) + 1.2, Z.clang(220, 0.14, 1.0)), (s(9) + 1.25, Z.cliquet(0.1)), (s(10), Z.chirp(300, 900, 0.7, 0.08)),
           (s(10) + 0.3, Z.scintillement(1.6, 0.06)), (s(10) + 0.7, Z.whoosh(0.3, 0.07))]
    # expérience
    for i in range(3):
        tb = s(11) + 0.5 + 0.35 * i
        ev += [(tb, Z.chirp(1500, 500, 0.4, 0.06)), (tb + 0.45, Z.thump(0.22)), (tb + 0.47, Z.bulles(0.4, 0.06, 20))]
    ev += [(s(12), Z.clang(900, 0.08, 0.6)), (s(12) + 0.2, Z.boom(0.25, 70))]
    # piège
    ev += [(s(13), Z.thump(0.3)), (s(14), Z.souffle(1.4, 0.08, False)), (s(14) + 0.2, Z.bulles(1.6, 0.08)),
           (s(14) + 1.8, Z.crepitement(1.0, 0.16, 120)), (s(14) + 1.9, Z.boom(0.3, 80)),
           (s(15), Z.boom(0.55, 55)), (s(15), Z.clang(120, 0.16, 1.2))]
    # tirer
    ev += [(s(16) + 0.1, Z.riser(0.3, 0.06)), (s(16) + 0.4, Z.grincement(s(18) + 0.4 - s(16) - 0.4, 0.14)),
           (s(17) + 0.3, Z.tictac(s(18) + 0.4 - s(17) - 0.3, 0.05, 0.12)),
           (s(18) + 0.4, Z.boom(0.6, 60)), (s(18) + 0.4, Z.clang(180, 0.16, 1.4)), (s(18) + 1.0, Z.whoosh(0.6, 0.1))]
    # solution
    ev += [(s(20), Z.alarme(0.08, 1)), (s(20), Z.thump(0.3)), (s(21), Z.whoosh(0.6, 0.06)), (s(21) + 0.7, Z.whoosh(0.6, 0.06)),
           (s(22), Z.bulles(2.0, 0.07)), (s(22), Z.souffle(1.2, 0.07, True)), (s(23) + 0.2, Z.whoosh(1.2, 0.09, False)),
           (s(24) + 0.3, Z.chirp(300, 1200, 0.8, 0.08)), (s(24) + 0.5, Z.scintillement(1.5, 0.05)),
           (s(25) + 0.2, Z.crepitement(2.4, 0.05, 25))]
    # le temps
    ev += [(s(26) + 0.2, Z.tictac(s(29) - s(26) - 0.3, 0.06, 0.25)), (s(27), Z.boom(0.5, 60)),
           (s(28), Z.vent(2.8, 0.12, 100, 700)), (s(28) + 0.3, Z.bulles(2.0, 0.05))]
    # récap et question
    ev += [(s(30), Z.cloche(523.3, 0.12)), (s(30) + 0.9, Z.cloche(659.3, 0.12)), (s(30) + 1.9, Z.cloche(784, 0.14)),
           (s(31), Z.boom(0.35, 70)), (s(31), Z.chirp(500, 1000, 0.3, 0.07)), (s(32) + 0.2, Z.pince(784, 0.08)),
           (s(32) + 0.35, Z.pince(988, 0.08)), (s(32) + 0.5, Z.pince(1175, 0.08))]
    for t0, _, tr in tabs[1:]:
        ev.append((t0, {"neige": lambda: Z.neige(0.22, 0.2), "balayage": lambda: Z.whoosh(0.4, 0.16),
                        "glitch": lambda: Z.glitch(0.25, 0.16), "noir": lambda: Z.thump(0.35)}[tr]()))
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep22_oscillo.mp4")
