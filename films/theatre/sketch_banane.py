"""Sketch muet n° 1 : « La peau de banane ».

Sam (mèche) évite une peau de banane avec panache… Léo (casquette) jette la sienne sans regarder, Sam glisse dessus,
Léo se moque… et reçoit une banane sur la tête. Ba-dum-tss, rideau.

    python -m films.theatre.sketch_banane output/sketch_banane.mp4
"""
import math
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import hook as HK
from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1
from films.theatre import scene as S
from films.theatre.acteur import MAINS, Acteur, Jeu, pose
from films.theatre.scene import SOL, W, H, ease, lerp

FPS = 30
DUR = 19.0
STRIDE = 230.0                         # px par cycle de marche (deux pas)
PEAU1, PEAU2_SOL = 520.0, 735.0


def win(t, a, b):
    return a <= t < b


def marche(t, t0, t1, x0, x1):
    """Position et phase de marche entre t0 et t1 (départ/arrivée adoucis)."""
    u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
    x = lerp(x0, x1, u)
    return x, abs(x - x0) / STRIDE, 1.0 if t0 <= t < t1 else 0.0


# ------------------------------------------------------------------------------------------------ Sam
def sam(t):
    j = Jeu(pose=pose("repos"), mains=MAINS["repos"], sol=SOL, humeur="content", tour=1)
    if t < 4.2:                                                     # entre en sifflotant
        j.x, j.marche, j.marche_k = marche(t, 0.9, 4.2, 110, 360)
        j.cligne = (t % 2.7) < 0.1
        return j
    if t < 5.2:                                                     # « ! » la peau de banane
        j.x = 360
        j.pose, j.mains, j.humeur = pose("surpris"), MAINS["surpris"], "surpris"
        j.regard = (1, 0.8)
        return j
    if t < 6.6:                                                     # face public : « je suis malin »
        j.x, j.tour = 360, 0
        j.pose, j.mains, j.humeur = pose("malin"), MAINS["malin"], "malin"
        j.regard = (0.3, 0)
        return j
    if t < 7.7:                                                     # grand pas par-dessus
        u = (t - 6.6) / 1.1
        j.x = lerp(360, 640, ease(u))
        j.saut = 70 * math.sin(math.pi * min(1, max(0, (u - 0.1) / 0.8)))
        j.pose, j.mains, j.humeur = pose("pas_haut"), MAINS["pas_haut"], "malin"
        return j
    if t < 10.4:                                                    # victoire, face public
        j.x, j.tour = 640, 0
        j.pose, j.mains, j.humeur = pose("victoire"), MAINS["victoire"], "content"
        j.cligne = win(t, 9.0, 9.12)
        if t > 9.6:
            j.pose = pose("hanches")
            j.mains = MAINS["hanches"]
        return j
    if t < 11.1:                                                    # repart fièrement vers la droite…
        j.x, j.marche, j.marche_k = marche(t, 10.4, 11.4, 640, 780)
        j.humeur = "content"
        return j
    # … et glisse sur la peau jetée par Léo
    ts = 11.1
    u = (t - ts) / 0.45
    j.x = 700 + 40 * ease(u)
    j.rotation = -95 * ease(u) + (3 * math.sin((t - ts) * 25) * math.exp(-(t - ts - 0.45) * 6) if u > 1 else 0)
    j.saut = 120 * math.sin(math.pi * min(1, u)) if u < 1 else 0
    j.pose = pose("surpris", jd_h=70, jg_h=50) if u < 1 else pose("allonge")
    j.mains = MAINS["surpris"]
    j.humeur = "surpris" if u < 1 else "ko"
    if t > 16.0:                                                    # pouce levé, toujours par terre
        j.pose = pose("allonge", bd_e=95, bd_c=-10)
        j.mains = ("ouverte", "pouce")
        j.humeur = "content"
    return j


# ------------------------------------------------------------------------------------------------ Léo
def leo(t):
    j = Jeu(pose=pose("repos"), mains=MAINS["repos"], sol=SOL, humeur="neutre", tour=-1, x=1250)
    if t < 8.6:
        return j
    if t < 10.0:                                                    # entre par la droite en mangeant
        j.x, j.marche, j.marche_k = marche(t, 8.6, 10.0, 1250, 930)
        j.humeur = "content"
        return j
    if t < 11.6:                                                    # jette la peau par-dessus l'épaule
        j.x = 930
        j.tour = -1 if t < 10.7 else 0
        if win(t, 10.0, 10.5):
            j.pose = pose("repos", bd_e=150, bd_c=40)
        j.humeur = "content"
        return j
    if t < 14.2:                                                    # se moque
        j.x, j.tour = 930, -0.6
        j.pose, j.mains, j.humeur = pose("rire"), MAINS["rire"], "rire"
        if t > 12.6:
            j.pose = pose("pointe")
            j.mains = MAINS["pointe"]
            j.pose["colonne"] = -12 + 4 * math.sin(t * 18)
        return j
    # bonk ! la banane tombe du ciel
    tb = 14.2
    u = (t - tb - 0.15) / 0.5
    j.x, j.tour = 930, -0.6
    j.humeur = "ko"
    j.pose = pose("surpris")
    j.mains = MAINS["surpris"]
    if u > 0:
        j.rotation = 95 * ease(u)
        j.pose = pose("allonge") if u > 1 else j.pose
    return j


# ------------------------------------------------------------------------------------------------ rendu
def ouverture(t):
    return ease((t - 0.2) / 1.0) * (1 - ease((t - 17.4) / 1.0))


def frame(c, t, sam_a, leo_a):
    js, jl = sam(t), leo(t)
    sam_a.avance(js)
    leo_a.avance(jl)
    c.save()
    shake = 0.0
    for t0 in (11.55, 14.35):
        d = t - t0
        if 0 <= d < 0.35:
            shake = 12 * math.exp(-d * 10) * math.sin(d * 80)
    c.translate(shake, 0)
    c.translate(W / 2, SOL - 330)
    c.scale(1.22, 1.22)
    c.translate(-640, -(SOL - 330))
    S.decor(c, t, ouverture(t))
    # peau n° 1 (enjambée)
    S.peau_banane(c, PEAU1, SOL - 4, 1.1, ecrase=0.0)
    # peau n° 2 : vol par-dessus l'épaule de Léo, atterrit devant Sam
    if t >= 10.25:
        u = min(1.0, (t - 10.25) / 0.55)
        x = lerp(940, PEAU2_SOL, u)
        y = lerp(SOL - 520, SOL - 4, u) - 260 * math.sin(math.pi * u)
        ang = 720 * u if u < 1 else 0
        if t > 11.1:                                                # glisse sous le pied de Sam
            v = min(1.0, (t - 11.1) / 0.4)
            x += 160 * ease(v)
            ang = -30 * v
        S.peau_banane(c, x, y, 1.1, ang)
    if t < 8.6 or t > 10.25:
        pass
    else:
        S.banane(c, 870, SOL - 560, -40, 0.7)                # Léo mange une banane (dans la main)
    sam_a.draw(c, js)
    leo_a.draw(c, jl)
    # banane qui tombe sur Léo
    if 13.6 <= t < 15.4:
        u = (t - 13.6) / 0.75
        if u < 1:
            S.banane(c, 930, lerp(-80, SOL - 760, u * u), 30 * u)
        else:
            v = t - 14.35
            S.banane(c, 930 + 260 * v, SOL - 760 - 300 * v + 900 * v * v, 30 + 400 * v)
    # effets
    if win(t, 1.4, 4.2):
        S.notes(c, js.x + 70, SOL - 700, t)
    if win(t, 4.25, 5.2):
        S.bulle(c, 420, SOL - 860, "!", (t - 4.25) / 0.25, queue=(-30, 90), taille=130)
    if win(t, 7.7, 9.6):
        for i in range(6):                                           # étincelles de victoire
            a = i * math.pi / 3 + t * 2
            r = 230 + 20 * math.sin(t * 6 + i)
            S.etoiles(c, 640 + r * math.cos(a) * 0.2, SOL - 500 + r * math.sin(a) * 0.2, t + i, 0.0)
        S.bulle(c, 640, SOL - 900, "TROP FACILE !", (t - 7.8) / 0.3, queue=(-10, 90), taille=86)
    if t > 11.6 and t < 17.5:
        S.etoiles(c, 410, SOL - 90, t)
    if win(t, 11.7, 14.2):
        S.bulle(c, 860, SOL - 900, "HA HA HA !", (t - 11.7) / 0.3, queue=(50, 90), taille=86)
    if t > 14.4 and t < 17.5:
        S.etoiles(c, 1110, SOL - 90, t + 1)
    if win(t, 16.0, 17.5):
        S.bulle(c, 420, SOL - 420, "ÇA VA…", (t - 16.0) / 0.3, queue=(70, 90), taille=80)
    c.restore()
    S.rideaux(c, ouverture(t))


def bande_son(path, dur):
    n = int(dur * MI.SR)
    mix = np.zeros(n)

    def add(t0, s, g=1.0):
        s = np.interp(np.arange(int(len(s) * MI.SR / S.SR)) * S.SR / MI.SR, np.arange(len(s)), s)
        i = int(t0 * MI.SR)
        k = min(n - i, len(s))
        if k > 0:
            mix[i:i + k] += s[:k] * g

    add(0.2, S.rideau_son(1.0))
    add(0.4, S.applaudissements(1.6, 0.12))
    add(1.3, S.sifflet(2.8))
    for k in range(int((4.2 - 1.0) * 2 * 230 / STRIDE)):             # pas
        add(1.0 + k * 0.42, S.tap())
    add(4.25, E1.ding(1046, 0.18))
    add(5.3, E1.sparkle(0.08))
    add(6.7, E1.swish(0.8, 0.12))
    add(7.65, S.tap(0.2))
    add(7.75, E1.sparkle(0.14))
    for k in range(4):
        add(8.6 + k * 0.38, S.tap(0.09))
    add(10.25, E1.swish(0.5, 0.12))
    add(11.1, S.glissade())
    add(11.55, HK.sub_drop(0.45))
    add(11.6, S.boing())
    add(11.8, E1.sparkle(0.1))
    add(13.6, E1.swish(0.7, 0.1))
    add(14.35, S.bonk())
    add(14.6, HK.sub_drop(0.35))
    add(16.2, S.ba_dum_tss())
    add(17.3, S.rideau_son(1.0))
    add(17.4, S.applaudissements(1.6, 0.16))
    mus = E1.music(dur) * 0.35
    out = mix + mus[:n]
    out = np.tanh(out * 1.4) / np.tanh(1.4)
    st = np.stack([out, out], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(MI.SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


def render(out, t_from=0.0, t_to=DUR):
    sam_a, leo_a = Acteur("meche"), Acteur("casquette")
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(t_to * FPS)):
        t = f / FPS
        c = surf.getCanvas()
        frame(c, t, sam_a, leo_a)
        if t >= t_from:
            ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    bande_son(f"{tmp}/a.wav", DUR)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-ss", str(t_from), "-i", f"{tmp}/a.wav",
                    "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/sketch_banane.mp4")
