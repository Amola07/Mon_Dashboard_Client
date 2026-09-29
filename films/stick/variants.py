"""Planche de variantes du personnage (bonhomme bâton lumineux sur fond noir).

    python -m films.stick.variants <image.png>
"""
import math
import sys

import skia

from .style_test import GOLD, LINE, brush, col, dust, pen, stroke

W, H = 1080, 1920


def body(c, x, y, s, rgb, w):
    neck, hip = (x, y - 185 * s), (x, y - 85 * s)
    for limb in ([neck, (x - 50 * s, y - 130 * s), (x - 62 * s, y - 75 * s)],
                 [neck, (x + 52 * s, y - 135 * s), (x + 90 * s, y - 180 * s)],
                 [hip, (x - 28 * s, y - 42 * s), (x - 40 * s, y)],
                 [hip, (x + 26 * s, y - 42 * s), (x + 38 * s, y)],
                 [neck, hip]):
        stroke(c, limb, rgb, w)
    return neck


def star_shape(x, y, r):
    p = skia.Path()
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.42
        a = -math.pi / 2 + k * math.pi / 5
        q = (x + rr * math.cos(a), y + rr * math.sin(a))
        p.moveTo(*q) if k == 0 else p.lineTo(*q)
    p.close()
    return p


def variant(c, k, x, y, s):
    w = 12 * s
    head = (x, y - 245 * s)
    hr = 48 * s
    if k == 1:   # Nova : cyan, écharpe rose, antenne-étoile
        rgb = (40, 215, 255)
        stroke(c, [(x, y - 185 * s), (x - 70 * s, y - 175 * s), (x - 140 * s, y - 195 * s), (x - 190 * s, y - 170 * s)], (255, 90, 150), w * 0.9)
        body(c, x, y, s, rgb, w)
        c.drawCircle(*head, hr, pen(rgb, w * 2, 70, glow=w)); c.drawCircle(*head, hr, pen(rgb, w))
        tip = (head[0] + 20 * s, head[1] - 100 * s)
        stroke(c, [(head[0] + 8 * s, head[1] - hr), tip], rgb, w * 0.5)
        c.drawPath(star_shape(*tip, 20 * s), brush(GOLD))
    elif k == 2:  # Orbite : violet, un anneau doré qui tourne autour de la tête
        rgb = (190, 110, 255)
        body(c, x, y, s, rgb, w)
        c.drawCircle(*head, hr, pen(rgb, w * 2, 70, glow=w)); c.drawCircle(*head, hr, pen(rgb, w))
        ring = skia.Rect.MakeXYWH(head[0] - 85 * s, head[1] - 22 * s, 170 * s, 44 * s)
        c.drawOval(ring, pen(GOLD, 5 * s, 90, glow=8 * s)); c.drawOval(ring, pen(GOLD, 4 * s))
        c.drawCircle(head[0] + 80 * s, head[1] + 4 * s, 8 * s, brush(GOLD))
    elif k == 3:  # Lueur : blanc, un œil lumineux au milieu de la tête
        rgb = (245, 245, 255)
        body(c, x, y, s, rgb, w)
        c.drawCircle(*head, hr, pen(rgb, w * 2, 60, glow=w)); c.drawCircle(*head, hr, pen(rgb, w))
        c.drawCircle(head[0] + 10 * s, head[1], 14 * s, brush((80, 230, 255), 200, glow=12 * s))
        c.drawCircle(head[0] + 10 * s, head[1], 11 * s, brush((80, 230, 255)))
    elif k == 4:  # Comète : vert citron, flamme-chevelure qui traîne derrière
        rgb = (170, 255, 90)
        body(c, x, y, s, rgb, w)
        for j, (dx, dy) in enumerate(((-60, -30), (-95, -5), (-80, 25))):
            stroke(c, [(head[0] - 30 * s, head[1] + (j - 1) * 18 * s), (head[0] + dx * s, head[1] + dy * s - 20 * s),
                       (head[0] + (dx - 55) * s, head[1] + (dy - 10) * s)], (255, 210, 80), w * 0.6)
        c.drawCircle(*head, hr, pen(rgb, w * 2, 70, glow=w)); c.drawCircle(*head, hr, pen(rgb, w))
    elif k == 5:  # Astro : bleu, casque d'astronaute avec visière dorée
        rgb = (90, 160, 255)
        body(c, x, y, s, rgb, w)
        c.drawCircle(*head, hr * 1.15, pen(rgb, w * 2, 70, glow=w)); c.drawCircle(*head, hr * 1.15, pen(rgb, w))
        visor = skia.Path()
        visor.addArc(skia.Rect.MakeXYWH(head[0] - 30 * s, head[1] - 26 * s, 62 * s, 52 * s), -60, 120)
        c.drawPath(visor, pen(GOLD, 9 * s))
        stroke(c, [(x - 22 * s, y - 180 * s), (x - 22 * s, y - 120 * s)], (200, 210, 230), w * 1.6, glow=False)
    elif k == 6:  # Prisme : magenta, tête triangulaire (le seul non rond)
        rgb = (255, 70, 200)
        body(c, x, y, s, rgb, w)
        tri = skia.Path()
        tri.moveTo(head[0], head[1] - 62 * s)
        tri.lineTo(head[0] + 58 * s, head[1] + 42 * s)
        tri.lineTo(head[0] - 58 * s, head[1] + 42 * s)
        tri.close()
        c.drawPath(tri, pen(rgb, w * 2, 70, glow=w)); c.drawPath(tri, pen(rgb, w))
        for j, cc in enumerate(((255, 80, 80), (255, 210, 60), (80, 255, 140), (80, 170, 255))):
            stroke(c, [(head[0] + 40 * s, head[1] + (j * 10 - 10) * s), (head[0] + 110 * s, head[1] + (j * 22 - 20) * s)],
                   cc, 4 * s, glow=False)
    elif k == 7:  # Éclat : doré, une cape courte qui bat au vent
        rgb = (255, 196, 70)
        cape = skia.Path()
        cape.moveTo(x - 10 * s, y - 185 * s)
        cape.quadTo(x - 120 * s, y - 150 * s, x - 150 * s, y - 70 * s)
        cape.lineTo(x - 40 * s, y - 95 * s)
        cape.close()
        c.drawPath(cape, brush((255, 110, 60), 170))
        body(c, x, y, s, rgb, w)
        c.drawCircle(*head, hr, pen(rgb, w * 2, 70, glow=w)); c.drawCircle(*head, hr, pen(rgb, w))
    elif k == 8:  # Pixel : turquoise, écouteurs et petite traînée de notes
        rgb = (60, 255, 210)
        body(c, x, y, s, rgb, w)
        c.drawCircle(*head, hr, pen(rgb, w * 2, 70, glow=w)); c.drawCircle(*head, hr, pen(rgb, w))
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeXYWH(head[0] - 60 * s, head[1] - 62 * s, 120 * s, 120 * s), 180, 180)
        c.drawPath(arc, pen((255, 255, 255), 6 * s))
        for side in (-1, 1):
            c.drawRoundRect(skia.Rect.MakeXYWH(head[0] + side * 60 * s - 12 * s, head[1] - 18 * s, 24 * s, 40 * s), 8 * s, 8 * s,
                            brush((255, 90, 150)))


NAMES = {1: "Nova", 2: "Orbite", 3: "Lueur", 4: "Comète", 5: "Astro", 6: "Prisme", 7: "Éclat", 8: "Pixel"}


def main(path):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    dust(c, 5, 60)
    font = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 40)
    for k in range(1, 9):
        cx = 270 + ((k - 1) % 2) * 540
        cy = 440 + ((k - 1) // 2) * 450
        variant(c, k, cx, cy, 1.05)
        label = f"{k}. {NAMES[k]}"
        c.drawString(label, cx - font.measureText(label) / 2, cy + 70, font, brush(LINE))
    surf.makeImageSnapshot().save(path, skia.kPNG)
    print(path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "variantes.png")
