"""Quatre images de style de « Goutte » en 2D graphique. python -m films.goutte2d.style_frames <dossier>"""
import sys
from pathlib import Path

import skia

from .style import (DROP, LINE, Dust, H, W, cloud, col, draw_drop, flower, glow_path, heat_waves, horizon, paint,
                    rain, rock, sprout, sun, vapor)

out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
out.mkdir(parents=True, exist_ok=True)
dust = Dust()


def frame(name, draw):
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(skia.ColorBLACK)
    draw(c)
    s.makeImageSnapshot().save(str(out / f"{name}.png"), skia.kPNG)


def chute(c):
    dust.draw(c, 3.0)
    horizon(c, 1500)
    x, y = W / 2, 820
    for k in range(10):                                   # traînée de chute : pointillés
        c.drawCircle(x, y - 60 - k * 38, 5 - k * 0.4, paint(col(DROP, 200 - k * 18)))
    draw_drop(c, x, y, 150, sx=0.85, sz=1.25, eyes=1.3, mouth=-0.0)
    guide = skia.Path()                                    # repère de hauteur, comme une règle
    guide.moveTo(W / 2 + 220, 300)
    guide.lineTo(W / 2 + 220, 1470)
    glow_path(c, guide, LINE, 2.0, glow=0.3, alpha=160)
    for k in range(9):
        yy = 300 + k * 146
        c.drawLine(W / 2 + 208, yy, W / 2 + 232, yy, paint(col(LINE, 160), "stroke", 2))


def soleil(c):
    dust.draw(c, 5.0)
    xs, ys = horizon(c, 1420)
    sun(c, W / 2 + 180, 420, 95, heat=0.9, t=2.0)
    heat_waves(c, W / 2 - 40, 1030, 1260, 1.3)
    draw_drop(c, W / 2 - 60, 1412, 230, eyes=0.35, mouth=0.4)
    vapor(c, W / 2 - 60, 1412 - 330, 1.0)


def pousse(c):
    dust.draw(c, 8.0)
    horizon(c, 1420, amp=18)
    rock(c, W / 2 + 290, 1404, 190)
    sprout(c, W / 2 + 90, 1408, 230, alive=0.0)
    draw_drop(c, W / 2 - 150, 1412, 150, eyes=0.7, look=(0.05, 0.0), mouth=-0.5)


def pluie(c):
    dust.draw(c, 12.0)
    cloud(c, W / 2, 520, 420, frown=1.0)
    rain(c, W / 2 - 330, W / 2 + 330, 640, 1400, 0.4)
    xs, ys = horizon(c, 1420, amp=18)
    import random
    rnd = random.Random(4)
    for k in range(11):
        x = 80 + k * 92 + rnd.uniform(-20, 20)
        flower(c, x, 1440 - 18 * abs(((x - 540) / 540)), rnd.uniform(120, 220), bloom=rnd.uniform(0.5, 1.0),
               petals=rnd.choice([5, 6, 7]), rot=rnd.uniform(0, 3))
    flower(c, W / 2 + 60, 1430, 430, bloom=1.0, petals=8)


for name, fn in [("1_chute", chute), ("2_soleil", soleil), ("3_pousse", pousse), ("4_pluie", pluie)]:
    frame(name, fn)
    print(out / f"{name}.png")
