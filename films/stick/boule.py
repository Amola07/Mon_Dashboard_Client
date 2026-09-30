"""Scène test : Éclat en boule (tête, yeux, écharpe — sans membres) dans la pièce dont la gravité suit la flèche.

Tout son jeu passe par la physique et le visage : il tombe, s'écrase, rebondit, roule, se ramasse avant de sauter,
s'étire en vol, et ses yeux regardent ce qui compte. Rien n'est une pose inventée : c'est ce que je fais bien.

    python -m films.stick.boule sortie.mp4
"""
import math
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from . import corps as K
from . import foley
from .hero import CAPES, CYAN, _brush, _pen, draw_emote, draw_face

W, H, FPS = 1080, 1920, 60
DT = 1 / FPS
ROOM = 300.0                                                  # pièce : carré de ±300
R = 58.0                                                      # rayon d'Éclat
G = 1500.0
SCALE = 1.62
GOLD = (255, 196, 70)
LINE = (236, 240, 248)
DUR = 21.0


def unit(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def keys(t, ks):
    """Interpolation douce entre valeurs clés [(t, v), …]."""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, a), (t1, b) in zip(ks, ks[1:]):
        if t < t1:
            return a + (b - a) * ease((t - t0) / (t1 - t0))
    return ks[-1][1]


# ------------------------------------------------------------------------------------------------ le scénario
# direction de la flèche (degrés écran, 90 = vers le bas), sa longueur (0 = absente)
PHI = [(0.0, 90.0), (6.8, 90.0), (7.4, 0.0), (9.6, 0.0), (10.6, -90.0)]
ARROW_L = [(0.0, 0.0), (2.2, 0.0), (2.6, 200.0), (17.2, 200.0), (18.0, 0.0)]
T_BUMP_MIN = 13.3                                             # il fonce sur la flèche après ce moment
# sauts : (début de la charge, durée de la charge, direction fixée ou "fleche", vitesse)
HOPS = [(4.05, 0.14, None, 420.0), (13.0, 0.28, "fleche", 780.0)]
# expressions et émotions (début, expression, émotion)
FACE = [(0.0, "dort", "zzz"), (3.1, "dort", None), (3.55, "surpris", "!"), (4.6, "curieux", None),
        (5.6, "curieux", "?"), (7.0, "surpris", None), (7.5, "peur", None), (8.25, "etourdi", "etoiles"),
        (9.4, "colere", None), (10.0, "surpris", "!"), (10.3, "peur", None), (11.6, "etourdi", None),
        (12.3, "decide", None), (12.55, "joie", "!"), (13.0, "decide", None), (13.6, "surpris", None),
        (14.0, "peur", "sueur"), (17.6, "etourdi", "etoiles"), (18.6, "joie", None), (19.3, "fatigue", None),
        (19.9, "dort", "zzz")]
# où il regarde : (début, cible) — "fleche", "bas", point fixe, ou None (droit devant)
GAZE = [(0.0, None), (3.7, (-240.0, 120.0)), (4.2, (240.0, 120.0)), (4.7, "fleche"), (7.5, "vitesse"),
        (8.3, None), (9.5, "fleche"), (10.3, "vitesse"), (11.7, "fleche"), (13.6, "vitesse"), (18.6, None)]


def at(track, t):
    cur = track[0]
    for k in track:
        if t >= k[0]:
            cur = k
    return cur


class Ball:
    def __init__(self):
        self.p = np.array([-60.0, -40.0])
        self.v = np.array([6.0, 0.0])
        self.face_a = -90.0 + 90                                # angle du visage (0 = tête en haut)
        self.s, self.sv = 0.0, 0.0                              # écrasement (+) / étirement (-) le long de l'axe
        self.axis = 90.0                                        # axe de la déformation (degrés)
        self.contact = None                                     # normale du mur touché
        self.hop = None
        self.hops_done = set()


class Scene:
    def __init__(self):
        self.b = Ball()
        self.arrow_w = 0.0                                      # vitesse de rotation de la flèche (après le choc)
        self.arrow_phi = PHI[0][1]
        self.bumped = None
        self.events = []                                        # (t, genre, position, force)
        self.frames = []
        self.cape = None

    def gravity(self, t):
        L = keys(t, ARROW_L)
        return np.array(unit(self.arrow_phi)) * G * (L / 200.0), L

    def step(self, t):
        b = self.b
        # ---- la flèche : suit son tracé, puis tourne librement après le choc
        if self.bumped is None:
            self.arrow_phi = keys(t, PHI)
        else:
            self.arrow_phi += self.arrow_w * DT
            self.arrow_w *= math.exp(-DT / 2.2)
        g, L = self.gravity(t)
        gm = float(np.hypot(*g))
        up = -g / gm if gm > 1 else np.array(unit(b.face_a - 90))
        # ---- sauts : charge (écrasé contre le sol), puis détente
        for k, (t0, dur, aim, speed) in enumerate(HOPS):
            if k in b.hops_done or t < t0:
                continue
            if t < t0 + dur:
                b.hop = (k, t0, dur)
                b.axis = math.degrees(math.atan2(up[1], up[0]))
                b.s += (0.32 - b.s) * 0.25                       # il se ramasse
                b.sv = 0.0
            else:
                if aim == "fleche":                            # visée balistique : il arrive sur la flèche
                    T = 0.42
                    b.v = (np.zeros(2) - b.p - 0.5 * g * T * T) / T
                    d = b.v.copy()
                else:
                    d = up
                    b.v = d / np.hypot(*d) * speed
                b.s, b.sv = -0.22, 0.0                          # détente : il s'étire
                b.axis = math.degrees(math.atan2(d[1], d[0]))
                b.hops_done.add(k)
                b.hop = None
                self.events.append((t, "whoosh", tuple(b.p), 0.6))
        # ---- mouvement (sous-pas)
        sub = 4
        h = DT / sub
        b.contact = None
        for _ in range(sub):
            if b.hop is None:
                b.v += g * h
            else:
                b.v *= 0.0
            if gm < 1:                                          # apesanteur : dérive lente, amortie
                b.v *= 1 - 0.25 * h
            b.p += b.v * h
            lim = ROOM - R * 0.98
            for ax in (0, 1):
                for sg in (-1, 1):
                    if b.p[ax] * sg > lim:
                        b.p[ax] = lim * sg
                        vn = b.v[ax] * sg
                        n = np.zeros(2)
                        n[ax] = -sg
                        if vn > 0:
                            if vn > 90:
                                b.s, b.sv = 0.0, 0.0
                                b.sv = min(9.0, vn / 110)       # choc : il s'écrase
                                b.axis = math.degrees(math.atan2(n[1], n[0]))
                                self.events.append((t, "bonk" if vn > 700 else "thud", tuple(b.p - n * R),
                                                    min(1.0, vn / 900)))
                            b.v[ax] = -0.38 * b.v[ax] if vn > 120 else 0.0
                        b.v[1 - ax] *= 0.995                    # frottement léger : il roule
                        b.contact = n
        # ---- le choc contre la flèche : elle part en toupie
        ad = np.array(unit(self.arrow_phi))
        proj = max(-100.0, min(100.0, float(np.dot(b.p, ad))))
        if self.bumped is None and t > T_BUMP_MIN and np.hypot(*(b.p - ad * proj)) < R + 6:
            self.bumped = t
            self.arrow_w = 900.0
            b.v = -b.v * 0.5
            self.events.append((t, "clang", (0.0, 0.0), 0.9))
        # ---- déformation : ressort peu amorti ; en vol, étiré dans le sens de la vitesse
        sp = float(np.hypot(*b.v))
        target = 0.0
        if b.contact is None and b.hop is None and sp > 350:
            target = -min(0.2, (sp - 350) / 2500)
            va = math.degrees(math.atan2(b.v[1], b.v[0]))
            b.axis += ((va - b.axis + 90) % 180 - 90) * 0.2
        if b.hop is None:
            b.sv += (-(b.s - target) * 520 - b.sv * 11) * DT
            b.s += b.sv * DT
            b.s = max(-0.3, min(0.45, b.s))
        # ---- orientation du visage : vers « le haut » du moment ; il roule quand il glisse au sol
        up_a = math.degrees(math.atan2(up[0], -up[1]))
        if b.contact is not None and gm > 1:
            tang = np.array([-b.contact[1], b.contact[0]])
            b.face_a += math.degrees(float(np.dot(b.v, tang)) / R * DT) * 0.35
        d = (up_a - b.face_a + 180) % 360 - 180
        b.face_a += d * (0.045 if self.bumped and t < 17.6 else 0.12)
        if gm < 1 and t < 2.6:                                  # il dort en flottant, tourne doucement
            b.face_a = -14 + 6 * math.sin(t * 0.9)
            b.p += np.array([math.sin(t * 0.6) * 0.15, math.cos(t * 0.5) * 0.12])
        if gm < 1 and t > 18.0:                                 # retour doux vers la position du début (boucle)
            home = np.array([-60.0, -40.0])
            b.v += (home - b.p) * 2.2 * DT - b.v * 3.0 * DT
            b.face_a += ((-14 - b.face_a + 180) % 360 - 180) * 0.02
        # ---- regard
        gz = at(GAZE, t)[1]
        if gz == "fleche":
            gp = np.zeros(2)
        elif gz == "vitesse":
            gp = b.p + b.v * 0.4 if sp > 40 else None
        elif gz is None:
            gp = None
        else:
            gp = np.array(gz)
        _, expr, emo = at(FACE, t)
        emo_t0 = at(FACE, t)[0]
        # ---- écharpe
        ua = math.radians(b.face_a)
        upv = np.array([math.sin(ua), -math.cos(ua)])
        side = np.array([-upv[1], upv[0]])                    # l'écharpe part du côté, à mi-hauteur : bien visible
        anchor = tuple(b.p + side * R * 0.92 - upv * R * 0.15)
        if self.cape is None:
            self.cape = K.Cape(anchor, n=7, seg=17.0)
        gg = tuple(g) if gm > 1 else (0.0, 0.0)
        back = tuple(-np.array([-upv[1], upv[0]]))
        self.cape.step(anchor, back, gg, DT, flutter=1.0 if gm < 1 else 0.3, t=t,
                       bounds=(-ROOM + 2, -ROOM + 2, ROOM - 2, ROOM - 2))
        self.frames.append(dict(p=tuple(b.p), s=b.s, axis=b.axis, face=b.face_a, expr=expr,
                                emo=(emo, t - emo_t0) if emo else None, gaze=None if gp is None else tuple(gp),
                                phi=self.arrow_phi, L=L, g=tuple(g), cape=list(self.cape.p)))

    def run(self):
        for f in range(int(DUR * FPS)):
            self.step(f * DT)
        return self


# ------------------------------------------------------------------------------------------------ dessin
def draw_arrow(c, phi, L):
    if L < 3:
        return
    d = np.array(unit(phi))
    n = np.array([-d[1], d[0]])
    tail, tip = -d * L / 2, d * L / 2
    k = min(1.0, L / 120)
    neck = tip - d * 30 * k
    c.drawLine(*tail, *neck, _pen(GOLD, 8))
    path = skia.Path()
    path.moveTo(*(tip + d * 4))
    path.lineTo(*(neck + n * 20 * k))
    path.lineTo(*(neck - n * 20 * k))
    path.close()
    c.drawPath(path, _brush(GOLD))
    side = n if n[1] <= 0.01 else -n
    gpos = tip - d * 26 * k + side * 44
    f = skia.Font(skia.Typeface("DejaVu Serif", skia.FontStyle.Italic()), 40 * max(0.5, k))
    c.drawString("g", gpos[0] - 11, gpos[1] + 12, f, _brush(GOLD))


def draw_field(c, g, t):
    gm = float(np.hypot(*g))
    step = 100.0
    if gm < 20:
        for i in range(-2, 3):
            for j in range(-2, 3):
                c.drawCircle(i * step + 16 * math.sin(t * 0.5 + j), j * step + 16 * math.cos(t * 0.4 + i), 2.2,
                             _brush(GOLD, 70))
        return
    d = np.array(g) / gm
    off = (t * 80) % step
    for i in range(-3, 4):
        for j in range(-3, 4):
            q = np.array([i * step + (j % 2) * step / 2, j * step]) + d * (off - step / 2)
            if abs(q[0]) > ROOM - 16 or abs(q[1]) > ROOM - 16:
                continue
            e = q + d * 16
            c.drawLine(*q, *e, _pen(GOLD, 2.2, 80))


def draw_ball(c, fr, t):
    p, s, axis = fr["p"], fr["s"], fr["axis"]
    c.save()
    c.translate(*p)
    c.rotate(axis)                                              # écrasé le long de l'axe, élargi en travers
    c.scale(1 / (1 + s) ** 0.5 * (1 - 0.55 * s), (1 + s) ** 0.5 * (1 + 0.55 * s) / (1 + 0.1 * abs(s)))
    c.rotate(-axis)
    c.drawCircle(0, 0, R, _brush((0, 0, 0)))
    c.drawCircle(0, 0, R, _pen(CYAN, 9.5))
    look = (0.0, 0.0)
    a = math.radians(fr["face"])
    if fr["gaze"] is not None:
        d = np.array(fr["gaze"]) - np.array(p)
        lx, ly = d[0] * math.cos(-a) - d[1] * math.sin(-a), d[0] * math.sin(-a) + d[1] * math.cos(-a)
        n = math.hypot(lx, ly) or 1.0
        k = min(1.0, n / 100)
        look = (lx / n * k, ly / n * k)
    # visage grand et centré (c'est tout son jeu) : on annule le décalage « de profil » du visage standard
    rf = R * 1.45
    kf = rf / 50
    draw_face(c, (-10 * kf * math.cos(a), -10 * kf * math.sin(a)), rf, a, 1, fr["expr"],
              (look[0] * 0.8, look[1] * 0.8), t)
    c.restore()
    if fr["emo"]:
        kind, age = fr["emo"]
        c.save()
        c.translate(*p)
        if kind == "zzz":
            for i in range(3):
                u = (age * 0.8 + i / 3) % 1.0
                f = skia.Font(skia.Typeface("DejaVu Sans", skia.FontStyle.Bold()), 16 + 14 * u)
                c.drawString("z", 34 + 34 * u + 6 * math.sin(age * 3 + i), -44 - 70 * u, f,
                             _brush((230, 240, 255), 255 * math.sin(math.pi * u)))
        else:
            draw_emote(c, (0.0, 0.0), R * 1.2, kind, t, age)
        c.restore()


def draw_frame(c, sc, f, stars):
    fr = sc.frames[f]
    t = f * DT
    c.clear(skia.Color(0, 0, 0))
    c.save()
    c.translate(W / 2, H / 2)
    for x, y, s, ph in stars:
        c.drawCircle(x, y, s, _brush(LINE, 120 * (0.5 + 0.5 * math.sin(ph + t * 1.3))))
    c.scale(SCALE, SCALE)
    walls = skia.Path()
    walls.addRect(skia.Rect(-ROOM, -ROOM, ROOM, ROOM))
    c.drawPath(walls, _pen(LINE, 2.4, 230))
    draw_field(c, fr["g"], t)
    cape = K.Cape((0, 0), n=7, seg=17.0)
    cape.p = fr["cape"]
    poly = cape.shape()
    path = skia.Path()
    path.moveTo(*poly[0])
    for q in poly[1:]:
        path.lineTo(*q)
    path.close()
    c.drawPath(path, _brush(CAPES["violet"], 235))
    draw_arrow(c, fr["phi"], fr["L"])
    draw_ball(c, fr, t)
    c.restore()


# ------------------------------------------------------------------------------------------------ son
def soundtrack(sc, path):
    mx = foley.Mixer(DUR)
    for t, kind, pos, force in sc.events:
        pan = max(-1.0, min(1.0, pos[0] / ROOM))
        if kind == "thud":
            mx.add(t, foley.thud(force), pan, 0.9)
        elif kind == "bonk":
            mx.add(t, foley.bonk(force), pan, 0.9)
            mx.add(t, foley.thud(force * 0.7), pan, 0.7)
        elif kind == "whoosh":
            mx.add(t, foley.whoosh(0.35, force, 1100), pan, 0.7)
        elif kind == "clang":
            mx.add(t, foley.clang(force), 0.0, 0.9)
    L = np.array([fr["L"] for fr in sc.frames]) / 200.0
    gm = np.array([math.hypot(*fr["g"]) for fr in sc.frames]) / G
    mx.add_stream(foley.hum_stream(70 + 40 * gm, 0.5 * L, DUR), 0.8)
    mx.add_stream(foley.wind_stream(0.05 * (1 - np.minimum(1, L)), DUR), 0.6)
    out = np.tanh(mx.out * 2.2) * 0.55
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(foley.SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "output/boule_test.mp4"
    sc = Scene().run()
    rng = np.random.default_rng(5)
    stars = [(rng.uniform(-W / 2, W / 2), rng.uniform(-H / 2, H / 2), rng.power(4) * 2 + 0.5, rng.uniform(0, 6.3))
             for _ in range(260)]
    tmp = tempfile.mkdtemp()
    vid = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", vid],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(len(sc.frames)):
        draw_frame(surf.getCanvas(), sc, f, stars)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    wav = f"{tmp}/a.wav"
    soundtrack(sc, wav)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", out], check=True)
    print(out, f"{DUR:.1f} s")


if __name__ == "__main__":
    main()
