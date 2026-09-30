"""Accroche (« hook ») des 2 premières secondes, ajoutée par-dessus n'importe quel épisode.

But : que la toute première image et le tout premier son arrêtent le pouce.

Image :
  - image 0 déjà forte : gros plan sur l'Orbe (zoom ×1,9) + phrase d'accroche en très gros, jamais d'écran vide ;
  - dès la 1re image, mouvement : recul rapide vers le plan normal (0 → 0,9 s), secousse et glitch RVB ;
  - la phrase d'accroche remonte ensuite en petit titre permanent en haut (pour ceux qui arrivent en cours de route).
Son :
  - pas de silence au départ : impact grave + « craquement » de glitch à t = 0, puis battement de cœur (ou tintement)
    sous la première phrase ; la musique est à plein niveau dès la première seconde.

    render(module_episode, "Tu es peut-être", "déjà mort.", "Immortalité quantique", sortie)
"""
import math
import subprocess
import tempfile
import wave

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1

W, H, FPS = 1080, 1920, 30
SR = E1.SR
FONT = skia.Typeface("DejaVu Sans", skia.FontStyle.Bold())
RED = (255, 70, 110)


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def orbe_center(ep):
    p = ep.orbe_pose(0.0)
    (x, y), s = p[0], p[1]
    return x, y, s


def _text(c, s, x, y, size, col, a, stroke=18):
    f = skia.Font(FONT, size)
    w = f.measureText(s)
    c.drawString(s, x - w / 2 + 5, y + 8, f, E1.P((0, 0, 0), a * 0.6, blur=10))
    c.drawString(s, x - w / 2, y, f, E1.P((8, 6, 20), a, stroke=stroke))
    c.drawString(s, x - w / 2, y, f, E1.P(col, a))
    return w


def compose(c, base, t, ep, line1, line2, title):
    """Image finale : caméra d'accroche + textes d'accroche."""
    cx, cy, _ = orbe_center(ep)
    u = ease(t / 0.9)
    zoom = 1.9 + (1.0 - 1.9) * u
    # centre de zoom : l'Orbe au départ, le centre de l'image à la fin du recul
    fx, fy = cx + (W / 2 - cx) * u, cy + (H / 2 - cy) * u
    shake = math.exp(-t / 0.25) if t < 1.2 else 0.0
    sx, sy = 16 * shake * math.sin(t * 90), 12 * shake * math.cos(t * 77)
    c.clear(skia.Color(10, 8, 24))
    c.save()
    c.translate(W / 2 + sx, H / 2 + sy)
    c.scale(zoom, zoom)
    c.translate(-fx, -fy)
    c.drawImage(base, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
    ab = math.exp(-t / 0.12) + (0.6 if 0.55 < t < 0.62 else 0.0)            # glitch RVB au départ + un rappel
    if ab > 0.03:
        for dx, mat in ((10 * ab, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]),
                        (-10 * ab, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0])):
            p = skia.Paint(ColorFilter=skia.ColorFilters.Matrix(mat), BlendMode=skia.BlendMode.kScreen)
            p.setAlphaf(min(0.6, ab * 0.6))
            c.drawImage(base, dx, 0, skia.SamplingOptions(), p)
    c.restore()
    if ab > 0.2:                                                            # bandes de glitch
        rng = np.random.default_rng(int(t * 1000))
        for _ in range(6):
            y = rng.uniform(0, H)
            h = rng.uniform(6, 30)
            c.drawRect(skia.Rect(0, y, W, y + h), E1.P((255, 255, 255), 40 * ab))
    # la phrase d'accroche : énorme au départ, puis elle remonte en titre permanent
    k = ease((t - 2.4) / 0.6)
    size1 = 92 + (46 - 92) * k
    y1 = 330 + (170 - 330) * k
    a = 255
    if k < 1:
        _text(c, line1, W / 2, y1, size1, (255, 255, 255), a)
        pop = 1.0 + 0.25 * math.exp(-t / 0.08)
        if True:
            c.save()
            c.translate(W / 2, y1 + size1 * 1.4)
            c.scale(pop, pop)
            _text(c, line2, 0, 0, size1 * 1.15, RED, a)
            c.restore()
    if k > 0:
        _text(c, title, W / 2, 170, 46, (255, 255, 255), 230 * k, stroke=12)


# ------------------------------------------------------------------------------------------------ son
def impact(amp=0.6):
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    f = 38 + 70 * np.exp(-tt / 0.07)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.5)
    click = np.random.default_rng(1).standard_normal(n) * np.exp(-tt / 0.012) * 0.5
    return (boom + click) * amp


def glitch(amp=0.12):
    n = int(0.25 * SR)
    rng = np.random.default_rng(6)
    x = rng.standard_normal(n)
    gate = (np.sin(np.arange(n) / SR * 2 * np.pi * 38) > 0).astype(float)
    return x * gate * np.exp(-np.arange(n) / SR / 0.1) * amp


def heartbeat(t0, count, amp=0.35):
    out = []
    for k in range(count):
        for dt, g in ((0.0, 1.0), (0.22, 0.7)):
            n = int(0.3 * SR)
            tt = np.arange(n) / SR
            s = np.sin(2 * np.pi * 52 * tt) * np.exp(-tt / 0.07) * g * amp
            out.append((t0 + k * 0.95 + dt, s))
    return out


def enhance(src_wav, out_wav, beats=3):
    with wave.open(src_wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float).reshape(-1, 2)[:, 0] / 32768
    n = len(x)
    fx = np.zeros(n)

    def add(t, s):
        i = int(t * SR)
        m = min(n - i, len(s))
        if m > 0:
            fx[i:i + m] += s[:m]

    add(0.0, impact(0.55))
    add(0.0, glitch(0.14))
    add(0.56, glitch(0.08))
    for t, s in heartbeat(0.9, beats):
        add(t, s)
    # nappe de départ : la musique est pleine dès la première seconde (compense le fondu d'entrée)
    tt = np.arange(int(2.5 * SR)) / SR
    pad = (np.sin(2 * np.pi * 55 * tt) + 0.5 * np.sin(2 * np.pi * 82.4 * tt) + 0.3 * np.sin(2 * np.pi * 110 * tt))
    add(0.0, pad * 0.08 * np.minimum(1, (2.5 - tt) / 1.2))
    out = np.tanh((x + fx) * 1.1) / np.tanh(1.1)
    st = np.stack([out, out], 1)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def render(ep, line1, line2, title, out_path, beats=3):
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", vid],
                          stdin=subprocess.PIPE)
    base_s, out_s = skia.Surface(W, H), skia.Surface(W, H)
    for f in range(int(ep.DUR * FPS)):
        t = f / FPS
        ep.frame(base_s.getCanvas(), t)
        compose(out_s.getCanvas(), base_s.makeImageSnapshot(), t, ep, line1, line2, title)
        ff.stdin.write(out_s.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    ep.soundtrack(f"{tmp}/a0.wav")
    enhance(f"{tmp}/a0.wav", f"{tmp}/a.wav", beats)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", f"{tmp}/a.wav", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)
