"""Démo « La flèche » (20 s) : Éclat découvre qu'une flèche « g » commande la gravité.

    python -m films.stick.fleche sortie.mp4 [--images t1,t2,...] [--morceaux N]

Une seule règle, montrée puis exploitée : la gravité tombe dans le sens de la flèche. Tout en découle —
Éclat et les pierres chutent, glissent, basculent selon la gravité du moment ; ses pieds et ses mains restent sur
leurs appuis (cinématique inverse) ; sa cape pend du bon côté. Les chutes sont balistiques : personne ne « vole ».
"""
import argparse
import math
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np
import skia

from . import corps as K
from .corps import Frame, Pose, build, lerp_pose, lying, stand, up_vec, v_add, v_len, v_lerp, v_mul, v_sub

W, H, FPS = 1080, 1920, 60
DURATION = 20.0
DT = 1.0 / FPS
LINE = (236, 240, 248)
CYAN = K.CYAN
GOLD = (255, 200, 90)
ROOM = 480.0                                   # la pièce : carré de ±480
G = 1800.0                                     # intensité de la gravité (unités/s²)
A = (0.0, ROOM - 300.0)                        # centre de la flèche (elle flotte, fixe)
A_HALF = 120.0                                 # demi-longueur de la flèche
FLOOR = Frame((0.0, ROOM), 0)
RWALL = Frame((ROOM, 0.0), 270)                # mur de droite (sol quand la gravité pointe à droite) : u = -y
CEIL = Frame((0.0, -ROOM), 180)


def clamp01(u):
    return min(max(u, 0.0), 1.0)


def ease_io(u):
    u = clamp01(u)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = clamp01(u)
    return 1 - (1 - u) ** 3


def ease_in(u):
    u = clamp01(u)
    return u * u


def unit(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def col(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def pen(c, w, a=255, glow=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if glow:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        p.setBlendMode(skia.BlendMode.kPlus)
    return p


def brush(c, a=255, glow=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if glow:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        p.setBlendMode(skia.BlendMode.kPlus)
    return p


# ---------------------------------------------------------------- la flèche (et donc la gravité)
T_ARRIVE = (0.50, 0.75)
T_POKE = 5.30
T_GRAB, T_PUSH, T_OFF, T_FACE = 7.45, 7.52, 7.66, 8.00
T_HIT = 15.55
SPIN_T, SPIN = 3.0, -450.0                     # après le choc : 1¼ tour (sens antihoraire), s'arrête pointée vers le haut


def arrow_phi(t):
    """Direction de la flèche (degrés, 90 = vers le bas) : c'est la direction de la gravité."""
    if t < T_POKE:
        return 90.0
    if t < T_PUSH:                                             # la pichenette : elle bascule de 25°
        a = 90 - 25 * ease_out((t - T_POKE) / 0.15)
        if t > T_POKE + 0.15:
            a += 4 * math.exp(-(t - T_POKE - 0.15) * 7) * math.sin((t - T_POKE - 0.15) * 25)
        return a
    if t < T_HIT:                                              # poussée : elle tourne sur son élan jusqu'à pointer à droite
        return 65 - 65 * ease_out((t - T_PUSH) / 0.7)
    v = (t - T_HIT) / SPIN_T
    if v < 1:
        return SPIN * (1 - (1 - v) ** 3)
    return SPIN + 3 * math.exp(-(t - T_HIT - SPIN_T) * 5) * math.sin((t - T_HIT - SPIN_T) * 22)


def arrow_center(t):
    if t < T_ARRIVE[0]:
        return None
    if t < T_ARRIVE[1]:                                        # arrive en trombe du haut de la pièce
        u = (t - T_ARRIVE[0]) / (T_ARRIVE[1] - T_ARRIVE[0])
        return (A[0], -900 + (A[1] + 900) * ease_in(u))
    u = (t - T_ARRIVE[1]) / 0.25
    if u < 1:                                                  # s'arrête net, léger rebond
        return (A[0], A[1] + 24 * math.sin(math.pi * u) * (1 - u))
    return A


def gravity(t):
    if t < T_ARRIVE[1]:
        return (0.0, 0.0)
    return v_mul(unit(arrow_phi(t)), G)


def arrow_point(t, k):
    """Point de la flèche à la distance k du centre, côté pointe (k négatif : côté empennage)."""
    c = arrow_center(t) or A
    return v_add(c, v_mul(unit(arrow_phi(t)), k))


# ---------------------------------------------------------------- pierres
class Stone:
    def __init__(self, pos, vel, r, sides, ang, spin):
        self.p, self.v, self.r, self.sides, self.a, self.w = list(pos), list(vel), r, sides, ang, spin
        self.held = False
        self.drag = 0.0                                        # frottement de l'air (un peu différent pour chacune)


def make_stones():
    rng = np.random.default_rng(11)
    spots = [(100, -240), (240, -340), (370, -110), (260, 120), (160, -30), (410, 210), (80, 260)]
    out = []
    for i, (x, y) in enumerate(spots):
        out.append(Stone((x, y), (rng.uniform(-14, 14), rng.uniform(-14, 14)), float(rng.uniform(17, 27)),
                         int(rng.integers(5, 8)), float(rng.uniform(0, 360)), float(rng.uniform(-20, 20))))
        out[-1].drag = float(rng.uniform(0.05, 0.6))
    return out


# ---------------------------------------------------------------- poses utiles
def swing_hands(p, angles, reach=70.0):
    """Mains pendantes dans le sens de la gravité, balancées de `angles` (degrés, + = vers l'avant)."""
    J = build(replace(p, hands=[None, None]))
    g = p.g or v_mul(up_vec(p.theta), -1)
    base = math.degrees(math.atan2(g[1], g[0]))
    side = 1 if (J["fwd"][0] * -g[1] + J["fwd"][1] * g[0]) > 0 else -1
    return [v_add(J["shoulder"], v_mul(unit(base - side * a), reach)) for a in angles]


def sitting(F, u, facing=1, lean=-12, **kw):
    pelvis = F.w(u, 15)
    feet = [F.w(u + facing * 62, 0), F.w(u + facing * 54, 0)]
    hands = [F.w(u - facing * 34, 0), F.w(u - facing * 26, 0)]
    return Pose(pelvis, F.alpha + lean * facing, 6, 6, facing, feet, hands, **kw)


def walk(F, t, t0, t1, u0, u1, n, g, lean=6.0, **kw):
    """Marche de u0 à u1 en n pas : pieds posés (ils ne glissent pas), bassin qui ondule, bras en balancier."""
    s = ease_io((t - t0) / (t1 - t0))
    d = 1 if u1 > u0 else -1
    w = 10.0
    plants = [[u0 - d * w], [u0 + d * w]]                        # pied arrière d'abord
    for k in range(n):
        mv = k % 2
        if k == n - 1:
            target = u1 - d * w if mv == 0 else u1 + d * w
        else:
            target = u0 + (u1 - u0) * (k + 1) / n + d * abs(u1 - u0) / n * 0.3
        plants[mv].append(target)
    phase = s * n
    k = min(int(phase), n - 1)
    v = phase - k
    feet = []
    for f in range(2):
        done = [i for i in range(n) if i % 2 == f and (i < k or (i == k and v >= 1))]
        idx = len(done)
        cur = plants[f][idx]
        if k % 2 == f and k < n and v < 1 and idx < len(plants[f]) - 1:
            nxt = plants[f][idx + 1]
            e = ease_io(v)
            feet.append(F.w(cur + (nxt - cur) * e, 15 * math.sin(math.pi * v)))
        else:
            feet.append(F.w(cur, 0))
    pu = u0 + (u1 - u0) * s
    speed = abs(ease_io(clamp01((t - t0) / (t1 - t0)) + 0.01) - s) / 0.01
    h = K.HIP_H - 3 - 4 * (1 - math.sin(math.pi * v))
    p = Pose(F.w(pu, h), F.alpha + d * lean * min(1.0, speed), 4, 2, d, feet, [None, None], g=g, **kw)
    sw = 22 * math.sin(math.pi * phase) * min(1.0, speed * 1.5)
    p.hands = swing_hands(p, [sw, -sw])
    return p


def keyed(t, keys, ease=ease_io):
    """Interpolation entre poses clés [(instant, pose ou fonction(t) -> pose), …]."""
    def P(x):
        return x(t) if callable(x) else x
    if t <= keys[0][0]:
        return P(keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t < t1:
            return lerp_pose(P(a), P(b), ease((t - t0) / (t1 - t0)))
    return P(keys[-1][1])


# ---------------------------------------------------------------- la chorégraphie
X_SLEEP = -300.0
GRAV_DOWN = (0.0, 1.0)
GRAV_RIGHT = (1.0, 0.0)


class Tumble:
    """Corps rigide qui roule et rebondit dans la pièce pendant que la gravité tourne."""
    R = 72.0

    def __init__(self, c, theta):
        self.c, self.v, self.th, self.w = list(c), [0.0, 0.0], theta, 0.0
        self.contact = None

    def step(self, g, dt):
        self.v[0] += g[0] * dt
        self.v[1] += g[1] * dt
        self.c[0] += self.v[0] * dt
        self.c[1] += self.v[1] * dt
        self.th += self.w * dt
        self.w *= 0.99
        self.contact = None
        lim = ROOM - self.R
        for axis, sgn in ((0, -1), (0, 1), (1, -1), (1, 1)):
            if self.c[axis] * sgn > lim:
                self.c[axis] = lim * sgn
                n = [0.0, 0.0]
                n[axis] = -sgn                                 # normale vers l'intérieur
                vn = self.v[axis] * sgn
                if vn > 0:
                    self.v[axis] = -0.3 * self.v[axis]
                    self.contact = (axis, sgn, vn)
                other = 1 - axis
                self.v[other] *= 0.9
                roll = math.degrees((n[0] * self.v[1] - n[1] * self.v[0]) / self.R)
                self.w = 0.6 * self.w + 0.4 * roll


class Show:
    """Toute la démo, calculée image par image (la simulation d'abord, le dessin ensuite)."""

    def __init__(self):
        self.stones = make_stones()
        self.events = []                                       # (t, genre, position, force)
        self.frames = []
        self.cape = None
        self.slide = None
        self.t_corner = None
        self.tumble = None
        self.t_ceiling = None
        self.pick = None
        self.last_pose = None
        self.head_hits = []

    # --- Éclat
    def getup(self, F, u0, t, t0, g_dir, e_sit="surpris", e_up="etourdi"):
        """Se relever depuis le dos (tête du côté -u) : s'asseoir, passer à genoux, s'accroupir, se redresser."""
        lie = self.lie(F, u0, g_dir, e_sit)
        sit = sitting(F, u0 + 8, 1, g=g_dir, expr=e_sit)
        uf = u0 + 50
        kneel = Pose(F.w(uf - 12, 40), F.alpha + 38, 10, 10, 1, [F.w(uf - 44, 0), F.w(uf - 10, 0)],
                     [F.w(uf + 36, 0), F.w(uf + 26, 0)], g=g_dir, expr=e_up)
        crouch = stand(F, uf, 1, crouch=0.55, lean=24, g=g_dir, expr=e_up)
        J = build(crouch)
        crouch.hands = [v_add(J["legs"][0][1], v_mul(J["up"], 10)), v_add(J["legs"][1][1], v_mul(J["up"], 12))]
        up = stand(F, uf, 1, g=g_dir, expr=e_up)
        up.hands = swing_hands(up, [-6, 10])
        return keyed(t, [(t0, lie), (t0 + 0.30, sit), (t0 + 0.65, kneel), (t0 + 1.00, crouch), (t0 + 1.30, up)]), uf

    @staticmethod
    def lie(F, u0, g_dir, expr):
        p = lying(F, u0, head_first=-1, knees=0.25, g=g_dir, expr=expr)
        J = build(p)
        su = F.local(J["shoulder"])[0]
        p.hands = [F.w(su - 20, 0), F.w(su + 26, 0)]
        return p

    def hero(self, t):
        g = gravity(t)
        gd = v_mul(g, 1 / G) if v_len(g) > 1 else None
        # ---- 1. dort en apesanteur ; la flèche arrive, la gravité s'allume : il tombe à plat, sans se réveiller
        if t < T_ARRIVE[1]:
            x = X_SLEEP + 10 * t
            p = Pose((x, ROOM - 280 - 6 * math.sin(t)), -90 + 4 * math.sin(1.3 * t), 0, -4, 1, [None, None],
                     [None, None], expr="dort", g=None, emote=("zzz", t))
            self.sleep_end = p
            return p
        y0 = self.sleep_end.pelvis[1]
        u0 = self.sleep_end.pelvis[0]
        lie = self.lie(FLOOR, u0, GRAV_DOWN, "dort")
        t_land = T_ARRIVE[1] + math.sqrt(2 * (lie.pelvis[1] - y0) / G)
        self.t_land1 = t_land
        if t < t_land:                                         # chute libre : la posture ne change pas
            fall = t - T_ARRIVE[1]
            return replace(self.sleep_end, pelvis=(u0, y0 + 0.5 * G * fall * fall),
                           emote=("zzz", t) if fall < 0.3 else None)
        if abs(t - t_land) < 0.5 * DT + 1e-9 or not getattr(self, "land1_done", False):
            self.land1_done = True
            self.events.append((t, "thud", lie.pelvis, 0.8))
        if t < t_land + 0.14:                                  # les membres retombent au sol
            return lerp_pose(replace(self.sleep_end, pelvis=lie.pelvis, theta=lie.theta), lie,
                             ease_in((t - t_land) / 0.14))
        awake = replace(lie, expr="surpris", emote=("!", t - t_land - 0.14) if t < t_land + 0.7 else None)
        if t < 1.80:                                           # réveil en sursaut, regarde autour
            gz = (u0 - 300, ROOM - 200) if t < 1.55 else (u0 + 300, ROOM - 200)
            return replace(awake, gaze=gz, head=-8 + 10 * math.sin((t - t_land) * 6))
        # ---- 2. se relève, découvre la flèche, va voir
        if t < 3.10:
            p, uf = self.getup(FLOOR, u0, t, 1.80, GRAV_DOWN)
            if t > 2.80:                                       # secoue la tête
                p = replace(p, head=12 * math.sin((t - 2.80) * 30) * (1 - (t - 2.80) / 0.3))
            return p
        uf = u0 + 50
        up = stand(FLOOR, uf, 1, g=GRAV_DOWN, expr="curieux", gaze=A)
        up.hands = swing_hands(up, [-6, 10])
        if t < 3.60:
            k = ease_io((t - 3.1) / 0.25)
            return replace(up, head=-12 * k, theta=-4 * k, emote=("?", t - 3.2) if t > 3.2 else None)
        x_poke = -58.0
        if t < 4.75:
            return walk(FLOOR, t, 3.60, 4.75, uf, x_poke, 4, GRAV_DOWN, expr="curieux", gaze=A)
        # ---- 3. la pichenette : la flèche penche, la gravité aussi ; il vacille et se rattrape en se penchant
        base = stand(FLOOR, x_poke, 1, g=GRAV_DOWN, expr="curieux", gaze=arrow_point(t, A_HALF - 10), head=-10)
        base.hands = swing_hands(base, [-4, 8])
        tip = arrow_point(t, A_HALF - 6)
        if t < T_POKE + 0.02:
            near = v_add(tip, (-26, 16))
            if t < 5.10:
                return keyed(t, [(4.75, base), (5.10, replace(base, hands=[base.hands[0], near], theta=4))])
            if t < 5.25:
                return replace(base, hands=[base.hands[0], near], theta=4)
            return replace(base, hands=[base.hands[0], v_lerp(near, v_add(tip, (-6, 4)), ease_io((t - 5.25) / 0.05))],
                           theta=5)
        lean_eq = arrow_phi(t) - 90                            # équilibre : le buste s'aligne sur la gravité
        feet_eq = (x_poke - 10, x_poke + 44)
        if t < 6.30:
            s0 = replace(base, hands=[base.hands[0], v_add(tip, (-8, 6))], theta=5)
            topple = stand(FLOOR, x_poke + 6, 1, g=gd, lean=12, expr="surpris", gaze=arrow_point(t, 80))
            topple.hands = [v_add(topple.pelvis, (-70, -120)), v_add(topple.pelvis, (60, -130))]
            step = stand(FLOOR, x_poke + 22, 1, g=gd, lean=4, expr="peur", feet_u=feet_eq)
            step.hands = [v_add(step.pelvis, (-80, -60)), v_add(step.pelvis, (70, -150))]
            back = stand(FLOOR, x_poke + 18, 1, g=gd, lean=-32, expr="peur", feet_u=feet_eq)
            back.hands = [v_add(back.pelvis, (-90, -110)), v_add(back.pelvis, (40, -60))]
            eq = stand(FLOOR, x_poke + 20, 1, g=gd, lean=lean_eq, expr="surpris", feet_u=feet_eq)
            eq.hands = [v_add(eq.pelvis, (-70, -80)), v_add(eq.pelvis, (60, -90))]
            return keyed(t, [(T_POKE, s0), (5.45, topple), (5.62, step), (5.86, back), (6.08, eq), (6.30, eq)])
        eq = stand(FLOOR, x_poke + 20, 1, g=gd, lean=lean_eq, feet_u=feet_eq)
        eq.hands = swing_hands(eq, [-10, 14])
        if t < 7.10:                                           # comprend : les pierres… la flèche… « ! »
            if t < 6.55:
                gz, ex = (ROOM - 60, ROOM - 20), "curieux"
            elif t < 6.80:
                gz, ex = arrow_point(t, 60), "curieux"
            else:
                gz, ex = (0, 2000), "joie"
            return replace(eq, gaze=gz, expr=ex, emote=("!", t - 6.8) if t > 6.8 else None,
                           head=-10 if t < 6.8 else 0)
        # ---- 4. il pousse la flèche : elle tourne en s'éloignant de lui, la gravité bascule vers la droite
        g1, g2 = arrow_point(t, A_HALF - 12), arrow_point(t, A_HALF - 38)
        under = stand(FLOOR, 2, 1, g=gd, lean=arrow_phi(t) - 90 + 6, expr="decide", gaze=g1, head=-14,
                      feet_u=(-12, 14))
        under.pelvis = v_add(under.pelvis, (0, -6))            # sur la pointe des pieds
        if t < T_GRAB:
            return keyed(t, [(7.10, replace(eq, expr="decide")),
                             (7.30, replace(under, hands=swing_hands(under, [30, 50]))),
                             (T_GRAB, replace(under, hands=[g2, g1]))])
        if t < T_OFF:
            u = ease_io((t - T_GRAB) / (T_OFF - T_GRAB))
            p = stand(FLOOR, 2 + 10 * u, 1, g=gd, lean=6 + 16 * u, expr="decide", gaze=g1, head=-14, feet_u=(-12, 14))
            p.pelvis = v_add(p.pelvis, (0, -6 - 4 * u))
            return replace(p, hands=[g2, g1])
        pivot = FLOOR.w(1, 0)
        th0 = 22.0
        if t < T_FACE:                                         # la gravité le tire vers l'avant : il bascule
            u = ease_in((t - T_OFF) / (T_FACE - T_OFF))
            th = th0 + (90 - th0) * u
            pel = v_add(pivot, v_mul(up_vec(th), 70 - 57 * u), (0, -13 * u))
            p = Pose(pel, th, 0, -10, 1, [FLOOR.w(-12, 0), FLOOR.w(14, 0)], [None, None], g=gd, expr="surpris",
                     emote=("!", t - T_OFF))
            J = build(p)
            reach = v_add(J["shoulder"], v_mul(v_add(v_mul(up_vec(th), 0.6), (0, 0.8)), 76))
            p.hands = [reach, v_add(reach, (14, 6))]              # les mains en avant pour amortir
            return p
        if self.slide is None:
            self.slide = {"u": pivot[0] + 64, "v": 180.0, "t": T_FACE}
            self.events.append((t, "thud", FLOOR.w(pivot[0] + 100, 0), 0.6))
        if self.t_corner is None:                              # glisse à plat ventre jusqu'au coin… et dans les pierres
            s = self.slide
            if t > s["t"]:
                a = G * max(0.0, math.cos(math.radians(arrow_phi(t))))
                s["v"] += a * DT
                s["u"] += s["v"] * DT
                s["t"] = t
            if s["u"] >= ROOM - 141:
                s["u"] = ROOM - 141
                self.t_corner = t
                self.events.append((t, "thud", (ROOM, ROOM - 30), 1.0))
            return self.face_down(s["u"], gd, "peur")
        tc = self.t_corner
        head_u = -(ROOM - 30)                                  # repère du mur de droite : u = -y
        on_head = Pose(RWALL.w(head_u + 4, 34 + 107), 90, 0, 0, 1,
                       [RWALL.w(head_u + 40, 141 + 60), RWALL.w(head_u + 70, 141 + 44)],
                       [RWALL.w(head_u + 60, 0), RWALL.w(head_u + 90, 0)], g=GRAV_RIGHT, expr="etourdi")
        if t < 9.40:                                           # sur la tête dans le coin, sonné
            if t < tc + 0.14:
                return lerp_pose(self.face_down(ROOM - 141, gd, "peur"), on_head, ease_io((t - tc) / 0.14))
            hit = [h for h in self.head_hits if 0 <= t - h < 0.35]
            return replace(on_head, emote=("etoiles", t - tc), expr="surpris" if hit else "etourdi")
        head_pt = RWALL.w(head_u, 34)
        u_lie = head_u + 107
        lie_r = self.lie(RWALL, u_lie, GRAV_RIGHT, "surpris")
        if t < 9.75:                                           # bascule sur le dos (côté opposé au visage)
            u = ease_in((t - 9.40) / 0.35)
            th = 90 + (lie_r.theta - 90) * u
            pel = v_sub(head_pt, v_mul(up_vec(th), K.SPINE + K.NECK))
            return Pose(pel, th, 0, 0, 1, [None, None], [None, None], g=GRAV_RIGHT, expr="peur")
        # ---- 5. debout sur le mur devenu sol ; la flèche est hors de portée : il saute… trop court
        if t < 11.05:
            p, _ = self.getup(RWALL, u_lie, t, 9.75, GRAV_RIGHT, "surpris", "colere")
            return p
        uf = u_lie + 50
        u_jump = -A[1] - 6
        tip = arrow_point(t, A_HALF - 8)
        if t < 11.75:
            return walk(RWALL, t, 11.05, 11.75, uf, u_jump, 2, GRAV_RIGHT, expr="decide", gaze=tip)
        look_up = stand(RWALL, u_jump, 1, g=GRAV_RIGHT, expr="decide", gaze=tip, head=-24)
        look_up.hands = swing_hands(look_up, [-4, 6])
        crouch = stand(RWALL, u_jump, 1, crouch=0.6, lean=10, g=GRAV_RIGHT, expr="decide", head=-26, gaze=tip)
        crouch.hands = swing_hands(crouch, [-40, -30])
        t_up, v0 = 12.15, 680.0
        t_down = t_up + 2 * v0 / G
        if t < t_up:
            return keyed(t, [(11.75, look_up), (11.95, look_up), (t_up, crouch)])
        if t < t_down:                                         # saut balistique, bras tendus vers la pointe
            tau = t - t_up
            h = v0 * tau - 0.5 * G * tau * tau
            p = stand(RWALL, u_jump, 1, g=GRAV_RIGHT, expr="decide" if tau < 0.3 else "surpris", head=-26, gaze=tip)
            off = v_mul(RWALL.w(0, h), 1)
            off = v_sub(off, RWALL.w(0, 0))
            p.pelvis = v_add(p.pelvis, off)
            J = build(replace(p, hands=[None, None]))
            p.feet = [None, None]
            p.hands = [v_add(J["shoulder"], v_add(v_mul(J["up"], 66), v_mul(J["fwd"], -34))),
                       v_add(J["shoulder"], v_add(v_mul(J["up"], 64), v_mul(J["fwd"], 38)))]
            if tau > 0.5 * (t_down - t_up):                    # redescend : les jambes se tendent vers le sol
                p.feet = [RWALL.w(u_jump - 10, max(0.0, h - 6)), RWALL.w(u_jump + 10, max(0.0, h - 4))]
            return p
        land = stand(RWALL, u_jump, 1, crouch=0.5, lean=12, g=GRAV_RIGHT, expr="colere")
        land.hands = swing_hands(land, [30, 20])
        mad = stand(RWALL, u_jump, 1, g=GRAV_RIGHT, expr="colere", gaze=tip, head=-18)
        J = build(mad)
        mad.hands = [v_add(J["shoulder"], v_add(v_mul(J["up"], 40), v_mul(J["fwd"], 30 + 10 * math.sin(t * 40)))),
                     v_add(J["shoulder"], v_mul(J["up"], -62))]
        if t < 13.40:
            if t > t_down and not getattr(self, "land2_done", False):
                self.land2_done = True
                self.events.append((t, "thud", RWALL.w(u_jump, 0), 0.5))
            return keyed(t, [(t_down, land), (t_down + 0.2, mad), (13.40, mad)])
        # ---- 6. l'idée : une pierre ! Il en ramasse une et la lance sur la flèche
        if self.pick is None:
            near = [s for s in self.stones if s.p[0] > ROOM - s.r - 8 and -s.p[1] < u_jump - 60]
            self.pick = min(near or self.stones, key=lambda s: abs(-s.p[1] - (u_jump - 150)))
            self.pick_u = -self.pick.p[1]
        stone = self.pick
        u_stand = self.pick_u + 44
        think = stand(RWALL, u_jump, 1, g=GRAV_RIGHT, expr="curieux", gaze=tuple(stone.p), head=14)
        J = build(think)
        think.hands = [v_add(J["head"], v_add(v_mul(J["up"], -28), v_mul(J["fwd"], 24))), None]
        if t < 13.70:
            return replace(think, emote=("!", t - 13.58) if t > 13.58 else None,
                           expr="joie" if t > 13.58 else "curieux")
        if t < 14.20:
            return walk(RWALL, t, 13.70, 14.20, u_jump, u_stand, 2, GRAV_RIGHT, expr="joie", gaze=tuple(stone.p))
        bend = stand(RWALL, u_stand, -1, crouch=0.75, lean=40, g=GRAV_RIGHT, expr="decide", head=20,
                     gaze=tuple(stone.p))
        grab = replace(bend, hands=[v_add(tuple(stone.p), (0, 12)), tuple(stone.p)])
        if t < 14.50:
            p = keyed(t, [(14.20, stand(RWALL, u_stand, -1, g=GRAV_RIGHT, expr="decide")), (14.40, grab), (14.50, grab)])
            if t >= 14.40:
                stone.held = True
            return p
        tgt = self.hit_target
        hold = stand(RWALL, u_stand - 4, 1, g=GRAV_RIGHT, expr="decide", gaze=tgt, head=-20)
        J = build(hold)
        hold.hands = [v_add(J["shoulder"], v_add(v_mul(J["up"], 20), v_mul(J["fwd"], 30))),
                      v_add(J["shoulder"], v_add(v_mul(J["up"], -10), v_mul(J["fwd"], 40)))]
        wind = stand(RWALL, u_stand - 14, 1, g=GRAV_RIGHT, lean=-18, expr="decide", gaze=tgt, head=-25,
                     feet_u=(u_stand - 34, u_stand + 6))
        J = build(wind)
        wind.hands = [v_add(J["shoulder"], v_add(v_mul(J["up"], 30), v_mul(J["fwd"], 50))),
                      v_add(J["shoulder"], v_add(v_mul(J["up"], 50), v_mul(J["fwd"], -55)))]
        release = stand(RWALL, u_stand, 1, g=GRAV_RIGHT, lean=16, expr="decide", gaze=tgt, head=-25,
                        feet_u=(u_stand - 34, u_stand + 6))
        J = build(release)
        release.hands = [v_add(J["shoulder"], v_add(v_mul(J["up"], -40), v_mul(J["fwd"], -30))),
                         v_add(J["shoulder"], v_add(v_mul(J["up"], 60), v_mul(J["fwd"], 45)))]
        follow = stand(RWALL, u_stand + 6, 1, g=GRAV_RIGHT, lean=26, expr="joie", gaze=tgt, head=-25,
                       feet_u=(u_stand - 34, u_stand + 6))
        J = build(follow)
        follow.hands = [v_add(J["shoulder"], v_add(v_mul(J["up"], -40), v_mul(J["fwd"], -20))),
                        v_add(J["shoulder"], v_add(v_mul(J["up"], -30), v_mul(J["fwd"], 70)))]
        if t < 15.60:
            p = keyed(t, [(14.50, grab), (14.70, hold), (14.95, wind), (15.00, release), (15.25, follow),
                          (15.60, replace(follow, expr="surpris" if t > T_HIT + 0.02 else "joie", gaze=A,
                                          emote=("!", t - T_HIT) if t > T_HIT else None))],
                      ease=lambda u: ease_io(u) if t < 14.95 or t > 15.0 else u)
            if t >= 15.0 and stone.held:                       # lâche la pierre : elle part vers la flèche
                stone.held = False
                self.throw(t, stone)
            return p
        # ---- 7. la flèche tourne sur elle-même : la gravité aussi ; il roule et rebondit comme un corps inerte
        if self.tumble is None:
            c = v_add(self.last_pose.pelvis, v_mul(up_vec(self.last_pose.theta), 30))
            self.tumble = Tumble(c, self.last_pose.theta)
            self.tumble_from = self.last_pose
        tb = self.tumble
        if self.t_ceiling is None:
            tb.step(g, DT)
            if tb.contact and tb.contact[2] > 150:
                self.events.append((t, "thud", tuple(tb.c), min(1.0, tb.contact[2] / 900)))
            if t > 18.2 and tb.contact and tb.contact[0] == 1 and tb.contact[1] == -1:
                self.t_ceiling = t
        pel = v_sub(tuple(tb.c), v_mul(up_vec(tb.th), 30))
        fl = t * 9
        flail = Pose(pel, tb.th, 10 * math.sin(fl), 0, 1, [None, None], [None, None], g=gd, expr="peur")
        flail.hands = [v_add(pel, v_mul(unit(tb.th - 90 + 70 * math.sin(fl)), 120)),
                       v_add(pel, v_mul(unit(tb.th - 90 + 180 + 70 * math.cos(fl * 1.3)), 120))]
        flail.feet = [v_add(pel, v_mul(unit(tb.th + 90 + 30 * math.sin(fl * 0.8)), 70)),
                      v_add(pel, v_mul(unit(tb.th + 90 - 30 * math.cos(fl * 0.9)), 66))]
        if self.t_ceiling is None:
            self.flail_last = flail
            if t < 15.85:
                return lerp_pose(self.tumble_from, flail, ease_io((t - 15.60) / 0.25))
            return flail
        # ---- 8. atterrit au plafond : sonné, se redresse… et la dernière pierre lui tombe sur la tête
        tcl = self.t_ceiling
        flat, sit = self.ceiling_poses()
        hit = [h for h in self.head_hits if h > tcl + 0.3]
        if t < tcl + 0.25:
            return lerp_pose(self.flail_last, flat, ease_io((t - tcl) / 0.25))
        if t < tcl + 0.6:
            return replace(flat, emote=("etoiles", t - tcl))
        p = keyed(t, [(tcl + 0.6, flat), (tcl + 0.95, sit)])
        p = replace(p, emote=("etoiles", t - tcl))
        if hit and t >= hit[0]:
            dt_h = t - hit[0]
            p = replace(p, expr="colere" if dt_h > 0.35 else "surpris", emote=("!", dt_h) if dt_h < 0.6 else None,
                        head=-16 * math.exp(-dt_h * 6) + 4)
        return p

    def face_down(self, u, gd, expr):
        p = Pose(FLOOR.w(u, 13), 90 - 11, 0, -10, 1, [FLOOR.w(u - 64, 6), FLOOR.w(u - 58, 10)],
                 [FLOOR.w(u + 150, 4), FLOOR.w(u + 136, 8)], g=gd, expr=expr)
        return p

    def ceiling_poses(self):
        tb = self.tumble
        pel = v_sub(tuple(tb.c), v_mul(up_vec(tb.th), 30))
        u_c = CEIL.local(pel)[0]
        head_first = 1 if CEIL.local(v_add(pel, up_vec(tb.th)))[0] > u_c else -1
        flat = lying(CEIL, u_c, head_first=head_first, knees=0.4, g=(0.0, -1.0), expr="etourdi")
        J = build(flat)
        su = CEIL.local(J["shoulder"])[0]
        flat.hands = [CEIL.w(su - 30, 0), CEIL.w(su + 30, 0)]
        sit = sitting(CEIL, u_c - head_first * 20, -head_first, g=(0.0, -1.0), expr="etourdi")
        return flat, sit

    # --- lancer
    @property
    def hit_target(self):
        return arrow_point(T_HIT, 60)

    def throw(self, t, stone):
        """Vitesse de lancer calculée pour toucher le manche de la flèche à T_HIT (balistique, gravité à droite)."""
        tau = T_HIT - t
        target = v_add(arrow_point(T_HIT, 60), (0, stone.r + 6))    # touche le manche par en dessous : elle tourne
        g = gravity(t)
        stone.v = [(target[0] - stone.p[0] - 0.5 * g[0] * tau * tau) / tau,
                   (target[1] - stone.p[1] - 0.5 * g[1] * tau * tau) / tau]
        stone.w = -600
        stone.drag = 0.0                                       # trajectoire calculée sans frottement
        self.thrown = stone
        self.events.append((t, "whoosh", tuple(stone.p), 0.7))

    # --- simulation d'une image
    def step(self, t):
        pose = self.hero(t)
        self.last_pose = pose
        J = build(pose)
        g = gravity(t)
        # pierres
        body = [(J["head"], K.HEAD_R), (J["chest"], 16), (J["pelvis"], 16), (J["legs"][0][1], 10),
                (J["legs"][1][1], 10), (J["legs"][0][2], 10), (J["legs"][1][2], 10), (J["arms"][0][1], 8),
                (J["arms"][1][1], 8)]
        prev_body = getattr(self, "prev_body", body)
        self.prev_body = body
        sub = 4
        for _ in range(sub):
            h = DT / sub
            for s in self.stones:
                if s.held:
                    hand = J["arms"][1][2]
                    s.p = [hand[0], hand[1]]
                    s.v = [0.0, 0.0]
                    continue
                s.v[0] = (s.v[0] + g[0] * h) * (1 - s.drag * h)
                s.v[1] = (s.v[1] + g[1] * h) * (1 - s.drag * h)
                s.p[0] += s.v[0] * h
                s.p[1] += s.v[1] * h
                s.a += s.w * h
                lim = ROOM - s.r
                for axis in (0, 1):
                    for sgn in (-1, 1):
                        if s.p[axis] * sgn > lim:
                            s.p[axis] = lim * sgn
                            vn = s.v[axis] * sgn
                            if vn > 0:
                                if vn > 220:
                                    q = list(s.p)
                                    q[axis] += sgn * s.r
                                    self.events.append((t, "clack", tuple(q), min(1.0, vn / 1400)))
                                s.v[axis] = -0.32 * s.v[axis]
                            other = 1 - axis
                            s.v[other] *= 0.975
                            n = [0.0, 0.0]
                            n[axis] = -sgn
                            s.w = math.degrees((n[0] * s.v[1] - n[1] * s.v[0]) / s.r)
            # pierre contre pierre
            for i in range(len(self.stones)):
                for j in range(i + 1, len(self.stones)):
                    a, b = self.stones[i], self.stones[j]
                    if a.held or b.held:
                        continue
                    d = v_sub(b.p, a.p)
                    L = v_len(d)
                    m = a.r + b.r
                    if 1e-6 < L < m:
                        n = (d[0] / L, d[1] / L)
                        pen_ = (m - L) / 2
                        a.p = [a.p[0] - n[0] * pen_, a.p[1] - n[1] * pen_]
                        b.p = [b.p[0] + n[0] * pen_, b.p[1] + n[1] * pen_]
                        rv = (b.v[0] - a.v[0]) * n[0] + (b.v[1] - a.v[1]) * n[1]
                        if rv < 0:
                            jimp = -(1.2) * rv / 2
                            a.v = [a.v[0] - jimp * n[0], a.v[1] - jimp * n[1]]
                            b.v = [b.v[0] + jimp * n[0], b.v[1] + jimp * n[1]]
                            if -rv > 260:
                                self.events.append((t, "clack", tuple(v_lerp(a.p, b.p, 0.5)), min(1.0, -rv / 1400)))
            # pierres contre Éclat (son corps pousse les pierres ; une pierre sur la tête le fait réagir)
            for s in self.stones:
                if s.held or (s is getattr(self, "thrown", None) and t < T_HIT + 0.3):
                    continue
                for k, (q, r) in enumerate(body):
                    d = v_sub(s.p, q)
                    L = v_len(d)
                    if 1e-6 < L < r + s.r:
                        n = (d[0] / L, d[1] / L)
                        s.p = [q[0] + n[0] * (r + s.r), q[1] + n[1] * (r + s.r)]
                        qv = v_mul(v_sub(q, prev_body[k][0]), FPS)
                        rel = (s.v[0] - qv[0]) * n[0] + (s.v[1] - qv[1]) * n[1]
                        if rel < 0:
                            s.v = [s.v[0] - 1.3 * rel * n[0], s.v[1] - 1.3 * rel * n[1]]
                            sp = v_len(s.v)
                            cap = 1400 if v_len(qv) < 50 else 450      # un membre qui bouge pousse, il ne catapulte pas
                            if sp > cap:
                                s.v = [s.v[0] * cap / sp, s.v[1] * cap / sp]
                            if -rel > 250:
                                self.events.append((t, "bonk" if k == 0 else "clack", tuple(s.p), min(1.0, -rel / 1200)))
                                if k == 0 and t > 8.5 and (not self.head_hits or t - self.head_hits[-1] > 0.3):
                                    self.head_hits.append(t)
        # la pierre lancée touche la flèche
        th = getattr(self, "thrown", None)
        if th is not None and not getattr(self, "hit_done", False) and t >= T_HIT - 1e-6:
            self.hit_done = True
            th.v = [th.v[0] * 0.4, abs(th.v[1]) * 0.45]
            self.events.append((t, "clang", tuple(arrow_point(t, 60)), 1.0))
        # dernière pierre : quand il atterrit au plafond, la pierre restée la plus loin finit sa chute sur sa tête
        if self.t_ceiling is not None and not getattr(self, "last_set", False):
            self.last_set = True
            far = max((s for s in self.stones if not s.held), key=lambda s: s.p[1])
            t_hit = max(self.t_ceiling + 0.95, 19.4)
            head = self.predict_head(t_hit)
            tau = t_hit - t
            far.v = [(head[0] - far.p[0] - 0.5 * g[0] * tau * tau) / tau,
                     (head[1] + K.HEAD_R + far.r - far.p[1] - 0.5 * g[1] * tau * tau) / tau]
            far.drag = 0.0
            self.last_stone = far
        # cape
        anchor = v_add(J["neck"], v_mul(J["fwd"], -5))
        if self.cape is None:
            self.cape = K.Cape(anchor)
        gg = g if v_len(g) > 1 else (0.0, 0.0)
        self.cape.step(anchor, v_mul(J["fwd"], -1), gg, DT, flutter=1.0 if v_len(g) < 1 else 0.25, t=t,
                       bounds=(-ROOM + 2, -ROOM + 2, ROOM - 2, ROOM - 2))
        return pose

    def predict_head(self, t):
        return build(self.ceiling_poses()[1])["head"]

    def run(self):
        for f in range(int(DURATION * FPS)):
            t = f / FPS
            pose = self.step(t)
            self.frames.append({
                "pose": pose, "cape": list(self.cape.p),
                "stones": [(tuple(s.p), s.r, s.sides, s.a) for s in self.stones],
                "arrow": (arrow_center(t), arrow_phi(t)),
            })
        return self


# ---------------------------------------------------------------- caméra : plans coupés
# (début, mode, centre, zoom début, zoom fin, rotation début, rotation fin). Rotation : la caméra « tombe » avec lui,
# il reste debout à l'écran et c'est la pièce qui tourne (le plan large d'avant montre la vraie situation).
SHOTS = [
    (0.00, "fixe", (0.0, 0.0), 1.05, 1.1, 0, 0),
    (1.90, "suivi", None, 2.6, 2.6, 0, 0),
    (3.55, "fixe", (-170.0, ROOM - 210), 1.7, 1.75, 0, 0),
    (5.20, "fixe", (40.0, ROOM - 230), 1.45, 1.5, 0, 0),
    (7.05, "fixe", (20.0, ROOM - 240), 2.1, 2.15, 0, 0),
    (7.75, "fixe", (0.0, 0.0), 1.05, 1.07, 0, 0),
    (9.40, "suivi", None, 2.0, 2.1, 0, 90),
    (11.70, "fixe", (250.0, ROOM - 290), 1.6, 1.65, 90, 90),
    (13.00, "suivi", None, 2.4, 2.45, 90, 90),
    (14.55, "suivi", None, 2.1, 2.2, 90, 90),
    (15.25, "fixe", (160.0, ROOM - 270), 1.5, 1.6, 90, 90),
    (15.90, "fixe", (0.0, 0.0), 1.05, 1.07, 0, 0),
    (18.45, "suivi", None, 2.4, 2.5, 180, 180),
]


# ---------------------------------------------------------------- tempo : vitesse du récit selon les moments
# (début dans le récit, vitesse). Les moments de jeu (réveil, surprise, idée) respirent ; chutes et chaos restent vifs.
TEMPO = [(0.00, 0.60), (0.70, 0.90), (1.35, 0.55), (3.60, 0.75), (5.30, 0.85), (6.30, 0.55), (7.45, 0.85),
         (8.50, 0.62), (11.05, 0.70), (13.70, 0.68), (15.55, 0.90), (18.30, 0.58)]


def _tempo_rate(x):
    """Vitesse du récit en x, avec un passage doux (0,3 s) à chaque changement."""
    for (a, ra), (b, rb) in zip(TEMPO, TEMPO[1:]):
        if abs(x - b) < 0.15:
            return ra + (rb - ra) * ease_io((x - b + 0.15) / 0.3)
    r = TEMPO[0][1]
    for a, ra in TEMPO:
        if x >= a:
            r = ra
    return r


def _build_tempo():
    story = [0.0]
    while story[-1] < DURATION - 1e-9:
        x = story[-1]
        story.append(min(DURATION - 1e-6, x + _tempo_rate(x) / FPS))
        if story[-1] >= DURATION - 1e-6:
            break
    return np.array(story)


F2S = _build_tempo()                                   # temps du récit pour chaque image du film
FILM_DUR = (len(F2S) - 1) / FPS


def s2f(x):
    """Instant du film correspondant à un instant du récit."""
    return float(np.interp(x, F2S, np.arange(len(F2S)) / FPS))


def shot_state(k, t, show, f):
    """Cadrage voulu par le plan k à l'instant t (centre, zoom, rotation)."""
    t0, mode, center, z0, z1, r0, r1 = SHOTS[k]
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DURATION
    zoom = z0 + (z1 - z0) * ease_io((t - t0) / (t1 - t0))
    rot = r0 + (r1 - r0) * ease_io((t - t0) / 1.2)
    if mode == "suivi":                                        # suit le buste, lissé
        acc, wsum = (0.0, 0.0), 0.0
        for j in range(max(0, f - 40), f + 1):
            J = build(show.frames[j]["pose"])
            q = v_lerp(J["pelvis"], J["head"], 0.45)
            w = math.exp(-(f - j) / 14)
            acc, wsum = v_add(acc, v_mul(q, w)), wsum + w
        center = v_mul(acc, 1 / wsum)
    return center, zoom, rot


def camera(t, show, f):
    """Caméra continue : pas de coupe sèche, elle glisse, zoome et pivote d'un cadrage au suivant."""
    def blended(k):
        center, zoom, rot = shot_state(k, t, show, f)
        if k > 0:
            pc, pz, pr = blended(k - 1)                        # le plan d'avant peut être encore en mouvement
            trans = 0.8 + 0.1 * abs(rot - pr) / 180            # une grande rotation prend un peu plus de temps
            u = (t - SHOTS[k][0]) / trans
            if u < 1:
                e = ease_io(u)
                center = v_lerp(pc, center, e)
                zoom = math.exp(math.log(pz) + (math.log(zoom) - math.log(pz)) * e)
                rot = pr + (rot - pr) * e
        return center, zoom, rot
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t)
    center, zoom, rot = blended(k)
    shake = 0.0
    for (te, kind, pos, force) in show.events:
        dt = t - te
        if kind in ("thud", "boom", "clang") and 0 <= dt < 0.4:
            shake += (18 if kind == "boom" else 10) * force * math.exp(-dt * 10)
    cx = center[0] + shake * math.sin(t * 57) / zoom
    cy = center[1] + shake * math.cos(t * 43) / zoom
    return (cx, cy), zoom, rot


# ---------------------------------------------------------------- dessin
def draw_arrow(c, center, phi, lw, glow=1.0, screen_rot=0.0):
    d = unit(phi)
    n = (-d[1], d[0])
    tail = v_sub(center, v_mul(d, A_HALF))
    tip = v_add(center, v_mul(d, A_HALF))
    neck = v_sub(tip, v_mul(d, 34))
    c.drawLine(*tail, *neck, pen(GOLD, 22 * lw, 90 * glow, glow=16 * lw))
    c.drawLine(*tail, *neck, pen(GOLD, 8 * lw))
    head = skia.Path()
    head.moveTo(*v_add(tip, v_mul(d, 4)))
    head.lineTo(*v_add(neck, v_mul(n, 24)))
    head.lineTo(*v_add(neck, v_mul(n, -24)))
    head.close()
    c.drawPath(head, brush(GOLD, 120 * glow, glow=14 * lw))
    c.drawPath(head, brush(GOLD))
    font = skia.Font(skia.Typeface("DejaVu Serif", skia.FontStyle.Italic()), 58)
    side = n if n[1] <= 0.01 else v_mul(n, -1)
    gpos = v_add(center, v_mul(side, 46))
    c.save()                                                   # la lettre reste droite à l'écran
    c.translate(*gpos)
    c.rotate(-screen_rot)
    c.drawString("g", -14, 14, font, brush(GOLD))
    c.restore()


def draw_stone(c, pos, r, sides, ang, lw):
    path = skia.Path()
    pts = [v_add(pos, v_mul(unit(ang + i * 360 / sides + 9 * math.sin(i * 2.3)), r)) for i in range(sides)]
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    path.close()
    c.drawPath(path, brush((10, 10, 16)))
    c.drawPath(path, pen(LINE, 3 * lw, 150, glow=5 * lw))
    c.drawPath(path, pen(LINE, 2.4 * lw))
    for q in pts:
        c.drawCircle(*q, 3.2 * lw, brush((0, 0, 0)))
        c.drawCircle(*q, 3.2 * lw, pen(LINE, 1.6 * lw))


def frame_at(show, t):
    """État interpolé entre deux images de la simulation (le récit peut avancer moins vite que le film)."""
    x = t * FPS
    f0 = min(int(x), len(show.frames) - 2)
    a = min(max(x - f0, 0.0), 1.0)
    A, B = show.frames[f0], show.frames[f0 + 1]
    return f0, {
        "pose": lerp_pose(A["pose"], B["pose"], a) if a > 1e-6 else A["pose"],
        "cape": [v_lerp(p, q, a) for p, q in zip(A["cape"], B["cape"])],
        "stones": [(v_lerp(p[0], q[0], a), p[1], p[2], p[3] + (q[3] - p[3]) * a) for p, q in zip(A["stones"], B["stones"])],
        "arrow": (arrow_center(t), arrow_phi(t)),
    }


def draw_frame(c, show, i, stars):
    t = float(F2S[min(i, len(F2S) - 1)])
    f, fr = frame_at(show, t)
    (cx, cy), zoom, rot = camera(t, show, f)
    c.clear(skia.ColorBLACK)
    c.save()
    c.translate(W / 2, H / 2)
    c.rotate(rot)
    for x, y, s, ph, depth in stars:                          # étoiles lointaines (parallaxe)
        sx = ((x - cx * depth * 0.5) % 2400) - 1200
        sy = ((y - cy * depth * 0.5) % 2400) - 1200
        c.drawCircle(sx, sy, s, brush(LINE, 150 * (0.5 + 0.5 * math.sin(ph + t * 1.3))))
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)
    lw = 1 / zoom
    # la pièce : quatre murs, points aux sommets et repères réguliers
    room = skia.Rect.MakeLTRB(-ROOM, -ROOM, ROOM, ROOM)
    c.drawRect(room, pen(LINE, 10 * lw, 60, glow=10 * lw))
    c.drawRect(room, pen(LINE, 3.2 * lw))
    for i in range(-2, 3):
        for q in ((i * 240, -ROOM), (i * 240, ROOM), (-ROOM, i * 240), (ROOM, i * 240)):
            c.drawCircle(*q, 4 * lw, brush(LINE, 170))
    for q in ((-ROOM, -ROOM), (ROOM, -ROOM), (ROOM, ROOM), (-ROOM, ROOM)):
        c.drawCircle(*q, 9 * lw, brush((0, 0, 0)))
        c.drawCircle(*q, 9 * lw, pen(LINE, 2.6 * lw))
    # flèche (traînée à l'arrivée)
    center, phi = fr["arrow"]
    if center is not None:
        if t < T_ARRIVE[1] + 0.05:
            for k in range(1, 8):
                q = arrow_center(max(T_ARRIVE[0], t - k * 0.012)) or center
                c.drawLine(q[0], q[1] - A_HALF, q[0], q[1] + A_HALF, pen(GOLD, 10 * lw, 110 - 12 * k))
        draw_arrow(c, center, phi, lw, screen_rot=rot)
    # effets
    for (te, kind, pos, force) in show.events:
        dt = t - te
        if kind == "boom" and 0 <= dt < 0.9:
            e = ease_out(dt / 0.9)
            c.drawCircle(*pos, 60 + 900 * e, pen(GOLD, 8 * lw, 230 * (1 - e), glow=12 * lw))
            c.drawCircle(*pos, 60 + 500 * e, pen((255, 240, 210), 3 * lw, 200 * (1 - e)))
            c.drawCircle(*pos, 160 * (1 - e) + 20, brush((255, 240, 200), 200 * (1 - e), glow=60))
        elif kind == "thud" and 0 <= dt < 0.5:
            e = ease_out(dt / 0.5)
            for i in range(9):
                a = i * 40 + 13
                r0, r1 = 40 + 120 * e, 60 + 150 * e
                c.drawLine(*v_add(pos, v_mul(unit(a), r0)), *v_add(pos, v_mul(unit(a), r1)),
                           pen(LINE, 3 * lw, 200 * (1 - e) * force))
        elif kind == "clang" and 0 <= dt < 0.6:
            e = ease_out(dt / 0.6)
            c.drawCircle(*pos, 30 + 200 * e, brush((255, 236, 200), 220 * (1 - e), glow=30))
            for i in range(12):
                a = i * 30
                c.drawLine(*v_add(pos, v_mul(unit(a), 20 + 160 * e)), *v_add(pos, v_mul(unit(a), 40 + 220 * e)),
                           pen(GOLD, 4 * lw, 255 * (1 - e)))
        elif kind == "bonk" and 0 <= dt < 0.5 and force > 0.25:
            e = ease_out(dt / 0.5)
            for i in range(8):
                a = i * 45 + 20
                c.drawLine(*v_add(pos, v_mul(unit(a), 10 + 50 * e)), *v_add(pos, v_mul(unit(a), 24 + 70 * e)),
                           pen((255, 220, 120), 3.5 * lw, 255 * (1 - e)))
    # pierres
    for (pos, r, sides, ang) in fr["stones"]:
        draw_stone(c, pos, r, sides, ang, lw)
    # Éclat et sa cape
    cape = K.Cape((0, 0))
    cape.p = fr["cape"]
    K.draw(c, fr["pose"], t, cape, screen_rot=rot)
    c.restore()


# ---------------------------------------------------------------- son
def soundtrack(show, path):
    from satisfying.engine import PROGRESSIONS, Sound
    import wave
    SR = 48000
    D = FILM_DUR
    n = int(D * SR)
    mix = np.zeros((n, 2))
    fr = int(D * FPS)

    def env(keys0):
        out = []
        for k in range(fr):
            x = k / FPS
            keys = [(s2f(a) if a < DURATION else D, v) for a, v in keys0]
            v = keys[-1][1]
            for (a, va), (b, vb) in zip(keys, keys[1:]):
                if a <= x < b:
                    v = va + (vb - va) * (x - a) / (b - a)
                    break
            out.append(v)
        return out
    layers = []
    music = Sound(np.random.default_rng(5), key="ré", timbre="kalimba", prog=PROGRESSIONS[1])
    music.bar = 2.0
    for t in np.arange(s2f(3.6), s2f(15.5), 0.3):              # petite mélodie qui avance avec lui
        if not (s2f(8.0) < t < s2f(9.8)):
            music.hit(float(t), 0.28)
    for t, st in [(1.35, 4), (3.2, 7), (5.3, 9), (6.8, 11), (13.55, 11), (15.55, 14), (19.4, 11)]:
        music.hit(s2f(t), 0.8, step=st)
    layers.append((music, 0.35))
    fx = Sound(np.random.default_rng(6), key="ré", timbre="cristal", prog=PROGRESSIONS[0])
    last = {}
    for (te, kind, pos, force) in sorted((s2f(e[0]),) + tuple(e[1:]) for e in show.events):
        if kind == "clack":
            if te - last.get(kind, -1) < 0.05:
                continue
            last[kind] = te
            fx.hit(te, 0.25 + 0.5 * force)
        elif kind in ("thud", "boom"):
            fx.hit(te, 0.9 * max(force, 0.5), step=0, octave=-1)
        elif kind in ("clang", "bonk"):
            fx.hit(te, 0.9, step=9, octave=1)
        elif kind == "whoosh":
            fx.hit(te, 0.4, step=4, octave=1)
    fx.bed("vent", env([(0, 0.15), (0.5, 0.2), (0.75, 0.8), (1.3, 0.1), (7.8, 0.1), (8.3, 0.7), (8.9, 0.1),
                        (15.5, 0.1), (16.0, 1.0), (18.3, 0.8), (18.8, 0.1), (20, 0.1)]), 1.0)
    layers.append((fx, 0.25))
    for i, (snd, pad) in enumerate(layers):
        wav = Path(path).with_name(f"f{i}.wav")
        snd.render(D, wav, pad_level=pad)
        with wave.open(str(wav)) as w:
            part = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float).reshape(-1, 2)[:n] / 32767
        mix[:len(part)] += part / max(1e-9, np.abs(part).max()) * (1.0 if i else 0.8)
    mix /= max(1e-9, np.abs(mix).max() / 0.9)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- rendu
SHOW = None


def get_show():
    global SHOW
    if SHOW is None:
        SHOW = Show()
        SHOW.events.append((T_ARRIVE[1], "boom", A, 1.0))
        SHOW.run()
    return SHOW


def make_stars():
    r = np.random.default_rng(3)
    n = 420
    return np.column_stack([r.uniform(0, 2400, n), r.uniform(0, 2400, n), r.power(4, n) * 2.2 + 0.5,
                            r.uniform(0, 6.28, n), r.uniform(0.2, 0.6, n)])


def render_video(f0, f1, path):
    show = get_show()
    stars = make_stars()
    surf = skia.Surface(W, H)
    ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        draw_frame(surf.getCanvas(), show, f, stars)
        ff.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
    ff.stdin.close()
    ff.wait()
    return str(path)


def _part(args):
    return render_video(*args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--images", default=None)
    ap.add_argument("--morceaux", type=int, default=1)
    a = ap.parse_args()
    show = get_show()
    if a.images:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        surf = skia.Surface(W, H)
        stars = make_stars()
        for s in a.images.split(","):
            draw_frame(surf.getCanvas(), show, min(int(round(float(s) * FPS)), len(F2S) - 1), stars)
            surf.makeImageSnapshot().save(str(out / f"t{float(s):06.2f}.png"), skia.kPNG)
        return
    total = len(F2S)
    n = max(1, a.morceaux)
    cuts = [total * i // n for i in range(n + 1)]
    with tempfile.TemporaryDirectory() as tmp:
        parts = [(cuts[i], cuts[i + 1], Path(tmp) / f"v{i}.mp4") for i in range(n)]
        if n == 1:
            render_video(*parts[0])
        else:
            import multiprocessing as mp
            with mp.get_context("fork").Pool(n) as pool:
                pool.map(_part, parts)
        lst = Path(tmp) / "liste.txt"
        lst.write_text("".join(f"file '{p[2]}'\n" for p in parts))
        video = Path(tmp) / "v.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(video)], check=True)
        audio = Path(tmp) / "a.wav"
        soundtrack(show, audio)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-i", str(audio),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.out],
                       check=True)
    print(a.out)


if __name__ == "__main__":
    main()
