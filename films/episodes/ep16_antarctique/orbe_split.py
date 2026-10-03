"""Épisode 16 — « L'air de l'Antarctique », format écran partagé : vraies images en haut (changement toutes les
2 à 3 s, léger mouvement de caméra), l'Orbe fixe en bas sur fond noir (bouche synchronisée, il ne bâille jamais),
accroche en lettres géantes au début et petits sous-titres karaoké entre les deux.

Les images (NASA, Wikimedia Commons) ne sont pas versionnées : voir images/CREDITS.md et images/telecharger.py.

    python -m films.episodes.ep16_antarctique.orbe_split output/ep16_antarctique.mp4
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
from PIL import Image

from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1
from films.persos import levres as LV
from films.persos.orbe import Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
PH = 1060                                                          # hauteur du panneau d'images
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
VOIX = os.path.join(HERE, "audio", "voix.mp3")
VOIX2 = os.path.join(HERE, "audio", "voix_serree.wav")
FONT = skia.Typeface.MakeFromFile(os.path.join(HERE, "..", "..", "fonts", "Montserrat-ExtraBold.ttf"))
T_HOOK = 5.7

# phrases (temps de la voix d'origine, minutage ASR ; texte = ce que dit vraiment la voix)
SEG = [
    (0.00, 1.30, "Si tu casses ce glaçon,"),
    (1.68, 5.69, "tu respirerais un air que personne n'a respiré depuis 2 millions d'années."),
    (6.60, 7.16, "Vu d'en haut,"), (7.58, 10.15, "l'Antarctique n'est qu'une immense tache blanche."),
    (10.52, 11.17, "En réalité,"), (11.58, 13.77, "c'est la plus grande archive de la planète."),
    (14.48, 15.16, "Chaque année,"), (15.51, 16.61, "la neige s'entasse."),
    (17.05, 18.14, "Sous son propre poids,"), (18.38, 19.59, "elle devient de la glace…"),
    (20.05, 22.24, "et enferme de minuscules bulles d'air."), (22.83, 24.24, "Couche après couche."),
    (24.79, 27.92, "Les scientifiques forent à plus de 3 km de profondeur."),
    (28.35, 30.61, "Ils remontent de longs cylindres de glace :"), (31.09, 31.88, "des carottes."),
    (32.40, 33.17, "À l'intérieur,"), (33.53, 34.88, "l'atmosphère de la Terre,"),
    (35.32, 36.84, "bien avant les premiers humains."), (37.61, 38.33, "Mais le plus fou,"),
    (38.71, 41.00, "c'est que l'Antarctique n'a pas toujours été gelé."),
    (41.38, 42.97, "Il y a 90 millions d'années,"), (43.36, 44.36, "il y poussait des forêts."),
    (44.86, 46.06, "Des dinosaures y vivaient."), (46.69, 48.13, "Alors pourquoi tout a gelé ?"),
    (49.11, 51.45, "L'Amérique du Sud et l'Australie se sont éloignées."),
    (51.75, 54.96, "Un courant marin géant s'est formé tout autour du continent…"),
    (55.34, 56.55, "et l'a coupé des eaux chaudes."), (57.17, 58.80, "Il y a 34 millions d'années,"),
    (59.19, 61.00, "la glace a tout recouvert."), (61.73, 62.50, "Et ce n'est pas tout."),
    (62.73, 63.59, "Sur cette glace,"), (63.83, 65.75, "la moindre pierre noire se voit de loin."),
    (66.13, 69.49, "C'est le meilleur endroit au monde pour trouver des météorites."), (70.44, 71.82, "En 1984,"),
    (72.16, 74.65, "une chercheuse ramasse un caillou de 2 kilos."), (75.13, 76.17, "Il vient de Mars."),
    (76.76, 78.13, "En 1996,"), (78.49, 82.26, "on y découvre des formes minuscules qui ressemblent à des bactéries fossiles."),
    (82.77, 87.57, "Le président Bill Clinton annonce à la télévision une possible trace de vie sur Mars."),
    (88.24, 89.09, "Aujourd'hui encore,"), (89.44, 91.33, "le doute n'a jamais été totalement levé."),
    (91.86, 93.28, "Ce désert blanc n'est pas vide."), (93.70, 95.48, "C'est la mémoire de la Terre."),
]

# plans : (début en temps d'origine, image(s) par ordre de préférence, point de mire (0..1), zoom début → fin)
PLANS = [
    (0.00, ["05_bulles2"], (0.66, 0.32), (1.45, 1.25)),
    (2.90, ["05_bulles2"], (0.62, 0.36), (2.2, 2.6)),
    (6.60, ["02_antarctique"], (0.5, 0.5), (1.0, 1.12)),
    (8.80, ["nasa_GSFC_20171208_Archive_e001267"], (0.5, 0.5), (1.0, 1.1)),
    (10.52, ["09_stock"], (0.5, 0.5), (1.0, 1.12)),
    (14.48, ["nasa_GSFC_20171208_Archive_e000911"], (0.55, 0.45), (1.0, 1.1)),
    (17.05, ["13_glace"], (0.5, 0.6), (1.0, 1.12)),
    (20.05, ["05_bulles2"], (0.62, 0.36), (1.6, 1.3)),
    (22.83, ["01_bulles"], (0.4, 0.55), (1.1, 1.3)),
    (24.79, ["06_forage"], (0.5, 0.5), (1.0, 1.12)),
    (28.35, ["07_camp"], (0.5, 0.45), (1.0, 1.15)),
    (31.09, ["07_camp"], (0.6, 0.3), (1.6, 1.4)),
    (32.40, ["09_stock"], (0.5, 0.45), (1.3, 1.1)),
    (35.32, ["04_lame"], (0.5, 0.5), (1.0, 1.15)),
    (37.61, ["nasa_PIA14557"], (0.5, 0.5), (1.0, 1.12)),
    (41.38, ["10b_foret"], (0.5, 0.5), (1.0, 1.12)),
    (43.36, ["10_foret"], (0.5, 0.5), (1.12, 1.0)),
    (44.86, ["11_dino"], (0.45, 0.45), (1.0, 1.15)),
    (46.69, ["nasa_GSFC_20171208_Archive_e001867"], (0.5, 0.5), (1.0, 1.1)),
    (49.11, ["12_courant"], (0.5, 0.48), (1.0, 1.08)),
    (51.75, ["12_courant"], (0.5, 0.5), (1.5, 1.3)),
    (55.34, ["nasa_GSFC_20171208_Archive_e000910"], (0.5, 0.5), (1.0, 1.1)),
    (57.17, ["13_glace"], (0.5, 0.5), (1.15, 1.0)),
    (59.19, ["02_antarctique"], (0.5, 0.5), (1.3, 1.05)),
    (61.73, ["nasa_GSFC_20171208_Archive_e000911"], (0.5, 0.5), (1.15, 1.0)),
    (63.83, ["15_meteorite"], (0.5, 0.5), (1.0, 1.12)),
    (66.13, ["15_meteorite"], (0.38, 0.65), (1.8, 1.5)),
    (70.44, ["nasa_S85-39565"], (0.5, 0.5), (1.0, 1.1)),
    (72.16, ["nasa_ARC-1996-AC96-0345-1"], (0.5, 0.5), (1.0, 1.12)),
    (75.13, ["nasa_PIA00407"], (0.5, 0.5), (1.0, 1.12)),
    (76.76, ["nasa_PIA00288"], (0.5, 0.5), (1.0, 1.12)),
    (78.49, ["nasa_ARC-1996-AC96-0345-11"], (0.5, 0.48), (2.4, 2.1)),
    (80.40, ["nasa_PIA00290"], (0.5, 0.5), (1.0, 1.12)),
    (82.77, ["16_clinton"], (0.4, 0.5), (1.0, 1.1)),
    (85.40, ["16b_clinton"], (0.55, 0.4), (1.0, 1.12)),
    (88.24, ["nasa_PIA00283"], (0.5, 0.5), (1.0, 1.12)),
    (91.86, ["14_glacebleue", "nasa_GSFC_20171208_Archive_e000910"], (0.5, 0.6), (1.12, 1.0)),
    (93.70, ["02_antarctique"], (0.5, 0.5), (1.0, 1.15)),
]

# humeurs de l'Orbe (temps d'origine) : (yeux, palette)
MOODS = [(0.0, "surpris", "surprise"), (6.6, "parle", "calme"), (24.79, "parle", "reflexion"),
         (37.61, "surpris", "surprise"), (41.38, "parle", "joie"), (46.69, "parle", "reflexion"),
         (61.73, "surpris", "surprise"), (66.13, "parle", "idee"), (75.13, "surpris", "surprise"),
         (76.76, "parle", "calme"), (82.77, "parle", "idee"), (88.24, "parle", "reflexion"),
         (91.86, "parle", "calme")]


# ------------------------------------------------------------------------------------------------ voix
def construire_voix():
    """Silences ramenés à 0,40 s au plus. Renvoie (durée, temps d'origine → temps nouveau)."""
    v, f, _ = MI.tighten(MI.load_voice(VOIX), max_gap=0.40, thr_db=-38.0)
    with wave.open(VOIX2, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(MI.SR)
        w.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes())
    return len(v) / MI.SR, f


# ------------------------------------------------------------------------------------------------ images
def trouver(noms):
    for n in noms:
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            p = os.path.join(IMG, n + ext)
            if os.path.exists(p):
                return p
    print("image absente :", noms[0], "→ remplacée", file=sys.stderr)
    return trouver(["nasa_GSFC_20171208_Archive_e000911"])


_CACHE = {}


def charger(path, zmax):
    """Image redimensionnée pour couvrir le panneau au zoom maximal (skia.Image)."""
    if path not in _CACHE:
        im = Image.open(path).convert("RGB")
        s = max(W / im.width, PH / im.height) * zmax
        im = im.resize((max(W, int(im.width * s)), max(PH, int(im.height * s))), Image.LANCZOS)
        a = np.array(im.convert("RGBA"))
        _CACHE[path] = skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType)
    return _CACHE[path]


def panneau(c, plans, t):
    k = max(i for i, p in enumerate(plans) if p[0] <= t)
    t0, path, (fx, fy), (z0, z1) = plans[k]
    t1 = plans[k + 1][0] if k + 1 < len(plans) else t0 + 3
    u = min(1.0, (t - t0) / max(0.1, t1 - t0))
    u = u * u * (3 - 2 * u) * 0.6 + u * 0.4
    zm = max(z0, z1)
    img = charger(path, zm)
    base = max(W / img.width(), PH / img.height())                 # échelle « couvrir » de l'image chargée
    z = z0 + (z1 - z0) * u
    z *= 1 + 0.035 * math.exp(-(t - t0) * 9)                         # petit coup de zoom à la coupe
    s = base * z
    cx, cy = fx * img.width(), fy * img.height()
    # on garde le panneau couvert
    hw, hh = W / 2 / s, PH / 2 / s
    cx = min(max(cx, hw), img.width() - hw)
    cy = min(max(cy, hh), img.height() - hh)
    c.save()
    c.clipRect(skia.Rect(0, 0, W, PH))
    c.translate(W / 2, PH / 2)
    c.scale(s, s)
    c.translate(-cx, -cy)
    c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    c.restore()
    # fondu vers le noir en bas du panneau
    g = skia.GradientShader.MakeLinear([skia.Point(0, PH - 170), skia.Point(0, PH)],
                                       [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 255)])
    c.drawRect(skia.Rect(0, PH - 170, W, PH), skia.Paint(Shader=g))
    return k


# ------------------------------------------------------------------------------------------------ texte
def texte(c, lignes, y0, k, taille, cols):
    f = skia.Font(FONT, taille)
    s = E1.pop(k) if k < 0.5 else 1.0
    c.save()
    c.translate(W / 2, y0)
    c.scale(s, s)
    for i, (ln, col) in enumerate(zip(lignes, cols)):
        ff = f
        w = ff.measureText(ln)
        while w > W - 80:
            ff = skia.Font(FONT, ff.getSize() - 6)
            w = ff.measureText(ln)
        y = i * taille * 1.05
        c.drawString(ln, -w / 2, y, ff, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0),
                                                    Style=skia.Paint.kStroke_Style, StrokeWidth=24,
                                                    StrokeJoin=skia.Paint.kRound_Join))
        c.drawString(ln, -w / 2, y, ff, skia.Paint(AntiAlias=True, Color=skia.Color(*col)))
    c.restore()


def accroche(c, t, t_hook):
    a = 1 - min(1, max(0, (t - t_hook) / 0.25))
    if a <= 0:
        return
    c.saveLayerAlpha(None, int(255 * a))
    texte(c, ["CET AIR A"], 330, t / 0.3, 120, [(255, 255, 255)])
    texte(c, ["2 MILLIONS", "D'ANNÉES"], 470, (t - 0.25) / 0.3, 150, [(120, 220, 255), (120, 220, 255)])
    c.restore()


MOTS = []


def preparer_mots(segs):
    MOTS.clear()
    for a, b, txt in segs:
        ws = txt.split()
        lens = [len(re.sub(r"\W", "", w)) + 1.5 for w in ws]
        t = a
        for j, (w, l) in enumerate(zip(ws, lens)):
            d = (b - a) * l / sum(lens)
            MOTS.append((w.upper(), t, t + d, len(MOTS) - j, j))
            t += d


def sous_titres(c, t):
    i = max([k for k, m in enumerate(MOTS) if m[1] <= t + 0.03] + [-1])
    if i < 0 or t > MOTS[i][2] + 0.4:
        return
    deb, rang = MOTS[i][3], MOTS[i][4]
    g0 = deb + (rang // 3) * 3
    grp = [m for m in MOTS[g0:g0 + 3] if m[3] == deb]
    size = 66
    f = skia.Font(FONT, size)
    sp = f.measureText(" ")
    tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    while tot > W - 100:
        size -= 4
        f = skia.Font(FONT, size)
        sp = f.measureText(" ")
        tot = sum(f.measureText(m[0]) for m in grp) + sp * (len(grp) - 1)
    age = t - MOTS[g0][1]
    pop = 1 + 0.12 * math.exp(-age * 12) * math.cos(age * 28) if age < 0.4 else 1.0
    c.save()
    c.translate(W / 2, 1150)
    c.scale(pop, pop)
    x = -tot / 2
    for k, m in enumerate(grp):
        wd = f.measureText(m[0])
        on = g0 + k == i
        c.drawString(m[0], x, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0),
                                               Style=skia.Paint.kStroke_Style, StrokeWidth=12,
                                               StrokeJoin=skia.Paint.kRound_Join))
        c.drawString(m[0], x, 0, f, skia.Paint(AntiAlias=True, Color=skia.Color(255, 214, 10) if on else
                                               skia.Color(255, 255, 255)))
        x += wd + sp
    c.restore()


# ------------------------------------------------------------------------------------------------ Orbe
def orbe(c, t, sync, moods):
    k = max(i for i, m in enumerate(moods) if m[0] <= t)
    tc, yeux, hum = moods[k]
    hum0 = moods[k - 1][2] if k else hum
    e = Etat(expr="parle", age=t - tc, levres=sync(t), yeux=yeux, humeur=hum, humeur_avant=hum0,
             humeur_mix=min(1.0, (t - tc) / 0.5))
    e.cligne = (t % 3.7) < 0.11
    e.regard = (0.0, -0.55)                                         # il regarde les images au-dessus
    c.save()
    c.translate(540, 1560)
    c.scale(2.1, 2.1)
    draw_orbe(c, t, e)
    c.restore()


# ------------------------------------------------------------------------------------------------ rendu
def render(out):
    dur_v, N = construire_voix()
    dur = dur_v + 0.6
    sync = LV.Synchro(VOIX2)
    preparer_mots([(N(a), N(b), txt) for a, b, txt in SEG])
    plans = [(N(t0), trouver(noms), fp, zz) for t0, noms, fp, zz in PLANS]
    moods = [(N(t0), y, h) for t0, y, h in MOODS]
    t_hook = N(T_HOOK)
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    coupes = []
    last = -1
    for f in range(int(dur * FPS)):
        t = f / FPS
        c = surf.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        k = panneau(c, plans, t)
        if k != last:
            coupes.append(plans[k][0])
            last = k
        accroche(c, t, t_hook)
        if t >= t_hook - 0.1:
            sous_titres(c, t)
        orbe(c, t, sync, moods)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    fx = [(0.0, E1.swell(0.12), 1.0)] + [(tc, E1.pop_s(520, 0.05), 1.0) for tc in coupes[1:]]
    MI.soundtrack(f"{tmp}/a.wav", MI.load_voice(VOIX2), dur, fx)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out, f"{dur:.1f} s")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/ep16_antarctique.mp4")
