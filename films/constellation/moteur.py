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
    def __init__(self, focus=100.0, aperture=0.0, fog_near=1e9, fog_far=2e9, max_coc=60.0, size=2.2, core=0.4):
        self.focus, self.aperture, self.fog_near, self.fog_far, self.max_coc = focus, aperture, fog_near, fog_far, max_coc
        self.size = size          # taille minimale d'un point (px) : les particules restent lisibles
        self.core = core          # part d'énergie gardée nette au centre de chaque point


# ------------------------------------------------------------------ dépôt des points
@njit(cache=True, fastmath=True)
def _deposit(P, C, A, S, pos, r, u, f, foc, focus, aperture, fn, ff, max_coc, size, core, buf):
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
        sz = size * S[i]
        if coc < sz:
            coc = sz
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
                if lvl > 0 and core > 0.0 and coc < 6.0:
                    # une part de l'énergie reste nette au centre : point brillant entouré d'un halo
                    wc = ww * core
                    buf[0, yy, xx, 0] += C[i, 0] * wc
                    buf[0, yy, xx, 1] += C[i, 1] * wc
                    buf[0, yy, xx, 2] += C[i, 2] * wc
                    ww = ww - wc
                buf[lvl, yy, xx, 0] += C[i, 0] * ww
                buf[lvl, yy, xx, 1] += C[i, 1] * ww
                buf[lvl, yy, xx, 2] += C[i, 2] * ww


def dust(cam, t, n=1500, seed=11, near=2.0, far=45.0, spread=0.8):
    """Poussière en suspension autour de la caméra (fortement floue = bokeh de premier plan)."""
    g = np.random.default_rng(seed)
    d = g.uniform(near, far, n)
    x = g.uniform(-spread, spread, n) * d
    y = g.uniform(-spread * 1.7, spread * 1.7, n) * d
    ph = g.uniform(0, 6.28, n)
    x = x + np.sin(t * 0.3 + ph) * 0.4
    y = y + np.cos(t * 0.23 + ph) * 0.4 - t * 0.15
    P = cam["pos"] + np.outer(d, cam["f"]) + np.outer(x, cam["r"]) + np.outer(y, cam["u"])
    return P, g.uniform(0.2, 1.0, n).astype(np.float32)


class Frame:
    """Accumule des groupes de points puis produit l'image finale (uint8 RGB)."""

    def __init__(self, cam, lens, scale=1.0):
        self.cam, self.lens = cam, lens
        self.buf = np.zeros((LEVELS, H, W, 3), np.float32)
        self.ray_src = []

    def points(self, P, col, alpha=1.0, warm_near=0.0, size=1.0):
        """P (n,3) ; col (3,) ou (n,3) ; alpha scalaire ou (n,).
        warm_near > 0 : les points plus proches que cette distance tirent vers un blanc chaud (profondeur)."""
        P = np.ascontiguousarray(P, np.float64)
        n = len(P)
        if n == 0:
            return
        C = np.ascontiguousarray(np.broadcast_to(np.asarray(col, np.float32), (n, 3)), np.float32)
        if warm_near > 0:
            z = (P - self.cam["pos"]) @ self.cam["f"]
            k = (np.clip(1.0 - z / warm_near, 0, 1) ** 2 * 0.55).astype(np.float32)[:, None]
            C = np.ascontiguousarray(C * (1 - k) + np.array([1.0, 0.9, 0.78], np.float32) * C.max(1, keepdims=True) * k)
        A = np.ascontiguousarray(np.broadcast_to(np.asarray(alpha, np.float32), (n,)), np.float32)
        S = np.ascontiguousarray(np.broadcast_to(np.asarray(size, np.float32), (n,)), np.float32)
        c, L = self.cam, self.lens
        _deposit(P, C, A, S, c["pos"], c["r"], c["u"], c["f"], c["foc"], L.focus, L.aperture, L.fog_near, L.fog_far,
                 L.max_coc, L.size, L.core, self.buf)

    def project(self, X):
        """Position écran (px) d'un point monde, ou None s'il est derrière la caméra."""
        c = self.cam
        d = np.asarray(X, float) - c["pos"]
        z = d @ c["f"]
        if z <= 0.1:
            return None
        return (d @ c["r"] * c["foc"] / z + W / 2, -(d @ c["u"]) * c["foc"] / z + H / 2)

    def rays(self, X, strength=0.6, length=0.35):
        """Rayons de lumière (« god rays ») partant du point monde X."""
        p = self.project(X)
        if p is not None:
            self.ray_src.append((p, strength, length))

    def finish(self, exposure=1.0, bloom=0.8, grain=0.035, seed=0, trail=None, vignette=0.35, aberration=1.2,
               tone="aces"):
        """Image finale. trail : dict d'état {'k': 0.0–0.9} partagé d'une image à l'autre → traînées lumineuses."""
        img = self.buf[0].copy()
        for k in range(1, LEVELS):
            if self.buf[k].any():
                s = 1.5 * 2 ** (k - 1) * 0.6
                img += cv2.GaussianBlur(self.buf[k], (0, 0), s)
        img = cv2.GaussianBlur(img, (0, 0), 0.55)
        if trail is not None:                               # persistance : l'image précédente s'estompe
            prev = trail.get("prev")
            if prev is not None:
                img = np.maximum(img, prev * trail.get("k", 0.5))
            trail["prev"] = img
        glow = (cv2.GaussianBlur(img, (0, 0), 4) * 0.5 + cv2.GaussianBlur(img, (0, 0), 16) * 0.35 +
                cv2.GaussianBlur(img, (0, 0), 48) * 0.3 + cv2.GaussianBlur(img, (0, 0), 120) * 0.15)
        img = img + glow * bloom
        for (cx, cy), st, ln in self.ray_src:               # rayons : flou radial de la partie brillante
            bright = np.maximum(img - 0.15, 0)
            acc = np.zeros_like(img)
            nst = 12
            for i in range(nst):
                sc = 1.0 + ln * i / nst
                M = np.array([[sc, 0, cx * (1 - sc)], [0, sc, cy * (1 - sc)]], np.float32)
                M = cv2.invertAffineTransform(M)
                acc += cv2.warpAffine(bright, M, (W, H), flags=cv2.INTER_LINEAR) * (1 - i / nst)
            img = img + acc * (st / nst)
        x = img * exposure
        if tone == "aces":
            out = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
        else:
            out = 1.0 - np.exp(-x)
        if aberration:                                      # léger décalage rouge / bleu vers les bords
            a = aberration / 1000.0
            for ch, sc in ((0, 1 + a), (2, 1 - a)):
                M = np.array([[sc, 0, W / 2 * (1 - sc)], [0, sc, H / 2 * (1 - sc)]], np.float32)
                out[:, :, ch] = cv2.warpAffine(np.ascontiguousarray(out[:, :, ch]), M, (W, H), flags=cv2.INTER_LINEAR)
        if vignette:
            yy, xx = np.ogrid[:H, :W]
            rr = ((xx - W / 2) / (W / 2)) ** 2 * 0.6 + ((yy - H / 2) / (H / 2)) ** 2
            out *= (1 - vignette * np.clip(rr - 0.25, 0, 1.2))[:, :, None].astype(np.float32)
        if grain:
            rng = np.random.default_rng(seed)
            out += rng.standard_normal((H, W, 1)).astype(np.float32) * grain * (0.2 + out.mean(2, keepdims=True))
        return (np.clip(out, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)


def flow(P, t, amp=0.3, freq=0.05, speed=0.4, seed=0):
    """Dérive douce et organique des particules (pseudo-bruit à base de sinus) : la matière « respire »."""
    ph = np.array([1.3, 2.7, 0.6]) + seed
    X = P * freq
    d = np.stack([np.sin(X[:, 1] * 1.7 + t * speed + ph[0]) + np.sin(X[:, 2] * 2.3 - t * speed * 0.7),
                  np.sin(X[:, 2] * 1.9 + t * speed * 0.8 + ph[1]) + np.sin(X[:, 0] * 2.1 + t * speed * 0.5),
                  np.sin(X[:, 0] * 1.5 - t * speed * 0.6 + ph[2]) + np.sin(X[:, 1] * 2.6 + t * speed * 0.9)], 1)
    return P + d * (amp * 0.5)


def twinkle(n, t, frac=0.02, seed=3, power=10, gain=4.0):
    """Multiplicateur d'éclat : une petite fraction de points scintille."""
    g = np.random.default_rng(seed)
    m = g.random(n) < frac
    ph = g.uniform(0, 6.28, n)
    sp = g.uniform(1.5, 3.5, n)
    return (1.0 + m * gain * np.maximum(0, np.sin(ph + t * sp)) ** power).astype(np.float32)


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
