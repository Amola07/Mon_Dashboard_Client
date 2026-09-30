"""Scène de test du personnage : Éclat seul, filmé de près, avec le rig souple et la bibliothèque de mouvements.

Pas de physique, pas de décor : on ne juge que le corps et sa façon de bouger.

    python -m films.stick.scene_test sortie.mp4
"""
import math
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from . import corps as K
from . import foley
from . import mouvements as M
from .corps import Frame, build, cascade, v_add, v_mul

W, H = 1080, 1920
FPS = 24
SCALE = 4.3                                                    # Éclat occupe près de la moitié de la hauteur
GROUND_Y = 1450
FLOOR = Frame((0.0, 0.0), 0.0)
CLIP = {c.nom: c for c in M.CLIPS}


def io(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


class Timeline:
    """Suite de segments ; entre deux segments dont les poses ne se raccordent pas, une transition en cascade."""

    def __init__(self):
        self.segs = []                                         # (début, durée, fonction image -> pose)
        self.events = []                                       # (image, son, force)
        self.n = 0

    def add(self, dur, fn, blend=0):
        self.segs.append((self.n, dur, fn, blend))
        self.n += dur

    def pose(self, f):
        for k, (s0, dur, fn, blend) in enumerate(self.segs):
            if f < s0 + dur:
                p = fn(f - s0)
                if blend and k and f - s0 < blend:            # raccord : la pose précédente cède en cascade
                    ps0, pd, pfn, _ = self.segs[k - 1]
                    prev = pfn(pd - 1)
                    p = cascade(prev, p, (f - s0 + 1) / (blend + 1), io)
                return p
        s0, dur, fn, _ = self.segs[-1]
        return fn(dur - 1)


def build_scene():
    T = Timeline()
    step_f, stride = 12, 64.0
    # 1. il entre en marchant
    u0 = -4 * stride
    T.add(48, lambda f: M.cycle("marche", f, FLOOR, u0, expr="neutre")[0])
    for k in range(4):
        T.events.append((k * step_f, "pas", 0.5))
    # 2. s'arrête, se gratte la tête, a une idée, saute
    T.add(14, lambda f: M.pose_at(CLIP["repos"], 0, FLOOR, 0.0), blend=8)
    T.add(56, lambda f: M.pose_at(CLIP["gratter"], f, FLOOR, 0.0))
    T.add(50, lambda f: M.pose_at(CLIP["idee"], f, FLOOR, 0.0))
    s = T.n
    T.add(50, lambda f: M.pose_at(CLIP["sauter"], f, FLOOR, 0.0))
    T.events += [(s + 13, "pas", 0.4), (s + 27, "choc", 0.6)]
    # 3. repart… et tombe
    s = T.n
    T.add(36, lambda f: M.cycle("marche", f, FLOOR, 0.0, expr="joie")[0], blend=6)
    for k in range(3):
        T.events.append((s + k * step_f, "pas", 0.5))
    u1 = 3 * stride
    s = T.n
    T.add(76, lambda f: M.pose_at(CLIP["tomber"], f, FLOOR, u1), blend=5)
    T.events += [(s + 11, "choc", 0.9)]
    # 4. hausse les épaules, montre la sortie, part en courant
    T.add(42, lambda f: M.pose_at(CLIP["hausser"], f, FLOOR, u1))
    T.add(50, lambda f: M.pose_at(CLIP["pointer"], f, FLOOR, u1))
    s = T.n
    T.add(34, lambda f: M.cycle("course", f, FLOOR, u1, expr="decide")[0], blend=4)
    for k in range(5):
        T.events.append((s + k * 7, "pas", 0.35))
    T.add(10, lambda f: M.cycle("course", 34 + f, FLOOR, u1, expr="decide")[0])
    return T


def soundtrack(T, path):
    D = T.n / FPS + 1
    mx = foley.Mixer(D)
    for f, kind, force in T.events:
        mx.add(f / FPS, foley.step(force) if kind == "pas" else foley.thud(force), 0.0, 0.8)
    out = mx.out
    out = np.tanh(out * 2.5) * 0.5
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(foley.SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/scene_test.mp4"
    T = build_scene()
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    cape = None
    cam = None
    grid = skia.Paint(AntiAlias=True, Color=skia.Color(70, 75, 90), StrokeWidth=1.2)
    for f in range(T.n):
        p = T.pose(f)
        J = build(p)
        x = J["pelvis"][0]
        cam = x if cam is None else cam + (x - cam) * 0.12       # caméra qui suit en douceur
        c = surf.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        c.save()
        c.translate(W / 2, GROUND_Y)
        c.scale(SCALE, SCALE)
        c.translate(-cam, 0)
        c.drawLine(cam - 200, 0, cam + 200, 0, skia.Paint(AntiAlias=True, Color=skia.Color(210, 215, 230),
                                                         StrokeWidth=1.4))
        for gx in range(int(cam // 60) * 60 - 240, int(cam) + 240, 60):
            c.drawLine(gx, 0, gx, 6, grid)
        anchor = v_add(J["neck"], v_mul(J["fwd"], -5))
        if cape is None:
            cape = K.Cape(anchor)
            for _ in range(40):
                cape.step(anchor, v_mul(J["fwd"], -1), (0.0, 1800.0), 1 / 60)
        for _ in range(3):
            cape.step(anchor, v_mul(J["fwd"], -1), (0.0, 1800.0), 1 / 72, flutter=0.2, t=f / FPS)
        K.draw(c, p, f / FPS, cape, J=J)
        c.restore()
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    wav = f"{tmp}/a.wav"
    soundtrack(T, wav)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", out], check=True)
    print(out, f"{T.n / FPS:.1f} s")


if __name__ == "__main__":
    main()
