"""Démo animée style « oscilloscope » (12 s, sans voix) : l'ascenseur en coupe tracé au faisceau, le câble qui casse,
la chute en vraie physique avec la courbe de vitesse tracée en direct, le saut comparé, puis le frein de sécurité.

Rendu : traits verts phosphorescents (3 passes : halo large, halo moyen, trait net), persistance (l'image précédente
s'efface lentement → traînées), point brillant du faisceau en tête de chaque tracé, lignes de balayage, vignette,
léger scintillement. Son : un bip par élément tracé, impact grave à chaque révélation, nappe coupée avant le frein.

    python -m films.styles.oscillo_ascenseur output/demo_oscillo_ascenseur.mp4
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
from films.episodes.ep01_triangle import ep01 as E1

W, H, FPS, DUR = 1080, 1920, 30, 12.0
HERE = os.path.dirname(os.path.abspath(__file__))
MONO = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "fonts", "JetBrainsMono.ttf"))
VERT = (90, 255, 140)
VERT_PALE = (200, 255, 215)
AMBRE = (255, 196, 90)                                     # seule couleur d'accent : ce qui est dangereux / important

X0, X1, Y0, Y1 = 300, 780, 470, 1430                       # la tour
G0, G1 = 470, 610                                          # la gaine
CAB = 110
T_TITRE, T_TOUR, T_CABINE, T_RUPTURE = 0.2, 1.4, 3.0, 3.8
G_REEL, H_REEL, FREIN_FRAC = 9.81, 30.0, 0.86
T_CHUTE = math.sqrt(2 * H_REEL * FREIN_FRAC / G_REEL)
T_FREIN = T_RUPTURE + T_CHUTE
D_FREIN = 0.4
T_SILENCE = T_FREIN - 0.7                                  # la nappe se coupe juste avant la révélation


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def P(col, w, a=255, blur=0.0, fill=False):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*col, int(max(0, min(255, a)))))
    if not fill:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def cercle_pts(cx, cy, r, n=24):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


def faisceau(c, traits, u, col=VERT, w=1.0, intense=1.0):
    """Trace la fraction u d'une liste de lignes brisées (dans l'ordre), avec halo phosphore et point brillant en tête."""
    if u <= 0:
        return
    long = [sum(math.dist(p, q) for p, q in zip(tr, tr[1:])) for tr in traits]
    reste = sum(long) * min(1.0, u)
    path = skia.Path()
    tete = None
    for tr, L in zip(traits, long):
        if reste <= 0:
            break
        path.moveTo(*tr[0])
        if reste >= L:
            for q in tr[1:]:
                path.lineTo(*q)
            reste -= L
            continue
        for p0, p1 in zip(tr, tr[1:]):
            d = math.dist(p0, p1)
            if reste >= d:
                path.lineTo(*p1)
                reste -= d
            else:
                k = reste / d if d else 0
                tete = (p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k)
                path.lineTo(*tete)
                reste = 0
                break
        break
    for wl, a, b in ((14 * w, 40, 16), (6 * w, 110, 5), (2.2 * w, 255, 0)):
        c.drawPath(path, P(col, wl, a * intense, b))
    if tete is not None:
        c.drawCircle(*tete, 9, P((235, 255, 240), 0, 200, 8, fill=True))
        c.drawCircle(*tete, 3.5, P((255, 255, 255), 0, 255, fill=True))


def ecrit(c, s, x, y, taille, col=VERT_PALE, u=1.0, centre=False):
    n = int(len(s) * min(1.0, max(0.0, u)))
    if n <= 0:
        return
    f = skia.Font(MONO, taille)
    if centre:
        x -= f.measureText(s) / 2
    c.drawString(s[:n], x, y, f, P(col, 0, 255, 6, fill=True))
    c.drawString(s[:n], x, y, f, P(col, 0, 255, fill=True))


def tour():
    return [rect_pts(X0, Y0, X1, Y1), [(G0, Y0), (G0, Y1)], [(G1, Y0), (G1, Y1)], [(140, Y1), (940, Y1)],
            rect_pts(G0 + 20, Y0 - 60, G1 - 20, Y0)]


def etages():
    tr = []
    for e in range(1, 10):
        y = Y0 + e * (Y1 - Y0) / 10
        tr += [[(X0, y), (G0, y)], [(G1, y), (X1, y)]]
        for wx in list(range(X0 + 30, G0 - 20, 46)) + list(range(G1 + 24, X1 - 30, 46)):
            tr.append(rect_pts(wx, y - 70, wx + 22, y - 40))
    return tr


def etat(t):
    yh = Y0 + 6
    course = (Y1 - 8 - CAB) - yh
    if t < T_RUPTURE:
        return yh, 0.0, "repos"
    tc = t - T_RUPTURE
    if tc < T_CHUTE:
        return yh + course * 0.5 * G_REEL * tc ** 2 / H_REEL, G_REEL * tc, "chute"
    v0 = G_REEL * T_CHUTE
    tf = min(tc - T_CHUTE, D_FREIN)
    a = v0 / D_FREIN
    d = H_REEL * FREIN_FRAC + v0 * tf - 0.5 * a * tf ** 2
    return yh + course * d / H_REEL, max(0.0, v0 - a * tf), ("frein" if tc - T_CHUTE < D_FREIN else "arret")


def cabine(c, y, t, phase, col):
    cx = (G0 + G1) / 2
    faisceau(c, [rect_pts(G0 + 14, y, G1 - 14, y + CAB)], ease((t - T_CABINE) / 0.5), col, 1.2)
    if t < T_CABINE + 0.4:
        return
    k = ease((t - T_RUPTURE) / 0.6) if phase == "chute" else 0.0
    if phase in ("frein", "arret"):                                           # allongé au sol
        q = [cercle_pts(cx - 34, y + CAB - 16, 8), [(cx - 24, y + CAB - 14), (cx + 34, y + CAB - 12)],
             [(cx - 10, y + CAB - 16), (cx - 34, y + CAB - 30)]]
        faisceau(c, q, 1.0, col, 1.0)
        return
    fl = 18 * k + 3 * math.sin(t * 7) * k
    hy = y + 32 - fl
    br = 6 + 22 * k                                                           # bras qui montent en apesanteur
    jb = 12 * k
    q = [cercle_pts(cx, hy, 9), [(cx, hy + 10), (cx, hy + 44)],
         [(cx - 20, hy + 18 - br), (cx, hy + 18), (cx + 20, hy + 18 - br)],
         [(cx - 14, hy + 64 - jb), (cx, hy + 44), (cx + 16, hy + 62 - jb)]]
    faisceau(c, q, ease((t - T_CABINE - 0.3) / 0.4), col, 1.0)


# graphe vitesse/temps en bas (le « vrai » oscilloscope)
GX0, GX1, GY0, GY1 = 120, 960, 1560, 1780


def graphe(c, t):
    if t < T_RUPTURE - 0.4:
        return
    u = ease((t - T_RUPTURE + 0.4) / 0.4)
    faisceau(c, [rect_pts(GX0, GY0, GX1, GY1)], u, VERT, 0.5, 0.7)
    for i in range(1, 8):                                                     # graduations
        x = GX0 + (GX1 - GX0) * i / 8
        c.drawLine(x, GY0, x, GY1, P(VERT, 1, 35))
    for i in range(1, 4):
        y = GY0 + (GY1 - GY0) * i / 4
        c.drawLine(GX0, y, GX1, y, P(VERT, 1, 35))
    ecrit(c, "VITESSE (km/h)", GX0, GY0 - 16, 26, VERT, u * 2)
    if t < T_RUPTURE:
        return
    trace = []
    tmax = T_CHUTE + D_FREIN + 1.2
    n = 0
    for i in range(0, 241):
        tt = T_RUPTURE + tmax * i / 240
        if tt > t:
            break
        _, v, _ = etat(tt)
        x = GX0 + (GX1 - GX0) * i / 240
        y = GY1 - (GY1 - GY0) * min(1, v * 3.6 / 100)
        trace.append((x, y))
        dernier = (x, y)
        n += 1
    if n > 1:
        faisceau(c, [trace], 1.0, AMBRE, 1.2)
        c.drawCircle(*dernier, 8, P((255, 240, 210), 0, 220, 6, fill=True))
    if t > T_RUPTURE + 1.2:                                                    # seuil du meilleur saut
        ys = GY1 - (GY1 - GY0) * 11 / 100
        faisceau(c, [[(GX0, ys), (GX1, ys)]], ease((t - T_RUPTURE - 1.2) / 0.5), VERT, 0.6)
        ecrit(c, "SAUT HUMAIN : 11", GX1 - 300, ys - 10, 24, VERT, (t - T_RUPTURE - 1.3) / 0.5)


ETINCELLES = []
RNG = np.random.default_rng(3)


def scene(c, t):
    # titre
    ecrit(c, "SI L'ASCENSEUR TOMBE", W / 2, 170, 58, VERT_PALE, (t - T_TITRE) / 0.9, True)
    ecrit(c, "SAUTER AU DERNIER MOMENT ?", W / 2, 240, 38, VERT, (t - T_TITRE - 0.6) / 0.9, True)
    # tour tracée au faisceau
    faisceau(c, tour(), ease((t - T_TOUR) / 1.0), VERT, 1.0)
    faisceau(c, etages(), ease((t - T_TOUR - 0.5) / 1.2), VERT, 0.6, 0.6)
    if t > T_TOUR + 1.0:
        ecrit(c, "30 m", X0 - 140, (Y0 + Y1) / 2, 32, VERT, (t - T_TOUR - 1.0) / 0.4)
        faisceau(c, [[(X0 - 50, Y0), (X0 - 50, Y1)]], ease((t - T_TOUR - 1.0) / 0.5), VERT, 0.5, 0.6)
    if t < T_CABINE:
        return
    y, v, phase = etat(t)
    col = AMBRE if phase != "repos" else VERT
    cm = (G0 + G1) / 2
    if t < T_RUPTURE:
        cable = [[(cm, Y0 - 14), (cm, y)]]
    else:
        bout = max(1, 60 - (t - T_RUPTURE) * 120)
        cable = [[(cm, Y0 - 14), (cm + 4, Y0 - 14 + bout)]]
    faisceau(c, cable, ease((t - T_CABINE) / 0.4), VERT, 0.8)
    cabine(c, y, t, phase, col)
    # étincelles (points brillants qui retombent)
    if phase in ("chute", "frein"):
        for _ in range(3 if phase == "chute" else 14):
            sx = G0 + 14 if RNG.random() < 0.5 else G1 - 14
            ETINCELLES.append([sx, y + RNG.uniform(0, CAB), RNG.uniform(-4, 4), RNG.uniform(-9, -2), 1.0])
    for e in ETINCELLES:
        e[0] += e[2]
        e[1] += e[3]
        e[3] += 0.8
        e[4] -= 0.05
    ETINCELLES[:] = [e for e in ETINCELLES if e[4] > 0]
    for e in ETINCELLES:
        c.drawCircle(e[0], e[1], 3, P(AMBRE, 0, 255 * e[4], 3, fill=True))
    # lectures
    kmh = v * 3.6
    etage = max(0.0, 10 - (y - Y0 - 6) / ((Y1 - Y0) / 10))
    ecrit(c, f"ÉTAGE {etage:04.1f}", 760, 640, 30, VERT)
    ecrit(c, f"{kmh:3.0f} km/h", 760, 690, 44, AMBRE if kmh > 1 else VERT_PALE)
    if phase == "chute" and t > T_RUPTURE + 0.5:
        ecrit(c, "APESANTEUR", G1 + 20, y + 40, 28, VERT_PALE, (t - T_RUPTURE - 0.5) / 0.4)
    if T_RUPTURE <= t < T_RUPTURE + 0.8 and int(t * 12) % 2 == 0:
        ecrit(c, "! CÂBLE ROMPU", W / 2, 360, 48, AMBRE, 1, True)
    if phase in ("frein", "arret"):
        ecrit(c, "FREIN DE SÉCURITÉ", W / 2, 340, 52, AMBRE, (t - T_FREIN) / 0.5, True)
        ecrit(c, "ACTIVÉ", W / 2, 400, 40, VERT_PALE, (t - T_FREIN - 0.4) / 0.3, True)
    if t > T_FREIN + 2.2:
        ecrit(c, "LA PHYSIQUE EST DE TON CÔTÉ", W / 2, 1880, 34, VERT_PALE, (t - T_FREIN - 2.2) / 1.0, True)
    graphe(c, t)


def ecran(c, t):
    for y in range(0, H, 4):                                                  # lignes de balayage
        c.drawLine(0, y, W, y, P((0, 0, 0), 2, 80))
    g = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1150, [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 220)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))
    if T_RUPTURE <= t < T_RUPTURE + 0.12 or T_FREIN <= t < T_FREIN + 0.1:      # flash à la rupture et au freinage
        c.drawRect(skia.Rect(0, 0, W, H), P((200, 255, 215), 0, 70, fill=True))


def render(out):
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    for f in range(int(DUR * FPS)):
        t = f / FPS
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        if prec is not None:                                                  # persistance du phosphore
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), P((0, 0, 0), 0, 150, fill=True))
        c.save()
        if T_RUPTURE <= t < T_RUPTURE + 0.25 or T_FREIN <= t < T_FREIN + D_FREIN:  # secousse
            c.translate(RNG.normal(0, 6), RNG.normal(0, 3))
        scene(c, t)
        c.restore()
        prec = surf.makeImageSnapshot()
        ecran(c, t)
        img = surf.makeImageSnapshot()
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    # --- son
    n = int(DUR * MI.SR)
    nappe = MI.bed(DUR)[:n]
    nappe = (nappe.mean(1) if nappe.ndim == 2 else nappe) * 0.35
    tt = np.arange(n) / MI.SR
    coupe = np.ones(n)
    coupe[(tt > T_SILENCE) & (tt < T_FREIN)] = 0.0                            # silence avant la révélation
    a = nappe * np.convolve(coupe, np.ones(2400) / 2400, "same")
    ev = [(T_TITRE + 0.07 * i, E1.pop_s(1700 + 20 * (i % 5), 0.025)) for i in range(20)]       # titre tapé
    ev += [(T_TOUR + 0.1 * i, E1.pop_s(1200 + 40 * (i % 6), 0.03)) for i in range(16)]          # tracé de la tour
    ev += [(T_CABINE, E1.pop_s(880, 0.10)), (T_RUPTURE, E1.pop_s(160, 0.45)), (T_RUPTURE + 0.01, E1.pop_s(2600, 0.15)),
           (T_RUPTURE + 1.2, E1.pop_s(990, 0.07)), (T_FREIN, E1.pop_s(140, 0.5)), (T_FREIN + 0.02, E1.pop_s(3000, 0.2)),
           (T_FREIN + 2.2, E1.ding(784, 0.14))]
    ev += [(T_RUPTURE + 0.2 + 0.2 * i, E1.pop_s(1400 + 80 * i, 0.03)) for i in range(int(T_CHUTE / 0.2))]  # tension
    for t0, snd in ev:
        snd = np.interp(np.arange(int(len(snd) * MI.SR / E1.SR)) * E1.SR / MI.SR, np.arange(len(snd)), snd)
        i = int(t0 * MI.SR)
        k = min(n - i, len(snd))
        a[i:i + k] += snd[:k]
    a = a / (np.abs(a).max() + 1e-9) * 0.8
    with wave.open(f"{tmp}/a.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(MI.SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/demo_oscillo_ascenseur.mp4")
