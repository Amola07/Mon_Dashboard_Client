"""Rendu « hologramme » (plan d'architecte lumineux) : fils de fer cyan en vraie 3D, halo, accent rouge.

Principe : chaque image est dessinée dans deux calques (cyan / rouge) en traits fins, puis composée sur un fond bleu
nuit étoilé avec deux halos (flou serré + flou large) en mode additif.
"""
import math
import os

import numpy as np
import skia

W, H = 1080, 1920
CYAN = (90, 170, 255)
CYAN_HI = (190, 230, 255)
RED = (255, 60, 70)
_FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
F_MED = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-Medium.ttf"))


# ------------------------------------------------------------------------------------------------ caméra
class Camera:
    def __init__(self, pos, target, fov=40.0, roll=0.0):
        self.pos = np.asarray(pos, float)
        f = np.asarray(target, float) - self.pos
        f /= np.linalg.norm(f)
        up = np.array([0.0, 1.0, 0.0])
        if abs(np.dot(f, up)) > 0.999:
            up = np.array([0.0, 0.0, -1.0])
        r = np.cross(f, up)
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        cr, sr = math.cos(roll), math.sin(roll)
        self.r, self.u = r * cr + u * sr, -r * sr + u * cr
        self.f = f
        self.focal = (H / 2) / math.tan(math.radians(fov) / 2)

    def project(self, p):
        """p : (N, 3) → (N, 2) écran, profondeur (N,)."""
        d = np.asarray(p, float) - self.pos
        z = d @ self.f
        x = d @ self.r
        y = d @ self.u
        zz = np.maximum(z, 1e-4)
        return np.stack([W / 2 + self.focal * x / zz, H / 2 - self.focal * y / zz], 1), z


def lerp(a, b, u):
    return a + (b - a) * u


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


# ------------------------------------------------------------------------------------------------ dessin
class Frame:
    """Une image : calques cyan et rouge, puis composition."""

    def __init__(self, cam):
        self.cam = cam
        self.layers = {"c": skia.Surface(W, H), "r": skia.Surface(W, H)}
        for s in self.layers.values():
            s.getCanvas().clear(skia.ColorTRANSPARENT)

    def poly(self, pts, col=CYAN, a=1.0, w=2.2, layer="c", closed=False, fade_depth=None):
        """Polyligne 3D (coupée derrière la caméra), avec atténuation optionnelle selon la profondeur."""
        if a <= 0.004:
            return
        pts = np.asarray(pts, float)
        if closed:
            pts = np.concatenate([pts, pts[:1]])
        sc, z = self.cam.project(pts)
        c = self.layers[layer].getCanvas()
        p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                       StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
        if fade_depth is None:
            p.setColor(skia.Color(*[int(v) for v in col], int(255 * min(1, a))))
            path = skia.Path()
            pen = False
            for (x, y), zz in zip(sc, z):
                if zz > 0.05 and abs(x) < 8000 and abs(y) < 8000:
                    if pen:
                        path.lineTo(x, y)
                    else:
                        path.moveTo(x, y)
                    pen = True
                else:
                    pen = False
            c.drawPath(path, p)
        else:
            for i in range(len(sc) - 1):
                if z[i] <= 0.05 or z[i + 1] <= 0.05:
                    continue
                k = a * max(0.0, 1 - (0.5 * (z[i] + z[i + 1]) - fade_depth[0]) / (fade_depth[1] - fade_depth[0]))
                if k <= 0.004:
                    continue
                p.setColor(skia.Color(*[int(v) for v in col], int(255 * min(1, k))))
                c.drawLine(*sc[i], *sc[i + 1], p)

    def dot(self, p, col=CYAN, a=1.0, r=7.0, layer="c"):
        sc, z = self.cam.project(np.asarray([p], float))
        if z[0] <= 0.05:
            return
        k = self.cam.focal / z[0] * 0.004 * r
        c = self.layers[layer].getCanvas()
        c.drawCircle(*sc[0], max(2.0, k), skia.Paint(AntiAlias=True, Color=skia.Color(*[int(v) for v in col],
                                                                                      int(255 * min(1, a)))))

    def compose(self, c, t, bg_seed=1, caption=None, cap_a=1.0):
        draw_background(c, t, bg_seed)
        for key, glow_col in (("c", None), ("r", None)):
            img = self.layers[key].makeImageSnapshot()
            for sig, al in ((26, 0.55), (7, 0.8)):
                pp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(sig, sig), BlendMode=skia.BlendMode.kPlus)
                pp.setAlphaf(al)
                c.drawImage(img, 0, 0, skia.SamplingOptions(), pp)
            pp = skia.Paint(BlendMode=skia.BlendMode.kPlus)
            c.drawImage(img, 0, 0, skia.SamplingOptions(), pp)
        vignette(c)
        if caption and cap_a > 0.01:
            draw_caption(c, caption, cap_a)


_STARS = None


def draw_background(c, t, seed=1):
    global _STARS
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                        [skia.Color(4, 10, 28), skia.Color(7, 18, 46), skia.Color(3, 8, 22)],
                                        [0.0, 0.55, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    for x, y, r, a in ((240, 520, 520, 26), (860, 1300, 620, 22), (600, 900, 380, 14)):
        c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color=skia.Color(40, 90, 200, a),
                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.5)))
    if _STARS is None:
        g = np.random.default_rng(seed)
        _STARS = np.stack([g.uniform(0, W, 420), g.uniform(0, H, 420), g.uniform(0.5, 1.7, 420),
                           g.uniform(0, 6.3, 420)], 1)
    p = skia.Paint(AntiAlias=True)
    for x, y, r, ph in _STARS:
        p.setColor(skia.Color(180, 210, 255, int(60 + 80 * (0.5 + 0.5 * math.sin(t * 1.3 + ph)))))
        c.drawCircle(x, y, r, p)


def vignette(c):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.7,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 40), skia.Color(0, 0, 0, 190)],
                                        [0.0, 0.55, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))


def draw_caption(c, s, a=1.0, y=1650, size=40):
    f = skia.Font(F_MED, size)
    words = s.split()
    lines, cur = [], ""
    for wd in words:
        if f.measureText((cur + " " + wd).strip()) > W - 160 and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    for i, ln in enumerate(lines):
        w = f.measureText(ln)
        yy = y + i * size * 1.35
        c.drawString(ln, W / 2 - w / 2 + 2, yy + 3, f, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, int(160 * a)),
                                                                     MaskFilter=skia.MaskFilter.MakeBlur(
                                                                         skia.kNormal_BlurStyle, 5)))
        c.drawString(ln, W / 2 - w / 2, yy, f, skia.Paint(AntiAlias=True, Color=skia.Color(235, 242, 255, int(255 * a))))


# ------------------------------------------------------------------------------------------------ primitives 3D
def circle(center, radius, normal=(0, 1, 0), n=64):
    nrm = np.asarray(normal, float)
    nrm /= np.linalg.norm(nrm)
    a = np.array([1.0, 0, 0]) if abs(nrm[0]) < 0.9 else np.array([0, 0, 1.0])
    u = np.cross(nrm, a)
    u /= np.linalg.norm(u)
    v = np.cross(nrm, u)
    th = np.linspace(0, 2 * math.pi, n + 1)
    return np.asarray(center) + radius * (np.outer(np.cos(th), u) + np.outer(np.sin(th), v))


def sphere_wire(fr, center, radius, col=CYAN, a=1.0, w=2.0, layer="c", n_lat=9, n_lon=12, spin=0.0):
    cx, cy, cz = center
    for i in range(1, n_lat):
        phi = math.pi * i / n_lat
        fr.poly(circle((cx, cy + radius * math.cos(phi), cz), radius * math.sin(phi)), col, a, w, layer)
    th = np.linspace(0, math.pi, 49)
    for j in range(n_lon):
        ang = spin + math.pi * j / n_lon
        d = np.array([math.cos(ang), 0, math.sin(ang)])
        pts = [np.array(center) + radius * (math.sin(p) * np.r_[d[0], 0, d[2]] * 1 + np.r_[0, math.cos(p), 0])
               for p in np.linspace(0, 2 * math.pi, 97)]
        fr.poly(pts, col, a, w, layer)


def grid_floor(fr, y=0.0, size=10.0, step=0.5, a=0.5, center=(0, 0), fade=(6, 16)):
    xs = np.arange(-size, size + 1e-6, step)
    for x in xs:
        pts = np.stack([np.full(41, center[0] + x), np.full(41, y), center[1] + np.linspace(-size, size, 41)], 1)
        fr.poly(pts, CYAN, a, 1.2, fade_depth=fade)
        pts = np.stack([center[0] + np.linspace(-size, size, 41), np.full(41, y), np.full(41, center[1] + x)], 1)
        fr.poly(pts, CYAN, a, 1.2, fade_depth=fade)


def heart_2d(n=80):
    t = np.linspace(0, 2 * math.pi, n)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    return np.stack([x, y], 1) / 17.0


def flat_person(n_scale=1.0):
    """Silhouette de personnage plat (contour 2D), en unités ~ hauteur 2."""
    pts = [(0, 1.0), (0.17, 0.98), (0.25, 0.86), (0.22, 0.72), (0.13, 0.66), (0.42, 0.6), (0.58, 0.2), (0.48, 0.17),
           (0.33, 0.48), (0.28, 0.05), (0.38, -0.95), (0.18, -0.97), (0.03, -0.25), (-0.03, -0.25), (-0.18, -0.97),
           (-0.38, -0.95), (-0.28, 0.05), (-0.33, 0.48), (-0.48, 0.17), (-0.58, 0.2), (-0.42, 0.6), (-0.13, 0.66),
           (-0.22, 0.72), (-0.25, 0.86), (-0.17, 0.98)]
    return np.array(pts) * n_scale


def tube(fr, a_pt, b_pt, r0, r1, col=CYAN, a=1.0, w=1.6, rings=5, lines=8, layer="c"):
    a_pt, b_pt = np.asarray(a_pt, float), np.asarray(b_pt, float)
    ax = b_pt - a_pt
    ln = np.linalg.norm(ax)
    ax /= ln
    for i in range(rings + 1):
        u = i / rings
        fr.poly(circle(a_pt + ax * ln * u, lerp(r0, r1, u), ax, 32), col, a, w, layer)
    ref = np.array([1.0, 0, 0]) if abs(ax[0]) < 0.9 else np.array([0, 0, 1.0])
    e1 = np.cross(ax, ref)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    for j in range(lines):
        th = 2 * math.pi * j / lines
        d = math.cos(th) * e1 + math.sin(th) * e2
        fr.poly([a_pt + d * r0, b_pt + d * r1], col, a, w, layer)


def human_wire(fr, base=(0, 0, 0), a=1.0, col=CYAN, w=1.5, heart=True):
    """Silhouette humaine en fil de fer (tubes et ellipsoïdes), hauteur ≈ 1,8."""
    bx, by, bz = base
    B = np.array([bx, by, bz])
    sphere_wire(fr, (bx, by + 1.62, bz), 0.12, col, a, w, n_lat=6, n_lon=6)
    tube(fr, B + (0, 1.45, 0), B + (0, 1.52, 0), 0.05, 0.05, col, a, w, rings=1)
    tube(fr, B + (0, 0.95, 0), B + (0, 1.45, 0), 0.15, 0.2, col, a, w, rings=6, lines=10)
    tube(fr, B + (0, 0.82, 0), B + (0, 0.95, 0), 0.17, 0.15, col, a, w, rings=2, lines=10)
    for s in (-1, 1):
        tube(fr, B + (0.23 * s, 1.42, 0), B + (0.3 * s, 1.1, 0.02), 0.055, 0.045, col, a, w, rings=3, lines=6)
        tube(fr, B + (0.3 * s, 1.1, 0.02), B + (0.33 * s, 0.82, 0.06), 0.045, 0.035, col, a, w, rings=3, lines=6)
        tube(fr, B + (0.1 * s, 0.82, 0), B + (0.11 * s, 0.43, 0.01), 0.085, 0.06, col, a, w, rings=4, lines=6)
        tube(fr, B + (0.11 * s, 0.43, 0.01), B + (0.11 * s, 0.03, 0), 0.06, 0.045, col, a, w, rings=4, lines=6)
    if heart:
        h = heart_2d() * 0.07
        fr.poly(np.stack([bx + 0.04 + h[:, 0], by + 1.3 + h[:, 1], np.full(len(h), bz + 0.05)], 1), RED, a, 2.4,
                layer="r")
