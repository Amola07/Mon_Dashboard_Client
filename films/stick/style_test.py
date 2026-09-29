"""Test de style « bonhomme bâton sur fond noir » avec un personnage original.

Style (repris des codes du genre) : fond noir, monde en fins traits blancs avec des points aux sommets,
éclats lumineux, un personnage d'une seule couleur vive en traits épais.
Personnage (le nôtre) : cyan, une écharpe qui flotte, une petite antenne-étoile sur la tête.

    python -m films.stick.style_test <dossier>
"""
import math
import sys
from pathlib import Path

import numpy as np
import skia

W, H = 1080, 1920
HERO = (40, 215, 255)
SCARF = (255, 90, 150)
LINE = (238, 240, 246)
GOLD = (255, 200, 90)


def col(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def pen(c, width, a=255, glow=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=width)
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


def stroke(c, pts, rgb, w, glow=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if glow:
        c.drawPath(p, pen(rgb, w * 2.2, 70, glow=w * 0.9))
    c.drawPath(p, pen(rgb, w))


def dot(c, x, y, r=8):
    c.drawCircle(x, y, r, brush((0, 0, 0)))
    c.drawCircle(x, y, r, pen(LINE, 3))


def dust(c, seed=1, n=70):
    r = np.random.default_rng(seed)
    for x, y, s in zip(r.uniform(0, W, n), r.uniform(0, H, n), r.uniform(1, 4, n)):
        c.drawCircle(x, y, s * 3, brush(LINE, 20, glow=s * 2))
        c.drawCircle(x, y, s * 0.8, brush(LINE, 150))


def hero(c, x, y, s, pose="debout", t=0.0):
    """Notre bonhomme : cyan, tête ronde, écharpe rose qui flotte, antenne terminée par une petite étoile."""
    w = 13 * s
    head = (x, y - 250 * s)
    neck = (x, y - 185 * s)
    hip = (x, y - 85 * s)
    if pose == "debout":
        arms = [[neck, (x - 55 * s, y - 130 * s), (x - 70 * s, y - 70 * s)],
                [neck, (x + 55 * s, y - 135 * s), (x + 95 * s, y - 175 * s)]]
        legs = [[hip, (x - 30 * s, y - 40 * s), (x - 45 * s, y)], [hip, (x + 28 * s, y - 40 * s), (x + 40 * s, y)]]
    else:  # vole, bras tendu vers l'avant
        arms = [[neck, (x + 70 * s, y - 200 * s), (x + 140 * s, y - 225 * s)],
                [neck, (x - 60 * s, y - 150 * s), (x - 110 * s, y - 120 * s)]]
        legs = [[hip, (x - 45 * s, y - 60 * s), (x - 110 * s, y - 40 * s)], [hip, (x - 20 * s, y - 30 * s), (x - 70 * s, y + 10 * s)]]
    # écharpe
    sc = [neck, (x - 60 * s, y - 180 * s + 10 * math.sin(t * 4) * s), (x - 130 * s, y - 200 * s + 18 * math.sin(t * 4 + 1) * s),
          (x - 190 * s, y - 175 * s + 22 * math.sin(t * 4 + 2) * s)]
    stroke(c, sc, SCARF, w * 0.9)
    for limb in arms + legs:
        stroke(c, limb, HERO, w)
    stroke(c, [neck, hip], HERO, w)
    c.drawCircle(*head, 50 * s, pen(HERO, w * 2.2, 70, glow=w))
    c.drawCircle(*head, 50 * s, pen(HERO, w))
    # antenne-étoile
    tip = (head[0] + 22 * s, head[1] - 105 * s)
    stroke(c, [(head[0] + 8 * s, head[1] - 50 * s), tip], HERO, w * 0.5)
    star = skia.Path()
    for k in range(10):
        r = (20 if k % 2 == 0 else 8) * s
        a = -math.pi / 2 + k * math.pi / 5
        q = (tip[0] + r * math.cos(a), tip[1] + r * math.sin(a))
        star.moveTo(*q) if k == 0 else star.lineTo(*q)
    star.close()
    c.drawPath(star, brush(GOLD, 200, glow=10 * s))
    c.drawPath(star, brush(GOLD))


def frame(out, name, draw):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    draw(c)
    surf.makeImageSnapshot().save(str(out / f"{name}.png"), skia.kPNG)
    print(out / f"{name}.png")


def personnage(c):
    dust(c)
    floor = [(80, 1300), (1000, 1300)]
    stroke(c, floor, LINE, 3, glow=False)
    dot(c, *floor[0])
    dot(c, *floor[1])
    hero(c, W / 2, 1300, 2.1)


def gravite(c):
    """Concept : les lois de l'univers. Ici, il saute d'orbite en orbite autour d'une planète."""
    dust(c, 3)
    cx, cy = W / 2, 1150
    for r in (170, 300, 430):
        c.drawCircle(cx, cy, r, pen(LINE, 2.5, 200))
    c.drawCircle(cx, cy, 90, brush((10, 10, 14)))
    c.drawCircle(cx, cy, 90, pen(GOLD, 6))
    c.drawCircle(cx, cy, 90, pen(GOLD, 14, 90, glow=12))
    for a, r in ((0.6, 300), (2.4, 430), (4.0, 170)):
        dot(c, cx + math.cos(a) * r, cy + math.sin(a) * r, 9)
    # trajectoire de saut en pointillés
    for k in range(14):
        u = k / 13
        x = cx + math.cos(0.6 + 1.0 * u) * (300 + 130 * math.sin(math.pi * u))
        y = cy + math.sin(0.6 + 1.0 * u) * (300 + 130 * math.sin(math.pi * u)) - 120 * math.sin(math.pi * u)
        c.drawCircle(x, y, 4, brush(HERO, 180))
    hero(c, cx + 250, 690, 1.0, pose="vole", t=1.0)
    c.drawLine(cx, cy, cx + math.cos(0.6) * 300, cy + math.sin(0.6) * 300, pen(LINE, 2, 140))
    c.drawString("g", cx + 120, cy + 40, skia.Font(None, 46), brush(LINE, 220))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    frame(out, "personnage", personnage)
    frame(out, "gravite", gravite)
