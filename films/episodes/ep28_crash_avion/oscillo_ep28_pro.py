"""Épisode 28 en version « animée pro » : mêmes dessins, même voix, même minutage que oscillo_ep28.py, avec les outils
de films/styles/anim_pro.py (testés sur l'écran de l'inertie, voir inertie_pro.py).

Ce qui change, sans réécrire les écrans :
  - chaque écran a sa caméra (avancée lente, zooms vers ce que dit la voix, secousses aux chocs, turbulences) ;
    le titre et le tableau des lois restent fixes au-dessus ;
  - les dessins arrivent avec un rebond, repartent en se réduisant, ne sont jamais figés (traits vivants, légers
    mouvements propres à chaque objet : flammes, fumée qui monte, avion qui tangue sur l'eau, poids qui tombe…) ;
  - les changements de pose des personnages sont continus (flux d'un dessin à l'autre) et ils respirent ;
  - les textes arrivent avec un rebond ; les chiffres en grand défilent comme un compteur ;
  - écrans réécrits : l'inertie (corps qui se penche, inertie_pro.py) et le sac qui part (trajectoire, rotation, choc).

    python -m films.episodes.ep28_crash_avion.oscillo_ep28_pro output/ep28_pro.mp4
    python -m films.episodes.ep28_crash_avion.oscillo_ep28_pro output/ep28_pro_extrait.mp4 53 61   (un extrait)

Calé sur le mot (audio/mots.json, films/outils/mots_voix.py) :
  - ACCENTS : sur les mots forts, la caméra donne un coup (« pop »), un choc (secousse + flash), ou marque un arrêt :
    l'image se fige presque 0,3 s avant le mot, recule un peu (anticipation), puis frappe sur le mot ;
  - RECALAGE : une apparition prévue « début de phrase + x s » est déplacée sur le mot qu'elle illustre ; l'image
    (et ses sons) est accélérée ou ralentie autour, les débuts d'écran ne bougent pas.
Rendu à 60 images/s (mouvements de caméra fluides) ; les traits « vivants » restent à 12 i/s (style dessin animé).
"""
import math
import re
import sys

import skia

from films.episodes.ep28_crash_avion import inertie_pro as I
from films.episodes.ep28_crash_avion import oscillo_ep28 as E
from films.episodes.ep28_crash_avion.oscillo_ep28 import AMBRE, VERT, VERT_PALE, W, Z, faisceau, info, objet, trace
from films.outils import mots_voix as MV
from films.outils.extrait import rendre_extrait
from films.styles import anim_pro as A

M = E.M
s, e = M.s, M.e
H = M.H

# les fonctions d'origine, avant remplacement
_ecrit, _titre = E.ecrit, E.titre


# ------------------------------------------------------------------------------------------------ textes
COMPTEURS = {"95 %": 2.4}                 # durée du défilement (s) quand elle doit suivre l'image ; sinon 0,6 s


def ecrit(c, t, t0, txt, x, y, taille, col=VERT_PALE, centre=True, halo=1.0, vitesse=0.035):
    """Comme ecrit, avec un rebond d'arrivée ; un chiffre écrit en grand défile comme un compteur."""
    if t < t0:
        return
    m = re.fullmatch(r"(\D{0,4})(\d{1,3})(\D{0,10})", txt)
    if m and taille >= 56:
        n = int(m.group(2))
        k = A.sortie((t - t0) / COMPTEURS.get(txt, 0.6), 2.5)
        txt = f"{m.group(1)}{round(n * k)}{m.group(3)}"
        vitesse = 0.0
    k = A.pop(t, t0, 0.3)
    f = skia.Font(M.MONO, taille)
    px = x if centre else x + f.measureText(txt) / 2
    py = y - taille * 0.35
    c.save()
    c.translate(px, py)
    c.scale(k, k)
    c.translate(-px, -py)
    _ecrit(c, t, t0, txt, x, y, taille, col, centre, halo, vitesse)
    c.restore()


TITRES = []


def titre(c, t, t0, txt, col=VERT_PALE, y=300, taille=58):
    """Le titre est dessiné après la caméra, fixe au-dessus de l'image."""
    TITRES.append((t0, txt, col, y, taille))


# ------------------------------------------------------------------------------------------------ dessins
def _bas(tr):
    return max(p[1] for l in tr for p in l)


def _vers_haut(tr, k, cx, cy):
    return [[(cx + (x - cx), cy + (y - cy) * k) for x, y in l] for l in tr]


def _sur_bas(tr, k):
    b = _bas(tr)
    return [[(x, b + (y - b) * k) for x, y in l] for l in tr]


def mouvement(nom, tr, t, t0, cx, cy, larg):
    """Le petit mouvement propre à chaque objet, pour qu'aucun dessin ne soit figé."""
    dt = t - t0
    if nom == "av_descente":                                             # l'avion pique, secoué
        tr = A.tourne(tr, 1.6 * A.doux(3 * t, 2) + 2.0 * dt, cx, cy)
        return A.deplace(tr, 14 * dt + 3 * A.doux(9 * t), 22 * dt + 3 * A.doux(11 * t, 4))
    if nom in ("cab_clignote", "cab_masques"):                           # turbulences
        return A.deplace(A.tourne(tr, 0.7 * A.doux(6 * t, 1), cx, cy), 4 * A.doux(9 * t, 3), 3 * A.doux(13 * t, 5))
    if nom == "fe_flammes":                                              # flammes qui dansent
        return A.vivant(_sur_bas(tr, 1 + 0.07 * A.doux(7 * t, 2)), t, 2.2, 14, 3)
    if nom == "fe_fumee":                                                # la fumée monte et gonfle
        return A.vivant(A.deplace(A.echelle(tr, 1 + 0.025 * dt, cx, cy), 0, -14 * dt), t, 1.4, 10, 5)
    if nom == "fe_plafond":
        return A.deplace(tr, 10 * A.doux(0.8 * t, 1), 0)
    if nom == "av_eau":                                                  # l'avion tangue sur l'eau
        return A.deplace(A.tourne(tr, 1.3 * math.sin(1.7 * t), cx, cy), 0, 6 * math.sin(1.7 * t + 1))
    if nom in ("eau_gilet_gonfle", "eau_gilet_vide"):
        return A.echelle(tr, 1 + 0.025 * math.sin(4 * t), cx, cy)
    if nom in ("ph_kettlebell", "ph_poids16"):                           # le poids tombe et rebondit
        u = dt / 0.55
        h = 0 if u >= 1 else abs(math.cos(1.5 * math.pi * u)) * (1 - u) ** 2
        return A.deplace(tr, 0, -320 * h)
    if nom == "ph_ressort":                                              # le ressort s'écrase et revient
        return _sur_bas(tr, 1 - 0.18 * abs(math.sin(2.2 * dt)) * math.exp(-0.3 * dt))
    if nom == "ph_accordeon":                                            # la structure se plie
        k = 1 - 0.12 * abs(math.sin(2.0 * dt))
        return [[(cx + (x - cx) * k, y) for x, y in l] for l in tr]
    if nom == "ph_mannequin":                                            # le choc du test
        return A.deplace(tr, 14 * A.secousse(dt - 0.1, 5.0, 5.0), 0)
    if nom == "gr_file":                                                 # la file avance
        return A.deplace(tr, 9 * dt, 0)
    if nom == "fe_main":                                                 # la main suit les rangées
        return A.deplace(tr, 10 * math.sin(5 * t), 0)
    return A.deplace(tr, 0, 3 * A.doux(1.2 * t, len(nom)))               # flottement par défaut


def apres(c, t, t0, nom, cx, cy, larg, col=VERT_PALE, d=0.5, bip=1500, miroir=False, intense=1.0, t1=None):
    """Comme apres : tracé au faisceau, plus un rebond d'arrivée, un mouvement propre, une sortie en se réduisant."""
    if t < t0 or (t1 is not None and t >= t1):
        return
    tr = objet(nom, cx, cy, larg, miroir)
    k = 0.86 + 0.14 * A.rebond((t - t0) / 0.45, 2.2)
    if t1 is not None and t > t1 - 0.15:
        k *= 1 - 0.5 * A.lisse((t - t1 + 0.15) / 0.15)
    tr = mouvement(nom, A.echelle(tr, k, cx, cy), t, t0, cx, cy, larg)
    trace(c, t, t0, d, A.vivant(tr, t, 0.6, 12, len(nom)), col, 1.2, intense, bip=bip)


def suite(c, t, tab, cx, bas, k, col=VERT_PALE, bip=1100, miroir=False):
    """Un personnage qui change de pose : la première se trace, les suivantes en découlent (flux) ; il respire."""
    cour = [(tt, n) for tt, n in tab if t >= tt]
    if not cour or cour[-1][1] is None:
        return
    t0, nom = cour[-1]
    resp = 1 + 0.008 * math.sin(2.3 * t)
    if len(cour) > 1 and cour[-2][1] and t - t0 < 0.3:
        av = cour[-2][1]
        cle = (av, nom, cx, bas, k, miroir)
        for tr, i in A.flux(cle, E.pose(av, cx, bas, k, miroir), E.pose(nom, cx, bas, k, miroir), (t - t0) / 0.3):
            faisceau(c, A.vivant(_sur_bas(tr, resp), t, 0.5), 1.0, col, 1.2, i)
        return
    debut = cour[0][0] if len(cour) == 1 else t0 - 1.0                    # seule la première pose se trace
    tr = A.vivant(_sur_bas(E.pose(nom, cx, bas, k, miroir), resp), t, 0.5)
    trace(c, t, debut, 0.35, tr, col, 1.2, 1.0, bip=bip if len(cour) == 1 else 0)


# ------------------------------------------------------------------------------------------------ l'écran du sac
def e7b(c, t):
    """Le sac part : il décrit une courbe en tournant, accélère et percute le passager."""
    titre(c, t, s(31), "4 · F = m × a")
    t0, d = s(32) + 3.5, 0.95
    ti = t0 + d
    recul = -10 * A.secousse(t - ti, 1.4, 3.0)                           # le passager encaisse
    tr = E.pose("as_regarde_haut", 270, 1500, 1.15)
    tr = A.tourne(tr, recul, 270, 1500)
    trace(c, t, s(32) + 3.2, 0.35, A.vivant(tr, t, 0.5), VERT_PALE, 1.2, 1.0, bip=1100)
    u = A.borne((t - t0) / d) ** 1.6
    x = 960 - 560 * u
    y = 760 + 300 * u - 220 * math.sin(math.pi * u)
    if t < ti + 0.05:
        sac = A.tourne(objet("sac_vol", x, y, 360 - 60 * u), -260 * u, x, y)
        faisceau(c, A.vivant(sac, t, 0.6), 1.0, AMBRE, 2.2, 1.0)
        for k in range(4):                                               # traînée
            v = max(0.0, u - 0.07 * (k + 1))
            px, py = 960 - 560 * v, 760 + 300 * v - 220 * math.sin(math.pi * v)
            faisceau(c, [[(px, py), (px + 30, py - 8)]], 1.0, AMBRE, 1.6, 0.6 - 0.12 * k)
    else:
        b = 1.0 - A.lisse((t - ti) / 0.6)                                # le sac retombe
        sac = A.tourne(objet("sac_vol", 470, 1060 + 280 * (1 - b), 300), -260 + 40 * (1 - b), 470, 1060)
        faisceau(c, sac, 1.0, AMBRE, 2.2, 0.4 + 0.6 * b)
    if ti <= t < ti + 0.35:                                              # étincelles du choc
        f = (t - ti) / 0.35
        for i in range(12):
            a = 2 * math.pi * i / 12
            r0, r1 = 40 + 120 * f, 80 + 180 * f
            faisceau(c, [[(400 + r0 * math.cos(a), 1050 + r0 * math.sin(a)),
                          (400 + r1 * math.cos(a), 1050 + r1 * math.sin(a))]], 1.0, AMBRE, 2.4, 1 - f)
    ecrit(c, t, s(32) + 3.6, "112 KG", 640, 700, 96, AMBRE, True, 2.4)


# ------------------------------------------------------------------------------------------------ caméras
def _tete_brace():
    w = 322 * 1.9
    h = w * info("as_brace")["ratio"]
    return 540 - w / 2 + 0.78 * w, 1480 - h + 0.12 * h


def cameras():
    """Pour chaque écran (par son début) : la caméra. Les écrans absents ont une avancée lente automatique."""
    tx, ty = _tete_brace()
    turbulences = [(0.3 * i, 0.3, 7) for i in range(int(s(3) / 0.3))]
    tb = s(32) + 3.5 + 0.95
    return {
        0.0: A.Camera([(0.0, 1.08, 540, 980), (s(2), 1.0, 540, 940), (s(3), 1.04, 540, 900)],
                      turbulences + [(s(2), 0.4, 16)]),
        s(3) - 0.1: A.Camera([(s(3), 1.0, 540, 960), (s(5), 1.02, 540, 940), (s(5) + 2.4, 1.06, 540, 1000),
                              (s(6), 1.07, 540, 1010), (s(7), 1.03, 540, 990)], [(s(5) + 2.4, 0.35, 12)]),
        s(14): A.Camera([(s(14), 1.0, 540, 960), (s(15), 1.03, 540, 980),
                         (s(16), 1.12, tx - 130, ty + 120, 0.4), (s(17), 1.12, tx - 110, ty + 160),
                         (s(18), 1.14, 470, ty + 300, 0.4), (s(19), 1.0, 540, 960, 0.4), (s(21), 1.05, 540, 1060)]),
        s(21): A.Camera([(s(21), 1.0, 540, 940), (s(24), 1.04, 540, 900), (s(24) + 0.3, 1.04, 520, 880, 0.5),
                         (s(26), 1.05, 530, 880)]),
        s(26) - 0.05: A.Camera([(s(26), 1.0, 540, 960), (s(28), 1.03, 540, 900), (s(28) + 1.6, 1.08, 540, 1000)]),
        s(29) - 0.05: A.Camera([(s(29), 1.12, 560, 860), (s(29) + 0.3, 1.0, 540, 940, 0.3), (s(31), 1.05, 560, 1000)],
                               [(s(29), 0.4, 18)]),
        s(31): A.Camera([(s(31), 1.0, 540, 900), (s(32), 1.03, 540, 1000), (s(32) + 2.0, 1.08, 640, 1150, 0.4),
                         (s(32) + 3.0, 1.1, 640, 1150)], [(s(32) + 2.0, 0.3, 10)]),
        s(32) + 3.0: A.Camera([(s(32) + 3.0, 1.0, 600, 960), (s(32) + 3.5, 1.04, 640, 900),
                               (tb, 1.14, 450, 1020), (tb + 0.12, 1.26, 420, 1040, 0.12), (s(33), 1.2, 430, 1030)],
                              [(tb, 0.5, 26)]),
        s(33): A.Camera([(s(33), 1.0, 540, 900), (s(34), 1.02, 540, 960), (s(35), 1.12, 300, 1100, 0.4),
                         (s(36), 1.1, 500, 1080, 0.5), (s(37), 1.14, 700, 1100)]),
        s(37): A.Camera([(s(37), 1.0, 540, 1000), (s(38), 1.04, 540, 1000), (s(38) + 0.3, 1.0, 540, 900, 0.3),
                         (s(39), 1.02, 540, 1000), (s(41), 1.08, 540, 1260)]),
        s(41): A.Camera([(s(41), 1.06, 540, 900), (s(43), 1.0, 540, 940), (s(44), 1.05, 540, 960),
                         (s(45), 1.1, 540, 1280, 0.4), (s(46), 1.12, 540, 1300)]),
        s(46): A.Camera([(s(46), 1.0, 540, 900), (s(46) + 0.4, 1.12, 420, 700, 0.3), (s(46) + 1.4, 1.12, 420, 1000),
                         (s(47), 1.06, 540, 1100, 0.4), (s(49), 1.04, 540, 1150, 0.4), (s(50), 1.06, 540, 1180)],
                        [(s(49), 0.3, 10)]),
        s(50): A.Camera([(s(50), 1.0, 540, 900), (s(51), 1.02, 540, 980), (s(51) + 0.4, 1.08, 380, 1060, 0.5),
                         (s(52) + 0.4, 1.08, 440, 1080), (s(53), 1.0, 540, 1000, 0.5), (s(55), 1.03, 560, 1020)]),
    }


# ------------------------------------------------------------------------------------------------ calage au mot
FPS = 60


def accents():
    """[(instant du mot, genre)] — genre : "pop" (petit coup de caméra), "choc" (secousse + flash),
    "arret" (l'image se fige avant le mot, puis frappe)."""
    m = MV.mot
    return [(m("s'écraser"), "choc"), (m("secondes", s(1)), "pop"), (m("physique", s(2)), "pop"),
            (m("quatre", s(5)), "arret"), (m("survécu", s(5)), "choc"), (m("gestes", s(6)), "pop"),
            (m("l'inertie", s(8)), "pop"), (m("continuer", s(9)), "pop"), (m("dossier", s(11)), "choc"),
            (m("mur", s(12)), "choc"), (m("tête", s(16)), "pop"), (m("bras", s(18)), "pop"),
            (m("fort", s(20)), "choc"), (m("temps", s(22)), "pop"), (m("seize", s(29)), "arret"),
            (m("poids", s(30)), "pop"), (m("danger", s(31)), "arret"), (m("seize", s(32)), "pop"),
            (m("douze", s(32)), "choc"), (m("dessus", s(32)), "choc"), (m("chronomètre", s(34)), "pop"),
            (m("quatre", s(35)), "arret"), (m("s'étende", s(36)), "pop"), (m("sept", s(39)), "choc"),
            (m("tue", s(43)), "arret"), (m("monte", s(44)), "pop"), (m("bas", s(45)), "pop"),
            (m("cinq", s(49)), "arret"), (m("l'eau", s(50)), "pop"), (m("surtout", s(52)), "arret"),
            (m("physique", s(53)), "pop")]


def recalages():
    """[(instant prévu dans l'écran, instant du mot)] : ce qui apparaissait à l'instant prévu arrive sur le mot."""
    m = MV.mot
    return [(s(5) + 2.4, m("survécu", s(5))), (s(6), m("gestes", s(6))), (I.T_CHOC(), m("dossier", s(11))),
            (s(12) + 0.15, m("mur", s(12))), (s(20) + 0.4, m("fort", s(20))), (s(32), m("sept", s(32))), (s(32) + 1.2, m("c'est", s(32) + 1.5)),
            (s(32) + 2.0, m("douze", s(32))), (s(32) + 3.5 + 0.95, m("dessus", s(32))),
            (s(36) + 0.6, m("s'étende", s(36))), (s(39) + 1.2, m("sept", s(39))), (s(43) + 0.5, m("tue", s(43))),
            (s(49), m("cinq", s(49)))]


REEL, PREVU, ACC = [], [], []


def preparer_calage(debuts):
    """Construit la correspondance temps réel → temps prévu (linéaire par morceaux, croissante)."""
    import numpy as np
    MV.charger(M)
    pts = {round(t, 4): t for t in debuts + [0.0, M.SEG[-1][1] + 5]}               # débuts d'écran : inchangés
    paires = sorted([(t, t) for t in pts.values()] + [(w, p) for p, w in recalages()])
    reel, prevu = [], []
    for r, p in paires:
        if reel and (r <= reel[-1] + 0.05 or p <= prevu[-1] + 0.05):
            continue                                                              # garde la fonction croissante
        reel.append(r)
        prevu.append(p)
    REEL[:], PREVU[:] = np.array(reel), np.array(prevu)
    ACC[:] = accents()
    alignes = iter(MV.MOTS)                                               # les sous-titres suivent les mêmes instants
    for i, (w, a, b, deb, rang) in enumerate(M.MOTS):
        if any(ch.isalnum() for ch in w):
            a2, b2, _ = next(alignes)
            M.MOTS[i] = (w, a2, b2, deb, rang)


def prevu(t):
    """Instant réel → instant prévu par les écrans (avec les arrêts avant les mots forts)."""
    import numpy as np
    for tw, genre in ACC:
        if genre == "arret" and tw - 0.3 <= t < tw:
            t = tw - 0.3 + 0.1 * (t - tw + 0.3)
            break
    return float(np.interp(t, REEL, PREVU))


def reel(tp):
    import numpy as np
    return float(np.interp(tp, PREVU, REEL))


def coup(c, t):
    """La couche d'accents de la caméra (temps réel) : recul avant un arrêt, coup de zoom et secousse sur le mot."""
    z, dx, dy = 1.0, 0.0, 0.0
    for tw, genre in ACC:
        if genre == "arret" and tw - 0.3 <= t < tw:
            z -= 0.03 * A.lisse((t - tw + 0.3) / 0.3)
        d = t - tw
        if 0 <= d < 0.6:
            amp = {"pop": 0.035, "choc": 0.07, "arret": 0.08}[genre]
            z += amp * A.sortie(d / 0.06) * math.exp(-6 * d)
            if genre != "pop":
                a = 14 * (1 - d / 0.6) ** 2
                dx += a * A._bruit(int(t * 60), 11)
                dy += 0.6 * a * A._bruit(int(t * 60), 12)
    c.translate(W / 2 + dx, H / 2 + dy)
    c.scale(z, z)
    c.translate(-W / 2, -H / 2)


# ------------------------------------------------------------------------------------------------ montage
FIXES = [E.e12]                           # écrans sans accents de caméra (cartons de fin)
HAUT = 330                                # sous le titre : l'image filmée commence ici, avec un fondu


def avec_camera(fn, cam, lois=True, haut=HAUT):
    def g(c, tr, hud=True):
        t = prevu(tr)                                                     # le temps des écrans
        TITRES.clear()
        c.save()
        if cam is not None:
            c.clipRect(skia.Rect(0, haut, W, H))
        if fn not in FIXES:
            coup(c, tr)
        if cam is not None:
            cam.appliquer(c, t)
        fn(c, t)
        c.restore()
        if cam is not None and haut == HAUT:
            fondu = skia.GradientShader.MakeLinear([skia.Point(0, HAUT), skia.Point(0, HAUT + 90)],
                                                  [skia.Color(2, 8, 4, 255), skia.Color(2, 8, 4, 0)])
            c.drawRect(skia.Rect(0, HAUT, W, HAUT + 90), skia.Paint(Shader=fondu))
        g.titres = list(TITRES)
        if hud:
            g.hud(c, tr)

    def dessus(c, tr):
        """Le titre et le tableau des lois : fixes, hors caméra."""
        t = prevu(tr)
        if g.titres:
            t0, txt, col, y, taille = g.titres[-1]
            ecrit(c, t, t0, txt, W / 2, y, taille, col, True, 1.6)
        if lois:
            (lois if callable(lois) else E.tableau_lois)(c, t)              # un autre épisode passe son tableau
    g.hud, g.titres, g.haut = dessus, [], haut
    return g


def tableaux():
    cams = cameras()
    out = []
    CAMS.clear()
    origine = E.tableaux()
    preparer_calage([x[0] for x in origine])
    ecrans = [E.e1, E.e2, I.e4_pro, E.e5, E.e6a, E.e6b, E.e6c, E.e7, e7b, E.e8a, E.e8b, E.e9, E.e10, E.e11, E.e12]
    for (t0, _, tr), fn in zip(origine, ecrans):
        fin = ([x[0] for x in origine if x[0] > t0] + [t0 + 5])[0]
        cam = cams.get(t0) or A.Camera([(t0, 1.0, 540, 960), (fin, 1.05, 540, 940)])
        if fn in (I.e4_pro, E.e12):
            cam = None                                                   # l'inertie a sa propre caméra ; carton de fin
        haut = 215 if fn in (E.e1, E.e2) else HAUT                       # e2 écrit dans le haut, e1 n'a pas de titre
        out.append((t0, avec_camera(fn, cam, lois=fn not in (E.e1, E.e12), haut=haut), tr))
        CAMS.append(I.camera() if fn is I.e4_pro else cam)
    return enchainements(out)


# ------------------------------------------------------------------------------------------------ enchaînements
CAMS = []
TRANSFOS = []                             # [(début, fin)] des enchaînements, pour les sons
_COUCHES = []


def mini_perso(x, y, r=10):
    return E.mini_perso(x, y, r)


def vers_ecran(i, t, traits):
    """Les traits d'un dessin de l'écran i tels qu'on les voit à l'instant réel t (caméra de l'écran)."""
    cam = CAMS[i]
    if cam is None:
        return traits
    z, cx, cy = cam.etat(prevu(t))
    return [[((x - cx) * z + W / 2, (y - cy) * z + H / 2) for x, y in l] for l in traits]


def centre(traits):
    xs = [p[0] for l in traits for p in l]
    ys = [p[1] for l in traits for p in l]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def heros():
    """Pour chaque début d'écran : (le dessin qui part, le dessin qui arrive, début, fin) ; ou ("plongee", P, Q) ;
    les dessins sont des fonctions du temps (coordonnées du monde de leur écran)."""
    cel = (207 + 66 * 5, 360 + 40 + 66 * 4 * 1.12)                       # un passager au milieu de la grille
    ob = objet
    return {
        s(3) - 0.1: (lambda t: E.pose("as_regarde_haut", W / 2, 1500, 1.45), lambda t: mini_perso(*cel),
                     s(3) - 0.4, s(3) + 0.012 * 45 + 0.35),
        s(7): (lambda t: mini_perso(*cel), lambda t: I.passager(t)[0][0], s(7) - 0.3, s(7) + 0.3),
        s(14): (lambda t: I.passager(t)[0][0], lambda t: E.pose("as_brace", 540, 1480, 1.9), s(14) - 0.3, s(15) + 0.4),
        s(21): ("plongee", (270, 1468), (540, 760)),
        s(26) - 0.05: ("plongee", (520, 1090), (290, 620)),
        s(29) - 0.05: (lambda t: ob("si_siege_coupe", 540, 1180, 330), lambda t: ob("ph_mannequin", 340, 880, 560),
                       s(29) - 0.35, s(29) + 0.75),
        s(31): ("plongee", (820, 1230), (540, 590)),
        s(32) + 3.0: (lambda t: ob("ph_kettlebell", 800, 1150, 290), lambda t: ob("sac_vol", 960, 760, 360),
                      s(32) + 2.7, s(32) + 3.3),
        s(37): (lambda t: ob("fe_flammes", 790, 1090, 440), lambda t: ob("sac_tas", 790, 1110, 400),
                s(37) - 0.3, s(37) + 0.95),
        s(41): (lambda t: A.deplace(ob("gr_file", W / 2, 700, 900), 9 * (t - s(38)), 0),
                lambda t: ob("fe_fumee", W / 2, 900, 520), s(41) - 0.3, s(41) + 0.85),
        s(46): (lambda t: ob("fe_plafond", W / 2, 740, 960), lambda t: ob("cab_dessus", W / 2, 840, 440),
                s(46) - 0.3, s(46) + 0.75),
        s(50): (lambda t: ob("cab_dessus", W / 2, 840, 440), lambda t: ob("av_eau", W / 2, 580, 940),
                s(50) - 0.3, s(50) + 0.75),
    }


def _couche(i):
    while len(_COUCHES) <= i:
        _COUCHES.append(skia.Surface(W, H))
    sf = _COUCHES[i]
    sf.getCanvas().clear(skia.Color(0, 0, 0, 0))
    return sf


def _poser(c, sf, alpha, k=1.0, pivot=(W / 2, H / 2)):
    if alpha <= 0.01:
        return
    c.save()
    c.translate(*pivot)
    c.scale(k, k)
    c.translate(-pivot[0], -pivot[1])
    c.drawImage(sf.makeImageSnapshot(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear),
                skia.Paint(Alphaf=min(1.0, alpha)))
    c.restore()


def transformation(i, g_av, g_ap, ha, hb, debut):
    """L'objet qui part (écran i - 1) se change en l'objet qui arrive (écran i) ; les deux écrans se fondent autour."""
    def m(c, t):
        k = A.borne((t - debut) / 0.6)
        A_ = vers_ecran(i - 1, debut, ha(debut))
        B_ = vers_ecran(i, debut + 0.6, hb(debut + 0.6))
        pa, pb = centre(A_), centre(B_)
        s1, s2 = _couche(0), _couche(1)
        g_av(s1.getCanvas(), t, hud=False)
        g_ap(s2.getCanvas(), t, hud=False)
        c.save()
        c.clipRect(skia.Rect(0, min(g_av.haut, g_ap.haut), W, H))
        _poser(c, s1, 1 - A.lisse(k / 0.6), 1 + 0.12 * A.lisse(k), pa)            # l'ancien écran s'efface en avançant
        _poser(c, s2, A.lisse((k - 0.35) / 0.65), 0.93 + 0.07 * A.lisse(k), pb)   # le nouveau arrive en reculant
        for tr, it in A.flux(("transfo", i), A_, B_, k):
            faisceau(c, A.vivant(tr, t, 0.6), 1.0, VERT_PALE, 1.4, it)
        c.restore()
        (g_av if k < 0.5 else g_ap).hud(c, t)
    return m


def plongee(g_av, g_ap, P, Q, debut):
    """La caméra plonge dans un point de l'écran qui part et ressort d'un point de l'écran qui arrive."""
    def m(c, t):
        k = A.borne((t - debut) / 0.6)
        s1, s2 = _couche(0), _couche(1)
        g_av(s1.getCanvas(), t, hud=False)
        g_ap(s2.getCanvas(), t, hud=False)
        c.save()
        c.clipRect(skia.Rect(0, min(g_av.haut, g_ap.haut), W, H))
        _poser(c, s1, 1 - A.lisse((k - 0.2) / 0.4), 1 + 5 * A.lisse(k / 0.7) ** 2, P)
        _poser(c, s2, A.lisse((k - 0.35) / 0.4), 0.35 + 0.65 * A.sortie((k - 0.3) / 0.7), Q)
        c.restore()
        (g_av if k < 0.5 else g_ap).hud(c, t)
    return m


def enchainements(tabs):
    """Remplace les coupes et les effets (glitch, balayage…) par des transformations entre écrans."""
    TRANSFOS.clear()
    H_ = heros()
    out = []
    for i, (t0, g, tr) in enumerate(tabs):
        h = H_.get(t0)
        if not h or i == 0:
            out.append((t0, g, tr))
            continue
        g_av = tabs[i - 1][1]
        if h[0] == "plongee":
            debut, fin = t0 - 0.3, t0 + 0.3
            m = plongee(g_av, g, h[1], h[2], debut)
        else:
            debut, fin = h[2], h[3]
            m = transformation(i, g_av, g, h[0], h[1], debut)
        TRANSFOS.append((debut, fin))
        out.append((debut, m, None))
        out.append((fin, g, None))
    return out


def chocs():
    flashs, _ = E.chocs()
    flashs = [reel(x) for x in flashs + [I.T_CHOC(), s(32) + 3.5 + 0.95]]
    flashs += [tw for tw, genre in ACC if genre == "choc"]
    return flashs, []                                                    # les secousses passent par les caméras


def effets(tabs):
    ev = I.effets_pro(tabs)
    tb = s(32) + 3.5 + 0.95
    ev = [x for x in ev if not (s(32) + 4.5 <= x[0] < s(32) + 4.7)]       # l'ancien choc du sac
    ev += [(tb, Z.boom(0.6, 55)), (tb, Z.thump(0.45)), (tb, Z.craquement(0.3)), (s(32) + 3.5, Z.whoosh(0.9, 0.1)),
           (s(30) + 0.1, Z.thump(0.3)), (s(32) + 2.0, Z.thump(0.35))]
    ev = [(reel(t0), snd) for t0, snd in ev]                              # sons des écrans : suivent le recalage
    ev += [(d, Z.whoosh(0.6, 0.08)) for d, f in TRANSFOS]                  # les enchaînements
    ev += [(tw, Z.thump(0.3)) for tw, genre in ACC if genre == "choc"]
    ev += [(tw, Z.boom(0.45, 70)) for tw, genre in ACC if genre == "arret"]
    return ev


_mixage = M.mixage


def mixage(path, voix, dur, tabs):
    """Les bips de tracé et la frappe des textes sont notés en temps des écrans : on les remet en temps réel."""
    for cle, (t0, kind, args) in list(M.SONS.items()):
        M.SONS[cle] = (reel(t0), kind, args)
    _mixage(path, voix, dur, tabs)


def installer():
    E.ecrit, E.titre, E.apres, E.suite = ecrit, titre, apres, suite
    M.tableaux, M.chocs, M.effets, M.mixage = tableaux, chocs, effets, mixage
    M.FPS = FPS
    M.ALPHA_PERSISTANCE = 255 * (150 / 255) ** (24 / FPS)               # même traînée par seconde qu'à 24 i/s


if __name__ == "__main__":
    installer()
    sortie = sys.argv[1] if len(sys.argv) > 1 else "output/ep28_pro.mp4"
    if len(sys.argv) > 3:
        rendre_extrait(M, float(sys.argv[2]), float(sys.argv[3]), sortie)
    else:
        M.render(sortie)
