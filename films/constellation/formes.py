"""Nuages de points : formes de base et Grande Pyramide (dimensions réelles, y = nord→sud, z = haut)."""
import math

import numpy as np

HALF, HEIGHT = 115.0, 146.6
GG0, GG1 = np.array([0, -37.0, 21.7]), np.array([0, 5.0, 42.9])
VOID0, VOID1 = np.array([0, -27.0, 36.0]), np.array([0, 3.0, 51.0])


def rng(seed):
    return np.random.default_rng(seed)


def sphere(n, R, center=(0, 0, 0), seed=0, lines=0.45):
    """Sphère : une partie des points sur méridiens et parallèles (lecture « globe »), le reste uniforme."""
    g = rng(seed)
    m = int(n * lines)
    u = g.random(n - m) * 2 - 1
    th = g.random(n - m) * 2 * math.pi
    pts = [np.stack([np.sqrt(1 - u * u) * np.cos(th), np.sqrt(1 - u * u) * np.sin(th), u], 1)]
    k = g.integers(0, 2, m)
    lat = np.where(k == 0, np.round(g.uniform(-80, 80, m) / 10) * 10, g.uniform(-89, 89, m))
    lon = np.where(k == 1, np.round(g.uniform(0, 360, m) / 15) * 15, g.uniform(0, 360, m))
    la, lo = np.radians(lat), np.radians(lon)
    pts.append(np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], 1))
    P = np.concatenate(pts) * R + np.asarray(center)
    return P


def polyline(pts, n, jitter=0.0, seed=0):
    pts = np.asarray(pts, np.float64)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.r_[0, np.cumsum(seg)]
    s = np.sort(rng(seed).random(n)) * cum[-1]
    i = np.clip(np.searchsorted(cum, s) - 1, 0, len(seg) - 1)
    k = ((s - cum[i]) / np.maximum(seg[i], 1e-9))[:, None]
    P = pts[i] * (1 - k) + pts[i + 1] * k
    if jitter:
        P += rng(seed + 1).standard_normal(P.shape) * jitter
    return P


def pyramid_surface(n, seed=0, courses=60, course_frac=0.55):
    """Faces de la pyramide ; une partie des points se range sur les assises (lignes horizontales)."""
    g = rng(seed)
    # échantillonnage uniforme sur l'aire : z suit une densité ∝ (1 - z/h)
    v = g.random(n)
    z = HEIGHT * (1 - np.sqrt(1 - v))
    m = g.random(n) < course_frac
    z[m] = np.round(z[m] / HEIGHT * courses) / courses * HEIGHT + g.normal(0, 0.15, m.sum())
    z = np.clip(z, 0, HEIGHT)
    s = HALF * (1 - z / HEIGHT)
    face = g.integers(0, 4, n)
    w = g.uniform(-1, 1, n) * s
    x = np.where(face == 0, w, np.where(face == 1, s, np.where(face == 2, -w, -s)))
    y = np.where(face == 0, -s, np.where(face == 1, w, np.where(face == 2, s, -w)))
    P = np.stack([x, y, z], 1)
    # arêtes plus denses
    e = g.random(n) < 0.08
    t = g.random(e.sum())
    corner = g.integers(0, 4, e.sum())
    cxy = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], float)[corner] * HALF
    P[e, 0] = cxy[:, 0] * (1 - t)
    P[e, 1] = cxy[:, 1] * (1 - t)
    P[e, 2] = HEIGHT * t
    return P


def pyramid_volume(n, seed=0):
    g = rng(seed)
    v = g.random(n)
    z = HEIGHT * (1 - np.cbrt(1 - v))
    s = HALF * (1 - z / HEIGHT)
    x = g.uniform(-1, 1, n) * s
    y = g.uniform(-1, 1, n) * s
    return np.stack([x, y, z], 1)


def interior(n, seed=0):
    """Couloirs et chambres connus, en lignes de points."""
    ent = (0, -HALF + 17.0 * HALF / HEIGHT, 17.0)
    L = [
        [ent, (0, -6.0, -30.0)],
        [(0, -72.0, 2.0), tuple(GG0)],
        [tuple(GG0), (0, -2.9, 21.7)],
        [(0, -2.9, 21.7), (0, 2.9, 21.7), (0, 2.9, 25.5), (0, 0, 27.9), (0, -2.9, 25.5), (0, -2.9, 21.7)],
        [tuple(GG0), tuple(GG1), tuple(GG1 + [0, 0, 8.6]), tuple(GG0 + [0, 0, 8.6]), tuple(GG0)],
        [tuple(GG1), (0, 8.0, 42.9)],
        [(0, 8.0, 43.0), (0, 13.2, 43.0), (0, 13.2, 48.8), (0, 8.0, 48.8), (0, 8.0, 43.0)],
        [(0, -6, -30), (0, 8, -30), (0, 8, -26), (0, -6, -26), (0, -6, -30)],
    ]
    lens = np.array([sum(np.linalg.norm(np.subtract(a, b)) for a, b in zip(l, l[1:])) for l in L])
    counts = np.maximum(50, (n * lens / lens.sum()).astype(int))
    pts = [polyline(l, c, 0.15, seed + i) for i, (l, c) in enumerate(zip(L, counts))]
    # épaisseur en x pour donner du volume aux couloirs
    P = np.concatenate(pts)
    P[:, 0] += rng(seed + 9).uniform(-0.8, 0.8, len(P))
    return P


def capsule_dist(P, a=VOID0, b=VOID1):
    """Distance de chaque point au segment ab, et direction de sortie."""
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    c = a + t[:, None] * ab
    d = P - c
    dist = np.linalg.norm(d, axis=1)
    dirn = d / np.maximum(dist, 1e-6)[:, None]
    return dist, dirn, c


# ================================================================== v2 : formes détaillées
import os

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _lonlat_to_xyz(lon, lat):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


def _sample_lines(pts, idx, n, seed, jitter=0.0):
    """Échantillonne n points le long d'un ensemble de polylignes lon/lat (idx = bornes)."""
    segs_a, segs_b = [], []
    for a, b in zip(idx[:-1], idx[1:]):
        if b - a >= 2:
            segs_a.append(pts[a:b - 1])
            segs_b.append(pts[a + 1:b])
    A, B = np.concatenate(segs_a), np.concatenate(segs_b)
    ok = np.abs(A[:, 0] - B[:, 0]) < 90                     # pas de segment à travers l'antiméridien
    A, B = A[ok], B[ok]
    L = np.linalg.norm(B - A, axis=1) + 1e-9
    g = rng(seed)
    i = g.choice(len(A), n, p=L / L.sum())
    k = g.random(n)[:, None]
    P = A[i] * (1 - k) + B[i] * k
    if jitter:
        P = P + g.normal(0, jitter, P.shape)
    return P


def earth(n, seed=0):
    """Globe réel (rayon 1) : côtes, terres en pointillé, fleuves, Nil, lumières des villes, grille faible.
    Renvoie (P, couleur RGB par point, rôle) ; rôle 0 grille, 1 terre, 2 côte, 3 fleuve, 4 Nil, 5 ville."""
    d = np.load(os.path.join(_DATA, "terre.npz"))
    g = rng(seed)
    shares = dict(grid=0.10, land=0.38, coast=0.30, rivers=0.07, nile=0.03, city=0.12)
    cnt = {k: int(n * v) for k, v in shares.items()}
    cnt["land"] += n - sum(cnt.values())
    parts, cols, roles = [], [], []
    # grille (parallèles / méridiens)
    m = cnt["grid"]
    kk = g.integers(0, 2, m)
    lat = np.where(kk == 0, np.round(g.uniform(-80, 80, m) / 15) * 15, g.uniform(-85, 85, m))
    lon = np.where(kk == 1, np.round(g.uniform(-180, 180, m) / 15) * 15, g.uniform(-180, 180, m))
    parts.append(np.stack([lon, lat], 1)); cols.append(np.tile([0.15, 0.35, 0.9], (m, 1)) * 0.35); roles.append(np.zeros(m))
    # terres : tirage dans le masque
    shape = tuple(d["land_shape"])
    mask = np.unpackbits(d["land"])[: shape[0] * shape[1]].reshape(shape).astype(bool)
    m = cnt["land"]
    got = []
    while sum(len(x) for x in got) < m:
        u = g.random(m * 3) * 2 - 1
        lat = np.degrees(np.arcsin(u))
        lon = g.uniform(-180, 180, m * 3)
        iy = np.clip(((90 - lat) * 10).astype(int), 0, shape[0] - 1)
        ix = np.clip(((lon + 180) * 10).astype(int), 0, shape[1] - 1)
        ok = mask[iy, ix]
        got.append(np.stack([lon[ok], lat[ok]], 1))
    parts.append(np.concatenate(got)[:m]); cols.append(np.tile([0.22, 0.5, 1.0], (m, 1)) * 0.55); roles.append(np.ones(m))
    # côtes
    m = cnt["coast"]
    parts.append(_sample_lines(d["coast"], d["coast_i"], m, seed + 1, 0.02)); cols.append(np.tile([0.45, 0.72, 1.0], (m, 1)))
    roles.append(np.full(m, 2))
    m = cnt["rivers"]
    parts.append(_sample_lines(d["rivers"], d["rivers_i"], m, seed + 2, 0.02)); cols.append(np.tile([0.3, 0.6, 1.0], (m, 1)) * 0.8)
    roles.append(np.full(m, 3))
    m = cnt["nile"]
    parts.append(_sample_lines(d["nile"], d["nile_i"], m, seed + 3, 0.03)); cols.append(np.tile([0.6, 0.85, 1.0], (m, 1)) * 1.6)
    roles.append(np.full(m, 4))
    # villes : grappes proportionnelles à la population (lumières chaudes)
    m = cnt["city"]
    c = d["cities"]
    w = np.sqrt(c[:, 2])
    i = g.choice(len(c), m, p=w / w.sum())
    spread = 0.05 + 0.25 * (c[i, 2] / c[:, 2].max()) ** 0.5
    ll = c[i, :2] + g.normal(0, 1, (m, 2)) * spread[:, None]
    parts.append(ll); cols.append(np.tile([1.0, 0.72, 0.4], (m, 1)) * 0.9); roles.append(np.full(m, 5))
    LL = np.concatenate(parts)
    return _lonlat_to_xyz(LL[:, 0], LL[:, 1]), np.concatenate(cols).astype(np.float32), np.concatenate(roles)


def align_rotation(src, dst, src_up=(0, 0, 1), dst_up=(0, 0, 1)):
    """Rotation qui envoie la direction src sur dst en gardant « le nord » vers dst_up."""
    def frame(d, up):
        d = np.asarray(d, float); d /= np.linalg.norm(d)
        up = np.asarray(up, float); up = up - d * (up @ d); up /= np.linalg.norm(up)
        return np.stack([d, up, np.cross(d, up)], 1)
    return frame(dst, dst_up) @ frame(src, src_up).T


# ------------------------------------------------------------------ Grande Pyramide en assises et en blocs
def _courses(seed=0, top=138.5):
    g = rng(seed)
    z, zs = 0.0, [0.0]
    while z < top:
        h = 1.45 - 0.8 * (z / top) + g.normal(0, 0.12)        # assises plus hautes à la base
        z = min(top, z + max(0.5, h))
        zs.append(z)
    return np.array(zs)


Z_COURSES = _courses()


def pyramid_blocks(n, seed=0, zmax=None, half=HALF, height=HEIGHT, courses=Z_COURSES):
    """Pyramide actuelle (sans revêtement, sommet arasé à 138,5 m) : marches, joints de blocs décalés.
    Renvoie (P, intensité relative par point)."""
    g = rng(seed)
    zs = courses if zmax is None else courses[courses <= zmax + 1e-6]
    if len(zs) < 2:
        zs = courses[:2]
    z0, z1 = zs[:-1], zs[1:]
    s_out = half * (1 - z1 / height) + 0.35              # front de la marche
    per = 8 * s_out * (z1 - z0 + 0.4)
    k = g.choice(len(z0), n, p=per / per.sum())
    zb, zt, s = z0[k], z1[k], s_out[k]
    typ = g.random(n)
    u = g.uniform(-1, 1, n) * s                           # position le long de la face
    face = g.integers(0, 4, n)
    z = np.empty(n)
    inten = np.empty(n)
    depth = np.zeros(n)
    # 1) arête haute de la marche (lignes horizontales nettes)
    m1 = typ < 0.36
    z[m1] = zt[m1]; inten[m1] = 1.0
    # 2) joints verticaux décalés d'une assise à l'autre
    m2 = (typ >= 0.36) & (typ < 0.62)
    off = (np.sin(k[m2] * 12.9898) * 43758.5453) % 1.0
    w = 1.3 + 0.9 * ((np.sin(k[m2] * 78.233) * 12345.6789) % 1.0)
    u[m2] = (np.round((u[m2] / w) - off) + off) * w
    z[m2] = zb[m2] + g.random(m2.sum()) * (zt[m2] - zb[m2]); inten[m2] = 0.75
    # 3) remplissage faible des faces de blocs
    m3 = (typ >= 0.62) & (typ < 0.88)
    z[m3] = zb[m3] + g.random(m3.sum()) * (zt[m3] - zb[m3]); inten[m3] = 0.22
    # 4) dessus des marches (recul vers la marche suivante)
    m4 = typ >= 0.88
    z[m4] = zt[m4]; depth[m4] = g.random(m4.sum()) * 1.1; inten[m4] = 0.3
    u = np.clip(u, -s, s)
    r = s - depth
    x = np.where(face == 0, u, np.where(face == 1, r, np.where(face == 2, -u, -r)))
    y = np.where(face == 0, -r, np.where(face == 1, u, np.where(face == 2, r, -u)))
    # arêtes d'angle renforcées
    corner = g.random(n) < 0.05
    sg = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]])[g.integers(0, 4, corner.sum())]
    x[corner] = sg[:, 0] * s[corner]; y[corner] = sg[:, 1] * s[corner]; inten[corner] = 1.2
    return np.stack([x, y, z], 1), inten.astype(np.float32)


def platform(n, z, seed=0, half=HALF, height=HEIGHT):
    """Plate-forme plane au sommet d'une pyramide inachevée (chantier)."""
    g = rng(seed)
    s = half * (1 - z / height)
    return np.stack([g.uniform(-s, s, n), g.uniform(-s, s, n), np.full(n, z)], 1)


def pyramid_simple(n, center, half, height, seed=0, top=None):
    """Pyramide voisine (Khéphren, Mykérinos) : assises + arêtes, moins dense."""
    zs = _courses(seed + 5, top or height * 0.97)
    P, I = pyramid_blocks(n, seed, half=half, height=height, courses=zs)
    return P + np.asarray(center), I


# ------------------------------------------------------------------ volumes intérieurs
def box_surface(n, x0, x1, y0, y1, z0, z1, seed=0, edge=0.4):
    """Surface d'une boîte : une part des points sur les arêtes."""
    g = rng(seed)
    dims = np.array([x1 - x0, y1 - y0, z1 - z0])
    areas = np.array([dims[1] * dims[2], dims[1] * dims[2], dims[0] * dims[2], dims[0] * dims[2], dims[0] * dims[1], dims[0] * dims[1]])
    ne = int(n * edge)
    f = g.choice(6, n - ne, p=areas / areas.sum())
    P = np.stack([g.uniform(x0, x1, n - ne), g.uniform(y0, y1, n - ne), g.uniform(z0, z1, n - ne)], 1)
    P[f == 0, 0] = x0; P[f == 1, 0] = x1; P[f == 2, 1] = y0; P[f == 3, 1] = y1; P[f == 4, 2] = z0; P[f == 5, 2] = z1
    c = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    E = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    e = g.integers(0, 12, ne)
    t = g.random(ne)[:, None]
    A = c[[E[i][0] for i in e]]
    B = c[[E[i][1] for i in e]]
    return np.concatenate([P, A * (1 - t) + B * t])


def along(P, a, b, w_axis=(1, 0, 0)):
    """Place des points définis dans un repère local (x = largeur, y = longueur 0→1 mis à l'échelle, z = haut)
    le long du segment a→b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d)
    ey = d / L
    ex = np.asarray(w_axis, float)
    ez = np.cross(ex, ey)
    return a + P[:, :1] * ex + (P[:, 1:2] * L) * ey + P[:, 2:3] * ez


def gallery(n, seed=0):
    """Grande Galerie : banquettes et 7 assises en encorbellement (largeur 2,06 m → 1,04 m, haut 8,6 m)."""
    g = rng(seed)
    parts = []
    courses = [(0.6, 2.9, 1.03)] + [(2.9 + 0.8 * k, 2.9 + 0.8 * (k + 1), 1.03 - 0.076 * (k + 1)) for k in range(7)]
    m = n // (2 * len(courses) + 2)
    for s in (-1, 1):
        for (z0, z1, xx) in courses:
            t = g.random(m)
            zz = np.where(g.random(m) < 0.5, z1, z0 + g.random(m) * (z1 - z0))
            parts.append(np.stack([np.full(m, s * xx), t, zz], 1))
        t = g.random(m)
        parts.append(np.stack([s * g.uniform(0.52, 1.03, m), t, np.full(m, 0.6)], 1))
    Q = np.concatenate(parts)
    return along(Q, GG0, GG1)


def interior_v2(n, seed=0):
    """Couloirs en tubes, chambres en volumes, galerie détaillée."""
    g = rng(seed)
    out = []
    ent = np.array([0, -HALF + 17.0 * HALF / HEIGHT, 17.0])

    def tube(a, b, m, w=1.05, h=1.2):
        t = g.random(m)
        side = g.integers(0, 4, m)
        x = np.where(side == 0, -w / 2, np.where(side == 1, w / 2, g.uniform(-w / 2, w / 2, m)))
        z = np.where(side == 2, 0.0, np.where(side == 3, h, g.uniform(0, h, m)))
        return along(np.stack([x, t, z], 1), a, b)
    out.append(tube(ent, (0, -6, -30), int(n * 0.12)))
    out.append(tube((0, -72, 2), GG0, int(n * 0.08)))
    out.append(tube(GG0, (0, -2.9, 21.7), int(n * 0.07)))
    out.append(gallery(int(n * 0.35), seed + 1))
    out.append(box_surface(int(n * 0.08), -2.6, 2.6, -2.9, 2.9, 21.7, 26.0, seed + 2))
    out.append(box_surface(int(n * 0.12), -5.2, 5.2, 8.0, 13.2, 43.0, 48.8, seed + 3))
    for i, z in enumerate((49.8, 51.9, 54.0, 56.1, 58.2)):
        out.append(box_surface(int(n * 0.02), -5.2, 5.2, 8.0, 13.2, z, z + 1.0, seed + 10 + i, edge=0.7))
    out.append(box_surface(int(n * 0.06), -4, 4, -6, 8, -30, -26, seed + 4))
    return np.concatenate(out)


# ------------------------------------------------------------------ texte en particules
def text_points(text, n, height=1.0, seed=0, font_size=400):
    """Points répartis dans les glyphes d'un texte (centré, dans le plan x-z, hauteur ≈ height)."""
    import skia
    from films import montage_ia as MI
    f = skia.Font(MI.F_SUB, font_size)
    w = int(f.measureText(text)) + 40
    h = int(font_size * 1.3)
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    c.drawString(text, 20, font_size, f, skia.Paint(AntiAlias=True, Color=skia.ColorWHITE))
    img = surf.makeImageSnapshot().toarray()[:, :, 0]
    ys, xs = np.nonzero(img > 128)
    edge = (img > 128) & ~(np.roll(img > 128, 1, 0) & np.roll(img > 128, -1, 0) & np.roll(img > 128, 1, 1) & np.roll(img > 128, -1, 1))
    ey, ex = np.nonzero(edge)
    g = rng(seed)
    ne = n // 3
    i = g.integers(0, len(xs), n - ne)
    j = g.integers(0, len(ex), ne)
    X = np.r_[xs[i], ex[j]] + g.random(n)
    Y = np.r_[ys[i], ey[j]] + g.random(n)
    sc = height / (font_size * 0.72)
    X = (X - w / 2) * sc
    Z = (font_size * 0.64 - Y) * sc
    return np.stack([X, np.zeros(n), Z], 1)


# ------------------------------------------------------------------ personnages en particules (Mixamo)
class Figure:
    """Personnage Mixamo échantillonné en points sur sa surface ; animé par skinning."""

    def __init__(self, n=20000, seed=0):
        from films.holo.perso import Perso
        p = Perso()
        self.p = p
        T = p.T[p.tpart == 0]
        V = p.V
        A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        area = np.linalg.norm(np.cross(B - A, C - A), axis=1)
        g = rng(seed)
        self.tri = T[g.choice(len(T), n, p=area / area.sum())]
        r1, r2 = g.random(n), g.random(n)
        s = np.sqrt(r1)
        self.bary = np.stack([1 - s, s * (1 - r2), s * r2], 1)

    def points(self, anim, t, pos=(0, 0, 0), yaw=0.0, lean=0.0, scale=1.0):
        """Points en coordonnées monde (z en haut) ; yaw = direction du regard (rad, 0 = +y), lean = penché en avant."""
        V = self.p.skin(self.p.mats(anim, t))
        P = (V[self.tri] * self.bary[:, :, None]).sum(1)
        # Mixamo : y en haut, regard vers +z → monde : z en haut, regard vers +y
        Q = np.stack([P[:, 0], P[:, 2], P[:, 1]], 1) * scale
        if lean:
            c, s = np.cos(lean), np.sin(lean)
            y, z = Q[:, 1].copy(), Q[:, 2].copy()
            Q[:, 1], Q[:, 2] = y * c + z * s, -y * s + z * c
        c, s = np.cos(yaw), np.sin(yaw)
        x, y = Q[:, 0].copy(), Q[:, 1].copy()
        Q[:, 0], Q[:, 1] = x * c + y * s, -x * s + y * c
        return Q + np.asarray(pos)
