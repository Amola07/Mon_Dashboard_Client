"""Le jeu d'acteur d'Éclat : chaque émotion passe par tout le corps, pas seulement par le visage.

La chorégraphie donne la pose « technique » (où sont les pieds, ce que tiennent les mains) ; cette couche ajoute
la réaction du corps, selon l'émotion affichée :

  • « ! » (surprise)  : le sursaut — le corps se redresse d'un coup, le buste part en arrière, la tête recule,
                        les mains libres s'écartent ; puis il retombe dans sa pose (couché : le buste se soulève) ;
  • « ? » (question) : la tête se penche, une main libre vient se gratter la tête ;
  • « sueur »         : il rentre les épaules, la tête baissée ;
  • « étoiles »       : sonné, la tête et le buste tournent lentement en rond ;
  • « zzz »           : la respiration du sommeil.

Une main qui tient quelque chose ou qui s'appuie n'est jamais déplacée : seules les mains qui pendent jouent.
"""
import math
from dataclasses import replace

from .corps import build, up_vec, right_vec, v_add, v_len, v_lerp, v_mul, v_sub


def _clamp(u):
    return min(max(u, 0.0), 1.0)


def _out(u):
    u = _clamp(u)
    return 1 - (1 - u) ** 3


def pulse(a, rise=0.08, hold=0.22, fall=0.55):
    """0 → 1 très vite (le sursaut), tenu, puis retour en douceur."""
    if a < 0:
        return 0.0
    if a < rise:
        return _out(a / rise)
    if a < hold:
        return 1.0
    u = _clamp((a - hold) / (fall - hold))
    return 1 - u * u * (3 - 2 * u)


def _free(p, J, i):
    """Main qui pend (libre de jouer) ?"""
    h = p.hands[i]
    if h is None:
        return True
    if p.g is None:
        return False
    d = v_sub(h, J["shoulder"])
    n = v_len(d)
    return n > 1 and (d[0] * p.g[0] + d[1] * p.g[1]) / n > 0.75


def _upright(p):
    if p.g is None:
        return True
    u = up_vec(p.theta)
    return -(u[0] * p.g[0] + u[1] * p.g[1]) > 0.6


def _hands(p, J):
    return [p.hands[i] if p.hands[i] is not None else J["arms"][i][2] for i in range(2)]


def startle(p, a):
    k = pulse(a)
    if k <= 0:
        return p
    J = build(p)
    f = p.facing
    if not _upright(p):                                        # couché : le buste se soulève d'un coup
        if p.g is None:
            return replace(p, head=p.head - 12 * k)
        up = (-p.g[0], -p.g[1])

        def lift(th):
            u = up_vec(th)
            return u[0] * up[0] + u[1] * up[1]
        sgn = 1 if lift(p.theta + 1) > lift(p.theta - 1) else -1   # tourne le buste vers la position assise
        return replace(p, theta=p.theta + sgn * 50 * k, head=p.head - 16 * k)
    u, fw = J["up"], J["fwd"]
    hands = _hands(p, J)
    sh = J["shoulder"]
    if p.expr in ("joie", "decide", "fier"):                  # « ! » d'une idée : l'index pointé vers le ciel
        k = pulse(a, 0.10, 0.55, 0.90)                         # une idée se tient plus longtemps qu'un sursaut
        i = 1 if _free(p, J, 1) else (0 if _free(p, J, 0) else None)
        if i is not None:
            d = v_add(v_mul(u, 0.45), fw)                      # levée à côté du visage, sans le traverser
            hands[i] = v_lerp(hands[i], v_add(J["head"], v_mul(d, 54 / v_len(d))), k)
        return replace(p, pelvis=v_add(p.pelvis, v_mul(u, 4 * k)), theta=p.theta - 4 * k * f, head=p.head - 10 * k,
                       hands=hands)
    fly = [v_add(sh, v_add(v_mul(u, 8), v_mul(fw, -70))), v_add(sh, v_add(v_mul(u, 12), v_mul(fw, 70)))]
    for i in range(2):
        if _free(p, J, i):
            hands[i] = v_lerp(hands[i], fly[i], k)
    return replace(p, pelvis=v_add(p.pelvis, v_mul(u, 5 * k)), theta=p.theta - 8 * k * f, bend=p.bend - 10 * k,
                   head=p.head - 14 * k, hands=hands)


def ponder(p, a):
    k = _out(a / 0.25) if a >= 0 else 0.0
    if k <= 0 or not _upright(p):
        return replace(p, head=p.head - 8 * k)
    J = build(p)
    hands = _hands(p, J)
    i = 0 if _free(p, J, 0) else (1 if _free(p, J, 1) else None)   # la main arrière passe derrière la tête
    if i is not None:                                          # se gratte la tête (petit va-et-vient)
        top = v_add(J["head"], v_add(v_mul(J["up"], 24 + 4 * math.sin(a * 40)), v_mul(J["fwd"], -44)))
        hands[i] = v_lerp(hands[i], top, k)
    return replace(p, head=p.head - 10 * k, theta=p.theta - 3 * k * p.facing, hands=hands)


def worry(p, a):
    k = _out(a / 0.3) if a >= 0 else 0.0
    return replace(p, bend=p.bend + 12 * k, head=p.head + 8 * k)


def dazed(p, a):
    w = a * 5.0
    return replace(p, head=p.head + 9 * math.sin(w), theta=p.theta + 3 * math.sin(w + 1.2) * p.facing)


def act(p, t):
    if not p.emote:
        return p
    kind, a = p.emote
    if kind == "!":
        return startle(p, a)
    if kind == "?":
        return ponder(p, a)
    if kind == "sueur":
        return worry(p, a)
    if kind == "etoiles":
        return dazed(p, a)
    if kind == "zzz":
        return replace(p, bend=p.bend + 4 * math.sin(t * 2.2))
    return p


# ------------------------------------------------------------------------------ corps en l'air
def airborne(pel, theta, vel, g, room, facing=1, t=0.0, expr="peur", R=60.0):
    """Pose d'un corps projeté, avec une logique de réflexes (et non des moulinets au hasard) :
    en vol, bras écartés pour l'équilibre, jambes fléchies ; quand le mur approche dans le sens du mouvement,
    les mains se tendent vers lui pour amortir, les jambes se replient. Les transitions dépendent du temps
    avant l'impact : elles sont continues, jamais de saut."""
    from .corps import Pose, free_limb
    sp = v_len(vel)
    ttc = 9.0
    if sp > 1:
        for ax in (0, 1):
            if abs(vel[ax]) > 1e-3:
                wall = room - R if vel[ax] > 0 else -(room - R)
                d = (wall - pel[ax]) / vel[ax]
                if d >= 0:
                    ttc = min(ttc, d)
    brace = _clamp((0.32 - ttc) / 0.2)
    p = Pose(pel, theta, 6, -6, facing, [None, None], [None, None], g=None, expr=expr)
    J = build(p)
    sh = J["shoulder"]
    w = 6 * math.sin(t * 7)                                    # léger battement d'équilibre, pas un moulinet
    spread = [free_limb(sh, theta, facing, -125 + w, 70), free_limb(sh, theta, facing, 130 - w, 70)]
    legs = [free_limb(pel, theta, facing, -22, 76), free_limb(pel, theta, facing, 30, 68)]
    if brace > 0 and sp > 1:
        dv = v_mul(vel, 1 / sp)
        side = right_vec(theta)
        reach = [v_add(sh, v_add(v_mul(dv, 70), v_mul(side, -14))), v_add(sh, v_add(v_mul(dv, 70), v_mul(side, 14)))]
        spread = [v_lerp(spread[i], reach[i], brace) for i in range(2)]
        tuck = [free_limb(pel, theta, facing, 60, 52), free_limb(pel, theta, facing, 75, 50)]
        legs = [v_lerp(legs[i], tuck[i], brace * 0.7) for i in range(2)]
        p.expr = "surpris" if brace > 0.5 else expr
    p.hands, p.feet = spread, legs
    p.gaze = v_add(pel, v_mul(vel, 0.4)) if sp > 1 else None     # il regarde où il va
    return p
