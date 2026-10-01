"""Essai « motion design 3D » : ton iris est plus unique que ton empreinte (≈ 21,5 s, sans voix).

Plans : survol en rase-mottes des crêtes de l'empreinte puis montée en grue → panoramique filé → plongée à
travers les couches de l'œil jusqu'à l'iris → survol du cratère de fibres → formation du motif en orbite →
jumeaux avec bascule de mise au point → 40 points contre 240. Son stéréo immersif calé sur chaque mouvement.
"""
import math
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool

import numpy as np
import skia

from films.persos.orbe import Etat, draw_orbe
from films.trait import espace as E
from films.trait import motifs3d as M
from films.trait import son as S
from films.trait import trait as T2
from films.trait.trait import BLUE, BLUE_HI, F_BOLD, FPS, H, RED, RED_HI, W, caption, ease, ease_out, lerp, win

DUR = 21.5
T1, T2_, T3, T4, T5 = 0.0, 4.3, 9.0, 13.0, 17.0
ORBE_HOME = (170, 1440)
ORBE_S = 0.4

CAPS = [(0.3, 4.1, "Ce n'est pas ton doigt qui te rend unique."),
        (4.6, 6.7, "C'est ton œil."),
        (6.9, 8.9, "De près, ton iris est un paysage de fibres et de sillons."),
        (9.2, 12.9, "Ce motif se dessine avant ta naissance… en partie au hasard."),
        (13.2, 16.9, "Même de vrais jumeaux ont des iris différents."),
        (17.2, 19.0, "Une empreinte : environ 40 points de comparaison."),
        (19.1, DUR, "Un iris : plus de 240.")]


def part(lines, u):
    if u >= 1:
        return lines
    if u <= 0:
        return []
    return [l[:max(2, int(len(l) * u))] for l in lines]


def smooth(a, b, u):
    return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * ease(u)


# ------------------------------------------------------------------------------------------------ plan 1
FINGER_LINES, FINGER_OUT = M.finger3d()
F_DUST = np.random.default_rng(21).uniform([-0.8, 0.01, -0.9], [0.8, 0.35, 1.0], (260, 3))


def shot_finger(t):
    if t < 2.0:                                            # rase-mottes vers le bout du doigt
        z = 0.75 - 0.22 * t
        pos = (0.04, 0.16 + 0.02 * t, z)
        tgt = (0.0, 0.0, z - 0.5)
    else:                                                  # grue : on monte et on découvre l'empreinte entière
        u = (t - 2.0) / 1.7
        z = 0.75 - 0.22 * 2.0
        pos = smooth((0.04, 0.2, z), (0.0, 2.05, 0.42), u)
        tgt = smooth((0.0, 0.0, z - 0.5), (0.0, 0.0, 0.03), u)
    if t > 3.85:                                           # panoramique filé vers la droite
        w = ease((t - 3.85) / 0.45) ** 2
        tgt = np.asarray(tgt, float) + np.array([3.5 * w, 0, 0])
    cam = E.cam_at(pos, tgt, 46)
    near = t < 2.4
    lens = E.Lens(focus=0.5 if near else 2.0, aperture=22 if near else 8, fog=(1.3, 2.4) if near else (2.5, 4.0))
    sc = E.Scene(cam, lens)
    sc.exposure = 0.65
    sc.polylines(FINGER_LINES, BLUE_HI, 0.8, 0.0014)
    sc.polylines(FINGER_OUT, BLUE_HI, 0.7, 0.004)
    sc.dust(F_DUST, BLUE_HI, 0.35, 0.002)
    return sc, None


# ------------------------------------------------------------------------------------------------ plan 2
IRIS = M.iris3d()
EYE_S = 1 / 0.36


def eye_lines():
    out = []
    for (name, lines), h, a in zip(M.eye_layers(), (1.6, 0.85, 0.4), (0.25, 0.5, 0.75)):
        out.append(([np.stack([l[:, 0] * EYE_S, np.full(len(l), h), -l[:, 1] * EYE_S], 1) for l in lines], a))
    return out


EYE = eye_lines()


def shot_iris(t, a=1.0):
    if t < 0.4:                                            # arrivée filée depuis la gauche
        w = (1 - ease(t / 0.4)) ** 2
        pos = np.array([0.0, 15.0, 0.6])
        tgt = np.array([-4.5 * w, 0.0, 0.0])
    elif t < 2.5:                                          # plongée à travers les couches de l'œil
        u = (t - 0.4) / 2.1
        hgt = math.exp(lerp(math.log(15.0), math.log(3.0), ease(u)))
        pos = np.array([0.0, hgt, 0.04 * hgt])
        tgt = np.array([0.0, 0.0, 0.0])
    else:                                                  # bascule vers le survol rasant du cratère
        u = ease((t - 2.5) / 2.0)
        ph = 0.4 + 0.08 * (t - 2.5)
        glide = np.array([0.84 * math.cos(ph), 0.37, 0.84 * math.sin(ph)])
        pos = smooth((0.0, 3.0, 0.12), glide, u)
        tgt = smooth((0.0, 0.0, 0.0), (0.1 * math.cos(ph), -0.05, 0.1 * math.sin(ph)), u)
    d = np.linalg.norm(pos - np.asarray(tgt))
    u2 = ease((t - 2.5) / 2.0)
    lens = E.Lens(focus=lerp(d, 0.72, u2), aperture=lerp(10, 20, u2), fog=(lerp(18, 1.3, u2), lerp(30, 2.4, u2)))
    cam = E.cam_at(pos, tgt, 42)
    sc = E.Scene(cam, lens)
    sc.exposure = lerp(1.0, 0.5, u2)
    for lines, al in EYE:
        sc.polylines(lines, BLUE, al * a * (1 - u2), 0.006)
    grow = ease_out((t - 0.2) / 2.6)
    sc.polylines(part(IRIS["cross"], grow), BLUE, 0.3 * a, 0.0012)
    sc.polylines(part(IRIS["blue"], grow), BLUE_HI, 0.45 * a, 0.0012)
    sc.polylines(part(IRIS["red"], grow), RED, 0.65 * a, 0.0014)
    for k, col, al, w in (("limb", BLUE, 0.7, 0.003), ("ticks", BLUE_HI, 0.5, 0.002), ("furrows", BLUE, 0.6, 0.002),
                          ("collar", BLUE_HI, 0.6, 0.0025), ("crypts", BLUE_HI, 0.35, 0.0015),
                          ("pupil", RED_HI, 0.75, 0.0025), ("wall", RED, 0.35, 0.0015)):
        sc.polylines(IRIS[k], col, al * a, w)
    sc.dust(M.iris_dust(), BLUE_HI, 0.3 * a, 0.002)
    sc.hole((0, -0.03, 0), 0.272, a=a)
    return sc, (W / 2, H / 2, 0.3 * a * (1 - 0.5 * u2), 0.28)


# ------------------------------------------------------------------------------------------------ plan 3
FORM_DUST = np.random.default_rng(31).uniform([-2, -0.6, -2], [2, 1.2, 2], (320, 3))


def shot_form(t, a=1.0):
    az = 0.5 + 0.16 * t
    el = math.radians(lerp(52, 38, ease(t / 4)))
    dist = lerp(5.0, 4.3, ease(t / 4))
    pos = np.array([dist * math.cos(el) * math.cos(az), dist * math.sin(el), dist * math.cos(el) * math.sin(az)])
    cam = E.cam_at(pos, (0, -0.05, 0), 44)
    sc = E.Scene(cam, E.Lens(focus=dist, aperture=16, fog=(5, 8)))
    sc.exposure = 0.85
    ring = [M.ring3d(1.0, 0.0), M.ring3d(1.03, 0.0), M.ring3d(1.1, -0.04)]
    sc.polylines(part(ring, ease_out(t / 0.9)), BLUE_HI, 0.75 * a, 0.004)
    net = ease((t - 0.2) / 0.8) * (1 - 0.8 * ease((t - 2.0) / 1.2))
    sc.polylines(M.network3d(), RED, 0.6 * a * net, 0.003)
    sw = ease_out((t - 1.2) / 2.4)
    sc.polylines(part(M.swirl3d(), sw), RED, 0.6 * a, 0.0025)
    sc.polylines(part(M.swirl3d(17, 160), sw), BLUE_HI, 0.35 * a, 0.002)
    sc.dust(FORM_DUST, BLUE_HI, 0.3 * a, 0.004)
    return sc, None


# ------------------------------------------------------------------------------------------------ plan 4
TW = ((-0.78, 0.0, 0.5), (0.78, 0.0, -0.9))
TW_S = 0.6


def shot_twins(t, a=1.0):
    u = ease(t / 4.0)
    x = lerp(-0.45, 0.45, u)
    pos = np.array([x, 0.3, 6.4])
    tgt = np.array([x * 0.6, 0.12, -0.2])
    cam = E.cam_at(pos, tgt, 44)
    fa = np.linalg.norm(pos - TW[0])
    fb = np.linalg.norm(pos - TW[1])
    lens = E.Lens(focus=lerp(fa, fb, ease((t - 1.6) / 0.9)), aperture=34, fog=(7, 11))
    sc = E.Scene(cam, lens)
    sc.exposure = 0.85
    for i, c in enumerate(TW):
        k = a * ease((t - 0.2 * i) / 0.7)
        spin = (0.25 if i else -0.2) * t
        R = M.rot_x(math.pi / 2) @ M.rot_y(spin)
        Rf = M.rot_x(math.pi / 2)
        sc.polylines(M.xf(M.torus(40, 0.62, 0.36, 0.5 if i else 0.0), R, c, TW_S), BLUE_HI, 0.5 * k, 0.003)
        sc.polylines(M.xf([M.ring3d(1.0), M.ring3d(1.025)], Rf, c, TW_S), BLUE_HI, 0.8 * k, 0.005)
        red = M.spirals3d(46, 2.2) if i == 0 else M.spirals3d(34, -1.3, 0.35)
        sc.polylines(M.xf(part(red, ease_out((t - 0.5) / 1.6)), M.rot_x(math.pi / 2) @ M.rot_y(-spin * 1.5), c, TW_S),
                     RED, 0.7 * k, 0.003)
        bust = T2.bust()
        bl = [np.stack([l[:, 0], -l[:, 1], np.full(len(l), -0.7)], 1) for l in
              (bust.pts[bust.starts[j]:bust.starts[j + 1]] for j in range(len(bust)))]
        sc.polylines(M.xf(bl, None, c, TW_S), BLUE, 0.35 * k, 0.006)
        sc.hole(np.asarray(c) + [0, 0, 0.02], 0.22 * TW_S, (0, 0, 1), k)
    return sc, None


# ------------------------------------------------------------------------------------------------ plan 5
CF, CI = np.array([-0.6, 0.0, 0.0]), np.array([0.6, 0.0, 0.0])
MINS = T2.finger_minutiae()
DOTS = T2.polar_dots()


def shot_cmp(t, a=1.0):
    az = -math.pi / 2 + 0.05 * t
    el = math.radians(48)
    dist = lerp(5.3, 4.8, ease(t / 4.5))
    pos = np.array([dist * math.cos(el) * math.cos(az), dist * math.sin(el), -dist * math.cos(el) * math.sin(az)])
    cam = E.cam_at(pos, (0, 0, 0.1), 42)
    sc = E.Scene(cam, E.Lens(focus=dist, aperture=10, fog=(6, 9)))
    sc.exposure = 0.85
    s_f = 0.5
    sc.polylines(M.xf(FINGER_LINES, None, CF, s_f), BLUE_HI, 0.7 * a, 0.002)
    sc.polylines(M.xf(FINGER_OUT, None, CF, s_f), BLUE_HI, 0.7 * a, 0.004)
    nf = int(len(MINS) * ease((t - 0.3) / 1.4))
    mf = np.stack([MINS[:nf, 0] * s_f, np.zeros(nf), MINS[:nf, 1] * s_f], 1) + CF
    s_i = 0.48
    sc.polylines(M.xf(M.torus(44, 0.64, 0.36, 0.0), M.rot_y(0.1 * t), CI, s_i), BLUE_HI, 0.45 * a, 0.0025)
    sc.polylines(M.xf([M.ring3d(1.0), M.ring3d(1.03)], None, CI, s_i), BLUE_HI, 0.8 * a, 0.004)
    sc.hole(CI + [0, 0.01, 0], 0.25 * s_i, a=a)
    ni = int(len(DOTS) * ease_out((t - 2.1) / 1.4))
    rot = 0.1 * t
    cr, sr = math.cos(rot), math.sin(rot)
    di = np.stack([(DOTS[:ni, 0] * cr - DOTS[:ni, 1] * sr) * s_i, np.zeros(ni),
                   (DOTS[:ni, 0] * sr + DOTS[:ni, 1] * cr) * s_i], 1) + CI
    for pts, t0, dur, col in ((mf, 0.3, 1.4, RED_HI), (di, 2.1, 1.4, RED)):
        if not len(pts):
            continue
        k = np.arange(len(pts))
        age = t - (t0 + dur * (k / max(1, len(DOTS if col == RED else MINS))))
        hgt = 0.09 * np.clip(age / 0.25, 0, 1)
        top = pts + np.stack([np.zeros(len(pts)), hgt, np.zeros(len(pts))], 1)
        sc.lines(np.stack([pts, top], 1), col, 0.55 * a, 0.002)
        sc.dust(top, col, 0.9 * a, 0.007)
    labels = []
    for anchor, n_end, t0, colr in ((CF + [0, 0, 0.62], 40, 0.3, BLUE_HI), (CI + [0, 0, 0.72], 240, 2.1, RED_HI)):
        if t >= t0:
            val = int(round(n_end * min(1.0, (t - t0) / 1.4)))
            s_ = f"≈ {val}" if n_end == 40 else (f"{val}" if val < n_end else f"{n_end}+")
            labels.append((cam.project(anchor[None])[0][0], s_, colr))
    return sc, None, labels


# ------------------------------------------------------------------------------------------------ Orbe
ORBE = [(0.0, "neutre"), (4.9, "surpris"), (6.0, "neutre"), (9.6, "parle"), (12.4, "neutre"), (13.4, "reflechit"),
        (16.8, "neutre"), (19.2, "surpris"), (20.4, "neutre")]


def draw_orbe_at(c, t, subject, ray=None):
    x, y = ORBE_HOME
    y += 600 * (1 - ease_out(t / 1.0)) + 9 * math.sin(t * 1.3)
    x += 5 * math.sin(t * 0.9)
    k = max(i for i, (t0, _) in enumerate(ORBE) if t0 <= t)
    expr, age = ORBE[k][1], t - ORBE[k][0]
    dx, dy = subject[0] - x, subject[1] - y
    d = math.hypot(dx, dy) or 1
    e = Etat(expr=expr, age=age, regard=(0.8 * dx / d, 0.8 * dy / d), humeur_mix=1.0)
    e.cligne = (t % 4.1) < 0.1 and t > 1.0
    if ray is not None:
        e.cible = ((ray[0] - x) / ORBE_S, (ray[1] - y) / ORBE_S)
        e.age = ray[2]
    c.save()
    c.translate(x, y)
    c.scale(ORBE_S, ORBE_S)
    draw_orbe(c, t, e)
    c.restore()


# ------------------------------------------------------------------------------------------------ image
def build(t):
    """Scène 3D + rayons + étiquettes + sujet (pour le regard de l'Orbe) + rayon de l'Orbe."""
    labels, ray = [], None
    if t < T2_:
        sc, rays = shot_finger(t)
        subj = (540, 700)
    elif t < T3:
        u = t - T2_
        sc, rays = shot_iris(u, 1 - ease((t - (T3 - 0.45)) / 0.4))
        subj = (540, 900)
    elif t < T4:
        sc, rays = shot_form(t - T3, win(t, T3, T4 - 0.4, 0.35, 0.35))
        p = sc.cam.project(np.array([[-0.35, 0.0, 0.3]]))[0][0]
        subj = tuple(p)
        if 9.7 < t < 12.3:
            ray = (p[0], p[1], t - 9.7)
    elif t < T5:
        sc, rays = shot_twins(t - T4, win(t, T4, T5 - 0.4, 0.35, 0.35))
        subj = (540, 900)
    else:
        sc, rays, labels = shot_cmp(t - T5, win(t, T5, DUR + 1, 0.4, 0.4))
        subj = (800, 900) if t > 19.0 else (300, 900)
    return sc, rays, labels, subj, ray


def blur_windows(t):
    """Sous-images pour le flou de mouvement pendant les panoramiques filés."""
    if 3.9 < t < T2_ + 0.35:
        return 5, 1 / FPS
    return 1, 0


def render_scene(c, t):
    sc, rays, labels, subj, ray = build(t)
    sc.render(c, t, rays=rays)
    return labels, subj, ray


def frame(c, t):
    n, dt = blur_windows(t)
    if n == 1:
        labels, subj, ray = render_scene(c, t)
    else:                                                  # moyenne de sous-images décalées dans le temps
        acc = None
        tmp = skia.Surface(W, H)
        for k in range(n):
            tk = t + dt * (k / (n - 1) - 0.5)
            labels, subj, ray = render_scene(tmp.getCanvas(), tk)
            a = tmp.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType,
                                                alphaType=skia.kPremul_AlphaType).astype(np.float32)
            acc = a if acc is None else acc + a
        img = skia.Image.fromarray(np.ascontiguousarray((acc / n).astype(np.uint8)), colorType=skia.kRGBA_8888_ColorType,
                                   alphaType=skia.kPremul_AlphaType)
        c.drawImage(img, 0, 0)
        labels, subj, ray = build(t)[2:]
    txt = skia.Surface(W, H)
    tc = txt.getCanvas()
    tc.clear(skia.ColorTRANSPARENT)
    f = skia.Font(F_BOLD, 74)
    for (x, y), s_, col in labels:
        wd = f.measureText(s_)
        tc.drawString(s_, float(x - wd / 2), float(y + 26), f, skia.Paint(AntiAlias=True, Color=skia.Color(*col, 240)))
    if labels:
        timg = txt.makeImageSnapshot()
        pp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(14, 14), BlendMode=skia.BlendMode.kPlus)
        pp.setAlphaf(0.7)
        c.drawImage(timg, 0, 0, skia.SamplingOptions(), pp)
        c.drawImage(timg, 0, 0)
    draw_orbe_at(c, t, subj, ray)
    for a0, a1, s in CAPS:
        caption(c, s, win(t, a0, a1, 0.25, 0.25))
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * (1 - ease(t / 0.5))))))


# ------------------------------------------------------------------------------------------------ son
def soundtrack(path):
    mx = S.Mix(DUR)
    mx.add(0, S.air(DUR, 0.05), send=0.2)
    # accords tenus : un par plan (la mineur → fa → do → sol → la mineur), qui se chevauchent
    for t0, t1, notes in ((0.0, 4.6, (S.A1, S.E2, S.A2, S.C3)), (4.3, 9.3, (S.F2, S.C3, S.A2, S.E3)),
                          (9.0, 13.3, (S.C2, S.G2, S.C3, S.E3)), (13.0, 17.3, (S.G2, S.D3, S.B2, S.G3)),
                          (17.0, DUR, (S.A1, S.E2, S.A2, S.C3, S.E3))):
        mx.add(t0, S.chord(notes, t1 - t0 + 1.2, 0.09, seed=int(t0)), send=0.5)
    mx.add(0.0, S.sub_hit(0.35), send=0.3)
    mx.add(0.2, S.whoosh(1.8, 0.08, -0.2, 0.2, 200, 700), send=0.4)        # rase-mottes
    mx.add(2.0, S.whoosh(1.7, 0.1, 0.0, 0.0, 250, 1100, seed=4), send=0.5)  # montée en grue
    mx.add(3.75, S.whoosh(0.85, 0.2, -0.8, 0.9, 400, 2200, seed=6), send=0.3)  # panoramique filé
    mx.add(T2_, S.sub_hit(0.4), send=0.4)
    mx.add(T2_ + 0.4, S.whoosh(2.2, 0.12, 0.0, 0.0, 180, 900, seed=7), send=0.5)   # plongée
    mx.add(T2_ + 0.9, S.riser(1.6, 0.06), send=0.4)
    for k in range(5):                                     # battement de cœur pendant le survol de l'iris
        mx.add(T2_ + 2.6 + 0.95 * k, S.heartbeat(0.22 + 0.03 * k), send=0.2)
    mx.add(T2_ + 2.5, S.shimmer(4.0, S.A2, 0.035), send=0.7)
    mx.add(T3, S.whoosh(1.2, 0.1, 0.6, -0.6, 300, 1300, seed=8), send=0.5)
    mx.add(T3 + 0.7, S.mallet(220, 0.05), p=-0.6, send=0.6)                # le rayon de l'Orbe
    mx.add(T3 + 1.2, S.shimmer(3.0, S.C3, 0.03), send=0.8)
    mx.add(T4, S.sub_hit(0.25), send=0.5)
    mx.add(T4 + 0.3, S.whoosh(3.6, 0.06, -0.7, 0.7, 200, 600, seed=9), send=0.5)   # travelling latéral
    mx.add(T4 + 1.7, S.mallet(196, 0.06), p=0.5, send=0.6)                 # bascule de mise au point
    mx.add(T5, S.whoosh(1.0, 0.08, 0.0, 0.0, 250, 900, seed=10), send=0.5)
    for k in range(14):                                    # points de l'empreinte, à gauche
        mx.add(T5 + 0.3 + 1.4 * k / 14, S.mallet(262 if k % 2 else 294, 0.035), p=-0.55, send=0.5)
    mx.add(T5 + 1.9, S.riser(1.6, 0.07), send=0.4)
    for k in range(24):                                    # points de l'iris, à droite, en pluie
        mx.add(T5 + 2.1 + 1.4 * (k / 24) ** 0.6, S.mallet((330, 392, 440, 494)[k % 4], 0.02), p=0.55, send=0.6)
    mx.add(T5 + 3.5, S.sub_hit(0.45), send=0.5)
    mx.add(T5 + 3.5, S.shimmer(3.0, S.A2, 0.05), send=0.8)
    mx.write(path)                                         # la voix, ajoutée plus tard, passera devant


# ------------------------------------------------------------------------------------------------ rendu
def _chunk(args):
    f0, f1, path = args
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
                           "-preset", "medium", path], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(f0, f1):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def render(out_path, procs=4):
    tmp = tempfile.mkdtemp()
    n = int(DUR * FPS)
    k = procs * 4
    jobs = [(i * n // k, (i + 1) * n // k, f"{tmp}/c{i:02d}.mp4") for i in range(k)]
    with Pool(procs) as p:
        parts = p.map(_chunk, jobs)
    with open(f"{tmp}/list.txt", "w") as f:
        f.writelines(f"file '{q}'\n" for q in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c",
                    "copy", f"{tmp}/v.mp4"], check=True)
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out_path], check=True)


def stills(out_dir, times):
    os.makedirs(out_dir, exist_ok=True)
    surf = skia.Surface(W, H)
    for t in times:
        frame(surf.getCanvas(), t)
        surf.makeImageSnapshot().save(os.path.join(out_dir, f"f_{t:05.2f}.png"))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "stills":
        stills(sys.argv[2], [float(x) for x in sys.argv[3:]])
    elif len(sys.argv) > 2 and sys.argv[1] == "son":
        soundtrack(sys.argv[2])
    else:
        render(sys.argv[1] if len(sys.argv) > 1 else "output/trait_iris_3d.mp4")
