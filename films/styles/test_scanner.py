"""Test de style « science-fiction cinéma + scanner » (10 s, sans voix).

Une image générée (décor immense, brume, une lumière orange) animée par un lent travelling, avec par-dessus une
interface de scanner dessinée en code : verrouillage de l'objet, mesure, compteur, loupe qui révèle l'intérieur.
L'interface est toujours la même d'une vidéo à l'autre : c'est elle qui fait la signature de la chaîne.

    python -m films.styles.test_scanner <image> output/test_scanner.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia
from PIL import Image

from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1

W, H, FPS, DUR = 1080, 1920, 30, 10.0
HERE = os.path.dirname(os.path.abspath(__file__))
MONO = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf")
TITRE = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "fonts", "Montserrat-ExtraBold.ttf"))
BLANC = (235, 240, 245)
ORANGE = (255, 138, 61)

# repères dans l'image (coordonnées écran à zoom 1)
MONO_R = (262, 192, 822, 1160)                       # le monolithe
HUMAIN = (538, 1462, 1562)                           # x, haut, bas de la silhouette
PAROI = (520, 560)                                   # point de la paroi examiné à la loupe
LOUPE = (850, 1420, 150)                             # centre et rayon de la loupe à l'écran


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def P(col, a=255, stroke=0.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*col, int(max(0, min(255, a)))))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def charger(path):
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x0, y0, x0 + W, y0 + H))
    return skia.Image.fromarray(np.array(im.convert("RGBA")), colorType=skia.kRGBA_8888_ColorType)


def camera(t):
    z = 1.0 + 0.11 * ease(t / DUR)
    return z, 540 + 10 * math.sin(t * 0.3), 820


def ecran(x, y, t):
    z, cx, cy = camera(t)
    return cx + (x - 540) * z, cy + (y - 820) * z


def texte(c, s, x, y, taille, col=BLANC, a=255, police=MONO, centre=False):
    f = skia.Font(police, taille)
    if centre:
        x -= f.measureText(s) / 2
    c.drawString(s, x, y, f, P(col, a))


def tape(s, u):
    """Texte qui s'écrit lettre à lettre (u de 0 à 1)."""
    n = int(len(s) * min(1.0, max(0.0, u)))
    return s[:n] + ("▌" if 0 < u < 1 else "")


def crochets(c, r, col, a, l=40, w=4):
    x0, y0, x1, y1 = r
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        c.drawLine(x, y, x + dx * l, y, P(col, a, w))
        c.drawLine(x, y, x, y + dy * l, P(col, a, w))


# ------------------------------------------------------------------------------------------------ ambiance
RNG = np.random.default_rng(4)
POUSSIERE = RNG.uniform([0, 0, 0.5, 0], [W, H, 2.2, 6.28], (90, 4))
GRAIN = [skia.Image.fromarray(np.dstack([np.full((H // 2, W // 2), v, np.uint8) for v in (255, 255, 255)] +
                                        [(RNG.random((H // 2, W // 2)) * 26).astype(np.uint8)]),
                              colorType=skia.kRGBA_8888_ColorType) for _ in range(3)]


def ambiance(c, t):
    for k in range(6):                                              # brume qui dérive
        x = (k * 260 + t * (18 + 6 * k)) % (W + 600) - 300
        y = 1250 + 120 * math.sin(k * 1.7) + 30 * math.sin(t * 0.4 + k)
        g = skia.GradientShader.MakeRadial(skia.Point(x, y), 420,
                                           [skia.Color(200, 215, 215, 26), skia.Color(200, 215, 215, 0)])
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))
    for x, y, r, ph in POUSSIERE:                                   # poussière dans la lumière
        yy = (y - t * 22 * r) % H
        xx = x + 14 * math.sin(t * 0.7 + ph)
        a = 90 + 80 * math.sin(t * 2 + ph)
        c.drawCircle(xx, yy, r, P((255, 236, 210), a))


def finitions(c, t):
    c.drawImageRect(GRAIN[int(t * FPS) % 3], skia.Rect(0, 0, W, H))
    g = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1150, [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0),
                                                                        skia.Color(0, 0, 0, 170)], [0, 0.55, 1])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))


# ------------------------------------------------------------------------------------------------ scanner
def scanner(c, t, img):
    # cadre d'écran et ligne de balayage
    u = ease((t - 0.2) / 0.6)
    if u > 0:
        crochets(c, (44, 44, W - 44, H - 44), BLANC, 160 * u, l=60 * u, w=3)
        texte(c, "SCAN // 01", 70, 100, 26, BLANC, 200 * u)
        texte(c, f"T+{t:05.2f}", W - 230, 100, 26, BLANC, 200 * u)
    if 0.2 < t < 1.4:
        y = H * ease((t - 0.2) / 1.2)
        g = skia.GradientShader.MakeLinear([skia.Point(0, y - 120), skia.Point(0, y)],
                                           [skia.Color(*ORANGE, 0), skia.Color(*ORANGE, 70)])
        c.drawRect(skia.Rect(0, y - 120, W, y), skia.Paint(Shader=g))
        c.drawLine(0, y, W, y, P(ORANGE, 230, 2))

    # verrouillage du monolithe
    x0, y0 = ecran(MONO_R[0], MONO_R[1], t)
    x1, y1 = ecran(MONO_R[2], MONO_R[3], t)
    u = ease((t - 1.0) / 0.5)
    if u > 0:
        m = 160 * (1 - u)
        clin = 255 if t > 1.8 or int(t * 12) % 2 else 90
        crochets(c, (x0 - m, y0 - m, x1 + m, y1 + m), ORANGE, clin * u, l=56, w=5)
    if t > 1.6:
        k = ease((t - 1.6) / 0.3)
        c.drawRoundRect(skia.Rect(x0 + 10, y0 + 14, x0 + 486, y0 + 92), 6, 6, P((8, 14, 18), 170 * k))
        texte(c, tape("OBJET 01 // CUBE", (t - 1.6) / 0.6), x0 + 22, y0 + 48, 30, ORANGE)
        v = ease((t - 2.0) / 1.3)
        texte(c, "ANALYSE EN COURS" if v < 1 else "ANALYSE TERMINÉE", x0 + 22, y0 + 80, 20, BLANC, 220)
        c.drawRect(skia.Rect(x0 + 272, y0 + 66, x0 + 272 + 200 * v, y0 + 76), P(ORANGE, 220))
        c.drawRect(skia.Rect(x0 + 272, y0 + 66, x0 + 472, y0 + 76), P(BLANC, 120, 1.5))

    # la silhouette pour l'échelle
    if t > 2.0:
        u = ease((t - 2.0) / 0.4)
        hx, hy0 = ecran(HUMAIN[0], HUMAIN[1], t)
        _, hy1 = ecran(HUMAIN[0], HUMAIN[2], t)
        crochets(c, (hx - 34, hy0 - 10, hx + 34, hy1 + 10), BLANC, 220 * u, l=14, w=3)
        c.drawLine(hx - 40, (hy0 + hy1) / 2, hx - 120, (hy0 + hy1) / 2 - 60, P(BLANC, 200 * u, 2))
        texte(c, tape("HUMAIN // 1,75 m", (t - 2.2) / 0.5), hx - 340, (hy0 + hy1) / 2 - 66, 22, BLANC, 230)

    # règle verticale + compteur
    if t > 3.4:
        u = ease((t - 3.4) / 0.8)
        rx = x1 + 34
        yb = y1 - (y1 - y0) * u
        c.drawLine(rx, y1, rx, yb, P(ORANGE, 230, 3))
        for k in range(0, 21):
            yk = y1 - (y1 - y0) * k / 20
            if yk >= yb:
                c.drawLine(rx, yk, rx + (18 if k % 5 == 0 else 9), yk, P(ORANGE, 200, 2))
        n = int(8_000_000_000 * ease((t - 3.6) / 1.6))
        s = f"{n:,}".replace(",", " ")
        texte(c, s, x0 + 10, y1 + 70, 52, BLANC, 255 * ease((t - 3.6) / 0.3))
        texte(c, "HUMAINS À L'INTÉRIEUR", x0 + 12, y1 + 108, 24, ORANGE, 255 * ease((t - 3.8) / 0.3))

    # loupe sur la paroi
    if t > 5.4:
        u = ease((t - 5.4) / 0.6)
        lx, ly, lr = LOUPE
        px, py = ecran(*PAROI, t)
        c.drawLine(px, py, lx - lr * 0.7 * u, ly - lr * 0.7 * u, P(BLANC, 200 * u, 2))
        c.drawCircle(px, py, 14, P(ORANGE, 255 * u, 3))
        r = lr * u
        c.save()
        clip = skia.Path()
        clip.addCircle(lx, ly, r)
        c.clipPath(clip, doAntiAlias=True)
        g = 4.0
        z, _, _ = camera(t)
        c.translate(lx, ly)
        c.scale(g * z, g * z)
        c.translate(-PAROI[0] - 4 * math.sin(t), -PAROI[1] - (t - 5.4) * 3)
        c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
        c.restore()
        c.drawCircle(lx, ly, r, P(BLANC, 230, 4))
        c.save()                                                    # anneau gradué qui tourne
        c.translate(lx, ly)
        c.rotate(t * 25)
        for k in range(48):
            a = math.radians(k * 7.5)
            l = 16 if k % 6 == 0 else 7
            c.drawLine((r + 8) * math.cos(a), (r + 8) * math.sin(a), (r + 8 + l) * math.cos(a),
                       (r + 8 + l) * math.sin(a), P(ORANGE, 220 * u, 2))
        c.restore()
        texte(c, tape("GROSSISSEMENT ×4", (t - 6.0) / 0.5), lx - lr, ly - lr - 40, 22, BLANC, 230)


def accroche(c, t):
    u = ease((t - 7.4) / 0.5)
    if u <= 0:
        return
    g = skia.GradientShader.MakeLinear([skia.Point(0, 1500), skia.Point(0, H)],
                                       [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, int(200 * u))])
    c.drawRect(skia.Rect(0, 1500, W, H), skia.Paint(Shader=g))
    s = E1.pop((t - 7.4)) if t < 7.9 else 1.0
    c.save()
    c.translate(W / 2, 1700)
    c.scale(s, s)
    texte(c, "TOUTE L'HUMANITÉ", 0, 0, 74, (255, 255, 255), 255, TITRE, centre=True)
    texte(c, "TIENT DANS UN SUCRE", 0, 86, 60, ORANGE, 255, TITRE, centre=True)
    c.restore()


# ------------------------------------------------------------------------------------------------ rendu
def render(src, out):
    img = charger(src)
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        t = f / FPS
        c = surf.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        z, cx, cy = camera(t)
        c.save()
        c.translate(cx, cy)
        c.scale(z, z)
        c.translate(-540, -820)
        c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
        c.restore()
        ambiance(c, t)
        finitions(c, t)
        scanner(c, t, img)
        accroche(c, t)
        if t < 0.4:
            c.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 255 * (1 - t / 0.4)))
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    # son : nappe + bips de l'interface
    n = int(DUR * MI.SR)
    a = MI.bed(DUR)[:n]
    a = (a.mean(1) if a.ndim == 2 else a) * 0.5
    ev = [(0.2, E1.swell(0.10)), (1.0, E1.pop_s(880, 0.12)), (1.5, E1.pop_s(1320, 0.10)), (2.0, E1.pop_s(990, 0.08)),
          (3.4, E1.pop_s(660, 0.10)), (5.4, E1.swell(0.12)), (6.0, E1.pop_s(1180, 0.08)), (7.4, E1.ding(784, 0.16))]
    ev += [(3.6 + k * 0.12, E1.pop_s(1500 + 40 * k, 0.025)) for k in range(13)]
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
    render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "output/test_scanner.mp4")
