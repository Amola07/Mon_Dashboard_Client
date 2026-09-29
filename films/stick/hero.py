"""« Éclat » : notre héros. Bonhomme bâton cyan lumineux, cape (violette) qui bat au vent, visage minimal expressif.

Le corps est un squelette (hanche, cou, tête, bras et jambes en deux segments). Une pose est un dict d'angles
(degrés ; 0 = vers le bas, positif = vers l'avant) ; les poses se mélangent (`blend`) pour des transitions
fluides, la marche et la course sont des cycles continus (`walk`, `run`). Au sol, le corps est recalé pour que
le pied le plus bas touche le sol : s'accroupir abaisse vraiment les hanches.
"""
import math

import skia

CYAN = (40, 220, 255)
CAPES = {"violet": (170, 90, 255), "rouge": (255, 80, 70), "or": (255, 196, 70), "blanc": (235, 240, 255)}

POSES = {
    "debout":    dict(lean=0, head=0, arm_l=(-18, -10), arm_r=(20, 12), leg_l=(-10, 4), leg_r=(10, -4)),
    "salut":     dict(lean=-4, head=-6, arm_l=(-20, -12), arm_r=(115, 40), leg_l=(-10, 4), leg_r=(10, -4)),
    "reflexion": dict(lean=-3, head=8, arm_l=(-15, -30), arm_r=(28, 132), leg_l=(-8, 3), leg_r=(10, -4)),
    "accroupi":  dict(lean=22, head=-10, arm_l=(-45, 35), arm_r=(-35, 30), leg_l=(65, -88), leg_r=(55, -80)),
    "saut":      dict(lean=4, head=-10, arm_l=(-125, 25), arm_r=(125, -25), leg_l=(-35, 55), leg_r=(30, 60)),
    "atterrit":  dict(lean=14, head=8, arm_l=(-80, 35), arm_r=(80, -35), leg_l=(55, -80), leg_r=(45, -72)),
    "vol":       dict(lean=80, head=-12, arm_l=(-55, 10), arm_r=(58, 0), leg_l=(-82, 0), leg_r=(-70, -18)),
    "surpris":   dict(lean=-12, head=-10, arm_l=(-80, -40), arm_r=(80, 40), leg_l=(-14, 6), leg_r=(14, -6)),
    "panique":   dict(lean=8, head=4, arm_l=(-140, 30), arm_r=(140, -30), leg_l=(-20, 30), leg_r=(25, -20)),
    "triomphe":  dict(lean=-6, head=-14, arm_l=(-20, -15), arm_r=(160, 5), leg_l=(-14, 6), leg_r=(14, -6)),
    "assis":     dict(lean=-10, head=-6, arm_l=(-40, -20), arm_r=(-30, -15), leg_l=(92, 0), leg_r=(62, 55)),
    "accroche":  dict(lean=0, head=-4, arm_l=(-105, -45), arm_r=(105, 45), leg_l=(8, 6), leg_r=(-8, -6)),
    "etire":     dict(lean=0, head=0, arm_l=(-150, 0), arm_r=(150, 0), leg_l=(-4, 0), leg_r=(4, 0)),
    "tete":      dict(lean=4, head=12, arm_l=(-40, 120), arm_r=(40, -120), leg_l=(-12, 6), leg_r=(12, -6)),
}
AIRBORNE = {"saut", "vol", "accroche", "etire", "panique"}


def blend(a, b, u):
    out = {}
    for k in a:
        va, vb = a[k], b.get(k, a[k])
        out[k] = tuple(x + (y - x) * u for x, y in zip(va, vb)) if isinstance(va, tuple) else va + (vb - va) * u
    return out


def walk(phase, amp=1.0):
    """Cycle de marche continu (phase en radians)."""
    s, c = math.sin(phase), math.cos(phase)
    return dict(lean=5 * amp, head=2 * math.sin(phase * 2),
                arm_l=(-26 * s * amp, 18 * amp), arm_r=(26 * s * amp, 18 * amp),
                leg_l=(32 * s * amp, -40 * amp * max(0.0, -c)), leg_r=(-32 * s * amp, -40 * amp * max(0.0, c)))


def run(phase, amp=1.0):
    """Cycle de course : grandes enjambées, bras pliés, buste penché."""
    s, c = math.sin(phase), math.cos(phase)
    return dict(lean=16 * amp, head=-4, arm_l=(-60 * s * amp, 75 * amp), arm_r=(60 * s * amp, 75 * amp),
                leg_l=(50 * s * amp, -85 * amp * max(0.0, -c)), leg_r=(-50 * s * amp, -85 * amp * max(0.0, c)))


def as_pose(p):
    return dict(POSES[p]) if isinstance(p, str) else dict(p)


def lift_of(pose, s=1.0, grounded=True):
    """Hauteur de la hanche : pied (ou genou) le plus bas au sol, ou hauteur fixe en l'air."""
    if not grounded:
        return 92 * s
    J = skeleton(pose, s, 1, True, 0.0)
    return max(J["legs"][0][2][1], J["legs"][1][2][1], J["legs"][0][1][1], J["legs"][1][1][1])


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


def skeleton(pose, s=1.0, facing=1, grounded=True, lift=None):
    """Articulations (coordonnées locales, pieds vers y=0, y vers le bas).

    lift : hauteur imposée de la hanche au-dessus de y=0 (sinon : pied le plus bas au sol, ou 92·s en l'air)."""
    P = as_pose(pose)
    L_body, L_limb, L_neck = 100 * s, 50 * s, 58 * s
    up = math.radians(P["lean"]) * facing

    def seg(o, ang, length):
        a = math.radians(ang) * facing
        return (o[0] + math.sin(a) * length, o[1] + math.cos(a) * length)

    hip = (0.0, 0.0)
    neck = (math.sin(up) * L_body, -math.cos(up) * L_body)
    hup = up + math.radians(P.get("head", 0)) * facing
    head = (neck[0] + math.sin(hup) * L_neck, neck[1] - math.cos(hup) * L_neck)

    def limb(o, ang, lean=0.0):
        mid = seg(o, ang[0] + lean, L_limb)
        return [o, mid, seg(mid, ang[0] + ang[1] + lean, L_limb)]

    arms = [limb(neck, P["arm_l"], P["lean"]), limb(neck, P["arm_r"], P["lean"])]
    legs = [limb(hip, P["leg_l"]), limb(hip, P["leg_r"])]
    if lift is None:
        lift = max(legs[0][2][1], legs[1][2][1], legs[0][1][1], legs[1][1][1]) if grounded else 92 * s
    dy = -lift

    def sh(p):
        return (p[0], p[1] + dy)
    return {"hip": sh(hip), "neck": sh(neck), "head": sh(head), "hup": hup,
            "arms": [[sh(q) for q in a] for a in arms], "legs": [[sh(q) for q in leg] for leg in legs]}


def draw_face(c, head, r, hup, facing, expr, look, t, alpha=255):
    """Visage minimal : deux yeux et une bouche, orientés avec la tête."""
    c.save()
    c.translate(*head)
    c.rotate(math.degrees(hup))
    k = r / 50
    fx = facing * 10 * k + look[0] * 9 * k
    fy = look[1] * 7 * k
    blink = (t % 3.7) < 0.12 and expr in ("neutre", "decide", "curieux")
    for side in (-1, 1):
        ex, ey = fx + side * 15 * k, -6 * k + fy
        if expr in ("joie", "fier") or blink or (expr == "clin" and side == 1):
            p = skia.Path()
            if blink:
                p.moveTo(ex - 6 * k, ey)
                p.lineTo(ex + 6 * k, ey)
            else:
                p.moveTo(ex - 7 * k, ey + 3 * k)
                p.quadTo(ex, ey - 7 * k, ex + 7 * k, ey + 3 * k)
            c.drawPath(p, _pen(CYAN, 4.5 * k, alpha))
        elif expr == "surpris":
            c.drawCircle(ex, ey, 9 * k, _pen(CYAN, 3.5 * k, alpha))
            c.drawCircle(ex, ey, 3.5 * k, _brush(CYAN, alpha))
        elif expr == "peur":
            c.drawCircle(ex, ey, 8 * k, _pen(CYAN, 3 * k, alpha))
            c.drawCircle(ex + look[0] * 3 * k, ey, 2 * k, _brush(CYAN, alpha))
        elif expr == "etourdi":
            p = skia.Path()
            for i in range(24):
                a = i * 0.55 + t * 8 * side
                rr = 1 + i * 0.38 * k
                q = (ex + math.cos(a) * rr, ey + math.sin(a) * rr)
                p.moveTo(*q) if i == 0 else p.lineTo(*q)
            c.drawPath(p, _pen(CYAN, 2.5 * k, alpha))
        elif expr == "fatigue":
            p = skia.Path()
            p.moveTo(ex - 7 * k, ey)
            p.lineTo(ex + 7 * k, ey + 1 * k)
            c.drawPath(p, _pen(CYAN, 4 * k, alpha))
            c.drawCircle(ex, ey + 3 * k, 3 * k, _brush(CYAN, alpha))
        else:
            c.drawOval(skia.Rect.MakeXYWH(ex - 4.5 * k, ey - 7.5 * k, 9 * k, 15 * k), _brush(CYAN, alpha))
        if expr in ("decide", "colere"):                        # sourcils froncés vers le nez
            c.drawLine(ex - 8 * k * side, ey - 18 * k, ex + 6 * k * side, ey - 13 * k, _pen(CYAN, 3.5 * k, alpha))
        if expr in ("surpris", "peur", "curieux"):              # sourcils levés
            c.drawLine(ex - 7 * k, ey - 18 * k, ex + 7 * k, ey - 20 * k, _pen(CYAN, 3 * k, alpha))
    mx, my = fx, 16 * k + fy
    m = skia.Path()
    if expr in ("joie", "fier", "clin"):
        m.moveTo(mx - 10 * k, my - 2 * k)
        m.quadTo(mx, my + 10 * k, mx + 10 * k, my - 2 * k)
    elif expr == "surpris":
        m.addCircle(mx, my + 2 * k, 5 * k)
    elif expr == "peur":
        m.moveTo(mx - 10 * k, my + 2 * k)
        for i in range(1, 5):
            m.lineTo(mx - 10 * k + i * 5 * k, my + (2 if i % 2 == 0 else -2) * k)
    elif expr in ("decide", "colere", "fatigue"):
        m.moveTo(mx - 7 * k, my)
        m.lineTo(mx + 7 * k, my)
    elif expr == "triste":
        m.moveTo(mx - 8 * k, my + 3 * k)
        m.quadTo(mx, my - 5 * k, mx + 8 * k, my + 3 * k)
    elif expr == "etourdi":
        m.moveTo(mx - 8 * k, my)
        m.quadTo(mx - 3 * k, my + 5 * k, mx, my)
        m.quadTo(mx + 3 * k, my - 5 * k, mx + 8 * k, my)
    if not m.isEmpty():
        c.drawPath(m, _pen(CYAN, 3.5 * k, alpha))
    c.restore()


def draw_emote(c, head, r, kind, t, age, alpha=255):
    """Symboles au-dessus de la tête : « ? », « ! », goutte de sueur, étoiles qui tournent, éclats de joie."""
    k = r / 50
    pop = min(1.0, age / 0.15) * (1 + 0.25 * math.exp(-age * 8) * math.sin(age * 40))
    x, y = head[0] + 55 * k, head[1] - 70 * k
    white = (240, 245, 255)
    if kind in ("?", "!"):
        f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), max(1.0, 64 * k * pop))
        c.drawString(kind, x - 12 * k, y + 10 * k, f, _brush(white, alpha))
    elif kind == "sueur":
        yy = y + 30 * k + (age % 1.0) * 30 * k
        p = skia.Path()
        p.moveTo(x - 10 * k, yy - 14 * k)
        p.quadTo(x - 18 * k, yy, x - 10 * k, yy + 6 * k)
        p.quadTo(x - 2 * k, yy, x - 10 * k, yy - 14 * k)
        c.drawPath(p, _brush((150, 220, 255), alpha))
    elif kind == "etoiles":
        for i in range(3):
            a = t * 5 + i * 2.09
            sx, sy = head[0] + math.cos(a) * 60 * k, head[1] - 55 * k + math.sin(a) * 16 * k
            star = skia.Path()
            for j in range(10):
                rr = (11 if j % 2 == 0 else 4.5) * k
                aa = -math.pi / 2 + j * math.pi / 5
                q = (sx + rr * math.cos(aa), sy + rr * math.sin(aa))
                star.moveTo(*q) if j == 0 else star.lineTo(*q)
            star.close()
            c.drawPath(star, _brush((255, 210, 90), alpha))
    elif kind == "eclats":
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.5
            r0, r1 = 62 * k, (62 + 26 * pop) * k
            c.drawLine(head[0] + math.cos(a) * r0, head[1] + math.sin(a) * r0,
                       head[0] + math.cos(a) * r1, head[1] + math.sin(a) * r1, _pen(white, 4 * k, alpha))


def draw(c, x, y, s=1.0, pose="debout", t=0.0, cape="violet", wind=1.0, facing=1, glow=1.0, alpha=255,
         expr="neutre", look=(0.0, 0.0), squash=(1.0, 1.0), emote=None, grounded=None, lift=None):
    """Dessine Éclat, pieds en (x, y) ; pose : nom ou dict ; squash : (largeur, hauteur) autour des pieds."""
    name = pose if isinstance(pose, str) else None
    if grounded is None:
        grounded = name not in AIRBORNE if name else True
    J = skeleton(pose, s, facing, grounded, lift)
    w = 13 * s
    c.save()
    c.translate(x, y)
    c.scale(squash[0], squash[1])
    neck, head, hip = J["neck"], J["head"], J["hip"]
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
    path = skia.Path()
    for pts in J["arms"] + J["legs"] + [[hip, neck]]:
        path.moveTo(*pts[0])
        for q in pts[1:]:
            path.lineTo(*q)
    r = 50 * s
    path.addCircle(*head, r)
    c.drawPath(path, _pen(CYAN, w * 2.3, 75 * glow * alpha / 255, glow=w * 0.9))
    c.drawPath(path, _pen(CYAN, w, alpha))
    c.drawCircle(*head, r - w / 2, _brush((0, 0, 0), alpha))
    draw_face(c, head, r, J["hup"], facing, expr, look, t, alpha)
    if emote:
        draw_emote(c, head, r, emote[0], t, emote[1], alpha)
    c.restore()
    return J
