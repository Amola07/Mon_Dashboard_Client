"""Accroche des 3 premières secondes, sobre et cinématographique, ajoutée par-dessus n'importe quel épisode.

Principes (pas d'effets « gratuits ») :
  - image 0 déjà composée et lisible : sujet éclairé, vignettage profond, phrase d'accroche déjà présente ;
  - mouvement lent et précis : léger recul caméra (×1,18 → ×1,0, ease-out sur 2,6 s), un seul reflet de lumière ;
  - typographie de titrage (Montserrat, licence OFL) : ligne d'amorce fine, mot-choc en capitales espacées qui se
    resserrent en se précisant (flou → net) ; sortie en fondu vers le haut ; puis petit titre de série discret ;
  - son : infra-grave qui tombe + accord grave résonnant avec réverbération, nappe pleine dès la première seconde.

    render(module_episode, "Tu es peut-être", "déjà mort.", "Immortalité quantique", sortie)
"""
import math
import os
import subprocess
import tempfile
import wave

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1

W, H, FPS = 1080, 1920, 30
SR = E1.SR
_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
F_MED = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-Medium.ttf"))
F_SEMI = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-SemiBold.ttf"))
F_XB = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-ExtraBold.ttf"))
T_OUT = (2.6, 3.2)                                       # sortie de la phrase d'accroche
HIDE_SUBS = 3.0                                          # pas de sous-titres pendant l'accroche (pas de doublon)


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def orbe_center(ep):
    p = ep.orbe_pose(0.0)
    return p[0][0], p[0][1]


def tracked(c, s, x, y, tf, size, tracking, paint, center=True):
    """Texte avec interlettrage (tracking en px), centré sur x."""
    f = skia.Font(tf, size)
    f.setSubpixel(True)
    ws = [f.measureText(ch) for ch in s]
    total = sum(ws) + tracking * (len(s) - 1)
    cx = x - total / 2 if center else x
    for ch, w in zip(s, ws):
        c.drawString(ch, cx, y, f, paint)
        cx += w + tracking
    return total


def paint(col, a, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(int(col[0]), int(col[1]), int(col[2]), int(max(0, min(255, a)))))
    if blur > 0.05:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def compose(c, base, t, ep, line1, line2, title):
    ox, oy = orbe_center(ep)
    u = ease_out(t / 2.6)
    zoom = 1.18 + (1.0 - 1.18) * u
    fx, fy = ox + (W / 2 - ox) * u, oy + (H / 2 - oy) * u
    hw, hh = W / (2 * zoom), H / (2 * zoom)                  # jamais de bord vide pendant le zoom
    fx, fy = min(max(fx, hw), W - hw), min(max(fy, hh), H - hh)
    c.clear(skia.Color(6, 5, 14))
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(zoom, zoom)
    c.translate(-fx, -fy)
    c.drawImage(base, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
    c.restore()
    # vignettage cinéma : très profond au départ, il se relâche
    v = 1.0 - 0.55 * ease((t - 0.4) / 2.6)
    sh = skia.GradientShader.MakeRadial(skia.Point(ox + (W / 2 - ox) * u, oy + (H / 2 - oy) * u), H * 0.62,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, int(90 * v)),
                                         skia.Color(0, 0, 0, int(235 * v))], [0.0, 0.45, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    # un seul reflet de lumière, lent, en diagonale
    if t < 2.2:
        k = ease(t / 2.0)
        x = -600 + 2300 * k
        g = skia.GradientShader.MakeLinear([skia.Point(x - 260, 0), skia.Point(x + 260, 400)],
                                           [skia.Color(255, 255, 255, 0), skia.Color(255, 240, 225, 22),
                                            skia.Color(255, 255, 255, 0)], [0.0, 0.5, 1.0])
        p = skia.Paint(Shader=g, BlendMode=skia.BlendMode.kScreen)
        c.drawRect(skia.Rect(0, 0, W, H), p)
    # phrase d'accroche
    if t < T_OUT[1]:
        out = ease((t - T_OUT[0]) / (T_OUT[1] - T_OUT[0]))
        dy = -30 * out
        a1 = 215 * (0.75 + 0.25 * ease(t / 0.5)) * (1 - out)
        tracked(c, line1, W / 2, 380 + dy, F_MED, 50, 3, paint((255, 255, 255), a1, blur=4 * out))
        k = ease_out(t / 0.9)
        trk = 16 + (7 - 16) * k                                   # les lettres se resserrent
        blur = 3.5 * (1 - k) + 6 * out
        a2 = 255 * (0.55 + 0.45 * k) * (1 - out)
        word = line2.upper()
        tracked(c, word, W / 2, 520 + dy, F_XB, 118, trk, paint((255, 70, 100), a2 * 0.55, blur=26))   # halo
        tracked(c, word, W / 2, 520 + dy, F_XB, 118, trk, paint((255, 255, 255), a2, blur=blur))
        lw = 120 * ease_out((t - 0.5) / 0.7) * (1 - out)          # fin trait d'accent sous le mot
        c.drawRect(skia.Rect(W / 2 - lw, 565 + dy, W / 2 + lw, 569 + dy), paint((255, 70, 100), 230 * (1 - out)))
    # petit titre de série, discret
    if t >= T_OUT[1] - 0.1:
        k = ease((t - (T_OUT[1] - 0.1)) / 0.8)
        tracked(c, title.upper(), W / 2, 150, F_SEMI, 26, 9, paint((255, 255, 255), 150 * k))
        c.drawRect(skia.Rect(W / 2 - 30 * k, 172, W / 2 + 30 * k, 174), paint((255, 70, 100), 170 * k))


# ------------------------------------------------------------------------------------------------ son
def _reverb(x, dur=2.6, decay=0.75, mix=0.4):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    ir = np.random.default_rng(12).standard_normal(n) * np.exp(-tt / decay)
    ir = np.convolve(ir, np.ones(40) / 40, "same")                # réverbération sombre (pas d'aigus)
    ir /= np.sqrt((ir ** 2).sum())
    wet = np.convolve(x, ir)
    dry = np.concatenate([x, np.zeros(len(wet) - len(x))])
    return dry * (1 - mix) + wet * mix * 3


def sub_drop(amp=0.5):
    n = int(2.2 * SR)
    tt = np.arange(n) / SR
    f = 36 + 44 * np.exp(-tt / 0.18)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tt / 0.006) * np.exp(-tt / 0.7) * amp


def sting(amp=0.2):
    """Accord grave résonnant (la mineur), timbre de piano feutré."""
    n = int(3.2 * SR)
    tt = np.arange(n) / SR
    y = np.zeros(n)
    for f0, g in ((110.0, 1.0), (164.8, 0.6), (220.0, 0.5), (261.6, 0.35)):
        for h, hg in ((1, 1.0), (2, 0.35), (3, 0.12), (4.2, 0.05)):
            y += g * hg * np.sin(2 * np.pi * f0 * h * tt) * np.exp(-tt * (0.9 + 0.5 * h))
    y *= np.minimum(1, tt / 0.004)
    r = _reverb(y)
    return r / np.abs(r).max() * amp                    # crête = amp


def pad(dur=4.0, amp=0.07):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = (np.sin(2 * np.pi * 55 * tt) + 0.55 * np.sin(2 * np.pi * 82.4 * tt) + 0.35 * np.sin(2 * np.pi * 110 * tt)
         + 0.2 * np.sin(2 * np.pi * 130.8 * tt))
    return y * amp * np.minimum(1, (dur - tt) / 1.8)


def enhance(src_wav, out_wav):
    with wave.open(src_wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float).reshape(-1, 2)[:, 0] / 32768
    n = len(x)
    fx = np.zeros(n)

    def add(t, s):
        i = int(t * SR)
        m = min(n - i, len(s))
        if m > 0:
            fx[i:i + m] += s[:m]

    add(0.0, sub_drop(0.32))
    add(0.0, sting(0.2))
    add(0.0, pad())
    out = np.tanh((x + fx) * 1.1) / np.tanh(1.1)
    st = np.stack([out, out], 1)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def render(ep, line1, line2, title, out_path, **_):
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    sub = E1.draw_subtitle
    E1.draw_subtitle = lambda c, t: None if t < HIDE_SUBS else sub(c, t)
    try:
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                               vid], stdin=subprocess.PIPE)
        base_s, out_s = skia.Surface(W, H), skia.Surface(W, H)
        for f in range(int(ep.DUR * FPS)):
            t = f / FPS
            ep.frame(base_s.getCanvas(), t)
            if t < 3.6:
                compose(out_s.getCanvas(), base_s.makeImageSnapshot(), t, ep, line1, line2, title)
            else:
                c = out_s.getCanvas()
                c.drawImage(base_s.makeImageSnapshot(), 0, 0)
                compose_title(c, title)
            ff.stdin.write(out_s.makeImageSnapshot().tobytes())
        ff.stdin.close()
        ff.wait()
    finally:
        E1.draw_subtitle = sub
    ep.soundtrack(f"{tmp}/a0.wav")
    enhance(f"{tmp}/a0.wav", f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", f"{tmp}/a.wav", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


def compose_title(c, title):
    tracked(c, title.upper(), W / 2, 150, F_SEMI, 26, 9, paint((255, 255, 255), 150))
    c.drawRect(skia.Rect(W / 2 - 30, 172, W / 2 + 30, 174), paint((255, 70, 100), 170))
