"""Style « Constellation » : tout est fait de particules de lumière, rendues par une vraie caméra
(perspective, profondeur de champ, brume) puis lueur et grain. Rendu CPU rapide (numba + OpenCV).

Principe de la profondeur de champ : chaque point est déposé dans une « couche de flou » selon son cercle de
confusion (0, 2, 4, 8… px) ; chaque couche est floutée une seule fois puis toutes sont additionnées.
"""
import math

import cv2
import numpy as np
from numba import njit, prange

W, H, FPS = 1080, 1920, 30
LEVELS = 7                      # couches de flou : sigma 0, 1.5, 3, 6, 12, 24, 48 px

BLUE = np.array([0.22, 0.52, 1.0], np.float32)
BLUE_HI = np.array([0.55, 0.78, 1.0], np.float32)
WHITE = np.array([0.9, 0.95, 1.0], np.float32)
RED = np.array([1.0, 0.12, 0.08], np.float32)
GOLD = np.array([1.0, 0.7, 0.25], np.float32)
ORANGE = np.array([1.0, 0.45, 0.12], np.float32)


# ------------------------------------------------------------------ caméra
def look_at(pos, target, fov_deg=40.0, roll=0.0):
    pos, target = np.asarray(pos, np.float64), np.asarray(target, np.float64)
    f = target - pos
    f /= np.linalg.norm(f)
    up = np.array([0, 0, 1.0])
    if abs(f @ up) > 0.999:
        up = np.array([0, 1.0, 0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    if roll:
        c, s = math.cos(roll), math.sin(roll)
        r, u = c * r + s * u, -s * r + c * u
    foc = 0.5 * W / math.tan(math.radians(fov_deg) / 2)      # fov horizontal
    return dict(pos=pos, r=r, u=u, f=f, foc=foc)


class Lens:
    def __init__(self, focus=100.0, aperture=0.0, fog_near=1e9, fog_far=2e9, max_coc=60.0):
        self.focus, self.aperture, self.fog_near, self.fog_far, self.max_coc = focus, aperture, fog_near, fog_far, max_coc


# ------------------------------------------------------------------ dépôt des points
@njit(cache=True, fastmath=True)
def _deposit(P, C, A, pos, r, u, f, foc, focus, aperture, fn, ff, max_coc, buf):
    n = P.shape[0]
    Hh, Ww = buf.shape[1], buf.shape[2]
    cx, cy = Ww * 0.5, Hh * 0.5
    for i in range(n):
        a = A[i]
        if a <= 0.0:
            continue
        dx, dy, dz = P[i, 0] - pos[0], P[i, 1] - pos[1], P[i, 2] - pos[2]
        z = dx * f[0] + dy * f[1] + dz * f[2]
        if z < 0.05:
            continue
        x = (dx * r[0] + dy * r[1] + dz * r[2]) * foc / z + cx
        y = -(dx * u[0] + dy * u[1] + dz * u[2]) * foc / z + cy
        if x < -40 or x > Ww + 40 or y < -40 or y > Hh + 40:
            continue
        coc = aperture * abs(1.0 - focus / z)
        if coc > max_coc:
            coc = max_coc
        lvl = 0
        if coc > 1.5:
            lvl = int(math.log2(coc / 1.5)) + 1
            if lvl > 6:
                lvl = 6
        fog = 1.0
        if z > fn:
            fog = max(0.0, 1.0 - (z - fn) / (ff - fn))
        w = a * fog
        if w <= 0.0:
            continue
        ix, iy = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - ix, y - iy
        for oy in range(2):
            yy = iy + oy
            if yy < 0 or yy >= Hh:
                continue
            wy = fy if oy == 1 else 1.0 - fy
            for ox in range(2):
                xx = ix + ox
                if xx < 0 or xx >= Ww:
                    continue
                ww = w * wy * (fx if ox == 1 else 1.0 - fx)
                buf[lvl, yy, xx, 0] += C[i, 0] * ww
                buf[lvl, yy, xx, 1] += C[i, 1] * ww
                buf[lvl, yy, xx, 2] += C[i, 2] * ww


class Frame:
    """Accumule des groupes de points puis produit l'image finale (uint8 RGB)."""

    def __init__(self, cam, lens, scale=1.0):
        self.cam, self.lens = cam, lens
        self.buf = np.zeros((LEVELS, H, W, 3), np.float32)

    def points(self, P, col, alpha=1.0):
        """P (n,3) ; col (3,) ou (n,3) ; alpha scalaire ou (n,)."""
        P = np.ascontiguousarray(P, np.float64)
        n = len(P)
        if n == 0:
            return
        C = np.ascontiguousarray(np.broadcast_to(np.asarray(col, np.float32), (n, 3)), np.float32)
        A = np.ascontiguousarray(np.broadcast_to(np.asarray(alpha, np.float32), (n,)), np.float32)
        c, L = self.cam, self.lens
        _deposit(P, C, A, c["pos"], c["r"], c["u"], c["f"], c["foc"], L.focus, L.aperture, L.fog_near, L.fog_far,
                 L.max_coc, self.buf)

    def finish(self, exposure=1.0, bloom=0.8, grain=0.035, seed=0):
        img = self.buf[0].copy()
        for k in range(1, LEVELS):
            if self.buf[k].any():
                s = 1.5 * 2 ** (k - 1) * 0.6
                img += cv2.GaussianBlur(self.buf[k], (0, 0), s)
        # léger cœur net + halo : les points isolés deviennent des étoiles douces
        img = cv2.GaussianBlur(img, (0, 0), 0.7) * 1.0
        glow = (cv2.GaussianBlur(img, (0, 0), 5) * 0.55 + cv2.GaussianBlur(img, (0, 0), 18) * 0.35 +
                cv2.GaussianBlur(img, (0, 0), 55) * 0.25)
        img = img + glow * bloom
        out = 1.0 - np.exp(-img * exposure)
        if grain:
            rng = np.random.default_rng(seed)
            out += rng.standard_normal((H, W, 1)).astype(np.float32) * grain * (0.25 + out.mean(2, keepdims=True))
        return (np.clip(out, 0, 1) ** (1 / 1.1) * 255).astype(np.uint8)


# ------------------------------------------------------------------ outils d'animation
def ease(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x < 0.5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)


def keyed(t, keys):
    """Interpolation lissée entre clés [(t, valeur), …] ; valeur scalaire ou vecteur."""
    if t <= keys[0][0]:
        return np.asarray(keys[0][1], np.float64)
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            k = float(ease_io((t - t0) / (t1 - t0)))
            return np.asarray(v0, np.float64) * (1 - k) + np.asarray(v1, np.float64) * k
    return np.asarray(keys[-1][1], np.float64)


def morph(A, B, t, t0, dur, order=None, spread=0.5, swirl=0.0, seed=0):
    """Transforme le nuage A en B entre t0 et t0+dur ; order (n,) dans [0,1] décale le départ de chaque point."""
    n = len(A)
    if order is None:
        order = np.random.default_rng(seed).random(n)
    local = (t - t0 - order * dur * spread) / (dur * (1 - spread))
    k = ease_io(local)[:, None]
    P = A * (1 - k) + B * k
    if swirl:
        s = np.sin(np.pi * k[:, 0])[:, None]
        rng = np.random.default_rng(seed + 1)
        d = rng.standard_normal((n, 3))
        P = P + d * swirl * s
    return P
