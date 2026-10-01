"""Trou noir de Schwarzschild calculé rayon par rayon (Numba) : la lumière est courbée par la gravité.

Unités : rayon de l'horizon = 1. Pour chaque pixel, on lance un photon depuis la caméra et on intègre sa
trajectoire avec l'accélération effective a = −1,5·h²·x/r⁵ (h = |x × v|, conservé), qui reproduit exactement
les orbites de la lumière en relativité générale. On récolte :
  • le disque d'accrétion (traversé éventuellement plusieurs fois : images secondaires, anneau de photons),
    avec effet Doppler relativiste (un côté plus brillant et plus bleu) et décalage gravitationnel vers le rouge ;
  • le ciel (étoiles + voie lactée procédurales), vu à travers la lentille gravitationnelle ;
  • le noir de l'horizon.
"""
import math

import numpy as np
from numba import njit, prange

R_IN, R_OUT = 3.0, 13.0                                    # dernière orbite stable (3 rs) → bord extérieur


@njit(cache=True, fastmath=True)
def _hash(ix, iy, iz):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777216.0


@njit(cache=True, fastmath=True)
def _vnoise2(x, y):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    ix, iy = int(ix), int(iy)
    a = _hash(ix, iy, 7)
    b = _hash(ix + 1, iy, 7)
    c = _hash(ix, iy + 1, 7)
    d = _hash(ix + 1, iy + 1, 7)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


@njit(cache=True, fastmath=True)
def _vnoise3(x, y, z):
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    fz = fz * fz * (3 - 2 * fz)
    ix, iy, iz = int(ix), int(iy), int(iz)
    v000 = _hash(ix, iy, iz)
    v100 = _hash(ix + 1, iy, iz)
    v010 = _hash(ix, iy + 1, iz)
    v110 = _hash(ix + 1, iy + 1, iz)
    v001 = _hash(ix, iy, iz + 1)
    v101 = _hash(ix + 1, iy, iz + 1)
    v011 = _hash(ix, iy + 1, iz + 1)
    v111 = _hash(ix + 1, iy + 1, iz + 1)
    x00 = v000 + (v100 - v000) * fx
    x10 = v010 + (v110 - v010) * fx
    x01 = v001 + (v101 - v001) * fx
    x11 = v011 + (v111 - v011) * fx
    y0 = x00 + (x10 - x00) * fy
    y1 = x01 + (x11 - x01) * fy
    return y0 + (y1 - y0) * fz


@njit(cache=True, fastmath=True)
def _sky(dx, dy, dz, star_scale):
    """Ciel : voie lactée inclinée (bruit), nébuleuses bleu-violet, étoiles ponctuelles."""
    # bande galactique : autour du plan de normale n
    nx, ny, nz = 0.55, 0.42, 0.72
    s = dx * nx + dy * ny + dz * nz
    band = math.exp(-(s / 0.28) ** 2)
    n1 = 0.0
    amp = 1.0
    f = 2.0
    for _ in range(5):
        n1 += amp * _vnoise3(dx * f + 11.0, dy * f + 3.0, dz * f + 7.0)
        amp *= 0.5
        f *= 2.1
    n1 /= 1.94
    dust = max(0.0, n1 - 0.45) * 2.0
    milky = band * (0.35 + 0.9 * n1 * n1) * (1 - 0.7 * dust * band)
    neb = max(0.0, _vnoise3(dx * 1.3 + 40, dy * 1.3, dz * 1.3) - 0.55) * 1.6
    r = 0.04 * milky + 0.05 * neb * neb + 0.0008
    g = 0.045 * milky + 0.018 * neb * neb + 0.0012
    b = 0.075 * milky + 0.10 * neb * neb + 0.0035
    # étoiles : une par cellule d'une grille sur la sphère, au hasard
    u = math.atan2(dz, dx)
    v = math.asin(max(-1.0, min(1.0, dy)))
    k = star_scale
    gx, gy = u * k, v * k
    ix, iy = math.floor(gx), math.floor(gy)
    for ox in range(-1, 2):
        for oy in range(-1, 2):
            cx, cy = int(ix) + ox, int(iy) + oy
            p = _hash(cx, cy, 3)
            if p < 0.1 + 0.35 * band:
                sx = cx + _hash(cx, cy, 5)
                sy = cy + _hash(cx, cy, 9)
                ddx = (gx - sx) * math.cos(v)
                ddy = gy - sy
                d2 = ddx * ddx + ddy * ddy
                br = _hash(cx, cy, 13) ** 8 * 14.0 + 0.16
                w = br * math.exp(-d2 / 0.0035)
                tint = _hash(cx, cy, 17)
                r += w * (0.8 + 0.4 * tint)
                g += w * 0.9
                b += w * (1.25 - 0.4 * tint)
    return r, g, b


@njit(cache=True, fastmath=True)
def _blackbody(T):
    """Couleur approximative d'un corps noir, T normalisée (0,3 = rouge sombre … 1 = blanc … 2 = bleuté)."""
    r = min(1.0, max(0.0, 1.6 * T))
    g = min(1.0, max(0.0, 1.5 * T - 0.35)) ** 1.1
    b = min(1.0, max(0.0, 1.3 * T - 0.75)) ** 1.2
    return r, g * 0.92, b * 0.95


@njit(cache=True, fastmath=True)
def _disk(px, pz, rr, vx, vy, vz, t, spin):
    """Émission et opacité du disque au point (px, 0, pz) vu par un photon de direction (vx, vy, vz)."""
    phi = math.atan2(pz, px)
    omega = spin * math.sqrt(0.5 / (rr * rr * rr))         # vitesse angulaire képlérienne (M = 1/2)
    a = phi - omega * t * 6.0
    # filaments en spirale : bruit étiré le long des orbites
    n = 0.0
    amp = 1.0
    fr = 1.0
    for _ in range(4):
        n += amp * _vnoise2(rr * 2.2 * fr + 0.5 * math.sin(a * 2), (a * 3.0 + rr * 0.35) * fr * 1.6)
        amp *= 0.55
        fr *= 2.0
    n /= 1.87
    edge = min(1.0, (rr - R_IN) / 0.5) * min(1.0, (R_OUT - rr) / 4.0)
    gaps = 0.5 + 0.5 * math.sin(rr * 5.3 + 2.0 * _vnoise2(rr * 0.8, a * 0.7))   # anneaux et lacunes
    dens = edge * (0.06 + 1.7 * n * n * n) * (0.35 + 0.65 * gaps)
    # température : profil de Shakura–Sunyaev
    T = (R_IN / rr) ** 0.75 * (1.0 - math.sqrt(R_IN / rr) * 0.98) ** 0.25 * 1.75
    # Doppler relativiste : la matière tourne à β = √(M/r) ; on regarde dans la direction −v du photon
    beta = math.sqrt(0.5 / rr)
    ux, uz = -math.sin(phi) * spin, math.cos(phi) * spin
    cosang = -(ux * vx + uz * vz)
    gamma = 1.0 / math.sqrt(1 - beta * beta)
    D = 1.0 / (gamma * (1.0 - beta * cosang))
    grav = math.sqrt(max(0.0, 1.0 - 1.0 / rr))
    shift = D * grav
    cr, cg, cb = _blackbody(T * shift)
    inten = dens * shift ** 3.5 * T * 2.2
    return cr * inten, cg * inten, cb * inten, min(1.0, dens * 0.7)


@njit(parallel=True, cache=True, fastmath=True)
def render(out, cam, fwd, right, up, tan_half, t, spin, star_scale, max_steps):
    """out : (H, W, 3) float32, linéaire. cam : position ; fwd/right/up : base caméra ; tan_half : tan(fov/2)."""
    Hh, Ww = out.shape[0], out.shape[1]
    aspect = Ww / Hh
    for j in prange(Hh):
        for i in range(Ww):
            sx = (2.0 * (i + 0.5) / Ww - 1.0) * tan_half * aspect
            sy = (1.0 - 2.0 * (j + 0.5) / Hh) * tan_half
            dx = fwd[0] + sx * right[0] + sy * up[0]
            dy = fwd[1] + sx * right[1] + sy * up[1]
            dz = fwd[2] + sx * right[2] + sy * up[2]
            nn = math.sqrt(dx * dx + dy * dy + dz * dz)
            vx, vy, vz = dx / nn, dy / nn, dz / nn
            x, y, z = cam[0], cam[1], cam[2]
            hx = y * vz - z * vy
            hy = z * vx - x * vz
            hz = x * vy - y * vx
            h2 = hx * hx + hy * hy + hz * hz
            cr = 0.0
            cg = 0.0
            cb = 0.0
            trans = 1.0
            hit = False
            for _ in range(max_steps):
                r2 = x * x + y * y + z * z
                r = math.sqrt(r2)
                dt = min(0.6, max(0.012, 0.07 * (r - 0.6)))
                # Verlet : demi-pas de vitesse, pas de position, demi-pas de vitesse
                k = -1.5 * h2 / (r2 * r2 * r)
                vx += 0.5 * dt * k * x
                vy += 0.5 * dt * k * y
                vz += 0.5 * dt * k * z
                nx, ny, nz = x + dt * vx, y + dt * vy, z + dt * vz
                if y * ny < 0.0:                           # traverse le plan du disque
                    f = y / (y - ny)
                    px, pz = x + f * (nx - x), z + f * (nz - z)
                    rr = math.sqrt(px * px + pz * pz)
                    if R_IN <= rr <= R_OUT:
                        vn = math.sqrt(vx * vx + vy * vy + vz * vz)
                        er, eg, eb, al = _disk(px, pz, rr, vx / vn, vy / vn, vz / vn, t, spin)
                        cr += trans * er
                        cg += trans * eg
                        cb += trans * eb
                        trans *= 1.0 - al
                        if trans < 0.02:
                            hit = True
                            break
                x, y, z = nx, ny, nz
                r2 = x * x + y * y + z * z
                r = math.sqrt(r2)
                k = -1.5 * h2 / (r2 * r2 * r)
                vx += 0.5 * dt * k * x
                vy += 0.5 * dt * k * y
                vz += 0.5 * dt * k * z
                if r < 1.0:                                # horizon : plus rien ne revient
                    hit = True
                    break
                if r > 80.0 and (x * vx + y * vy + z * vz) > 0:
                    vn = math.sqrt(vx * vx + vy * vy + vz * vz)
                    sr, sg, sb = _sky(vx / vn, vy / vn, vz / vn, star_scale)
                    cr += trans * sr
                    cg += trans * sg
                    cb += trans * sb
                    hit = True
                    break
            if not hit:                                    # photon presque piégé (anneau de photons) : noir
                pass
            out[j, i, 0] = cr
            out[j, i, 1] = cg
            out[j, i, 2] = cb


def camera_basis(pos, target, roll=0.0):
    pos, target = np.asarray(pos, float), np.asarray(target, float)
    f = target - pos
    f /= np.linalg.norm(f)
    upw = np.array([0.0, 1.0, 0.0])
    if abs(f @ upw) > 0.999:
        upw = np.array([0.0, 0.0, 1.0])
    r = np.cross(f, upw)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    cr, sr = math.cos(roll), math.sin(roll)
    return f, r * cr + u * sr, -r * sr + u * cr


def trace(w, h, pos, target, fov_deg, t, roll=0.0, spin=1.0, star_scale=260.0, max_steps=900):
    f, r, u = camera_basis(pos, target, roll)
    out = np.zeros((h, w, 3), np.float32)
    render(out, np.asarray(pos, float), f, r, u, math.tan(math.radians(fov_deg) / 2), float(t), float(spin),
           float(star_scale), int(max_steps))
    return out
