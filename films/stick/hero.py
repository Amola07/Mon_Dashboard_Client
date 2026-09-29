"""« Éclat » : notre héros. Bonhomme bâton cyan lumineux avec une petite cape qui bat au vent.

Le personnage est défini par un squelette (tête, cou, hanches, coudes, mains, genoux, pieds) : chaque pose
est un jeu d'angles, et l'animation interpole entre les poses. La cape suit le cou et flotte selon le vent.
"""
import math

import skia

CYAN = (40, 220, 255)
CAPES = {"rouge": (255, 80, 70), "or": (255, 196, 70), "violet": (170, 90, 255), "blanc": (235, 240, 255)}


def col(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def _pen(c, w, a=255, glow=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if glow:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        p.setBlendMode(skia.BlendMode.kPlus)
    return p


def _brush(c, a=255, glow=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if glow:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        p.setBlendMode(skia.BlendMode.kPlus)
    return p


# poses : angles en degrés (0 = vers le bas, positif = vers l'avant/droite), inclinaison du buste
POSES = {
    "debout":    dict(lean=0, arm_l=(20, 15), arm_r=(-25, -10), leg_l=(12, -5), leg_r=(-12, 5)),
    "salut":     dict(lean=-3, arm_l=(-20, -15), arm_r=(110, 40), leg_l=(12, -5), leg_r=(-12, 5)),
    "course":    dict(lean=14, arm_l=(-60, 70), arm_r=(55, 60), leg_l=(-45, 60), leg_r=(40, -10)),
    "vol":       dict(lean=80, arm_l=(-60, 10), arm_r=(55, 0), leg_l=(-82, 0), leg_r=(-70, -18)),
    "reflexion": dict(lean=-4, arm_l=(-20, -10), arm_r=(25, 135), leg_l=(10, -5), leg_r=(-12, 5)),
    "saut":      dict(lean=4, arm_l=(-120, 20), arm_r=(120, -20), leg_l=(-50, 80), leg_r=(40, 70)),
}


def blend(a, b, u):
    out = {}
    for k in a:
        va, vb = a[k], b[k]
        out[k] = tuple(x + (y - x) * u for x, y in zip(va, vb)) if isinstance(va, tuple) else va + (vb - va) * u
    return out


def draw(c, x, y, s=1.0, pose="debout", t=0.0, cape="rouge", wind=1.0, facing=1, glow=1.0, alpha=255):
    """Dessine Éclat, pieds en (x, y). pose : nom ou dict d'angles. t : temps (cape). facing : 1 droite, -1 gauche."""
    P = POSES[pose] if isinstance(pose, str) else pose
    w = 13 * s
    up = math.radians(P["lean"]) * facing
    hip = (x, y - 92 * s)
    L_body, L_limb = 100 * s, 50 * s

    def seg(origin, ang_deg, length):
        a = math.radians(ang_deg) * facing
        return (origin[0] + math.sin(a) * length, origin[1] + math.cos(a) * length)

    neck = (hip[0] + math.sin(up) * L_body, hip[1] - math.cos(up) * L_body)
    head = (neck[0] + math.sin(up) * 58 * s, neck[1] - math.cos(up) * 58 * s)
    lean = P["lean"]

    def limb(origin, angles, lean_part=0.0):
        a1, a2 = angles
        mid = seg(origin, a1 + lean_part, L_limb)
        end = seg(mid, a1 + a2 + lean_part, L_limb)
        return [origin, mid, end]

    arms = [limb(neck, P["arm_l"], lean), limb(neck, P["arm_r"], lean)]
    legs = [limb(hip, P["leg_l"]), limb(hip, P["leg_r"])]
    # cape : attachée au cou, flotte derrière (sens opposé au regard)
    cc = CAPES.get(cape, cape) if isinstance(cape, str) else cape
    back = -facing
    flap = math.sin(t * 5.0) * 0.5 + math.sin(t * 8.3) * 0.25
    tip1 = (neck[0] + back * (70 + 55 * wind) * s, neck[1] + (95 - 40 * wind + 18 * flap) * s)
    tip2 = (neck[0] + back * (25 + 35 * wind) * s, neck[1] + (125 - 20 * wind - 10 * flap) * s)
    cp = skia.Path()
    cp.moveTo(neck[0] - back * 6 * s, neck[1])
    cp.quadTo(neck[0] + back * 60 * s, neck[1] - (10 + 12 * flap) * s * wind, *tip1)
    cp.quadTo(neck[0] + back * 50 * s, neck[1] + 80 * s, *tip2)
    cp.lineTo(neck[0] + back * 8 * s, neck[1] + 30 * s)
    cp.close()
    c.drawPath(cp, _brush(cc, 110 * glow * alpha / 255, glow=14 * s))
    c.drawPath(cp, _brush(cc, 225 * alpha / 255))
    # corps
    path = skia.Path()
    for pts in arms + legs + [[hip, neck]]:
        path.moveTo(*pts[0])
        for q in pts[1:]:
            path.lineTo(*q)
    path.addCircle(*head, 50 * s)
    c.drawPath(path, _pen(CYAN, w * 2.3, 75 * glow * alpha / 255, glow=w * 0.9))
    c.drawPath(path, _pen(CYAN, w, alpha))
    return {"head": head, "neck": neck, "hip": hip, "hands": (arms[0][-1], arms[1][-1]), "feet": (legs[0][-1], legs[1][-1])}
