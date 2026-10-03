"""Démo du format « C'est quoi la différence ? » : bonhomme bâton animé, deux vignettes, sous-titres en majuscules.

Voix : Kokoro (voix locale, en attendant ElevenLabs), phrase par phrase. Vignettes : emplacements à remplir par des
images Gemini (ici des cadres provisoires).

    python -m films.baton.demo output/baton_demo.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import montage_ia as MI
from films.baton.baton import Baton, Etat, back, ease
from films.episodes.ep01_triangle import ep01 as E1
from films.persos import levres as LV

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
FONT = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "fonts", "BebasNeue-Regular.ttf"))
VOIX = os.path.join(HERE, "demo_voix.wav")

# (phrase, pose, humeur, extras) — la pose commence avec la phrase
SCRIPT = [("Ça, c'est un venin.", "pointe_g", "sourire", {"vignette": 1}),
          ("Ça, c'est un poison.", "pointe_d", "sourire", {"vignette": 2}),
          ("C'est quoi la différence ?", "reflechit", "inquiet", {"question": 1}),
          ("Le venin, il faut qu'on te l'injecte.", "index", "malin", {}),
          ("Une morsure, une piqûre.", "explique", "sourire", {}),
          ("Le poison, lui, il suffit de l'avaler ou de le toucher.", "pointe_d", "neutre", {}),
          ("Donc un serpent est venimeux…", "pointe_g", "malin", {}),
          ("mais une grenouille peut être vénéneuse.", "deux", "surpris", {})]
PAUSE = 0.32


def voix():
    import sherpa_onnx as so
    from films.episodes.ep14_chatouilles.voix import D, SID, trim
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(kokoro=so.OfflineTtsKokoroModelConfig(
        model=f"{D}/model.onnx", voices=f"{D}/voices.bin", tokens=f"{D}/tokens.txt", data_dir=f"{D}/espeak-ng-data",
        lexicon=f"{D}/lexicon-us-en.txt", lang="fr"), num_threads=4))
    tts = so.OfflineTts(cfg)
    sr, t, parts, times = 24000, 0.4, [np.zeros(int(0.4 * 24000), np.float32)], []
    for txt, *_ in SCRIPT:
        a = tts.generate(txt.replace("…", "."), sid=SID, speed=1.05)
        sr = a.sample_rate
        x = trim(np.array(a.samples, np.float32), sr)
        times.append((t, t + len(x) / sr))
        parts += [x, np.zeros(int(PAUSE * sr), np.float32)]
        t += len(x) / sr + PAUSE
    y = np.concatenate(parts + [np.zeros(int(1.2 * sr), np.float32)])
    y *= 0.8 / (np.abs(y).max() + 1e-9)
    with wave.open(VOIX, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    return times, len(y) / sr


def vignette(c, x, y, w, h, label, k, a=255):
    """Cadre provisoire (l'image Gemini viendra ici) + étiquette au-dessus."""
    if k <= 0:
        return
    s = back(k)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    f = skia.Font(FONT, 54)
    tw = f.measureText(label)
    c.drawString(label, -tw / 2, -h / 2 - 18, f, skia.Paint(AntiAlias=True, Color=skia.Color(15, 15, 18)))
    r = skia.Rect(-w / 2, -h / 2, w / 2, h / 2)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, -h / 2), skia.Point(0, h / 2)],
                                        [skia.Color(70, 75, 85), skia.Color(20, 22, 28)])
    c.drawRect(r, skia.Paint(Shader=sh))
    f2 = skia.Font(FONT, 30)
    t2 = "image " + label.lower()
    c.drawString(t2, -f2.measureText(t2) / 2, 10, f2, skia.Paint(AntiAlias=True, Color=skia.Color(200, 200, 210)))
    c.restore()


def sous_titre(c, txt, age):
    txt = txt.upper()
    f = skia.Font(FONT, 78)
    words, lines, cur = txt.split(), [], ""
    for w in words:
        if f.measureText((cur + " " + w).strip()) > W - 160:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    k = back(age / 0.18, 1.2) if age < 0.18 else 1.0
    c.save()
    c.translate(W / 2, 700)
    c.scale(0.9 + 0.1 * k, 0.9 + 0.1 * k)
    for i, ln in enumerate(lines):
        tw = f.measureText(ln)
        c.drawString(ln, -tw / 2, i * 82, f, skia.Paint(AntiAlias=True, Color=skia.Color(15, 15, 18)))
    c.restore()


def etat_a(t, times, env, rate, cues):
    idx = max([i for i, (a, b) in enumerate(times) if t >= a - 0.15] + [-1])
    e = Etat(t=t)
    if idx < 0:
        return e, idx
    prev = SCRIPT[idx - 1][1] if idx > 0 else "repos"
    _, pose, hum, ex = SCRIPT[idx]
    a, b = times[idx]
    e.pose_a, e.pose_b = prev, pose
    e.u = back((t - (a - 0.15)) / 0.38, 1.1)
    e.humeur = hum
    if t > times[-1][1] + 0.5:                                    # fin : retour au repos, sourire
        e.pose_a, e.pose_b, e.humeur = pose, "repos", "sourire"
        e.u = ease((t - times[-1][1] - 0.5) / 0.5)
    v = env[min(len(env) - 1, max(0, int((t + 0.03) * rate)))]
    cur = LV.cue_a(cues, t + 0.04)
    e.bouche = 0.0 if (v < 0.08 or cur in ("X", "A")) else min(1.0, 0.25 + 0.9 * v)
    e.cligne = 1.0 if (t % 3.1) < 0.1 else 0.0
    if ex.get("question"):
        e.question = back((t - a) / 0.3)
        e.gratte = 1.0
    e.regard = {"pointe_g": (-1, -0.6), "pointe_d": (1, -0.6), "reflechit": (0.4, -0.8)}.get(pose, (0.2, 0))
    return e, idx


def render(out):
    times, dur = voix()
    cues = LV.analyse(VOIX)
    env, rate = LV.enveloppe(VOIX)
    b = Baton()
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for fi in range(int(dur * FPS)):
        t = fi / FPS
        c = surf.getCanvas()
        c.clear(skia.Color(255, 255, 255))
        e, idx = etat_a(t, times, env, rate, cues)
        vignette(c, 300, 420, 380, 320, "VENIN", (t - times[0][0]) / 0.35)
        vignette(c, 780, 420, 380, 320, "POISON", (t - times[1][0]) / 0.35)
        if idx >= 0:
            sous_titre(c, SCRIPT[idx][0], t - times[idx][0])
        c.save()
        c.translate(W / 2, 1640)
        c.scale(1.02, 1.02)
        b.draw(c, e)
        c.restore()
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    fx = [(times[0][0], E1.pop_s(520, 0.12), 1.0), (times[1][0], E1.pop_s(600, 0.12), 1.0),
          (times[2][0], E1.swish(0.4, 0.08), 1.0)]
    MI.soundtrack(f"{tmp}/a.wav", MI.load_voice(VOIX), dur, fx)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out, f"{dur:.1f} s")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/baton_demo.mp4")
