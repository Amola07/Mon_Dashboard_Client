"""« La flèche », actes 2 à 4 : la maîtrise, l'escalade, la résolution.

Même règle qu'à l'acte 1 — la gravité suit la flèche — prolongée logiquement :
  • acte 2 : il bâtit une tour de pierres, attrape la flèche, l'arrache… et la gravité le suit partout où il la pointe ;
  • acte 3 : la longueur de la flèche, c'est la force : trop courte tout flotte, trop longue tout s'écrase… elle casse ;
  • acte 4 : deux flèches, deux gravités qui s'additionnent. Il oppose la sienne à l'autre : plus rien ne pèse.
    Il réunit les deux flèches, elles s'annulent ; il se rendort en apesanteur — la vidéo boucle sur la première image.

La suite est une chaîne de phases : chacune démarre là où la précédente s'est arrêtée (position, vitesse, posture).
Chutes, sauts et dérives sont balistiques ; les atterrissages sont détectés, pas programmés à l'avance.
"""
import math
from dataclasses import replace

from . import corps as K
from . import fleche as F
from .corps import Frame, Pose, build, lerp_pose, stand, up_vec, v_add, v_len, v_lerp, v_mul, v_sub

R = F.ROOM
G = F.G
DT = F.DT
LWALL = Frame((-R, 0.0), 90)
SURFACES = [(F.FLOOR, (0.0, 1.0)), (F.CEIL, (0.0, -1.0)), (F.RWALL, (1.0, 0.0)), (LWALL, (-1.0, 0.0))]
L0 = 240.0                                                     # longueur normale de la flèche
CENTER_R = (0.0, -40.0)                                        # là où s'immobilise la flèche folle


def ease(u):
    return F.ease_io(u)


def down_phi(Fr):
    """Direction « vers le sol » d'une surface (degrés)."""
    return Fr.alpha + 90


def surface_for(g):
    n = v_len(g) or 1.0
    return max(SURFACES, key=lambda s: (g[0] * s[1][0] + g[1] * s[1][1]) / n)[0]


def turn(a, b, u):
    return a + ((b - a + 180) % 360 - 180) * u


# ---------------------------------------------------------------- outils sur Éclat
def hold(show, p, phi, L, spread=16.0, dist=30.0):
    """Il tient sa flèche à deux mains devant lui ; renvoie le centre de la flèche."""
    J = build(replace(p, hands=[None, None]))
    c = v_add(J["shoulder"], v_mul(J["fwd"], dist), v_mul(J["up"], -12))
    d = F.unit(phi)
    s = min(spread, 70.0)
    p.hands = [v_sub(c, v_mul(d, s)), v_add(c, v_mul(d, s))]
    return c


def set_held(show, c, phi, L):
    arrows = [a for a in show.arrows if a["kind"] not in ("held", "fixed")]     # la flèche fixe, c'est celle qu'il tient
    show.arrows = [dict(kind="held", c=c, phi=phi, L=L)] + arrows


def grav(show):
    g = (0.0, 0.0)
    for a in show.arrows:
        g = v_add(g, v_mul(F.unit(a["phi"]), G * a["L"] / L0))
    return g


def standing(Fr, u, facing, g=None, **kw):
    return stand(Fr, u, facing, g=g or F.unit(down_phi(Fr)), **kw)


# ---------------------------------------------------------------- les phases
class Suite:
    def __init__(self, show, t):
        self.show = show
        self.phases = [self.stand_up, self.look, self.carry(0), self.carry(1), self.carry(2), self.hop, self.jump_grab,
                       self.hang, self.fall_with_arrow, self.land(), self.tilt, self.flip, self.fall(), self.land(),
                       self.park_rotate(0), self.fall(hop=260), self.land(),
                       self.park_rotate(1), self.fall(hop=260), self.land(),
                       self.park_rotate(2), self.fall(hop=260), self.land(proud=True),
                       self.stretch_small, self.shrink, self.moon(620, flip=True), self.land(soft=True),
                       self.moon(430, flip=False), self.land(soft=True), self.greed, self.chaos, self.cancel,
                       self.push_off, self.drift, self.merge, self.sleep]
        self.i = 0
        self.st = {"t0": t}
        self.p0 = show.last_pose
        show.arrows = [dict(kind="fixed", c=F.A, phi=F.arrow_phi(t), L=L0)]

    def step(self, t):
        show = self.show
        if self.i >= len(self.phases):
            show.finished = True
            return show.last_pose
        st = self.st
        if "init" not in st:
            st["init"] = True
            self.p0 = show.last_pose
        pose = self.phases[self.i](t, st)
        if st.get("done"):
            self.i += 1
            self.st = {"t0": t + DT}
        return pose

    # -- outils
    def mark(self, t, rate=None, shot=None):
        if rate is not None:
            self.show.tempo2.append((t, rate))
        if shot is not None:
            self.show.shots2.append((t,) + shot)

    def feet_dist(self, pose, Fr):
        return Fr.local(pose.pelvis)[1]

    # ======================================================= ACTE 2 : la maîtrise
    def stand_up(self, t, st):
        """Assis au plafond, sonné : il se relève en se frottant la tête, fâché."""
        tau = t - st["t0"]
        if tau < DT / 2:
            self.mark(t, rate=0.62)
        p0 = self.p0
        fc = p0.facing
        u = F.CEIL.local(p0.pelvis)[0] + fc * 34
        cr = standing(F.CEIL, u, fc, crouch=0.6, lean=25, expr="colere")
        J = build(cr)
        cr.hands = [v_add(J["head"], v_mul(J["up"], 30)), None]
        up = standing(F.CEIL, u, fc, expr="colere", gaze=F.arrow_point(t, 100), head=-10)
        up.hands = F.swing_hands(up, [-6, 8])
        self.u = u
        self.facing = fc
        st["done"] = tau >= 1.0
        return F.keyed(tau, [(0, p0), (0.45, cr), (1.0, up)])

    def look(self, t, st):
        """Il regarde la flèche, hors de portée… puis les pierres : « ! »."""
        tau = t - st["t0"]
        show = self.show
        tip = F.arrow_point(t, 110)
        near = min((s for s in show.stones if not s.held), key=lambda s: v_len(v_sub(s.p, F.CEIL.w(self.u, 0))))
        if tau < 0.6:
            p = standing(F.CEIL, self.u, self.facing, expr="curieux", gaze=tip, head=-20, emote=("?", tau))
        else:
            p = standing(F.CEIL, self.u, self.facing, expr="joie", gaze=tuple(near.p), head=12,
                         emote=("!", tau - 0.6) if tau > 0.6 else None)
        p.hands = F.swing_hands(p, [-6, 8])
        if tau >= 1.2:
            st["done"] = True
            self.plan_tower()
        return p

    def plan_tower(self):
        show = self.show
        self.uT = 0.0
        on_ceiling = [s for s in show.stones if s.p[1] < -R + s.r + 12 and not s.held]
        pool = sorted(on_ceiling or show.stones, key=lambda s: abs(F.CEIL.local(s.p)[0] - self.uT))[:5]
        chosen = sorted(pool, key=lambda s: -s.r)[:3]
        self.tower = chosen
        self.tower_h = []
        h = 0.0
        for s in chosen:
            self.tower_h.append(h + s.r)
            h += 2 * s.r
        self.tower_top = h

    def carry(self, k):
        """Va chercher une pierre, la soulève, la pose au sommet de la pile."""
        def ph(t, st):
            show = self.show
            s = self.tower[k]
            if "plan" not in st:
                if k == 0:
                    self.mark(t, rate=1.15, shot=("suivi", None, 1.7, 1.7, 180, 180))
                su = F.CEIL.local(s.p)[0]
                uh = self.u
                d = 1 if su >= uh else -1
                ua = su - d * (s.r + 30)
                w1 = max(0.3, abs(ua - uh) / 320)
                d2 = 1 if self.uT >= ua else -1
                ub = self.uT - d2 * (self.tower[0].r + 40)
                w2 = max(0.3, abs(ub - ua) / 300)
                st["plan"] = dict(su=su, uh=uh, d=d, ua=ua, w1=w1, d2=d2, ub=ub, w2=w2)
            P = st["plan"]
            tau = t - st["t0"]
            gd = (0.0, -1.0)
            T1 = P["w1"]
            T2 = T1 + 0.35                                      # saisie
            T3 = T2 + 0.25                                      # se relève avec la pierre
            T4 = T3 + P["w2"]                                   # marche jusqu'à la pile
            T5 = T4 + 0.45                                      # la pose
            T6 = T5 + 0.2
            target = F.CEIL.w(self.uT, self.tower_h[k])

            def carried(p):
                J = build(replace(p, hands=[None, None]))
                cpos = v_add(J["shoulder"], v_mul(J["fwd"], s.r + 22), v_mul(J["up"], -18))
                p.hands = [v_add(cpos, v_mul(J["up"], s.r * 0.8)), v_add(cpos, v_mul(J["up"], -s.r * 0.6))]
                return cpos
            if tau < T1:
                n = max(1, int(round(abs(P["ua"] - P["uh"]) / 70)))
                p = F.walk(F.CEIL, t, st["t0"], st["t0"] + T1, P["uh"], P["ua"], n, gd, expr="decide", gaze=tuple(s.p))
                return p
            if tau < T3:
                up_p = standing(F.CEIL, P["ua"], P["d"], expr="decide", gaze=tuple(s.p))
                bend = standing(F.CEIL, P["ua"], P["d"], crouch=0.75, lean=40, head=20, expr="decide", gaze=tuple(s.p))
                J = build(bend)
                bend.hands = [v_add(tuple(s.p), v_mul(J["up"], s.r * 0.7)), v_add(tuple(s.p), v_mul(J["fwd"], -s.r * 0.7))]
                if tau < T2:
                    return F.keyed(tau, [(T1, up_p), (T2, bend)])
                lift = standing(F.CEIL, P["ua"], P["d2"], expr="decide", gaze=target)
                u = ease((tau - T2) / 0.25)
                p = lerp_pose(bend, lift, u)
                cpos = carried(lift)
                s.held = True
                show.carry_pos = v_lerp(tuple(s.p) if u < 0.02 else show.carry_pos or tuple(s.p), cpos, u)
                p.hands = lift.hands if u > 0.5 else bend.hands
                return p
            if tau < T4:
                n = max(1, int(round(abs(P["ub"] - P["ua"]) / 70)))
                p = F.walk(F.CEIL, t, st["t0"] + T3, st["t0"] + T4, P["ua"], P["ub"], n, gd, expr="decide", gaze=target)
                show.carry_pos = carried(p)
                return p
            base = standing(F.CEIL, P["ub"], P["d2"], lean=12, expr="decide", gaze=target)
            if tau < T5:
                u = ease((tau - T4) / 0.45)
                J = build(base)
                c0 = carried(standing(F.CEIL, P["ub"], P["d2"]))
                show.carry_pos = v_lerp(c0, target, u)
                base.hands = [v_add(show.carry_pos, v_mul(J["up"], s.r * 0.8)),
                              v_add(show.carry_pos, v_mul(J["up"], -s.r * 0.6))]
                return base
            if s.held:
                s.held = False
                s.fixed = True
                s.p = list(target)
                s.v = [0.0, 0.0]
                show.carry_pos = None
                show.events.append((t, "clack", target, 0.4))
            base.hands = F.swing_hands(base, [-6, 8])
            self.u = P["ub"]
            self.facing = P["d2"]
            st["done"] = tau >= T6
            return base
        return ph

    def hop(self, t, st):
        """Grimpe d'un bond au sommet de la pile."""
        tau = t - st["t0"]
        if tau < DT / 2:
            self.mark(t, rate=0.75, shot=("fixe", (0.0, -190.0), 1.3, 1.35, 180, 180))
        top = self.tower_top
        fc = self.facing
        a = standing(F.CEIL, self.u, fc, expr="decide", gaze=F.CEIL.w(self.uT, top))
        cr = standing(F.CEIL, self.u, fc, crouch=0.6, lean=15, expr="decide", gaze=F.CEIL.w(self.uT, top))
        on = standing(F.CEIL, self.uT, fc, crouch=0.5, lean=10, expr="joie", width=6)
        on.pelvis = v_add(on.pelvis, v_sub(F.CEIL.w(0, top), F.CEIL.w(0, 0)))
        on.feet = [F.CEIL.w(self.uT - 6, top), F.CEIL.w(self.uT + 6, top)]
        if tau < 0.25:
            return F.keyed(tau, [(0, a), (0.25, cr)])
        if tau < 0.75:                                          # le bond (parabole)
            u = (tau - 0.25) / 0.5
            pu = self.u + (self.uT - self.u) * u
            ph = F.K.HIP_H * 0.7 + (top + F.K.HIP_H * 0.75 - F.K.HIP_H * 0.7) * u + 90 * 4 * u * (1 - u)
            p = standing(F.CEIL, pu, fc, expr="decide")
            p.pelvis = F.CEIL.w(pu, ph)
            p.feet = [None, None]
            p.g = (0.0, -1.0)
            return p
        st["done"] = tau >= 1.0
        return on

    def jump_grab(self, t, st):
        """Debout sur la pile : il vise la pointe, s'accroupit, saute… et l'attrape au sommet du saut."""
        tau = t - st["t0"]
        top = self.tower_top
        fc = self.facing
        grip = [F.arrow_point(t, 110), F.arrow_point(t, 88)]
        lift = v_sub(F.CEIL.w(0, top), F.CEIL.w(0, 0))
        look = standing(F.CEIL, self.uT, fc, expr="decide", gaze=grip[0], head=-26, width=6)
        look.pelvis = v_add(look.pelvis, lift)
        look.feet = [v_add(q, lift) for q in look.feet]
        look.hands = F.swing_hands(look, [-4, 6])
        cr = standing(F.CEIL, self.uT, fc, crouch=0.6, lean=8, expr="decide", gaze=grip[0], head=-26, width=6)
        cr.pelvis = v_add(cr.pelvis, lift)
        cr.feet = [v_add(q, lift) for q in cr.feet]
        cr.hands = F.swing_hands(cr, [-40, -30])
        if "v0" not in st:
            grip_h = max(F.CEIL.local(q)[1] for q in grip)
            apex = grip_h - K.SHOULDER - 72
            start = F.CEIL.local(cr.pelvis)[1]
            st["v0"] = math.sqrt(2 * G * max(60.0, apex - start))
            st["h0"] = start
        if tau < 0.35:
            return F.keyed(tau, [(0, look), (0.35, look)])
        if tau < 0.6:
            return F.keyed(tau, [(0.35, look), (0.6, cr)])
        v0 = st["v0"]
        T = tau - 0.6
        t_apex = v0 / G
        h = st["h0"] + v0 * T - 0.5 * G * T * T
        p = standing(F.CEIL, self.uT, fc, expr="decide", gaze=grip[0], head=-26)
        p.pelvis = F.CEIL.w(self.uT, h)
        p.feet = [None, None]
        p.g = (0.0, -1.0)
        J = build(replace(p, hands=[None, None]))
        up_h = [v_add(J["shoulder"], v_add(v_mul(J["up"], 62), v_mul(J["fwd"], -56))),
                v_add(J["shoulder"], v_add(v_mul(J["up"], 64), v_mul(J["fwd"], 58)))]
        k = ease((T - (t_apex - 0.15)) / 0.15)
        p.hands = [v_lerp(up_h[0], grip[1], k), v_lerp(up_h[1], grip[0], k)]
        if T >= t_apex:
            st["done"] = True
            self.show.events.append((t, "clack", grip[0], 0.6))
        return p

    def hang(self, t, st):
        """Suspendu à la pointe : il gigote, tire d'un coup sec… la flèche se décroche."""
        tau = t - st["t0"]
        show = self.show
        if tau < DT / 2:
            self.mark(t, rate=0.7)
        wob = 4 * math.sin(tau * 9) * min(1.0, tau * 2)
        for a in show.arrows:
            a["phi"] = 270 + wob
        grip = [F.arrow_point(t, 110), F.arrow_point(t, 88)]
        grip = [v_add(F.A, v_mul(F.unit(270 + wob), 110)), v_add(F.A, v_mul(F.unit(270 + wob), 88))]
        mid = v_lerp(grip[0], grip[1], 0.5)
        sw = 14 * math.sin(tau * 7)
        th = 180 + sw * 0.4
        pel = v_sub(mid, v_mul(up_vec(th), K.SHOULDER + 66))
        kick = math.sin(tau * 14) * (1 if tau < 0.9 else 0)
        J = build(Pose(pel, th, 0, 0, self.facing, [None, None], [grip[1], grip[0]], g=(0.0, -1.0)))
        feet = [v_add(pel, v_mul(F.unit(th + 90 + 20 * kick), 70)), v_add(pel, v_mul(F.unit(th + 90 - 20 * kick), 66))]
        p = Pose(pel, th, 0, -12, self.facing, feet, [grip[1], grip[0]], expr="decide" if tau < 0.9 else "colere",
                 g=(0.0, -1.0), gaze=mid)
        if tau >= 1.25:
            st["done"] = True
            show.events.append((t, "clang", grip[0], 0.8))
            for s in self.tower:                                # la pile s'écroule (il l'a poussée en sautant)
                s.fixed = False
                s.v = [60.0 * (1 if s.p[0] > 0 else -1), 0.0]
        return p

    def fall_with_arrow(self, t, st):
        """La flèche arrachée, il retombe vers le plafond en la ramenant contre lui."""
        tau = t - st["t0"]
        show = self.show
        if "p" not in st:
            st["p"] = self.p0.pelvis
            st["v"] = (0.0, 0.0)
            st["c0"] = show.arrows[0]["c"]
            st["th"] = self.p0.theta
        phi = 270.0
        g = (0.0, -G)
        st["v"] = v_add(st["v"], v_mul(g, DT))
        st["p"] = v_add(st["p"], v_mul(st["v"], DT))
        th = turn(st["th"], 180.0, ease(tau / 0.4))
        p = Pose(st["p"], th, 0, -6, self.facing, [None, None], [None, None], expr="surpris", g=(0.0, -1.0))
        k = ease(tau / 0.4)
        c_hold = hold(show, p, phi, L0)
        c = v_lerp(st["c0"], c_hold, k)
        d = F.unit(phi)
        p.hands = [v_sub(c, v_mul(d, 16)), v_add(c, v_mul(d, 16))]
        set_held(show, c, phi, L0)
        if F.CEIL.local(st["p"])[1] <= K.HIP_H * 0.75:
            st["done"] = True
            self.landing = (F.CEIL, F.CEIL.local(st["p"])[0])
            show.events.append((t, "thud", F.CEIL.w(self.landing[1], 0), 0.8))
        return p

    def land(self, proud=False, soft=False):
        def ph(t, st):
            tau = t - st["t0"]
            show = self.show
            Fr, u = self.landing
            phi = down_phi(Fr)
            L = show.arrows[0]["L"] if show.arrows else L0
            fc = self.facing
            cr = standing(Fr, u, fc, crouch=0.35 if soft else 0.7, lean=14, expr="surpris" if not proud else "joie")
            up = standing(Fr, u, fc, expr="joie" if not proud else "fier")
            if proud:
                self.mark(t, rate=0.6, shot=("suivi", None, 2.2, 2.3, 0, 0)) if tau < DT / 2 else None
            p = F.keyed(tau, [(0, self.p0 if tau < 0.12 else cr), (0.12, cr), (0.45, up)])
            c = hold(show, p, phi, L)
            set_held(show, c, phi, L)
            if proud and tau > 0.5:                            # une main brandie, l'autre tient la flèche
                J = build(replace(p, hands=[None, None]))
                p.hands = [v_add(J["shoulder"], v_add(v_mul(J["up"], 70), v_mul(J["fwd"], 20))),
                           v_add(J["shoulder"], v_add(v_mul(J["up"], -40), v_mul(J["fwd"], 30)))]
                c = v_add(p.hands[1], v_mul(F.unit(phi), 10))
                set_held(show, c, phi, L)
                hit = [h for h in show.head_hits if h > st["t0"]]
                if hit:
                    p = replace(p, expr="colere" if t - hit[-1] > 0.3 else "surpris",
                                emote=("etoiles", t - hit[0]))
            self.u = u
            st["done"] = tau >= (0.5 if not proud else 2.2)
            return p
        return ph

    def tilt(self, t, st):
        """Il incline la flèche dans ses mains : la gravité penche avec elle. Il a compris."""
        tau = t - st["t0"]
        show = self.show
        if tau < DT / 2:
            self.mark(t, rate=0.62, shot=("suivi", None, 2.0, 2.1, 180, 180))
        phi = 270 - 28 * math.sin(math.pi * min(1.0, tau / 1.6))
        lean = phi - 270
        ex = "curieux" if tau < 0.8 else "joie"
        p = standing(F.CEIL, self.u, self.facing, lean=lean * 0.9, expr=ex, gaze=None, head=14,
                     emote=("!", tau - 0.9) if 0.9 < tau < 1.6 else None)
        c = hold(show, p, phi, L0)
        p.gaze = c
        set_held(show, c, phi, L0)
        st["done"] = tau >= 1.9
        return p

    def flip(self, t, st):
        """Il retourne la flèche vers le sol. La gravité avec."""
        tau = t - st["t0"]
        show = self.show
        if tau < DT / 2:
            self.mark(t, rate=0.85, shot=("fixe", (0.0, 0.0), 1.05, 1.07, 180, 0))
        phi = 270 - 180 * ease(tau / 0.35)
        p = standing(F.CEIL, self.u, self.facing, expr="decide", head=10)
        c = hold(show, p, phi, L0)
        p.gaze = c
        set_held(show, c, phi, L0)
        st["done"] = tau >= 0.35
        return p

    def park_rotate(self, n):
        """Parkour : il pointe la flèche vers une autre surface (petit saut d'appel)."""
        def ph(t, st):
            tau = t - st["t0"]
            show = self.show
            Fr, u = self.landing
            if "to" not in st:
                x = self.show.last_pose.pelvis[0]
                seq = [F.RWALL if x < 0 else LWALL, F.CEIL, F.FLOOR]
                st["to"] = down_phi(seq[n])
                st["from"] = down_phi(Fr)
                if n == 0:
                    self.mark(t, rate=0.85, shot=("fixe", (0.0, 0.0), 1.05, 1.06, 0, 0))
            phi = turn(st["from"], st["to"], ease((tau - 0.15) / 0.2))
            cr = standing(Fr, u, self.facing, crouch=0.5 * math.sin(math.pi * min(1.0, tau / 0.35)), lean=10,
                          expr="joie")
            c = hold(show, cr, phi, L0)
            cr.gaze = v_add(c, v_mul(F.unit(st["to"]), 300))
            set_held(show, c, phi, L0)
            st["done"] = tau >= 0.35
            return cr
        return ph

    def fall(self, hop=0.0):
        """Chute libre dans le sens de la flèche ; en l'air il se tourne pour arriver les pieds devant."""
        def ph(t, st):
            tau = t - st["t0"]
            show = self.show
            held = show.arrows[0]
            phi = held["phi"]
            g = grav(show)
            if "p" not in st:
                p0 = self.p0
                st["p"] = p0.pelvis
                st["th"] = p0.theta
                Fr, _ = self.landing if hasattr(self, "landing") else (F.CEIL, 0)
                n = F.unit(down_phi(Fr) + 180)
                st["v"] = v_mul(n, hop)
                st["to"] = surface_for(g)
            st["v"] = v_add(st["v"], v_mul(g, DT))
            st["p"] = v_add(st["p"], v_mul(st["v"], DT))
            Fr = st["to"]
            th = turn(st["th"], Fr.alpha, ease(tau / 0.55))
            p = Pose(st["p"], th, 0, -8, self.facing, [None, None], [None, None], expr="joie", g=v_mul(g, 1 / G))
            J = build(p)
            p.feet = [v_add(st["p"], v_mul(F.unit(th + 90 - 12), 66)), v_add(st["p"], v_mul(F.unit(th + 90 + 14), 60))]
            c = hold(show, p, phi, held["L"])
            set_held(show, c, phi, held["L"])
            if tau > 0.1 and Fr.local(st["p"])[1] <= K.HIP_H * 0.8:
                st["done"] = True
                self.landing = (Fr, Fr.local(st["p"])[0])
                show.events.append((t, "thud", Fr.w(self.landing[1], 0), 0.7))
            return p
        return ph

    # ======================================================= ACTE 3 : l'escalade
    def stretch_small(self, t, st):
        """La longueur ! Il l'étire un peu : il pèse plus lourd. Vite, il la raccourcit."""
        tau = t - st["t0"]
        show = self.show
        Fr, u = self.landing
        if tau < DT / 2:
            self.mark(t, rate=0.62, shot=("suivi", None, 2.5, 2.6, 0, 0))
        if tau < 0.5:
            L = L0
        elif tau < 1.1:
            L = L0 + 120 * ease((tau - 0.5) / 0.6)
        elif tau < 1.5:
            L = 360
        else:
            L = 360 - 120 * ease((tau - 1.5) / 0.4)
        heavy = max(0.0, L / L0 - 1.0) * 2
        ex = "curieux" if tau < 0.5 else ("peur" if tau < 1.6 else "surpris")
        p = standing(Fr, u, self.facing, crouch=0.55 * heavy, lean=18 * heavy, expr=ex,
                     emote=("?", tau) if tau < 0.5 else (("sueur", tau - 0.8) if 0.8 < tau < 1.6 else None))
        c = hold(show, p, down_phi(Fr), L, spread=16 + (L - L0) * 0.4)
        p.gaze = c
        set_held(show, c, down_phi(Fr), L)
        show.sag = 0.0
        st["done"] = tau >= 2.0
        return p

    def shrink(self, t, st):
        """Il la raccourcit : tout devient léger."""
        tau = t - st["t0"]
        show = self.show
        Fr, u = self.landing
        L = L0 - 150 * ease(tau / 0.8)
        p = standing(Fr, u, self.facing, expr="joie" if tau > 0.8 else "curieux", head=-4)
        p.pelvis = v_add(p.pelvis, v_mul(F.unit(down_phi(Fr) + 180), 4 * math.sin(tau * 5) * (tau > 0.8)))
        c = hold(show, p, down_phi(Fr), L, spread=max(8.0, 16 - (L0 - L) * 0.05))
        p.gaze = c
        set_held(show, c, down_phi(Fr), L)
        st["done"] = tau >= 1.2
        return p

    def moon(self, v0, flip):
        """Saut en gravité faible : très haut, très lent. Il garde la flèche pointée vers le sol en tournant autour."""
        def ph(t, st):
            tau = t - st["t0"]
            show = self.show
            Fr, u = self.landing
            L = show.arrows[0]["L"]
            phi = down_phi(Fr)
            gmag = G * L / L0
            if tau < DT / 2:
                self.mark(t, rate=0.72, shot=("suivi", None, 1.35, 1.4, 0, 0) if flip else None)
            cr = standing(Fr, u, self.facing, crouch=0.6, lean=12, expr="joie")
            if tau < 0.3:
                p = F.keyed(tau, [(0, standing(Fr, u, self.facing, expr="joie")), (0.3, cr)])
                c = hold(show, p, phi, L)
                set_held(show, c, phi, L)
                return p
            T = tau - 0.3
            h = F.K.HIP_H * 0.7 + v0 * T - 0.5 * gmag * T * T
            ua = u + self.facing * 110 * T
            tf = 2 * v0 / gmag
            th = Fr.alpha + (self.facing * 360 * ease((T - 0.15 * tf) / (0.7 * tf)) if flip else 0)
            p = Pose(Fr.w(ua, h), th, 0, -6, self.facing, [None, None], [None, None], expr="joie",
                     g=F.unit(phi))
            J = build(p)
            tuck = math.sin(math.pi * min(1.0, T / tf)) if flip else 0.3
            p.feet = [v_add(p.pelvis, v_mul(F.unit(th + 90 - 30 * tuck), 70 - 30 * tuck)),
                      v_add(p.pelvis, v_mul(F.unit(th + 90 + 20 * tuck), 66 - 26 * tuck))]
            if flip:
                c = v_add(p.pelvis, v_mul(F.unit(phi + 180), 40))
                d = F.unit(phi)
                p.hands = [v_sub(c, v_mul(d, 14)), v_add(c, v_mul(d, 14))]
            else:
                c = hold(show, p, phi, L)
                J = build(replace(p, hands=[None, None]))
                p.hands = [v_add(J["shoulder"], v_add(v_mul(J["up"], 40), v_mul(J["fwd"], -60))), p.hands[1]]
            set_held(show, c, phi, L)
            if T > 0.2 and h <= F.K.HIP_H * 0.72:
                st["done"] = True
                self.landing = (Fr, ua)
                show.events.append((t, "thud", Fr.w(ua, 0), 0.4))
                for s in show.stones:                          # l'atterrissage fait sauter les pierres voisines
                    if v_len(v_sub(s.p, Fr.w(ua, 0))) < 260 and not s.fixed:
                        s.v = v_add(s.v, v_mul(F.unit(phi + 180), 260))
                        s.v = list(s.v)
            return p
        return ph

    def greed(self, t, st):
        """Plus longue, toujours plus longue… il est écrasé, le sol plie, la flèche casse en deux."""
        tau = t - st["t0"]
        show = self.show
        Fr, u = self.landing
        phi = down_phi(Fr)
        if tau < DT / 2:
            self.mark(t, rate=0.6, shot=("suivi", None, 2.3, 1.9, 0, 0))
        T_S = 3.0                                               # la cassure
        if tau < 0.6:
            L = 90 + 150 * ease(tau / 0.6)
        elif tau < T_S:
            L = 240 + 360 * ease((tau - 0.6) / (T_S - 0.6)) ** 0.8
        else:
            L = 600
        r = L / L0
        crush = max(0.0, min(1.0, (r - 1.2) / 1.2))
        ex = "decide" if tau < 0.9 else ("peur" if crush < 0.8 else "colere")
        emote = ("!", tau) if tau < 0.4 else (("sueur", tau) if crush > 0.3 else None)
        up = standing(Fr, u, self.facing, expr=ex, emote=emote)
        knee = Pose(Fr.w(u, 34), Fr.alpha + 58 * self.facing, 20, 20, self.facing,
                    [Fr.w(u - self.facing * 46, 0), Fr.w(u - self.facing * 30, 0)], [None, None], expr=ex,
                    g=F.unit(phi), emote=emote)
        p = lerp_pose(up, knee, ease(crush))
        vib = 3 * math.sin(tau * 80) * crush
        spread = 16 + min(54.0, (L - L0) * 0.3)
        c = hold(show, p, phi + vib, L, spread=spread, dist=34 + 10 * crush)
        p.gaze = c
        show.sag = 26 * ease((r - 1.6) / 0.9) if Fr is F.FLOOR else 0.0
        if tau < T_S:
            set_held(show, c, phi + vib, L)
            if r > 2.2 and int(tau * 12) != int((tau - DT) * 12):
                show.events.append((t, "clack", v_add(c, v_mul(F.unit(phi), 40)), 0.3))
            return p
        # cassure : deux flèches de 300 ; l'une reste dans ses mains, l'autre s'échappe et tournoie
        if "snap" not in st:
            st["snap"] = t
            st["c0"] = c
            show.events.append((t, "boom", c, 1.0))
            self.t_snap = t
            self.mark(t, rate=0.7, shot=("fixe", (0.0, 60.0), 1.15, 1.1, 0, 0))
        T = t - st["snap"]
        rc = v_lerp(st["c0"], CENTER_R, F.ease_out(T / 0.8))
        self.rogue_phi = lambda tt: phi + 620 * F.ease_out((tt - self.t_snap) / 1.1) + 45 * (tt - self.t_snap)
        show.arrows = [dict(kind="held", c=c, phi=phi, L=300.0),
                       dict(kind="rogue", c=rc, phi=self.rogue_phi(t), L=300.0)]
        show.sag = 26 * (1 - ease(T / 0.5))
        p = replace(p, expr="surpris", emote=("!", T))
        st["done"] = T >= 0.6
        return p

    # ======================================================= ACTE 4 : la résolution
    def chaos(self, t, st):
        """Deux gravités qui s'additionnent : la sienne tourne avec son corps, l'autre tourne toute seule."""
        tau = t - st["t0"]
        show = self.show
        if "tb" not in st:
            p0 = self.p0
            st["tb"] = F.Tumble(v_add(p0.pelvis, v_mul(up_vec(p0.theta), 30)), p0.theta)
            self.mark(t, rate=0.85, shot=("fixe", (0.0, 0.0), 1.05, 1.06, 0, 0))
        tb = st["tb"]
        rphi = self.rogue_phi(t)
        hphi = tb.th + 90
        show.arrows = [dict(kind="held", c=tb.c, phi=hphi, L=300.0), dict(kind="rogue", c=CENTER_R, phi=rphi, L=300.0)]
        g = grav(show)
        tb.step(g, DT)
        tb.w = max(-500.0, min(500.0, tb.w))
        if tb.contact and tb.contact[2] > 150:
            show.events.append((t, "thud", tuple(tb.c), min(1.0, tb.contact[2] / 900)))
        pel = v_sub(tuple(tb.c), v_mul(up_vec(tb.th), 30))
        fl = t * 9
        p = Pose(pel, tb.th, 8 * math.sin(fl), 0, self.facing, [None, None], [None, None], g=v_mul(g, 1 / max(1, v_len(g))),
                 expr="peur", emote=("sueur", tau))
        p.feet = [v_add(pel, v_mul(F.unit(tb.th + 90 + 30 * math.sin(fl * 0.8)), 70)),
                  v_add(pel, v_mul(F.unit(tb.th + 90 - 30 * math.cos(fl * 0.9)), 66))]
        c = hold(show, p, hphi, 300.0)
        show.arrows[0]["c"] = c
        if tau < 0.25:
            p = lerp_pose(self.p0, p, ease(tau / 0.25))
        if tau > 3.5 and tb.contact and v_len(tb.v) < 220 or tau > 6.0:
            st["done"] = True
            self.tb = tb
        return p

    def cancel(self, t, st):
        """L'idée : pointer sa flèche à l'opposé de l'autre. Les deux gravités s'annulent."""
        tau = t - st["t0"]
        show = self.show
        tb = self.tb
        if tau < DT / 2:
            self.mark(t, rate=0.6, shot=("suivi", None, 1.9, 2.0, 0, 0))
            st["h0"] = tb.th + 90
            st["th0"] = tb.th
            st["c"] = tuple(tb.c)
            # le mur contre lequel il est plaqué
            x, y = tb.c
            d = [(R - y, F.FLOOR), (y + R, F.CEIL), (R - x, F.RWALL), (x + R, LWALL)]
            st["wall"] = min(d, key=lambda e: e[0])[1]
        rphi = self.rogue_phi(t)
        k = ease((tau - 0.35) / 0.6)
        hphi = turn(st["h0"], rphi + 180, k)
        Fr = st["wall"]
        u = Fr.local(st["c"])[0]
        crouched = standing(Fr, u, self.facing, crouch=0.7, lean=10, g=None, expr="decide", gaze=CENTER_R)
        th = turn(st["th0"], crouched.theta, ease(tau / 0.9))
        p = lerp_pose(Pose(v_sub(st["c"], v_mul(up_vec(st["th0"]), 30)), st["th0"], 0, 0, self.facing,
                           [None, None], [None, None], g=None, expr="peur"), crouched, ease(tau / 0.9))
        p = replace(p, expr="surpris" if tau < 0.35 else "decide", emote=("!", tau) if tau < 0.8 else None,
                    gaze=CENTER_R, g=None)
        c = hold(show, p, hphi, 300.0)
        show.arrows = [dict(kind="held", c=c, phi=hphi, L=300.0), dict(kind="rogue", c=CENTER_R, phi=rphi, L=300.0)]
        self.wall = (Fr, u)
        st["done"] = tau >= 1.3
        return p

    def push_off(self, t, st):
        """En apesanteur, il pousse sur le mur avec les jambes et part vers l'autre flèche."""
        tau = t - st["t0"]
        show = self.show
        Fr, u = self.wall
        rphi = self.rogue_phi(t)
        a = standing(Fr, u, self.facing, crouch=0.7, lean=10, g=None, expr="decide", gaze=CENTER_R)
        b = standing(Fr, u, self.facing, crouch=0.0, lean=0, g=None, expr="decide", gaze=CENTER_R)
        p = F.keyed(tau, [(0, a), (0.15, a), (0.35, b)])
        c = hold(show, p, rphi + 180, 300.0)
        show.arrows = [dict(kind="held", c=c, phi=rphi + 180, L=300.0), dict(kind="rogue", c=CENTER_R, phi=rphi, L=300.0)]
        if tau >= 0.35:
            st["done"] = True
            d = v_sub(CENTER_R, p.pelvis)
            n = v_len(d) or 1.0
            self.drift_v = v_mul(d, 300 / n)
        return p

    def drift(self, t, st):
        """Il flotte en ligne droite (rien ne le freine), en gardant sa flèche à l'opposé de l'autre."""
        tau = t - st["t0"]
        show = self.show
        if "p" not in st:
            st["p"] = self.p0.pelvis
            st["th"] = self.p0.theta
        rphi = self.rogue_phi(t)
        st["p"] = v_add(st["p"], v_mul(self.drift_v, DT))
        d = v_sub(CENTER_R, st["p"])
        face = math.degrees(math.atan2(d[1], d[0]))
        th = turn(st["th"], face + 90 - 60 * self.facing, ease(tau / 0.8))
        p = Pose(st["p"], th, 10, -10, self.facing, [None, None], [None, None], g=None, expr="decide", gaze=CENTER_R)
        c = hold(show, p, rphi + 180, 300.0)
        J = build(replace(p, hands=[None, None]))
        reach = v_add(J["shoulder"], v_mul(v_sub(CENTER_R, J["shoulder"]), 74 / max(74.0, v_len(v_sub(CENTER_R, J["shoulder"])))))
        p.hands = [reach, p.hands[1]]
        show.arrows = [dict(kind="held", c=c, phi=rphi + 180, L=300.0), dict(kind="rogue", c=CENTER_R, phi=rphi, L=300.0)]
        if v_len(v_sub(reach, CENTER_R)) < 12 or tau > 4.0:
            st["done"] = True
            show.events.append((t, "clack", CENTER_R, 0.5))
        return p

    def merge(self, t, st):
        """Il les réunit : deux flèches opposées s'annulent et disparaissent dans un éclair."""
        tau = t - st["t0"]
        show = self.show
        if tau < DT / 2:
            self.mark(t, rate=0.55, shot=("suivi", None, 2.4, 2.6, 0, 0))
            st["p"] = self.p0
            st["rphi"] = self.rogue_phi(t)
            st["hc"] = show.arrows[0]["c"]
        p0 = st["p"]
        rphi = st["rphi"] + 30 * tau
        J = build(replace(p0, hands=[None, None]))
        front = v_add(J["shoulder"], v_mul(J["fwd"], 40), v_mul(J["up"], -8))
        k = ease(tau / 0.9)
        rc = v_lerp(CENTER_R, front, k)
        hc = v_lerp(st["hc"], front, k)
        L = 300.0 * (1 - ease((tau - 1.1) / 0.5))
        p = replace(p0, hands=[rc, hc], expr="decide" if tau < 1.1 else "surpris", gaze=front)
        if L > 1:
            show.arrows = [dict(kind="held", c=hc, phi=rphi + 180, L=L), dict(kind="rogue", c=rc, phi=rphi, L=L)]
        else:
            if show.arrows:
                show.events.append((t, "boom", front, 0.8))
            show.arrows = []
        st["done"] = tau >= 1.9
        return p

    def sleep(self, t, st):
        """Plus rien ne pèse. Il regarde ses mains vides, sourit, bâille… et se rendort en flottant (boucle)."""
        tau = t - st["t0"]
        show = self.show
        D = 7.0
        if "p" not in st:
            st["p"] = self.p0
            st["stones"] = [tuple(s.p) for s in show.stones]
            self.mark(t, rate=0.55)
            self.mark(t + 3.2, shot=("fixe", (0.0, 0.0), 1.05, 1.05, 0, 0))
            for s in show.stones:
                s.fixed = False
        show.arrows = []
        end = F.Pose((F.X_SLEEP, R - 280), -90, 0, -4, 1, [None, None], [None, None], expr="dort", g=None)
        k = ease(tau / D)
        pel = v_lerp(st["p"].pelvis, end.pelvis, k)
        th = turn(st["p"].theta, -90, ease((tau - 2.0) / 3.5))
        if tau < 1.2:
            ex, em = "surpris", None
            J = build(st["p"])
            hands = [v_add(J["shoulder"], v_mul(J["fwd"], 50)), v_add(J["shoulder"], v_add(v_mul(J["fwd"], 44), v_mul(J["up"], 10)))]
        elif tau < 2.2:
            ex, em, hands = "joie", None, [None, None]
        elif tau < 3.4:
            ex, em, hands = "fatigue", None, [None, None]
        else:
            ex, em, hands = "dort", ("zzz", tau - 3.4), [None, None]
        p = Pose(pel, th, 0, -4, 1, [None, None], hands, expr=ex, g=None, emote=em)
        if tau > 5.5:
            p = lerp_pose(p, replace(end, emote=em), ease((tau - 5.5) / 1.5))
        # les pierres dérivent doucement vers leur place du début (la vidéo boucle)
        u = ease((tau - 2.0) / (D - 2.0))
        for s, q0, q1 in zip(show.stones, st["stones"], show.stone_spots):
            s.p = list(v_lerp(q0, q1, u))
            s.v = [0.0, 0.0]
        st["done"] = tau >= D
        return p
