"""Test de dialogue « toon » en voiture : champ-contrechamp, bouches synchronisées, bandeau, sous-titres karaoké.

Voix de test locales : elle = Kokoro (siwis), lui = Piper (tom). À remplacer par ElevenLabs (deux voix).

    python -m films.dialogue.voiture output/dialogue_voiture.mp4
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
from films.dialogue import toon as T
from films.persos import levres as LV

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
SR = 48000
BANDEAU = "Quand elle choisit la musique"
FONT = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "fonts", "Montserrat-Bold.ttf"))
FSUB = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "fonts", "BebasNeue-Regular.ttf"))

# (qui parle, texte, expression de celui qui parle, expression de l'autre, pause après)
DIALOGUE = [
    ("lui", "Vas-y, mets ce que tu veux.", "content", "content", 0.35),
    ("elle", "C'est vrai ? Je peux mettre ma playlist ?", "content", "content", 0.35),
    ("lui", "Évidemment. Je suis très ouvert d'esprit.", "content", "moqueur", 1.6),     # la « musique » démarre
    ("lui", "C'est quoi, ça ?", "suspicieux", "content", 0.3),
    ("elle", "Ma playlist pour dormir. Douze heures de grillons.", "content", "blase", 0.35),
    ("lui", "Douze heures ?", "choque", "content", 0.35),
    ("elle", "T'as dit que t'étais ouvert d'esprit.", "moqueur", "blase", 0.35),
    ("lui", "Ouvert d'esprit. Pas insomniaque.", "blase", "agace", 0.9),
]


# ------------------------------------------------------------------------------------------------ voix
def _tts():
    import sherpa_onnx as so
    from films.episodes.ep14_chatouilles.voix import D
    k = so.OfflineTts(so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(kokoro=so.OfflineTtsKokoroModelConfig(
        model=f"{D}/model.onnx", voices=f"{D}/voices.bin", tokens=f"{D}/tokens.txt", data_dir=f"{D}/espeak-ng-data",
        lexicon=f"{D}/lexicon-us-en.txt", lang="fr"), num_threads=4)))
    pdir = D.replace("kokoro-multi-lang-v1_0", "vits-piper-fr_FR-tom-medium")
    p = so.OfflineTts(so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(vits=so.OfflineTtsVitsModelConfig(
        model=glob.glob(f"{pdir}/*.onnx")[0], tokens=f"{pdir}/tokens.txt", data_dir=f"{pdir}/espeak-ng-data"),
        num_threads=4)))
    return {"elle": (k, 30, 1.08), "lui": (p, 0, 1.0)}


def _rs(x, sr):
    n = int(len(x) * SR / sr)
    return np.interp(np.arange(n) * sr / SR, np.arange(len(x)), x)


def voix():
    tts = _tts()
    t = 0.5
    pistes = {"lui": [], "elle": []}
    lignes = []
    for qui, txt, *_rest in DIALOGUE:
        eng, sid, sp = tts[qui]
        a = eng.generate(txt.replace("…", ","), sid=sid, speed=sp)
        x = np.array(a.samples, np.float32)
        idx = np.where(np.abs(x) > 0.01)[0]
        x = _rs(x[max(0, idx[0] - 200): idx[-1] + int(0.12 * a.sample_rate)], a.sample_rate)
        x *= 10 ** (-17 / 20) / (np.sqrt((x[np.abs(x) > 0.01] ** 2).mean()) + 1e-9)
        lignes.append((qui, t, t + len(x) / SR))
        pistes[qui].append((t, x))
        t += len(x) / SR + _rest[-1]
    dur = t + 0.6
    n = int(dur * SR)
    out = {}
    for qui in pistes:
        y = np.zeros(n)
        for t0, x in pistes[qui]:
            i = int(t0 * SR)
            y[i:i + len(x)] += x[:n - i]
        path = os.path.join(HERE, f"voix_{qui}.wav")
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
        out[qui] = (path, y)
    return lignes, dur, out


def grillons(dur):
    tt = np.arange(int(dur * SR)) / SR
    env = (np.sin(2 * np.pi * 14 * tt) > 0.3) * (np.sin(2 * np.pi * 0.9 * tt) > -0.2)
    return np.sin(2 * np.pi * 4300 * tt) * env * 0.08 + np.sin(2 * np.pi * 4700 * tt) * env * 0.04


# ------------------------------------------------------------------------------------------------ image
def bandeau(c):
    f = skia.Font(FONT, 46)
    w = f.measureText(BANDEAU)
    r = skia.RRect.MakeRectXY(skia.Rect(W / 2 - w / 2 - 26, 150, W / 2 + w / 2 + 26, 226), 14, 14)
    c.drawRRect(r, T.P((255, 255, 255)))
    c.drawString(BANDEAU, W / 2 - w / 2, 204, f, T.P((10, 10, 12)))


def mots(lignes):
    out = []
    for (qui, a, b), (_, txt, *_r) in zip(lignes, DIALOGUE):
        ws = txt.upper().split()
        lens = [len(x) + 2 for x in ws]
        t = a
        for j, (w_, l) in enumerate(zip(ws, lens)):
            d = (b - a) * l / sum(lens)
            out.append((w_, t, t + d, len(out) - j, j))           # (mot, début, fin, 1er mot de la réplique, rang)
            t += d
    return out


def sous_titres(c, t, ws):
    # groupe de 3 mots autour du mot courant, mot courant sur fond rouge
    i = max([k for k, w in enumerate(ws) if w[1] <= t + 0.02] + [-1])
    if i < 0 or t > ws[i][2] + 0.6:
        return
    debut, rang = ws[i][3], ws[i][4]
    g0 = debut + (rang // 3) * 3
    grp = [w for w in ws[g0:g0 + 3] if w[3] == debut]
    f = skia.Font(FSUB, 92)
    sp = f.measureText(" ")
    tot = sum(f.measureText(w[0]) for w in grp) + sp * (len(grp) - 1)
    x = W / 2 - tot / 2
    y = 1560
    for k, (w_, a, b, _, _) in enumerate(grp):
        wd = f.measureText(w_)
        if g0 + k == i:
            r = skia.RRect.MakeRectXY(skia.Rect(x - 10, y - 78, x + wd + 10, y + 14), 12, 12)
            c.drawRRect(r, T.P((230, 30, 60)))
        c.drawString(w_, x, y, f, T.P(T.INK, 12))
        c.drawString(w_, x, y, f, T.P((255, 255, 255)))
        x += wd + sp


def plan(t, lignes):
    """Plan courant : large au début, puis gros plan sur celui qui parle (ou réaction de l'autre)."""
    if t < lignes[0][1] + 0.1:
        return "large", None
    cur = None
    for k, (qui, a, b) in enumerate(lignes):
        if t >= a - 0.08:
            cur = (k, qui, a, b)
    k, qui, a, b = cur
    # pendant la longue pause « musique » et après la chute : réaction de l'autre
    autre = "elle" if qui == "lui" else "lui"
    if t > b + 0.25 and DIALOGUE[k][4] > 0.8:
        return autre, cur
    return qui, cur


def expr_de(qui, t, lignes):
    e = "neutre"
    for (q, a, b), (_, _, es, eo, _) in zip(lignes, DIALOGUE):
        if t >= a - 0.08:
            e = es if q == qui else eo
    return e


def frame(c, t, lignes, sync, ws, t_plan):
    sh, cur = plan(t, lignes)
    if sh == "large":
        c.drawRect(skia.Rect(0, 0, W, H), T.P((110, 106, 112)))
        T.ville(c, 60, 300, W - 60, 900, t)
        c.drawRect(skia.Rect(60, 300, W - 60, 900), T.P(T.INK, 12))
        for x, q in ((290, "lui"), (790, "elle")):
            T.siege(c, x, 1150, 0.55)
            c.save()
            c.translate(x, 1100)
            c.scale(0.5, 0.5)
            T.tete(c, q, expr_de(q, t, lignes), "fermee", t=t)
            c.restore()
        c.drawRect(skia.Rect(0, 1500, W, H), T.P((70, 68, 74)))          # tableau de bord
        c.drawLine(0, 1500, W, 1500, T.P(T.INK, 12))
    else:
        age = t - t_plan.get(sh, 0)
        z = 1.0 + 0.04 * min(1.0, age / 3)                              # lente poussée de caméra
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        T.interieur(c, W, H, t, 1 if sh == "lui" else -1)
        T.siege(c, 540, 980)
        c.save()
        c.translate(540, 900 + 6 * math.sin(t * 2.2))
        c.scale(1.12, 1.12)
        e = expr_de(sh, t, lignes)
        bouche = "fermee"
        parle = cur is not None and cur[1] == sh and cur[2] - 0.05 <= t <= cur[3] + 0.05
        if parle:
            w_, h_, _, _ = sync[sh](t)
            if h_ > 40:
                bouche = "ouverte"
            elif h_ > 14:
                bouche = "mi" if w_ > 40 else "o"
        cl = ((t + (0.7 if sh == "elle" else 0)) % 3.3) < 0.1
        c.rotate(1.5 * math.sin(t * 1.3) + (2.0 * math.sin(t * 9) if parle else 0))
        T.tete(c, sh, e, bouche, cl, t)
        c.restore()
        c.restore()
    bandeau(c)
    sous_titres(c, t, ws)


def render(out):
    lignes, dur, pistes = voix()
    sync = {q: LV.Synchro(p[0]) for q, p in pistes.items()}
    ws = mots(lignes)
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    t_plan, last = {}, None
    for f in range(int(dur * FPS)):
        t = f / FPS
        sh, _ = plan(t, lignes)
        if sh != last:
            t_plan[sh] = t
            last = sh
        frame(surf.getCanvas(), t, lignes, sync, ws, t_plan)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    voixmix = pistes["lui"][1] + pistes["elle"][1]
    t_mus = lignes[2][2] + 0.2
    g = grillons(dur - t_mus)
    voixmix[int(t_mus * SR): int(t_mus * SR) + len(g)] += g[:len(voixmix) - int(t_mus * SR)]
    MI.soundtrack(f"{tmp}/a.wav", voixmix, dur)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out, f"{dur:.1f} s")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/dialogue_voiture.mp4")
