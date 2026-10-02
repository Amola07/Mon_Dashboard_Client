"""Épisode 12 — démo du style « Constellation » sur l'ouverture (0 à 14,1 s de la voix).

    python -m films.episodes.ep12_pyramide.constellation_demo output/ep12_constellation_demo.mp4 [--still T]
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
import skia

from films import montage_ia as MI
from films.constellation import formes as F
from films.constellation import moteur as M
from films.episodes.ep12_pyramide.montage import SEG

HERE = os.path.dirname(os.path.abspath(__file__))
END = 14.1

# ---------------------------------------------------------------- nuages (calculés une fois)
NS, NV, NI = 360_000, 800_000, 40_000
SURF = F.pyramid_surface(NS, seed=1)
GLOBE = F.sphere(NS, 95.0, (0, 0, 80), seed=2)
ORDER = SURF[:, 2] / F.HEIGHT                         # la pyramide se construit de bas en haut
VOL = F.pyramid_volume(NV, seed=3)
VOL = VOL[np.abs(VOL[:, 0]) < 9.0]                     # tranche centrale : la « carte de densité » vue de côté
_v2 = F.pyramid_volume(NV, seed=8)
VOL = np.concatenate([VOL, _v2[np.abs(_v2[:, 0]) < 9.0]])
INT = F.interior(NI, seed=4)
DV, DIRV, _ = F.capsule_dist(VOL)
DI, DIRI, _ = F.capsule_dist(INT)
g = np.random.default_rng(5)
STARS = F.sphere(4000, 3000.0, (0, 0, 0), seed=6, lines=0.0)
STARS = STARS[STARS[:, 2] > -200]
# sol du plateau : poussière de points qui s'estompe avec la distance
rr = np.sqrt(g.random(220_000)) * 900
th = g.random(220_000) * 2 * np.pi
GROUND = np.stack([rr * np.cos(th), rr * np.sin(th), g.normal(0, 0.3, 220_000)], 1)
GROUND_A = (np.exp(-rr / 350) * g.uniform(0.3, 1, 220_000)).astype(np.float32)
STAR_A = g.uniform(0.2, 1.0, len(STARS)).astype(np.float32)
# muons : traînées verticales qui tombent en boucle
K, PER, LEN, SPEED = 90, 40, 45.0, 420.0
RX, RY = g.uniform(-110, 110, K), g.uniform(-110, 110, K)
RPH = g.uniform(0, 1, K)
TOP, BOT = 650.0, -60.0


def rays(t, alpha):
    z0 = TOP - ((RPH * (TOP - BOT) + SPEED * t) % (TOP - BOT))
    s = np.linspace(0, 1, PER)
    P = np.empty((K * PER, 3))
    P[:, 0] = np.repeat(RX, PER)
    P[:, 1] = np.repeat(RY, PER)
    P[:, 2] = (z0[:, None] + s[None, :] * LEN).ravel()
    A = np.tile((1 - s) ** 1.5, K) * alpha                # tête brillante, queue qui s'efface
    return P, A


CAM = [(0.0, (60, -360, 250), (0, 0, 85), 38), (2.6, (70, -330, 215), (0, 0, 80), 38),
       (4.2, (240, -290, 22), (0, 0, 62), 36), (6.1, (225, -255, 30), (0, 0, 58), 36),
       (8.6, (330, -40, 62), (0, -6, 46), 34), (11.4, (200, -22, 50), (0, -11, 44), 32),
       (END, (120, -16, 47), (0, -12, 44), 30)]


def camera(t):
    pos = M.keyed(t, [(k[0], k[1]) for k in CAM])
    tgt = M.keyed(t, [(k[0], k[2]) for k in CAM])
    fov = float(M.keyed(t, [(k[0], k[3]) for k in CAM]))
    dist = float(np.linalg.norm(tgt - pos))
    ap = float(M.keyed(t, [(0, 3.0), (6, 4.0), (10, 10.0), (END, 18.0)]))
    return M.look_at(pos, tgt, fov), M.Lens(focus=dist, aperture=ap, fog_near=dist * 1.6, fog_far=dist * 4.5)


def frame(t):
    cam, lens = camera(t)
    fr = M.Frame(cam, lens)
    fr.points(STARS, M.WHITE, STAR_A * 0.6)
    a_gr = float(M.keyed(t, [(0, 0.0), (2.6, 0.0), (4.0, 0.35), (8.6, 0.12)]))
    if a_gr > 0:
        fr.points(GROUND, M.BLUE, GROUND_A * a_gr)
    # globe → pyramide
    if t < 2.6:
        ang = 0.08 * t
        c, s = np.cos(ang), np.sin(ang)
        G = GLOBE - [0, 0, 80]
        P = np.stack([G[:, 0] * c - G[:, 1] * s, G[:, 0] * s + G[:, 1] * c, G[:, 2]], 1) + [0, 0, 80]
    else:
        G = GLOBE - [0, 0, 80]
        ang = 0.08 * 2.6
        c, s = np.cos(ang), np.sin(ang)
        G = np.stack([G[:, 0] * c - G[:, 1] * s, G[:, 0] * s + G[:, 1] * c, G[:, 2]], 1) + [0, 0, 80]
        P = M.morph(G, SURF, t, 2.6, 1.5, order=ORDER, spread=0.55, swirl=2.5, seed=7)
    a_surf = float(M.keyed(t, [(0, 0.2), (6.2, 0.2), (8.6, 0.06)]))
    # le vide repousse aussi la surface ? non : il est intérieur ; seule la matière interne s'écarte
    fr.points(P, M.BLUE, a_surf)
    # densité intérieure (ce que « voient » les muons) puis le vide qui se creuse
    a_vol = float(M.keyed(t, [(0, 0.0), (6.3, 0.0), (8.6, 0.32)]))
    if a_vol > 0:
        o = float(M.keyed(t, [(0, 0.0), (9.4, 0.0), (11.2, 1.0)]))
        R = 6.5 * o
        for base, D, DIR, alpha, col in ((VOL, DV, DIRV, a_vol, M.BLUE), (INT, DI, DIRI, a_vol * 1.0, M.BLUE_HI)):
            if R > 0:
                nd = np.sqrt(D * D + R * R)
                Q = base + DIR * (nd - D)[:, None]
                w = (o * np.exp(-((nd - R) / 2.2) ** 2))[:, None].astype(np.float32)
                C = col[None, :] * (1 - w) + M.RED[None, :] * w
                fr.points(Q, C, alpha * (1 + 2.5 * w[:, 0]))
            else:
                fr.points(base, col, alpha)
    a_ray = float(M.keyed(t, [(0, 1.0), (8.6, 1.0), (10.5, 0.25)]))
    Pr, Ar = rays(t, a_ray)
    fr.points(Pr, M.BLUE_HI, Ar * 3.0)
    return fr.finish(exposure=1.7, bloom=1.0, seed=int(t * 30))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep12_constellation_demo.mp4"
    if "--still" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--still") + 1].split(",")]
        imgs = [frame(t)[::2, ::2] for t in ts]
        import cv2
        cv2.imwrite(out, cv2.cvtColor(np.hstack(imgs), cv2.COLOR_RGB2BGR))
        return
    seg = [s for s in SEG if s[1] < END]
    subs = MI.groups(seg)
    tmp = tempfile.mkdtemp()
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{M.W}x{M.H}",
                            "-r", str(M.FPS), "-i", "-", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
                            f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    n = int(END * M.FPS)
    for i in range(n):
        t = i / M.FPS
        rgb = frame(t)
        arr = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
        MI.draw_sub(skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType).getCanvas(), t, subs)
        enc.stdin.write(arr.tobytes())
        if i % 30 == 0:
            print(f"{t:.1f} s", flush=True)
    enc.stdin.close()
    enc.wait()
    voice = MI.load_voice(os.path.join(HERE, "audio", "voix.mp3"))[: int(END * MI.SR)]
    MI.soundtrack(f"{tmp}/a.wav", voice, END)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    main()
