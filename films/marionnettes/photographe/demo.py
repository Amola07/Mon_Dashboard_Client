"""Démo de la marionnette du photographe : décor de forêt en aplats, coucou, phrase synchronisée, haussement d'épaules.

Voix : Piper « fr_FR-tom-medium » (sherpa-onnx), générée phrase par phrase. Bouche : Rhubarb Lip Sync → trois
bouches de la planche (+ la bouche d'origine au repos).

    python -m films.marionnettes.photographe.demo output/marionnette_demo.mp4
"""
import glob
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1
from films.marionnettes.photographe.rig import Photographe
from films.persos import levres as LV

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
PIPER = os.environ.get("PIPER_TOM", "/tmp/claude-0/-home-user-Mon-Dashboard-Client/074a8d09-4de2-5e84-a06b-0cddbabdcc79/"
                       "scratchpad/tts/vits-piper-fr_FR-tom-medium")
LIGNES = [(1.0, "Salut !"), (None, "Moi, c'est Sam."), (None, "Je photographie les animaux sauvages."),
          (None, "Enfin…"), (None, "quand ils veulent bien se montrer.")]
PAUSES = [0.3, 0.35, 0.45, 0.4]
VOIX = os.path.join(HERE, "demo_voix.wav")


# ------------------------------------------------------------------------------------------------ voix
def voix():
    import sherpa_onnx as so
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(vits=so.OfflineTtsVitsModelConfig(
        model=glob.glob(f"{PIPER}/*.onnx")[0], tokens=f"{PIPER}/tokens.txt", data_dir=f"{PIPER}/espeak-ng-data"),
        num_threads=4))
    tts = so.OfflineTts(cfg)
    sr = 44100
    out, t, subs = [np.zeros(int(LIGNES[0][0] * sr), np.float32)], LIGNES[0][0], []
    for i, (_, txt) in enumerate(LIGNES):
        a = tts.generate(txt, sid=0, speed=1.0)
        x = np.array(a.samples, np.float32)
        idx = np.where(np.abs(x) > 0.01)[0]
        x = x[max(0, idx[0] - 400): idx[-1] + 4000]
        subs.append((txt, t, t + len(x) / sr))
        out.append(x)
        t += len(x) / sr
        if i < len(PAUSES):
            out.append(np.zeros(int(PAUSES[i] * sr), np.float32))
            t += PAUSES[i]
    y = np.concatenate(out + [np.zeros(int(2.0 * sr), np.float32)])
    y *= 0.8 / (np.abs(y).max() + 1e-9)
    with wave.open(VOIX, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    return subs, len(y) / sr


# ------------------------------------------------------------------------------------------------ décor
INK = skia.Color(28, 30, 26)


def paint(c, a=255, stroke=0.0):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*c, a) if len(c) == 3 else c)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def blob(cx, cy, r, n=9, seed=0, k=0.18):
    """Feuillage en nuage : cercle bosselé."""
    rng = np.random.default_rng(seed)
    path = skia.Path()
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1 + k * rng.uniform(-1, 1))
        pts.append((cx + rr * math.cos(a), cy + rr * 0.85 * math.sin(a)))
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        dx, dy = mx - cx, my - cy
        d = math.hypot(dx, dy) or 1
        bump = r * 0.32
        ctrl = (mx + dx / d * bump, my + dy / d * bump)
        if i == 0:
            path.moveTo(*p0)
        path.quadTo(*ctrl, *p1)
    path.close()
    return path


def arbre(c, x, base, h, r, col, seed, trunk=(110, 80, 55), outline=4.0):
    c.drawRect(skia.Rect(x - r * 0.12, base - h, x + r * 0.12, base), paint(trunk))
    c.drawRect(skia.Rect(x - r * 0.12, base - h, x + r * 0.12, base), paint((28, 30, 26), stroke=outline))
    for j, (dx, dy, s) in enumerate(((0, -h, 1.0), (-r * 0.55, -h + r * 0.45, 0.7), (r * 0.6, -h + r * 0.4, 0.75))):
        p = blob(x + dx, base + dy, r * s, seed=seed * 7 + j)
        c.drawPath(p, paint(col))
        c.drawPath(p, paint((28, 30, 26), stroke=outline))
        hl = blob(x + dx - r * s * 0.2, base + dy - r * s * 0.2, r * s * 0.45, n=7, seed=seed * 11 + j)
        c.drawPath(hl, paint(tuple(min(255, int(v * 1.15)) for v in col)))


def decor():
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    sky = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 1100)],
                                         [skia.Color(150, 205, 235), skia.Color(215, 238, 225)])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sky))
    for i, x in enumerate(range(-60, W + 120, 150)):                     # forêt lointaine
        c.drawPath(blob(x, 900, 150, seed=i), paint((150, 195, 140)))
    for i, x in enumerate((60, 330, 640, 930)):                          # arbres du fond
        arbre(c, x, 1250, 520 + 60 * (i % 2), 190, (95, 160, 85), seed=i + 10, outline=3.0)
    ground = skia.Path()
    ground.moveTo(0, 1180)
    ground.cubicTo(300, 1140, 700, 1210, W, 1160)
    ground.lineTo(W, H)
    ground.lineTo(0, H)
    ground.close()
    c.drawPath(ground, paint((120, 185, 90)))
    c.drawPath(ground, paint((28, 30, 26), stroke=4))
    path = skia.Path()                                                   # chemin de terre
    path.moveTo(430, 1200)
    path.cubicTo(380, 1450, 200, 1650, 120, H)
    path.lineTo(760, H)
    path.cubicTo(700, 1650, 600, 1450, 560, 1200)
    path.close()
    c.drawPath(path, paint((215, 190, 140)))
    c.drawPath(path, paint((28, 30, 26), stroke=4))
    for i, (x, y, r) in enumerate(((60, 1300, 110), (1010, 1320, 120), (930, 1780, 140), (40, 1800, 130))):
        p = blob(x, y, r, seed=40 + i)                                   # buissons
        c.drawPath(p, paint((70, 140, 70)))
        c.drawPath(p, paint((28, 30, 26), stroke=4))
    for i, x in enumerate((-40, 1110)):                                  # gros troncs au premier plan
        c.drawRect(skia.Rect(x - 70, 0, x + 70, H), paint((95, 70, 50)))
        c.drawRect(skia.Rect(x - 70, 0, x + 70, H), paint((28, 30, 26), stroke=5))
    return surf.makeImageSnapshot()


# ------------------------------------------------------------------------------------------------ animation
def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def bouche_a(cues, env, rate, t):
    cur = LV.cue_a(cues, t + 0.04)
    v = env[min(len(env) - 1, max(0, int((t + 0.03) * rate)))]
    if cur in ("X",) or v < 0.08:
        return "repos"
    if cur == "A":
        return "fermee"
    if cur in ("D", "C", "H") and v > 0.45:
        return "ouverte"
    return "mi"


def pose_a(t, cues, env, rate, dur):
    p = {"respire": 3 * math.sin(t * 2.0)}
    # coucou de 0,6 s à 2,8 s
    up = ease((t - 0.6) / 0.35) * (1 - ease((t - 2.6) / 0.4))
    p["epaule_d"] = -155 * up
    p["coude_d"] = (-20 + 28 * math.sin(t * 13)) * up
    v = env[min(len(env) - 1, max(0, int(t * rate)))]
    p["tete"] = 2.5 * math.sin(t * 1.3) + 3 * v * math.sin(t * 7)
    # haussement d'épaules sur « Enfin… »
    hs = ease((t - T_SHRUG) / 0.3) * (1 - ease((t - T_SHRUG - 1.6) / 0.4))
    p["respire"] += 9 * hs
    p["tete"] += -6 * hs
    p["epaule_d"] = p["epaule_d"] - 8 * hs
    p["bouche"] = bouche_a(cues, env, rate, t)
    blinks = (0.3, 3.4, dur - 1.2)
    p["cligne"] = max([max(0.0, 1 - abs(t - b) / 0.08) for b in blinks] + [0.0])
    if hs > 0.5:
        p["cligne"] = max(p["cligne"], 0.45)                            # regard blasé
    return p


T_SHRUG = 6.0


def render(out):
    global T_SHRUG
    subs, dur = voix()
    T_SHRUG = subs[3][1]
    cues = LV.analyse(VOIX)
    env, rate = LV.enveloppe(VOIX)
    bg = decor()
    ph = Photographe()
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    groups = MI.groups([(s, a, b) for s, a, b in subs])
    for f in range(int(dur * FPS)):
        t = f / FPS
        c = surf.getCanvas()
        zoom = 1 + 0.03 * t / dur                                          # léger travelling avant
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(zoom, zoom)
        c.translate(-W / 2, -H / 2)
        c.drawImage(bg, 0, 0)
        sh = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 60))
        c.drawOval(skia.Rect(290, 1465, 800, 1525), sh)                  # ombre au sol
        c.save()
        c.translate(323, 513)
        c.scale(1.4, 1.4)
        ph.draw(c, pose_a(t, cues, env, rate, dur))
        c.restore()
        c.restore()
        MI.draw_sub(c, t, groups, size=58, y=H * 0.9)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    v = MI.load_voice(VOIX)
    fx = [(0.6, E1.swish(0.4, 0.12), 1.0), (T_SHRUG, E1.pop_s(380, 0.1), 1.0)]
    MI.soundtrack(f"{tmp}/a.wav", v, dur, fx)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out, f"{dur:.1f} s", subs)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/marionnette_demo.mp4")
