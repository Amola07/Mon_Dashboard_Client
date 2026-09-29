"""Fiche personnage d'Éclat : poses principales et couleurs de cape.  python -m films.stick.sheet <image.png>"""
import sys

import skia

from . import hero
from .style_test import LINE, brush, dust

W, H = 1080, 1920


def main(path):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    dust(c, 8, 60)
    font = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 38)
    small = skia.Font(skia.Typeface("DejaVu Sans"), 30)

    def label(txt, x, y, f=font):
        c.drawString(txt, x - f.measureText(txt) / 2, y, f, brush(LINE))

    label("ÉCLAT", W / 2, 90)
    # poses (cape rouge)
    poses = [("debout", 190, 520), ("salut", 540, 520), ("reflexion", 890, 520),
             ("course", 190, 1010), ("saut", 540, 1010), ("vol", 800, 1040)]
    names = {"debout": "debout", "salut": "salut", "reflexion": "réflexion", "course": "course", "saut": "saut", "vol": "vol"}
    for i, (p, x, y) in enumerate(poses):
        hero.draw(c, x, y, 1.0, p, t=0.4 * i, wind=1.6 if p in ("course", "vol") else 0.9)
        label(names[p], x, y + 60, small)
    # couleurs de cape
    label("couleur de cape", W / 2, 1230)
    for i, (name, _) in enumerate(hero.CAPES.items()):
        x = 150 + i * 260
        hero.draw(c, x, 1640, 0.95, "debout", t=1.0, cape=name, wind=1.2)
        label(name, x, 1710, small)
    surf.makeImageSnapshot().save(path, skia.kPNG)
    print(path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "eclat.png")
