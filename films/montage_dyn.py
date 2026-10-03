"""Montage dynamique (« retention editing ») des clips générés : rythme de coupe, recadrages, zooms, flashs,
sous-titres karaoké, étalonnage et bruitages.

Entrées identiques à montage_ia : SEG [(texte, début, fin)], SHOTS [(plan, t0, t1, départ, vitesse)] en temps voix,
plus des repères : MOTS (mots ou débuts de mots à frapper), PARTIES (instants de changement de partie).

  • chaque plan est redécoupé en sous-plans d'environ 1,5–2,2 s, calés sur les groupes de mots, avec un cadrage
    différent à chaque fois (large / serré / très serré, point de vue décalé) et une poussée de caméra continue ;
  • « punch » de zoom + petite secousse sur les mots frappés (chiffres, mots clés) ;
  • flash blanc + zoom d'entrée aux changements de partie ;
  • sous-titres de 1 à 3 mots, très gros, contour noir, mot prononcé en jaune avec un léger rebond ;
  • étalonnage commun (contraste, saturation, vignettage, grain) ;
  • whoosh discret à chaque coupe, impact aux changements de partie, nappe musicale sous la voix.
"""
import os
import re
import subprocess
import tempfile

import cv2
import numpy as np
import skia

from films import hook as HK
from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1

W, H, FPS = 1080, 1920, 30
F = MI.F_SUB
YELLOW = skia.Color(255, 214, 10)


# ------------------------------------------------------------------------------------------------ mots
def mots(seg):
    """Chaque mot avec son début et sa fin (répartis au prorata du nombre de lettres dans la phrase)."""
    out = []
    for txt, a, b in seg:
        ws = txt.split()
        lens = [len(re.sub(r"\W", "", w)) + 1.5 for w in ws]
        t = a
        for w, l in zip(ws, lens):
            d = (b - a) * l / sum(lens)
            out.append((w, t, t + d))
            t += d
    return out


def groupes(ws, max_mots=3, max_car=16):
    """Groupes de 1 à 3 mots pour l'affichage (on ne coupe pas entre deux phrases)."""
    out, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        txt = " ".join(x[0] for x in cur)
        fin_phrase = i + 1 == len(ws) or ws[i + 1][1] - w[2] > 0.15
        if len(cur) >= max_mots or len(txt) >= max_car or fin_phrase or w[0][-1] in ",.:;!?…":
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------------------------------------ cadrage
CADRES = [(1.00, 0.50, 0.46), (1.22, 0.50, 0.40), (1.10, 0.42, 0.50), (1.32, 0.56, 0.42), (1.12, 0.58, 0.48)]


def sous_plans(shots, grp, tmap):
    """Découpe chaque plan en sous-plans de ~1,5–2,2 s, aux frontières des groupes de mots."""
    bornes = sorted({tmap(g[0][1]) for g in grp})
    out = []
    k = 0
    for plan, t0, t1, st, sp in shots:
        cuts = [t0]
        for b in bornes:
            if b - cuts[-1] >= 1.5 and t1 - b >= 1.2:
                cuts.append(b)
        cuts.append(t1)
        for a, b in zip(cuts[:-1], cuts[1:]):
            out.append((plan, a, b, st + (a - t0) * sp, sp, CADRES[k % len(CADRES)], k))
            k += 1
    return out


class Lecteur:
    """Lit les images d'un plan à la demande (flux ffmpeg), mis à l'échelle 1080×1920."""

    def __init__(self, src, start, speed, scale_vf):
        self.p = None
        self.last = np.zeros((H, W, 3), np.uint8)
        if os.path.exists(src):
            vf = f"setpts=(PTS-STARTPTS)/{speed},{scale_vf},fps={FPS}"
            self.p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{start}", "-i", src, "-an",
                                       "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)

    def lire(self):
        if self.p is not None:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) == W * H * 3:
                self.last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        return self.last

    def fermer(self):
        if self.p is not None:
            self.p.stdout.close()
            self.p.wait()


def zoom(img, z, fx, fy, dx=0.0, dy=0.0):
    """Agrandit de z autour du point (fx, fy) (fractions de l'image), avec décalage en pixels."""
    cx, cy = fx * W, fy * H
    # on garde l'image remplie : le centre est contraint pour ne pas montrer les bords
    half_w, half_h = W / (2 * z), H / (2 * z)
    cx = min(max(cx, half_w), W - half_w)
    cy = min(max(cy, half_h), H - half_h)
    M = np.float32([[z, 0, W / 2 - z * cx + dx], [0, z, H / 2 - z * cy + dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


_VIG = None
_RNG = np.random.default_rng(5)


def etalonnage(img):
    global _VIG
    if _VIG is None:
        y, x = np.mgrid[0:H, 0:W]
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        _VIG = (1 - 0.28 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None].astype(np.float32)
    f = img.astype(np.float32)
    g = f.mean(2, keepdims=True)
    f = g + (f - g) * 1.12                                             # saturation
    f = (f - 128) * 1.07 + 128                                         # contraste
    f *= _VIG
    f += _RNG.normal(0, 3.0, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)   # grain
    return np.clip(f, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------------------------------------ sous-titres
def sous_titres(c, t, grp, tmap, frappes):
    cur = None
    for k, g in enumerate(grp):
        a, b = tmap(g[0][1]), tmap(g[-1][2])
        nxt = tmap(grp[k + 1][0][1]) if k + 1 < len(grp) else b + 0.5
        if a - 0.04 <= t < min(nxt, b + 0.45):
            cur = (g, a)
    if cur is None:
        return
    g, a = cur
    size = 88
    f = skia.Font(F, size)
    txt = " ".join(w[0] for w in g)
    while f.measureText(txt) > W - 110 and size > 50:
        size -= 4
        f = skia.Font(F, size)
    space = f.measureText(" ")
    widths = [f.measureText(w[0]) for w in g]
    total = sum(widths) + space * (len(g) - 1)
    age = t - a
    pop = 1 + 0.18 * np.exp(-age * 14) * np.cos(age * 30) if age < 0.4 else 1.0
    y = H * 0.66
    c.save()
    c.translate(W / 2, y)
    c.scale(pop, pop)
    x = -total / 2
    stroke = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0), Style=skia.Paint.kStroke_Style,
                        StrokeWidth=size * 0.16, StrokeJoin=skia.Paint.kRound_Join)
    shadow = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 150),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
    for (w, wa, wb), wd in zip(g, widths):
        on = tmap(wa) - 0.03 <= t
        frappe = any(abs(tmap(wa) - tf) < 0.05 for tf in frappes)
        col = YELLOW if (on and (frappe or re.search(r"\d", w))) else (skia.Color(255, 255, 255) if on else
                                                                     skia.Color(255, 255, 255, 235))
        sc = 1.0
        if on and tmap(wa) <= t < tmap(wb) + 0.05:
            col = YELLOW
            sc = 1.06
        c.save()
        c.translate(x + wd / 2, 0)
        c.scale(sc, sc)
        c.drawString(w, -wd / 2, 8, f, shadow)
        c.drawString(w, -wd / 2, 0, f, stroke)
        c.drawString(w, -wd / 2, 0, f, skia.Paint(AntiAlias=True, Color=col))
        c.restore()
        x += wd + space
    c.restore()


# ------------------------------------------------------------------------------------------------ rendu
def render(out_path, voix, clips, seg, shots, frappes_mots=(), parties=(), scale_vf=None, tighten_voice=True,
           fx_extra=()):
    voice = MI.load_voice(voix)
    if tighten_voice:
        voice, tmap, _ = MI.tighten(voice)
    else:
        tmap = lambda t: t
    dur = len(voice) / MI.SR + 0.5
    scale_vf = scale_vf or MI.CROP
    ws = mots(seg)
    grp = groupes(ws)
    # mots frappés : chiffres + mots listés
    cles = [s.lower() for s in frappes_mots]
    frappes = [tmap(a) for w, a, b in ws
               if re.search(r"\d", w) or re.sub(r"\W", "", w).lower() in cles or (w.isupper() and len(w) > 2)]
    parties = [tmap(p) for p in parties]
    edges = [tmap(s[1]) for s in shots] + [dur]
    shots2 = [(p, edges[i], edges[i + 1], st, sp) for i, (p, _, _, st, sp) in enumerate(shots)]
    subs = sous_plans(shots2, grp, tmap)
    tmp = tempfile.mkdtemp()
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                            "-pix_fmt", "yuv420p", f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    nframes = int(dur * FPS)
    si, lect = -1, None
    for fi in range(nframes):
        t = fi / FPS
        while si + 1 < len(subs) and t >= subs[si + 1][1]:
            si += 1
            if lect:
                lect.fermer()
            plan, a, b, st, sp, cad, k = subs[si]
            lect = Lecteur(os.path.join(clips, f"{plan}.mp4"), st, sp, scale_vf)
        img = lect.lire()
        plan, a, b, st, sp, (z0, fx, fy), k = subs[si]
        u = (t - a) / max(0.1, b - a)
        z = z0 * (1 + 0.045 * u)                                          # poussée continue
        fx += (0.02 if k % 2 else -0.02) * u                              # légère dérive
        # punch sur les mots frappés + secousse
        for tf in frappes:
            d = t - tf
            if 0 <= d < 0.35:
                z *= 1 + 0.10 * np.exp(-d * 9)
        dx = dy = 0.0
        for tp in parties:
            d = t - tp
            if 0 <= d < 0.35:
                z *= 1 + 0.25 * (1 - d / 0.35) ** 2                       # zoom d'entrée
            if 0 <= d < 0.3:
                dx += 14 * np.sin(d * 90) * (1 - d / 0.3)
                dy += 10 * np.cos(d * 70) * (1 - d / 0.3)
        frame = etalonnage(zoom(img, z, fx, fy, dx, dy))
        rgba = np.dstack([frame, np.full((H, W), 255, np.uint8)])
        c = surf.getCanvas()
        c.drawImage(skia.Image.fromarray(rgba, colorType=skia.kBGRA_8888_ColorType), 0, 0)
        for tp in parties:                                                 # flash blanc
            d = t - tp
            if 0 <= d < 0.22:
                c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(255, 255, 255,
                                                                               int(200 * (1 - d / 0.22)))))
        sous_titres(c, t, grp, tmap, frappes)
        enc.stdin.write(surf.makeImageSnapshot().tobytes())
    if lect:
        lect.fermer()
    enc.stdin.close()
    enc.wait()
    # son : whoosh à chaque coupe, impact aux parties, nappe sous la voix
    fx = [(s[1] - 0.12, E1.swish(0.35, 0.05), 1.0) for s in subs[1:]]
    fx += [(tp, HK.sub_drop(0.35), 1.0) for tp in parties]
    fx += [(tmap(t0), snd, g) for t0, snd, g in fx_extra]
    MI.soundtrack(f"{tmp}/a.wav", voice, dur, fx)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav",
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)
    print(f"OK {out_path} : {dur:.1f} s, {len(subs)} sous-plans")
