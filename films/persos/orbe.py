"""L'Orbe : la mascotte des vidéos éducatives (choisie parmi les concepts modernes).

Une sphère de lumière dont les couleurs tournent lentement, avec deux yeux-lumière.
  • Ses couleurs suivent son humeur : bleu-violet au calme, chaudes quand il est content, cyan quand il réfléchit,
    rose vif quand il est surpris, dorées quand il a une idée.
  • Ses yeux changent de forme (pilules, arcs de joie, cercles, étoiles, cœurs, spirales, pilule plissée…).
  • Il n'a pas de bras : pour montrer quelque chose, il envoie un rayon de lumière vers la cible.
  • Il flotte, se gonfle et s'écrase légèrement à chaque changement d'émotion, pulse quand il parle.

Utilisation : draw_orbe(canvas, t, Etat(...)) dessine l'Orbe centré en (0, 0), rayon 140.

    python -m films.persos.orbe sortie.mp4          (planche animée de toutes ses expressions)
"""
import math
import subprocess
import sys
from dataclasses import dataclass

import skia

W, H, FPS = 1080, 1920, 30
R = 140.0

# palettes d'humeur : quatre couleurs qui tournent dans la sphère, et la couleur du halo
HUMEURS = {
    "calme": [(90, 120, 255), (190, 90, 255), (255, 110, 190), (90, 220, 255)],
    "joie": [(255, 150, 90), (255, 110, 170), (255, 210, 90), (200, 110, 255)],
    "reflexion": [(60, 200, 255), (90, 120, 255), (120, 255, 220), (70, 150, 255)],
    "surprise": [(255, 80, 150), (255, 150, 90), (190, 90, 255), (255, 90, 120)],
    "idee": [(255, 210, 80), (255, 240, 150), (255, 160, 70), (255, 230, 120)],
    "triste": [(80, 100, 180), (110, 120, 200), (70, 90, 160), (120, 140, 210)],
}
HUMEUR_DE = {"neutre": "calme", "parle": "calme", "joie": "joie", "amour": "joie", "surpris": "surprise",
             "reflechit": "reflexion", "idee": "idee", "triste": "triste", "etourdi": "surprise"}


@dataclass
class Etat:
    expr: str = "neutre"
    age: float = 0.0                     # temps depuis le début de l'expression (s)
    regard: tuple = (0.0, 0.0)           # -1..1
    cligne: bool = False
    cible: tuple = None                  # point montré par le rayon de lumière (coordonnées locales)
    humeur_mix: float = 1.0              # transition de couleur vers la nouvelle humeur (0..1)
    humeur_avant: str = "calme"


def rgb(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(a))


def P(color=(255, 255, 255), a=255, shader=None, blur=0.0, stroke=0.0):
    p = skia.Paint(AntiAlias=True, Color=rgb(color, a))
    if shader is not None:
        p.setShader(shader)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def mix(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def palette(e):
    new = HUMEURS[HUMEUR_DE.get(e.expr, "calme")]
    old = HUMEURS[e.humeur_avant]
    u = ease(e.humeur_mix)
    return [mix(o, n, u) for o, n in zip(old, new)]


def star(x, y, r, k=0.45):
    p = skia.Path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * k
        a = -math.pi / 2 + i * math.pi / 5
        q = (x + rr * math.cos(a), y + rr * math.sin(a))
        p.moveTo(*q) if i == 0 else p.lineTo(*q)
    p.close()
    return p


def heart(x, y, r):
    p = skia.Path()
    p.moveTo(x, y + r * 0.9)
    p.cubicTo(x - r * 1.4, y - r * 0.1, x - r * 0.7, y - r * 1.2, x, y - r * 0.45)
    p.cubicTo(x + r * 0.7, y - r * 1.2, x + r * 1.4, y - r * 0.1, x, y + r * 0.9)
    p.close()
    return p


def yeux(c, t, e):
    h = 64.0
    wdt = h * 0.46
    lx, ly = e.regard
    white = (255, 255, 255)
    for side in (-1, 1):
        x, y = side * 38 + lx * 20, -6 + ly * 16
        halo = P(white, 150, blur=20)
        if e.cligne and e.expr in ("neutre", "parle", "reflechit"):
            c.drawRoundRect(skia.Rect(x - 16, y - 4, x + 16, y + 4), 4, 4, P(white))
            continue
        ex = e.expr
        if ex in ("joie", "idee") and not (ex == "idee" and e.age > 0.25):
            p = skia.Path()
            p.moveTo(x - 17, y + 8)
            p.quadTo(x, y - 36, x + 17, y + 8)
            c.drawPath(p, P(white, 150, blur=8, stroke=16))
            c.drawPath(p, P(white, stroke=12))
        elif ex == "idee":                                      # des étoiles dans les yeux
            s = 1 + 0.12 * math.sin(t * 10)
            c.drawPath(star(x, y, 26 * s), halo)
            c.drawPath(star(x, y, 24 * s), P(white))
        elif ex == "amour":
            s = 1 + 0.14 * math.sin(t * 12)
            c.drawPath(heart(x, y, 20 * s), halo)
            c.drawPath(heart(x, y, 20 * s), P(white))
        elif ex == "surpris":
            c.drawCircle(x, y, 30, halo)
            c.drawCircle(x, y, 28, P(white))
        elif ex == "etourdi":
            p = skia.Path()
            for k in range(44):
                a = k * 0.42 + t * 8 * side
                rr = k * 0.62
                q = (x + rr * math.cos(a), y + rr * math.sin(a))
                p.moveTo(*q) if k == 0 else p.lineTo(*q)
            c.drawPath(p, P(white, stroke=5))
        elif ex == "triste":                                    # pilules penchées vers l'extérieur, paupière
            c.save()
            c.translate(x, y + 6)
            c.rotate(-side * 14)
            rr = skia.RRect.MakeRectXY(skia.Rect(-wdt / 2, -h * 0.34, wdt / 2, h * 0.34), wdt / 2, wdt / 2)
            c.drawRRect(rr, halo)
            c.drawRRect(rr, P(white))
            c.restore()
        else:
            hh = h * (0.28 if (ex == "reflechit" and side == 1) else 1.0)
            rr = skia.RRect.MakeRectXY(skia.Rect(x - wdt / 2, y - hh / 2, x + wdt / 2, y + hh / 2), wdt / 2, wdt / 2)
            c.drawRRect(rr, halo)
            c.drawRRect(rr, P(white))


def bouche(c, t, e):
    white = (255, 255, 255)
    ex = e.expr
    if ex in ("joie", "idee", "amour"):
        p = skia.Path()
        p.moveTo(-22, 46)
        p.quadTo(0, 72, 22, 46)
        c.drawPath(p, P(white, stroke=7))
    elif ex == "surpris":
        c.drawCircle(0, 56, 9, P(white, stroke=6))
    elif ex == "parle":
        o = 5 + 14 * abs(math.sin(t * 13)) * (0.6 + 0.4 * math.sin(t * 3.1))
        c.drawRoundRect(skia.Rect(-12, 50 - o / 2, 12, 50 + o / 2), 8, 8, P(white))
    elif ex == "triste":
        p = skia.Path()
        p.moveTo(-18, 58)
        p.quadTo(0, 44, 18, 58)
        c.drawPath(p, P(white, stroke=6))
    elif ex == "etourdi":
        p = skia.Path()
        p.moveTo(-22, 54)
        for k in range(1, 7):
            p.lineTo(-22 + k * 7.3, 54 + (6 if k % 2 else -6))
        c.drawPath(p, P(white, stroke=5))


def rayon(c, t, e):
    """Pour montrer quelque chose : un rayon de lumière part de l'Orbe vers la cible."""
    if e.cible is None:
        return
    tx, ty = e.cible
    d = math.hypot(tx, ty) or 1.0
    ux, uy = tx / d, ty / d
    grow = ease(e.age / 0.25)
    sx, sy = ux * (R + 6), uy * (R + 6)
    ex, ey = sx + (tx - sx) * grow, sy + (ty - sy) * grow
    col = palette(e)[0]
    c.drawLine(sx, sy, ex, ey, P(col, 120, blur=10, stroke=18))
    c.drawLine(sx, sy, ex, ey, P((255, 255, 255), 230, stroke=5))
    if grow > 0.95:
        pulse = 1 + 0.2 * math.sin(t * 8)
        c.drawCircle(tx, ty, 26 * pulse, P(col, 130, blur=12))
        c.drawCircle(tx, ty, 10, P((255, 255, 255)))


def draw_orbe(c, t, e, parle_pulse=True):
    cols = palette(e)
    # respiration / pulsation de la parole / écrasement au changement d'émotion
    pulse = 0.015 * math.sin(t * 2.4)
    if e.expr == "parle" and parle_pulse:
        pulse += 0.025 * abs(math.sin(t * 13))
    sq = 0.08 * math.exp(-e.age * 8) * math.cos(e.age * 28)
    if e.expr == "surpris":
        sq -= 0.08 * math.exp(-e.age * 5)
    rayon(c, t, e)
    c.save()
    c.scale((1 + pulse) * (1 + sq), (1 + pulse) * (1 - sq))
    glow = cols[0] if e.expr != "idee" else (255, 220, 110)
    c.drawCircle(0, 0, R * 1.3, P(glow, 120 if e.expr != "idee" else 170, blur=60))
    path = skia.Path()
    path.addCircle(0, 0, R)
    sweep = skia.GradientShader.MakeSweep(0, 0, [rgb(x) for x in cols + [cols[0]]],
                                          localMatrix=skia.Matrix.RotateDeg(t * 40))
    c.drawPath(path, P(shader=sweep))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.drawCircle(-30, -40, 150, P((255, 255, 255), 90, blur=40))              # volume : lumière haute
    c.drawCircle(40, 60, 120, P((20, 10, 60), 120, blur=40))                  # ombre basse
    c.drawOval(skia.Rect(-90, -118, 10, -70), P((255, 255, 255), 170, blur=10))
    c.restore()
    c.drawCircle(0, 0, R, P((255, 255, 255), 120, stroke=3))
    c.save()
    if e.expr == "reflechit":
        c.rotate(6 * ease(e.age / 0.3))
    yeux(c, t, e)
    bouche(c, t, e)
    c.restore()
    c.restore()
    # petites étincelles autour pour la joie et l'idée
    if e.expr in ("joie", "idee", "amour"):
        for i in range(5):
            a = t * 1.5 + i * 2 * math.pi / 5
            rr = R * 1.35 + 10 * math.sin(t * 4 + i)
            x, y = rr * math.cos(a), rr * math.sin(a)
            s = 8 + 4 * math.sin(t * 9 + i)
            c.drawPath(star(x, y, s, 0.35), P((255, 245, 200), 230))


# ------------------------------------------------------------------------------------------------ planche animée
SEQ = [(0.0, "neutre", None, "Bonjour"), (2.0, "parle", None, "Il explique"),
       (4.4, "parle", (170, 230), "Il montre (rayon de lumière)"), (6.8, "reflechit", None, "Il réfléchit"),
       (8.8, "idee", None, "Il a une idée"), (10.8, "joie", None, "Joie"), (12.6, "surpris", None, "Surprise"),
       (14.2, "triste", None, "Triste"), (15.8, "etourdi", None, "Sonné"), (17.4, "amour", None, "Il adore")]
DUR = 19.2


def state_at(t):
    cur, prev = SEQ[0], SEQ[0]
    for s in SEQ:
        if t >= s[0]:
            prev, cur = cur, s
    t0, expr, cible, lab = cur
    a = t - t0
    e = Etat(expr=expr, age=a, cible=cible, humeur_mix=a / 0.6,
             humeur_avant=HUMEUR_DE.get(prev[1], "calme") if prev is not cur else "calme")
    e.cligne = (t % 3.1) < 0.12
    if expr == "reflechit":
        e.regard = (0.6 * ease(a / 0.3), -0.6 * ease(a / 0.3))
    if cible is not None:
        e.regard = (0.7 * ease(a / 0.3), 0.5 * ease(a / 0.3))
    return e, lab


def frame(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P(shader=skia.GradientShader.MakeLinear(
        [skia.Point(0, 0), skia.Point(0, H)], [rgb((22, 20, 44)), rgb((40, 26, 70)), rgb((18, 30, 60))])))
    c.drawCircle(200, 300, 400, P((120, 80, 255), 40, blur=120))
    c.drawCircle(900, 1500, 450, P((60, 200, 255), 35, blur=140))
    e, lab = state_at(t)
    c.save()
    c.translate(W / 2, 820 + 12 * math.sin(t * 2.2))
    c.scale(1.35, 1.35)
    if e.cible is not None:                                   # un petit objet à montrer
        tx, ty = e.cible                                      # la cible est le coin de l'objet montré
        bx, by = tx + 80, ty + 62
        c.drawRoundRect(skia.Rect(bx - 74, by - 54, bx + 74, by + 54), 20, 20, P((255, 255, 255), 30))
        c.drawRoundRect(skia.Rect(bx - 74, by - 54, bx + 74, by + 54), 20, 20, P((255, 255, 255), 90, stroke=2))
        f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 46)
        c.drawString("180°", bx - f.measureText("180°") / 2, by + 16, f, P((255, 255, 255)))
    draw_orbe(c, t, e)
    c.restore()
    f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 50)
    wdt = f.measureText(lab)
    c.drawString(lab, W / 2 - wdt / 2, 1520, f, P((255, 255, 255), 230))
    t1 = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 60)
    c.drawString("L'Orbe", W / 2 - t1.measureText("L'Orbe") / 2, 200, t1, P((255, 255, 255)))


def sheet(path):
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.drawRect(skia.Rect(0, 0, W, H), P(shader=skia.GradientShader.MakeLinear(
        [skia.Point(0, 0), skia.Point(0, H)], [rgb((22, 20, 44)), rgb((40, 26, 70)), rgb((18, 30, 60))])))
    items = [("neutre", "calme"), ("parle", "il explique"), ("reflechit", "il réfléchit"), ("idee", "une idée !"),
             ("joie", "joie"), ("surpris", "surprise"), ("triste", "triste"), ("etourdi", "sonné"),
             ("amour", "il adore")]
    f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 36)
    for i, (ex, lab) in enumerate(items):
        x, y = 190 + (i % 3) * 350, 330 + (i // 3) * 560
        c.save()
        c.translate(x, y)
        c.scale(0.8, 0.8)
        draw_orbe(c, 1.3 + i * 0.7, Etat(expr=ex, age=1.0, regard=(0.5, -0.5) if ex == "reflechit" else (0, 0)))
        c.restore()
        c.drawString(lab, x - f.measureText(lab) / 2, y + 230, f, P((255, 255, 255), 230))
    s.makeImageSnapshot().save(path)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/orbe.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    sheet(out.replace(".mp4", "_expressions.png"))
    print(out)


if __name__ == "__main__":
    main()
