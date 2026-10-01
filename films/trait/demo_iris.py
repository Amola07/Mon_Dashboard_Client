"""Essai du style « trait lumineux » avec l'Orbe : ton iris est plus unique que ton empreinte (≈ 21 s, sans voix).

Scènes : empreinte + œil → poussée dans l'iris → formation du motif → jumeaux → 40 points contre 240.
L'Orbe reste en bas à gauche, regarde ce dont on parle et montre la formation avec son rayon.
"""
import math
import os
import subprocess
import sys
import tempfile
import wave
from multiprocessing import Pool

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1
from films import finition as FI
from films import hook as HK
from films.persos.orbe import Etat, draw_orbe
from films.trait.trait import (BLUE, BLUE_HI, F_BOLD, FPS, H, RED, RED_HI, W, Frame, View, bust, caption, ease,
                               ease_out, eye_parts, finger_minutiae, finger_outline, fingerprint, iris_detail, lerp,
                               network, polar_dots, rosette, Shape, spirals, swirl, win)

DUR = 21.0
T_ZOOM, T_FORM, T_TWIN, T_CMP = 4.2, 9.0, 13.0, 17.0
FINGER = (540, 470, 380)                                   # x, y, échelle (largeur du doigt)
EYE = (540, 1170, 420)
FORM = (600, 860, 330)
TWINS = ((300, 930, 215), (790, 930, 215))
CMP_F = (290, 900, 330)
CMP_I = (790, 900, 230)
ORBE_HOME = (175, 1435)
ORBE_S = 0.42

CAPS = [(0.25, 4.1, "Ce n'est pas ton doigt qui te rend unique."),
        (4.3, 6.7, "C'est ton œil."),
        (6.8, 8.9, "De près, ton iris est un paysage de fibres et de sillons."),
        (9.1, 12.9, "Ce motif se dessine avant ta naissance… en partie au hasard."),
        (13.1, 16.9, "Même de vrais jumeaux ont des iris différents."),
        (17.1, 19.1, "Une empreinte : environ 40 points de comparaison."),
        (19.2, DUR, "Un iris : plus de 240.")]


# ------------------------------------------------------------------------------------------------ caméra
def view_at(t):
    if t < T_ZOOM:                                         # lente poussée vers l'œil
        u = t / T_ZOOM
        return View(540, lerp(900, 1020, ease(u)), lerp(1.0, 1.16, u))
    if t < T_FORM:                                         # plongée dans l'iris, puis dérive lente
        u = ease_out((t - T_ZOOM) / 1.6)
        z = math.exp(lerp(math.log(1.16), math.log(3.4), u)) * (1 + 0.06 * (t - T_ZOOM))
        return View(540, lerp(1020, EYE[1], ease((t - T_ZOOM) / 1.0)), z, rot=0.03 * (t - T_ZOOM))
    if t < T_TWIN:
        return View(560, 940, 1.0 + 0.025 * (t - T_FORM))
    if t < T_CMP:
        return View(545, 900, 1.02 + 0.02 * (t - T_TWIN))
    return View(540, 900, 1.0 + 0.015 * (t - T_CMP))


# ------------------------------------------------------------------------------------------------ scènes
def scene_open(fr, t, a):
    fp = fingerprint()
    clip = Shape([finger_outline()])
    place = (FINGER[0], FINGER[1], FINGER[2], 0.0)
    rev = ease_out(t / 1.6) if t < 2 else 1.0
    fr.lines(fp, place, BLUE, 0.85 * a, 1.25, upto=rev, clip=clip)
    fr.lines(clip, place, BLUE_HI, 0.8 * a, 1.6, upto=rev)
    outer = Shape([finger_outline() * 1.06, finger_outline() * 1.13])
    fr.lines(outer, place, BLUE, 0.3 * a, 1.0, upto=rev)
    fr.fade(place, 0.45, 0.88, -0.65, 0.65)
    ep = eye_parts()
    pe = (EYE[0], EYE[1], EYE[2], 0.0)
    r2 = ease_out((t - 0.3) / 1.4)
    fr.lines(ep["sweep"], pe, BLUE, 0.22 * a, 1.0, upto=r2)
    fr.lines(ep["outline"], pe, BLUE, 0.75 * a, 1.3, upto=r2)
    fr.lines(ep["crease"], pe, BLUE, 0.5 * a, 1.2, upto=r2)
    fr.lines(ep["iris"], pe, RED, 0.85 * a * ease((t - 0.6) / 0.8), 1.4, layer="r", clip=ep["opening"])
    fr.mask((EYE[0], EYE[1], EYE[2]), 0.14, a * ease((t - 0.6) / 0.8))


def scene_iris(fr, t, a, a_eye):
    """t : temps depuis T_ZOOM. L'œil (simplifié) cède la place à l'iris détaillé, au même endroit du monde."""
    ep = eye_parts()
    pe = (EYE[0], EYE[1], EYE[2], 0.0)
    if a_eye > 0.01:
        fr.lines(ep["sweep"], pe, BLUE, 0.22 * a_eye, 1.0)
        fr.lines(ep["outline"], pe, BLUE, 0.75 * a_eye, 1.4)
        fr.lines(ep["crease"], pe, BLUE, 0.5 * a_eye, 1.2)
    k = ease((t - 0.2) / 1.0) * a
    if k <= 0.01:
        return
    d = iris_detail()
    s = EYE[2] * 0.36
    rot = 0.02 * t
    pi = (EYE[0], EYE[1], s, rot)
    grow = ease_out((t - 0.2) / 2.2)
    fr.lines(d["limb"], pi, BLUE, 0.7 * k, 1.3)
    fr.lines(d["ticks"], pi, BLUE_HI, 0.45 * k, 1.0)
    fr.lines(d["furrows"], pi, BLUE, 0.5 * k, 1.0)
    fr.lines(d["cross"], pi, BLUE, 0.28 * k, 0.9, upto=grow)
    fr.lines(d["blue"], pi, BLUE_HI, 0.38 * k, 0.9, upto=grow)
    fr.lines(d["collar"], pi, BLUE_HI, 0.5 * k, 1.2)
    fr.lines(d["red"], pi, RED, 0.55 * k, 1.0, layer="r", upto=grow)
    ck = k * ease((t - 1.6) / 0.8)
    fr.lines(d["crypts"], pi, BLUE_HI, 0.6 * ck, 1.3)
    for r, ang in d["crypt_c"]:                            # creux sombres
        fr.mask((EYE[0] + s * r * math.cos(ang + rot), EYE[1] + s * r * math.sin(ang + rot), s), 0.025, 0.7 * ck)
    beat = 1 + 0.02 * math.sin(t * 2.2)
    fr.lines(d["pupil"], (EYE[0], EYE[1], s * beat, rot), RED_HI, 0.9 * k, 2.0, layer="r")
    fr.mask((EYE[0], EYE[1], s * beat), d["rp"], k)


def scene_form(fr, t, a):
    """t : temps depuis T_FORM. Réseau au hasard → tourbillon de fibres qui se fige."""
    place = (FORM[0], FORM[1], FORM[2], 0.15 * t)
    ring = Shape([np.stack([np.cos(q), np.sin(q)], 1) * r for r in (1.0, 1.025)
                  for q in [np.linspace(0, 2 * math.pi, 240)]])
    fr.lines(ring, place, BLUE_HI, 0.8 * a * ease(t / 0.6), 1.6, upto=ease_out(t / 0.9))
    net_a = ease((t - 0.3) / 0.8) * (1 - 0.75 * ease((t - 2.0) / 1.2))
    fr.lines(network(), place, RED, 0.65 * a * net_a, 1.0, layer="r")
    sw = ease_out((t - 1.3) / 2.4)
    if sw > 0:
        fr.lines(swirl(), place, RED, 0.6 * a, 1.1, layer="r", upto=max(0.02, sw))
        fr.lines(swirl(seed=17, n=160), place, BLUE_HI, 0.35 * a * sw, 0.9, upto=max(0.02, sw))


def scene_twins(fr, t, a):
    for i, (x, y, s) in enumerate(TWINS):
        k = a * ease((t - 0.15 * i) / 0.7)
        fr.lines(bust(), (x, y, s, 0.0), BLUE, 0.35 * k, 1.3)
        rot = (0.12 if i else -0.1) * t
        fr.lines(rosette(40), (x, y, s, rot), BLUE_HI, 0.55 * k, 1.0)
        fr.lines(Shape([np.stack([np.cos(q), np.sin(q)], 1) for q in [np.linspace(0, 2 * math.pi, 200)]]),
                 (x, y, s, 0), BLUE_HI, 0.8 * k, 1.6)
        red = spirals(46, 2.2) if i == 0 else spirals(34, -1.3, wob=0.35)
        fr.lines(red, (x, y, s, -rot * 1.5), RED, 0.7 * k, 1.1, layer="r", upto=ease_out((t - 0.5) / 1.6))
        fr.mask((x, y, s), 0.22, k)


def scene_cmp(fr, c_text, t, a):
    fp = fingerprint()
    clip = Shape([finger_outline()])
    pf = (CMP_F[0], CMP_F[1], CMP_F[2], 0.0)
    fr.lines(fp, pf, BLUE, 0.8 * a, 1.2, clip=clip)
    fr.lines(clip, pf, BLUE_HI, 0.8 * a, 1.6)
    fr.fade(pf, 0.45, 0.88, -0.65, 0.65)
    mins = finger_minutiae()
    nf = int(len(mins) * ease((t - 0.3) / 1.4))
    fr.dots(mins[:nf], pf, RED_HI, a, 5.5)
    pi = (CMP_I[0], CMP_I[1], CMP_I[2], 0.08 * t)
    fr.lines(rosette(44, 0.36, 0.64), pi, BLUE_HI, 0.5 * a, 1.0)
    fr.lines(Shape([np.stack([np.cos(q), np.sin(q)], 1) for q in [np.linspace(0, 2 * math.pi, 200)]]),
             pi, BLUE_HI, 0.8 * a, 1.6)
    fr.mask((CMP_I[0], CMP_I[1], CMP_I[2]), 0.25, a)
    dots = polar_dots()
    ni = int(len(dots) * ease_out((t - 2.2) / 1.4))
    fr.dots(dots[:ni], pi, RED, a, 3.6)
    for (x, y, s), n_show, n_end, t0 in ((CMP_F, nf, 40, 0.3), (CMP_I, ni, 240, 2.2)):
        if t < t0:
            continue
        val = int(round(n_end * min(1.0, (t - t0) / 1.4)))
        sc = fr.to_screen((x, y, 1, 0), np.array([[0, 0]]))[0]
        f = skia.Font(F_BOLD, 74)
        s_ = f"≈ {val}" if n_end == 40 else (f"{val}" if val < n_end else f"{n_end}+")
        wd = f.measureText(s_)
        y_txt = (CMP_I[1] + CMP_I[2] * 1.0 - fr.v.c[1]) * fr.v.z + H / 2 + 120
        col = BLUE_HI if n_end == 40 else RED_HI
        c_text.drawString(s_, float(sc[0] - wd / 2), float(y_txt), f,
                          skia.Paint(AntiAlias=True, Color=skia.Color(*col, int(240 * a))))


# ------------------------------------------------------------------------------------------------ Orbe
ORBE = [(0.0, "neutre"), (4.6, "surpris"), (5.8, "neutre"), (9.5, "parle"), (12.4, "neutre"), (13.4, "reflechit"),
        (16.8, "neutre"), (19.3, "surpris"), (20.4, "neutre")]


def orbe_state(t):
    k = max(i for i, (t0, _) in enumerate(ORBE) if t0 <= t)
    return ORBE[k][1], t - ORBE[k][0]


def subject(t):
    if t < T_ZOOM:
        return (EYE[0], EYE[1]) if t > 1.5 else (FINGER[0], FINGER[1])
    if t < T_FORM:
        return (540, 900)
    if t < T_TWIN:
        return FORM[:2]
    if t < T_CMP:
        return (540, 930)
    return CMP_I[:2] if t > 18.9 else CMP_F[:2]


def draw_orbe_at(c, t):
    x, y = ORBE_HOME
    y += 600 * (1 - ease_out(t / 1.0)) + 9 * math.sin(t * 1.3)
    x += 5 * math.sin(t * 0.9)
    expr, age = orbe_state(t)
    sx, sy = subject(t)
    dx, dy = sx - x, sy - y
    d = math.hypot(dx, dy) or 1
    e = Etat(expr=expr, age=age, regard=(0.8 * dx / d, 0.8 * dy / d), humeur_mix=1.0)
    e.cligne = (t % 4.1) < 0.1 and t > 1.0
    if 9.6 < t < 12.2:                                    # le rayon montre le motif en train de se former
        e.cible = ((FORM[0] - 0.55 * FORM[2] - x) / ORBE_S, (FORM[1] + 0.3 * FORM[2] - y) / ORBE_S)
        e.age = t - 9.6
    c.save()
    c.translate(x, y)
    c.scale(ORBE_S, ORBE_S)
    draw_orbe(c, t, e)
    c.restore()


# ------------------------------------------------------------------------------------------------ image
def frame(c, t):
    v = view_at(t)
    fr = Frame(v)
    a_open = 1 - ease((t - T_ZOOM - 0.2) / 1.2)
    if t < T_ZOOM + 1.6:
        if t < T_ZOOM:
            scene_open(fr, t, 1.0)
        else:                                              # l'empreinte s'efface, l'œil reste pendant la plongée
            fp_a = 1 - ease((t - T_ZOOM) / 0.4)
            if fp_a > 0.01:
                scene_open(fr, 4.0, 1.0)
    if T_ZOOM <= t < T_FORM + 0.3:
        scene_iris(fr, t - T_ZOOM, win(t, T_ZOOM, T_FORM - 0.45, 0.01, 0.4), a_open)
    if T_FORM - 0.1 <= t < T_TWIN + 0.3:
        scene_form(fr, t - T_FORM, win(t, T_FORM, T_TWIN - 0.4, 0.35, 0.35))
    if T_TWIN - 0.1 <= t < T_CMP + 0.3:
        scene_twins(fr, t - T_TWIN, win(t, T_TWIN, T_CMP - 0.4, 0.35, 0.35))
    txt = skia.Surface(W, H)
    txt.getCanvas().clear(skia.ColorTRANSPARENT)
    if t >= T_CMP - 0.1:
        scene_cmp(fr, txt.getCanvas(), t - T_CMP, win(t, T_CMP, DUR + 1, 0.4, 0.4))
    fr.compose(c, t)
    timg = txt.makeImageSnapshot()
    pp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(14, 14), BlendMode=skia.BlendMode.kPlus)
    pp.setAlphaf(0.7)
    c.drawImage(timg, 0, 0, skia.SamplingOptions(), pp)
    c.drawImage(timg, 0, 0)
    draw_orbe_at(c, t)
    for a0, a1, s in CAPS:
        caption(c, s, win(t, a0, a1, 0.25, 0.25))
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * (1 - ease(t / 0.5))))))


# ------------------------------------------------------------------------------------------------ son
def soundtrack(path):
    sr = E1.SR
    n = int(DUR * sr)
    y = FI.drone(DUR)[:n] * 0.9 + HK.pad(DUR, 0.04)[:n]
    fx = np.zeros(n)

    def add(t0, s_, g=1.0):
        i = int(t0 * sr)
        m = min(n - i, len(s_))
        if m > 0:
            fx[i:i + m] += s_[:m] * g

    add(0.0, HK.sub_drop(0.2))
    add(1.6, E1.swell(0.08))
    add(T_ZOOM - 0.9, FI.riser(1.0, 0.07))
    add(T_ZOOM + 0.1, HK.sub_drop(0.18))
    add(6.8, E1.swell(0.07))
    add(T_FORM, E1.swish(0.6, 0.06))
    add(T_FORM + 1.3, E1.scribble(2.2, 0.025))
    add(9.6, E1.ding(440, 0.06))
    add(T_TWIN, E1.swish(0.6, 0.06))
    add(T_TWIN + 0.5, HK.sting(0.09))
    add(T_CMP, E1.swish(0.6, 0.06))
    for k in range(14):                                    # points de l'empreinte : petits « tocs » feutrés
        add(T_CMP + 0.3 + 1.4 * ease(k / 14), E1.tock(0.035))
    add(T_CMP + 2.2, FI.riser(1.4, 0.06))
    add(T_CMP + 3.6, HK.sub_drop(0.22))
    add(T_CMP + 3.65, HK.sting(0.1))
    out = np.tanh((y + E1.soften(fx, 6)) * 1.2) / np.tanh(1.2)
    out *= 0.55 * np.minimum(1, (n - np.arange(n)) / (0.8 * sr))   # crête ≈ −14 dB : la voix passera devant
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(np.stack([out, out], 1), -1, 1) * 32767).astype(np.int16).tobytes())


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
    k = procs * 3
    jobs = [(i * n // k, (i + 1) * n // k, f"{tmp}/c{i:02d}.mp4") for i in range(k)]
    with Pool(procs) as p:
        parts = p.map(_chunk, jobs)
    with open(f"{tmp}/list.txt", "w") as f:
        f.writelines(f"file '{q}'\n" for q in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c",
                    "copy", f"{tmp}/v.mp4"], check=True)
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


def stills(out_dir, times):
    os.makedirs(out_dir, exist_ok=True)
    surf = skia.Surface(W, H)
    for t in times:
        frame(surf.getCanvas(), t)
        surf.makeImageSnapshot().save(os.path.join(out_dir, f"f_{t:05.2f}.png"))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "stills":
        stills(sys.argv[2], [float(x) for x in sys.argv[3:]])
    else:
        render(sys.argv[1] if len(sys.argv) > 1 else "output/trait_iris.mp4")
