"""Moteur commun : rendu Skia image par image, palettes, sons ASMR accordés, encodage."""
from __future__ import annotations

import math
import subprocess
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import skia

W, H, FPS = 1080, 1920, 60
SR = 48000


# ---------------------------------------------------------------- couleurs

@dataclass
class Palette:
    name: str
    bg: tuple            # dégradé du fond (haut, bas)
    surface: tuple       # intérieur des contenants
    rim: tuple           # bord des contenants
    shadow: tuple        # couleur des ombres (RGB)
    accents: list        # couleurs des objets, dans l'ordre du dégradé
    dark: bool = False


PALETTES = [  # toutes sur fond noir étoilé, objets pastel
    Palette("nuit lavande", ((14, 12, 30), (3, 3, 8)), (20, 18, 40), (62, 58, 104), (0, 0, 0),
            [(255, 196, 170), (255, 170, 196), (214, 182, 255), (164, 208, 255), (158, 230, 204)], dark=True),
    Palette("nuit menthe", ((6, 18, 22), (2, 4, 6)), (12, 26, 32), (40, 82, 92), (0, 0, 0),
            [(158, 230, 204), (164, 208, 255), (196, 182, 255), (255, 176, 206), (255, 214, 160)], dark=True),
    Palette("nuit sorbet", ((22, 10, 20), (4, 2, 6)), (30, 16, 30), (92, 52, 82), (0, 0, 0),
            [(255, 214, 160), (255, 186, 170), (255, 164, 200), (206, 176, 255), (170, 196, 255)], dark=True),
    Palette("nuit dorée", ((16, 12, 8), (3, 2, 2)), (26, 20, 16), (92, 76, 56), (0, 0, 0),
            [(246, 200, 150), (240, 170, 160), (214, 186, 226), (170, 206, 216), (190, 220, 176)], dark=True),
    Palette("nuit douce", ((34, 32, 58), (8, 8, 18)), (28, 27, 50), (58, 56, 92), (0, 0, 0),
            [(255, 190, 200), (255, 214, 170), (190, 230, 200), (170, 200, 255), (214, 190, 255)], dark=True),
    Palette("océan nuit", ((16, 36, 52), (4, 10, 18)), (14, 30, 44), (40, 70, 92), (0, 0, 0),
            [(140, 220, 230), (150, 200, 255), (190, 180, 255), (255, 190, 220), (255, 225, 180)], dark=True),
    Palette("noir absolu", ((8, 8, 12), (0, 0, 0)), (14, 14, 20), (50, 50, 66), (0, 0, 0),
            [(255, 180, 190), (255, 220, 170), (180, 235, 200), (170, 210, 255), (220, 190, 255)], dark=True),
]


def lerp_rgb(cols, u):
    x = min(max(u, 0.0), 1.0) * (len(cols) - 1)
    i = min(int(x), len(cols) - 2)
    t = x - i
    return tuple(cols[i][k] * (1 - t) + cols[i + 1][k] * t for k in range(3))


def color(rgb, a=255, mul=1.0):
    return skia.Color(*(int(max(0, min(255, c * mul))) for c in rgb[:3]), int(max(0, min(255, a))))


def paint(c=skia.ColorBLACK, style="fill", width=0.0, blur=0.0, shader=None, blend=None):
    p = skia.Paint(AntiAlias=True, Color=c, StrokeWidth=width,
                   Style=skia.Paint.kStroke_Style if style == "stroke" else skia.Paint.kFill_Style)
    if style == "stroke":
        p.setStrokeCap(skia.Paint.kRound_Cap)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
    if blend is not None:
        p.setBlendMode(blend)
    return p


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# ---------------------------------------------------------------- dessin

class Painter:
    """Éléments visuels communs, dans le style de la palette."""

    def __init__(self, pal: Palette, seed: int = 0):
        self.pal = pal
        self.t = 0.0
        self.bg = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [color(pal.bg[0]), color(pal.bg[1])])
        rng = np.random.default_rng(seed)
        n = 230
        self.stars = np.column_stack([rng.uniform(0, W, n), rng.uniform(0, H, n), rng.power(3, n) * 2.2 + 0.5,
                                      rng.uniform(0, 2 * math.pi, n), rng.uniform(0.3, 1.4, n)])
        self.nebula = [(rng.uniform(0.15, 0.85) * W, rng.uniform(0.15, 0.85) * H, rng.uniform(500, 900),
                        pal.accents[int(rng.integers(len(pal.accents)))], rng.uniform(0, 6.28)) for _ in range(2)]

    def background(self, c, stars=True):
        """Fond noir étoilé : dégradé, voile de nébuleuse très léger, étoiles qui scintillent et dérivent."""
        t = self.t
        self.t += 1 / FPS
        c.drawPaint(paint(shader=self.bg))
        for x, y, r, col, ph in self.nebula:
            x += 40 * math.sin(t * 0.05 + ph)
            sh = skia.GradientShader.MakeRadial((x, y), r, [color(col, 16), color(col, 0)])
            c.drawCircle(x, y, r, paint(shader=sh))
        if not stars:
            return
        for x, y, r, ph, sp in self.stars:
            a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(ph + t * sp * 2.2))
            yy = (y + t * 4 * sp) % H
            if r > 2.0:
                c.drawCircle(x, yy, r * 3, paint(skia.Color(255, 255, 255, int(28 * a)), blur=r * 2))
            c.drawCircle(x, yy, r, paint(skia.Color(255, 255, 255, int(235 * a))))

    def container(self, c, cx, cy, r, rim=22):
        p = self.pal
        c.drawCircle(cx, cy + 18, r + rim, paint(color(p.shadow, 90 if p.dark else 45), blur=34))
        c.drawCircle(cx, cy, r + rim, paint(color(p.rim)))
        c.drawCircle(cx, cy, r, paint(color(p.surface, 185)))   # les étoiles transparaissent
        c.save()
        c.clipPath(skia.Path.Circle(cx, cy, r), doAntiAlias=True)
        c.drawCircle(cx, cy - 14, r + 20, paint(color(p.shadow, 70 if p.dark else 40), "stroke", 40, blur=16))
        c.restore()

    def ball(self, c, x, y, r, rgb, alpha=255, shadow=True):
        if r <= 0.3:
            return
        if shadow:
            c.drawCircle(x + r * 0.06, y + r * 0.12, r, paint(color(self.pal.shadow, (80 if self.pal.dark else 55)
                                                                    * alpha / 255), blur=max(3, r * 0.18)))
        shade = skia.GradientShader.MakeRadial((x - r * 0.35, y - r * 0.45), r * 1.6,
                                               [color(rgb, alpha, 1.12), color(rgb, alpha), color(rgb, alpha, 0.8)],
                                               [0.0, 0.5, 1.0])
        c.drawCircle(x, y, r, paint(shader=shade))
        if r > 5:
            c.drawCircle(x - r * 0.36, y - r * 0.42, r * 0.22,
                         paint(skia.Color(255, 255, 255, int(90 * alpha / 255)), blur=max(1.5, r * 0.12)))


class Ripples:
    """Ondulations douces qui s'élargissent depuis un point d'impact."""

    def __init__(self, life=0.7, reach=180):
        self.items, self.life, self.reach = [], life, reach

    def add(self, x, y, rgb, strength=1.0):
        self.items.append([x, y, 0.0, rgb, strength])

    def draw(self, c, dt=1 / FPS):
        keep = []
        for it in self.items:
            it[2] += dt
            a = 1 - it[2] / self.life
            if a <= 0:
                continue
            c.drawCircle(it[0], it[1], 10 + self.reach * (it[2] / self.life) ** 0.7,
                         paint(color(it[3], 120 * a * it[4], 0.92), "stroke", 4 * a + 1))
            keep.append(it)
        self.items = keep


class Particles:
    """Petites billes qui s'envolent puis retombent en s'effaçant (éclatement d'un anneau…)."""

    def __init__(self, gravity=700.0, drag=0.975):
        self.p = np.zeros((0, 7))   # x, y, vx, vy, vie, r, index couleur
        self.cols, self.g, self.drag = [], gravity, drag

    def burst(self, xs, ys, vxs, vys, life, radius, rgb):
        n = len(xs)
        self.cols.extend([rgb] * n)
        new = np.column_stack([xs, ys, vxs, vys, life, radius, np.arange(len(self.cols) - n, len(self.cols))])
        self.p = np.vstack([self.p, new])

    def draw(self, c, painter, dt=1 / FPS):
        if not len(self.p):
            return
        p = self.p
        p[:, 2:4] *= self.drag
        p[:, 3] += self.g * dt
        p[:, 0:2] += p[:, 2:4] * dt
        p[:, 4] -= dt
        self.p = p[p[:, 4] > 0]
        for x, y, _, _, life, r, ci in self.p:
            painter.ball(c, x, y, r * min(1.0, life * 2.5), self.cols[int(ci)], shadow=False)


# ---------------------------------------------------------------- son

PROGRESSIONS = [  # accords en demi-tons au-dessus de la tonique (septièmes douces)
    [[5, 9, 12, 16], [7, 11, 14, 19], [4, 7, 11, 16], [9, 12, 16, 21]],    # IV V iii vi
    [[0, 4, 7, 11], [9, 12, 16, 19], [5, 9, 12, 16], [7, 11, 14, 17]],     # I vi IV V
    [[9, 12, 16, 19], [5, 9, 12, 16], [0, 4, 7, 11], [7, 11, 14, 19]],     # vi IV I V
    [[2, 5, 9, 12], [7, 11, 14, 17], [0, 4, 7, 11], [9, 12, 16, 19]],      # ii V I vi
    [[0, 4, 7, 11], [5, 9, 12, 16], [0, 4, 7, 11], [5, 9, 12, 16]],        # Imaj7 IVmaj7
]
PENTA = [0, 2, 4, 7, 9]
KEYS = {"do": 261.63, "ré": 293.66, "mi♭": 311.13, "fa": 349.23, "sol": 196.00, "la": 220.00}


def _bloop(f, n):
    tt = np.arange(n) / SR
    inst = f * (1 + 0.45 * np.exp(-tt / 0.018))
    body = np.sin(2 * np.pi * np.cumsum(inst) / SR) * np.exp(-tt * 9) * np.minimum(1, tt * 500)
    tone = (np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 3.2) * np.minimum(1, tt * 150)
    return body * 0.8 + tone * 0.35


def _kalimba(f, n):
    tt = np.arange(n) / SR
    env = np.exp(-tt * 2.8) * np.minimum(1, tt * 400)
    return (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 3.1 * f * tt) * np.exp(-tt * 14)
            + 0.12 * np.sin(2 * np.pi * 5.9 * f * tt) * np.exp(-tt * 30)) * env


def _glass(f, n):
    tt = np.arange(n) / SR
    env = np.exp(-tt * 1.6) * np.minimum(1, tt * 120)
    return (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt * 3)
            + 0.15 * np.sin(2 * np.pi * 5.4 * f * tt) * np.exp(-tt * 6)) * env


def _softkeys(f, n):
    tt = np.arange(n) / SR
    env = np.exp(-tt * 2.0) * np.minimum(1, tt * 60)
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 3)
            + 0.1 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 5)) * env


TIMBRES = {"goutte": _bloop, "kalimba": _kalimba, "cristal": _glass, "piano doux": _softkeys}


@dataclass
class Sound:
    """Collecte les impacts pendant le rendu puis fabrique une bande-son accordée."""
    rng: np.random.Generator
    key: str = ""
    timbre: str = ""
    prog: list = field(default_factory=list)
    bar: float = 4.0
    hits: list = field(default_factory=list)
    beds: list = field(default_factory=list)

    def __post_init__(self):
        self.key = self.key or str(self.rng.choice(list(KEYS)))
        self.timbre = self.timbre or str(self.rng.choice(list(TIMBRES)))
        self.prog = self.prog or PROGRESSIONS[int(self.rng.integers(len(PROGRESSIONS)))]
        self.bar = float(self.rng.uniform(3.4, 4.6))
        self._pattern = [0, 2, 1, 3, 2, 0, 3, 1]
        self._k = 0

    def hit(self, t, vel=1.0, step=None, octave=0):
        """Un impact. step=None : note suivante de l'accord en cours ; step=k : k-ième degré de la gamme."""
        self.hits.append((t, vel, step, octave))

    def bed(self, kind, env, level=1.0):
        """Fond sonore continu ("sable", "océan", "vent") ; env : intensité par image (0 à 1)."""
        self.beds.append((kind, np.asarray(env, dtype=float), level))

    def chord_at(self, t):
        return self.prog[int(t / self.bar) % len(self.prog)]

    def render(self, duration, path, min_gap=0.09, pad_level=0.35):
        base = KEYS[self.key]
        voice = TIMBRES[self.timbre]
        N = int((duration + 3) * SR)
        dry = np.zeros(N)
        cache = {}
        last = -1.0
        for t, vel, step, octave in sorted(self.hits, key=lambda h: h[0]):
            gap = t - last
            if step is None:
                if gap < min_gap:
                    continue
                semi = self.chord_at(t)[self._pattern[self._k % 8]]
                self._k += 1
                amp = 0.45 * min(1.0, (gap / 0.4) ** 0.7)
            else:
                semi = PENTA[step % 5] + 12 * (step // 5)
                amp = 0.4
            last = t
            f = base * 2 ** (semi / 12 + octave)
            if f not in cache:
                cache[f] = voice(f, int(2.4 * SR))
            sig = cache[f] * amp * (0.7 + 0.3 * min(1.0, vel))
            i = int(t * SR)
            n = min(len(sig), N - i)
            if n > 0:
                dry[i:i + n] += sig[:n]
        pad = np.zeros(N)
        for b in range(int(duration / self.bar) + 2):
            tt = np.arange(int((self.bar + 1.5) * SR)) / SR
            env = np.minimum(1, tt / 1.5) * np.clip((self.bar + 1.5 - tt) / 1.5, 0, 1)
            sig = sum(np.sin(2 * np.pi * base * 2 ** (s / 12 - 1) * (1 + d) * tt)
                      for s in self.prog[b % len(self.prog)] for d in (-0.002, 0.002))
            i = int(b * self.bar * SR)
            n = min(len(sig), N - i)
            if n > 0:
                pad[i:i + n] += (sig * env)[:n] / 8
        dry += pad * pad_level
        left = dry * 0.8 + _reverb(dry, 1) * 0.6
        right = dry * 0.8 + _reverb(dry, 2) * 0.6
        peak = max(1e-9, np.abs(left).max(), np.abs(right).max())
        for kind, env, level in self.beds:
            e = np.interp(np.arange(N) / SR, np.arange(len(env)) / FPS, env, right=0.0)
            for side, buf in enumerate((left, right)):
                buf += _noise(kind, N, 10 + side) * e * level * peak * 0.18
        st = np.stack([left, right], axis=1)[: int(duration * SR)]
        fi, fo = int(0.3 * SR), int(0.6 * SR)
        st[:fi] *= np.linspace(0, 1, fi)[:, None]
        st[-fo:] *= np.linspace(1, 0.3, fo)[:, None]
        st /= max(1e-9, np.abs(st).max() / 0.8)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((st * 32767).astype(np.int16).tobytes())


def _noise(kind, n, seed):
    """Bruit filtré par son spectre : souffle de sable, ressac, vent."""
    x = np.fft.rfft(np.random.default_rng(seed).standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR) + 1.0
    if kind == "sable":
        shape = np.exp(-((np.log2(f) - np.log2(5000)) ** 2) / 2.0)
    elif kind == "océan":
        shape = 1 / np.sqrt(f) * np.exp(-f / 2500) + 0.02 * np.exp(-((np.log2(f) - 12.5) ** 2) / 1.5)
    else:  # vent
        shape = np.exp(-((np.log2(f) - np.log2(500)) ** 2) / 1.2)
    y = np.fft.irfft(x * shape, n)
    return y / max(1e-9, np.sqrt((y ** 2).mean()))


def _reverb(x, seed, length=2.2, decay=0.55):
    ir_n = int(length * SR)
    g = np.random.default_rng(seed).standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR / decay)
    g /= np.sqrt((g ** 2).sum())
    size = 1 << int(np.ceil(np.log2(len(x) + ir_n)))
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(g, size), size)[: len(x)]


# ---------------------------------------------------------------- vidéo

class Video:
    def __init__(self, path: Path, preview: bool = False):
        self.path = Path(path)
        self.surface = skia.Surface(W, H)
        self.frames = 0
        args = ["-preset", "veryfast", "-crf", "24"] if preview else ["-preset", "medium", "-crf", "17"]
        self.proc = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", *args, "-pix_fmt", "yuv420p",
             str(self.path)], stdin=subprocess.PIPE)

    @property
    def canvas(self):
        return self.surface.getCanvas()

    def emit(self):
        self.proc.stdin.write(self.surface.makeImageSnapshot().toarray().tobytes())
        self.frames += 1

    def close(self):
        self.proc.stdin.close()
        if self.proc.wait():
            raise RuntimeError("ffmpeg a échoué pendant l'encodage")


def mux(video: Path, audio: Path, out: Path):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-i", str(audio),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
                   check=True)


@dataclass
class Ctx:
    """Ce que reçoit chaque concept."""
    rng: np.random.Generator
    pal: Palette
    painter: Painter
    sound: Sound
    video: Video
    seconds: float = 64.0     # durée visée (> 61 s : seuil de rémunération TikTok)
    max_frames: int | None = None  # aperçu : coupe la vidéo

    def done(self, f):
        return self.max_frames is not None and f >= self.max_frames


def circle_hit(pos, vel, r, cx, cy, R):
    """Rebond à l'intérieur d'un cercle. Retourne (normale, vitesse normale) ou None."""
    dx, dy = pos[0] - cx, pos[1] - cy
    dist = math.hypot(dx, dy)
    if dist + r < R or dist == 0:
        return None
    n = (dx / dist, dy / dist)
    pos[0], pos[1] = cx + n[0] * (R - r - 0.5), cy + n[1] * (R - r - 0.5)
    vn = vel[0] * n[0] + vel[1] * n[1]
    if vn <= 0:
        return None
    vel[0] -= 2 * vn * n[0]
    vel[1] -= 2 * vn * n[1]
    return n, vn
