"""Nébuleuses volumétriques (Numba) : un vrai nuage de gaz traversé par la lumière, pas un dessin.

Densité : deux volumes de bruit périodiques précalculés (spectre en 1/f, par FFT) lus à plusieurs échelles,
avec déformation du domaine (des volutes, des piliers, des filaments). Rendu : lancer de rayons avant → arrière,
émission + absorption, couleur selon un champ « d'ionisation », éclairage par quelques étoiles enfouies
(cœurs brillants qui illuminent le gaz autour), et étoiles de fond.
"""
import functools
import math

import numpy as np
from numba import njit, prange

N = 128


@functools.lru_cache(4)
def noise_volume(seed=1, beta=3.3, n=N):
    """Bruit 3D périodique de spectre 1/f^β (β ≈ 3 : nuageux), normalisé dans [0, 1]."""
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(n)
    k = np.sqrt(f[:, None, None] ** 2 + f[None, :, None] ** 2 + f[None, None, :] ** 2)
    k[0, 0, 0] = 1.0
    spec = np.fft.fftn(rng.standard_normal((n, n, n))) / k ** (beta / 2)
    spec[0, 0, 0] = 0
    v = np.real(np.fft.ifftn(spec))
    v = (v - v.mean()) / v.std()
    return np.ascontiguousarray((0.5 + 0.18 * v).clip(0, 1).astype(np.float32))


@njit(cache=True, fastmath=True)
def _tri(V, x, y, z):
    n = V.shape[0]
    x -= math.floor(x / n) * n
    y -= math.floor(y / n) * n
    z -= math.floor(z / n) * n
    ix, iy, iz = int(x), int(y), int(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    ix %= n
    iy %= n
    iz %= n
    jx, jy, jz = (ix + 1) % n, (iy + 1) % n, (iz + 1) % n
    c00 = V[ix, iy, iz] + (V[jx, iy, iz] - V[ix, iy, iz]) * fx
    c10 = V[ix, jy, iz] + (V[jx, jy, iz] - V[ix, jy, iz]) * fx
    c01 = V[ix, iy, jz] + (V[jx, iy, jz] - V[ix, iy, jz]) * fx
    c11 = V[ix, jy, jz] + (V[jx, jy, jz] - V[ix, jy, jz]) * fx
    c0 = c00 + (c10 - c00) * fy
    c1 = c01 + (c11 - c01) * fy
    return c0 + (c1 - c0) * fz


@njit(cache=True, fastmath=True)
def _hash3(i, j, k):
    h = (i * 73856093) ^ (j * 19349663) ^ (k * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777216.0


@njit(cache=True, fastmath=True)
def density(A, B, x, y, z, P, blobs):
    """Masses de gaz : des ellipsoïdes (blobs : cx, cy, cz, rx, ry, rz) dont la surface est sculptée par du bruit
    déformé (volutes, piliers, filaments). P : échelle, déformation, seuil, contraste, temps, crêtes, …"""
    sc, warp, thr, con, t, ridge = P[0], P[1], P[2], P[3], P[4], P[5]
    # distance (douce) à la masse la plus proche, en unités de rayon
    sd = 1e9
    acc = 0.0
    for q in range(blobs.shape[0]):
        ex = (x - blobs[q, 0]) / blobs[q, 3]
        ey = (y - blobs[q, 1]) / blobs[q, 4]
        ez = (z - blobs[q, 2]) / blobs[q, 5]
        acc += math.exp(-4.0 * (math.sqrt(ex * ex + ey * ey + ez * ez) - 1.0))
    sd = -math.log(acc + 1e-9) / 4.0                   # union lisse
    if sd > 0.9:
        return 0.0
    wx = _tri(B, x * sc * 0.5 + 17.0, y * sc * 0.5, z * sc * 0.5 + t) - 0.5
    wy = _tri(B, x * sc * 0.5, y * sc * 0.5 + 31.0, z * sc * 0.5 - t) - 0.5
    wz = _tri(B, x * sc * 0.5 + 5.0, y * sc * 0.5 + 9.0, z * sc * 0.5) - 0.5
    qx, qy, qz = x + warp * wx, y + warp * wy, z + warp * wz
    big = _tri(A, qx * sc, qy * sc, qz * sc)
    mid = _tri(A, qx * sc * 2.9 + 40, qy * sc * 2.9, qz * sc * 2.9)
    fine2 = _tri(A, qx * sc * 21.0 + 3, qy * sc * 21.0, qz * sc * 21.0 + 11)
    fine = _tri(B, qx * sc * 8.0, qy * sc * 8.0 + 7, qz * sc * 8.0)
    r = 1.0 - abs(2.0 * mid - 1.0)
    n = (big - 0.5) * 1.2 + 0.45 * (mid - 0.5) + ridge * 0.3 * (r * r - 0.45) + 0.2 * (fine - 0.5) + 0.1 * (fine2 - 0.5)
    d = (n * P[11] - sd - thr) * con
    return max(0.0, d)


@njit(parallel=True, cache=True, fastmath=True)
def render(out, A, B, cam, fwd, right, up, tan_half, P, pal, lights, blobs, n_steps, t_near, t_far, star_k):
    """Rayon avant → arrière à pas réguliers (avec décalage aléatoire contre les bandes).
    pal : (4, 3) couleurs d'émission ; lights : (k, 7) x, y, z, rayon, r, g, b."""
    Hh, Ww = out.shape[0], out.shape[1]
    aspect = Ww / Hh
    dt = (t_far - t_near) / n_steps
    for j in prange(Hh):
        for i in range(Ww):
            sx = (2.0 * (i + 0.5) / Ww - 1.0) * tan_half * aspect
            sy = (1.0 - 2.0 * (j + 0.5) / Hh) * tan_half
            dx = fwd[0] + sx * right[0] + sy * up[0]
            dy = fwd[1] + sx * right[1] + sy * up[1]
            dz = fwd[2] + sx * right[2] + sy * up[2]
            nn = math.sqrt(dx * dx + dy * dy + dz * dz)
            dx /= nn
            dy /= nn
            dz /= nn
            cr = 0.0
            cg = 0.0
            cb = 0.0
            T = 1.0
            jit = _hash3(i, j, 7) * dt * 0.8
            s = t_near + jit
            for _ in range(n_steps):
                x = cam[0] + dx * s
                y = cam[1] + dy * s
                z = cam[2] + dz * s
                d = density(A, B, x, y, z, P, blobs)
                if d > 0.0:
                    # couleur : champ d'ionisation lent → mélange de la palette
                    ion = _tri(B, x * P[0] * 0.35 + 70, y * P[0] * 0.35, z * P[0] * 0.35 + 3)
                    u = min(0.999, max(0.0, (ion - 0.3) * 2.5)) * 3.0
                    k = int(u)
                    f = u - k
                    er = pal[k, 0] + (pal[k + 1, 0] - pal[k, 0]) * f
                    eg = pal[k, 1] + (pal[k + 1, 1] - pal[k, 1]) * f
                    eb = pal[k, 2] + (pal[k + 1, 2] - pal[k, 2]) * f
                    # éclairage par les étoiles enfouies (le gaz près d'elles s'allume)
                    lr = 0.0
                    lg = 0.0
                    lb = 0.0
                    for q in range(lights.shape[0]):
                        ex = x - lights[q, 0]
                        ey = y - lights[q, 1]
                        ez = z - lights[q, 2]
                        w = lights[q, 3] * lights[q, 3] / (ex * ex + ey * ey + ez * ez + 0.02)
                        lr += w * lights[q, 4]
                        lg += w * lights[q, 5]
                        lb += w * lights[q, 6]
                    # relief : on compare la densité avec un point décalé vers la lumière principale
                    dl = density(A, B, x + P[7] * 0.12, y + P[8] * 0.12, z + P[9] * 0.12, P, blobs)
                    diff = max(0.0, (d - dl) * 4.0)
                    thin = math.exp(-d * 1.6)                    # gaz fin : il luit ; gaz dense : poussière sombre
                    glow = P[10] * (0.25 + 1.6 * diff) * (0.25 + thin)
                    dust = 1.0 - thin
                    a = 1.0 - math.exp(-d * P[6] * dt)
                    cr += T * a * (glow * er * (1.0 - 0.75 * dust) + lr * (0.15 + diff) * 0.35 + dust * 0.012)
                    cg += T * a * (glow * eg * (1.0 - 0.8 * dust) + lg * (0.15 + diff) * 0.35 + dust * 0.006)
                    cb += T * a * (glow * eb * (1.0 - 0.8 * dust) + lb * (0.15 + diff) * 0.35 + dust * 0.004)
                    T *= 1.0 - a
                    if T < 0.01:
                        break
                s += dt
            # étoiles lointaines derrière le gaz, et une faible lueur de fond colorée
            if T > 0.01:
                hz = _tri(B, dx * 30 + 200, dy * 30, dz * 30)
                cr += T * 0.010 * hz * pal[2, 0]
                cg += T * 0.010 * hz * pal[2, 1]
                cb += T * 0.016 * hz * pal[0, 2]
                u2 = math.atan2(dz, dx) * star_k
                v2 = math.asin(max(-1.0, min(1.0, dy))) * star_k
                ix, iy = math.floor(u2), math.floor(v2)
                for ox in range(-1, 2):
                    for oy in range(-1, 2):
                        cx, cy = int(ix) + ox, int(iy) + oy
                        if _hash3(cx, cy, 1) < 0.28:
                            px = cx + _hash3(cx, cy, 2)
                            py = cy + _hash3(cx, cy, 3)
                            d2 = (u2 - px) ** 2 + (v2 - py) ** 2
                            br = _hash3(cx, cy, 4) ** 7 * 9.0 + 0.12
                            w = br * math.exp(-d2 / 0.006) * T
                            tint = _hash3(cx, cy, 5)
                            cr += w * (0.8 + 0.4 * tint)
                            cg += w * 0.9
                            cb += w * (1.2 - 0.4 * tint)
            # étoiles enfouies elles-mêmes (cœurs éblouissants)
            for q in range(lights.shape[0]):
                ex = lights[q, 0] - cam[0]
                ey = lights[q, 1] - cam[1]
                ez = lights[q, 2] - cam[2]
                dist = math.sqrt(ex * ex + ey * ey + ez * ez)
                c = (ex * dx + ey * dy + ez * dz) / dist
                if c > 0.9:
                    ang2 = 2.0 * (1.0 - c) * dist * dist
                    g = 0.004 * lights[q, 3] / (ang2 + 0.00025) * T
                    cr += g * lights[q, 4]
                    cg += g * lights[q, 5]
                    cb += g * lights[q, 6]
            out[j, i, 0] = cr
            out[j, i, 1] = cg
            out[j, i, 2] = cb


def basis(pos, target, roll=0.0):
    pos, target = np.asarray(pos, float), np.asarray(target, float)
    f = target - pos
    f /= np.linalg.norm(f)
    upw = np.array([0.0, 1.0, 0.0]) if abs(f[1]) < 0.99 else np.array([0.0, 0.0, 1.0])
    r = np.cross(f, upw)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    cr, sr = math.cos(roll), math.sin(roll)
    return f, r * cr + u * sr, -r * sr + u * cr


def nebula(w, h, pos, target, fov, params, pal, lights, blobs, steps=96, near=0.2, far=9.0, roll=0.0, seed=1):
    A = noise_volume(seed, 3.3)
    B = noise_volume(seed + 10, 2.8)
    f, r, u = basis(pos, target, roll)
    out = np.zeros((h, w, 3), np.float32)
    render(out, A, B, np.asarray(pos, float), f, r, u, math.tan(math.radians(fov) / 2),
           np.asarray(params, np.float64), np.asarray(pal, np.float64), np.asarray(lights, np.float64),
           np.asarray(blobs, np.float64), int(steps), float(near), float(far), 220.0)
    return out
