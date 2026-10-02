"""Montage commun des épisodes en clips générés, selon films/BIBLE_STYLE.md.

- Voix : les silences de plus de 0,15 s sont raccourcis à 0,40 s au plus (respiration naturelle entre les phrases) ; le minutage des phrases et des plans est
  recalculé automatiquement.
- Sous-titres : une seule ligne, petits, blancs, ombre douce, sans contour, vers 85 % de la hauteur, découpés en
  groupes de quelques mots calés sur la voix.
- Son : nappe musicale continue ≈ 18 dB sous la voix, aucun trou ; niveau final −15 LUFS.
- Image : clips agrandis en 1080×1920, recadrés pour exclure le filigrane du coin bas droit.

Usage : un épisode déclare SEG (texte, début, fin dans la voix d'origine) et SHOTS (plan, début, fin, départ dans
le clip, vitesse) puis appelle render(...).
"""
import os
import subprocess
import tempfile
import wave

import numpy as np
import skia

from films.episodes.ep01_triangle import ep01 as E1

W, H, FPS = 1080, 1920, 30
SR = 48000
_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
F_SUB = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-ExtraBold.ttf"))
CROP = ("crop=trunc(iw*0.876/2)*2:trunc(ih*0.875/2)*2:(iw-trunc(iw*0.876/2)*2)/2:0,"
        "scale=1080:1920:flags=lanczos,unsharp=5:5:0.5:5:5:0.0,fps=30")


# ------------------------------------------------------------------------------------------------ voix
def load_voice(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768


def tighten(voice, max_gap=0.40, thr_db=-38.0):
    """Raccourcit les silences à max_gap. Renvoie (voix, fonction temps_origine → temps_nouveau)."""
    win = int(0.02 * SR)
    n = len(voice) // win
    e = 20 * np.log10(np.sqrt((voice[:n * win].reshape(n, win) ** 2).mean(1)) + 1e-9)
    quiet = e < thr_db
    keep = np.ones(n, bool)
    i = 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            run = j - i
            limit = int(max_gap / 0.02)
            if run > limit and i > 0:                     # on garde le début du silence, on retire le reste
                keep[i + limit // 2: j - (limit - limit // 2)] = False
            i = j
        else:
            i += 1
    idx = np.repeat(keep, win)
    out = voice[:n * win][idx]
    old_t = np.arange(n + 1) * 0.02
    new_t = np.r_[0, np.cumsum(keep) * 0.02]
    fade = int(0.004 * SR)                                # pas de clic aux raccords
    return out, (lambda t: float(np.interp(t, old_t, new_t))), fade


# ------------------------------------------------------------------------------------------------ sous-titres
def groups(seg, max_words=6):
    """Découpe chaque phrase en groupes de ≤ max_words mots, répartis au prorata des syllabes approximatives."""
    out = []
    for txt, a, b in seg:
        words = txt.split()
        chunks = [words[i:i + max_words] for i in range(0, len(words), max_words)]
        if len(chunks) > 1 and len(chunks[-1]) <= 2:
            last = chunks.pop()
            chunks[-1] = chunks[-1] + last
        weights = [sum(len(w) for w in c) for c in chunks]
        tot = float(sum(weights))
        t = a
        for c, w in zip(chunks, weights):
            d = (b - a) * w / tot
            out.append((" ".join(c), t, t + d))
            t += d
    return out


def draw_sub(c, t, subs, size=46, y=H * 0.85):
    cur = None
    for k, (txt, a, b) in enumerate(subs):
        nxt = subs[k + 1][1] if k + 1 < len(subs) else b + 0.6
        if a - 0.03 <= t < min(nxt, b + 0.6):
            cur = txt
    if not cur:
        return
    f = skia.Font(F_SUB, size)
    while f.measureText(cur) > W - 120 and size > 30:
        size -= 2
        f = skia.Font(F_SUB, size)
    w = f.measureText(cur)
    x = W / 2 - w / 2
    c.drawString(cur, x, y + 3, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 200),
                                               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    c.drawString(cur, x, y, f, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255, 255)))


# ------------------------------------------------------------------------------------------------ image
def shot_file(tmp, clips, plan, t0, t1, start, speed):
    out = f"{tmp}/s{plan}.mp4"
    n = int(round(t1 * FPS)) - int(round(t0 * FPS))
    src = os.path.join(clips, f"{plan}.mp4")
    if os.path.exists(src):
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                                 capture_output=True, text=True).stdout)
        pad = max(0.0, start + (t1 - t0) * speed - d + 0.1)
        vf = f"setpts=(PTS-STARTPTS)/{speed},{CROP},tpad=stop_mode=clone:stop_duration={pad / speed + 0.2:.2f}"
        cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", f"{start}", "-i", src, "-an", "-vf", vf]
    else:
        vf = (f"drawtext=text='PLAN {plan}':fontcolor=white@0.8:fontsize=110:x=(w-text_w)/2:y=(h-text_h)/2-80,"
              f"drawtext=text='a generer':fontcolor=white@0.5:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2+60")
        cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=0x050814:s={W}x{H}:r={FPS}",
               "-vf", vf]
    subprocess.run(cmd + ["-frames:v", str(max(1, n)), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out],
                   check=True)
    return out


def burn(base, out, overlay):
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17",
                            "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    size = W * H * 4
    f = 0
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        arr = np.frombuffer(buf, np.uint8).reshape(H, W, 4).copy()
        overlay(skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType).getCanvas(), f / FPS)
        enc.stdin.write(arr.tobytes())
        f += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()


# ------------------------------------------------------------------------------------------------ son
def bed(dur):
    """Nappe ambiante continue, grave-médium, stéréo large, sans percussions."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(3)
    chords = [(55.0, 82.4, 110.0, 164.8), (49.0, 73.4, 98.0, 146.8), (43.65, 65.4, 87.3, 130.8), (41.2, 61.7, 82.4, 123.5)]
    L = np.zeros(n)
    R = np.zeros(n)
    seg = 8.0
    for k in range(int(dur / seg) + 2):
        ch = chords[k % len(chords)]
        a = int(max(0, (k * seg - 2) * SR))
        b = min(n, int((k * seg + seg + 2) * SR))
        if a >= n:
            break
        tt = t[a:b]
        env = np.clip((tt - (k * seg - 2)) / 2, 0, 1) * np.clip(((k + 1) * seg + 2 - tt) / 2, 0, 1)
        for i, f0 in enumerate(ch):
            for det, side in ((-0.003, 0), (0.003, 1)):
                ph = rng.uniform(0, 6.28)
                s = (np.sin(2 * np.pi * f0 * (1 + det) * tt + ph) + 0.3 * np.sin(4 * np.pi * f0 * (1 + det) * tt + ph))
                s *= env * (0.9 - 0.15 * i)
                (L if side == 0 else R)[a:b] += s
    shimmer = np.convolve(rng.standard_normal(n), np.ones(40) / 40, "same") * 0.03
    L += shimmer
    R += np.roll(shimmer, 900)
    st = np.stack([L, R], 1)
    return st / (np.abs(st).max() + 1e-9)


def soundtrack(path, voice, dur, fx_events=()):
    n = int(dur * SR)
    v = np.zeros(n)
    v[:min(n, len(voice))] = voice[:n]
    v *= 10 ** (-16 / 20) / (np.sqrt((v[np.abs(v) > 0.01] ** 2).mean()) + 1e-9)     # voix ≈ −16 dB RMS
    m = bed(dur)[:n] * 10 ** (-34 / 20) / 0.35                                       # nappe ≈ 18 dB dessous
    env = np.convolve(np.abs(v), np.ones(int(0.2 * SR)) / int(0.2 * SR), "same")
    duck = 1 - 0.4 * np.minimum(1, env / 0.03)
    fx = np.zeros(n)
    for t0, snd, g in fx_events:
        snd = np.interp(np.arange(int(len(snd) * SR / E1.SR)) * E1.SR / SR, np.arange(len(snd)), snd)
        i = int(t0 * SR)
        k = min(n - i, len(snd))
        if k > 0:
            fx[i:i + k] += snd[:k] * g
    out = np.stack([v, v], 1) + m * duck[:, None] + np.stack([fx, fx], 1) * 0.5
    out *= np.minimum(1, (n - np.arange(n)) / (0.5 * SR))[:, None]
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------------------------------------ assemblage
def render(out_path, voix, clips, seg, shots, fx_events=(), tighten_voice=True):
    voice = load_voice(voix)
    if tighten_voice:
        voice, tmap, _ = tighten(voice)
    else:
        tmap = lambda t: t
    dur = len(voice) / SR + 0.4
    seg2 = [(txt, tmap(a), tmap(b)) for txt, a, b in seg]
    edges = [tmap(s[1]) for s in shots] + [dur]
    shots2 = [(p, edges[i], edges[i + 1], st, sp) for i, (p, _, _, st, sp) in enumerate(shots)]
    subs = groups(seg2)
    tmp = tempfile.mkdtemp()
    parts = [shot_file(tmp, clips, *s) for s in shots2]
    with open(f"{tmp}/list.txt", "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                    "-c", "copy", f"{tmp}/base.mp4"], check=True)
    burn(f"{tmp}/base.mp4", f"{tmp}/v.mp4", lambda c, t: draw_sub(c, t, subs))
    soundtrack(f"{tmp}/a.wav", voice, dur, [(tmap(t), s, g) for t, s, g in fx_events])
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav",
                    "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)
    have = [s[0] for s in shots if os.path.exists(os.path.join(clips, f"{s[0]}.mp4"))]
    print(f"durée {dur:.1f} s (voix resserrée) — plans présents : {' '.join(have) or 'aucun'}")
