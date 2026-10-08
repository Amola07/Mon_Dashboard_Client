"""Test de style « infographie pixel » (bleu-vert + orange) sur la partie « Archimède » de l'épisode 29 (≈ 16 s).

Même voix, mêmes instants (calés au mot) que oscillo_ep29.py ; seul le style change (films/styles/pixel_info.py).
Sortie : l'extrait en style pixel, l'extrait d'origine coupé dans output/ep29.mp4, et la comparaison côte à côte.

    python -m films.episodes.ep29_gilet.pixel_archimede output/ep29_pixel
    → output/ep29_pixel_apres.mp4, output/ep29_pixel_avant.mp4, output/ep29_pixel_comparaison.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import ImageDraw

from films import montage_ia as MI
from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.outils import mots_voix as MV
from films.styles import oscillo_son as Z
from films.styles import pixel_info as X
from films.styles.pixel_info import (BLANC, BV, BV_MOYEN, BV_SOMBRE, F8, F16, F24, F32, GRIS, ORANGE, ORANGE_CLAIR,
                                     ORANGE_SOMBRE)

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
s, e = M.s, M.e


def w(mot, i):
    return MV.mot(mot, s(i))


# ------------------------------------------------------------------------------------------------ icônes pleines
def cube(d, x, y, c=40, p=9):
    """Un cube orange vu de trois quarts : face avant, dessus clair, côté sombre."""
    d.polygon([(x, y), (x + p, y - p), (x + c + p, y - p), (x + c, y)], fill=ORANGE_CLAIR)
    d.polygon([(x + c, y), (x + c + p, y - p), (x + c + p, y + c - p), (x + c, y + c)], fill=ORANGE_SOMBRE)
    d.rectangle([x, y, x + c, y + c], fill=ORANGE)
    for gy in range(y + 3, y + c - 1, 4):                  # une trame dans la face, comme leurs objets
        for gx in range(x + 3 + (gy // 4) % 2 * 2, x + c - 1, 4):
            d.point((gx, gy), fill=ORANGE_SOMBRE)


def gilet(d, cx, cy, k=1.0):
    """Un gilet de sauvetage gonflé : deux boudins reliés au col, lumière à gauche, ombre à droite."""
    def ell(x0, y0, x1, y1, col):
        d.ellipse([cx + x0 * k, cy + y0 * k, cx + x1 * k, cy + y1 * k], fill=col)
    ell(-36, -52, 36, -8, ORANGE_SOMBRE)                    # le col
    ell(-34, -54, 32, -12, ORANGE)
    ell(-18, -44, 18, -20, X.NOIR)                          # le trou pour la tête
    for sgn in (-1, 1):                                    # les deux boudins
        x0 = -40 if sgn < 0 else 4
        ell(x0, -30, x0 + 36, 52, ORANGE_SOMBRE)
        ell(x0, -32, x0 + 32, 48, ORANGE)
        ell(x0 + 4, -24, x0 + 12, 30, ORANGE_CLAIR)        # reflet
    d.rectangle([cx - 4 * k, cy - 10 * k, cx + 4 * k, cy + 40 * k], fill=X.NOIR)
    d.line([(cx - 38 * k, cy + 30 * k), (cx + 38 * k, cy + 30 * k)], fill=BV, width=max(1, int(2 * k)))   # la sangle
    d.rectangle([cx - 3 * k, cy + 42 * k, cx + 3 * k, cy + 50 * k], fill=BLANC)                           # la languette


def tete(d, cx, cy, k=1.0):
    """Une tête de face, sans visage, bonnet bleu-vert (notre personnage)."""
    def r(a):
        return round(a * k)
    d.ellipse([cx - r(8), cy - r(9), cx + r(8), cy + r(9)], fill=BLANC)
    d.ellipse([cx + r(2), cy - r(7), cx + r(8), cy + r(8)], fill=GRIS)
    d.chord([cx - r(9), cy - r(16), cx + r(9), cy + r(2)], 180, 360, fill=BV)
    d.rectangle([cx - r(9), cy - r(8), cx + r(9), cy - r(5)], fill=BV_MOYEN)
    for x in range(cx - r(7), cx + r(8), max(2, r(3))):
        d.line([(x, cy - r(14)), (x, cy - r(9))], fill=BV_MOYEN)


# ------------------------------------------------------------------------------------------------ la scène
CUVE = (72, 196, 198, 350)
NIV0, C = 264, 40


def cube_y(t):
    u = X.lisse((t - w("tout", 8)) / 1.6)
    return 136 + 3 * math.sin(2.4 * t) * (1 - u) + (NIV0 + 34 - 136) * u


def scene(t):
    """(toile basse définition, [phrases en pleine définition], neige)."""
    toile = X.fond(t)
    d = ImageDraw.Draw(toile)
    phrases = []
    T = [s(5) - 0.25, s(7), s(9), s(11)]
    neige = max([max(0.0, 0.85 - (t - t0) / 0.1) for t0 in T[1:] if t0 <= t < t0 + 0.1] + [0.0])

    if t < T[1]:                                          # « La raison, c'est Archimède. »
        phrases.append((["La raison ?"], 170, s(5)))
        ta = w("archimède", 6)
        if t >= ta:
            cal = X.calque()
            dc = ImageDraw.Draw(cal)
            X.texte(dc, (X.LW / 2, 150), "ARCHIMÈDE", F32, ORANGE)
            X.texte(dc, (X.LW / 2, 196), "IIIE SIÈCLE AV. J.-C.", F8, BV)
            if os.path.exists(os.path.join(X.DOSSIER_ICONES, "px_archimede.png")):
                buste = X.icone("px_archimede", 2)
                cal.paste(buste, (round(X.LW / 2 - buste.width / 2), 220), buste)
            X.poser(toile, cal, X.apparition(t, ta, 0.3))
        return toile, phrases, neige

    if t < T[2]:                                          # la cuve et le cube
        tt = w("tout", 8)
        phrases.append((["Dans l'eau, tout est", "poussé vers le *haut*"], 170, s(7)))
        x0, y0, x1, y1 = CUVE
        cal = X.calque()
        dc = ImageDraw.Draw(cal)
        yc = cube_y(t)
        immerge = min(1.0, max(0.0, (yc + C - NIV0) / C))
        niv = NIV0 - round(C * C / (x1 - x0) * immerge)
        cube(dc, (x0 + x1) // 2 - C // 2, round(yc))
        X.eau(dc, x0 + 2, x1 - 1, niv, y1, t)
        tp = w("poids", 8)
        if t >= tp:                                       # l'eau déplacée
            for y in range(niv + 2, NIV0 + 1):
                for x in range(x0 + 3 + y % 2, x1 - 2, 2):
                    dc.point((x, y), fill=ORANGE_SOMBRE)
        dc.rectangle([x0, y0, x0 + 2, y1], fill=BV)
        dc.rectangle([x1 - 2, y0, x1, y1], fill=BV)
        dc.rectangle([x0, y1 - 2, x1, y1], fill=BV)
        X.poser(toile, cal, X.apparition(t, s(7), 0.3))
        if immerge > 0:
            X.fleche_haut(d, (x0 + x1) // 2, round(yc) + C // 2 + 18, round(64 * immerge), 6, BLANC, GRIS)
            X.texte(d, (234, round(yc) - 6), "POUSSÉE", F8, ORANGE)
            X.texte(d, (234, round(yc) + 4), f"{round(100 * immerge)} %", F16, ORANGE)
        if t >= tp:
            X.texte(d, (X.LW / 2, 364), X.tape("= LE POIDS DE L'EAU DÉPLACÉE", (t - tp) / 0.5), F8, ORANGE)
        return toile, phrases, neige

    if t < T[3]:                                          # le gilet : 16 litres → 16 kilos
        tl, tk = w("seize", 9), w("seize", 10)
        phrases.append((["Un gilet gonflé :", "*16 litres* d'air"], 170, s(9), tk))
        phrases.append((["Donc *16 kilos*", "vers le haut"], 170, tk))
        cal = X.calque()
        dc = ImageDraw.Draw(cal)
        monte = round(14 * X.sortie((t - tk) / 0.6)) if t >= tk else 0
        gilet(dc, 82, 262 - monte, 0.95)
        X.poser(toile, cal, X.apparition(t, s(9), 0.3))
        n = 0 if t < tl else min(16, int((t - tl) / 0.06) + 1)
        for i in range(16):                               # 1 case = 1 litre
            gx, gy = 160 + (i % 4) * 20, 196 + (i // 4) * 20
            allume = i < n
            col = (BV if allume else BV_SOMBRE) if t < tk else (BV_MOYEN if allume else BV_SOMBRE)
            d.rectangle([gx, gy, gx + 15, gy + 15], fill=col if allume else None, outline=col)
        if t >= tl:
            X.texte(d, (190, 288), f"{n} L", F24, BLANC if t < tk else GRIS)
            X.texte(d, (190, 318), "1 CASE = 1 LITRE", F8, BV)
        if t >= tk:
            u = X.sortie((t - tk) / 0.5)
            X.fleche_haut(d, 82, 196 - monte, round(56 * u), 10)
            kg = round(16 * X.sortie((t - tk) / 0.7, 2.5))
            X.texte(d, (190, 140), f"{kg} KG", F32, ORANGE)
        return toile, phrases, neige

    phrases.append((["Dehors : *parfait*"], 170, s(11)))     # dehors, on flotte
    te = w("effort", 12)
    cal = X.calque()
    dc = ImageDraw.Draw(cal)
    houle = round(3 * math.sin(1.7 * t))
    surf = 250 + houle
    cx = 135
    for sgn in (-1, 1):                                   # les bras écartés à la surface
        dc.line([(cx + sgn * 34, surf + 10), (cx + sgn * 70, surf + 4)], fill=GRIS, width=8)
    gilet(dc, cx, surf + 44, 0.85)
    tete(dc, cx, surf - 22, 1.7)
    X.eau(dc, 0, X.LW, surf + 12, 420, t)                 # l'eau par-dessus : on voit le corps à travers la trame
    X.poser(toile, cal, X.apparition(t, s(11), 0.35))
    X.fleche_haut(d, cx, surf + 118, round(34 + 4 * math.sin(3 * t)), 8)
    if t >= te:
        u = X.apparition(t, te, 0.25)
        cal2 = X.calque()
        d2 = ImageDraw.Draw(cal2)
        X.coche(d2, 46, 166, BV, 3)
        X.texte(d2, (150, 162), "SANS EFFORT", F16, BV)
        X.poser(toile, cal2, u)
    return toile, phrases, neige


# ------------------------------------------------------------------------------------------------ son
def sons(T0):
    """Effets : un bip par apparition, une rafale pour les cases, un impact par révélation, neige aux transitions."""
    ev = [(s(7), Z.neige(0.12, 0.18)), (s(9), Z.neige(0.12, 0.18)), (s(11), Z.neige(0.12, 0.18)),
          (w("archimède", 6), X.bip(660, 0.12, 0.14)), (w("archimède", 6), Z.thump(0.35)),
          (s(7), X.bip(990, 0.06)), (w("tout", 8) + 1.5, Z.thump(0.3)), (w("poids", 8), X.bip(1320, 0.06)),
          (s(9), X.bip(990, 0.06)), (w("seize", 10), Z.boom(0.5, 70)), (w("seize", 10), X.bip(520, 0.15, 0.14)),
          (s(11), X.bip(990, 0.06)), (w("effort", 12), X.bip(1760, 0.08)), (w("tout", 8), Z.bulles(1.6, 0.08))]
    ev += [(w("seize", 9) + dt, b) for dt, b in X.rafale(900, 16, 0.06, 0.07)]
    return [(t - T0, snd) for t, snd in ev]


def mixage(chemin, voix, T0, T1):
    n = int((T1 - T0) * MI.SR)
    v = np.zeros(n)
    seg = voix[int(T0 * MI.SR):int(T0 * MI.SR) + n]
    v[:len(seg)] = seg
    v *= 10 ** (-16 / 20) / (np.sqrt((v[np.abs(v) > 0.01] ** 2).mean()) + 1e-9)
    nappe = MI.bed(T1 - T0 + 1)[:n]
    nappe = (nappe.mean(1) if nappe.ndim == 2 else nappe)
    nappe = nappe / (np.abs(nappe).max() + 1e-9) * 10 ** (-24 / 20)
    tc = w("seize", 10) - T0                              # la nappe se coupe juste avant « 16 kilos »
    tt = np.arange(n) / MI.SR
    nappe *= np.clip(np.maximum(np.abs(tt - (tc - 0.45)) / 0.45, (tt > tc + 0.3)), 0, 1)
    a = v + nappe
    for t0, snd in sons(T0):
        i = int(t0 * MI.SR)
        k = min(n - i, len(snd))
        if k > 0 and i >= 0:
            a[i:i + k] += 0.6 * snd[:k]
    a = a / max(1.0, np.abs(a).max() / 0.95)
    with wave.open(chemin, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(MI.SR)
        f.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "output/ep29_pixel"
    M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
    M.SEGS = os.path.join(HERE, "audio", "voix.json")
    voix = M.preparer()
    MV.charger(M)
    T0, T1 = s(5) - 0.25, s(13) - 0.05
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{X.W}x{X.H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    for f in range(int((T1 - T0) * FPS)):
        t = T0 + f / FPS
        toile, phrases, neige = scene(t)
        img = X.finition(toile, t, FPS, neige)
        for p in phrases:
            lignes, y, t0 = p[:3]
            X.phrase(img, lignes, y, t, t0, t1=p[3] if len(p) > 3 else None)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    mixage(f"{tmp}/a.wav", voix, T0, T1)
    apres, avant = base + "_apres.mp4", base + "_avant.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", M.volume_cible(f"{tmp}/a.wav"), "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", apres], check=True)
    if os.path.exists("output/ep29.mp4"):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{T0:.3f}", "-t", f"{T1 - T0:.3f}", "-i", "output/ep29.mp4",
                        "-c:v", "libx264", "-crf", "18", "-c:a", "aac", avant], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", avant, "-i", apres, "-filter_complex",
                        "[0:v]fps=30,scale=540:960,drawtext=text='AVANT':x=20:y=20:fontsize=34:fontcolor=white[a];"
                        "[1:v]scale=540:960,drawtext=text='APRES':x=20:y=20:fontsize=34:fontcolor=white[b];"
                        "[a][b]hstack[v]", "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "20", "-c:a", "aac",
                        base + "_comparaison.mp4"], check=True)
    print("OK", apres)


if __name__ == "__main__":
    main()
