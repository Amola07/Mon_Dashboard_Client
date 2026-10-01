"""« Flatland » : le bonhomme bâton vit sur une feuille (monde en 2D) ; l'Orbe (3D) traverse sa feuille.
Pour lui, l'Orbe n'est qu'un cercle qui apparaît, grandit, rétrécit et disparaît. 16 s, 1080×1920.

Bonhomme : rig « 2D StickMan Rig v2 » (Blend Swap n° 79370), licence CC BY 3.0 — créditer l'auteur.

    python -m films.stick2d.flatland sortie.mp4
"""
import math
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import hook as HK
from films.episodes.ep01_triangle import ep01 as E1
from films.holo.holo import CYAN, CYAN_HI, W, H, Camera, Frame, circle, ease, ease_out, lerp
from films.persos.orbe import Etat, draw_orbe
from films.stick2d import stick as ST

FPS, DUR = 30, 16.0
K = 0.45                                                  # échelle bonhomme → monde (m)
OZ = 0.1                                                  # hanches du bonhomme : profondeur z sur la feuille
GROUND = -1.12
RING_C = (0.32, -0.28)                                    # centre du cercle, en coordonnées du bonhomme (x, y)
R_ORBE = 0.36
T_PASS = (6.3, 9.0)                                       # l'Orbe traverse la feuille
CAPS = [(0.3, 3.9, "Imagine un monde en 2D, plat comme une feuille."),
        (4.5, 6.3, "Toi, tu vis en 3D."),
        (6.5, 9.7, "Pour lui, tu serais un cercle qui apparaît… grandit… puis disparaît."),
        (9.9, 12.7, "Il ne peut pas te voir : tu es au-dessus de son monde."),
        (12.9, 15.9, "Et si quelqu'un, en 4D, nous regardait de la même façon ?")]


def to_world(x, y):
    return np.stack([np.asarray(x) * K, np.zeros_like(np.asarray(x, float)) + 0.002, OZ - np.asarray(y) * K], -1)


# ------------------------------------------------------------------------------------------------ chorégraphie
def stick_state(t):
    """Position des hanches (x, y bonhomme) + pose."""
    x_start, x_stop = -2.35, -0.75
    if t < 3.8:                                           # il marche
        u = t / 3.8
        x = lerp(x_start, x_stop, u)
        d = x - x_start
        f, a = ST.walk_feet(d)
        return ST.pose(hip=(x, 0.02 * math.cos(d / 0.5 * math.pi * 2)), feet={k: (v[0], v[1]) for k, v in f.items()},
                       foot_ang=a, hands=ST.walk_hands(d), lean=0.05)
    x = x_stop
    breath = 0.012 * math.sin(t * 2.2)
    if t < 6.5:                                           # il s'arrête, respire
        return ST.pose(hip=(x, breath), neck=0.05 * math.sin(t * 0.8))
    if t < 7.2:                                           # sursaut : petit saut en arrière, bras en l'air
        u = (t - 6.5) / 0.7
        jump = 0.35 * math.sin(math.pi * min(1, u * 1.4)) if u < 0.72 else 0.0
        back = -0.35 * ease_out(u)
        k = ease_out(u * 2)
        return ST.pose(hip=(x + back, jump + breath), lean=-0.18 * k,
                       hands={"l": (lerp(0.12, 0.45, k), lerp(-0.16, 1.45, k)),
                              "r": (lerp(-0.06, -0.4, k), lerp(-0.16, 1.4, k))},
                       feet={"l": (0.12, -1.1 + 0.6 * jump), "r": (-0.1, -1.1 + 0.6 * jump)})
    x -= 0.35
    if t < 9.0:                                           # il se penche et montre le cercle du doigt
        k = ease((t - 7.2) / 0.5)
        return ST.pose(hip=(x, breath - 0.06 * k), lean=0.22 * k, neck=0.15 * k,
                       hands={"l": (lerp(0.12, 1.0, k), lerp(-0.16, 0.45, k)), "r": (-0.06, -0.16)},
                       feet={"l": (0.25 * k + 0.12, -1.1), "r": (-0.1, -1.1)})
    if t < 11.0:                                          # il se gratte la tête
        k = ease((t - 9.0) / 0.5) * (1 - ease((t - 10.6) / 0.4))
        scr = 0.04 * math.sin(t * 22) * k
        return ST.pose(hip=(x, breath), neck=0.18 * k,
                       hands={"l": (lerp(0.12, 0.12 + scr, k), lerp(-0.16, 1.27, k)), "r": (-0.06, -0.16)})
    if t < 12.8:                                          # il regarde autour de lui (se retourne)
        facing = -1 if 11.3 < t < 12.2 else 1
        return ST.pose(hip=(x, breath), facing=facing, neck=0.1 * math.sin(t * 3))
    k = ease((t - 12.8) / 0.6)                            # il hausse les épaules
    sh = 0.06 * k * (0.5 + 0.5 * math.sin(t * 4))
    return ST.pose(hip=(x, breath), hands={"l": (lerp(0.12, 0.42, k), lerp(-0.16, 0.2 + sh, k)),
                                           "r": (lerp(-0.06, -0.38, k), lerp(-0.16, 0.2 + sh, k))})


def orbe_state(t):
    """Centre de l'Orbe (monde), expression, opacité."""
    cx, cz = to_world(*RING_C)[[0, 2]]
    if t < 4.5:
        return None
    if t < T_PASS[0]:                                     # il arrive d'en haut
        u = ease_out((t - 4.5) / 1.6)
        return np.array([cx + 0.6 * (1 - u), lerp(2.6, R_ORBE + 0.02, ease((t - 4.5) / (T_PASS[0] - 4.5))), cz]), "joie"
    if t < T_PASS[1]:                                     # il traverse la feuille
        u = (t - T_PASS[0]) / (T_PASS[1] - T_PASS[0])
        return np.array([cx, lerp(R_ORBE + 0.02, -R_ORBE - 0.02, u), cz]), "neutre"
    if t < 10.4:                                          # il ressort par-dessous, puis remonte à côté de la feuille
        u = ease((t - T_PASS[1]) / 1.4)
        return np.array([lerp(cx, 2.3, u), lerp(-R_ORBE, -0.2, u), lerp(cz, -0.4, u)]), "neutre"
    u = ease((t - 10.4) / 1.6)
    p = np.array([lerp(2.3, 0.35, u), lerp(-0.2, 1.25, u), lerp(-0.4, -0.2, u)])
    p[1] += 0.05 * math.sin(t * 3)
    return p, ("joie" if t < 12.9 else "neutre")


def camera(t):
    k = ease((t - 12.9) / 3.0)
    return Camera((0.0, lerp(4.1, 5.3, k), lerp(2.3, 3.3, k)), (0.0, 0.0, lerp(-0.42, -0.5, k)), fov=46)


# ------------------------------------------------------------------------------------------------ image
def frame(c, t):
    cam = camera(t)
    fr = Frame(cam)
    # la feuille : son monde
    sheet = [(-1.55, 0, 0.75), (1.55, 0, 0.75), (1.55, 0, -2.0), (-1.55, 0, -2.0)]
    fr.poly(sheet, CYAN_HI, 0.85, 2.4, closed=True)
    for z in np.arange(0.75, -2.01, -0.25):
        fr.poly([(-1.55, 0, z), (1.55, 0, z)], CYAN, 0.16, 1.0)
    for x in np.arange(-1.5, 1.51, 0.25):
        fr.poly([(x, 0, 0.75), (x, 0, -2.0)], CYAN, 0.16, 1.0)
    gx = np.linspace(-3.2, 3.2, 60)                       # le sol du bonhomme
    fr.poly(to_world(gx / K * 0.48, np.full_like(gx, GROUND)), CYAN_HI, 0.6, 2.0)
    # le cercle que voit le bonhomme
    o = orbe_state(t)
    ring_r = 0.0
    if o is not None:
        h = o[0][1]
        if abs(h) < R_ORBE:
            ring_r = math.sqrt(R_ORBE ** 2 - h ** 2)
            ctr = np.array([o[0][0], 0.004, o[0][2]])
            pts = circle(ctr, ring_r, (0, 1, 0), 96)
            sc, z = cam.project(pts)
            p = skia.Path()
            p.addPoly([skia.Point(float(x), float(y)) for x, y in sc], True)
            fr.layers["c"].getCanvas().drawPath(p, skia.Paint(AntiAlias=True, Color=skia.Color(120, 200, 255, 70)))
            fr.poly(pts, (235, 245, 255), 1.0, 3.2)
    # le bonhomme (dessiné sur la feuille)
    P = stick_state(t)
    tri, (hc, hr) = ST.triangles(P)
    sc, z = cam.project(to_world(tri[..., 0].ravel(), tri[..., 1].ravel()))
    sc = sc.reshape(-1, 3, 2)
    cc = fr.layers["c"].getCanvas()
    path = skia.Path()
    for a, b, d in sc:
        path.moveTo(*a)
        path.lineTo(*b)
        path.lineTo(*d)
        path.close()
    white = skia.Paint(AntiAlias=True, Color=skia.Color(245, 250, 255, 255))
    cc.drawPath(path, white)
    head = circle(to_world(hc[0], hc[1]), hr * K, (0, 1, 0), 64)
    hs, _ = cam.project(head)
    hp = skia.Path()
    hp.addPoly([skia.Point(float(x), float(y)) for x, y in hs], True)
    cc.drawPath(hp, white)
    # composition (fond, halos)
    cap = None
    cap_a = 0.0
    for a, b, s_ in CAPS:
        k = ease((t - a) / 0.35) * (1 - ease((t - b + 0.3) / 0.3))
        if k > cap_a:
            cap, cap_a = s_, k
    below = o is not None and o[0][1] < 0
    if below:                                             # l'Orbe sous la feuille : dessiné avant, voilé
        draw_orbe_3d(c, cam, o, t, alpha=0.35, before=True, fr=fr, cap=cap, cap_a=cap_a)
    else:
        fr.compose(c, t, caption=cap, cap_a=cap_a)
        if o is not None:
            crossing = T_PASS[0] - 0.2 < t < T_PASS[1] + 0.2
            draw_orbe_3d(c, cam, o, t, alpha=0.45 if crossing else 1.0)
    if t < 0.3:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(2, 5, 14, int(255 * (1 - t / 0.3)))))


def draw_orbe_3d(c, cam, o, t, alpha=1.0, before=False, fr=None, cap=None, cap_a=0.0):
    (pos, expr) = o
    sc, z = cam.project(pos[None])
    if z[0] <= 0.1:
        return

    def orbe():
        s = cam.focal * R_ORBE / z[0] / 140.0
        e = Etat(expr=expr, age=2.0, humeur_mix=1.0)
        e.cligne = (t % 3.4) < 0.12
        d = np.array([0.0, 0.0, OZ]) - pos
        e.regard = (0.4 * float(np.sign(d[0])) * min(1, abs(d[0]) * 2), 0.5)
        c.saveLayerAlpha(None, int(255 * alpha))
        c.save()
        c.translate(*sc[0])
        c.scale(s, s)
        draw_orbe(c, t, e)
        c.restore()
        c.restore()

    if before:
        # fond + Orbe voilé, puis la feuille par-dessus (sans refaire le fond)
        from films.holo.holo import draw_background
        draw_background(c, t)
        orbe()
        for key in ("c", "r"):
            img = fr.layers[key].makeImageSnapshot()
            for sig, al in ((26, 0.55), (7, 0.8)):
                pp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(sig, sig), BlendMode=skia.BlendMode.kPlus)
                pp.setAlphaf(al)
                c.drawImage(img, 0, 0, skia.SamplingOptions(), pp)
            c.drawImage(img, 0, 0, skia.SamplingOptions(), skia.Paint(BlendMode=skia.BlendMode.kPlus))
        from films.holo.holo import vignette, draw_caption
        vignette(c)
        if cap and cap_a > 0.01:
            draw_caption(c, cap, cap_a)
    else:
        orbe()


# ------------------------------------------------------------------------------------------------ son et rendu
def soundtrack(path):
    sr = E1.SR
    n = int(DUR * sr)
    y = E1.music(DUR) * 0.9 + HK.pad(DUR, 0.05)[:n]
    fx = np.zeros(n)

    def add(t0, s_, g=1.0):
        i = int(t0 * sr)
        m = min(n - i, len(s_))
        if m > 0:
            fx[i:i + m] += s_[:m] * g

    add(0.0, HK.sub_drop(0.22))
    k = 0
    while True:                                           # pas : un « toc » feutré à chaque appui
        t0 = 0.5 * 2 * 0.5 / (2.15 / 3.8) * k / 2 + 0.2
        if t0 > 3.8:
            break
        add(t0, E1.tock(0.07))
        k += 1
    add(4.5, E1.swell(0.14))
    add(4.6, E1.orbe_voice("joie"), 0.8)
    add(T_PASS[0], E1.ding(660, 0.12))
    add(6.5, E1.pop_s(520, 0.16))
    add(6.55, E1.swish(0.5, 0.12))
    add(7.65, E1.sparkle(0.1))
    add(T_PASS[1], E1.pop_s(380, 0.12))
    add(9.2, E1.scribble(1.2, 0.04))
    add(11.3, E1.swish(0.4, 0.08))
    add(12.2, E1.swish(0.4, 0.08))
    add(10.6, E1.orbe_voice("joie"), 0.8)
    add(12.9, HK.sting(0.16))
    out = np.tanh((y + E1.soften(fx, 6)) * 1.25) / np.tanh(1.25)
    out *= np.minimum(1, (n - np.arange(n)) / (0.8 * sr))
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(np.stack([out, out], 1), -1, 1) * 32767).astype(np.int16).tobytes())


def render(out_path):
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", f"{tmp}/a.wav", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/flatland.mp4")
