"""Personnage Open Peeps qui parle : bouche dessinée synchronisée sur la voix (films.persos.levres), clignements,
mouvements de tête suivant la voix, expressions qui changent au fil du texte.

    python -m films.peeps.parle voix.mp3 debut duree sortie.mp4
"""
import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import skia

from films import montage_ia as MI
from films.persos import levres as LV

HERE = os.path.dirname(os.path.abspath(__file__))
SVG = os.path.join(HERE, "svg")
W, H, FPS = 1080, 1920, 30
VB = (184.2, 210.8, 940.3, 1130.6)                 # cadre du buste Open Peeps (composant Effigy)
INK = (27, 27, 47)
EFF = open(os.path.join(HERE, "effigy_offsets.js")).read()


def _offset(fn, t):
    m = re.search(r"var %s = function.*?\n};" % fn, EFF, re.S)
    for k, tr in re.findall(r'\.type === "(\w+)"\)\s*\{\s*return React\.createElement\("g", \{ transform: \'([^\']+)\'', m.group(0)):
        if k == t:
            return tr
    return "translate(0 0)"


def _inner(path):
    return re.sub(r"^<svg[^>]*>|</svg>$", "", open(path).read())


def face_sans_bouche(name):
    """Visage sans sa bouche : on retire les sous-tracés situés dans la zone de la bouche (sous le nez)."""
    s = _inner(os.path.join(SVG, "face", name + ".svg"))

    def keep(d):
        subs = [p for p in re.split(r"(?=M)", d) if p]
        out = []
        for sp in subs:
            nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", sp)]
            ys = nums[1::2]
            if min(ys) > 195 or (len(sp) < 200 and min(ys) > 185) or (min(ys) > 175 and np.mean(ys) > 205):
                continue
            out.append(sp)
        return "".join(out)
    return re.sub(r'd="([^"]+)"', lambda m: f'd="{keep(m.group(1))}"', s)


def doc(groups):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB[0]} {VB[1]} {VB[2]} {VB[3]}">{"".join(groups)}</svg>'
    return skia.SVGDOM.MakeFromStream(skia.MemoryStream(svg.encode()))


class Peep:
    def __init__(self, body="Explaining", hair="ShortTwo", beard=None, faces=("Smile", "EyesClosed", "Awe", "Concerned"),
                 size=900):
        self.size = size
        self.body = doc([f'<g transform="translate(147, 639)">{_inner(os.path.join(SVG, "body/effigy", body + ".svg"))}</g>'])
        hair_g = f'<g transform="translate(342, 190)"><g transform="{_offset("createHair", hair)}">{_inner(os.path.join(SVG, "head", hair + ".svg"))}</g></g>'
        beard_g = (f'<g transform="translate(495, 518)"><g transform="{_offset("createBeard", beard)}">'
                   f'{_inner(os.path.join(SVG, "beard", beard + ".svg"))}</g></g>') if beard else ""
        self.heads = {f: doc([hair_g, f'<g transform="translate(531, 366)">{face_sans_bouche(f)}</g>', beard_g]) for f in faces}
        for d in [self.body] + list(self.heads.values()):
            d.setContainerSize(skia.Size(size, size * VB[3] / VB[2]))
        self.k = size / VB[2]

    def to_px(self, x, y):
        return (x - VB[0]) * self.k, (y - VB[1]) * self.k

    def draw(self, c, x, y, face, mouth, tilt=0.0, nod=0.0, breath=0.0):
        """Dessine le buste avec son coin haut gauche en (x, y)."""
        c.save()
        c.translate(x, y)
        c.save()
        px, py = self.to_px(640, 1000)
        c.translate(px, py)
        c.scale(1 + breath, 1 + breath)
        c.translate(-px, -py)
        self.body.render(c)
        c.restore()
        nx, ny = self.to_px(660, 640)                     # pivot du cou
        c.translate(nx, ny + nod)
        c.rotate(tilt)
        c.translate(-nx, -ny)
        self.heads[face].render(c)
        mx, my = self.to_px(531 + 165, 366 + 230)         # centre de la bouche (vue de trois-quarts)
        c.translate(mx, my)
        c.scale(self.k * 1.45, self.k * 1.45)
        bouche(c, *mouth)
        c.restore()


def bouche(c, w, h, dents, langue):
    ink = skia.Paint(AntiAlias=True, Color=skia.Color(*INK), Style=skia.Paint.kStroke_Style, StrokeWidth=7,
                     StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
    w = w * 1.05
    if h < 7:                                            # lèvres fermées : un trait légèrement souriant
        p = skia.Path()
        p.moveTo(-w / 2, -2)
        p.quadTo(0, 6, w / 2, -3)
        c.drawPath(p, ink)
        return
    p = skia.Path()                                      # bouche ouverte : haut presque plat, bas arrondi
    p.moveTo(-w / 2, -h * 0.35)
    p.cubicTo(-w * 0.2, -h * 0.5, w * 0.2, -h * 0.5, w / 2, -h * 0.35)
    p.cubicTo(w * 0.48, h * 0.45, -w * 0.48, h * 0.45, -w / 2, -h * 0.35)
    p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=skia.Color(70, 20, 32)))
    c.save()
    c.clipPath(p, doAntiAlias=True)
    if dents > 0.3:
        c.drawRect(skia.Rect(-w / 2, -h * 0.6, w / 2, -h * 0.5 + 9), skia.Paint(AntiAlias=True, Color=skia.ColorWHITE))
    if langue > 0.3:
        c.drawOval(skia.Rect(-w * 0.3, h * 0.0, w * 0.3, h * 0.6), skia.Paint(AntiAlias=True, Color=skia.Color(232, 106, 122)))
    c.restore()
    c.drawPath(p, ink)


def main():
    voix, t0, dur, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    from films.episodes.ep12_pyramide.montage import SEG
    sync = LV.Synchro(voix, t0, dur)
    env, rate = sync.env, sync.rate
    subs = MI.groups([(txt, a - t0, b - t0) for txt, a, b in SEG if t0 <= a < t0 + dur])
    # expressions au fil du texte (instants dans la voix d'origine)
    expr = [(6.24, 8.9, "Awe"), (14.26, 17.7, "Concerned")]
    peep = Peep(beard="Chin")
    tmp = tempfile.mkdtemp()
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", f"{tmp}/v.mp4"],
                           stdin=subprocess.PIPE)
    arr = np.zeros((H, W, 4), np.uint8)
    for i in range(int(dur * FPS)):
        t = i / FPS
        arr[:] = (243, 233, 216, 255)
        c = skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType).getCanvas()
        c.drawCircle(W / 2, 760, 520, skia.Paint(AntiAlias=True, Color=skia.Color(232, 214, 188)))
        face = "Smile"
        for a, b, f in expr:
            if a - t0 <= t < b - t0:
                face = f
        if face == "Smile" and (t % 3.7) < 0.13:
            face = "EyesClosed"
        e = env[min(len(env) - 1, int((t + 0.05) * rate))]
        slow = env[max(0, int((t - 0.25) * rate)):int((t + 0.05) * rate) + 1].mean() if t > 0.3 else 0
        tilt = 2.2 * math.sin(t * 0.9) + 2.0 * (e - slow)
        nod = 10 * (e - slow)
        peep.draw(c, (W - peep.size) / 2, 330, face, sync(t), tilt=tilt, nod=nod, breath=0.006 * math.sin(t * 1.6))
        MI.draw_sub(c, t, subs)
        enc.stdin.write(arr.tobytes())
    enc.stdin.close()
    enc.wait()
    v = MI.load_voice(voix)[int(t0 * MI.SR): int((t0 + dur) * MI.SR)]
    MI.soundtrack(f"{tmp}/a.wav", v, dur)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    main()
