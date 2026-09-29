"""Anime « motion comic » : anime une illustration fixe grâce à sa carte de profondeur.

La caméra avance et glisse lentement : les plans proches bougent plus que le fond (parallaxe 2.5D).
Par-dessus : étoiles qui scintillent, poussières lumineuses, halo doux.

    python -m films.anime.motion image.png profondeur.png sortie.mp4 [secondes]
"""
import math
import subprocess
import sys

import cv2
import numpy as np

W, H, FPS = 1080, 1920, 60


def cover(img, w=W, h=H):
    """Recadre et agrandit l'image pour remplir le format vertical."""
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    img = cv2.resize(img, (int(iw * s + 0.5), int(ih * s + 0.5)), interpolation=cv2.INTER_LANCZOS4)
    y0, x0 = (img.shape[0] - h) // 2, (img.shape[1] - w) // 2
    return img[y0:y0 + h, x0:x0 + w]


def render(image_path, depth_path, out, seconds=8.0, strength=38.0, zoom=0.07, seed=1):
    img = cover(cv2.imread(image_path, cv2.IMREAD_COLOR)).astype(np.float32) / 255
    depth = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
    depth = cover(depth).astype(np.float32) / 255              # 1 = proche, 0 = lointain
    depth = cv2.GaussianBlur(depth, (0, 0), 6)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    # étoiles : points lumineux déjà présents dans le fond, que l'on fait scintiller
    lum = img.mean(axis=2)
    far = depth < 0.35
    peaks = (lum > 0.75) & far & (cv2.dilate(lum, np.ones((5, 5))) == lum)
    sy, sx = np.nonzero(peaks)
    rng = np.random.default_rng(seed)
    keep = rng.random(len(sx)) < min(1.0, 400 / max(1, len(sx)))
    sx, sy = sx[keep], sy[keep]
    ph = rng.uniform(0, 6.28, len(sx))
    motes = np.column_stack([rng.uniform(0, W, 70), rng.uniform(0, H, 70), rng.uniform(1.5, 4.5, 70),
                             rng.uniform(0, 6.28, 70), rng.uniform(8, 30, 70)])
    ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(seconds * FPS)
    for f in range(n):
        t = f / FPS
        u = t / seconds
        e = u * u * (3 - 2 * u)
        cam_x = math.sin(u * math.pi * 0.9) * 1.0 - 0.5         # glisse latérale
        cam_z = e                                                # avance
        k = 1 + zoom * cam_z * (0.4 + depth)                     # les plans proches grossissent plus
        mx = (xs - W / 2) / k + W / 2 - cam_x * strength * depth
        my = (ys - H * 0.55) / k + H * 0.55 - 0.3 * strength * depth * cam_z
        frame = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # scintillement des étoiles
        tw = 0.5 + 0.5 * np.sin(ph + t * 2.2)
        star = np.zeros((H, W), np.float32)
        px = np.clip(((sx - W / 2) * (1 + zoom * cam_z * 0.4) + W / 2 + cam_x * strength * 0.1).astype(int), 0, W - 1)
        py = np.clip(((sy - H * 0.55) * (1 + zoom * cam_z * 0.4) + H * 0.55).astype(int), 0, H - 1)
        star[py, px] = tw * 1.5
        star = cv2.GaussianBlur(star, (0, 0), 2.2) * 6
        frame += star[..., None] * np.array([1.0, 0.95, 0.85], np.float32)
        # poussières lumineuses au premier plan
        glow = np.zeros((H, W), np.float32)
        for x, y, s, p, sp in motes:
            yy = int((y - t * sp) % H)
            xx = int(x + 20 * math.sin(p + t * 0.5) - cam_x * strength * 1.2) % W
            glow[yy, xx] += s * (0.5 + 0.5 * math.sin(p + t * 1.3))
        glow = cv2.GaussianBlur(glow, (0, 0), 5) * 25
        frame += glow[..., None] * np.array([1.0, 0.85, 0.6], np.float32)
        # halo doux (bloom) sur les zones claires
        bright = np.clip(frame - 0.7, 0, None)
        frame += cv2.GaussianBlur(bright, (0, 0), 18) * 0.8
        # vignettage
        frame *= (1 - 0.35 * (((xs - W / 2) / W) ** 2 + ((ys - H / 2) / H) ** 2) * 2)[..., None]
        ff.stdin.write((np.clip(frame, 0, 1) * 255).astype(np.uint8).tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 8.0)
