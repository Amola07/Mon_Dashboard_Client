"""Test « anime chibi entièrement codé » : une petite voyageuse sous un ciel étoilé.

Tout est dessiné par le code (Skia) : contours, aplats, une ombre en « cel shading », grands yeux à reflets.
Animation : clignements, mèches et cape au vent, regard vers le ciel, étoile filante, lente poussée de caméra.

    python -m films.anime.chibi sortie.mp4 [secondes]
"""
import math
import subprocess
import sys

import numpy as np
import skia

W, H, FPS = 1080, 1920, 60
INK = (34, 28, 52)


def col(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def fill(c, path, rgb, a=255, shader=None):
    p = skia.Paint(AntiAlias=True, Color=col(rgb, a))
    if shader is not None:
        p.setShader(shader)
    c.drawPath(path, p)


def line(c, path, width=5, rgb=INK, a=255):
    p = skia.Paint(AntiAlias=True, Color=col(rgb, a), Style=skia.Paint.kStroke_Style, StrokeWidth=width)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    c.drawPath(path, p)


def glow(c, x, y, r, rgb, a=120):
    g = skia.GradientShader.MakeRadial((x, y), r, [col(rgb, a), col(rgb, 0)])
    p = skia.Paint(AntiAlias=True, Shader=g, BlendMode=skia.BlendMode.kPlus)
    c.drawCircle(x, y, r, p)


def poly(pts, closed=True, smooth=True):
    """Chemin lissé passant par des points (courbes de Catmull-Rom converties en Bézier)."""
    path = skia.Path()
    n = len(pts)
    path.moveTo(*pts[0])
    rng_ = range(n if closed else n - 1)
    for i in rng_:
        p0, p1 = pts[(i - 1) % n], pts[i]
        p2, p3 = pts[(i + 1) % n], pts[(i + 2) % n]
        if not closed:
            p0 = pts[max(i - 1, 0)]
            p3 = pts[min(i + 2, n - 1)]
        if smooth:
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            path.cubicTo(*c1, *c2, *p2)
        else:
            path.lineTo(*p2)
    if closed:
        path.close()
    return path


class Sky:
    def __init__(self, seed=2):
        r = np.random.default_rng(seed)
        n = 300
        self.stars = np.column_stack([r.uniform(0, W, n), r.uniform(0, H * 0.75, n), r.power(6, n) * 2.8 + 0.3,
                                      r.uniform(0, 6.28, n), r.uniform(0.5, 2.0, n)])

    def draw(self, c, t):
        g = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [col((10, 8, 34)), col((34, 22, 78)), col((92, 58, 128))],
                                           [0.0, 0.62, 1.0])
        c.drawPaint(skia.Paint(Shader=g))
        glow(c, W * 0.72, H * 0.3, 620, (120, 90, 220), 60)          # nébuleuse
        glow(c, W * 0.25, H * 0.18, 480, (60, 120, 220), 45)
        for x, y, s, ph, sp in self.stars:
            a = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(ph + t * sp))
            if s > 2.3:
                glow(c, x, y, s * 6, (200, 220, 255), 60 * a)
            c.drawCircle(x, y, s, skia.Paint(AntiAlias=True, Color=col((255, 255, 255), 255 * a)))
        # étoile filante
        u = (t % 6.0) / 1.2
        if 0 <= u <= 1:
            x0, y0 = W * (0.95 - 0.7 * u), H * (0.06 + 0.2 * u)
            p = skia.Paint(AntiAlias=True, StrokeWidth=4, Style=skia.Paint.kStroke_Style, BlendMode=skia.BlendMode.kPlus)
            p.setShader(skia.GradientShader.MakeLinear([(x0, y0), (x0 + 260, y0 - 75)],
                                                       [col((255, 255, 255), 255 * (1 - u)), col((255, 255, 255), 0)]))
            c.drawLine(x0, y0, x0 + 260, y0 - 75, p)
            glow(c, x0, y0, 30, (200, 230, 255), 200 * (1 - u))


def hill(c):
    pts = [(-20, 1500), (200, 1450), (420, 1420), (640, 1430), (860, 1470), (1100, 1530), (1100, 1940), (-20, 1940)]
    path = poly(pts, closed=True)
    fill(c, path, (22, 16, 40))
    rim = poly(pts[:6], closed=False)
    line(c, rim, 3, (150, 130, 230), 200)
    for x in range(60, 1040, 70):                       # herbes
        y = 1430 + 0.0004 * (x - 520) ** 2
        g = skia.Path()
        g.moveTo(x, y + 6)
        g.quadTo(x + 4, y - 18, x + 10, y - 30)
        line(c, g, 3, (60, 44, 100))


def character(c, cx, ground, t, blink, look_up):
    """Chibi : grosse tête, grands yeux, mèches qui bougent au vent, cape, petite lanterne-étoile."""
    s = 1.0
    wind = math.sin(t * 1.7) * 0.5 + math.sin(t * 3.1) * 0.25
    hy = ground - 520                                   # centre de la tête
    # cape (derrière)
    cape = [(cx - 120, hy + 200), (cx + 120, hy + 200), (cx + 190 + 40 * wind, ground - 40),
            (cx + 60 + 20 * wind, ground - 10), (cx - 70, ground - 20), (cx - 170 + 25 * wind, ground - 60)]
    fill(c, poly(cape), (64, 52, 140))
    shade = [(cx + 20, hy + 210), (cx + 120, hy + 200), (cx + 190 + 40 * wind, ground - 40), (cx + 60 + 20 * wind, ground - 10)]
    fill(c, poly(shade), (44, 34, 104))
    line(c, poly(cape), 5)
    # corps
    body = [(cx - 85, hy + 190), (cx + 85, hy + 190), (cx + 110, ground - 70), (cx - 110, ground - 70)]
    fill(c, poly(body), (236, 232, 246))
    fill(c, poly([(cx + 10, hy + 195), (cx + 85, hy + 190), (cx + 110, ground - 70), (cx + 25, ground - 70)]), (196, 190, 222))
    line(c, poly(body), 5)
    for side in (-1, 1):                                # jambes
        leg = poly([(cx + side * 40 - 22, ground - 72), (cx + side * 40 + 22, ground - 72),
                    (cx + side * 44 + 20, ground - 8), (cx + side * 44 - 24, ground - 8)])
        fill(c, leg, (60, 50, 90))
        line(c, leg, 5)
    scarf = [(cx - 95, hy + 185), (cx + 95, hy + 185), (cx + 100, hy + 225), (cx - 90, hy + 228)]
    tail = [(cx - 60, hy + 215), (cx - 20, hy + 225), (cx - 150 - 60 * wind, hy + 330 + 20 * wind),
            (cx - 200 - 70 * wind, hy + 300 + 25 * wind)]
    for part in (tail, scarf):
        fill(c, poly(part), (226, 70, 96))
        line(c, poly(part), 5)
    # bras qui tient la lanterne-étoile
    lx, ly = cx + 150, hy + 300 + 8 * math.sin(t * 2)
    arm = poly([(cx + 62, hy + 212), (lx - 18, ly - 38), (lx + 16, ly - 6), (cx + 92, hy + 262)])
    fill(c, arm, (236, 232, 246))
    line(c, arm, 5)
    glow(c, lx + 10, ly + 30, 170, (120, 200, 255), 150)
    star = skia.Path()
    for k in range(10):
        r = 48 if k % 2 == 0 else 20
        a = -math.pi / 2 + k * math.pi / 5 + t * 0.6
        pt = (lx + 10 + r * math.cos(a), ly + 30 + r * math.sin(a))
        star.moveTo(*pt) if k == 0 else star.lineTo(*pt)
    star.close()
    fill(c, star, (200, 240, 255))
    line(c, star, 3, (90, 150, 230))
    # tête
    head = skia.Path()
    head.addOval(skia.Rect.MakeXYWH(cx - 190, hy - 175, 380, 360))
    fill(c, head, (255, 226, 214))
    line(c, head, 6)
    # cheveux : masse arrière + mèches avant qui ondulent
    back = [(cx - 215, hy + 40), (cx - 205, hy - 120), (cx - 120, hy - 215), (cx + 20, hy - 235), (cx + 150, hy - 200),
            (cx + 225, hy - 90), (cx + 230, hy + 90), (cx + 250 + 25 * wind, hy + 190), (cx + 150, hy + 150),
            (cx - 150, hy + 160), (cx - 245 + 20 * wind, hy + 200)]
    bangs = [(cx - 200, hy - 20), (cx - 170, hy - 150), (cx - 60, hy - 205), (cx + 80, hy - 195), (cx + 180, hy - 120),
             (cx + 205, hy + 10), (cx + 150, hy - 40 + 6 * wind), (cx + 110, hy + 10), (cx + 60, hy - 60 + 5 * wind),
             (cx, hy - 10), (cx - 50, hy - 70 + 5 * wind), (cx - 110, hy + 5), (cx - 150, hy - 50 + 6 * wind)]
    c.save()
    clip = skia.Path()
    clip.addRect(skia.Rect.MakeLTRB(0, 0, W, H))
    fill(c, poly(back), (48, 44, 110))
    line(c, poly(back), 6)
    fill(c, head, (255, 226, 214))
    line(c, head, 6)
    c.restore()
    # visage
    ey = hy + 60 - 22 * look_up
    for side in (-1, 1):
        ex = cx + side * 78
        h = 110 * blink
        if blink > 0.12:
            eye = skia.Path()
            eye.addOval(skia.Rect.MakeXYWH(ex - 42, ey - h / 2, 84, h))
            iris = skia.GradientShader.MakeLinear([(ex, ey - h / 2), (ex, ey + h / 2)],
                                                  [col((30, 40, 120)), col((70, 150, 240)), col((170, 230, 255))], [0, 0.55, 1])
            fill(c, eye, (0, 0, 0), shader=iris)
            line(c, eye, 5)
            c.drawCircle(ex - 14, ey - h * 0.22, 15, skia.Paint(AntiAlias=True, Color=col((255, 255, 255))))
            c.drawCircle(ex + 16, ey + h * 0.2, 7, skia.Paint(AntiAlias=True, Color=col((255, 255, 255))))
            lash = skia.Path()
            lash.moveTo(ex - 50, ey - h / 2 + 4)
            lash.quadTo(ex, ey - h / 2 - 16, ex + 52, ey - h / 2 + 2)
            line(c, lash, 8)
        else:
            closed = skia.Path()
            closed.moveTo(ex - 42, ey)
            closed.quadTo(ex, ey + 18, ex + 42, ey)
            line(c, closed, 7)
        glow(c, ex + side * 40, ey + 70, 46, (255, 130, 150), 90)
    mouth = skia.Path()
    mouth.moveTo(cx - 16, ey + 92)
    mouth.quadTo(cx, ey + 104, cx + 16, ey + 92)
    line(c, mouth, 5)
    fill(c, poly(bangs), (58, 54, 132))
    fill(c, poly([(cx + 60, hy - 190), (cx + 180, hy - 120), (cx + 205, hy + 10), (cx + 150, hy - 40)]), (40, 36, 96))
    line(c, poly(bangs), 6)
    shine = poly([(cx - 110, hy - 150), (cx - 40, hy - 175), (cx + 40, hy - 172), (cx - 30, hy - 158)], smooth=True)
    fill(c, shine, (140, 140, 230), 160)


def render(out, seconds=8.0):
    sky = Sky()
    ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(seconds * FPS)):
        t = f / FPS
        c = surf.getCanvas()
        sky.draw(c, t)
        zoom = 1 + 0.06 * t / seconds                   # lente poussée de caméra
        c.save()
        c.translate(W / 2, H * 0.7)
        c.scale(zoom, zoom)
        c.translate(-W / 2, -H * 0.7)
        hill(c)
        bl = 1.0
        for b in (2.3, 5.6):                            # clignements
            if b < t < b + 0.16:
                bl = abs((t - b) / 0.08 - 1)
        look = min(1.0, max(0.0, (t - 3.2) / 0.8))
        character(c, W / 2 - 60, 1452, t, bl, look)
        c.restore()
        ff.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "chibi.mp4", float(sys.argv[2]) if len(sys.argv) > 2 else 8.0)
