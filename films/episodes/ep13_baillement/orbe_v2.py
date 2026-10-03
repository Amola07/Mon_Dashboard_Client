"""Épisode 13, version 2 (≈ 70 s) : même voix, montée en version courte et plus « TikTok ».

Changements par rapport à la v1 (statistiques : 85 % des gens partent à la 1re seconde) :
  • accroche géante dès l'image 0 (« TU VAS BÂILLER AVANT LA FIN ») + un personnage qui bâille en très gros plan ;
  • l'Orbe plus gros (il ne bâille jamais) ; fond plus lumineux et coloré ;
  • gros sous-titres karaoké au centre (mot prononcé en jaune) ;
  • voix resserrée sur les passages les plus forts (Provine, fœtus, chiens, psychopathie, cerveau qui refroidit,
    poche de froid, mystère) et accélérée de 6 % ; petit « punch » de caméra à chaque nouvelle phrase.

Les scènes de la v1 (orbe_ep13) sont réutilisées : elles sont écrites en temps de voix d'origine, et O(t) ramène le
temps de la v2 à ce temps.

    python -m films.episodes.ep13_baillement.orbe_v2 output/ep13_orbe_v2_court.mp4
"""
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
from films.episodes.ep13_baillement import orbe_ep13 as B
from films.episodes.ep13_baillement.montage import SEG
from films.persos import levres as LV
from films.persos.orbe import Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.mp3")
VOIX2 = os.path.join(HERE, "audio", "voix_v2.wav")
F_HOOK = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "..", "fonts", "Montserrat-ExtraBold.ttf"))
F_SUB = F_HOOK

# passages gardés (temps de la voix d'origine)
GARDE = [(0.00, 2.35), (3.25, 6.20), (6.69, 11.10), (11.70, 23.51), (36.81, 39.68), (48.36, 50.36),
         (54.46, 60.59), (61.21, 75.33), (76.02, 78.85), (89.97, 94.26), (100.43, 104.59), (109.80, 118.47)]
PAUSE, VITESSE = 0.22, 1.06
T_FIN = 2.2                                                       # « TU AS BÂILLÉ ? » à la fin

# ------------------------------------------------------------------------------------------------ voix et temps
_DEBUTS = []


def construire_voix():
    v = MI.load_voice(VOIX)
    sr = MI.SR
    parts, t = [], 0.0
    _DEBUTS.clear()
    for a, b in GARDE:
        x = v[int((a - 0.04) * sr) if a > 0.04 else 0: int((b + 0.08) * sr)]
        _DEBUTS.append((t, a, b))
        parts += [x, np.zeros(int(PAUSE * sr))]
        t += len(x) / sr + PAUSE
    y = np.concatenate(parts)
    tmp = tempfile.mkdtemp()
    with wave.open(f"{tmp}/v.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.wav", "-af", f"atempo={VITESSE}", "-ar", str(sr),
                    VOIX2], check=True)
    with wave.open(VOIX2) as w:
        return w.getnframes() / sr


def O(t):
    """Temps v2 → temps de la voix d'origine (pendant les pauses, l'instant de fin du passage est figé)."""
    ts = t * VITESSE
    o = 0.0
    for t0, a, b in _DEBUTS:
        xa = max(0.0, a - 0.04)
        if ts >= t0:
            o = min(b + 0.08, xa + (ts - t0))
    return o


def N(o):
    """Temps d'origine → temps v2 (pour les sous-titres)."""
    for t0, a, b in _DEBUTS:
        xa = max(0.0, a - 0.04)
        if xa <= o <= b + 0.08:
            return (t0 + o - xa) / VITESSE
    return None


def segments_v2():
    out = []
    for txt, a, b in SEG:
        na, nb = N(a), N(b)
        if na is not None and nb is not None:
            out.append((txt, na, nb))
    return out


# ------------------------------------------------------------------------------------------------ image
def fond(c, t):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                        [skia.Color(62, 30, 120), skia.Color(28, 44, 130), skia.Color(16, 70, 120)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    for x, y, r, col in ((180 + 60 * math.sin(t * 0.3), 420, 520, (255, 90, 200)),
                         (900, 1300 + 80 * math.sin(t * 0.25), 600, (60, 220, 255))):
        g = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [skia.Color(*col, 70), skia.Color(*col, 0)])
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))


def texte_geant(c, lignes, y0, k, taille=150, col=(255, 255, 255)):
    f = skia.Font(F_HOOK, taille)
    s = E1.pop(k) if k < 0.5 else 1.0
    c.save()
    c.translate(W / 2, y0)
    c.scale(s, s)
    for i, ln in enumerate(lignes):
        w = f.measureText(ln)
        while w > W - 70:
            f = skia.Font(F_HOOK, f.getSize() - 6)
            w = f.measureText(ln)
        y = i * taille * 1.02
        c.drawString(ln, -w / 2, y, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0),
                                                   Style=skia.Paint.kStroke_Style, StrokeWidth=22,
                                                   StrokeJoin=skia.Paint.kRound_Join))
        c.drawString(ln, -w / 2, y, f, skia.Paint(AntiAlias=True, Color=skia.Color(*col)))
    c.restore()


def accroche(c, t):
    """0 → 2,4 s : un visage qui bâille en très gros plan + défi en lettres géantes."""
    a = 255 * (1 - B.ease((t - 2.2) / 0.3))
    if a <= 1:
        return
    y = B.yawn_curve(t + 0.35, 2.6)
    c.saveLayerAlpha(None, int(a))
    B.pion(c, W / 2, 1180, 3.4, B.PINK, y, 255, body=False, glow=0.8)
    texte_geant(c, ["TU VAS", "BÂILLER", "AVANT LA FIN"], 300, t / 0.3)
    c.restore()


def fin(c, t, dur):
    k = (t - (dur - T_FIN)) / 0.3
    if k <= 0:
        return
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(10, 8, 30, int(200 * min(1, k)))))
    texte_geant(c, ["ALORS,", "TU AS BÂILLÉ ?"], 760, k, 130, (255, 214, 10))


MOTS = []


def preparer_mots(segs):
    MOTS.clear()
    for txt, a, b in segs:
        ws = txt.split()
        lens = [len(re.sub(r"\W", "", w)) + 1.5 for w in ws]
        t = a
        for j, (w, l) in enumerate(zip(ws, lens)):
            d = (b - a) * l / sum(lens)
            MOTS.append((w.upper(), t, t + d, len(MOTS) - j, j))
            t += d


def sous_titres(c, t):
    i = max([k for k, m in enumerate(MOTS) if m[1] <= t + 0.03] + [-1])
    if i < 0 or t > MOTS[i][2] + 0.5:
        return None
    deb, rang = MOTS[i][3], MOTS[i][4]
    g0 = deb + (rang // 3) * 3
    grp = [m for m in MOTS[g0:g0 + 3] if m[3] == deb]
    size = 84
    f = skia.Font(F_SUB, size)
    sp = f.measureText(" ")
    tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    while tot > W - 90:
        size -= 4
        f = skia.Font(F_SUB, size)
        sp = f.measureText(" ")
        tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    age = t - MOTS[g0][1]
    pop = 1 + 0.16 * math.exp(-age * 12) * math.cos(age * 28) if age < 0.4 else 1.0
    c.save()
    c.translate(W / 2, 1265)
    c.scale(pop, pop)
    x = -tot / 2
    for k, m in enumerate(grp):
        wd = f.measureText(m[0])
        on = g0 + k == i
        c.drawString(m[0], x, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0),
                                               Style=skia.Paint.kStroke_Style, StrokeWidth=16,
                                               StrokeJoin=skia.Paint.kRound_Join))
        c.drawString(m[0], x, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(255, 214, 10) if on else
                                               skia.Color(255, 255, 255)))
        x += wd + sp
    c.restore()
    return g0


SYNC = None


def orbe(c, t, o):
    (yeux, hum), (_, hum0), tc = B.last(B.MOODS, o)
    x, y, s = 540.0, 1585.0, 0.95
    e = Etat(expr="parle", age=o - tc, levres=SYNC(t), yeux=yeux, humeur=hum or "calme",
             humeur_avant=hum0 or "calme", humeur_mix=(o - tc) / 0.5)
    e.cligne = yeux == "parle" and (t % 3.4) < 0.11
    (fp,), _, _ = B.last([(a_, b_) for a_, b_ in B.FOCUS], o)
    if fp is not None:
        d = (fp[0] - x, fp[1] - y)
        n = math.hypot(*d) or 1.0
        e.regard = (0.7 * d[0] / n, 0.7 * d[1] / n)
    k = E1.pop(t - 2.2) if t < 2.8 else 1.0                        # l'Orbe arrive avec un « pop » après l'accroche
    if k <= 0:
        return
    c.save()
    c.translate(x, y + 6 * math.sin(t * 2.1))
    c.scale(s * k, s * k)
    draw_orbe(c, t, e)
    c.restore()


def render(out):
    global SYNC
    dur = construire_voix() + T_FIN
    SYNC = LV.Synchro(VOIX2)
    segs = segments_v2()
    preparer_mots(segs)
    E1.TIMING = []
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    last_g, t_g = None, -9.0
    for f in range(int(dur * FPS)):
        t = f / FPS
        o = O(t)
        B.T = t
        c = surf.getCanvas()
        fond(c, t)
        # punch de caméra à chaque nouveau groupe de sous-titres
        z = 1.0 + 0.05 * math.exp(-(t - t_g) * 8) if t - t_g < 0.6 else 1.0
        c.save()
        c.translate(W / 2, 700)
        c.scale(z * 1.08, z * 1.08)                                 # illustrations un peu plus grandes
        c.translate(-W / 2, -700)
        if t >= 2.2:
            for sc in B.SCENES:
                sc(c, o)
            B.sc_fin(c, o, t)
        c.restore()
        accroche(c, t)
        orbe(c, t, o)
        g = sous_titres(c, t) if t >= 2.2 else None
        if g is not None and g != last_g:
            last_g, t_g = g, t
        fin(c, t, dur)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    fx = [(0.0, E1.swell(0.14), 1.0), (0.05, E1.pop_s(420, 0.14), 1.0), (2.2, E1.pop_s(620, 0.14), 1.0),
          (dur - T_FIN, E1.ding(784, 0.14), 1.0)]
    MI.soundtrack(f"{tmp}/a.wav", MI.load_voice(VOIX2), dur, fx)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out, f"{dur:.1f} s")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep13_orbe_v2_court.mp4")
