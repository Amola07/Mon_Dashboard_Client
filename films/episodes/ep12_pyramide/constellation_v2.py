"""Épisode 12 — démo v2 du style « Constellation » : vraie Terre, pyramide en blocs, intérieur en volumes,
chiffres et ouvriers en particules. Deux extraits : ouverture (0–14,1 s) et première énigme (24,6–32,9 s).

    python -m films.episodes.ep12_pyramide.constellation_v2 output/ep12_constellation_v2.mp4 [--still A:1.0,B:5.0]
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
PARTS = {"A": (0.0, 14.1), "B": (24.6, 32.9)}
g = np.random.default_rng(5)

# ================================================================== décor commun
N_PYR = 420_000
PYR, PYR_I = F.pyramid_blocks(N_PYR, seed=1)
PYR_C = (M.BLUE[None, :] * PYR_I[:, None]).astype(np.float32)
SPARK = g.random(N_PYR) < 0.015
SPARK_PH = g.uniform(0, 6.28, N_PYR)
KHA, KHA_I = F.pyramid_simple(160_000, (-160, 420, 0), 107.5, 136.4, seed=2)
MEN, MEN_I = F.pyramid_simple(70_000, (-330, 880, 0), 51.5, 65.5, seed=3)
STARS = F.sphere(5000, 4000.0, (0, 0, 0), seed=6, lines=0.0)
STARS = STARS[STARS[:, 2] > 0]
STAR_A = g.uniform(0.15, 1.0, len(STARS)).astype(np.float32)
NG = 260_000
rr = np.sqrt(g.random(NG)) * 1400
th = g.random(NG) * 2 * np.pi
GROUND = np.stack([rr * np.cos(th), rr * np.sin(th), g.normal(0, 0.25, NG)], 1)
GROUND_A = (np.exp(-rr / 500) * g.uniform(0.3, 1, NG)).astype(np.float32)


def sparkle(t):
    return 1.0 + SPARK * 4.0 * np.maximum(0, np.sin(SPARK_PH + t * 2.2)) ** 12


def base_scene(fr, t, a_ground, a_neigh):
    fr.points(STARS, M.WHITE, STAR_A * 0.6)
    if a_ground > 0:
        fr.points(GROUND, M.BLUE, GROUND_A * a_ground, warm_near=60)
    if a_neigh > 0:
        fr.points(KHA, M.BLUE[None, :] * KHA_I[:, None], a_neigh)
        fr.points(MEN, M.BLUE[None, :] * MEN_I[:, None], a_neigh)


def add_dust(fr, cam, t, a):
    P, A = M.dust(cam, t)
    fr.points(P, M.BLUE_HI, A * a)


# ================================================================== extrait A : 0 → 14,1 s
EC, ER = np.array([0, 0, 80.0]), 95.0
CAM0 = np.array([60, -360, 250.0])
_d = (CAM0 - EC) / np.linalg.norm(CAM0 - EC) + np.array([0, 0, 0.3])
EGY_DIR = _d / np.linalg.norm(_d)
EARTH_U, EARTH_C, _ = F.earth(N_PYR, seed=4)
EGY = F._lonlat_to_xyz(np.array(31.2), np.array(27.0))


def earth_at(t):
    a = np.radians(-2.0 * t)                                  # la Terre tourne doucement
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Ra = F.align_rotation(Rz @ EGY, EGY_DIR, Rz @ np.array([0, 0, 1.0]), (0, 0, 1))
    return (EARTH_U @ Rz.T @ Ra.T) * ER + EC


EGY_PT = EC + EGY_DIR * ER
ORDER = PYR[:, 2] / 140
INT = F.interior_v2(90_000, seed=7)
VOL = F.pyramid_volume(1_300_000, seed=3)
VOL = VOL[np.abs(VOL[:, 0]) < 9.0]
DV, DIRV, _ = F.capsule_dist(VOL)
DI, DIRI, _ = F.capsule_dist(INT)
K, PER, LEN, SPEED = 110, 40, 45.0, 420.0
RX, RY, RPH = g.uniform(-1, 1, K), g.uniform(-1, 1, K), g.uniform(0, 1, K)


def rays(t, alpha):
    k = float(M.ease_io((t - 2.6) / 1.8))
    cx, cy = EGY_PT[0] * (1 - k), EGY_PT[1] * (1 - k)
    sp = 22 * (1 - k) + 110 * k
    top, bot = 700.0, (EGY_PT[2] - 5) * (1 - k) - 40 * k
    z0 = top - ((RPH * (top - bot) + SPEED * t) % (top - bot))
    s = np.linspace(0, 1, PER)
    P = np.empty((K * PER, 3))
    P[:, 0] = np.repeat(cx + RX * sp, PER)
    P[:, 1] = np.repeat(cy + RY * sp, PER)
    P[:, 2] = (z0[:, None] + s[None, :] * LEN).ravel()
    return P, np.tile((1 - s) ** 1.5, K) * alpha


CAM_A = [(0.0, CAM0, (0, 0, 120), 34), (2.6, (70, -330, 225), (0, 0, 95), 36),
         (4.4, (250, -300, 18), (0, 0, 64), 36), (6.1, (235, -265, 26), (0, 0, 58), 36),
         (8.6, (330, -40, 62), (0, -6, 46), 34), (11.4, (190, -22, 50), (0, -11, 44), 32),
         (14.1, (110, -16, 47), (0, -12, 44), 30)]


def cam_from(keys, t, ap_keys, fog=True):
    pos = M.keyed(t, [(k[0], k[1]) for k in keys])
    tgt = M.keyed(t, [(k[0], k[2]) for k in keys])
    fov = float(M.keyed(t, [(k[0], k[3]) for k in keys]))
    dist = float(np.linalg.norm(tgt - pos))
    ap = float(M.keyed(t, ap_keys))
    fn, ff = (dist * 1.8, dist * 6) if fog else (1e9, 2e9)
    return M.look_at(pos, tgt, fov), M.Lens(focus=dist, aperture=ap, fog_near=fn, fog_far=ff)


def frame_A(t):
    cam, lens = cam_from(CAM_A, t, [(0, 3.0), (6, 4.0), (10, 10.0), (14.1, 18.0)])
    fr = M.Frame(cam, lens)
    base_scene(fr, t, float(M.keyed(t, [(0, 0), (2.8, 0), (4.4, 0.4), (8.6, 0.12)])),
               float(M.keyed(t, [(0, 0), (3.6, 0), (5.0, 0.12), (8.0, 0.0)])))
    E = earth_at(min(t, 2.6))
    if t < 2.6:
        P, C = E, EARTH_C
    else:
        P = M.morph(E, PYR, t, 2.6, 1.8, order=ORDER, spread=0.55, swirl=2.0, seed=7)
        k = M.ease_io((t - 2.6 - ORDER * 1.8 * 0.55) / (1.8 * 0.45))[:, None].astype(np.float32)
        C = EARTH_C * (1 - k) + PYR_C * k
    a_s = float(M.keyed(t, [(0, 0.55), (2.6, 0.55), (4.0, 0.42), (6.2, 0.42), (8.6, 0.1)]))
    fr.points(P, C, a_s * sparkle(t), warm_near=180)
    a_vol = float(M.keyed(t, [(0, 0.0), (6.3, 0.0), (8.6, 0.32)]))
    if a_vol > 0:
        o = float(M.keyed(t, [(0, 0.0), (9.4, 0.0), (11.2, 1.0)]))
        R = 6.5 * o
        for base, D, DIR, alpha, col in ((VOL, DV, DIRV, a_vol, M.BLUE), (INT, DI, DIRI, a_vol * 1.4, M.BLUE_HI)):
            if R > 0:
                nd = np.sqrt(D * D + R * R)
                Q = base + DIR * (nd - D)[:, None]
                w = (o * np.exp(-((nd - R) / 2.2) ** 2))[:, None].astype(np.float32)
                fr.points(Q, col[None, :] * (1 - w) + M.RED[None, :] * w, alpha * (1 + 2.5 * w[:, 0]), warm_near=60)
            else:
                fr.points(base, col, alpha, warm_near=60)
    Pr, Ar = rays(t, float(M.keyed(t, [(0, 1.0), (8.6, 1.0), (10.5, 0.25)])))
    fr.points(Pr, M.BLUE_HI, Ar * 3.0)
    add_dust(fr, cam, t, 0.25)
    return fr.finish(exposure=2.6, bloom=1.0, seed=int(t * 30))


# ================================================================== extrait B : 24,6 → 32,9 s (u = 0 → 8,3)
ZB = lambda u: float(M.keyed(u, [(0, 46.0), (3.4, 46.0), (4.6, 76.0)]))
PYR_B, PYR_BI = F.pyramid_blocks(520_000, seed=12)
NUM = F.text_points("2 300 000", 90_000, height=15.0, seed=13)
NUM_SKY = g.normal(0, 1, (len(NUM), 3)) * [160, 60, 80] + [0, 0, 160]
_new = np.nonzero((PYR_B[:, 2] > 46) & (PYR_B[:, 2] <= 76))[0]
NUM_DST = PYR_B[g.choice(_new, len(NUM))]
NUM_ORDER = g.random(len(NUM))
FIG = F.Figure(16_000, seed=14)
SLED0 = np.array([150.0, -262.0, 0.0])
DIRW = -SLED0[:2] / np.linalg.norm(SLED0[:2])                 # vers la pyramide
DIRW3 = np.array([DIRW[0], DIRW[1], 0.0])
SIDE3 = np.array([-DIRW[1], DIRW[0], 0.0])
YAW = np.arctan2(DIRW[0], DIRW[1])
BLOCK = F.box_surface(14_000, -0.8, 0.8, -0.6, 0.6, 0.25, 1.35, seed=15, edge=0.5)
TEAM = [(1.0 * (i % 2 * 2 - 1), 3.2 + 1.5 * (i // 2), 0.37 * i) for i in range(8)]   # (côté, distance, phase)
TORCH = [SLED0 + DIRW3 * d + SIDE3 * s for d, s in ((2.0, 3.2), (7.0, -3.2), (12.0, 3.2))]
MOON = F.sphere(6000, 40.0, (-900, 1600, 700), seed=16, lines=0.3)
_S = np.array([150.0, -262.0, 0.0]); _D = -_S / np.linalg.norm(_S[:2]); _D[2] = 0; _L = np.array([-_D[1], _D[0], 0])
_C1 = _S + _D * 6.5 + _L * 7.5 + [0, 0, 1.6]; _T1 = _S + _D * 3.0 + [0, 0, 1.2]
CAM_B = [(0.0, (430, -470, 150), (0, 0, 55), 36), (1.2, (420, -500, 120), (40, -120, 150), 36),
         (3.2, (420, -500, 120), (40, -120, 150), 36), (4.6, (330, -420, 70), (0, 0, 60), 36),
         (5.4, _C1, _T1, 42), (8.3, _C1 + _D * 3.2 + [0, 0, -0.3], _T1 + _D * 3.6, 42)]


def frame_B(u):
    cam, lens = cam_from(CAM_B, u, [(0, 4.0), (4.6, 4.0), (5.4, 9.0), (8.3, 10.0)], fog=False)
    fr = M.Frame(cam, lens)
    night = float(M.keyed(u, [(0, 0.0), (7.2, 0.0), (8.0, 1.0)]))
    base_scene(fr, u, 0.4 * (1 - 0.5 * night), 0.12)
    zb = ZB(u)
    m = PYR_B[:, 2] <= min(zb, 46.0) + 1e-6 if u < 4.6 else PYR_B[:, 2] <= zb + 1e-6
    fr.points(PYR_B[m], M.BLUE[None, :] * PYR_BI[m, None], 0.42, warm_near=120)
    plat = F.platform(30_000, zb, seed=17)
    fr.points(plat, M.BLUE, 0.12)
    # rampe de chantier jusqu'au front de taille
    s_top = F.HALF * (1 - zb / F.HEIGHT)
    ramp = F.along(F.box_surface(40_000, -6, 6, 0, 1, -0.5, 0.0, seed=18, edge=0.6) * [1, 1, 1],
                   (SLED0[0] + 10, SLED0[1] - 30, 0), (s_top * 0.7, -s_top, zb))
    fr.points(ramp, M.ORANGE * 0.6, 0.35)
    # « 2 300 000 » : se forme dans le ciel puis pleut sur les nouvelles assises
    if 1.0 < u:
        cb = M.look_at(*[M.keyed(3.0, [(k[0], k[i]) for k in CAM_B]) for i in (1, 2)])
        Pn = cb["pos"] + 260 * cb["f"]
        num = Pn + np.outer(NUM[:, 0], cb["r"]) + np.outer(NUM[:, 2], cb["u"])
        sky = Pn + NUM_SKY - [0, 0, 160]
        if u < 3.2:
            P = M.morph(sky, num, u, 1.0, 1.0, order=NUM_ORDER, spread=0.5, swirl=4.0, seed=19)
        else:
            P = M.morph(num, NUM_DST, u, 3.2, 1.5, order=NUM_ORDER, spread=0.6, swirl=6.0, seed=20)
        a = float(M.keyed(u, [(1.0, 0.0), (1.6, 1.2), (3.2, 1.2), (4.7, 0.42)]))
        col = M.GOLD if u < 3.4 else M.GOLD * (1 - min(1, (u - 3.4))) + M.BLUE * min(1, (u - 3.4))
        fr.points(P, col, a)
    # l'équipe tire le bloc sur son traîneau
    if u > 4.4:
        adv = DIRW3 * 0.45 * (u - 4.4)
        sled = SLED0 + adv
        R2 = np.array([[DIRW[1], DIRW[0], 0], [-DIRW[0], DIRW[1], 0], [0, 0, 1]]).T
        fr.points(BLOCK @ R2.T + sled, M.BLUE_HI, 0.18, warm_near=12)
        for sd in (-0.55, 0.55):
            run = F.polyline([sled - DIRW3 * 1.0 + SIDE3 * sd + [0, 0, 0.08], sled + DIRW3 * 1.0 + SIDE3 * sd + [0, 0, 0.08],
                              sled + DIRW3 * 1.3 + SIDE3 * sd + [0, 0, 0.3]], 1500, seed=21)
            fr.points(run, M.ORANGE, 0.25)
        for k, (side, dist, ph) in enumerate(TEAM):
            pos = sled + DIRW3 * dist + SIDE3 * side
            pts = FIG.points("walking", (u + ph) * 0.65, pos, yaw=-YAW, lean=0.32)
            fr.points(pts, M.BLUE_HI, 0.11, warm_near=12)
            hand = pos + DIRW3 * 0.35 + [0, 0, 1.0]
            rope = F.polyline([sled + DIRW3 * 0.8 + SIDE3 * side * 0.4 + [0, 0, 0.9], hand], 400, seed=30 + k)
            fr.points(rope, M.GOLD, 0.3)
        if night > 0:
            for i, tp in enumerate(TORCH):
                tp = tp + adv
                pole = F.polyline([tp, tp + [0, 0, 2.4]], 300, seed=40 + i)
                fr.points(pole, M.BLUE, 0.3)
                fl = tp + [0, 0, 2.6] + g.normal(0, 1, (900, 3)) * [0.12, 0.12, 0.25]
                fr.points(fl, M.ORANGE, night * (0.5 + 0.15 * np.sin(u * 23 + i)))
    if night > 0:
        fr.points(MOON, M.WHITE, 0.5 * night)
    add_dust(fr, cam, u, 0.3)
    return fr.finish(exposure=2.6, bloom=1.0, seed=int(u * 30) + 999)


FRAMES = {"A": frame_A, "B": frame_B}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep12_constellation_v2.mp4"
    if "--still" in sys.argv:
        import cv2
        spec = sys.argv[sys.argv.index("--still") + 1].split(",")
        imgs = []
        for s in spec:
            part, t = s.split(":")
            imgs.append(FRAMES[part](float(t))[::2, ::2])
        cv2.imwrite(out, cv2.cvtColor(np.hstack(imgs), cv2.COLOR_RGB2BGR))
        return
    tmp = tempfile.mkdtemp()
    voice_all = MI.load_voice(os.path.join(HERE, "audio", "voix.mp3"))
    pieces = []
    for name, (a, b) in PARTS.items():
        subs = MI.groups([(txt, s0 - a, s1 - a) for txt, s0, s1 in SEG if a <= s0 < b])
        enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                                "-s", f"{M.W}x{M.H}", "-r", str(M.FPS), "-i", "-", "-c:v", "libx264", "-crf", "20",
                                "-pix_fmt", "yuv420p", f"{tmp}/{name}.mp4"], stdin=subprocess.PIPE)
        for i in range(int(round((b - a) * M.FPS))):
            t = i / M.FPS
            rgb = FRAMES[name](t)
            arr = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
            MI.draw_sub(skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType).getCanvas(), t, subs)
            enc.stdin.write(arr.tobytes())
            if i % 60 == 0:
                print(name, f"{t:.1f} s", flush=True)
        enc.stdin.close()
        enc.wait()
        v = voice_all[int(a * MI.SR): int(b * MI.SR)]
        MI.soundtrack(f"{tmp}/{name}.wav", v, b - a)
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", f"{tmp}/{name}.mp4", "-i", f"{tmp}/{name}.wav",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{tmp}/{name}_av.mp4"], check=True)
        pieces.append(f"{tmp}/{name}_av.mp4")
    with open(f"{tmp}/l.txt", "w") as f:
        f.writelines(f"file '{p}'\n" for p in pieces)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/l.txt",
                    "-c:v", "libx264", "-crf", "24", "-preset", "slow", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    main()
