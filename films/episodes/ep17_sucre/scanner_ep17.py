"""Épisode 17, version « scanner » : images générées (style cinéma) animées en code, interface de scanner par-dessus.

Chaque plan : une image, un mouvement de caméra (zoom vers un point), et une liste d'événements d'interface
(verrouillage, repère, compteur, loupe, texte) calés sur la voix. Transition entre plans : ligne de balayage orange.
Les plans sans image reçue sont simplement sautés.

    python -m films.episodes.ep17_sucre.scanner_ep17 output/ep17_scanner.mp4
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1
from films.styles.test_scanner import (BLANC, MONO, ORANGE, P, TITRE, W, H, FPS, ambiance, charger, crochets, ease,
                                       finitions, tape, texte)

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
VOIX = os.environ.get("VOIX", os.path.join(HERE, "audio", "voix.mp3"))
VOIX2 = os.path.join(HERE, "audio", "voix_serree.wav")
SEGS = os.environ.get("SEGS", os.path.join(HERE, "audio", "voix.json"))
T_ACC = 3.0                                                          # fin de l'accroche (recalculée)
TR = 0.35                                                            # durée de la transition « balayage »

# ------------------------------------------------------------------------------------------------ plans
# phrase de départ (index dans SEGS), image, zoom début → fin, point visé, événements (t relatif au plan)
#   ("lock", t, (x0, y0, x1, y1), étiquette)       crochets orange qui se resserrent + étiquette
#   ("tag", t, (x, y, demi-largeur, demi-hauteur), étiquette, côté)   petit repère blanc + étiquette
#   ("compteur", t, durée, (x, y), v0, v1, unité, sous-titre)
#   ("loupe", t, (sx, sy), (lx, ly, r), grossissement, étiquette)
#   ("texte", t, (x, y), texte, taille, couleur)
PLANS = [
    (0, "01", (1.0, 1.08), (540, 700), [
        ("lock", 0.6, (262, 192, 822, 1160), "OBJET 01 // CUBE"),
        ("tag", 1.4, (538, 1512, 34, 60), "HUMAIN // 1,75 m", -1),
    ]),
    (1, "02", (1.04, 1.12), (540, 900), [
        ("compteur", 0.0, 0.9, (80, 300), 0, 8_000_000_000, "", "PERSONNES"),
    ]),
    (2, "03", (1.0, 1.6), (600, 1000), [
        ("lock", 0.1, (274, 450, 928, 1406), "OBJET 02 // TA MAIN"),
        ("texte", 1.1, (120, 300), "ZOOM ×10", 34, ORANGE),
        ("texte", 2.1, (120, 360), "ZOOM ×100", 34, ORANGE),
    ]),
    (5, "04", (1.0, 1.3), (560, 850), [
        ("loupe", 0.1, (560, 820), (760, 1300, 170), 3.0, "GROSSISSEMENT"),
        ("texte", 0.2, (90, 300), "×1 000        CELLULES", 30, BLANC),
        ("texte", 1.4, (90, 360), "×1 000 000    MOLÉCULES", 30, BLANC),
        ("texte", 2.7, (90, 420), "×10 000 000   ATOMES", 30, ORANGE),
    ]),
    (8, "05", (1.0, 1.25), (538, 964), [
        ("tag", 0.6, (538, 964, 14, 14), "NOYAU", 1),
        ("lock", 1.2, (150, 560, 930, 1380), "ATOME"),
    ]),
    (9, "07", (1.0, 1.25), (540, 1266), [
        ("tag", 0.5, (540, 1266, 36, 36), "NOYAU // UNE BILLE", 1),
    ]),
    (10, "06", (1.0, 1.5), (534, 970), [
        ("lock", 0.3, (90, 700, 1000, 1480), "ATOME // UN STADE"),
        ("tag", 1.2, (534, 970, 16, 16), "NOYAU", 1),
        ("texte", 2.5, (220, 1250), "ENTRE LES DEUX : RIEN", 36, ORANGE),
    ]),
    (14, "03", (1.25, 1.0), (600, 900), [
        ("lock", 0.1, (274, 450, 928, 1406), "TON CORPS"),
        ("compteur", 1.6, 2.6, (80, 300), 0, 99.9999999999999, " %", "DE VIDE"),
    ]),
    (16, "15", (1.0, 1.3), (541, 893), [
        ("tag", 0.4, (541, 893, 30, 90), "CONTACT ?", 1),
        ("texte", 2.6, (90, 300), "ÉLECTRONS ⟷ ÉLECTRONS : RÉPULSION", 28, ORANGE),
        ("texte", 4.9, (90, 370), "CONTACT RÉEL : 0", 34, ORANGE),
    ]),
    (19, "08", (1.0, 1.12), (500, 900), [
        ("tag", 0.3, (281, 1293, 46, 258), "SUJET 01 // TOI", 1),
        ("compteur", 1.0, 3.8, (80, 300), 0, 8_000_000_000, "", "HUMAINS COMPRESSÉS"),
        ("tag", 1.8, (830, 776, 20, 20), "POINT DE COMPRESSION", -1),
    ]),
    (22, "09", (1.0, 1.3), (540, 742), [
        ("lock", 0.2, (480, 680, 600, 804), "8 000 000 000 HUMAINS"),
    ]),
    (23, "10", (1.0, 1.15), (540, 1167), [
        ("lock", 0.2, (387, 1043, 692, 1290), "MORCEAU DE SUCRE // 2 cm³"),
    ]),
    (24, "11", (1.0, 1.15), (540, 1100), [
        ("lock", 0.2, (490, 1290, 590, 1395), "MASSE ?"),
        ("compteur", 0.5, 2.4, (80, 300), 0, 400_000_000, " t", "MASSE DU SUCRE"),
        ("tag", 1.0, (771, 1167, 18, 40), "HUMAIN", 1),
    ]),
    ((24, 1.3), "12", (1.0, 1.4), (540, 960), [
        ("tag", 0.2, (540, 960, 30, 30), "IL S'ENFONCE", 1),
    ]),
    (25, "05", (1.6, 2.2), (538, 964), [
        ("texte", 1.6, (120, 300), "ÉTOILE GÉANTE // EFFONDREMENT", 30, BLANC),
    ]),
    (28, "13", (1.0, 1.25), (540, 952), [
        ("lock", 0.2, (440, 852, 640, 1052), "ÉTOILE À NEUTRONS"),
        ("texte", 1.6, (120, 300), "MASSE > SOLEIL", 34, BLANC),
        ("texte", 3.2, (120, 360), "DIAMÈTRE ≈ 20 km", 34, ORANGE),
    ]),
    (31, "14", (1.0, 1.2), (541, 900), [
        ("lock", 0.2, (337, 766, 745, 1034), "1 CUILLÈRE D'ÉTOILE"),
        ("texte", 1.9, (90, 300), "MASSE > 8 000 000 000 HUMAINS", 32, ORANGE),
    ]),
    (33, "16", (1.12, 1.0), (540, 900), [
        ("tag", 0.3, (539, 1473, 30, 50), "TOI", -1),
        ("lock", 1.0, (260, 415, 809, 1322), "99,9999999999999 % DE VIDE"),
    ]),
]


# ------------------------------------------------------------------------------------------------ dessin
def camera(plan, u):
    """Zoom du plan à l'avancement u ; le point visé glisse doucement vers le centre de l'écran."""
    (z0, z1), (fx, fy) = plan["zoom"], plan["vise"]
    z = z0 + (z1 - z0) * (0.6 * u + 0.4 * ease(u))
    k = ease(u) * min(1.0, (z1 - 1) * 1.5)
    return z, fx, fy, fx + (540 - fx) * k, fy + (820 - fy) * k


def vers_ecran(plan, u, x, y):
    z, fx, fy, tx, ty = camera(plan, u)
    return tx + (x - fx) * z, ty + (y - fy) * z


def image_plan(c, plan, u):
    c.save()
    z, fx, fy, tx, ty = camera(plan, u)
    c.translate(tx, ty)
    c.scale(z, z)
    c.translate(-fx, -fy)
    c.drawImage(plan["img"], 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
    c.restore()


def fmt(v, unite):
    if isinstance(v, float) and v < 100 and unite.strip() == "%":
        s = f"{v:.13f}".rstrip("0").replace(".", ",")
    elif v >= 1e15:
        e = int(math.log10(max(v, 1)))
        s = f"{v / 10 ** e:.1f} × 10".replace(".", ",") + str(e).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
    else:
        s = f"{int(v):,}".replace(",", " ")
    return s + unite


def hud(c, plan, a, u, t_abs):
    E = lambda x, y: vers_ecran(plan, u, x, y)                     # noqa: E731
    for ev in plan["hud"]:
        kind, t0 = ev[0], ev[1]
        if a < t0:
            continue
        d = a - t0
        if kind == "lock":
            x0, y0 = E(*ev[2][:2])
            x1, y1 = E(*ev[2][2:])
            x0, x1 = max(x0, 70), min(x1, W - 70)                   # reste dans l'écran malgré le zoom
            y0, y1 = max(y0, 190), min(y1, H - 260)
            k = ease(d / 0.45)
            m = 150 * (1 - k)
            clin = 255 if d > 0.8 or int(d * 12) % 2 else 90
            crochets(c, (x0 - m, y0 - m, x1 + m, y1 + m), ORANGE, clin * k, l=50, w=5)
            ly = max(y0 - 26, 150)
            c.drawRoundRect(skia.Rect(x0, ly - 34, x0 + 24 + 19 * len(ev[3]), ly + 10), 5, 5,
                            P((8, 14, 18), 170 * ease(d / 0.3)))
            texte(c, tape(ev[3], d / 0.5), x0 + 12, ly, 30, ORANGE)
        elif kind == "tag":
            x, y, hw, hh = ev[2]
            cx, cy = E(x, y)
            z = camera(plan, u)[0]
            k = ease(d / 0.35)
            crochets(c, (cx - hw * z - 8, cy - hh * z - 8, cx + hw * z + 8, cy + hh * z + 8), BLANC, 230 * k, l=14, w=3)
            sd = ev[4]
            ex, ey = cx + sd * (hw * z + 20), cy - 50
            c.drawLine(cx + sd * (hw * z + 8), cy, ex, ey, P(BLANC, 210 * k, 2))
            s = tape(ev[3], (d - 0.2) / 0.5)
            f = skia.Font(MONO, 24)
            tx = ex + 8 if sd > 0 else ex - 8 - f.measureText(ev[3])
            tx = min(max(tx, 60), W - 60 - f.measureText(ev[3]))
            c.drawRoundRect(skia.Rect(tx - 8, ey - 26, tx + f.measureText(ev[3]) + 8, ey + 8), 4, 4,
                            P((8, 14, 18), 150 * k))
            texte(c, s, tx, ey, 24, BLANC)
        elif kind == "compteur":
            dur, (x, y), v0, v1, unite, sous = ev[2:]
            k = ease(d / dur)
            if v1 > 1e12:                                            # échelle log pour les très grands nombres
                v = 10 ** (math.log10(v0) + (math.log10(v1) - math.log10(v0)) * k)
            elif unite.strip() == "%":                               # les « 9 » s'ajoutent un à un
                v = 100 - 100 * 10 ** (-15 * k) if k > 0 else 0.0
            else:
                v = v0 + (v1 - v0) * k
                if isinstance(v1, int):
                    v = int(v)
            al = 255 * ease(d / 0.25)
            c.drawRoundRect(skia.Rect(x - 16, y - 66, W - x + 16, y + 52), 8, 8, P((8, 14, 18), 120 * ease(d / 0.25)))
            texte(c, fmt(v, unite), x, y, 54, BLANC, al)
            texte(c, sous, x + 2, y + 38, 24, ORANGE, al)
        elif kind == "loupe":
            (sx, sy), (lx, ly, r0), g, lab = ev[2:]
            k = ease(d / 0.55)
            px, py = E(sx, sy)
            c.drawLine(px, py, lx - r0 * 0.7 * k, ly - r0 * 0.7 * k, P(BLANC, 200 * k, 2))
            c.drawCircle(px, py, 14, P(ORANGE, 255 * k, 3))
            r = r0 * k
            c.save()
            clip = skia.Path()
            clip.addCircle(lx, ly, r)
            c.clipPath(clip, doAntiAlias=True)
            c.translate(lx, ly)
            c.scale(g, g)
            c.translate(-sx - 3 * math.sin(t_abs), -sy - d * 4)
            c.drawImage(plan["img"], 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
            c.restore()
            c.drawCircle(lx, ly, r, P(BLANC, 230, 4))
            c.save()
            c.translate(lx, ly)
            c.rotate(t_abs * 25)
            for i in range(48):
                an = math.radians(i * 7.5)
                l = 16 if i % 6 == 0 else 7
                c.drawLine((r + 8) * math.cos(an), (r + 8) * math.sin(an), (r + 8 + l) * math.cos(an),
                           (r + 8 + l) * math.sin(an), P(ORANGE, 220 * k, 2))
            c.restore()
            texte(c, tape(lab, (d - 0.5) / 0.6), max(60, lx - r0 - 60), ly - r0 - 40, 22, BLANC)
        elif kind == "texte":
            (x, y), s, taille, col = ev[2:]
            f = skia.Font(MONO, taille)
            c.drawRoundRect(skia.Rect(x - 12, y - taille - 6, x + f.measureText(s) + 12, y + 14), 6, 6,
                            P((8, 14, 18), 160 * ease(d / 0.3)))
            texte(c, tape(s, d / 0.7), x, y, taille, col)


def cadre(c, t, n):
    u = ease(t / 0.6)
    crochets(c, (44, 44, W - 44, H - 44), BLANC, 150 * u, l=60 * u, w=3)
    texte(c, f"SCAN // {n:02d}", 70, 100, 26, BLANC, 200 * u)
    texte(c, f"T+{t:05.2f}", W - 230, 100, 26, BLANC, 200 * u)


# ------------------------------------------------------------------------------------------------ sous-titres
MOTS = []


def preparer_mots(segs):
    for a, b, txt in segs:
        ws = txt.split()
        lens = [len(re.sub(r"\W", "", w)) + 1.5 for w in ws]
        t = a
        for j, (w, l) in enumerate(zip(ws, lens)):
            d = (b - a) * l / sum(lens)
            MOTS.append((w.upper(), t, t + d, len(MOTS) - j, j))
            t += d


def sous_titres(c, t):
    i = max([k for k, m in enumerate(MOTS) if m[1] <= t + 0.03] + [-1])
    if i < 0 or t > MOTS[i][2] + 0.4:
        return
    deb, rang = MOTS[i][3], MOTS[i][4]
    g0 = deb + (rang // 3) * 3
    grp = [m for m in MOTS[g0:g0 + 3] if m[3] == deb]
    size = 66
    f = skia.Font(TITRE, size)
    sp = f.measureText(" ")
    tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    while tot > W - 140:
        size -= 4
        f = skia.Font(TITRE, size)
        sp = f.measureText(" ")
        tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    age = t - MOTS[g0][1]
    pop = 1 + 0.1 * math.exp(-age * 12) * math.cos(age * 28) if age < 0.4 else 1.0
    c.save()
    c.translate(W / 2, 1640)
    c.scale(pop, pop)
    x = -tot / 2
    for k, m in enumerate(grp):
        on = g0 + k == i
        c.drawString(m[0], x, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 200),
                                               Style=skia.Paint.kStroke_Style, StrokeWidth=12,
                                               StrokeJoin=skia.Paint.kRound_Join))
        c.drawString(m[0], x, 0, f, P(ORANGE if on else (255, 255, 255)))
        x += f.measureText(m[0]) + sp
    c.restore()


def accroche(c, t):
    if t > T_ACC:
        return
    a = 255 * (1 - ease((t - T_ACC + 0.3) / 0.3))
    s = E1.pop(t) if t < 0.5 else 1.0
    c.save()
    c.translate(W / 2, 1560)
    c.scale(s, s)
    for txt, y, taille, col in (("TOUTE L'HUMANITÉ", 0, 80, (255, 255, 255)), ("TIENT DANS UN SUCRE", 92, 64, ORANGE)):
        f = skia.Font(TITRE, taille)
        w = f.measureText(txt)
        c.drawString(txt, -w / 2, y, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, int(a * 0.8)),
                                                    Style=skia.Paint.kStroke_Style, StrokeWidth=14,
                                                    StrokeJoin=skia.Paint.kRound_Join))
        c.drawString(txt, -w / 2, y, f, P(col, a))
    c.restore()


# ------------------------------------------------------------------------------------------------ rendu
def preparer():
    """Voix resserrée (silences ≤ 0,40 s), minutage recalé, images chargées (plans sans image sautés)."""
    global T_ACC
    v, N, _ = MI.tighten(MI.load_voice(VOIX), max_gap=0.40, thr_db=-38.0)
    with wave.open(VOIX2, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(MI.SR)
        w.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes())
    segs = [(N(a), N(b), txt) for a, b, txt in json.load(open(SEGS))]
    T_ACC = segs[0][1] + 0.1
    plans = []
    for s, nom, zoom, vise, ev in PLANS:
        s, dt = s if isinstance(s, tuple) else (s, 0.0)               # (phrase, décalage) pour couper en cours de phrase
        p = os.path.join(IMG, nom + ".jpg")
        if os.path.exists(p):
            plans.append({"t0": segs[s][0] + dt - (0.15 if s and not dt else 0.0), "nom": nom, "img": charger(p), "zoom": zoom,
                          "vise": vise, "hud": ev})
    for k, p in enumerate(plans):
        p["t1"] = plans[k + 1]["t0"] if k + 1 < len(plans) else segs[-1][1] + 1.2
    preparer_mots(segs)
    return plans, segs


def render(out):
    plans, segs = preparer()
    dur = plans[-1]["t1"]
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    fx = [(0.0, E1.swell(0.10), 1.0)]
    for k, p in enumerate(plans):
        if k:
            fx.append((p["t0"], E1.swell(0.06), 1.0))
        for ev in p["hud"]:
            t = p["t0"] + ev[1]
            fx.append((t, E1.pop_s({"lock": 880, "tag": 1180, "compteur": 660, "loupe": 990, "texte": 1320}[ev[0]],
                                   0.08), 1.0))
            if ev[0] == "compteur":
                fx += [(t + 0.1 + j * 0.12, E1.pop_s(1500 + 30 * j, 0.02), 1.0) for j in range(int(ev[2] / 0.12))]
    for f in range(int(dur * FPS)):
        t = f / FPS
        k = max(i for i, p in enumerate(plans) if p["t0"] <= t or i == 0)
        p = plans[k]
        a = t - p["t0"]
        u = min(1.0, max(0.0, a / (p["t1"] - p["t0"])))
        c = surf.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        image_plan(c, p, u)
        if k and a < TR:                                             # balayage : l'ancien plan reste sous la ligne
            q = plans[k - 1]
            y = H * ease(a / TR)
            c.save()
            c.clipRect(skia.Rect(0, y, W, H))
            image_plan(c, q, 1.0)
            c.restore()
            g = skia.GradientShader.MakeLinear([skia.Point(0, y - 160), skia.Point(0, y)],
                                               [skia.Color(*ORANGE, 0), skia.Color(*ORANGE, 90)])
            c.drawRect(skia.Rect(0, y - 160, W, y), skia.Paint(Shader=g))
            c.drawLine(0, y, W, y, P(ORANGE, 240, 3))
        ambiance(c, t)
        finitions(c, t)
        hud(c, p, a, u, t)
        cadre(c, t, int(p["nom"]))
        accroche(c, t)
        if t > T_ACC:
            sous_titres(c, t)
        if t < 0.3:
            c.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 255 * (1 - t / 0.3)))
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    MI.soundtrack(f"{tmp}/a.wav", MI.load_voice(VOIX2), dur, fx)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out, f"{dur:.1f} s")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep17_scanner.mp4")
