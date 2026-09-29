"""Bibliothèque de mouvements d'Éclat.

Chaque mouvement est écrit comme un animateur l'écrit : une suite de POSES CLÉS, placées à une image précise
(24 images/s), et une façon d'aller de l'une à l'autre. Les règles viennent de l'étude image par image de
l'animation de référence (on n'en recopie aucune séquence, on en tire le métier) :

  • le mouvement se fait en rafale continue, puis la pose est TENUE, parfaitement immobile (4 à 15 images) ;
  • un geste voulu est rapide (4 à 6 images) et arrive avec un léger dépassement, puis se pose ;
  • avant chaque action, une ANTICIPATION dans le sens opposé (on recule le bras avant de pointer, on
    s'accroupit avant de sauter) ; après, une ACCOMPAGNEMENT (le bras qui lance continue sa course) ;
  • des poses franches et asymétriques : genoux fléchis, poids sur une jambe, dos rond, tête en avant ;
  • les mains décrivent des arcs autour de l'épaule (jamais une ligne droite) ; un pied qui change de place se
    soulève ; un pied posé ne glisse pas.

Une pose se décrit sur une surface (sol, mur, plafond), relativement à un point d'ancrage u et au sens du
regard : bassin (du, h), inclinaison du buste, courbure du dos, tête, pieds (du, h), mains.
Une main vaut :
  None            → elle pend (bras détendu, écarté du buste) ;
  ("e", av, haut) → position par rapport à l'épaule (av = vers l'avant, haut = vers le haut de la surface) ;
  ("s", du, h)    → point fixe de la surface (un objet, le sol, un mur).
"""
import math
from dataclasses import dataclass, field, replace

from .corps import HIP_H, Pose, build, v_add, v_len, v_mul, v_sub

FPS = 24


@dataclass
class P:
    pel: tuple = (-3.0, HIP_H - 1)                              # jambes presque tendues, comme en vrai
    lean: float = 2.0                                           # légèrement voûté, tête en avant (référence)
    bend: float = 16.0
    head: float = 9.0
    feet: tuple = ((-9.0, 0.0), (20.0, 0.0))
    hands: tuple = (None, None)
    expr: str = "neutre"
    emote: str = None


REPOS = P()


def _ease(kind, u):
    u = min(max(u, 0.0), 1.0)
    if kind == "lin":
        return u
    if kind == "in":
        return u * u
    if kind == "out":
        return 1 - (1 - u) ** 3
    if kind == "snap":                                          # part vite, dépasse un peu, se pose
        x, s = u - 1, 1.4
        return 1 + (s + 1) * x ** 3 + s * x ** 2
    return u * u * (3 - 2 * u)                                  # "io" : lent — vite — lent


@dataclass
class Clip:
    nom: str
    keys: list                                                  # [(image, P, transition vers cette clé)]
    titre: str = ""
    duree: int = field(default=0)

    def __post_init__(self):
        self.duree = self.duree or self.keys[-1][0]


def _lerp(a, b, u):
    return a + (b - a) * u


def _lerp2(a, b, u):
    return (_lerp(a[0], b[0], u), _lerp(a[1], b[1], u))


def _hand_rel(spec, i, F, u0, facing, shoulder):
    """Main → vecteur (avant, haut) depuis l'épaule, dans le repère de la surface."""
    if spec is None:
        return (-18.0, -80.0) if i == 0 else (22.0, -79.0)         # bras détendu : presque tendu
    kind, a, b = spec
    if kind == "e":
        return (a, b)
    q = F.w(u0 + facing * a, b)                                 # point de la surface → relatif à l'épaule
    lu, lh = F.local(q)
    su, sh = F.local(shoulder)
    return ((lu - su) * facing, lh - sh)


def _body(F, u0, facing, pel, lean, bend, head, feet, expr, g):
    return Pose(F.w(u0 + facing * pel[0], pel[1]), F.alpha + lean * facing, bend, head, facing,
                [F.w(u0 + facing * f[0], f[1]) for f in feet], [None, None], expr=expr, g=g)


def pose_at(clip, frame, F, u0=0.0, facing=1, g=(0.0, 1.0)):
    """Pose d'Éclat à l'image `frame` (peut être fractionnaire) du mouvement."""
    keys = clip.keys
    if frame <= keys[0][0]:
        k, u = 0, 0.0
    elif frame >= keys[-1][0]:
        k, u = len(keys) - 2, 1.0
    else:
        k = max(i for i in range(len(keys) - 1) if keys[i][0] <= frame)
        u = (frame - keys[k][0]) / max(1e-6, keys[k + 1][0] - keys[k][0])
    (f0, a, _), (f1, b, ease) = keys[k], keys[k + 1]
    e = _ease(ease, u)
    pel = _lerp2(a.pel, b.pel, e)
    feet = []
    for i in range(2):
        fa, fb = a.feet[i], b.feet[i]
        q = _lerp2(fa, fb, min(1.0, max(0.0, e)))
        step = abs(fb[0] - fa[0])
        if step > 6 and fa[1] < 3 and fb[1] < 3:               # un pied qui change de place se soulève
            q = (q[0], q[1] + min(26.0, 0.35 * step) * math.sin(math.pi * min(1.0, max(0.0, e))))
        feet.append(q)
    p = _body(F, u0, facing, pel, _lerp(a.lean, b.lean, e), _lerp(a.bend, b.bend, e), _lerp(a.head, b.head, e),
              feet, (b if e >= 0.5 else a).expr, g)
    sh = build(p)["shoulder"]
    fw = v_sub(F.w(1, 0), F.w(0, 0))
    fw = v_mul(fw, facing)
    up = v_sub(F.w(0, 1), F.w(0, 0))
    hands = []
    for i in range(2):
        ra = _hand_rel(a.hands[i], i, F, u0, facing, sh)
        rb = _hand_rel(b.hands[i], i, F, u0, facing, sh)
        # arc autour de l'épaule : on interpole l'angle et la distance, pas la position
        aa, ab = math.atan2(ra[1], ra[0]), math.atan2(rb[1], rb[0])
        d = (ab - aa + math.pi) % (2 * math.pi) - math.pi
        ang = aa + d * e
        r = _lerp(math.hypot(*ra), math.hypot(*rb), e)
        hands.append(v_add(sh, v_add(v_mul(fw, r * math.cos(ang)), v_mul(up, r * math.sin(ang)))))
    p.hands = hands
    em = b.emote if e >= 0.5 else a.emote
    p.emote = (em, (frame - f0) / FPS) if em else None
    return p


def K(*keys):
    return list(keys)


# ------------------------------------------------------------------------------------------ poses de base
POIDS_AVANT = replace(REPOS, pel=(6.0, HIP_H - 7), lean=2.0, feet=((-9.0, 0.0), (20.0, 0.0)))
ACCROUPI = P(pel=(-8.0, 50.0), lean=34.0, bend=22.0, head=-6.0, feet=((-16.0, 0.0), (22.0, 0.0)),
             hands=(("e", 18.0, -44.0), ("e", 34.0, -40.0)))


def _repos(expr="neutre"):
    return replace(REPOS, expr=expr)


# ------------------------------------------------------------------------------------------ la bibliothèque
CLIPS = []


def clip(nom, titre, keys, duree=0):
    c = Clip(nom, keys, titre, duree)
    CLIPS.append(c)
    return c


clip("repos", "Repos : le poids passe d'une jambe à l'autre", K(
    (0, REPOS, "io"),
    (30, REPOS, "io"),
    (42, POIDS_AVANT, "io"),
    (78, POIDS_AVANT, "io"),
    (90, REPOS, "io"),
    (100, REPOS, "io")))

clip("reflechir", "Réfléchir : main au menton", K(
    (0, _repos(), "io"),
    (5, replace(REPOS, head=12, pel=(-3, HIP_H - 8)), "io"),                      # anticipation : il baisse la tête
    (11, replace(REPOS, lean=-8, head=-8, bend=6, expr="curieux",
                 hands=(("e", 16, -28), ("e", 30, 16))), "snap"),
    (40, replace(REPOS, lean=-8, head=-8, bend=6, expr="curieux",
                 hands=(("e", 16, -28), ("e", 30, 16))), "io"),
    (43, replace(REPOS, lean=-9, head=-12, bend=6, expr="curieux",                 # petite relance : il penche
                 hands=(("e", 16, -28), ("e", 30, 18))), "io"),                   # la tête
    (60, replace(REPOS, lean=-9, head=-12, bend=6, expr="curieux",
                 hands=(("e", 16, -28), ("e", 30, 18))), "io"),
    (70, _repos(), "io"),
    (76, _repos(), "io")))

_point_prep = replace(REPOS, lean=-8, head=4, pel=(-6, HIP_H - 7), hands=(None, ("e", -26, -26)), expr="decide")
_point = replace(REPOS, lean=8, bend=8, head=-2, pel=(4, HIP_H - 6), feet=((-12, 0), (26, 0)),
                 hands=(("e", -24, -66), ("e", 85, 4)), expr="decide")
clip("pointer", "Montrer du doigt", K(
    (0, _repos(), "io"),
    (6, _point_prep, "io"),                                    # anticipation : le bras recule
    (10, _point, "snap"),                                      # 4 images : le geste part et se pose
    (34, _point, "io"),                                        # tenue
    (44, _repos(), "io"),
    (50, _repos(), "io")))

_crouch_grab = replace(ACCROUPI, pel=(-4, 48), lean=44, head=-14, hands=(("e", 10, -40), ("s", 44, 3)),
                       expr="curieux")
_up_hold = replace(REPOS, hands=(None, ("e", 26, -20)), expr="joie")
clip("ramasser", "Ramasser un objet", K(
    (0, _repos(), "io"),
    (4, replace(REPOS, head=18, expr="curieux"), "io"),       # il regarde l'objet
    (13, _crouch_grab, "io"),                                  # descend en pliant les genoux, pas le dos seul
    (19, _crouch_grab, "io"),                                  # tenue : il saisit
    (23, replace(_crouch_grab, pel=(-4, 56), hands=(("e", 10, -40), ("s", 40, 16))), "io"),
    (32, _up_hold, "out"),                                     # se relève d'un élan
    (48, _up_hold, "io")))

_kneel = P(pel=(-2.0, 50.0), lean=22.0, bend=18.0, head=-4.0, feet=((-50.0, 2.0), (34.0, 0.0)),
           hands=(("e", 6, -46), ("e", 38, -42)), expr="decide")
clip("genou", "Poser un genou à terre", K(
    (0, _repos(), "io"),
    (6, replace(REPOS, feet=((-20, 0), (26, 0)), pel=(0, HIP_H - 10), lean=6), "io"),
    (14, _kneel, "io"),
    (46, _kneel, "io"),
    (50, replace(_kneel, head=-14, lean=16), "io"),            # relève la tête avant de se relever
    (62, _repos(), "out"),
    (70, _repos(), "io")))

_squat = replace(ACCROUPI, pel=(-8, 50), lean=30, head=-10, hands=(("e", -48, -40), ("e", -36, -46)),
                 expr="decide")
_push = P(pel=(2, HIP_H - 2), lean=-4, bend=0, head=-12, feet=((-8, 6), (14, 8)),
          hands=(("e", -10, 72), ("e", 18, 72)), expr="decide")
_tuck = P(pel=(0, 150), lean=6, bend=14, head=-6, feet=((-14, 96), (16, 104)),
          hands=(("e", -50, 34), ("e", 54, 40)), expr="joie")
_reach_down = P(pel=(0, 104), lean=4, bend=10, head=4, feet=((-12, 18), (16, 22)),
                hands=(("e", -56, 10), ("e", 56, 14)), expr="joie")
_land = replace(ACCROUPI, pel=(-6, 50), lean=30, head=4, hands=(("e", -30, -40), ("e", 40, -42)), expr="joie")
clip("sauter", "Sauter : anticipation, élan, vol, réception", K(
    (0, _repos(), "io"),
    (7, _squat, "io"),                                         # anticipation : il se ramasse, bras en arrière
    (10, _squat, "io"),                                        # tenue courte (la charge)
    (13, _push, "out"),                                        # détente : tout le corps s'étire vers le haut
    (18, _tuck, "out"),                                        # sommet : genoux repliés
    (21, _tuck, "io"),
    (25, _reach_down, "in"),                                   # redescend : les jambes cherchent le sol
    (27, _land, "out"),                                        # réception écrasée
    (33, _land, "io"),
    (44, _repos(), "io"),
    (50, _repos(), "io")))

_take = P(pel=(-6, HIP_H + 2), lean=-16, bend=-6, head=-16, feet=((-9, 0), (20, 0)),
          hands=(("e", -58, 18), ("e", 60, 30)), expr="surpris", emote="!")
clip("sursaut", "Sursauter", K(
    (0, _repos(), "io"),
    (3, replace(REPOS, pel=(-2, HIP_H - 10), head=12, bend=20), "in"),   # micro-anticipation : il se tasse
    (6, _take, "snap"),                                        # le sursaut : 3 images
    (18, _take, "io"),
    (26, replace(_take, lean=-6, head=-6, pel=(-4, HIP_H - 5),
                 hands=(("e", -34, -30), ("e", 38, -24)), emote="!"), "io"),
    (40, _repos("surpris"), "io"),
    (46, _repos("surpris"), "io")))

_idea = replace(REPOS, pel=(-2, HIP_H - 2), lean=-4, bend=4, head=-12, hands=(None, ("e", 58, 44)),
                expr="joie", emote="!")
clip("idee", "Avoir une idée", K(
    (0, _repos("curieux"), "io"),
    (5, replace(REPOS, pel=(-3, HIP_H - 9), head=14, expr="curieux"), "io"),
    (9, _idea, "snap"),
    (34, _idea, "io"),
    (44, _repos("joie"), "io"),
    (50, _repos("joie"), "io")))


def _scratch(dx):
    return replace(REPOS, lean=-4, head=-10, bend=10, hands=(("e", -28 + dx, 58), None), expr="curieux",
                   emote="?")


clip("gratter", "Se gratter la tête", K(
    (0, _repos(), "io"),
    (8, _scratch(0), "io"),
    (11, _scratch(6), "io"),
    (14, _scratch(0), "io"),
    (17, _scratch(6), "io"),
    (20, _scratch(0), "io"),
    (23, _scratch(6), "io"),
    (40, _scratch(3), "io"),
    (50, _repos(), "io"),
    (56, _repos(), "io")))

_shrug = replace(REPOS, pel=(-3, HIP_H - 3), lean=-4, bend=-2, head=-8,
                 hands=(("e", -46, -10), ("e", 48, -8)), expr="neutre")
clip("hausser", "Hausser les épaules", K(
    (0, _repos(), "io"),
    (4, replace(REPOS, pel=(-3, HIP_H - 8)), "io"),
    (9, _shrug, "snap"),
    (26, _shrug, "io"),
    (36, _repos(), "io"),
    (42, _repos(), "io")))

_wall = 74
_push_wall = P(pel=(4, HIP_H - 12), lean=36, bend=10, head=-12, feet=((-62, 0), (8, 0)),
               hands=(("s", _wall, 150), ("s", _wall, 128)), expr="colere")
clip("pousser", "Pousser (effort)", K(
    (0, _repos("decide"), "io"),
    (10, _push_wall, "io"),
    (22, replace(_push_wall, pel=(9, HIP_H - 13)), "io"),      # effort : il pousse par à-coups
    (28, _push_wall, "io"),
    (40, replace(_push_wall, pel=(10, HIP_H - 13), lean=38), "io"),
    (46, _push_wall, "io"),
    (58, _repos("decide"), "io"),
    (62, _repos("decide"), "io")))

_wind = P(pel=(-12, HIP_H - 9), lean=-16, bend=4, head=-6, feet=((-34, 0), (30, 0)),
          hands=(("e", 44, 12), ("e", -62, 36)), expr="decide")
_release = P(pel=(10, HIP_H - 8), lean=18, bend=14, head=-8, feet=((-34, 0), (30, 0)),
             hands=(("e", -40, -24), ("e", 70, 36)), expr="decide")
_follow = P(pel=(16, HIP_H - 12), lean=30, bend=20, head=-2, feet=((-24, 6), (30, 0)),
            hands=(("e", -46, -10), ("e", 26, -62)), expr="joie")
clip("lancer", "Lancer", K(
    (0, _repos("decide"), "io"),
    (9, _wind, "io"),                                          # armé : tout le corps recule
    (13, _wind, "io"),                                         # tenue : on sent la charge
    (16, _release, "out"),                                     # le bras part : 3 images
    (21, _follow, "out"),                                      # accompagnement : le bras continue sa course
    (34, _follow, "io"),
    (46, _repos("joie"), "io"),
    (50, _repos("joie"), "io")))

_trip = P(pel=(-10, HIP_H - 4), lean=-26, bend=-8, head=-18, feet=((-9, 0), (34, 18)),
          hands=(("e", -40, 50), ("e", 50, 56)), expr="surpris", emote="!")
_fall = P(pel=(-30, 40), lean=-50, bend=-6, head=-10, feet=((6, 0), (34, 26)),
          hands=(("e", -60, 0), ("e", 30, 60)), expr="peur")
_sit = P(pel=(-34, 14), lean=-24, bend=10, head=-2, feet=((24, 0), (38, 10)),
         hands=(("s", -74, 0), ("s", -60, 0)), expr="etourdi", emote="etoiles")
clip("tomber", "Tomber sur les fesses", K(
    (0, _repos(), "io"),
    (4, _trip, "out"),                                         # déséquilibre : il bascule en arrière
    (9, _fall, "in"),                                          # la chute accélère (pas de freinage)
    (11, _sit, "lin"),                                         # choc
    (13, replace(_sit, pel=(-34, 11), lean=-28), "out"),       # écrasement
    (17, _sit, "io"),
    (40, _sit, "io"),
    (48, replace(_sit, lean=-10, hands=(("s", -60, 0), ("s", -46, 0)), expr="colere"), "io"),
    (58, replace(ACCROUPI, pel=(-10, 52), lean=36, head=0, hands=(("e", 22, -42), ("e", 36, -40)),
                 expr="colere"), "io"),
    (68, _repos("colere"), "out"),
    (76, _repos("colere"), "io")))


# ------------------------------------------------------------------------------------------ cycles
def cycle(kind, frame, F, u0=0.0, facing=1, g=(0.0, 1.0), expr="neutre"):
    """Marche et course, décomposées comme au dessin animé : contact, descente (le plus bas), passage,
    montée (le plus haut), contact. Le pied d'appui ne glisse jamais ; le bassin monte et descend ;
    les bras balancent à l'opposé des jambes ; le buste penche dans le sens de la marche."""
    if kind == "marche":
        n, stride, h_keys, lean, lift, arm = 12, 64.0, (80.0, 74.0, 82.0, 86.0), 6.0, 20.0, 34.0
    else:
        n, stride, h_keys, lean, lift, arm = 7, 112.0, (72.0, 64.0, 82.0, 92.0), 26.0, 48.0, 60.0
    step = int(frame // n)
    ph = (frame % n) / n                                       # 0 contact · .25 descente · .5 passage · .75 montée
    base = u0 + step * stride
    pu = base + stride * ph
    hk = h_keys + (h_keys[0],)
    x = ph * 4
    i = min(int(x), 3)
    h = _lerp(hk[i], hk[i + 1], _ease("io", x - i))
    front = step % 2                                           # le pied qui vient d'arriver devant
    plant = [0.0, 0.0]
    plant[front] = base + stride / 2
    plant[1 - front] = base - stride / 2                       # le pied arrière va passer devant
    feet = [None, None]
    feet[front] = (plant[front], 0.0)
    sw = 1 - front
    e = _ease("io", ph)
    su = plant[sw] + stride * 2 * e * (1.0 if kind == "marche" else 1.0)
    feet[sw] = (su, lift * math.sin(math.pi * ph) ** 0.8)
    if kind == "course" and 0.45 < ph:                          # phase de vol : les deux pieds quittent le sol
        k = (ph - 0.45) / 0.55
        feet[front] = (plant[front] - 10 * k, 30 * math.sin(math.pi * k))
    p = Pose(F.w(pu, h), F.alpha + facing * (lean + 3 * math.sin(2 * math.pi * ph)), 10 + lean * 0.3, -4,
             facing, [F.w(u, v) for u, v in feet], [None, None], expr=expr, g=g)
    if facing < 0:
        p.pelvis = F.w(2 * u0 - pu, h)
        p.feet = [F.w(2 * u0 - u, v) for u, v in feet]
    sh = build(p)["shoulder"]
    fw = v_mul(v_sub(F.w(1, 0), F.w(0, 0)), facing)
    up = v_sub(F.w(0, 1), F.w(0, 0))
    s = math.cos(math.pi * (ph + front))                       # balancier opposé aux jambes
    hands = []
    for j in range(2):
        a = s * (1 if j == front else -1)
        if kind == "marche":
            ang = math.radians(-90 + a * arm)
            r = 80
        else:                                                  # course : coudes pliés, bras qui pompent
            ang = math.radians(-60 + a * arm)
            r = 52
        hands.append(v_add(sh, v_add(v_mul(fw, r * math.cos(ang)), v_mul(up, r * math.sin(ang)))))
    p.hands = hands
    return p, (pu if facing > 0 else 2 * u0 - pu)
