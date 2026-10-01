"""Style « trait lumineux » : dessin au trait très dense (bleu + accent rouge), halo, fond de nébuleuse.

Tout est procédural (aucune image générée) : chaque motif est une liste de polylignes en coordonnées unitaires,
placée dans le monde (x, y, échelle, rotation), puis vue par une caméra 2D (centre + zoom) qui pousse en continu.
Le dessin se fait dans deux calques (bleu / rouge) composés en mode additif avec deux flous (halo serré + large).
"""
import functools
import math
import os

import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
BLUE = (80, 160, 255)
BLUE_HI = (185, 225, 255)
RED = (255, 55, 65)
RED_HI = (255, 150, 150)
_FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
F_MED = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-Medium.ttf"))
F_BOLD = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-ExtraBold.ttf"))


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def lerp(a, b, u):
    return a + (b - a) * u


def win(t, a, b, fi=0.4, fo=0.4):
    return ease((t - a) / fi) * (1 - ease((t - b) / fo))


# ------------------------------------------------------------------------------------------------ caméra 2D
class View:
    """Monde en pixels (mise en page de base 1080×1920) → écran : (p − centre)·zoom + milieu de l'écran."""

    def __init__(self, cx=W / 2, cy=H / 2, zoom=1.0, rot=0.0):
        self.c = np.array([cx, cy], float)
        self.z = zoom
        self.rot = rot

    def m(self, x, y, s, r=0.0):
        """Matrice affine (2×2, translation) : coordonnées unitaires d'un motif → écran."""
        cr, sr = math.cos(r + self.rot), math.sin(r + self.rot)
        A = np.array([[cr, sr], [-sr, cr]]) * s * self.z
        R = np.array([[math.cos(self.rot), -math.sin(self.rot)], [math.sin(self.rot), math.cos(self.rot)]])
        T = (np.array([x, y]) - self.c) @ R.T * self.z + [W / 2, H / 2]
        return A, T


class Shape:
    """Polylignes concaténées : points (N, 2) et indices de début de chaque ligne."""

    def __init__(self, lines):
        lines = [np.asarray(l, float) for l in lines if len(l) >= 2]
        self.pts = np.concatenate(lines) if lines else np.zeros((0, 2))
        self.starts = np.cumsum([0] + [len(l) for l in lines])

    def __len__(self):
        return len(self.starts) - 1


def _path(pts, starts, upto=1.0):
    p = skia.Path()
    for i in range(len(starts) - 1):
        a, b = starts[i], starts[i + 1]
        if upto < 1.0:
            b = a + max(2, int(round((b - a) * upto)))
        seg = pts[a:b]
        if len(seg) < 2:
            continue
        p.addPoly([skia.Point(float(x), float(y)) for x, y in seg], False)
    return p


class Frame:
    def __init__(self, view):
        self.v = view
        self.layers = {"b": skia.Surface(W, H), "r": skia.Surface(W, H)}
        for s in self.layers.values():
            s.getCanvas().clear(skia.ColorTRANSPARENT)
        self.masks = []                                   # disques sombres (pupilles…) posés sur le fond

    def canvas(self, layer):
        return self.layers[layer].getCanvas()

    def lines(self, shape, place, col=BLUE, a=1.0, w=1.2, layer="b", upto=1.0, clip=None):
        """Dessine un Shape placé en (x, y, échelle, rotation) ; clip = Shape fermé (même placement)."""
        if a <= 0.004 or not len(shape):
            return
        A, T = self.v.m(*place)
        pts = shape.pts @ A + T
        c = self.canvas(layer)
        c.save()
        if clip is not None:
            cp = clip.pts @ A + T
            path = skia.Path()
            path.addPoly([skia.Point(float(x), float(y)) for x, y in cp], True)
            c.clipPath(path, doAntiAlias=True)
        c.drawPath(_path(pts, shape.starts, upto),
                   skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                              StrokeCap=skia.Paint.kRound_Cap,
                              Color=skia.Color(*[int(v) for v in col], int(255 * min(1.0, a)))))
        c.restore()

    def dots(self, pts, place, col=RED, a=1.0, r=4.0, layer="r"):
        if a <= 0.004 or not len(pts):
            return
        A, T = self.v.m(*place)
        q = np.asarray(pts, float) @ A + T
        c = self.canvas(layer)
        p = skia.Paint(AntiAlias=True, Color=skia.Color(*[int(v) for v in col], int(255 * min(1.0, a))))
        for x, y in q:
            c.drawCircle(float(x), float(y), r, p)

    def mask(self, place, radius, a=1.0):
        A, T = self.v.m(*place)
        self.masks.append((T, radius * np.linalg.norm(A[0]), a))

    def fade(self, place, y0, y1, x0=-1.0, x1=1.0, layer="b"):
        """Estompe le calque vers le bas entre y0 et y1 (coordonnées unitaires du motif)."""
        A, T = self.v.m(*place)
        (ax, ay), (bx, by) = np.array([[x0, y0], [x1, y1]]) @ A + T
        sh = skia.GradientShader.MakeLinear([skia.Point(0, float(ay)), skia.Point(0, float(by))],
                                            [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 255)])
        c = self.canvas(layer)
        c.drawRect(skia.Rect(float(min(ax, bx)) - 20, float(ay), float(max(ax, bx)) + 20, float(by) + 2),
                   skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kDstOut))

    def to_screen(self, place, p):
        A, T = self.v.m(*place)
        return np.asarray(p, float) @ A + T

    def compose(self, c, t, bg_a=1.0):
        draw_nebula(c, t, self.v, bg_a)
        for (x, y), r, a in self.masks:                   # pupilles : un trou noir qui « mange » la nébuleuse
            c.drawCircle(float(x), float(y), r * 1.05,
                         skia.Paint(AntiAlias=True, Color=skia.Color(1, 3, 10, int(250 * a)),
                                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.08 + 1)))
        for key in ("b", "r"):
            img = self.layers[key].makeImageSnapshot()
            for sig, al in ((30, 0.6), (8, 0.85), (2.2, 0.6)):
                pp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(sig, sig), BlendMode=skia.BlendMode.kPlus)
                pp.setAlphaf(al * (1.25 if key == "r" else 1.0))
                c.drawImage(img, 0, 0, skia.SamplingOptions(), pp)
            c.drawImage(img, 0, 0, skia.SamplingOptions(), skia.Paint(BlendMode=skia.BlendMode.kPlus))
        vignette(c)


# ------------------------------------------------------------------------------------------------ nébuleuse
def _noise(shape, cells, rng):
    """Bruit de valeur lissé (interpolation bilinéaire + lissage cubique) de taille `shape`."""
    gh, gw = cells
    g = rng.random((gh + 2, gw + 2))
    ys = np.linspace(0, gh, shape[0])
    xs = np.linspace(0, gw, shape[1])
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    cc = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None]
    bot = cc + (d - cc) * fx[None]
    return top + (bot - top) * fy[:, None]


@functools.lru_cache(1)
def nebula_image(seed=7):
    h, w = 720, 405                                       # 1/2.67 de la taille finale : de toute façon flou
    rng = np.random.default_rng(seed)
    f = sum(_noise((h, w), (int(4 * 2 ** o), int(2.3 * 2 ** o)), rng) * 0.55 ** o for o in range(6))
    f = (f - f.min()) / (f.max() - f.min())
    m = sum(_noise((h, w), (int(3 * 2 ** o), int(2 * 2 ** o)), rng) * 0.5 ** o for o in range(4))
    m = (m - m.min()) / (m.max() - m.min())
    cloud = np.clip((f - 0.42) / 0.5, 0, 1) ** 1.6 * (0.35 + 0.9 * m)
    wisps = np.clip((f - 0.62) / 0.3, 0, 1) ** 2.2
    img = np.zeros((h, w, 4), np.float32)
    base = np.array([5, 10, 26], np.float32)
    img[..., :3] = base + cloud[..., None] * np.array([22, 60, 140]) + wisps[..., None] * np.array([40, 90, 170])
    img[..., 3] = 255
    stars = rng.random((h, w)) > 0.9975
    img[stars, :3] = np.array([150, 190, 255]) * rng.uniform(0.4, 1, stars.sum())[:, None]
    arr = np.ascontiguousarray(np.clip(img, 0, 255).astype(np.uint8))
    return skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)


def draw_nebula(c, t, view, a=1.0):
    img = nebula_image()
    c.clear(skia.Color(3, 7, 18))
    par = 1 + 0.12 * math.log(max(view.z, 0.2))           # parallaxe : le fond suit à peine le zoom
    s = 2.67 * 1.12 * par
    dx = (view.c[0] - W / 2) * 0.06 + 18 * math.sin(t * 0.05)
    dy = (view.c[1] - H / 2) * 0.06 + 12 * math.cos(t * 0.04)
    c.save()
    c.translate(W / 2 - dx, H / 2 - dy)
    c.rotate(math.degrees(view.rot) * 0.3)
    c.scale(s, s)
    p = skia.Paint(MaskFilter=None)
    p.setAlphaf(a)
    c.drawImage(img, -img.width() / 2, -img.height() / 2, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()


def vignette(c):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.68,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 50), skia.Color(0, 0, 0, 200)],
                                        [0.0, 0.6, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))


def caption(c, s, a=1.0, y=1640, size=42):
    if a <= 0.01 or not s:
        return
    f = skia.Font(F_MED, size)
    lines, cur = [], ""
    for wd in s.split():
        if f.measureText((cur + " " + wd).strip()) > W - 170 and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    for i, ln in enumerate(lines):
        w = f.measureText(ln)
        yy = y + i * size * 1.35
        c.drawString(ln, W / 2 - w / 2 + 2, yy + 3, f,
                     skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, int(170 * a)),
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
        c.drawString(ln, W / 2 - w / 2, yy, f, skia.Paint(AntiAlias=True, Color=skia.Color(238, 244, 255, int(255 * a))))


# ------------------------------------------------------------------------------------------------ motifs
def circle(r=1.0, n=160, cx=0.0, cy=0.0, a0=0.0, a1=2 * math.pi):
    th = np.linspace(a0, a1, n)
    return np.stack([cx + r * np.cos(th), cy + r * np.sin(th)], 1)


def _warp(p, k=1.0, seed=0):
    x, y = p[:, 0], p[:, 1]
    s = seed * 1.7
    return np.stack([x + k * (0.012 * np.sin(7 * y + 1.3 + s) + 0.008 * np.sin(13 * x + 11 * y + s)),
                     y + k * (0.010 * np.sin(8 * x + 2 + s) + 0.006 * np.sin(15 * y - 9 * x))], 1)


FINGER_TIP = None


def finger_outline(n=200):
    """Bout de doigt : demi-ellipse en haut, flancs légèrement évasés, coupé en bas."""
    th = np.linspace(math.pi, 2 * math.pi, n // 2)
    top = np.stack([0.5 * np.cos(th), -0.12 + 0.62 * np.sin(th)], 1)
    ys = np.linspace(-0.12, 0.85, n // 4)
    right = np.stack([0.5 + 0.03 * (ys + 0.12), ys], 1)
    left = right[::-1] * [-1, 1]
    return np.concatenate([left, top, right])


@functools.lru_cache(4)
def fingerprint(seed=3):
    """Crêtes en boucle (motif le plus courant) + coupures aléatoires (minuties). Unité : largeur 1."""
    rng = np.random.default_rng(seed)
    cy, d = -0.05, 0.026
    lines = [np.array([[0.0, cy - 0.03], [0.0, cy + 0.06]])]
    for k in range(1, 40):
        r = k * d
        th = np.linspace(math.pi, 2 * math.pi, max(12, int(70 * r)))
        arc = np.stack([r * np.cos(th), cy + 1.25 * r * np.sin(th)], 1)
        ys = np.linspace(cy, 0.95, 40)
        sh = 0.22 * (ys - cy) ** 2
        right = np.stack([r * (1 + 0.25 * (ys - cy)) + sh, ys], 1)
        left = np.stack([-r * (1 + 0.25 * (ys - cy)) + sh, ys], 1)[::-1]
        line = _warp(np.concatenate([left, arc[1:-1], right]), 1.0, seed)
        cuts = sorted(rng.integers(5, len(line) - 5, rng.integers(0, 3)))
        prev = 0
        for ci in cuts:                                   # minuties : petites coupures dans la crête
            lines.append(line[prev:ci])
            prev = ci + int(rng.integers(2, 4))
        lines.append(line[prev:])
    return Shape(lines)


def finger_minutiae(seed=3, n=14):
    rng = np.random.default_rng(seed + 50)
    sh = fingerprint(seed)
    out = []
    while len(out) < n:
        i = rng.integers(0, len(sh))
        a = sh.starts[i]
        p = sh.pts[a]
        if abs(p[0]) < 0.42 and -0.6 < p[1] < 0.75 and all(np.hypot(*(p - q)) > 0.12 for q in out):
            out.append(p)
    return np.array(out)


def eye_lids(x):
    up = -0.40 * np.clip(1 - x * x, 0, 1) ** 0.8 * (1 + 0.12 * x)
    lo = 0.30 * np.clip(1 - x * x, 0, 1) ** 1.1 * (1 - 0.1 * x)
    return up, lo


@functools.lru_cache(1)
def eye_parts():
    x = np.linspace(-1, 1, 160)
    up, lo = eye_lids(x)
    opening = np.concatenate([np.stack([x, up], 1), np.stack([x, lo], 1)[::-1]])
    outl = []
    for s, sy in ((1.0, 1.0), (1.04, 1.07), (1.09, 1.16), (1.16, 1.3), (1.25, 1.48)):
        outl.append(np.stack([x * s, up * sy], 1))
        outl.append(np.stack([x * s, lo * sy], 1))
    xs = np.linspace(-0.9, 1.0, 120)
    crease = [np.stack([xs * k, eye_lids(xs)[0] * 1.6 * k - 0.04], 1) for k in (1.0, 1.05)]
    sweep = []
    for k in range(4):                                     # grandes courbes de construction autour de l'œil
        xx = np.linspace(-1.6, 1.6, 120)
        sweep.append(np.stack([xx, -0.75 - 0.05 * k + (0.32 + 0.03 * k) * xx ** 2], 1))
        sweep.append(np.stack([xx, 0.62 + 0.05 * k - (0.22 + 0.02 * k) * xx ** 2], 1))
    iris_r = [circle(r, 120) for r in np.linspace(0.15, 0.36, 7)]
    iris_s = [np.array([[0.15 * math.cos(a), 0.15 * math.sin(a)], [0.36 * math.cos(a), 0.36 * math.sin(a)]])
              for a in np.linspace(0, 2 * math.pi, 120, endpoint=False)]
    return {"outline": Shape(outl), "crease": Shape(crease), "sweep": Shape(sweep),
            "iris": Shape(iris_r + iris_s), "opening": Shape([opening])}


@functools.lru_cache(2)
def iris_detail(seed=5):
    """Iris vu de près (rayon 1) : fibres rouges près de la pupille, fibres bleues croisées, cryptes, limbe."""
    rng = np.random.default_rng(seed)
    rp, rc = 0.28, 0.52
    red, blue, cross = [], [], []
    for i in range(560):
        th0 = rng.uniform(0, 2 * math.pi)
        r1 = rng.uniform(0.5, 0.92)
        r = np.linspace(rp + 0.005, r1, 26)
        tw = rng.normal(0, 0.25)
        th = th0 + tw * (r - rp) + 0.025 * np.sin(r * rng.uniform(15, 30) + rng.uniform(0, 6))
        red.append(np.stack([r * np.cos(th), r * np.sin(th)], 1))
    for i in range(420):
        th0 = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(0.36, 0.55)
        r = np.linspace(r0, rng.uniform(0.9, 1.0), 24)
        th = th0 + 0.04 * np.sin(r * 18 + i) + rng.normal(0, 0.06) * (r - r0)
        blue.append(np.stack([r * np.cos(th), r * np.sin(th)], 1))
    for i in range(170):                                   # fibres en hélice qui se croisent (effet de trame)
        th0 = rng.uniform(0, 2 * math.pi)
        r = np.linspace(0.42, 0.98, 30)
        th = th0 + (1 if i % 2 else -1) * 0.9 * (r - 0.42)
        cross.append(np.stack([r * np.cos(th), r * np.sin(th)], 1))
    limb = [circle(r, 260) for r in (0.97, 1.0, 1.035, 1.075)]
    ticks = [np.array([[1.085 * math.cos(a), 1.085 * math.sin(a)], [1.14 * math.cos(a), 1.14 * math.sin(a)]])
             for a in np.linspace(0, 2 * math.pi, 300, endpoint=False)]
    furrows = []
    for r in (0.74, 0.82, 0.9):
        a = 0.0
        while a < 2 * math.pi:
            ln = rng.uniform(0.3, 0.9)
            furrows.append(circle(r + rng.normal(0, 0.006), 40, a0=a, a1=a + ln))
            a += ln + rng.uniform(0.15, 0.5)
    collar = [_warp(circle(rc + 0.02 * k, 200), 0.6, k + 1) for k in range(2)]
    crypt_c = [(rng.uniform(0.56, 0.76), a) for a in np.linspace(0, 2 * math.pi, 9, endpoint=False) + rng.uniform(0, 0.4)]
    crypts = []
    for r, a in crypt_c:                                   # cryptes : petites lacunes irrégulières, allongées
        q = circle(1.0, 40)
        q = _warp(q * [rng.uniform(0.035, 0.06), rng.uniform(0.016, 0.026)], 0.25, rng.integers(9))
        ca, sa = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        crypts.append(q @ np.array([[ca, sa], [-sa, ca]]) + [r * math.cos(a), r * math.sin(a)])
    pupil = [circle(rp + 0.006 * k, 200) for k in range(3)]
    return {"red": Shape(red), "blue": Shape(blue), "cross": Shape(cross), "limb": Shape(limb),
            "ticks": Shape(ticks), "furrows": Shape(furrows), "collar": Shape(collar), "crypts": Shape(crypts),
            "pupil": Shape(pupil), "rp": rp, "crypt_c": crypt_c}


@functools.lru_cache(2)
def network(seed=11, n=170):
    """Réseau aléatoire (avant la formation de l'iris) : chaque point relié à ses 3 voisins, légèrement courbé."""
    rng = np.random.default_rng(seed)
    r = np.sqrt(rng.random(n)) * 0.95
    a = rng.uniform(0, 2 * math.pi, n)
    p = np.stack([r * np.cos(a), r * np.sin(a)], 1)
    d = np.linalg.norm(p[:, None] - p[None], axis=2)
    seen, lines = set(), []
    for i in range(n):
        for j in np.argsort(d[i])[1:4]:
            k = (min(i, j), max(i, j))
            if k in seen:
                continue
            seen.add(k)
            m = (p[i] + p[j]) / 2 + rng.normal(0, 0.012, 2)
            u = np.linspace(0, 1, 8)[:, None]
            lines.append((1 - u) ** 2 * p[i] + 2 * u * (1 - u) * m + u * u * p[j])
    return Shape(lines)


@functools.lru_cache(2)
def swirl(seed=13, n=520):
    """Lignes de courant d'un double tourbillon : le motif qui « se fige » dans l'iris."""
    rng = np.random.default_rng(seed)
    vort = [((0.32, 0.18), 1.0), ((-0.3, -0.22), 1.0), ((0.05, -0.05), -0.35)]
    lines = []
    for _ in range(n):
        r = math.sqrt(rng.random()) * 0.95
        a = rng.uniform(0, 2 * math.pi)
        q = np.array([r * math.cos(a), r * math.sin(a)])
        pts = [q.copy()]
        for _s in range(46):
            v = np.zeros(2)
            for (cx, cy), g in vort:
                dx, dy = q[0] - cx, q[1] - cy
                d2 = dx * dx + dy * dy + 0.02
                v += g * np.array([-dy, dx]) / d2
            v += 0.4 * q
            q = q + 0.022 * v / (np.linalg.norm(v) + 1e-9)
            if np.hypot(*q) > 0.97:
                break
            pts.append(q.copy())
        lines.append(np.array(pts))
    return Shape(lines)


@functools.lru_cache(4)
def rosette(n=40, rc=0.38, cr=0.62):
    """Anneau de cercles qui se chevauchent (« spirographe ») : bord extérieur à rc + cr."""
    return Shape([circle(rc, 120, cr * math.cos(a), cr * math.sin(a))
                  for a in np.linspace(0, 2 * math.pi, n, endpoint=False)])


@functools.lru_cache(4)
def spirals(m=46, twist=2.2, r0=0.24, r1=0.62, wob=0.0):
    out = []
    for i in range(m):
        th0 = 2 * math.pi * i / m
        r = np.linspace(r0, r1, 40)
        u = (r - r0) / (r1 - r0)
        th = th0 + twist * u + wob * np.sin(u * math.pi * 2)
        out.append(np.stack([r * np.cos(th), r * np.sin(th)], 1))
        if twist < 0:
            out.append(np.stack([r * np.cos(-th + 2 * th0), r * np.sin(-th + 2 * th0)], 1))
    return Shape(out)


@functools.lru_cache(1)
def bust():
    """Silhouette humaine (tête + épaules + torse), sans visage. Unité : rayon du disque de poitrine."""
    head = circle(1.0, 120)
    head = np.stack([head[:, 0] * 0.26, -1.62 + head[:, 1] * 0.33], 1)
    t = np.linspace(0, 1, 60)[:, None]
    p0, p1, p2, p3 = np.array([0.13, -1.31]), np.array([0.16, -1.12]), np.array([0.75, -1.18]), np.array([0.92, -0.8])
    sh = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3
    side = np.stack([np.linspace(0.92, 0.84, 30), np.linspace(-0.8, 1.6, 30)], 1)
    right = np.concatenate([sh, side])
    left = right * [-1, 1]
    lines = []
    for k in (1.0, 1.03):
        lines += [head * k + [0, -1.62 * (1 - k)], right * k, left * k]
    return Shape(lines)


def polar_dots(n_rings=(18, 24, 30, 36, 42, 46, 48), r0=0.32, r1=0.9):
    pts = []
    for i, k in enumerate(n_rings):
        r = r0 + (r1 - r0) * i / (len(n_rings) - 1)
        off = 0.5 * (i % 2)
        for j in range(k):
            a = 2 * math.pi * (j + off) / k
            pts.append((r * math.cos(a), r * math.sin(a)))
    return np.array(pts)
