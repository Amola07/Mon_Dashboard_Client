"""Moteur « motion design 3D » du style trait lumineux.

Vraie caméra perspective, traits 3D dont l'épaisseur suit la distance, profondeur de champ par tranches de
flou (comme un objectif ouvert), particules en bokeh, halo, rayons de lumière, aberration chromatique,
grain et vignettage. Tout reste procédural (numpy + skia) et rapide : ≈ 0,3 à 0,6 s par image 1080×1920.
"""
import math

import numpy as np
import skia

from films.holo.holo import Camera
from films.trait.trait import H, W, draw_nebula, View

SIGMAS = (0.0, 1.6, 3.4, 6.0, 10.0, 16.0)           # flou de chaque tranche de profondeur (px)


def segs_from(lines):
    """Liste de polylignes 3D → segments (N, 2, 3)."""
    out = [np.stack([l[:-1], l[1:]], 1) for l in lines if len(l) >= 2]
    return np.concatenate(out) if out else np.zeros((0, 2, 3))


def lift(shape_pts2, starts, height_fn=None, plane="xz"):
    """Shape 2D (coordonnées unitaires) → polylignes 3D posées sur un plan, avec relief optionnel."""
    lines = []
    for i in range(len(starts) - 1):
        p = shape_pts2[starts[i]:starts[i + 1]]
        h = height_fn(p) if height_fn is not None else np.zeros(len(p))
        if plane == "xz":
            lines.append(np.stack([p[:, 0], h, p[:, 1]], 1))
        else:                                             # plan vertical face caméra (x, −y)
            lines.append(np.stack([p[:, 0], -p[:, 1], h], 1))
    return lines


class Lens:
    def __init__(self, focus=5.0, aperture=0.0, fog=(30.0, 60.0)):
        self.focus = focus                                 # distance nette (unités monde)
        self.aperture = aperture                           # 0 = tout net ; ≈ 20–60 = très ouvert
        self.fog = fog

    def coc(self, cam, z):
        """Diamètre du cercle de confusion en pixels."""
        return self.aperture * cam.focal / 1000 * np.abs(1.0 / np.maximum(z, 1e-3) - 1.0 / self.focus) * self.focus


class Scene:
    def __init__(self, cam, lens):
        self.cam = cam
        self.lens = lens
        self.batches = []
        self.points = []
        self.flat = []                                     # dessins 2D libres (fonction(canvas)) par tranche nette
        self.exposure = 1.0
        self.holes = []                                    # disques noirs 3D (pupille) : (centre, rayon, normale, a)

    def lines(self, segs, col, a=1.0, w=0.004, min_px=0.7):
        """segs : (N, 2, 3) ; w : épaisseur dans le monde (devient plus fine au loin)."""
        if a > 0.004 and len(segs):
            self.batches.append((np.asarray(segs, float), col, a, w, min_px))

    def polylines(self, lines, col, a=1.0, w=0.004, min_px=0.7):
        self.lines(segs_from(lines), col, a, w, min_px)

    def hole(self, center, radius, normal=(0, 1, 0), a=1.0):
        self.holes.append((np.asarray(center, float), radius, np.asarray(normal, float), a))

    def dust(self, pts, col, a=1.0, size=0.01):
        """Particules (N, 3) : de minuscules points nets, de grands disques doux quand elles sont floues."""
        if a > 0.004 and len(pts):
            self.points.append((np.asarray(pts, float), col, a, size))

    # -------------------------------------------------------------------------------------------- rendu
    def render(self, c, t, bg=True, rays=None, view2d=None, aberration=1.0, grain=0.05):
        cam, lens = self.cam, self.lens
        nb = len(SIGMAS)
        surf = [skia.Surface(W, H) for _ in range(nb)]
        for s in surf:
            s.getCanvas().clear(skia.ColorTRANSPARENT)
        groups = {}
        for segs, col, a, w, min_px in self.batches:
            P = segs.reshape(-1, 3)
            sc, z = cam.project(P)
            sc, z = sc.reshape(-1, 2, 2), z.reshape(-1, 2)
            ok = (z > 0.02).all(1)
            ok &= (np.abs(sc) < 6000).all((1, 2))
            if not ok.any():
                continue
            sc, z = sc[ok], z[ok].mean(1)
            px = w * cam.focal / z
            k = a * np.clip(px / min_px, 0.05, 1.0)        # sous le pixel : plus fin = plus transparent
            px = np.maximum(px, min_px)
            f0, f1 = lens.fog
            k *= np.clip(1 - (z - f0) / (f1 - f0), 0, 1)
            coc = lens.coc(cam, z) if lens.aperture > 0 else np.zeros_like(z)
            b = np.clip(np.searchsorted(SIGMAS, coc * 0.5), 0, nb - 1)
            k *= np.minimum(1.0, 1.0 + np.array(SIGMAS)[b] / 6.0)  # un trait flou s'étale : on compense un peu
            aq = np.clip((k * 10).round().astype(int), 0, 10)
            wq = np.clip((px * 2).round().astype(int), 1, 16)
            for key in set(zip(b.tolist(), aq.tolist(), wq.tolist())):
                if key[1] == 0:
                    continue
                m = (b == key[0]) & (aq == key[1]) & (wq == key[2])
                groups.setdefault((key, col), []).append(sc[m])
        for ((bi, aq, wq), col), arrs in groups.items():
            pts = np.concatenate(arrs).reshape(-1, 2)
            p = skia.Paint(AntiAlias=True, StrokeWidth=wq / 2, StrokeCap=skia.Paint.kRound_Cap,
                           Color=skia.Color(*[int(v) for v in col], int(255 * aq / 10)))
            surf[bi].getCanvas().drawPoints(skia.Canvas.kLines_PointMode,
                                            [skia.Point(float(x), float(y)) for x, y in pts], p)
        for pts, col, a, size in self.points:
            sc, z = cam.project(pts)
            ok = (z > 0.05) & (np.abs(sc) < 4000).all(1)
            sc, z = sc[ok], z[ok]
            r0 = np.maximum(size * cam.focal / z, 0.8)
            coc = lens.coc(cam, z) * 0.5 if lens.aperture > 0 else np.zeros_like(z)
            r = np.maximum(r0, coc)
            al = a * np.clip((r0 / r) ** 1.2, 0.04, 1) * np.clip(1 - (z - lens.fog[0]) / (lens.fog[1] - lens.fog[0]), 0, 1)
            cv = surf[0].getCanvas()
            for (x, y), rr, aa in zip(sc, r, al):
                if aa < 0.01:
                    continue
                cv.drawCircle(float(x), float(y), float(rr),
                              skia.Paint(AntiAlias=True, Color=skia.Color(*[int(v) for v in col], int(255 * min(1, aa)))))
                if rr > 6:                                 # liseré de bokeh
                    cv.drawCircle(float(x), float(y), float(rr) * 0.94,
                                  skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                                             Color=skia.Color(*[int(v) for v in col], int(160 * min(1, aa)))))
        for fn in self.flat:
            fn(surf[0].getCanvas())
        # ---- assemblage des tranches floues
        lines = skia.Surface(W, H)
        lc = lines.getCanvas()
        lc.clear(skia.ColorTRANSPARENT)
        used = {0} | {k[0][0] for k in groups}
        for bi, (s, sig) in enumerate(zip(surf, SIGMAS)):
            if bi not in used:
                continue
            blur_add(lc, s.makeImageSnapshot(), sig)
        img = tonemap(lines.makeImageSnapshot(), self.exposure)
        # ---- fond + halo + rayons
        if bg:
            draw_nebula(c, t, view2d or View(), 1.0)
        else:
            c.clear(skia.Color(2, 5, 14))
        for ctr, rad, nrm, a in self.holes:               # la pupille « mange » le fond
            n = nrm / np.linalg.norm(nrm)
            e1 = np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0])
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(n, e1)
            th = np.linspace(0, 2 * math.pi, 96)
            ring = ctr + rad * (np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2)
            sc2, z2 = self.cam.project(ring)
            if (z2 > 0.02).all():
                path = skia.Path()
                path.addPoly([skia.Point(float(x), float(y)) for x, y in sc2], True)
                c.drawPath(path, skia.Paint(AntiAlias=True, Color=skia.Color(1, 2, 8, int(245 * a)),
                                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
        for sig, al in ((34, 0.55), (10, 0.8), (2.5, 0.55), (0, 1.0)):
            blur_add(c, img, sig, al)
        if rays:
            god_rays(c, img, *rays)
        post(c, t, aberration, grain)


_TM = {}


def tonemap(img, exposure=1.0, knee=1.6):
    """Compression douce des hautes lumières en gardant la teinte : les zones très denses ne virent pas au blanc.
    (Table de 256 facteurs selon la composante la plus forte : rapide.)"""
    key = (round(exposure, 3), knee)
    if key not in _TM:
        m = np.arange(256) / 255.0 * exposure
        f = (1 - np.exp(-m * knee)) / (1 - math.exp(-knee))
        _TM[key] = (np.where(m > 1e-6, f / np.maximum(m, 1e-6), knee / (1 - math.exp(-knee))) * exposure).astype(np.float32)
    a = img.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    fac = _TM[key][a[..., :3].max(2)]
    out = a.copy()
    out[..., :3] = np.minimum(a[..., :3] * fac[..., None], 255).astype(np.uint8)
    out[..., 3] = np.maximum(a[..., 3], out[..., :3].max(2))
    return skia.Image.fromarray(out, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)


def blur_add(c, img, sigma, alpha=1.0):
    """Ajoute (mode additif) une copie floue de img. Le flou est calculé sur une copie réduite (rapide), puis
    agrandie : un flou est lisse, la perte de résolution ne se voit pas."""
    if sigma <= 0:
        p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
        p.setAlphaf(alpha)
        c.drawImage(img, 0, 0, skia.SamplingOptions(), p)
        return
    k = 2 if sigma < 6 else (4 if sigma < 20 else 8)
    small = skia.Surface(W // k, H // k)
    sc = small.getCanvas()
    sc.clear(skia.ColorTRANSPARENT)
    sc.save()
    sc.scale(1 / k, 1 / k)
    sc.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
    sc.restore()
    blurred = skia.Surface(W // k, H // k)
    bc = blurred.getCanvas()
    bc.clear(skia.ColorTRANSPARENT)
    bc.drawImage(small.makeImageSnapshot(), 0, 0, skia.SamplingOptions(),
                 skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma / k, sigma / k)))
    p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
    p.setAlphaf(alpha)
    c.save()
    c.scale(k, k)
    c.drawImage(blurred.makeImageSnapshot(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()


def god_rays(c, img, cx, cy, strength=0.5, length=0.35, n=10):
    """Rayons de lumière : copies floues de l'image agrandies depuis la source (flou radial)."""
    small = skia.Surface(W // 2, H // 2)
    sc_ = small.getCanvas()
    sc_.clear(skia.ColorTRANSPARENT)
    sc_.scale(0.5, 0.5)
    for i in range(n):
        s = 1 + length * (i + 1) / n
        sc_.save()
        sc_.translate(cx, cy)
        sc_.scale(s, s)
        sc_.translate(-cx, -cy)
        p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
        p.setAlphaf(strength * (1 - i / n) / n * 2)
        sc_.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
        sc_.restore()
    p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
    c.save()
    c.scale(2, 2)
    c.drawImage(small.makeImageSnapshot(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()


_GR = []


def post(c, t, aberration=1.0, grain=0.05):
    """Vignettage, aberration chromatique sur les bords, grain animé."""
    surf = c.getSurface()
    if aberration > 0 and surf is not None:
        img = surf.makeImageSnapshot()
        c.clear(skia.ColorBLACK)
        for mat, s in (([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], 1 + 0.0035 * aberration),
                       ([0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], 1.0),
                       ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0], 1 - 0.0035 * aberration)):
            c.save()
            c.translate(W / 2, H / 2)
            c.scale(s, s)
            c.translate(-W / 2, -H / 2)
            c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear),
                        skia.Paint(ColorFilter=skia.ColorFilters.Matrix(mat), BlendMode=skia.BlendMode.kPlus))
            c.restore()
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.66,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 60), skia.Color(0, 0, 0, 215)],
                                        [0.0, 0.58, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    if grain > 0:
        if not _GR:
            rng = np.random.default_rng(5)
            for _ in range(8):
                g = np.clip(128 + rng.normal(0, 1, (H // 2, W // 2)) * 70, 0, 255).astype(np.uint8)
                a = np.stack([g, g, g, np.full_like(g, 255)], 2)
                _GR.append(skia.Image.fromarray(np.ascontiguousarray(a), colorType=skia.kRGBA_8888_ColorType))
        p = skia.Paint(BlendMode=skia.BlendMode.kOverlay)
        p.setAlphaf(grain)
        c.save()
        c.scale(2, 2)
        c.drawImage(_GR[int(t * 24) % len(_GR)], 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
        c.restore()


def shake(t, amp, seed=0):
    """Tremblement de caméra doux (somme de sinus), en unités monde."""
    s = seed * 1.3
    return amp * np.array([math.sin(t * 13.1 + s) * 0.6 + math.sin(t * 29.3 + 2 * s) * 0.4,
                           math.sin(t * 11.7 + 1 + s) * 0.6 + math.sin(t * 31.9 + s) * 0.4,
                           math.sin(t * 9.1 + 2 + s)])


def cam_at(pos, target, fov=40.0, roll=0.0):
    return Camera(pos, target, fov, roll)
