"""Mandelbulb en lancer de rayons (Numba) : forme fractale 3D qui respire, caméra en orbite lente, éclairage de
cinéma (soleil + ciel, ombres douces, occlusion ambiante, lueur des bords, brume), couleurs par « piège d'orbite ».

    python -m films.beaute.mandelbulb output/mandelbulb.mp4 [largeur] [secondes]
"""
import math
import subprocess
import sys
import time

import numpy as np
from numba import njit, prange

FPS = 30


@njit(cache=True, fastmath=True)
def de(px, py, pz, power):
    """Distance estimée au Mandelbulb + piège d'orbite (distance minimale à l'origine, et à un plan)."""
    zx, zy, zz = px, py, pz
    dr = 1.0
    r = 0.0
    trap = 1e9
    trap2 = 1e9
    for i in range(10):
        r = math.sqrt(zx * zx + zy * zy + zz * zz)
        if r > 2.0:
            break
        trap = min(trap, r)
        trap2 = min(trap2, abs(zy))
        th = math.acos(min(1.0, max(-1.0, zz / (r + 1e-12))))
        ph = math.atan2(zy, zx)
        dr = r ** (power - 1.0) * power * dr + 1.0
        zr = r ** power
        th *= power
        ph *= power
        st = math.sin(th)
        zx = zr * st * math.cos(ph) + px
        zy = zr * st * math.sin(ph) + py
        zz = zr * math.cos(th) + pz
    return 0.5 * math.log(r + 1e-12) * r / dr, trap, trap2


@njit(cache=True, fastmath=True)
def palette(t, out):
    """Or chaud dans les reliefs, bleu-vert profond dans les creux, une pointe de corail entre les deux."""
    t = min(1.0, max(0.0, t))
    if t < 0.5:
        u = t / 0.5
        c0, c1 = (0.03, 0.22, 0.30), (0.85, 0.32, 0.22)
    else:
        u = (t - 0.5) / 0.5
        c0, c1 = (0.85, 0.32, 0.22), (1.0, 0.78, 0.40)
    u = u * u * (3 - 2 * u)
    out[0] = c0[0] + (c1[0] - c0[0]) * u
    out[1] = c0[1] + (c1[1] - c0[1]) * u
    out[2] = c0[2] + (c1[2] - c0[2]) * u


@njit(parallel=True, cache=True, fastmath=True)
def render(W, H, cam, look, fov, power, sun, img):
    fx, fy, fz = look[0] - cam[0], look[1] - cam[1], look[2] - cam[2]
    n = math.sqrt(fx * fx + fy * fy + fz * fz)
    fx, fy, fz = fx / n, fy / n, fz / n
    # repère caméra (haut = +z)
    rx, ry, rz = fy * 1.0 - fz * 0.0, fz * 0.0 - fx * 1.0, 0.0
    rx, ry, rz = fy, -fx, 0.0
    n = math.sqrt(rx * rx + ry * ry) + 1e-9
    rx, ry = rx / n, ry / n
    ux, uy, uz = ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx
    for j in prange(H):
        col = np.zeros(3)
        alb = np.zeros(3)
        for i in range(W):
            acc0 = acc1 = acc2 = 0.0
            for s in range(2):                                   # 2 échantillons (anticrénelage diagonal)
                ox = (s * 0.5 - 0.25)
                u = ((i + 0.5 + ox) / W * 2 - 1) * fov * W / H
                v = -((j + 0.5 + ox) / H * 2 - 1) * fov
                dx = fx + u * rx + v * ux
                dy = fy + u * ry + v * uy
                dz = fz + u * rz + v * uz
                n = math.sqrt(dx * dx + dy * dy + dz * dz)
                dx, dy, dz = dx / n, dy / n, dz / n
                # fond : dégradé + halo du soleil
                sd = max(0.0, dx * sun[0] + dy * sun[1] + dz * sun[2])
                bg0 = 0.002 + 0.006 * (1 - v) + 0.5 * sd ** 30
                bg1 = 0.004 + 0.009 * (1 - v) + 0.32 * sd ** 30
                bg2 = 0.010 + 0.022 * (1 - v) + 0.16 * sd ** 30
                # marche du rayon (intersection avec la sphère englobante d'abord)
                t = 0.0
                b = cam[0] * dx + cam[1] * dy + cam[2] * dz
                c = cam[0] ** 2 + cam[1] ** 2 + cam[2] ** 2 - 1.3 * 1.3
                disc = b * b - c
                hit = False
                steps = 0
                trap = 0.0
                trap2 = 0.0
                if disc > 0:
                    t = max(0.0, -b - math.sqrt(disc))
                    tmax = -b + math.sqrt(disc)
                    for k in range(220):
                        px, py, pz = cam[0] + dx * t, cam[1] + dy * t, cam[2] + dz * t
                        d, trap, trap2 = de(px, py, pz, power)
                        steps = k
                        eps = 0.00035 * t + 0.00008
                        if d < eps:
                            hit = True
                            break
                        t += d * 0.9
                        if t > tmax:
                            break
                glow = steps / 220.0
                if not hit:
                    acc0 += bg0 + 0.55 * glow ** 3 * 1.0
                    acc1 += bg1 + 0.55 * glow ** 3 * 0.62
                    acc2 += bg2 + 0.55 * glow ** 3 * 0.35
                    continue
                px, py, pz = cam[0] + dx * t, cam[1] + dy * t, cam[2] + dz * t
                # normale (tétraèdre)
                e = 0.0005 * (1 + t)
                d1, _, _ = de(px + e, py - e, pz - e, power)
                d2, _, _ = de(px - e, py - e, pz + e, power)
                d3, _, _ = de(px - e, py + e, pz - e, power)
                d4, _, _ = de(px + e, py + e, pz + e, power)
                nx = d1 - d2 - d3 + d4
                ny = -d1 - d2 + d3 + d4
                nz = -d1 + d2 - d3 + d4
                nn = math.sqrt(nx * nx + ny * ny + nz * nz) + 1e-12
                nx, ny, nz = nx / nn, ny / nn, nz / nn
                # occlusion ambiante
                ao = 0.0
                w = 1.0
                for k in range(1, 6):
                    h = 0.012 * k
                    dd, _, _ = de(px + nx * h, py + ny * h, pz + nz * h, power)
                    ao += w * (h - dd)
                    w *= 0.6
                ao = max(0.0, 1.0 - 9.0 * ao)
                # ombre douce vers le soleil
                sh = 1.0
                ts = 0.004
                for k in range(48):
                    dd, _, _ = de(px + sun[0] * ts, py + sun[1] * ts, pz + sun[2] * ts, power)
                    sh = min(sh, 10.0 * dd / ts)
                    if sh < 0.01:
                        break
                    ts += max(dd, 0.004)
                    if ts > 2.0:
                        break
                sh = max(0.0, sh)
                # couleur de surface
                palette((trap - 0.55) * 1.6 + 0.35 * ao, alb)
                dif = max(0.0, nx * sun[0] + ny * sun[1] + nz * sun[2])
                sky = 0.5 + 0.5 * nz
                hx, hy, hz = sun[0] - dx, sun[1] - dy, sun[2] - dz
                hn = math.sqrt(hx * hx + hy * hy + hz * hz) + 1e-12
                spec = max(0.0, (nx * hx + ny * hy + nz * hz) / hn) ** 40 * sh
                fres = (1 + nx * dx + ny * dy + nz * dz) ** 3
                for q in range(3):
                    sunc = (1.0, 0.82, 0.6)[q]
                    skyc = (0.25, 0.35, 0.6)[q]
                    col[q] = alb[q] * (2.6 * dif * sh * sunc + 0.18 * sky * ao * skyc + 0.04 * ao) \
                        + 0.8 * spec * sunc + 0.55 * fres * ao * (0.5, 0.75, 1.0)[q]
                # brume légère
                fog = math.exp(-0.25 * max(0.0, t - 1.5))
                acc0 += col[0] * fog + bg0 * (1 - fog)
                acc1 += col[1] * fog + bg1 * (1 - fog)
                acc2 += col[2] * fog + bg2 * (1 - fog)
            img[j, i, 0] = acc0 * 0.5
            img[j, i, 1] = acc1 * 0.5
            img[j, i, 2] = acc2 * 0.5


def tonemap(img):
    x = img * 1.15
    x = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)          # ACES
    x = np.clip(x, 0, 1) ** (1 / 2.2)
    return (x * 255).astype(np.uint8)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/mandelbulb.mp4"
    W = int(sys.argv[2]) if len(sys.argv) > 2 else 720
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
    H = W * 16 // 9
    img = np.zeros((H, W, 3), np.float64)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264",
                           "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = int(dur * FPS)
    t0 = time.time()
    for f in range(n):
        u = f / n
        ang = 0.6 + 2 * math.pi * 0.22 * u                          # orbite lente
        rad = 3.15 - 0.75 * (0.5 - 0.5 * math.cos(math.pi * u))     # on s'approche lentement
        cam = np.array([rad * math.cos(ang), rad * math.sin(ang), 0.55 + 0.35 * math.sin(math.pi * u)])
        look = np.array([0.0, 0.0, 0.05])
        power = 8.0 + 1.6 * (0.5 - 0.5 * math.cos(2 * math.pi * u))   # la forme respire
        sa = ang + 1.1
        sun = np.array([math.cos(sa) * 0.6, math.sin(sa) * 0.6, 0.55])
        sun /= np.linalg.norm(sun)
        render(W, H, cam, look, 0.62, power, sun, img)
        ff.stdin.write(tonemap(img).tobytes())
        if f % 30 == 0:
            el = time.time() - t0
            print(f"{f}/{n}  {el / (f + 1):.2f} s/image", flush=True)
    ff.stdin.close()
    ff.wait()
    print("OK", out)


if __name__ == "__main__":
    main()
