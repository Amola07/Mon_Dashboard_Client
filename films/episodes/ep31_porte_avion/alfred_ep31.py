"""Épisode 31 dans le style @alfred.explique, en bleu, 100 % code (aucune planche) — démo de l'accroche.

0 → 1,1 s : le passager tire sur la poignée (alarme, jauge PRESSION). 1,1 s : la porte saute, la cabine se vide —
le cliché des films. Puis ◀◀ rembobinage VHS jusqu'au calme. « La réponse est non. » : image figée, NON.
« Il ne pourrait même pas l'ouvrir » : il tire, la porte ne bouge pas. « La raison va vous surprendre » : zoom.

    python -m films.episodes.ep31_porte_avion.alfred_ep31 output/ep31_alfred.mp4
"""
import math
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

from films import montage_ia as MI
from films.episodes.ep31_porte_avion import jeu_ep31 as G
from films.styles import mixage_pro as MP
from films.styles import oscillo_son as Z
from films.styles import pixel_bleu as P
from films.styles import son_jeu as J
from films.styles.pixel_bleu import B0, B1, B2, B3, B4, BLANC, GRIS, GRIS_F, NOIR, ROUGE, ROUGE_F

FPS = 30
T = G.T
SOL = 372
PORTE = (205, 280, 241, SOL)                                     # x0, y0, x1, y1
POIGNEE = (211, 313)
TB = 1.1                                                         # la porte saute
RNG = np.random.default_rng(31)
DEBRIS = [(RNG.uniform(20, 190), RNG.uniform(230, 360), RNG.uniform(0, 1.3), RNG.integers(0, 4), RNG.uniform(-1, 1))
          for _ in range(16)]


def lisse(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def cabine(d, s):
    """Le décor : plafond et coffres, hublots, plancher."""
    d.rectangle((10, 196, 200, 220), fill=B0)                    # les coffres à bagages
    d.rectangle((10, 196, 200, 198), fill=B2)
    for x in range(14, 200, 48):
        d.rectangle((x, 202, x + 42, 216), outline=B1)
        d.line([(x + 30, 209), (x + 38, 209)], fill=B2)
    for x in range(22, 190, 30):                                 # les hublots
        d.rounded_rectangle((x, 238, x + 12, 256), 5, fill=B1, outline=B2)
        d.line([(x + 3, 242), (x + 3, 250)], fill=B3)
    d.line([(10, 266), (200, 266)], fill=B1)
    P.sol(d, SOL)


def porte(d, s, tient=False, tremble=0.0):
    x0, y0, x1, y1 = PORTE
    d.rectangle((x0 - 3, y0 - 6, x1 + 3, y1), outline=GRIS_F, width=2)   # l'encadrement
    u = (s - TB) if not tient else -1
    if u > 0:                                                    # l'ouverture : le ciel, la lumière
        lum = max(0.0, 1 - u / 0.25)
        d.rectangle((x0, y0, x1, y1 - 1), fill=B4 if lum > 0.5 else B1)
        for k in range(6):
            yy = y0 + 8 + k * 14
            xx = x0 + ((k * 13 + s * 300) % (x1 - x0))
            d.line([(xx, yy), (xx + 8, yy)], fill=B3)
        if u > 1.4:
            return
        dx, dy = 240 * u ** 1.6, -60 * u + 120 * u * u              # la porte part en tournoyant
        ang = 300 * u
        img = Image.new("RGBA", (40, 100), (0, 0, 0, 0))
        from PIL import ImageDraw
        dd = ImageDraw.Draw(img)
        _dessin_porte(dd, 2, 4, 2 + x1 - x0, 4 + y1 - y0)
        img = img.rotate(-ang, expand=True, resample=Image.NEAREST)
        d._image.paste(img, (int(x0 + dx - 10), int(y0 + dy - 10)), img)
        return
    _dessin_porte(d, x0 + tremble, y0, x1 + tremble, y1)


def _dessin_porte(d, x0, y0, x1, y1):
    d.rounded_rectangle((x0, y0, x1, y1 - 1), 8, fill=B3)
    d.rounded_rectangle((x0 + 3, y0 + 2, x1 - 1, y1 - 1), 7, fill=B4)
    d.rectangle((x0, y1 - 8, x1, y1 - 1), fill=B1)
    cx = (x0 + x1) / 2 + 3
    d.ellipse((cx - 6, y0 + 8, cx + 6, y0 + 22), fill=B1, outline=B2)
    d.point((cx - 2, y0 + 12), fill=B3)
    d.rectangle((x0 + 4, y0 + 31, x0 + 18, y0 + 35), fill=GRIS)  # la poignée-levier, à hauteur de poitrine
    d.rectangle((x0 + 4, y0 + 31, x0 + 18, y0 + 32), fill=BLANC)
    d.rectangle((x0 + 15, y0 + 27, x0 + 19, y0 + 38), fill=GRIS_F)


def tirer(t, fort=1.0):
    p = 0.5 + 0.5 * math.sin(2 * math.pi * 1.7 * t)
    return -(28 + 12 * p * fort), 0.4 + 0.35 * p * fort


def vol(d, depart, t0, s, taille, delai=0.65, tenue="pull"):
    """Un passager aspiré vers la porte : il part de `depart`, tourne, file dehors."""
    u = (s - t0) / delai
    if u < 0:
        return False
    if u > 1.3:
        return True
    cx, cy = (PORTE[0] + PORTE[2]) / 2, (PORTE[1] + PORTE[3]) / 2
    x = depart[0] + (cx + 120 * max(0, u - 0.8) - depart[0]) * u ** 1.7
    y = depart[1] + (cy + 30 - depart[1]) * u
    P.personnage(d._image, (x, y), taille, tronc=10, flexion=0.5, rotation=70 + 220 * u, tenue=tenue)
    return True


def scene(img, d, s, t, mode="chaos"):
    """L'histoire à l'instant s (s recule pendant le rembobinage). mode : chaos (le cliché) ou tient (la réalité)."""
    cabine(d, s)
    tient = mode == "tient"
    rouge = (not tient) and s > TB and int(t * 6) % 2 == 0
    if rouge:                                                    # l'alarme rouge
        d.rectangle((96, 182, 116, 188), fill=ROUGE)
    sieges = [(48, 0.30, "gris"), (92, 0.62, "clair"), (136, 0.95, "costume")]
    for x, delai, tenue in sieges:
        P.siege(d, x, SOL)
        if tient or s < TB + delai:
            lean = 0 if tient or s < TB else 25 * lisse((s - TB) / 0.4)
            P.personnage(img, (x + 4, SOL), 66, tronc=lean, assis=True, mains=(x + 16 + lean / 3, SOL - 20),
                         tete=lean * 1.5, tenue=tenue)
        else:
            vol(d, (x + 4, SOL - 20), TB + delai, s, 66, tenue=tenue)
    tremble = 1 if tient and int(t * 25) % 2 else 0
    porte(d, s, tient, tremble)
    if tient or s < TB + 0.12:                                   # le passager debout, mains sur la poignée
        tr, ge = tirer(t, 1.6 if tient else (1.0 if s < TB - 0.4 else 1.5))
        cible = (POIGNEE[0] + tremble, POIGNEE[1])
        px = min(P.pieds_pour_saisir(cible, SOL, 84, tr, ge), PORTE[0] - 12)   # jamais les pieds dans la porte
        P.personnage(img, (px, SOL), 84, tronc=tr, mains=cible, flexion=ge)
    else:
        vol(d, (170, SOL - 30), TB + 0.12, s, 84, 0.5)
    if not tient and s > TB:                                     # objets aspirés, masques, vent
        for x, y, dt, k, rot in DEBRIS:
            u = (s - TB - dt) / 0.7
            if 0 <= u <= 1.2:
                px = x + (PORTE[0] + 20 - x) * u ** 1.8
                py = y + (310 - y) * u
                col = [GRIS, BLANC, B1, B3][k]
                a = rot * 8 * u
                w, h = [(5, 8), (7, 5), (9, 7), (4, 4)][k]
                d.polygon([(px + w * math.cos(a) - h * math.sin(a), py + w * math.sin(a) + h * math.cos(a)),
                           (px - w * math.cos(a) - h * math.sin(a), py - w * math.sin(a) + h * math.cos(a)),
                           (px - w * math.cos(a) + h * math.sin(a), py - w * math.sin(a) - h * math.cos(a)),
                           (px + w * math.cos(a) + h * math.sin(a), py + w * math.sin(a) - h * math.cos(a))], fill=col)
        for k in range(14):                                      # les traînées de vent vers la porte
            ph = (s * 2.4 + k * 0.37) % 1
            y = 230 + (k * 37) % 130
            x = 15 + 190 * ph
            d.line([(x, y), (x + 14, y)], fill=B3 if k % 2 else B2)
        for x in range(30, 200, 34):                             # les masques à oxygène qui tombent
            u = lisse((s - TB - 0.15) / 0.3)
            if u > 0:
                yy = 222 + 26 * u
                sw = 6 * math.sin(s * 9 + x)
                d.line([(x, 222), (x + sw, yy)], fill=GRIS)
                d.rectangle((x + sw - 3, yy, x + sw + 3, yy + 4), fill=BLANC)
    return rouge


def histoire(t):
    """Le temps de l'histoire : il avance, puis recule (rembobinage), puis reste au calme."""
    tr0, tr1 = T["aspire"] + 0.35, T["aspire"] + 1.45
    if t < tr0:
        return t, False
    if t < tr1:
        u = (t - tr0) / (tr1 - tr0)
        return tr0 * (1 - u) ** 1.5, True
    return 0.0, False


def _draw(img):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    return d


def zoomer(img, z, cx, cy):
    """La caméra : recadre autour de (cx, cy) et agrandit au plus proche (les pixels grossissent, comme en jeu)."""
    w, h = P.LW / z, P.LH / z
    x0 = min(max(0, cx - w / 2), P.LW - w)
    y0 = min(max(0, cy - h / 2), P.LH - h)
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((P.LW, P.LH), Image.NEAREST)


def image(t):
    img, _ = P.toile()
    img = P.halo(img, 135, 300, 190, B0, 0.55)
    d = _draw(img)
    P.poussieres(d, t)
    tn = T["non"]
    rembobine = False
    s = 0.0
    if t < tn:
        s, rembobine = histoire(t)
        scene(img, d, s, t)
    else:
        scene(img, d, 0.0, t, "tient")
        if t >= T["ouvrir"] + 0.6:                               # la croix : impossible
            x0, y0, x1, y1 = PORTE
            for w_ in range(3):
                d.line([(x0 - 6 + w_, y0 + 20), (x1 + 6 + w_, y1 - 20)], fill=ROUGE, width=2)
                d.line([(x1 + 6 + w_, y0 + 20), (x0 - 6 + w_, y1 - 20)], fill=ROUGE, width=2)
    z, cx, cy = 1.35, 150, 278                                   # la caméra : le héros remplit l'écran
    if t >= T["surprendre"]:
        u = lisse((t - T["surprendre"]) / 0.9)
        z, cx, cy = 1.35 + 0.9 * u, 150 + 55 * u, 278 + 40 * u
    img = zoomer(img, z, cx, cy)
    dx = dy = 0
    for tc, amp in ((TB, 6), (tn, 4)):                           # la caméra encaisse
        if t >= tc:
            k = math.exp(-7 * (t - tc)) * math.sin(70 * (t - tc))
            dx += int(amp * k)
            dy += int(amp * 0.6 * k)
    if dx or dy:
        img = Image.fromarray(np.roll(np.roll(np.asarray(img), dx, 1), dy, 0))
    if t >= tn and t < T["ouvrir"]:                              # NON sur l'image figée, assombrie
        img = Image.fromarray((np.asarray(img).astype(np.float32) * 0.35).astype(np.uint8))
    d = _draw(img)
    if t < tn:                                                   # l'interface par-dessus la caméra
        pression = 0.9 if s < TB else max(0.0, 0.9 - (s - TB) * 2)
        P.jauge(d, t, pression, etiquette="PRESSION", valeur="0,55 BAR" if s < TB else "0 BAR", alerte=s > TB)
        if t < 2.6:
            f = P.police(16, pixel=False)
            d.text((10, 92), "PORTE", font=f, fill=BLANC)
            d.text((10, 110), "D'AVION", font=f, fill=BLANC)
    else:
        P.jauge(d, t, 0.9, etiquette="PRESSION", valeur="0,55 BAR", alerte=False)
        if t < T["ouvrir"]:
            f = P.police(64, pixel=False)
            k = int((t - tn) * 6) % 2 == 0 or t > tn + 0.6
            lg = d.textlength("NON", font=f)
            d.text(((P.LW - lg) / 2 + 3, 172 + 3), "NON", font=f, fill=ROUGE_F)
            d.text(((P.LW - lg) / 2, 172), "NON", font=f, fill=BLANC if k else ROUGE)
            P.cadre_texte(d, (10, 100), "II ARRET SUR IMAGE", 8, B4, B2)
        else:
            P.cadre_texte(d, (40, 110), "IL NE PEUT MEME PAS L'OUVRIR", 8, BLANC, ROUGE)
            if t >= T["surprendre"]:
                P.cadre_texte(d, (96, 130), "LA RAISON ?", 8, B4, B2)
    a = np.asarray(P.agrandir(img))
    if rembobine:
        a = P.vhs(a, t)
        from PIL import ImageDraw
        im = Image.fromarray(a)
        dd = ImageDraw.Draw(im)
        for k in range(2):                                       # ◀◀
            x = 900 + 46 * k
            dd.polygon([(x, 120), (x + 40, 96), (x + 40, 144)], fill=BLANC)
        a = np.asarray(im)
    if t < 0.12:
        a = (a.astype(np.float32) * (t / 0.12) + 255 * (1 - t / 0.12)).astype(np.uint8)
    return a


def sons():
    tr0 = T["aspire"] + 0.35
    ev = [(0.0, J.fichier("boum_cine", 0.5, 2.0), "accent", 0.0)]
    ev += [(0.1 + 0.45 * i, J.alerte(1, 0.05), "interface", 0.3) for i in range(int(tr0 / 0.45))]
    ev += [(TB, J.fichier("boum_cine", 0.6, 3.0), "accent", 0.4), (TB, J.fichier("glitch", 0.3), "effet", 0.4),
           (TB, J.fichier("impact", 0.3), "accent", 0.4), (TB + 0.05, Z.vent(tr0 - TB, 0.25, 200, 3000), "ambiance", 0.3),
           (TB + 0.1, J.fichier("souffle_sombre", 0.3), "ambiance", 0.2)]
    ev += [(TB + dt + 0.3, J.fichier("swoosh_court", 0.2), "effet", 0.5) for _, _, dt, _, _ in DEBRIS[::3]]
    ev += [(tr0, J.fichier("rembobine", 0.4, 1.2), "effet", 0.0), (tr0, J.fichier("glitch", 0.3), "effet", 0.0),
           (T["non"], J.fichier("erreur", 0.35), "effet", 0.0), (T["non"], J.fichier("impact", 0.35), "accent", 0.0),
           (T["ouvrir"] + 0.6, J.fichier("echec", 0.35), "effet", 0.3), (T["surprendre"], J.fichier("question", 0.3), "effet", 0.0)]
    ev += [(T["ouvrir"] + 0.3 * i, J.fichier("porte_ferme", 0.15, 0.3), "effet", 0.4) for i in range(4)]
    mus = Z.musique(T["onze"] + 1, [(0, "tension"), (TB, "pulsation"), (tr0, "silence"), (T["non"] + 0.3, "tension")])
    mus = mus.mean(1) if mus.ndim == 2 else mus
    ev.append((0.0, mus, "ambiance", 0.0))
    return ev


def rendre(sortie, t1=None):
    voix = G.preparer()
    t1 = t1 or T["onze"] - 0.05
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{P.W}x{P.H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    for f in range(int(t1 * FPS)):
        ff.stdin.write(np.ascontiguousarray(image(f / FPS)).tobytes())
    ff.stdin.close()
    ff.wait()
    MP.mixer(f"{tmp}/a.wav", voix[:int(t1 * MI.SR)], t1, sons())
    filt = MP.loudnorm(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-map", "0:v", "-map",
                    "1:a", "-c:v", "copy", "-af", filt, "-ar", "48000", "-c:a", "aac", "-b:a", "256k", "-shortest",
                    "-movflags", "+faststart", sortie], check=True)
    print("OK", sortie)


if __name__ == "__main__":
    rendre(sys.argv[1] if len(sys.argv) > 1 else "output/ep31_alfred.mp4")
