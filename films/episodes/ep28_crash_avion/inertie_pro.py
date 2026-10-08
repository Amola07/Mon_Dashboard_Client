"""Test avant / après sur l'écran « 1 · L'INERTIE » de l'épisode 28 (≈ 14,3 s → 27,2 s).

Avant : e4 de oscillo_ep28 (dessins tracés puis figés, poses qui se remplacent).
Après : e4_pro, mêmes dessins et même voix, animés avec films/styles/anim_pro.py :
  - caméra virtuelle (avancée lente, zooms sur ce que dit la voix, panoramique vers le mur, secousses aux chocs) ;
  - l'avion roule (piste qui défile, caméra qui le suit), freine, pique du nez et se repose ;
  - le corps du passager se penche vraiment sous l'inertie (flexion du dessin au bassin), avec ressort ;
  - les changements de pose sont des transformations continues d'un dessin à l'autre, plus des remplacements ;
  - textes et icônes arrivent avec un rebond ; traits légèrement « vivants » ; décor atténué quand on parle du corps.

    python -m films.episodes.ep28_crash_avion.inertie_pro output/inertie
    → output/inertie_avant.mp4, output/inertie_apres.mp4, output/inertie_comparaison.mp4
"""
import math
import os
import subprocess
import sys

import skia

from films.episodes.ep28_crash_avion import oscillo_ep28 as E
from films.episodes.ep28_crash_avion.oscillo_ep28 import (AMBRE, VERT, VERT_PALE, W, Z, coche, croix, ecrit, faisceau,
                                                         fleche, info, objet, tampon, trace)
from films.outils.extrait import rendre_extrait
from films.outils.image_en_traits import dessin
from films.styles import anim_pro as A

M = E.M
s, e = M.s, M.e
K = 1.5                                   # échelle commune des planches (comme e4)
CX, BAS = 560, 1500                       # pieds du passager


# ------------------------------------------------------------------------------------------------ le passager
def ancre(nom):
    """Traits d'une pose en pixels de planche, origine au milieu du bas (commun à toutes les poses)."""
    d = info(nom)
    w = d["px"][0]
    return A.deplace(dessin(nom, 0, 0, w), -w / 2, -w * d["ratio"])


POSES = {}
RECALAGE = {"as_serre_ceinture": (-10, 0), "as_attache": (-2, 0)}   # alignées sur la pose neutre (sièges superposés)
HANCHE = (-62.0, -146.0)                  # le bassin, en pixels de planche (pose neutre)


def pose(nom):
    if nom not in POSES:
        POSES[nom] = A.deplace(ancre(nom), *RECALAGE.get(nom, (0, 0)))
    return POSES[nom]


def poids_buste(x, y):
    """Part du buste dans la flexion : 1 pour les épaules et la tête, 0 pour les cuisses, le siège et le dossier
    de devant."""
    dx, dy = x - HANCHE[0], HANCHE[1] - y
    phi = math.degrees(math.atan2(dy, dx))                                # 0° = vers l'avant, 90° = vers le haut
    w = A.lisse((phi - 8) / 72) * A.lisse(math.hypot(dx, dy) / 45)
    bord = -125 + 0.2 * (y + 300)                                         # bord du dossier (il penche vers l'arrière)
    w *= A.lisse((x - bord - 4) / 20)                                     # le dossier du passager ne bouge pas
    w *= 1 - A.lisse((x - 58) / 18)                                       # le siège de devant non plus
    return w


def corps(t):
    """[(traits, intensité)] du passager à l'instant t (une pose, ou deux pendant un changement de pose)."""
    seq = [(-1.0, "as_neutre"), (s(10), "as_serre_ceinture"), (s(10) + 1.6, "as_attache"), (s(11) + 0.15, "as_neutre")]
    durees = {"as_serre_ceinture": 0.35, "as_attache": 0.3, "as_neutre": 0.25}
    cour = [x for x in seq if x[0] <= t]
    t0, nom = cour[-1]
    if len(cour) > 1:
        av = cour[-2][1]
        k = A.lisse((t - t0) / durees[nom])
        if k < 1:
            return A.flux((av, nom), pose(av), pose(nom), k)
    return [(pose(nom), 1.0)]


def penche(t):
    """Angle du buste (degrés, + = vers l'avant)."""
    a = 0.8 * A.doux(t, 1.0)                                              # respiration, jamais figé
    a += 18 * A.secousse(t - (s(9) + 0.1), 0.45, 1.6)                     # l'avion freine : le corps continue
    a += 9 * A.secousse(t - (s(10) + 2.3), 0.9, 3.0)                      # avec ceinture : retenu, revient
    ti = s(11) + 0.55                                                     # sans ceinture : le buste part
    if t >= ti:
        u = (t - ti) / 0.3
        a += 32 * A.borne(u) ** 2 if u < 1 else 32 - 6 * A.secousse(t - ti - 0.3, 2.2, 4.0)
    return a



def ecran_passager(xy):
    return CX + xy[0] * K, BAS + xy[1] * K


def passager(t):
    out = []
    for tr, i in corps(t):
        tr = A.vivant(A.plier(tr, penche(t), HANCHE, poids_buste), t, 0.5)
        out.append(([[ecran_passager(p) for p in l] for l in tr], i))
    return out


def point_buste(t, x, y):
    """Où se trouve un point du buste (pixels de planche) une fois penché."""
    return ecran_passager(A.plier([[(x, y)]], penche(t), HANCHE, poids_buste)[0][0])


# ------------------------------------------------------------------------------------------------ l'avion
V0, DB = 1500.0, 1.1            # vitesse au sol (px/s), début et durée du freinage


def distance(t):
    tb, t_dep = s(9), s(7) - 1.0
    if t < tb:
        return V0 * (t - t_dep)
    u = min(1.0, (t - tb) / DB)
    return V0 * (tb - t_dep) + V0 * DB / 3 * (1 - (1 - u) ** 3)


def vitesse(t):
    u = (t - s(9)) / DB
    return V0 if u < 0 else V0 * max(0.0, 1 - u) ** 2


def avion(c, t, intense):
    d = info("av_piste")
    larg, cx, cy = 900, W / 2, 560
    x0, y0 = cx - larg / 2, cy - larg * d["ratio"] / 2
    tr = dessin("av_piste", x0, y0, larg)
    sol = y0 + 0.335 * larg
    corps_av = [l for l in tr if min(p[1] for p in l) < sol]                  # sans la piste dessinée
    u = (t - s(9)) / DB
    tangage = 3.2 * math.sin(math.pi * min(1, u)) if 0 <= u else 0.0      # pique du nez en freinant
    tangage -= 1.4 * A.secousse(t - s(9) - DB, 1.1, 3.0)                  # puis se repose
    elan = 34 * A.secousse(t - s(9), 0.5, 1.8)                            # la caméra qui suit a un temps de retard
    roue = (x0 + 0.84 * larg, sol)
    corps_av = A.deplace(A.tourne(corps_av, tangage, *roue), elan)
    corps_av = A.vivant(corps_av, t, 0.6, graine=7)
    faisceau(c, corps_av, 1.0, VERT_PALE, 1.2, intense)
    v = vitesse(t)                                                        # la piste défile sous l'avion
    pas, dist = 150, distance(t)
    faisceau(c, [[(-200, sol + 4), (W + 200, sol + 4)]], 1.0, VERT, 1.2, 0.8 * intense)
    tirets = []
    for i in range(-2, 12):
        x = i * pas - (dist % pas)
        tirets.append([(x, sol + 26), (x + 70, sol + 26)])
    faisceau(c, tirets, 1.0, VERT, 1.4, 0.8 * intense)
    if v > 40:                                                            # traînées de vitesse
        a = min(1.0, v / V0)
        for k in range(5):
            yy = y0 + 70 + 34 * k
            x1 = x0 + 40 - 30 * k + elan
            L = 220 * a * (0.6 + 0.4 * A._bruit(int(t * 12), k))
            faisceau(c, [[(x1 - L, yy), (x1, yy)]], 1.0, VERT_PALE, 1.4, 0.7 * a * intense)


# ------------------------------------------------------------------------------------------------ textes
def etiquette(c, t, t0, txt, x, y, taille, col=VERT_PALE, halo=1.6, t1=None):
    if t < t0 or (t1 is not None and t >= t1):
        return
    k = A.pop(t, t0, 0.32)
    c.save()
    c.translate(x, y - taille * 0.35)
    c.scale(k, k)
    ecrit(c, t, t0, txt, 0, taille * 0.35, taille, col, True, halo, vitesse=0.02)
    c.restore()


def icone(c, t, t0, nom, cx, cy, larg, col=VERT_PALE, intense=1.0):
    if t < t0:
        return
    k = A.pop(t, t0, 0.35)
    faisceau(c, A.echelle(objet(nom, cx, cy, larg), k, cx, cy), 1.0, col, 1.3, intense)


# ------------------------------------------------------------------------------------------------ l'écran
def T_CHOC():
    return s(11) + 0.85


CAM = None


def camera():
    global CAM
    if CAM is None:
        tc = T_CHOC()
        CAM = A.Camera([(s(7) - 0.5, 1.0, 540, 960), (s(9), 1.04, 540, 940),
                        (s(10), 1.07, 540, 960),
                        (s(10) + 0.6, 1.16, 420, 1120, 0.6),               # sur le passager et la ceinture
                        (s(11), 1.18, 440, 1120),
                        (s(11) + 0.5, 1.12, 560, 1120, 0.5),
                        (tc, 1.12, 560, 1120),
                        (tc + 0.12, 1.32, 680, 1060, 0.12),                 # coup de poing au choc
                        (s(12), 1.28, 690, 1060),
                        (s(12) + 0.3, 1.3, 800, 1120, 0.3),                 # panoramique vers le mur
                        (s(13), 1.3, 800, 1120),
                        (s(13) + 0.35, 1.2, 600, 1180, 0.35),             # recul : le passager et le tampon
                        (s(14), 1.22, 600, 1180)],
                       chocs=[(s(9) + DB - 0.1, 0.35, 6), (s(10) + 2.4, 0.25, 5), (tc, 0.45, 22), (s(13), 0.3, 12)])
    return CAM


def e4_pro(c, t):
    E.titre(c, t, s(7), "1 · L'INERTIE")
    c.save()
    c.clipRect(skia.Rect(0, 345, W, M.H))                                 # titre et tableau des lois restent nets
    camera().appliquer(c, t)
    deco = 1.0 if t < s(10) else 0.45 * (1 - A.lisse((t - s(12)) / 0.4))  # le décor s'efface quand on parle du corps
    avion(c, t, deco)
    if s(9) + 0.5 <= t < s(10):
        etiquette(c, t, s(9) + 0.5, "AVION : STOP", 270, 780, 40, VERT_PALE)
    for tr, i in passager(t):
        faisceau(c, tr, 1.0, VERT_PALE, 1.25, i)

    tete = point_buste(t, -10, -330)
    poitrine = point_buste(t, 0, -250)
    if s(9) + 0.2 <= t < s(10):                                          # le corps veut continuer
        v = A.rebond((t - s(9) - 0.2) / 0.5)
        faisceau(c, fleche(poitrine[0] + 20, poitrine[1], poitrine[0] + 20 + 230 * v, poitrine[1], 30), 1.0, AMBRE, 2.6)
        etiquette(c, t, s(9) + 0.5, "LE CORPS CONTINUE", 560, 1580, 38, AMBRE)
    if s(10) <= t < s(11) + 0.6:                                         # la ceinture
        icone(c, t, s(10) + 0.15, "si_ceinture_fermee", 175, 990, 270, VERT_PALE)
        etiquette(c, t, s(10) + 0.3, "SERRÉE BAS", 175, 1090, 34, VERT_PALE)
    if s(10) + 1.7 <= t < s(11):
        etiquette(c, t, s(10) + 2.4, "RETENU", 560, 1580, 42, VERT_PALE)
        trace(c, t, s(10) + 2.5, 0.25, coche(700, 1565, 26), VERT_PALE, 3.0, bip=1600)
        v = A.rebond((t - s(10) - 2.3) / 0.3)
        faisceau(c, fleche(poitrine[0] + 20, poitrine[1], poitrine[0] + 20 + 70 * v, poitrine[1], 26), 1.0, VERT_PALE, 2.4)
    if s(11) <= t < s(12):                                               # sans ceinture
        k = A.pop(t, s(11), 0.3)
        faisceau(c, A.echelle(croix(175, 990, 130), k, 175, 990), 1.0, AMBRE, 2.8)
        if t < s(11) + 0.6:
            icone(c, t, s(10) + 0.15, "si_ceinture_fermee", 175, 990, 270, VERT, 0.5)
    tc = T_CHOC()
    if tc <= t < tc + 0.35:                                              # étincelles du choc
        f = (t - tc) / 0.35
        for i in range(10):
            a = 2 * math.pi * i / 10 + 0.3
            r0, r1 = 30 + 90 * f, 60 + 140 * f
            faisceau(c, [[(tete[0] + 40 + r0 * math.cos(a), tete[1] + r0 * math.sin(a)),
                          (tete[0] + 40 + r1 * math.cos(a), tete[1] + r1 * math.sin(a))]], 1.0, AMBRE, 2.2, 1 - f)
    if t >= tc:
        etiquette(c, t, tc, "LE DOSSIER", 560, 860, 46, AMBRE, t1=s(12))
    if t >= s(12):                                                       # le mur
        k = A.sortie((t - s(12)) / 0.25)
        x = 1200 - 260 * k
        faisceau(c, [[(x, 820), (x, 1500)]] + [[(x, 900 + 100 * i), (x + 60, 860 + 100 * i)] for i in range(6)],
                 1.0, AMBRE, 2.2)
        etiquette(c, t, s(12) + 0.15, "OU LE MUR", 800, 790, 44, AMBRE, t1=s(13))
    c.restore()
    if t >= s(13):
        tampon(c, t, s(13), ["SANS CEINTURE"], 540, 500, 7, 64, AMBRE, t1=s(14))


# ------------------------------------------------------------------------------------------------ rendu
def tableaux_pro():
    return [(x[0], E.avec_lois(e4_pro) if x[0] == s(7) else x[1], x[2]) for x in E.tableaux()]


def chocs_pro():
    flashs, secousses = E.chocs()
    secousses = [x for x in secousses if not (s(7) <= x[0] < s(14))]   # la caméra s'en charge
    return flashs + [T_CHOC()], secousses


def effets_pro(tabs):
    ev = E.effets(tabs)
    ev = [x for x in ev if not (s(9) + 0.0 < x[0] < s(9) + 0.2)]
    ev += [(s(9), Z.whoosh(1.0, 0.09)), (s(9) + 0.2, Z.vibration(1.0, 0.07)), (s(9) + DB - 0.1, Z.thump(0.35)),
           (s(10) + 0.15, Z.cloche(988, 0.07)), (s(10) + 1.6, Z.snap(0.3)), (s(10) + 2.3, Z.thump(0.3)),
           (s(11) + 0.55, Z.whoosh(0.4, 0.09)), (T_CHOC(), Z.boom(0.6, 60)), (T_CHOC(), Z.craquement(0.3)),
           (s(12), Z.whoosh(0.3, 0.08))]
    return ev


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "output/inertie"
    M.preparer()
    t0, t1 = s(7) - 0.4, s(14) - 0.05
    avant, apres = base + "_avant.mp4", base + "_apres.mp4"
    if "--apres" not in sys.argv:
        rendre_extrait(M, t0, t1, avant)
    M.effets = effets_pro
    M.SONS.clear()
    rendre_extrait(M, t0, t1, apres, tableaux=tableaux_pro, chocs=chocs_pro)
    if os.path.exists(avant):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", avant, "-i", apres, "-filter_complex",
                        "[0:v]scale=540:960,drawtext=text='AVANT':x=20:y=20:fontsize=36:fontcolor=white[a];"
                        "[1:v]scale=540:960,drawtext=text='APRES':x=20:y=20:fontsize=36:fontcolor=white[b];"
                        "[a][b]hstack[v]", "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "20",
                        "-c:a", "copy", base + "_comparaison.mp4"], check=True)
        print("OK", base + "_comparaison.mp4")


if __name__ == "__main__":
    main()
