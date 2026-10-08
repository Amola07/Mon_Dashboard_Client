"""Épisode 29 — « Le gilet de sauvetage » — en style « infographie pixel » (bleu-vert + orange), complet (≈ 1 min 25).

Même voix et mêmes instants (calés au mot) que oscillo_ep29.py. Style : films/styles/pixel_info.py ; icônes générées :
films/illustrations_pixel/px_* (prompts dans icones_pixel.md) ; la partie Archimède vient de pixel_archimede.py.
Une phrase blanche en haut (mot-clé en orange), un visuel plein en dessous, un chiffre en police pixel ; pas de
sous-titres ; chaque écran s'ouvre par un éclair de neige de 0,1 s.

    python -m films.episodes.ep29_gilet.pixel_ep29 output/ep29_pixel.mp4
    python -m films.episodes.ep29_gilet.pixel_ep29 output/ep29_pixel_extrait.mp4 40 60      (un extrait)
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw

from films import montage_ia as MI
from films.episodes.ep29_gilet import pixel_archimede as PA
from films.styles import oscillo_son as Z
from films.styles import pixel_info as X
from films.styles.pixel_info import (BLANC, BV, BV_SOMBRE, F8, F16, F24, F32, GRIS, ORANGE, ORANGE_SOMBRE, icone)

M, MV = PA.M, PA.MV
HERE = PA.HERE
FPS = 30
s, e, w = M.s, M.e, PA.w


def fondu(t, t0, d=0.3):
    return X.apparition(t, t0, d)


def pose(toile, t, tab, cx, bas, k=2, d=0.3):
    """Un personnage qui change de pose : tab = [(t0, nom)] ; l'ancienne pose s'efface en trame, la nouvelle apparaît."""
    cour = [(t0, n) for t0, n in tab if t >= t0]
    if not cour:
        return
    t0, nom = cour[-1]
    u = fondu(t, t0, d)
    if len(cour) > 1 and u < 1:
        X.coller(toile, icone(cour[-2][1], k), cx, bas, u, disparait=True)
    X.coller(toile, icone(nom, k), cx, bas, u if len(cour) > 1 or t0 > 0 else 1.0)


# ------------------------------------------------------------------------------------------------ 1. l'accroche
def e1(t, toile, d, ph):
    ph += [(["Votre avion s'est", "posé sur l'*eau*"], 0.0, s(2)), (["Un geste peut", "vous *noyer*"], s(2), s(3)),
           (["Le gonfler", "*tout de suite*"], s(3), None)]
    houle = round(1.5 * math.sin(1.4 * t))
    X.coller(toile, icone("px_avion_mer", 2), 135, 200 + houle)
    tg = w("gonfler", 3)
    pose(toile, t, [(-1.0, "px_gilet_plat"), (tg, "px_gonfle")], 135, 390, 2)
    X.tampon(toile, t, w("suite", 3) + 0.1, "PAS TOUT DE SUITE", 135, 300, -8, F16)


# ------------------------------------------------------------------------------------------------ 3. la cabine
CAB_K, CAB_X, CAB_Y = 4, 3, 112                           # px_cabine ×4, coin haut gauche (x, y) sur la toile
INT = (3, 12, 62, 37)                                     # l'intérieur de la cabine, en pixels de l'icône
PORTE = (53, 14, 60, 31)


def cab(x, y):
    return CAB_X + x * CAB_K, CAB_Y + y * CAB_K


def niveau(t):
    u1 = X.lisse((t - w("monte", 14)) / 1.6)
    u2 = X.lisse((t - s(17)) / 2.0)
    yb, yh, yp = cab(0, INT[3])[1], cab(0, PORTE[1] - 2)[1], cab(0, INT[1] + 3)[1]
    return yb - (yb - yh) * u1 - (yh - yp) * u2


def e3(t, toile, d, ph):
    ta = w("arrivez", 20)
    ph += [(["Mais dans la cabine,", "l'eau *monte*"], s(13), s(15)), (["Les sorties sont", "*sous l'eau*"], s(15), s(17)),
           (["Pour sortir,", "il faut *plonger*"], s(17), s(19)), (["Avec *16 kg*", "vers le plafond…"], s(19), ta),
           (["*Impossible*"], ta, None)]
    cabine = icone("px_cabine", CAB_K)
    toile.paste(cabine, (CAB_X, CAB_Y), cabine)
    niv = niveau(t)
    perso = icone("px_plafond", 1).crop((0, 4, 59, 53))
    perso = perso.resize((perso.width * 2, perso.height * 2), Image.NEAREST)
    plafond = cab(0, INT[1])[1] + 2
    py = max(plafond, round(niv) - 30)
    tp = w("monte", 14) + 0.7                              # il apparaît quand l'eau le soulève
    if t >= tp:
        cal = X.calque()
        cal.paste(perso, (60, py), perso)
        X.poser(toile, cal, fondu(t, tp, 0.3))
    cal = X.calque()
    dc = ImageDraw.Draw(cal)
    x0, y0 = cab(INT[0], INT[1])
    x1, y1 = cab(INT[2], INT[3])
    X.eau(dc, x0 + 2, x1, niv, y1, t)
    toile.paste(cal, (0, 0), cal)
    ts = w("sorties", 15)
    if t >= ts and int((t - ts) * 4) % 2 == 0 or t >= ts + 1.5:
        px0, py0 = cab(PORTE[0] - 1, PORTE[1] - 1)
        px1, py1 = cab(PORTE[2] + 1, PORTE[3] + 1)
        d.rectangle([px0, py0, px1, py1], outline=ORANGE, width=2)
        X.texte(d, ((px0 + px1) / 2, py1 + 8), "SORTIE", F8, ORANGE)
    if t >= s(17):                                         # le chemin vers la porte, en pointillés
        v = X.lisse((t - s(17)) / 0.8)
        pts = [(130, py + 40), (150, 230), (200, 240), (228, 210)]
        tot = 0
        for a, b in zip(pts, pts[1:]):
            n = int(math.dist(a, b) / 4)
            for j in range(n):
                tot += 1
                if tot > 60 * v:
                    break
                if j % 2 == 0:
                    d.point((round(a[0] + (b[0] - a[0]) * j / n), round(a[1] + (b[1] - a[1]) * j / n)), fill=BLANC)
    tk = w("seize", 19)
    if t >= tk:
        for dx in (-30, 0, 30):
            X.fleche_haut(d, 120 + dx, py + 10, round(14 * X.sortie((t - tk) / 0.4)), 4)
        X.texte(d, (135, 330), f"{round(16 * X.sortie((t - tk) / 0.6, 2.5))} KG", F32, ORANGE)
    if t >= ta:
        d.line([(166, 222), (190, 246)], fill=ORANGE, width=4)
        d.line([(190, 222), (166, 246)], fill=ORANGE, width=4)


# ------------------------------------------------------------------------------------------------ 4. Comores 1996
def mini(d, x, y, gilet):
    d.rectangle([x - 2, y - 7, x + 2, y - 5], fill=BV)                  # bonnet
    d.rectangle([x - 2, y - 4, x + 2, y - 2], fill=BLANC)               # tête
    d.rectangle([x - 3, y - 1, x + 3, y + 5], fill=GRIS)                # corps
    if gilet:
        d.rectangle([x - 4, y - 2, x + 4, y + 2], fill=ORANGE)


def e4(t, toile, d, ph):
    tg = w("gonflé", 24)
    ph += [(["*1996*, près", "des Comores"], s(21), s(22)), (["Beaucoup ont", "*survécu* au choc"], s(22), s(24)),
           (["Mais ils avaient", "*gonflé* leur gilet"], s(24), None)]
    if t < s(22):
        X.coller(toile, icone("px_avion_pique", 2), 135, 360, fondu(t, s(21) - 0.1))
        X.texte(d, (135, 372), X.tape("AVION DÉTOURNÉ · OCÉAN INDIEN", (t - w("détourné", 21)) / 0.6), F8, BV)
        return
    x0, y0, x1, y1 = 40, 150, 230, 330                      # la cabine en coupe
    d.rectangle([x0, y0, x1, y1], outline=BV, width=2)
    niv = y1 - 4 - 110 * X.lisse((t - tg) / 2.0)
    cal = X.calque()
    X.eau(ImageDraw.Draw(cal), x0 + 3, x1 - 2, niv, y1 - 2, t)
    tv = s(22)
    for i in range(4):
        for j in range(8):
            x = x0 + 18 + j * 22
            yb = y0 + 40 + i * 38
            dly = 0.1 * (j + 2 * i)
            u = X.lisse((t - tg - dly) / 0.9)
            y = round(yb + (y0 + 12 - yb) * u)
            if t >= tv + 0.03 * (j + 8 * i):
                mini(d, x, y, t >= tg + dly)
    toile.paste(cal, (0, 0), cal)
    if t >= tg:
        X.texte(d, (135, 344), "GILETS GONFLÉS DANS LA CABINE", F8, ORANGE)


# ------------------------------------------------------------------------------------------------ 5. le bon geste
def e5a(t, toile, d, ph):
    ph += [(["Le *bon* geste"], s(25), None)]
    X.coller(toile, icone("px_gilet_plat", 2), 70, 390, fondu(t, s(25)))
    lignes = [("ENFILÉ", w("enfilé", 26), True), ("SERRÉ", w("serrées", 27), True), ("GONFLÉ", w("gonflé", 29), False)]
    for k, (txt, t0, oui) in enumerate(lignes):
        if t < t0:
            continue
        y = 170 + 60 * k
        X.texte(d, (128, y), txt, F16, BLANC if oui else ORANGE, centre=False)
        if oui:
            X.coche(d, 232, y + 4, BV, 3)
        else:
            d.line([(228, y), (244, y + 16)], fill=ORANGE, width=3)
            d.line([(244, y), (228, y + 16)], fill=ORANGE, width=3)


def e5b(t, toile, d, ph):
    tg = w("remplit", 32)
    ph += [(["On tire la languette", "*à la porte*"], s(30), s(31)), (["*une fois dehors*"], s(31), s(32)),
           (["Une cartouche de gaz", "le *gonfle*"], s(32), s(33)), (["en *quelques secondes*"], s(33), None)]
    X.coller(toile, icone("px_porte", 3), 135, 400, fondu(t, s(30) - 0.1))
    pose(toile, t, [(s(30) - 0.1, "px_tire"), (tg, "px_gonfle")], 135, 396, 2, 0.15)
    tc = w("cartouche", 32)
    if t >= tc:
        X.coller(toile, icone("px_cartouche", 2), 236, 230, fondu(t, tc, 0.2))
        X.texte(d, (236, 236), "CO2", F16, ORANGE)
    if tg <= t < tg + 0.5:                                  # le gaz qui gonfle
        f = (t - tg) / 0.5
        for i in range(12):
            a = 2 * math.pi * i / 12
            r = 34 + 40 * f
            d.point((round(135 + r * math.cos(a)), round(300 + r * math.sin(a))), fill=BLANC)


# ------------------------------------------------------------------------------------------------ 6. le froid
def e6a(t, toile, d, ph):
    tx = w("vingt", 36)
    ph += [(["Deuxième ennemi :", "le *froid*"], s(34), s(36)), (["L'eau vole la chaleur", "*25 fois* plus vite"], s(36), None)]
    X.coller(toile, icone("px_grelotte", 3), 135, 400, fondu(t, s(34) - 0.1))
    tv = w("vole", 36)
    if t >= tv:
        n = 4 + int(18 * X.lisse((t - tv) / 1.0))
        X.chaleur(d, t, 135, 330, n, 50, 95)
    if t >= tx:
        X.texte(d, (135, 128), f"× {round(1 + 24 * X.sortie((t - tx) / 0.7, 2.5))}", F32, ORANGE)


def e6b(t, toile, d, ph):
    td, tc = w("deux", 37) + 0.25, w("cent", 39)
    ph += [(["L'Hudson, *2009*"], s(37), s(38)), (["Secours en", "*quelques minutes*"], s(38), s(39)),
           (["*155 sur 155*", "ont survécu"], s(39), None)]
    X.coller(toile, icone("px_hudson", 2), 135, 268, fondu(t, s(37) - 0.1))
    if s(37) <= t < s(39) and t >= td:
        X.coller(toile, icone("px_thermometre", 2), 60, 388, fondu(t, td - 0.1, 0.2))
        X.texte(d, (170, 330), f"{round(15 - 13 * X.sortie((t - td) / 0.8, 2.5))} DEGRÉS", F24, ORANGE)
    if s(38) <= t < s(39):
        X.coller(toile, icone("px_chrono", 1), 236, 300, fondu(t, s(38), 0.2))
    if t >= tc:
        n = round(155 * X.sortie((t - tc) / 1.2, 2))
        X.grille_cases(d, 55, 290, 160, n, 32, 4, 5, BV, BV_SOMBRE)
        X.texte(d, (135, 352), f"{n} / 155", F24, ORANGE)


# ------------------------------------------------------------------------------------------------ 7. la position
def e7(t, toile, d, ph):
    tb, tg, ts = w("remonte", 44), w("colle", 46), w("surface", 47)
    ph += [(["On ne *nage* pas"], s(40), w("bouger", 42)), (["Bouger fait fuir", "la *chaleur*"], w("bouger", 42), tb),
           (["Genoux *remontés*,", "bras serrés"], tb, tg), (["On se *colle*", "aux autres"], tg, ts),
           (["Moins de *surface*,", "moins de chaleur perdue"], ts, None)]
    pose(toile, t, [(s(40) - 0.1, "px_nage"), (tb, "px_boule"), (tg, "px_groupe")], 135, 360, 3, 0.25)
    if t < tb:
        n = 10 + int(10 * X.lisse((t - w("bouger", 42)) / 0.8))
    elif t < tg:
        n = 9
    else:
        n = 4
    X.chaleur(d, t, 135, 270, n, 80, 125)
    tn = w("nage", 41)
    if tn <= t < tb:
        d.line([(212, 140), (236, 164)], fill=ORANGE, width=4)
        d.line([(236, 140), (212, 164)], fill=ORANGE, width=4)


# ------------------------------------------------------------------------------------------------ 8. le toboggan
def e8(t, toile, d, ph):
    te = w("enlever", 51)
    ph += [(["Et avant", "le *toboggan*…"], s(49), te), (["une chose", "à *enlever*"], te, None)]
    X.coller(toile, icone("px_toboggan", 3), 135, 330, fondu(t, s(49) - 0.1))
    if t >= te:
        X.coller(toile, icone("px_talon", 2), 90, 420, fondu(t, te, 0.2))
        if int((t - te) * 3) % 2 == 0 or t > te + 1.5:
            X.texte(d, (200, 352), "?", F32, ORANGE)


def fin(t, toile, d, ph):
    d.rectangle([0, 0, X.LW, X.LH], fill=(64, 26, 8))
    ph += [(["Avant le toboggan :", "la chose à *enlever*"], -1.0, None)]
    dx = round(3 * abs(math.sin(t * 5)))
    X.texte(d, (125 + dx, 260), "LA SUITE DEMAIN", F16, BLANC)
    xt = 125 + dx + d.textlength("LA SUITE DEMAIN", font=F16) / 2 + 8
    d.polygon([(xt, 263), (xt, 275), (xt + 9, 269)], fill=ORANGE)
    X.texte(d, (135, 400), "INFORMATION GÉNÉRALE · SUIVEZ L'ÉQUIPAGE", F8, ORANGE)


# ------------------------------------------------------------------------------------------------ montage
def ecrans():
    return [(0.0, e1), (s(5) - 0.25, None), (s(13), e3), (s(21), e4), (s(25), e5a), (s(30), e5b), (s(34), e6a),
            (s(37), e6b), (s(40), e7), (s(49), e8), (e(57) + 0.05, fin)]


def image(t):
    ec = ecrans()
    k = max(i for i, x in enumerate(ec) if x[0] <= t)
    t0, fn = ec[k]
    if fn is None:                                        # Archimède : pixel_archimede.py
        toile, phs, neige = PA.scene(t)
        phrases = [(p[0], p[2], p[3] if len(p) > 3 else None) for p in phs]
        return toile, phrases, neige
    toile = X.fond(t)
    d = ImageDraw.Draw(toile)
    phrases = []
    fn(t, toile, d, phrases)
    neige = max(0.0, 0.85 - (t - t0) / 0.1) if 0 < t0 <= t < t0 + 0.1 else 0.0
    return toile, phrases, neige


def debuts():
    return [x[0] for x in ecrans()[1:]] + [s(7), s(9), s(11)]


def sons():
    ev = [(t0, Z.neige(0.12, 0.18)) for t0 in debuts()]
    ev += [(t0, X.bip(990, 0.06)) for t0 in debuts()]
    ev += [(t, Z.thump(0.35)) for t in [w("seize", 9), w("plafond", 19), w("arrivez", 20), w("gonflé", 29),
                                        w("remplit", 32), w("vingt", 36), w("cent", 39), w("nage", 41)]]
    ev += [(t, Z.boom(0.45, 70)) for t in [w("noyer", 2), w("seize", 10), w("gonflé", 24), w("froid", 35),
                                           w("enlever", 51)]]
    ev += [(w("suite", 3) + 0.1, X.bip(440, 0.15, 0.14)), (w("monte", 14), Z.bulles(2.0, 0.1)),
           (w("tout", 8), Z.bulles(1.6, 0.08)), (w("gonflé", 24), Z.bulles(2.0, 0.1)),
           (w("remplit", 32), Z.souffle(0.5, 0.15, False)), (w("vole", 36), Z.vent(2.5, 0.05, 150, 900)),
           (w("archimède", 6), X.bip(660, 0.12, 0.14)), (w("effort", 12), X.bip(1760, 0.08)),
           (w("sorties", 15), X.bip(1320, 0.06)), (e(57) + 0.05, Z.boom(0.6, 50)), (e(57) + 0.05, Z.riser(0.8, 0.07))]
    for mot, i in [("enfilé", 26), ("serrées", 27), ("cartouche", 32), ("l'hudson", 37), ("minutes", 38),
                   ("remonte", 44), ("colle", 46), ("surface", 47), ("toboggan", 49)]:
        ev.append((w(mot, i), X.bip(1320, 0.06)))
    ev += [(w("seize", 9) + dt, b) for dt, b in X.rafale(900, 16, 0.06, 0.07)]
    ev += [(w("cent", 39) + dt, b) for dt, b in X.rafale(800, 20, 0.06, 0.05)]
    ev += [(w("passagers", 23) + dt, b) for dt, b in X.rafale(1000, 12, 0.08, 0.05)]
    return ev


def mixage(chemin, voix, dur):
    n = int(dur * MI.SR)
    v = np.zeros(n)
    v[:min(n, len(voix))] = voix[:n]
    v *= 10 ** (-16 / 20) / (np.sqrt((v[np.abs(v) > 0.01] ** 2).mean()) + 1e-9)
    nappe = MI.bed(dur + 1)[:n]
    nappe = nappe.mean(1) if nappe.ndim == 2 else nappe
    nappe = nappe / (np.abs(nappe).max() + 1e-9) * 10 ** (-24 / 20)
    tt = np.arange(n) / MI.SR
    for tc in [w("seize", 10), w("vingt", 36), w("enlever", 51)]:   # la nappe se coupe avant les révélations
        nappe *= np.clip(np.maximum(np.abs(tt - (tc - 0.45)) / 0.45, (tt > tc + 0.3) | (tt < tc - 0.9)), 0, 1)
    a = v + nappe
    for t0, snd in sons():
        i = int(t0 * MI.SR)
        k = min(n - i, len(snd))
        if k > 0 and i >= 0:
            a[i:i + k] += 0.6 * snd[:k]
    a *= np.minimum(1, (n - np.arange(n)) / (0.6 * MI.SR))
    a = a / max(1.0, np.abs(a).max() / 0.95)
    with wave.open(chemin, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(MI.SR)
        f.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def preparer():
    M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
    M.SEGS = os.path.join(HERE, "audio", "voix.json")
    voix = M.preparer()
    MV.charger(M)
    return voix


def rendre(sortie, t0=0.0, t1=None):
    voix = preparer()
    dur = M.SEG[-1][1] + 1.8
    t1 = dur if t1 is None else t1
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{X.W}x{X.H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    for f in range(int(t0 * FPS), int(t1 * FPS)):
        t = f / FPS
        toile, phrases, neige = image(t)
        img = X.finition(toile, t, FPS, neige)
        for lignes, ta, tb in phrases:
            X.phrase(img, lignes, 170, t, ta, t1=tb)
        ff.stdin.write(img.tobytes())
        if f % 300 == 0:
            print(f"{t:5.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()
    mixage(f"{tmp}/a.wav", voix, dur)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}",
                    "-i", f"{tmp}/a.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", M.volume_cible(f"{tmp}/a.wav"), "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", sortie], check=True)
    print("OK", sortie)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep29_pixel.mp4"
    if len(sys.argv) > 3:
        rendre(out, float(sys.argv[2]), float(sys.argv[3]))
    else:
        rendre(out)
