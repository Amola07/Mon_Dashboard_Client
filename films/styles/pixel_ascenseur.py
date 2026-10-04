"""Démo « infographie pixel » (10 s, sans voix) : la tour vue en coupe comme aux rayons X, une cabine d'ascenseur avec
une personne dedans, le câble qui casse, la chute (étages et vitesse en direct, apesanteur), puis le frein de sécurité.

Tout est dessiné en code sur une petite toile de 270 × 480 px puis agrandi ×4 sans lissage (vrais pixels), avec une
trame de points, un léger halo sur les couleurs vives et du grain. Palette maison : bleu-vert + orange sur noir.

    python -m films.styles.pixel_ascenseur output/demo_pixel_ascenseur.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1

LW, LH, K = 270, 480, 4                                   # toile basse définition et facteur d'agrandissement
W, H, FPS, DUR = LW * K, LH * K, 30, 10.0
HERE = os.path.dirname(os.path.abspath(__file__))
F8 = ImageFont.truetype(os.path.join(HERE, "..", "fonts", "Silkscreen-Regular.ttf"), 8)
F16 = ImageFont.truetype(os.path.join(HERE, "..", "fonts", "Silkscreen-Bold.ttf"), 16)

NOIR = (6, 10, 12)
BV = (40, 175, 175)                                        # bleu-vert vif
BV_SOMBRE = (16, 58, 62)
ORANGE = (255, 138, 61)
BLANC = (232, 240, 238)

# géométrie de la tour (toile basse définition)
X0, X1 = 70, 200
TOIT, SOL = 92, 412
ETAGES = 10
HE = (SOL - TOIT) / ETAGES                                 # hauteur d'un étage en pixels
GX0, GX1 = 118, 152                                        # gaine
CAB = 28                                                   # côté de la cabine

# chronologie (s)
T_TOUR, T_CABINE, T_RUPTURE = 0.0, 1.2, 2.6
G_REEL = 9.81
H_REEL = 30.0                                              # 10 étages ≈ 30 m
FREIN_FRAC = 0.86                                          # le frein agit à 86 % de la hauteur
T_CHUTE = math.sqrt(2 * H_REEL * FREIN_FRAC / G_REEL)      # ≈ 2,3 s de chute libre réelle
T_FREIN = T_RUPTURE + T_CHUTE
D_FREIN = 0.45


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def etat(t):
    """Position verticale de la cabine (px, haut de cabine), vitesse (m/s), phase."""
    y_haut = TOIT + 3
    course = (SOL - 3 - CAB) - y_haut
    if t < T_RUPTURE:
        return y_haut, 0.0, "repos"
    tc = t - T_RUPTURE
    if tc < T_CHUTE:
        d = 0.5 * G_REEL * tc ** 2
        return y_haut + course * d / H_REEL, G_REEL * tc, "chute"
    v0 = G_REEL * T_CHUTE
    tf = min(tc - T_CHUTE, D_FREIN)
    a = v0 / D_FREIN
    d = H_REEL * FREIN_FRAC + v0 * tf - 0.5 * a * tf ** 2
    v = max(0.0, v0 - a * tf)
    return y_haut + course * d / H_REEL, v, ("frein" if tc - T_CHUTE < D_FREIN else "arret")


def texte(d, xy, s, f=F8, col=BLANC, centre=False):
    x, y = xy
    if centre:
        x -= d.textlength(s, font=f) / 2
    d.text((round(x), round(y)), s, font=f, fill=col)


def tape(s, u):
    n = int(len(s) * min(1.0, max(0.0, u)))
    return s[:n]


def crochets(d, r, col, l=5):
    x0, y0, x1, y1 = r
    for x, y, dx, dy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(x, y), (x + dx * l, y)], fill=col)
        d.line([(x, y), (x, y + dy * l)], fill=col)


def personne(d, cx, cy, pose, col=BLANC):
    """Petit personnage pixel (≈ 8 × 16) ; pose : 'debout', 'flotte' (k 0..1) ou 'allonge'."""
    if pose == "allonge":
        d.rectangle([cx - 8, cy + 9, cx - 5, cy + 12], fill=col)            # tête
        d.line([(cx - 4, cy + 11), (cx + 6, cy + 11)], fill=col)              # corps
        d.line([(cx + 6, cy + 11), (cx + 9, cy + 12)], fill=col)
        d.line([(cx - 2, cy + 10), (cx - 6, cy + 8)], fill=col)               # bras sur la tête
        return
    k = 0.0 if pose == "debout" else pose
    d.rectangle([cx - 2, cy - 8, cx + 1, cy - 5], fill=col)                  # tête
    d.line([(cx, cy - 4), (cx, cy + 2)], fill=col)                            # buste
    br = int(2 + 4 * k)                                                       # les bras se lèvent en apesanteur
    d.line([(cx, cy - 2), (cx - 3, cy - 2 - br // 2)], fill=col)
    d.line([(cx, cy - 2), (cx + 3, cy - 2 - br // 2)], fill=col)
    jb = int(3 * k)                                                           # les jambes se replient
    d.line([(cx, cy + 2), (cx - 2, cy + 7 - jb)], fill=col)
    d.line([(cx, cy + 2), (cx + 2, cy + 7 - jb)], fill=col)


RNG = np.random.default_rng(7)
ETINCELLES = []


def image(t):
    im = Image.new("RGB", (LW, LH), NOIR)
    d = ImageDraw.Draw(im)
    # --- titre
    rupture = T_RUPTURE <= t < T_RUPTURE + 0.9
    if not rupture and t < T_FREIN:                                            # le titre cède la place aux alertes
        texte(d, (LW / 2, 26), tape("SI L'ASCENSEUR TOMBE", t / 0.8), F16, ORANGE, centre=True)
        texte(d, (LW / 2, 48), tape("SAUTER AU DERNIER MOMENT ?", (t - 0.5) / 0.8), F8, BLANC, centre=True)
    # --- la tour en coupe, révélée de haut en bas
    rev = TOIT + (SOL - TOIT) * ease((t - T_TOUR) / 1.0)
    for e in range(ETAGES + 1):
        y = round(TOIT + e * HE)
        if y > rev:
            break
        d.line([(X0, y), (GX0 - 1, y)], fill=BV_SOMBRE)
        d.line([(GX1 + 1, y), (X1, y)], fill=BV_SOMBRE)
        if e < ETAGES:
            texte(d, (X0 - 22, y + HE / 2 - 4), f"{ETAGES - e:02d}", F8, BV_SOMBRE)
            for wx in range(X0 + 8, GX0 - 6, 10):                              # fenêtres
                d.point((wx, round(y + HE / 2)), fill=BV_SOMBRE)
            for wx in range(GX1 + 8, X1 - 4, 10):
                d.point((wx, round(y + HE / 2)), fill=BV_SOMBRE)
    yb = min(rev, SOL)
    d.line([(X0, TOIT), (X0, yb)], fill=BV)
    d.line([(X1, TOIT), (X1, yb)], fill=BV)
    d.line([(GX0, TOIT), (GX0, yb)], fill=BV)                                 # parois de la gaine
    d.line([(GX1, TOIT), (GX1, yb)], fill=BV)
    d.line([(X0, TOIT), (X1, TOIT)], fill=BV)
    if rev >= SOL:
        d.line([(X0 - 10, SOL), (X1 + 10, SOL)], fill=BV)
        d.rectangle([GX0 + 6, SOL - 4, GX1 - 6, SOL - 1], outline=BV_SOMBRE)  # amortisseur
    d.rectangle([GX0 + 4, TOIT - 10, GX1 - 4, TOIT - 1], outline=BV)          # salle des machines
    d.ellipse([(GX0 + GX1) / 2 - 3, TOIT - 8, (GX0 + GX1) / 2 + 3, TOIT - 2], outline=ORANGE)

    if t < T_CABINE:
        return im
    # --- cabine radiographiée
    y, v, phase = etat(t)
    secousse = 0
    if phase == "frein":
        secousse = int(RNG.integers(-1, 2))
    cx0 = (GX0 + GX1) // 2 - CAB // 2 + secousse
    cy0 = round(y)
    cm = (GX0 + GX1) // 2
    # câble
    if t < T_RUPTURE:
        d.line([(cm, TOIT - 2), (cm, cy0)], fill=ORANGE)
    else:
        tr = t - T_RUPTURE
        haut = TOIT - 2 + min(30, tr * 60)                                    # le bout cassé remonte
        d.line([(cm, TOIT - 2), (cm, TOIT - 2 + max(0, 18 - tr * 40))], fill=ORANGE)
        if tr < 1.0:
            d.line([(cm + 1, cy0 - int(14 * (1 - tr))), (cm, cy0)], fill=ORANGE)
        _ = haut
    apparition = ease((t - T_CABINE) / 0.4)
    if apparition < 1 and int(t * 20) % 2:
        return im
    d.rectangle([cx0, cy0, cx0 + CAB, cy0 + CAB], outline=ORANGE)
    for gy in range(cy0 + 2, cy0 + CAB - 1, 3):                              # trame « rayons X » dans la cabine
        for gx in range(cx0 + 2, cx0 + CAB - 1, 3):
            d.point((gx, gy), fill=(70, 34, 18))
    # personne
    pcx = cx0 + CAB // 2
    if phase == "repos":
        personne(d, pcx, cy0 + CAB - 9, "debout")
    elif phase == "chute":
        k = ease((t - T_RUPTURE) / 0.6)
        flotte = round(4 * k + math.sin(t * 6) * 1.2)
        personne(d, pcx, cy0 + CAB - 9 - flotte, k)
    else:
        personne(d, pcx, cy0 + CAB - 16, "allonge")
    # étincelles pendant la chute et au freinage
    if phase in ("chute", "frein"):
        n = 2 if phase == "chute" else 9
        for _ in range(n):
            sx = GX0 + 1 if RNG.random() < 0.5 else GX1 - 1
            ETINCELLES.append([sx, cy0 + RNG.uniform(0, CAB), RNG.uniform(-1.2, 1.2), RNG.uniform(-3.5, -1.0), 1.0])
    for e in ETINCELLES:
        e[0] += e[2]
        e[1] += e[3]
        e[3] += 0.25
        e[4] -= 0.06
    ETINCELLES[:] = [e for e in ETINCELLES if e[4] > 0]
    for e in ETINCELLES:
        d.point((round(e[0]), round(e[1])), fill=ORANGE if e[4] > 0.5 else (150, 70, 30))

    # --- interface
    etage = max(0, ETAGES - (y - TOIT - 3) / HE)
    kmh = v * 3.6
    hx = 212
    crochets(d, (cx0 - 4, cy0 - 4, cx0 + CAB + 4, cy0 + CAB + 4), BLANC if phase != "frein" else ORANGE)
    texte(d, (hx, 120), "ÉTAGE", F8, BV)
    texte(d, (hx, 130), f"{etage:04.1f}", F16, BLANC)
    texte(d, (hx, 160), "VITESSE", F8, BV)
    texte(d, (hx, 170), f"{kmh:3.0f}", F16, ORANGE if kmh > 1 else BLANC)
    texte(d, (hx, 190), "KM/H", F8, BV)
    if T_RUPTURE <= t < T_RUPTURE + 0.9 and int(t * 10) % 2 == 0:
        texte(d, (LW / 2, 30), "CÂBLE ROMPU", F16, ORANGE, centre=True)
    if phase == "chute" and t > T_RUPTURE + 0.6:
        texte(d, (cx0 + CAB + 8, cy0 + 6), "APESANTEUR", F8, BLANC)
    # comparaison chute / saut
    if phase in ("chute", "frein", "arret") and t > T_RUPTURE + 0.3:
        by = 430
        texte(d, (16, by), "CHUTE", F8, BV)
        vmax = G_REEL * T_CHUTE * 3.6
        vaff = vmax if phase in ("frein", "arret") else min(kmh, vmax)          # la barre garde la vitesse maximale
        d.rectangle([60, by + 1, 60 + int(170 * vaff / 90), by + 6], fill=ORANGE)
        texte(d, (60 + int(170 * vaff / 90) + 4, by), f"{vaff:.0f} KM/H", F8, BLANC)
        texte(d, (16, by + 12), "SAUT", F8, BV)
        d.rectangle([60, by + 13, 60 + int(170 * 11 / 90), by + 18], fill=BV)
        texte(d, (60 + int(170 * 11 / 90) + 4, by + 12), "+11 KM/H", F8, BLANC)
    if phase in ("frein", "arret"):
        texte(d, (LW / 2, 26), "FREIN DE SÉCURITÉ", F16, ORANGE, centre=True)
        texte(d, (LW / 2, 48), tape("ACTIVÉ", (t - T_FREIN) / 0.4), F8, BLANC, centre=True)
    if t > T_FREIN + 1.6:
        texte(d, (LW / 2, 458), tape("LA PHYSIQUE EST DE TON CÔTÉ", (t - T_FREIN - 1.6) / 1.2), F8, ORANGE, centre=True)
    return im


# ------------------------------------------------------------------------------------------------ finition
_YY, _XX = np.mgrid[0:H, 0:W]
TRAME = (((_XX % K) == K // 2) & ((_YY % K) == K // 2)).astype(np.float32)   # un point lumineux par pixel source
VIGNETTE = (1 - 0.45 * (((_XX - W / 2) / (W / 2)) ** 2 + ((_YY - H / 2) / (H / 2)) ** 2)).clip(0.4, 1)[..., None]


def finition(im, t):
    grand = im.resize((W, H), Image.NEAREST)
    a = np.asarray(grand, np.float32)
    lum = a.max(axis=2, keepdims=True)
    fond = (lum < 20).astype(np.float32)
    a = a + fond * TRAME[..., None] * np.array([14, 30, 30], np.float32)       # trame de points sur le fond
    halo = np.asarray(grand.resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
                      .resize((W, H), Image.BILINEAR), np.float32)
    a = a + 0.55 * halo                                                       # halo des couleurs vives
    g = np.random.default_rng(int(t * FPS)).normal(0, 4, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)
    a = (a + g) * VIGNETTE
    return np.clip(a, 0, 255).astype(np.uint8)


def render(out):
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    for f in range(int(DUR * FPS)):
        t = f / FPS
        ff.stdin.write(finition(image(t), t).tobytes())
    ff.stdin.close()
    ff.wait()
    n = int(DUR * MI.SR)
    a = MI.bed(DUR)[:n]
    a = (a.mean(1) if a.ndim == 2 else a) * 0.4
    ev = [(0.05, E1.swell(0.10)), (T_CABINE, E1.pop_s(880, 0.10)), (T_RUPTURE, E1.pop_s(300, 0.25)),
          (T_RUPTURE + 0.02, E1.pop_s(2200, 0.12)), (T_RUPTURE + 0.1, E1.swell(0.14)),
          (T_FREIN, E1.pop_s(1800, 0.20)), (T_FREIN + 1.6, E1.ding(784, 0.14))]
    ev += [(T_FREIN + j * 0.05, E1.pop_s(2600 + 90 * j, 0.06)) for j in range(9)]
    ev += [(T_RUPTURE + 0.3 + j * 0.25, E1.pop_s(1300 + 60 * j, 0.03)) for j in range(int(T_CHUTE / 0.25))]
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
    render(sys.argv[1] if len(sys.argv) > 1 else "output/demo_pixel_ascenseur.mp4")
