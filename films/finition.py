"""Finition « v2 » commune à tous les épisodes : ce qui fait rester sur TikTok, appliqué par-dessus une animation.

Image :
  - caméra vivante : légère poussée continue, « punch » (zoom sec + secousse) sur chaque révélation ;
  - sous-titres mot par mot, par groupes de 1 à 3 mots, mot courant mis en avant, chiffres en or ;
  - bloom (halo sur les lumières), vignettage, grain de film, aberration chromatique brève sur les impacts.
Son :
  - nappe grave et sombre (sous-graves), montée (« riser ») avant chaque révélation, impact grave dessus ;
  - mini-silence de la musique juste avant l'impact (la voix, elle, n'est jamais touchée).

Utilisation : ``render(module_episode, REVEALS, sortie)`` où REVEALS = [(t, force), …] (force 0..1).
"""
import math
import re
import subprocess
import tempfile
import wave

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1

W, H, FPS = 1080, 1920, 30
SR = E1.SR
FONT = skia.Typeface("DejaVu Sans", skia.FontStyle.Bold())
GOLD = (255, 205, 90)


# ------------------------------------------------------------------------------------------------ mots
def _syll(w):
    """Poids d'un mot ≈ nombre de syllabes (groupes de voyelles), pour répartir le temps d'une phrase."""
    v = re.findall(r"[aeiouyàâäéèêëîïôöùûü]+", w.lower())
    return max(1, len(v)) + (0.6 if any(ch.isdigit() for ch in w) else 0.0) * len(w)


def words_from_seg(seg):
    """[(mot, début, fin)] à partir des phrases minutées [(clé, texte, a, b)]."""
    out = []
    for _, txt, a, b in seg:
        ws = txt.split()
        wt = np.array([_syll(w) for w in ws], float)
        edges = a + (b - a) * np.concatenate([[0], np.cumsum(wt) / wt.sum()])
        out += [(w, edges[i], edges[i + 1]) for i, w in enumerate(ws)]
    return out


def chunks(words, max_words=3, max_chars=18):
    """Groupes de 1 à 3 mots ; un chiffre et son unité restent ensemble, la ponctuation forte coupe."""
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or len(" ".join(x[0] for x in cur + [w])) > max_chars):
            joined = any(ch.isdigit() for ch in cur[-1][0]) and not any(ch.isdigit() for ch in w[0])
            if not (joined and len(cur) < 4):
                out.append(cur)
                cur = []
        cur.append(w)
        if w[0][-1] in ".?!…":
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def draw_captions(c, t, groups, y=1560):
    cur = None
    for i, g in enumerate(groups):
        end = groups[i + 1][0][1] if i + 1 < len(groups) and groups[i + 1][0][1] - g[-1][2] < 0.7 else g[-1][2] + 0.45
        if g[0][1] - 0.04 <= t < end:
            cur = g
    if cur is None:
        return
    f = skia.Font(FONT, 86)
    txts = [w[0] for w in cur]
    widths = [f.measureText(s + " ") for s in txts]
    total = sum(widths) - f.measureText(" ")
    age = t - cur[0][1]
    sc = 1.0 + 0.12 * math.exp(-age / 0.08) * math.cos(age * 30) if age < 0.3 else 1.0
    c.save()
    c.translate(W / 2, y)
    c.scale(sc, sc)
    x = -total / 2
    for (w, a, b), wd in zip(cur, widths):
        on = t >= a
        is_num = any(ch.isdigit() for ch in w)
        col = GOLD if is_num else (255, 255, 255)
        alpha = 255 if on else 110
        pop = 1.0
        if a <= t < a + 0.18:
            pop = 1.0 + 0.18 * (1 - (t - a) / 0.18)
        c.save()
        c.translate(x + (wd - f.measureText(" ")) / 2, 0)
        c.scale(pop, pop)
        tw = f.measureText(w)
        c.drawString(w, -tw / 2 + 4, 6, f, E1.P((0, 0, 0), alpha * 0.55, blur=8))
        c.drawString(w, -tw / 2, 0, f, E1.P((8, 6, 20), alpha, stroke=16))
        c.drawString(w, -tw / 2, 0, f, E1.P(col, alpha))
        c.restore()
        x += wd
    c.restore()


# ------------------------------------------------------------------------------------------------ caméra et effets
def punch(t, reveals):
    z, sx, sy, ab = 0.0, 0.0, 0.0, 0.0
    for tr, k in reveals:
        a = t - tr
        if 0 <= a < 1.2:
            e = math.exp(-a / 0.22)
            z += 0.07 * k * e
            sx += 14 * k * e * math.sin(a * 83)
            sy += 11 * k * e * math.cos(a * 71)
            ab += k * math.exp(-a / 0.1)
    return z, sx, sy, ab


_GRAIN = []


def grain_tile(i):
    if not _GRAIN:
        rng = np.random.default_rng(3)
        for _ in range(6):
            g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
            a = np.zeros((H // 2, W // 2, 4), np.uint8)
            v = np.clip(128 + g * 60, 0, 255).astype(np.uint8)
            a[..., 0] = a[..., 1] = a[..., 2] = v
            a[..., 3] = 255
            _GRAIN.append(skia.Image.fromarray(a, colorType=skia.ColorType.kRGBA_8888_ColorType))
    return _GRAIN[i % len(_GRAIN)]


def vignette(c):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2 - 60), H * 0.72,
                                        [E1.rgb((0, 0, 0), 0), E1.rgb((0, 0, 0), 0), E1.rgb((0, 0, 0), 150)],
                                        [0.0, 0.55, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), E1.P(shader=sh))


def finish(c, base, t, fidx, reveals, groups):
    """Compose l'image finale à partir de l'image « base » de l'épisode."""
    z, sx, sy, ab = punch(t, reveals)
    zoom = 1.0 + 0.012 * (1 - math.cos(t * 0.35)) + z
    c.clear(skia.Color(10, 8, 24))
    c.save()
    c.translate(W / 2 + sx, H / 2 + sy)
    c.scale(zoom, zoom)
    c.translate(-W / 2, -H / 2)
    c.drawImage(base, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
    # bloom : les lumières débordent doucement
    bl = skia.Paint(ImageFilter=skia.ImageFilters.Blur(18, 18), BlendMode=skia.BlendMode.kScreen)
    bl.setAlphaf(0.22)
    c.drawImage(base, 0, 0, skia.SamplingOptions(), bl)
    # aberration chromatique brève sur les impacts
    if ab > 0.02:
        for dx, mat in ((6 * ab, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]),
                        (-6 * ab, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0])):
            p = skia.Paint(ColorFilter=skia.ColorFilters.Matrix(mat), BlendMode=skia.BlendMode.kScreen)
            p.setAlphaf(min(0.5, ab * 0.6))
            c.drawImage(base, dx, 0, skia.SamplingOptions(), p)
    c.restore()
    vignette(c)
    gp = skia.Paint(BlendMode=skia.BlendMode.kOverlay)
    gp.setAlphaf(0.10)
    c.drawImageRect(grain_tile(fidx), skia.Rect(0, 0, W, H), skia.SamplingOptions(), gp)
    draw_captions(c, t, groups)


# ------------------------------------------------------------------------------------------------ son
def drone(dur):
    """Nappe sombre : quinte grave (la mineur) + sous-grave qui respire lentement."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * tt / 9.0)
    y = (0.5 * np.sin(2 * np.pi * 55 * tt) + 0.3 * np.sin(2 * np.pi * 82.4 * tt + 0.3 * np.sin(tt * 0.7))
         + 0.18 * np.sin(2 * np.pi * 110 * tt) + 0.08 * np.sin(2 * np.pi * 164.8 * tt))
    return y * lfo * 0.09 * np.minimum(1, tt / 1.5)


def riser(dur=1.2, amp=0.12):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    noise = np.convolve(np.random.default_rng(2).standard_normal(n), np.ones(30) / 30, "same")
    tone = np.sin(2 * np.pi * np.cumsum(90 + 140 * u ** 2) / SR)
    return (0.6 * noise + 0.5 * tone) * u ** 2.2 * amp


def impact(amp=0.5):
    n = int(1.8 * SR)
    tt = np.arange(n) / SR
    f = 42 + 60 * np.exp(-tt / 0.08)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.45)
    thud = np.convolve(np.random.default_rng(4).standard_normal(n), np.ones(80) / 80, "same") * np.exp(-tt / 0.05)
    return (boom + 0.8 * thud) * amp


def enhance_audio(src_wav, voice_mp3, dur, reveals, out_wav):
    """Ajoute nappe, montées, impacts et respirations à la bande-son d'origine."""
    with wave.open(src_wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float).reshape(-1, 2)[:, 0] / 32768
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", voice_mp3, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    voice = np.frombuffer(raw, np.int16).astype(float) / 32768
    n = len(x)
    v = np.zeros(n)
    v[:min(n, len(voice))] = voice[:n]
    bed = x - v                                        # tout sauf la voix (musique + bruitages d'origine)
    extra = drone(n / SR)[:n]

    def add(t, s, g=1.0):
        i = int(t * SR)
        m = min(n - i, len(s))
        if m > 0 and i >= 0:
            extra[i:i + m] += s[:m] * g

    duck = np.ones(n)
    for tr, k in reveals:
        add(tr - 1.2, riser(1.2, 0.1 * k))
        add(tr, impact(0.42 * k))
        a, b = int((tr - 0.3) * SR), int(tr * SR)      # mini-silence juste avant l'impact
        if a > 0:
            duck[a:b] = np.minimum(duck[a:b], np.linspace(1, 0.15, b - a))
            c2 = min(n, b + int(0.25 * SR))
            duck[b:c2] = np.minimum(duck[b:c2], np.linspace(0.15, 1, c2 - b))
    env = np.convolve(np.abs(v), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
    vduck = 1 - 0.45 * np.minimum(1, env / 0.05)
    out = v * 1.1 + (bed + extra) * duck * vduck
    out = np.tanh(out * 1.35) / np.tanh(1.35)
    st = np.stack([out, out], 1)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------------------------------------ rendu
def render(ep, reveals, out_path, t0=0.0, t1=None):
    """ep : module d'épisode (frame, soundtrack, SEG, DUR, VOIX)."""
    t1 = ep.DUR if t1 is None else t1
    groups = chunks(words_from_seg(ep.SEG))
    E1_sub = E1.draw_subtitle
    E1.draw_subtitle = lambda c, t: None               # les sous-titres d'origine sont remplacés
    try:
        tmp = tempfile.mkdtemp()
        vid = f"{tmp}/v.mp4"
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                               vid], stdin=subprocess.PIPE)
        base_s = skia.Surface(W, H)
        out_s = skia.Surface(W, H)
        for f in range(int(t0 * FPS), int(t1 * FPS)):
            t = f / FPS
            ep.frame(base_s.getCanvas(), t)
            finish(out_s.getCanvas(), base_s.makeImageSnapshot(), t, f, reveals, groups)
            ff.stdin.write(out_s.makeImageSnapshot().tobytes())
        ff.stdin.close()
        ff.wait()
        src = f"{tmp}/a0.wav"
        ep.soundtrack(src)
        enhance_audio(src, ep.VOIX, ep.DUR, reveals, f"{tmp}/a.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-ss", str(t0), "-i", f"{tmp}/a.wav", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)
    finally:
        E1.draw_subtitle = E1_sub
