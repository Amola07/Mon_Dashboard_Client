"""Nouvelle ouverture d'ep08 (0 → 5,75 s) : il se passe quelque chose dès la première image.

Constat (statistiques TikTok) : la majorité des spectateurs partait à 0:01 ; l'ancienne ouverture montrait une
petite Orbe immobile sur un fond vide pendant 5 s. Ici, même style, mais un événement par seconde :
  0,0 s  l'Orbe, en grand, est déjà en train de se dédoubler (comme une cellule) ;
  0,55 s les deux copies se séparent : l'une devient grise, se fissure et éclate en poussière ;
  1,8 s  derrière la survivante surgissent des dizaines de copies éteintes (toutes celles qui sont mortes) ;
  2,9 s  elles plongent dans les feuilles de l'arbre des possibles qui pousse, la survivante au bout du seul
         chemin doré. À 5,75 s on enchaîne sur la suite inchangée de l'épisode.

    python -m films.episodes.ep08_quantique.ouverture output/ep08_quantique_v2.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep01_triangle.ep01 import GOLD, P, ease
from films.episodes.ep08_quantique import ep08 as M
from films.persos.orbe import Etat, draw_orbe
from films.trait import son as S

W, H, FPS = 1080, 1920, 30
T_CUT = 5.75
HERE = os.path.dirname(os.path.abspath(__file__))
_FD = os.path.join(os.path.dirname(os.path.dirname(HERE)), "fonts")
F_MED = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-Medium.ttf"))
F_BOLD = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-ExtraBold.ttf"))

T_SEP, T_GRAY, T_CRACK, T_BURST = 0.0, 0.5, 0.75, 1.15
T_GHOSTS, T_TREE, T_GOLD = 1.75, 2.9, 4.25


def eo(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def lerp(a, b, u):
    return a + (b - a) * u


def gray_matrix(k, a=1.0):
    """Désature de k (0 → 1) et assombrit, opacité a."""
    l = (0.2126, 0.7152, 0.0722)
    m = []
    for i in range(3):
        row = [(1 - k) * (1 if j == i else 0) + k * l[j] * 0.6 for j in range(3)]
        m += row + [0, 0]
    m += [0, 0, 0, a, 0]
    return m


def orbe(c, t, x, y, s, expr="neutre", age=1.0, gray=0.0, alpha=1.0, regard=(0, 0), squash=(1.0, 1.0)):
    if alpha <= 0.005 or s <= 0.005:
        return
    e = Etat(expr=expr, age=age, regard=regard, humeur_mix=1.0)
    e.cligne = False
    c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(gray_matrix(gray, alpha))))
    c.translate(x, y)
    c.scale(s * squash[0], s * squash[1])
    draw_orbe(c, t, e, parle_pulse=False)
    c.restore()


# ------------------------------------------------------------------------------------------------ données
_rng = np.random.default_rng(12)
LEAVES = [(x1, y1, idx) for x0, y0, x1, y1, d, idx in M.TREE if d == 6]
SURV_LEAF = M.PATH[-1]
DEAD = [p for p in LEAVES if not M.on_path(6, p[2])]
_rng.shuffle(DEAD)
GHOSTS = []                                                 # (départ autour de la survivante, feuille d'arrivée)
for k in range(26):
    ang = -math.pi / 2 + (k - 12.5) / 12.5 * 1.25 + _rng.normal(0, 0.06)
    r = 330 + 170 * (k % 3) + _rng.uniform(-30, 30)
    GHOSTS.append(((540 + r * math.cos(ang) * 1.05, 900 + r * math.sin(ang) * 0.85 + 120),
                   DEAD[k % len(DEAD)][:2], _rng.uniform(0.32, 0.5), T_GHOSTS + 0.035 * k))
SHARDS = []                                                 # éclats de l'Orbe qui meurt
for k in range(150):
    a = _rng.uniform(0, 2 * math.pi)
    r0 = _rng.uniform(0.2, 1.0) * 200
    sp = _rng.uniform(250, 900)
    SHARDS.append((r0 * math.cos(a), r0 * math.sin(a), sp * math.cos(a), sp * math.sin(a) - 200,
                   _rng.uniform(3, 11), _rng.uniform(0.6, 1.4)))
CRACKS = []
for k in range(6):                                          # fissures : lignes brisées depuis un point d'impact
    a = -0.6 + k * 1.05 + _rng.normal(0, 0.2)
    pts = [(-30.0, -20.0)]
    for j in range(5):
        r = (j + 1) * 34
        a2 = a + _rng.normal(0, 0.28)
        pts.append((-30 + r * math.cos(a2), -20 + r * math.sin(a2)))
    CRACKS.append(pts)


# ------------------------------------------------------------------------------------------------ image
def draw_title(c, t):
    if t > 2.9:
        return
    a = 1 - ease((t - 2.45) / 0.4)                          # visible dès la première image
    k = eo(t / 0.35)
    f1, f2 = skia.Font(F_MED, 52), skia.Font(F_BOLD, 118)
    s1, s2 = "Et si tu étais", "DÉJÀ MORT ?"
    c.save()
    c.translate(540, 360)
    sc = lerp(1.1, 1.0, k)
    c.scale(sc, sc)
    w1 = f1.measureText(s1)
    c.drawString(s1, -w1 / 2, -120, f1, P((225, 220, 245), 255 * a))
    w2 = f2.measureText(s2)
    c.drawString(s2, -w2 / 2, 30, f2, P((255, 60, 80), 170 * a, blur=26))
    c.drawString(s2, -w2 / 2, 30, f2, P((10, 6, 20), 255 * a, stroke=10))
    c.drawString(s2, -w2 / 2, 30, f2, P((255, 255, 255), 255 * a))
    c.restore()


def draw_tree(c, t):
    if t < T_TREE:
        return
    g = eo((t - T_TREE) / 1.3) * 7.0
    gold = ease((t - T_GOLD) / 0.7)
    for x0, y0, x1, y1, d, idx in M.TREE:
        k = min(1.0, max(0.0, g - d))
        if k <= 0:
            continue
        xe, ye = lerp(x0, x1, k), lerp(y0, y1, k)
        path = M.on_path(d, idx)
        col = (200, 190, 255)
        al = 200.0
        w = max(2.0, 7 - d)
        if path:
            col = tuple(lerp(ci, cg, gold) for ci, cg in zip(col, GOLD))
            w += 3 * gold
        else:
            col = tuple(lerp(ci, 95, gold) for ci in col)
            al *= 1 - 0.55 * gold
        c.drawLine(x0, y0, xe, ye, P(col, al * 0.35, blur=6, stroke=w * 2.5))
        c.drawLine(x0, y0, xe, ye, P(col, al, stroke=w))


def frame(c, t):
    E1.draw_background(c, t)
    c.drawRect(skia.Rect(0, 0, W, H), P((4, 3, 12), 255 * 0.45))
    shake = 14 * math.exp(-t / 0.12) * math.sin(t * 90) + 10 * math.exp(-max(0, t - T_BURST) / 0.1) * \
        math.sin(t * 80) * (t > T_BURST)
    c.save()
    c.translate(shake, 0)
    # flash de la division (toute première image : un anneau lumineux s'ouvre)
    if t < 0.5:
        u = t / 0.5
        c.drawCircle(540, 900, 220 + 520 * eo(u), P((255, 200, 240), 200 * (1 - u), stroke=14 * (1 - u) + 2))
    draw_tree(c, t)
    # copies éteintes : elles surgissent puis plongent dans les feuilles de l'arbre
    for (sx, sy), (lx, ly), sc, t0 in GHOSTS:
        if t < t0:
            continue
        ap = eo((t - t0) / 0.25)
        u = ease((t - T_TREE - 0.15) / 1.1)
        x, y = lerp(sx, lx, u), lerp(sy, ly, u)
        s = lerp(sc * (0.6 + 0.4 * ap), 0.11, u)
        orbe(c, t, x, y, s, "neutre", gray=1.0, alpha=0.55 * ap)
    # la copie qui meurt (gauche)
    sep = 230 * eo((t - T_SEP) / 0.55) + 55
    if t < T_BURST:
        gk = ease((t - T_GRAY) / 0.45)
        xd = 540 - sep - 40 * ease((t - T_GRAY) / 0.6)
        wob = 1 + 0.05 * math.sin(t * 40) * (t > T_CRACK)
        orbe(c, t, xd, 900, 1.25, "surpris" if t < T_GRAY else "triste", age=t, gray=gk, regard=(0.6, 0),
             squash=(wob, 2 - wob))
        if t >= T_CRACK:
            kk = ease((t - T_CRACK) / 0.3)
            for pts in CRACKS:
                n = max(2, int(len(pts) * kk))
                path = skia.Path()
                path.moveTo(xd + pts[0][0], 900 + pts[0][1])
                for px, py in pts[1:n]:
                    path.lineTo(xd + px, 900 + py)
                c.drawPath(path, P((255, 255, 255), 230, stroke=4))
                c.drawPath(path, P((200, 220, 255), 120, stroke=12, blur=6))
    else:
        xd = 540 - sep - 40
        u = t - T_BURST
        if u < 0.25:
            c.drawCircle(xd, 900, 150 + 220 * eo(u / 0.25), P((235, 235, 255), 120 * (1 - u / 0.25), blur=30))
        for x0, y0, vx, vy, r, life in SHARDS:
            if u > life:
                continue
            x = xd + x0 + vx * u * (1 - 0.35 * u)
            y = 900 + y0 + vy * u + 600 * u * u
            al = 255 * (1 - u / life)
            c.drawCircle(x, y, r * (1 - 0.5 * u / life), P((160, 150, 185), al))
    # la survivante (droite → centre → feuille dorée)
    xs = 540 + sep
    expr, age = ("surpris", t) if t < 2.4 else ("neutre", t - 2.4)
    regard = (-0.8, 0) if t < 1.8 else (0, -0.3)
    s = 1.25
    xs, ys = (lerp(xs, 540, ease((t - 1.3) / 0.6)), 900)
    if t > T_TREE:
        u = ease((t - T_TREE) / 1.2)
        xs, ys = lerp(xs, SURV_LEAF[0], u), lerp(ys, SURV_LEAF[1] - 30, u)
        s = lerp(1.25, 0.3, u)
    if t > T_GOLD:
        g = ease((t - T_GOLD) / 0.5)
        c.drawCircle(xs, ys, 90 * s / 0.3, P(GOLD, 120 * g, blur=40))
    orbe(c, t, xs, ys, s, expr, age=age, regard=regard)
    c.restore()
    # pont lumineux de la division (les deux moitiés encore reliées)
    if t < 0.55:
        u = t / 0.55
        c.drawOval(skia.Rect.MakeXYWH(540 - sep, 900 - 110 * (1 - u), 2 * sep, 220 * (1 - u)),
                   P((255, 210, 245), 140 * (1 - u), blur=18))
    draw_title(c, t)
    if t >= M.S("h2") - 0.05:
        E1.TIMING = [(txt, a, b) for _, txt, a, b in M.SEG if _ == "h2"]
        E1.draw_subtitle(c, t)


# ------------------------------------------------------------------------------------------------ son
def sfx(path):
    mx = S.Mix(T_CUT + 2)
    mx.add(0.0, S.sub_hit(0.5), send=0.3)
    tt = np.arange(int(0.55 * S.SR)) / S.SR                # étirement de la division : glissando grave
    stretch = np.sin(2 * np.pi * np.cumsum(90 + 140 * (tt / 0.55) ** 2) / S.SR) * np.sin(np.pi * tt / 0.55) * 0.25
    mx.add(0.0, stretch, send=0.4)
    mx.add(0.5, S.mallet(196, 0.12), p=-0.4, send=0.5)       # la copie s'éteint
    crack = S.bandpass(np.random.default_rng(2).standard_normal(int(0.4 * S.SR)), 1500, 2.0) * \
        np.exp(-np.arange(int(0.4 * S.SR)) / S.SR / 0.05) * 0.5
    mx.add(T_CRACK, crack, p=-0.5, send=0.3)
    burst = S.lowpass(np.random.default_rng(3).standard_normal(int(1.2 * S.SR)), 1800) * \
        np.exp(-np.arange(int(1.2 * S.SR)) / S.SR / 0.25) * 0.9
    mx.add(T_BURST, burst, p=-0.45, send=0.5)
    mx.add(T_BURST, S.sub_hit(0.35), send=0.4)
    for k in range(10):                                    # les copies éteintes surgissent
        mx.add(T_GHOSTS + 0.09 * k, S.mallet((147, 165, 175, 196)[k % 4], 0.03), p=(k % 5 - 2) / 2.5, send=0.7)
    mx.add(T_TREE - 0.1, S.whoosh(1.3, 0.12, 0.3, -0.2, 200, 900), send=0.5)
    mx.add(T_GOLD, S.shimmer(2.0, S.A2, 0.06), send=0.8)
    y = mx.dry + S.reverb(mx.wet, mix=1.0) * 0.6
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(S.SR)
        w.writeframes((np.clip(y * 0.5, -1, 1) * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------------------------------------ assemblage
def render(out_path, base="output/ep08_quantique.mp4"):
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
                           f"{tmp}/ouv.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(round(T_CUT * FPS))):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    sfx(f"{tmp}/sfx.wav")
    # image : nouvelle ouverture + suite de l'épisode à partir de T_CUT ; son : voix/musique d'origine + effets
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/ouv.mp4", "-ss", f"{T_CUT}", "-i", base,
                    "-i", base, "-i", f"{tmp}/sfx.wav",
                    "-filter_complex",
                    "[0:v]setsar=1[a];[1:v]setsar=1,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v];"
                    "[2:a][3:a]amix=inputs=2:duration=first:normalize=0[au]",
                    "-map", "[v]", "-map", "[au]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_path], check=True)


def stills(out_dir, times):
    os.makedirs(out_dir, exist_ok=True)
    surf = skia.Surface(W, H)
    for t in times:
        frame(surf.getCanvas(), t)
        surf.makeImageSnapshot().save(os.path.join(out_dir, f"o_{t:05.2f}.png"))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "stills":
        stills(sys.argv[2], [float(x) for x in sys.argv[3:]])
    else:
        render(sys.argv[1] if len(sys.argv) > 1 else "output/ep08_quantique_v2.mp4")
