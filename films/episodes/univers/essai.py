"""Essai « L'Orbe rentre à la maison » : 10 s de plan continu (vitesse lumière → galaxie → plongée dans le disque).

Rendu par particules en 3D : chaque étoile est projetée puis « déposée » dans un tampon lumineux (numpy), la
poussière est un second tampon flou qui colore et assombrit ; halo par flou gaussien (skia).

    python -m films.episodes.univers.essai sortie.mp4
"""
import math
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep01_triangle.ep01 import P, ease, text_c
from films.persos.orbe import Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
DUR = 10.0
F = 1150.0                                             # focale (px)
rng = np.random.default_rng(7)

# ------------------------------------------------------------------------------------------------ la galaxie
def make_galaxy(n_disk=90000, n_bulge=22000, n_dust=26000):
    r = rng.gamma(2.0, 0.17, n_disk)
    arm = rng.integers(0, 2, n_disk)
    th = arm * math.pi + np.log(r + 0.05) / math.tan(math.radians(14)) + rng.normal(0, 0.32, n_disk)
    x, z = r * np.cos(th), r * np.sin(th)
    y = rng.normal(0, 0.012 + 0.01 * np.exp(-r / 0.2), n_disk)
    warm = np.clip(1 - r / 0.9, 0, 1)[:, None]
    col = warm * np.array([1.0, 0.82, 0.6]) + (1 - warm) * np.array([0.72, 0.8, 1.0])
    pink = rng.random(n_disk) < 0.012                                     # nébuleuses roses dans les bras
    col[pink] = [1.0, 0.45, 0.7]
    lum = rng.lognormal(0, 0.7, n_disk) * (1 + 4 * pink)
    # bulbe
    b = rng.normal(0, 1, (n_bulge, 3)) * np.array([0.11, 0.07, 0.11])
    bcol = np.tile([1.0, 0.8, 0.55], (n_bulge, 1))
    blum = rng.lognormal(0, 0.5, n_bulge) * 1.4
    pts = np.concatenate([np.stack([x, y, z], 1), b])
    cols = np.concatenate([col, bcol])
    lums = np.concatenate([lum, blum])
    # poussière : un peu en retrait des bras
    rd = rng.gamma(2.2, 0.17, n_dust)
    armd = rng.integers(0, 2, n_dust)
    thd = armd * math.pi + np.log(rd + 0.05) / math.tan(math.radians(14)) - 0.35 + rng.normal(0, 0.22, n_dust)
    dust = np.stack([rd * np.cos(thd), rng.normal(0, 0.008, n_dust), rd * np.sin(thd)], 1)
    return pts, cols, lums, dust


GAL, GCOL, GLUM, DUST = make_galaxy()
TILT = np.array([[1, 0, 0], [0, math.cos(0.35), -math.sin(0.35)], [0, math.sin(0.35), math.cos(0.35)]])
GAL, DUST = GAL @ TILT.T, DUST @ TILT.T

# étoiles lointaines (direction seule, pas de parallaxe) et étoiles proches (vitesse lumière)
SKY_DIR = rng.normal(0, 1, (5000, 3))
SKY_DIR /= np.linalg.norm(SKY_DIR, axis=1, keepdims=True)
SKY_LUM = rng.lognormal(-0.6, 0.8, 5000)
SKY_COL = np.where(rng.random((5000, 1)) < 0.3, [1.0, 0.85, 0.7], [0.85, 0.9, 1.0])
NEAR = rng.uniform(-1, 1, (3500, 3)) * np.array([60, 60, 200])


# ------------------------------------------------------------------------------------------------ caméra
TARGET = np.array([0.42, 0.0, 0.18]) @ TILT.T          # on plonge dans un bras, bulbe sur le côté
U = np.array([0.25, 0.55, -1.0])
U /= np.linalg.norm(U)


def cam_dist(t):
    return 120 * math.exp(-0.62 * t)


def warp_speed(t):
    """Vitesse des étoiles proches (effet vitesse lumière) : forte au début, puis tombe."""
    return 900 * math.exp(-1.6 * t) + 6


def camera(t):
    pos = TARGET + cam_dist(t) * U
    fwd = -U
    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(fwd, up0)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    roll = 0.25 * math.sin(t * 0.35) + 0.04 * t
    r2 = right * math.cos(roll) + up * math.sin(roll)
    u2 = -right * math.sin(roll) + up * math.cos(roll)
    return pos, r2, u2, fwd


def project(pts, pos, right, up, fwd):
    d = pts - pos
    z = d @ fwd
    x = d @ right
    y = d @ up
    return x, y, z


# ------------------------------------------------------------------------------------------------ tampon lumineux
def splat(buf, x, y, val):
    ix, iy = x.astype(np.int32), y.astype(np.int32)
    m = (ix >= 0) & (ix < buf.shape[1]) & (iy >= 0) & (iy < buf.shape[0])
    for ch in range(val.shape[1]):
        np.add.at(buf[:, :, ch], (iy[m], ix[m]), val[m, ch])


def render_light(t):
    pos, right, up, fwd = camera(t)
    img = np.zeros((H, W, 3), np.float32)
    # ciel lointain
    z = SKY_DIR @ fwd
    m = z > 0.05
    sx = W / 2 + F * (SKY_DIR[m] @ right) / z[m]
    sy = H / 2 - F * (SKY_DIR[m] @ up) / z[m]
    splat(img, sx, sy, SKY_COL[m] * SKY_LUM[m, None] * 0.55)
    # galaxie : luminosité ∝ 1/z², donc brillance de surface constante quelle que soit la distance
    x, y, z = project(GAL, pos, right, up, fwd)
    m = z > 0.004
    sx = W / 2 + F * x[m] / z[m]
    sy = H / 2 - F * y[m] / z[m]
    b = GLUM[m] * 2.2 / z[m] ** 2
    val = GCOL[m] * b[:, None]
    splat(img, sx, sy, np.minimum(val, 2.5) * 0.35)                         # étoiles résolues
    diff = np.zeros((H // 8, W // 8, 3), np.float32)                         # lueur diffuse (étoiles non résolues)
    far = (b < 25)[:, None]                                                  # seules les étoiles lointaines
    splat(diff, sx / 8, sy / 8, val * far / 64 * 0.65)
    # poussière (basse résolution, très floue) : même loi, donc épaisseur optique constante
    dsm = np.zeros((H // 4, W // 4, 1), np.float32)
    x, y, z = project(DUST, pos, right, up, fwd)
    m = z > 0.004
    splat(dsm, (W / 2 + F * x[m] / z[m]) / 4, (H / 2 - F * y[m] / z[m]) / 4,
          (13.0 / z[m] ** 2 / 16)[:, None])
    img_d = diff
    return img, dsm, img_d, (pos, right, up, fwd)


def to_image(arr):
    a = np.ascontiguousarray(arr)
    return skia.Image.fromarray(a, colorType=skia.ColorType.kRGBA_8888_ColorType)


def rgba(rgb_f):
    out = np.empty((rgb_f.shape[0], rgb_f.shape[1], 4), np.uint8)
    out[:, :, :3] = np.clip(rgb_f * 255, 0, 255)
    out[:, :, 3] = 255
    return out


def frame(c, t):
    img, dsm, diff, (pos, right, up, fwd) = render_light(t)
    # poussière : agrandie, floutée ; elle assombrit les étoiles derrière et brille en orangé
    dimg = to_image(rgba(np.repeat(np.minimum(dsm, 1.0), 3, axis=2)))
    ds = skia.Surface(W, H)
    dc = ds.getCanvas()
    dc.clear(skia.ColorBLACK)
    dp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(10, 10))
    dc.drawImageRect(dimg, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear), dp)
    dust = ds.makeImageSnapshot().toarray()[:, :, :1].astype(np.float32) / 255 * 3.2
    # lueur diffuse : agrandie et floutée, ajoutée à la lumière des étoiles
    dfi = to_image(rgba(np.minimum(diff / 4, 1.0)))
    ds2 = skia.Surface(W, H)
    ds2.getCanvas().clear(skia.ColorBLACK)
    ds2.getCanvas().drawImageRect(dfi, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear),
                                  skia.Paint(ImageFilter=skia.ImageFilters.Blur(22, 22)))
    img = img + ds2.makeImageSnapshot().toarray()[:, :, :3].astype(np.float32) / 255 * 4
    img = img * np.exp(-dust * 2.2) + dust * np.array([0.5, 0.26, 0.1], np.float32) * 0.6
    expo = 1.6 * min(1.0, max(0.3, (cam_dist(t) / 2.5) ** 0.6))              # on baisse l'exposition en plongeant
    tone = 1 - np.exp(-img * expo)
    simg = to_image(rgba(tone))
    c.clear(skia.Color(3, 3, 8))
    c.drawImage(simg, 0, 0)
    glow = skia.Paint(ImageFilter=skia.ImageFilters.Blur(14, 14), BlendMode=skia.BlendMode.kPlus)
    glow.setAlphaf(0.75)
    c.drawImage(simg, 0, 0, skia.SamplingOptions(), glow)
    glow2 = skia.Paint(ImageFilter=skia.ImageFilters.Blur(60, 60), BlendMode=skia.BlendMode.kPlus)
    glow2.setAlphaf(0.5)
    c.drawImage(simg, 0, 0, skia.SamplingOptions(), glow2)
    # vitesse lumière : étoiles proches étirées en traits
    v = warp_speed(t)
    near_a = 255 * (1 - ease((t - 3.2) / 1.2))
    if near_a > 1:
        s0 = t * 0
        zz = (NEAR[:, 2] - (200 * (1 - math.exp(-1.6 * t)) * 900 / 200 / 1.6 + 6 * t)) % 200 + 0.5
        x, y = NEAR[:, 0], NEAR[:, 1]
        z1 = zz + v / FPS * 1.6
        for i in range(0, len(NEAR)):
            if zz[i] < 1.0:
                continue
            ax, ay = W / 2 + F * x[i] / zz[i], H / 2 - F * y[i] / zz[i]
            bx, by = W / 2 + F * x[i] / z1[i], H / 2 - F * y[i] / z1[i]
            if not (-50 < ax < W + 50 and -50 < ay < H + 50):
                continue
            a = near_a * min(1.0, 30 / zz[i])
            c.drawLine(bx, by, ax, ay, P((215, 225, 255), a, stroke=1.6 if zz[i] > 20 else 2.6))
        del s0
    # l'Orbe, petit, qui file vers la galaxie
    e = Etat(expr="surpris" if t < 6.5 else "amour", age=t, humeur_mix=1.0)
    e.regard = (0.0, -0.6)
    e.cligne = (t % 3.1) < 0.12
    c.save()
    c.translate(540 + 14 * math.sin(t * 1.7), 1480 + 10 * math.sin(t * 2.3))
    c.scale(0.42, 0.42)
    draw_orbe(c, t, e)
    c.restore()
    # textes : la phrase ironique, et l'échelle
    text_c(c, "« L'univers, c'est pas si grand »", 540, 250, 50, (255, 255, 255), 255)
    dist = cam_dist(t)
    if t > 5.2:
        k = ease((t - 5.2) / 0.5) * (1 - ease((t - 8.4) / 0.5))
        text_c(c, "une galaxie : 100 000 années-lumière", 540, 1700, 40, (255, 225, 170), 255 * k)
    if t > 1.0:
        k = ease((t - 1.0) / 0.5) * (1 - ease((t - 4.4) / 0.5))
        text_c(c, "l'univers observable : 93 milliards d'années-lumière", 540, 1700, 34, (200, 215, 255), 255 * k)


def soundtrack(path):
    sr = E1.SR
    n = int(DUR * sr)
    y = E1.music(DUR) * 1.4
    fx = np.zeros(n)

    def add(t0, s_, g=1.0):
        i = int(t0 * sr)
        m = min(n - i, len(s_))
        fx[i:i + m] += s_[:m] * g

    add(0.0, E1.swish(3.2, 0.3))
    add(0.1, E1.swell(0.25))
    add(5.0, E1.swell(0.2))
    add(6.5, E1.swish(3.4, 0.22))
    add(7.2, E1.sparkle(0.1))
    out_ = y + E1.soften(fx, 6)
    fade = np.minimum(1, np.minimum(np.arange(n) / (0.3 * sr), (n - np.arange(n)) / (0.8 * sr)))
    out_ = np.tanh(out_ * fade * 1.4) / np.tanh(1.4)
    st = np.stack([out_, out_], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def render(out_path):
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    wav = f"{tmp}/a.wav"
    soundtrack(wav)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out_path], check=True)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/univers_essai.mp4")
