"""Corps d'Éclat, version « physique » : squelette à cinématique inverse (IK).

Une pose ne donne plus des angles de membres, mais des positions dans le monde : le bassin, l'inclinaison du buste,
et les points que visent les pieds et les mains (le sol, un objet saisi…). Genoux et coudes se plient d'eux-mêmes du
bon côté : un pied posé ne glisse jamais, une main qui tient un objet reste dessus. La cape est une chaîne simulée
qui tombe dans le sens de la gravité du moment.

Repère : y vers le bas. theta = inclinaison du buste en degrés (0 = tête vers le haut de l'écran, + = sens horaire).
"""
import math
from dataclasses import dataclass, field, replace

import skia

from .hero import CAPES, CYAN, _brush, _pen, draw_emote, draw_face

# Proportions : jambes longues (≈ 42 % de la hauteur), buste court, pas de cou visible (la tête pose sur le haut du
# buste) et bras attachés juste sous la tête. Hauteur totale inchangée (≈ 210) : le décor reste valable.
THIGH, SHIN = 45.0, 44.0
UPPER, FORE = 40.0, 38.0
SPINE = 60.0                     # bassin → haut du buste
SHOULDER = 53.0                  # bassin → épaules (juste sous la tête)
NECK = 30.0                      # haut du buste → centre de la tête (< HEAD_R : aucun trait de cou)
HEAD_R = 34.0
HIP_H = 86.0                     # hauteur du bassin debout (genoux jamais verrouillés)
LINE_W = 9.0


def v_add(*vs):
    return (sum(v[0] for v in vs), sum(v[1] for v in vs))


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def v_mul(v, k):
    return (v[0] * k, v[1] * k)


def v_len(v):
    return math.hypot(v[0], v[1])


def v_lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def up_vec(theta):
    a = math.radians(theta)
    return (math.sin(a), -math.cos(a))


def right_vec(theta):
    a = math.radians(theta)
    return (math.cos(a), math.sin(a))


def ik2(root, target, l1, l2, prefer, stretch=1.0):
    """Deux segments de root vers target ; l'articulation se plie du côté de `prefer` (vecteur).
    stretch > 1 : le membre peut s'allonger un peu pour atteindre la cible (bras élastiques de cartoon)."""
    d = v_sub(target, root)
    dist = v_len(d)
    if dist > l1 + l2 and stretch > 1:
        k = min(stretch, dist / (l1 + l2))
        l1, l2 = l1 * k, l2 * k
    if dist < 1e-6:
        d, dist = (0.0, 1.0), 1e-6
    reach = min(dist, l1 + l2 - 1e-4)
    base = math.atan2(d[1], d[0])
    c = (l1 * l1 + reach * reach - l2 * l2) / (2 * l1 * reach)
    a = math.acos(max(-1.0, min(1.0, c)))
    best = None
    for s in (1, -1):
        mid = (root[0] + math.cos(base + s * a) * l1, root[1] + math.sin(base + s * a) * l1)
        score = (mid[0] - root[0] - d[0] * 0.5) * prefer[0] + (mid[1] - root[1] - d[1] * 0.5) * prefer[1]
        if best is None or score > best[0]:
            best = (score, mid)
    mid = best[1]
    to = v_sub(target, mid)
    n = v_len(to) or 1.0
    end = v_add(mid, v_mul(to, l2 / n))
    return mid, end


@dataclass
class Pose:
    pelvis: tuple
    theta: float = 0.0                          # inclinaison du buste
    bend: float = 0.0                           # courbure du haut du dos (+ = vers l'avant)
    head: float = 0.0                           # inclinaison de la tête par rapport au cou (+ = vers l'avant)
    facing: int = 1
    feet: list = field(default_factory=lambda: [None, None])    # cibles des pieds (monde) ; None = libre
    hands: list = field(default_factory=lambda: [None, None])   # cibles des mains (monde) ; None = libre
    expr: str = "neutre"
    look: tuple = (0.0, 0.0)
    emote: tuple = None
    g: tuple = (0.0, 1.0)                       # direction de la gravité (None = apesanteur) : où pendent les membres libres
    gaze: tuple = None                          # point du monde regardé (les yeux le suivent)


def lerp_pose(a, b, u):
    """Mélange de deux poses (les cibles libres prennent la position calculée de l'autre pose)."""
    ja, jb = build(a), build(b)

    def pts(pa, pb, key):
        out = []
        for i in range(2):
            qa = pa[i] if pa[i] is not None else ja[key][i][2]
            qb = pb[i] if pb[i] is not None else jb[key][i][2]
            out.append(v_lerp(qa, qb, u))
        return out
    return replace(b if u >= 0.5 else a, pelvis=v_lerp(a.pelvis, b.pelvis, u),
                   theta=a.theta + ((b.theta - a.theta + 180) % 360 - 180) * u,
                   bend=a.bend + (b.bend - a.bend) * u, head=a.head + (b.head - a.head) * u,
                   feet=pts(a.feet, b.feet, "legs"), hands=pts(a.hands, b.hands, "arms"),
                   look=v_lerp(a.look, b.look, u))


def pose_vec(p):
    """Pose → liste de nombres (les membres libres prennent leur position calculée)."""
    J = build(p)
    feet = [p.feet[i] if p.feet[i] is not None else J["legs"][i][2] for i in range(2)]
    hands = [p.hands[i] if p.hands[i] is not None else J["arms"][i][2] for i in range(2)]
    return [p.pelvis[0], p.pelvis[1], p.theta, p.bend, p.head, *feet[0], *feet[1], *hands[0], *hands[1],
            p.look[0], p.look[1]]


def vec_pose(v, base):
    return replace(base, pelvis=(v[0], v[1]), theta=v[2], bend=v[3], head=v[4], feet=[(v[5], v[6]), (v[7], v[8])],
                   hands=[(v[9], v[10]), (v[11], v[12])], look=(v[13], v[14]))


def free_limb(root, theta, facing, ang, reach):
    """Cible d'un membre libre : angle (degrés) compté depuis « le long du buste vers le bas », + = vers l'avant."""
    down = v_mul(up_vec(theta), -1)
    fwd = v_mul(right_vec(theta), facing)
    a = math.radians(ang)
    return v_add(root, v_mul(v_add(v_mul(down, math.cos(a)), v_mul(fwd, math.sin(a))), reach))


def build(p):
    """Articulations dans le monde."""
    u = up_vec(p.theta)
    f = v_mul(right_vec(p.theta), p.facing)
    neck_dir = up_vec(p.theta + p.bend * p.facing)
    neck = v_add(p.pelvis, v_mul(neck_dir, SPINE))
    chest = v_add(p.pelvis, v_mul(u, SPINE * 0.5))
    head_theta = p.theta + (p.bend + p.head) * p.facing
    head = v_add(neck, v_mul(up_vec(head_theta), NECK))
    shoulder = v_add(p.pelvis, v_mul(v_lerp(u, neck_dir, 0.7), SHOULDER))
    legs, arms = [], []
    for i in range(2):
        if p.feet[i] is not None:
            tgt = p.feet[i]
        elif p.g is None:                                      # apesanteur : genoux mi-pliés, jambes un peu en avant
            tgt = free_limb(p.pelvis, p.theta, p.facing, 28 + 14 * i, 58)
        else:                                                  # pendent dans le sens de la gravité
            tgt = v_add(p.pelvis, v_mul(p.g, 70), v_mul(f, 6 if i else -6))
        knee, foot = ik2(p.pelvis, tgt, THIGH, SHIN, f)
        legs.append([p.pelvis, knee, foot])
    back_down = v_add(v_mul(f, -1), v_mul(u, -0.6))
    for i in range(2):
        if p.hands[i] is not None:
            tgt = p.hands[i]
        elif p.g is None:                                      # apesanteur : bras qui flottent devant
            tgt = free_limb(shoulder, p.theta, p.facing, 95 + 20 * i, 60)
        else:
            tgt = v_add(shoulder, v_mul(p.g, 64), v_mul(f, 24 if i else -20))
        elbow, hand = ik2(shoulder, tgt, UPPER, FORE, back_down, stretch=1.15)
        arms.append([shoulder, elbow, hand])
    return {"pelvis": p.pelvis, "chest": chest, "neck": neck, "shoulder": shoulder, "head": head,
            "head_theta": head_theta, "legs": legs, "arms": arms, "up": u, "fwd": f}


class Cape:
    """Chaîne de points (intégration de Verlet) accrochée au cou : elle tombe dans le sens de la gravité."""

    def __init__(self, anchor, n=7, seg=15.0):
        self.n, self.seg = n, seg
        self.p = [(anchor[0], anchor[1] + i * seg) for i in range(n)]
        self.q = list(self.p)

    def step(self, anchor, back, g, dt, flutter=0.0, t=0.0, bounds=None):
        new = [anchor]
        for i in range(1, self.n):
            x, y = self.p[i]
            px, py = self.q[i]
            wob = flutter * math.sin(t * 6.0 + i * 0.9)
            ax = g[0] * 0.45 + back[0] * 260 + wob * back[1] * 300
            ay = g[1] * 0.45 + back[1] * 260 - wob * back[0] * 300
            new.append((x + (x - px) * 0.9 + ax * dt * dt, y + (y - py) * 0.9 + ay * dt * dt))
        for _ in range(5):
            new[0] = anchor
            for i in range(1, self.n):
                a, b = new[i - 1], new[i]
                d = v_sub(b, a)
                L = v_len(d) or 1e-6
                corr = (L - self.seg) / L
                if i == 1:
                    new[i] = (b[0] - d[0] * corr, b[1] - d[1] * corr)
                else:
                    new[i - 1] = (a[0] + d[0] * corr * 0.5, a[1] + d[1] * corr * 0.5)
                    new[i] = (b[0] - d[0] * corr * 0.5, b[1] - d[1] * corr * 0.5)
            if bounds:
                x0, y0, x1, y1 = bounds
                new = [new[0]] + [(min(max(q[0], x0), x1), min(max(q[1], y0), y1)) for q in new[1:]]
        self.q, self.p = self.p, new

    def shape(self):
        pts = self.p
        left, right = [], []
        for i, q in enumerate(pts):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            d = v_sub(b, a)
            L = v_len(d) or 1.0
            n = (-d[1] / L, d[0] / L)
            w = 4 + 17 * (i / (len(pts) - 1)) ** 0.8
            left.append(v_add(q, v_mul(n, w)))
            right.append(v_add(q, v_mul(n, -w)))
        return left + right[::-1]


def smooth_path(path, pts):
    """Courbe lisse (Catmull-Rom) passant par tous les points."""
    P = [(float(q[0]), float(q[1])) for q in pts]
    path.moveTo(*P[0])
    for i in range(len(P) - 1):
        p0 = P[i - 1] if i > 0 else P[i]
        p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if i + 2 < len(P) else P[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        path.cubicTo(*c1, *c2, *p2)


def draw(c, p, t, cape=None, cape_color="violet", glow=1.0, alpha=255, screen_rot=0.0, J=None):
    """Dessine Éclat (coordonnées monde). J : articulations déjà calculées (lissées). Renvoie les articulations."""
    J = J or build(p)
    cc = CAPES.get(cape_color, cape_color) if isinstance(cape_color, str) else cape_color
    if cape is not None:
        poly = cape.shape()
        path = skia.Path()
        path.moveTo(*poly[0])
        for q in poly[1:]:
            path.lineTo(*q)
        path.close()
        c.drawPath(path, _brush(cc, 110 * glow * alpha / 255, glow=10))
        c.drawPath(path, _brush(cc, 225 * alpha / 255))
    path = skia.Path()                                          # corps : colonne et jambes
    arms = skia.Path()                                          # bras : dessinés PAR-DESSUS la tête, pour qu'un
    if "chains" in J:                                           # geste près du visage reste visible
        C = J["chains"]
        for pts in list(C["legs"]) + [C["spine"]]:
            smooth_path(path, pts)
        for pts in C["arms"]:
            smooth_path(arms, pts)
    else:
        for (a, m, b), dst in [(x, arms) for x in J["arms"]] + [(x, path) for x in J["legs"]]:
            cp = v_sub(v_mul(m, 2.0), v_mul(v_add(a, b), 0.5))
            dst.moveTo(*a)
            dst.quadTo(*cp, *b)
        path.moveTo(*J["pelvis"])
        mid = v_lerp(J["pelvis"], J["neck"], 0.5)
        ctrl = v_add(v_sub(v_mul(J["chest"], 2.0), mid), v_mul(J["fwd"], p.bend * 0.25))
        path.quadTo(*ctrl, *J["neck"])
    path.addCircle(*J["head"], HEAD_R)
    glow_all = skia.Path(path)
    glow_all.addPath(arms)
    c.drawPath(glow_all, _pen(CYAN, LINE_W * 2.3, 75 * glow * alpha / 255, glow=LINE_W * 0.9))
    c.drawPath(path, _pen(CYAN, LINE_W, alpha))
    c.drawCircle(*J["head"], HEAD_R - LINE_W / 2, _brush((0, 0, 0), alpha))
    look = p.look
    if p.gaze is not None:                                     # les yeux visent le point regardé
        d = v_sub(p.gaze, J["head"])
        a = -math.radians(J["head_theta"])
        lx, ly = d[0] * math.cos(a) - d[1] * math.sin(a), d[0] * math.sin(a) + d[1] * math.cos(a)
        n = max(v_len((lx, ly)), 1e-6)
        k = min(1.0, n / 120)
        look = ((lx / n) * k, (ly / n) * k)
    draw_face(c, J["head"], HEAD_R, math.radians(J["head_theta"]), p.facing, p.expr, look, t, alpha)
    c.drawPath(arms, _pen(CYAN, LINE_W, alpha))
    for arm in J["arms"]:                                       # mains : petites boules
        c.drawCircle(*arm[2], LINE_W * 0.85, _brush(CYAN, alpha))
    if p.emote:                                                # symboles toujours droits à l'écran
        kind, age = p.emote
        c.save()
        c.translate(*J["head"])
        c.rotate(-screen_rot)
        if kind == "zzz":
            for i in range(3):
                a = (age * 0.8 + i / 3) % 1.0
                f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 18 + 16 * a)
                x = 30 + 40 * a + 6 * math.sin(age * 3 + i)
                y = -30 - 80 * a
                c.drawString("z", x, y, f, _brush((230, 240, 255), 255 * math.sin(math.pi * a) * alpha / 255))
        else:
            draw_emote(c, (0.0, 0.0), HEAD_R, kind, t, age, alpha)
        c.restore()
    return J


# ---------------------------------------------------------------- surfaces et poses types
@dataclass
class Frame:
    """Repère d'une surface : origine, angle de la tangente (degrés). h = hauteur au-dessus de la surface."""
    origin: tuple
    alpha: float

    def w(self, u, h=0.0):
        t = (math.cos(math.radians(self.alpha)), math.sin(math.radians(self.alpha)))
        n = (math.cos(math.radians(self.alpha - 90)), math.sin(math.radians(self.alpha - 90)))
        return (self.origin[0] + t[0] * u + n[0] * h, self.origin[1] + t[1] * u + n[1] * h)

    def local(self, q):
        t = (math.cos(math.radians(self.alpha)), math.sin(math.radians(self.alpha)))
        n = (math.cos(math.radians(self.alpha - 90)), math.sin(math.radians(self.alpha - 90)))
        d = v_sub(q, self.origin)
        return (d[0] * t[0] + d[1] * t[1], d[0] * n[0] + d[1] * n[1])


def stand(F, u, facing=1, crouch=0.0, lean=0.0, width=13.0, shift=0.0, hands=None, bend=0.0, head=0.0,
          feet_u=None, **kw):
    """Debout sur la surface F, bassin au-dessus de u. crouch 0..1 plie les genoux ; lean incline le buste."""
    # contrapposto : pied arrière sous le bassin (il porte le poids), pied avant plus loin ; le bassin s'abaisse
    # un peu, le haut du dos s'arrondit et la tête avance (ligne d'action en S, jamais un piquet vertical)
    fu = feet_u or (u - facing * width * 0.7, u + facing * width * 1.5)
    h = HIP_H * (1 - 0.5 * crouch) - 5
    pelvis = F.w(u + shift - facing * crouch * 14 - facing * 3, h)
    return Pose(pelvis, F.alpha + (lean - 3) * facing, bend + 14 + 8 * crouch, head + 6, facing,
                [F.w(fu[0]), F.w(fu[1])], hands or [None, None], **kw)


def lying(F, u, head_first=-1, knees=0.3, **kw):
    """Allongé sur le dos (visage vers le haut), bassin en u, tête du côté head_first (±1 le long de la surface)."""
    pelvis = F.w(u, 13)
    tilt = 11.3                                                # la tête (plus épaisse) repose sur le sol
    theta = F.alpha + (90 - tilt if head_first > 0 else -90 + tilt)
    k = knees
    feet = [F.w(u - head_first * (64 - 30 * k), 6 + 26 * k), F.w(u - head_first * (66 - 20 * k), 5)]
    return Pose(pelvis, theta, 0, -8, -head_first, feet, [None, None], **kw)
