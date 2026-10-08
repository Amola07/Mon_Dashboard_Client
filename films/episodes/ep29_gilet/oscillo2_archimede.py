"""Test « oscilloscope 2.0 » sur la partie « Archimède » de l'épisode 29 (≈ 16 s), pour comparer avec la version
actuelle et la version pixel (pixel_archimede.py). Même voix, mêmes instants (calés au mot) ; style :
films/styles/oscillo2.py (quadrillage, hachures de faisceau, texte au faisceau, chiffres en segments, image nette).

    python -m films.episodes.ep29_gilet.oscillo2_archimede output/ep29_osc2
    → output/ep29_osc2.mp4 et output/ep29_trois_styles.mp4 (actuel | pixel | oscilloscope 2.0)
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import montage_ia as MI
from films.episodes.ep29_gilet import pixel_archimede as PA
from films.styles import anim_pro as A
from films.styles import oscillo2 as O
from films.styles import oscillo_son as Z
from films.styles.oscillo2 import AMBRE, VERT, VERT_PALE, VERT_SOMBRE, W, H

M, MV = PA.M, PA.MV
HERE = PA.HERE
FPS = 30
s, e, w = M.s, M.e, PA.w


def phrase(c, t, t0, lignes, y=300, h=64, t1=None):
    """La phrase en haut, écrite par le faisceau ; *…* = en ambre."""
    if t < t0 or (t1 is not None and t >= t1):
        return
    u = (t - t0) / 0.45
    for i, ligne in enumerate(lignes):
        morceaux = ligne.split("*")
        larg = O.largeur_texte(ligne.replace("*", ""), h)
        x = W / 2 - larg / 2
        for j, m in enumerate(morceaux):
            if m:
                O.dessiner(c, O.texte(m, x, y + i * h * 1.45, h, centre=False, gras=True), AMBRE if j % 2 else VERT_PALE,
                           3.2, 1.0, u)
            x += O.largeur_texte(m, h)


def sous_titre(c, t):
    """Une ligne de sous-titres discrète, en bas (3 mots à la fois)."""
    i = max([k for k, m in enumerate(M.MOTS) if m[1] <= t + 0.03] + [-1])
    if i < 0 or t > M.MOTS[i][2] + 0.4:
        return
    deb, rang = M.MOTS[i][3], M.MOTS[i][4]
    g0 = deb + (rang // 3) * 3
    grp = [m for m in M.MOTS[g0:g0 + 3] if m[3] == deb]
    txt = " ".join(m[0] for m in grp)
    O.dessiner(c, O.texte(txt, W / 2, 1720, 34), VERT, 1.6, 0.75)


def fleche_haut(cx, y_bas, long, larg=26):
    if long < 6:
        return []
    yh = y_bas - long
    return [[(cx, y_bas), (cx, yh)], [(cx - larg, yh + larg), (cx, yh), (cx + larg, yh + larg)]]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def vague(x0, x1, y, t, amp=6, lg=110):
    return [[(x, y + amp * math.sin(x / lg * 2 * math.pi + 2.2 * t)) for x in np.arange(x0, x1 + 1, 10)]]


def eau(c, x0, x1, y, y_bas, t, a=1.0):
    """L'eau : une surface brillante qui ondule, et des hachures horizontales qui s'éteignent vers le bas."""
    p = skia.Path()
    p.addRect(skia.Rect(x0, y + 8, x1, y_bas))
    c.save()
    g = skia.GradientShader.MakeLinear([skia.Point(0, y), skia.Point(0, y_bas)],
                                       [skia.Color(255, 255, 255, 255), skia.Color(255, 255, 255, 0)])
    c.saveLayer(None, None)
    O.hachures(c, p, VERT, 11, 0, 1.3, 0.45 * a)
    c.drawRect(skia.Rect(x0, y, x1, y_bas), skia.Paint(Shader=g, BlendMode=skia.BlendMode.kDstIn))
    c.restore()
    c.restore()
    O.dessiner(c, vague(x0, x1, y, t), VERT, 3.2, a)


# ------------------------------------------------------------------------------------------------ formes
CUVE = (290, 800, 790, 1400)
NIV0, C = 1080, 170


def cube_y(t):
    u = A.lisse((t - w("tout", 8)) / 1.6)
    return 560 + 8 * math.sin(2.4 * t) * (1 - u) + (NIV0 + 140 - 560) * u


def faces_cube(x, y, c=C, p=38):
    devant = skia.Path()
    devant.addRect(skia.Rect(x, y, x + c, y + c))
    dessus = skia.Path()
    dessus.addPoly([skia.Point(x, y), skia.Point(x + p, y - p), skia.Point(x + c + p, y - p), skia.Point(x + c, y)], True)
    cote = skia.Path()
    cote.addPoly([skia.Point(x + c, y), skia.Point(x + c + p, y - p), skia.Point(x + c + p, y + c - p),
                  skia.Point(x + c, y + c)], True)
    return devant, dessus, cote


def cube_traits(t):
    y = cube_y(t)
    x = (CUVE[0] + CUVE[2]) / 2 - C / 2 - 19
    out = []
    for f in faces_cube(x, y):
        out += O.contours(f, 8)
    return out


def dessiner_cube(c, t, a=1.0):
    y = cube_y(t)
    x = (CUVE[0] + CUVE[2]) / 2 - C / 2 - 19
    devant, dessus, cote = faces_cube(x, y)
    O.hachures(c, devant, AMBRE, 9, -35, 1.6, 0.75 * a)
    O.hachures(c, dessus, AMBRE, 5, 0, 1.4, 0.9 * a)
    O.hachures(c, cote, AMBRE, 12, 60, 1.4, 0.45 * a)
    for f in (devant, dessus, cote):
        O.dessiner(c, O.contours(f, 8), AMBRE, 3.2, a)
    return y


def gilet_chemin(cx, cy, k=3.4):
    def ell(x0, y0, x1, y1):
        p = skia.Path()
        p.addOval(skia.Rect(cx + x0 * k, cy + y0 * k, cx + x1 * k, cy + y1 * k))
        return p
    p = ell(-34, -54, 32, -12)
    for x0 in (-40, 4):
        p = skia.Op(p, ell(x0, -32, x0 + 32, 48), skia.PathOp.kUnion_PathOp)
    p = skia.Op(p, ell(-18, -44, 18, -20), skia.PathOp.kDifference_PathOp)
    fente = skia.Path()
    fente.addRect(skia.Rect(cx - 4 * k, cy - 10 * k, cx + 4 * k, cy + 40 * k))
    return skia.Op(p, fente, skia.PathOp.kDifference_PathOp)


def dessiner_gilet(c, cx, cy, k=3.4, a=1.0, u=1.0):
    p = gilet_chemin(cx, cy, k)
    O.hachures(c, p, AMBRE, 8, -35, 1.6, 0.7 * a, u)
    O.dessiner(c, O.contours(p, 8), AMBRE, 3.4, a, u)
    O.dessiner(c, [[(cx - 38 * k, cy + 30 * k), (cx + 38 * k, cy + 30 * k)]], VERT, 2.4, a, u)   # la sangle


def tete(cx, cy, r=44):
    visage = skia.Path()
    visage.addCircle(cx, cy, r)
    bonnet = skia.Path()
    bonnet.addArc(skia.Rect(cx - r - 4, cy - r * 1.75, cx + r + 4, cy + r * 0.25), 180, 180)
    bonnet.close()
    return visage, bonnet


# ------------------------------------------------------------------------------------------------ les écrans
def lissajous(t, cx=540, cy=1300, r=200):
    return [[(cx + r * math.sin(3 * u + 0.4 * t), cy + r * 0.8 * math.sin(2 * u)) for u in np.linspace(0, 2 * math.pi, 240)]]


def ecran_a(c, t, a=1.0):
    phrase(c, t, s(5), ["La raison ?"])
    O.dessiner(c, lissajous(t), VERT, 1.8, 0.35 * a)
    ta = w("archimède", 6)
    if t >= ta:
        O.dessiner(c, O.texte("ARCHIMÈDE", W / 2, 880, 112, gras=True), AMBRE, 3.4, a, (t - ta) / 0.5)
        O.dessiner(c, O.texte("IIIe SIÈCLE AV. J.-C.", W / 2, 960, 34), VERT, 1.8, 0.8 * a, (t - ta - 0.3) / 0.4)


def ecran_b(c, t, a=1.0):
    phrase(c, t, s(7), ["Dans l'eau, tout est", "poussé vers le *haut*"])
    x0, y0, x1, y1 = CUVE
    yc = cube_y(t)
    imm = min(1.0, max(0.0, (yc + C - NIV0) / C))
    niv = NIV0 - C * C / (x1 - x0) * imm
    tp = w("poids", 8)
    if t >= tp:                                            # l'eau déplacée
        bande = skia.Path()
        bande.addRect(skia.Rect(x0 + 6, niv + 8, x1 - 6, NIV0 + 8))
        O.hachures(c, bande, AMBRE, 6, 0, 1.6, 0.8 * a, (t - tp) / 0.4)
    dessiner_cube(c, t, a)
    eau(c, x0 + 6, x1 - 6, niv, y1 - 6, t, a)
    O.dessiner(c, [[(x0, y0), (x0, y1), (x1, y1), (x1, y0)]], VERT_PALE, 5, a)
    if imm > 0:
        cx = (x0 + x1) / 2
        O.dessiner(c, fleche_haut(cx, yc + C / 2 + 120, 280 * imm, 30), VERT_PALE, 5, a)
        O.dessiner(c, O.texte("POUSSÉE", 930, yc + 10, 30), AMBRE, 1.8, a)
        O.dessiner(c, O.segments(f"{round(100 * imm):3d}", 930, yc + 110, 80), AMBRE, 4, a)
    if t >= tp:
        O.dessiner(c, O.texte("= LE POIDS DE L'EAU DÉPLACÉE", W / 2, 1490, 34), AMBRE, 2, a, (t - tp) / 0.6)


def ecran_c(c, t, a=1.0):
    tl, tk = w("seize", 9), w("seize", 10)
    phrase(c, t, s(9), ["Un gilet gonflé :", "*16 litres* d'air"], t1=tk)
    phrase(c, t, tk, ["Donc *16 kilos*", "vers le haut"])
    monte = 60 * A.sortie((t - tk) / 0.6) if t >= tk else 0
    dessiner_gilet(c, 330, 1060 - monte, 3.4, a, (t - s(9) + 0.25) / 0.5)
    n = 0 if t < tl else min(16, int((t - tl) / 0.06) + 1)
    for i in range(16):                                    # 1 case = 1 litre
        gx, gy = 640 + (i % 4) * 78, 820 + (i // 4) * 78
        case = skia.Path()
        case.addRect(skia.Rect(gx, gy, gx + 62, gy + 62))
        if i < n:
            O.hachures(c, case, VERT, 7, -35, 1.4, (0.8 if t < tk else 0.4) * a)
            O.dessiner(c, [rect(gx, gy, gx + 62, gy + 62)], VERT_PALE if t < tk else VERT, 2.4, a)
        else:
            O.dessiner(c, [rect(gx, gy, gx + 62, gy + 62)], VERT_SOMBRE, 1.6, 0.8 * a)
    if t >= tl:
        O.dessiner(c, O.segments(f"{n:2d}", 790, 1260, 110), VERT_PALE if t < tk else VERT, 5, a)
        O.dessiner(c, O.texte("L", 935, 1260, 70), VERT_PALE if t < tk else VERT, 3, a)
        O.dessiner(c, O.texte("1 CASE = 1 LITRE", 795, 1330, 30), VERT, 1.6, 0.8 * a)
    if t >= tk:
        u = A.sortie((t - tk) / 0.5)
        O.dessiner(c, fleche_haut(330, 780 - monte, 230 * u, 40), AMBRE, 8, a)
        kg = round(16 * A.sortie((t - tk) / 0.7, 2.5))
        O.dessiner(c, O.segments(f"{kg:2d}", 760, 700, 130), AMBRE, 6, a)
        O.dessiner(c, O.texte("KG", 870, 700, 80, centre=False, gras=True), AMBRE, 3.4, a)


def ecran_d(c, t, a=1.0):
    phrase(c, t, s(11), ["Dehors : *parfait*"])
    surf = 1040 + 10 * math.sin(1.7 * t)
    cx = 540
    for sgn in (-1, 1):
        O.dessiner(c, [O.lisser([(cx + sgn * 120, surf + 30), (cx + sgn * 200, surf + 20), (cx + sgn * 270, surf + 8)])],
                   VERT_PALE, 7, a)
    dessiner_gilet(c, cx, surf + 120, 3.0, a)
    visage, bonnet = tete(cx, surf - 80)
    O.hachures(c, bonnet, VERT, 7, 0, 1.6, 0.8 * a)
    O.dessiner(c, O.contours(bonnet, 6), VERT_PALE, 3.4, a)
    O.dessiner(c, O.contours(visage, 6), VERT_PALE, 3.4, a)
    eau(c, 70, W - 70, surf + 40, 1560, t, a)
    O.dessiner(c, fleche_haut(cx, surf + 420, 110 + 12 * math.sin(3 * t), 26), AMBRE, 6, a)
    te = w("effort", 12)
    if t >= te:
        O.dessiner(c, [[(150, 600), (180, 630), (230, 560)]], VERT_PALE, 6, a, (t - te) / 0.25)
        O.dessiner(c, O.texte("SANS EFFORT", 590, 630, 64, gras=True), VERT_PALE, 3, a, (t - te - 0.1) / 0.4)


# ------------------------------------------------------------------------------------------------ enchaînements
def bornes():
    return [s(5) - 0.25, s(7), s(9), s(11), s(13) - 0.05]


ECRANS = [ecran_a, ecran_b, ecran_c, ecran_d]


def heros(i, t):
    """Le dessin qui passe d'un écran au suivant (à l'enchaînement i : écran i-1 → écran i)."""
    if i == 1:
        return O.texte("ARCHIMÈDE", W / 2, 880, 112), cube_traits(s(7) + 0.25)
    if i == 2:
        return cube_traits(s(9) - 0.25), O.contours(gilet_chemin(330, 1060, 3.4), 8)
    return O.contours(gilet_chemin(330, 1060 - 60, 3.4), 8), O.contours(gilet_chemin(540, 1040 + 120, 3.0), 8)


def image(c, t):
    O.ecran(c, t)
    b = bornes()
    k = max(i for i in range(4) if b[i] <= t)
    for i in range(1, 4):                                  # enchaînement : les deux écrans se fondent, le héros se transforme
        if b[i] - 0.25 <= t < b[i] + 0.25:
            u = (t - b[i] + 0.25) / 0.5
            c.saveLayerAlpha(None, int(255 * (1 - A.lisse(u / 0.6))))
            ECRANS[i - 1](c, t)
            c.restore()
            c.saveLayerAlpha(None, int(255 * A.lisse((u - 0.4) / 0.6)))
            ECRANS[i](c, t)
            c.restore()
            ha, hb = heros(i, t)
            for tr, it in A.flux(("osc2", i), ha, hb, u):
                O.dessiner(c, tr, AMBRE, 3.2, it)
            break
    else:
        tk = w("seize", 10)                                # un seul coup de caméra : sur « seize kilos »
        z = 1 + 0.05 * math.exp(-6 * (t - tk)) if t >= tk else 1.0
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        ECRANS[k](c, t)
        c.restore()
    sous_titre(c, t)


# ------------------------------------------------------------------------------------------------ son et rendu
def sons():
    ev = [(w("archimède", 6), Z.pince(659.3, 0.1)), (w("archimède", 6), Z.thump(0.3)), (s(7), Z.whoosh(0.5, 0.07)),
          (s(9), Z.whoosh(0.5, 0.07)), (s(11), Z.whoosh(0.5, 0.07)), (w("tout", 8), Z.bulles(1.6, 0.08)),
          (w("tout", 8) + 1.5, Z.thump(0.3)), (w("poids", 8), Z.chirp(400, 900, 0.4, 0.06)),
          (w("seize", 10), Z.boom(0.5, 70)), (w("seize", 10), Z.chirp(300, 1200, 0.5, 0.07)),
          (w("effort", 12), Z.pince(1046.5, 0.08)), (s(5), Z.chirp(600, 1200, 0.3, 0.05))]
    ev += [(w("seize", 9) + 0.06 * i, Z.pince(523.3 * 2 ** (i / 12), 0.05, 0.25)) for i in range(16)]
    return ev


def mixage(chemin, voix, T0, T1):
    n = int((T1 - T0) * MI.SR)
    v = np.zeros(n)
    seg = voix[int(T0 * MI.SR):int(T0 * MI.SR) + n]
    v[:len(seg)] = seg
    v *= 10 ** (-16 / 20) / (np.sqrt((v[np.abs(v) > 0.01] ** 2).mean()) + 1e-9)
    nappe = MI.bed(T1 - T0 + 1)[:n]
    nappe = nappe.mean(1) if nappe.ndim == 2 else nappe
    nappe = nappe / (np.abs(nappe).max() + 1e-9) * 10 ** (-24 / 20)
    tt = np.arange(n) / MI.SR
    tc = w("seize", 10) - T0
    nappe *= np.clip(np.maximum(np.abs(tt - (tc - 0.45)) / 0.45, (tt > tc + 0.3) | (tt < tc - 0.9)), 0, 1)
    a = v + nappe
    for t0, snd in sons():
        i = int((t0 - T0) * MI.SR)
        k = min(n - i, len(snd))
        if k > 0 and i >= 0:
            a[i:i + k] += 0.6 * snd[:k]
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
    alignes = iter(MV.MOTS)                                # les sous-titres suivent l'instant réel des mots
    for i, (mot, a, b, deb, rang) in enumerate(M.MOTS):
        if any(ch.isalnum() for ch in mot):
            a2, b2, _ = next(alignes)
            M.MOTS[i] = (mot, a2, b2, deb, rang)
    return voix


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "output/ep29_osc2"
    voix = preparer()
    T0, T1 = bornes()[0], bornes()[-1]
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    for f in range(int((T1 - T0) * FPS)):
        t = T0 + f / FPS
        c = surf.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        image(c, t)
        if prec is not None:                               # traînée très brève du phosphore
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=0.35, BlendMode=skia.BlendMode.kLighten))
        prec = surf.makeImageSnapshot()
        ff.stdin.write(O.finition(prec.toarray(), t, FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    mixage(f"{tmp}/a.wav", voix, T0, T1)
    sortie = base + ".mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", M.volume_cible(f"{tmp}/a.wav"), "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", sortie], check=True)
    if os.path.exists("output/ep29_pixel_avant.mp4") and os.path.exists("output/ep29_pixel_apres.mp4"):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "output/ep29_pixel_avant.mp4", "-i", "output/ep29_pixel_apres.mp4",
                        "-i", sortie, "-filter_complex",
                        "[0:v]fps=30,scale=360:640,drawtext=text='ACTUEL':x=14:y=14:fontsize=26:fontcolor=white[a];"
                        "[1:v]scale=360:640,drawtext=text='PIXEL':x=14:y=14:fontsize=26:fontcolor=white[b];"
                        "[2:v]scale=360:640,drawtext=text='OSCILLO 2.0':x=14:y=14:fontsize=26:fontcolor=white[c];"
                        "[a][b][c]hstack=3[v]", "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-crf", "20", "-c:a", "aac",
                        "output/ep29_trois_styles.mp4"], check=True)
    print("OK", sortie)


if __name__ == "__main__":
    main()
