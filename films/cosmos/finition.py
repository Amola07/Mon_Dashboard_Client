"""Finition « photo spatiale » : exposition, courbe filmique, saturation, halo des hautes lumières, grain."""
import numpy as np
import skia

from films.trait.espace import blur_add, post
from films.trait.trait import H, W


def grade(lin, exposure=1.3, sat=1.35, contrast=1.08, lift=0.0):
    x = lin * exposure
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = lum + (x - lum) * sat                              # saturation avant compression
    x = np.maximum(x, 0)
    y = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
    y = np.clip(y, 0, 1)
    y = np.clip((y - 0.5) * contrast + 0.5 + lift, 0, 1)
    return y ** (1 / 2.2)


def to_image(a):
    rgba = np.empty(a.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    rgba[..., 3] = 255
    return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)


def compose(c, lin, t, exposure=1.3, sat=1.35, bloom=0.5, grain=0.045, aberration=0.8):
    """lin : image linéaire (h, w, 3) de n'importe quelle taille → toile 1080×1920 finie."""
    h, w = lin.shape[:2]
    base = to_image(grade(lin, exposure, sat))
    bright = to_image(grade(np.maximum(lin * exposure - 0.7, 0), 1.0, sat))
    c.clear(skia.ColorBLACK)
    c.save()
    c.scale(W / w, H / h)
    c.drawImage(base, 0, 0, skia.SamplingOptions(skia.CubicResampler.Mitchell()))
    c.restore()
    big = skia.Surface(W, H)
    bc = big.getCanvas()
    bc.clear(skia.ColorBLACK)
    bc.scale(W / w, H / h)
    bc.drawImage(bright, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
    bimg = big.makeImageSnapshot()
    for sig, al in ((50, 0.6 * bloom), (14, 0.7 * bloom), (4, 0.5 * bloom)):
        blur_add(c, bimg, sig, al)
    post(c, t, aberration=aberration, grain=grain)
