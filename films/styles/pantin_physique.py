"""Démo : un personnage animé par la PHYSIQUE (pantin articulé, moteur pymunk), dans le style oscilloscope.

Rien n'est animé à la main : on décrit un corps (segments, articulations, limites, « tonus » musculaire) et la
cabine d'ascenseur ; la gravité fait le reste. Le câble casse → la cabine tombe → le personnage perd l'appui, flotte
et se débat ; le frein de sécurité → il est plaqué au sol et ses genoux plient.

    python -m films.styles.pantin_physique output/demo_pantin.mp4
"""
import math
import subprocess
import sys
import tempfile
import wave

import numpy as np
import pymunk
import skia

from films import montage_ia as MI
from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.styles import oscillo_son as Z
from films.styles.oscillo_ascenseur import AMBRE, VERT, VERT_PALE, P, cercle_pts, faisceau, rect_pts

W, H, FPS = 1080, 1920, 30
PX = 120.0                      # pixels par mètre
G = 9.81 * PX
T_CASSE, T_FREIN, D_FREIN, DUREE = 1.6, 3.4, 0.30, 7.5
CAB_W, CAB_H = 460, 640
CAB_X, CAB_Y = W / 2, 1030      # centre de la cabine à l'écran
S = 1.75                        # taille du personnage


def corps(space, cabine):
    """Le pantin : 10 segments, articulations avec butées et ressorts de tonus. Pieds au plancher."""
    sol = CAB_H / 2 - 6
    def pt(x, y):
        return (x * S, sol + (y - 64) * S)
    groupe = pymunk.ShapeFilter(group=1)
    parties = {}

    def segment(nom, a, b, masse, r=4.5):
        a, b = pt(*a), pt(*b)
        mil = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        bd = pymunk.Body(masse, pymunk.moment_for_segment(masse, (a[0] - mil[0], a[1] - mil[1]),
                                                           (b[0] - mil[0], b[1] - mil[1]), r))
        bd.position = mil
        sh = pymunk.Segment(bd, (a[0] - mil[0], a[1] - mil[1]), (b[0] - mil[0], b[1] - mil[1]), r)
        sh.friction, sh.elasticity, sh.filter = 0.9, 0.05, groupe
        space.add(bd, sh)
        parties[nom] = (bd, sh)
        return bd

    tronc = segment("tronc", (0, -58), (0, 0), 30)
    tete = pymunk.Body(5, pymunk.moment_for_circle(5, 0, 13 * S))
    tete.position = pt(0, -76)
    ct = pymunk.Circle(tete, 13 * S)
    ct.friction, ct.filter = 0.9, groupe
    space.add(tete, ct)
    parties["tete"] = (tete, ct)
    for c, sx in (("g", -1), ("d", 1)):
        segment("bras" + c, (0, -54), (sx * 6, -28), 2.2)
        segment("avbras" + c, (sx * 6, -28), (sx * 8, -4), 1.6)
        segment("cuisse" + c, (sx * 3, 0), (sx * 5, 32), 8)
        segment("jambe" + c, (sx * 5, 32), (sx * 6, 63), 4.5)

    ressorts = {}

    def lien(a, b, ancre, lim, raideur, nom):
        A, B = parties[a][0], parties[b][0]
        space.add(pymunk.PivotJoint(A, B, pt(*ancre)), pymunk.RotaryLimitJoint(A, B, *lim))
        r = pymunk.DampedRotarySpring(A, B, 0.0, raideur, raideur * 0.08)
        space.add(r)
        ressorts[nom] = r

    lien("tronc", "tete", (0, -60), (-0.6, 0.6), 4e7, "cou")
    for c, sx in (("g", -1), ("d", 1)):
        lien("tronc", "bras" + c, (0, -54), (-3.0, 3.0), 6e6, "epaule" + c)
        lien("bras" + c, "avbras" + c, (sx * 6, -28), (-2.3, 0.0) if sx > 0 else (0.0, 2.3), 2e6, "coude" + c)
        lien("tronc", "cuisse" + c, (sx * 3, 0), (-1.6, 1.2), 3e7, "hanche" + c)
        lien("cuisse" + c, "jambe" + c, (sx * 5, 32), (0.0, 2.4) if sx > 0 else (-2.4, 0.0), 3e7, "genou" + c)
    # l'équilibre (comme un réflexe de posture) : le tronc reste droit tant que les pieds ont un appui
    equilibre = pymunk.DampedRotarySpring(cabine, tronc, 0.0, 6e8, 4e7)
    space.add(equilibre)
    ressorts["equilibre"] = equilibre
    return parties, ressorts


def cabine_corps(space):
    cab = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    cab.position = (0, 0)
    space.add(cab)
    w, h = CAB_W / 2, CAB_H / 2
    murs = [((-w, h), (w, h)), ((-w, -h), (w, -h)), ((-w, -h), (-w, h)), ((w, -h), (w, h))]
    for a, b in murs:
        s = pymunk.Segment(cab, a, b, 6)
        s.friction, s.elasticity = 0.9, 0.05
        space.add(s)
    return cab


def simuler():
    """Renvoie, pour chaque image : la vitesse de la cabine et les traits du pantin (repère cabine)."""
    space = pymunk.Space()
    space.gravity = (0, G)
    space.iterations = 30
    cab = cabine_corps(space)
    parties, ressorts = corps(space, cab)
    images = []
    pas = 12
    dt = 1 / (FPS * pas)
    v = 0.0
    t = 0.0
    tonus = {k: r.stiffness for k, r in ressorts.items()}
    for f in range(int(DUREE * FPS)):
        for _ in range(pas):
            if T_CASSE <= t < T_FREIN:
                v += G * dt                                           # chute libre
                if ressorts["equilibre"].stiffness:
                    ressorts["equilibre"].stiffness = 0               # plus d'appui : plus d'équilibre
                    ressorts["equilibre"].damping = 0
                    for nom, (bd, _) in parties.items():              # le sursaut
                        bd.velocity = (bd.velocity[0], bd.velocity[1] - 70)
                    parties["tete"][0].angular_velocity = 0.6
                # panique : les bras s'agitent (muscles qui tirent vers des angles qui changent)
                for c, sx in (("g", -1), ("d", 1)):
                    ressorts["epaule" + c].rest_angle = sx * (2.3 + 0.5 * math.sin(t * 11 + sx))
                    ressorts["coude" + c].rest_angle = -sx * (0.6 + 0.5 * math.sin(t * 13))
                    ressorts["hanche" + c].rest_angle = 0.35 * math.sin(t * 7 + sx * 1.3)
            elif T_FREIN <= t < T_FREIN + D_FREIN:
                v = max(0.0, v - (v_frein / D_FREIN) * dt)               # frein de sécurité
                for nom in ("genoug", "genoud", "hancheg", "hanched"):
                    ressorts[nom].stiffness = tonus[nom] * 0.15         # les jambes cèdent sous le choc
            elif t >= T_FREIN + D_FREIN:
                v = 0.0
                for c in ("g", "d"):
                    ressorts["epaule" + c].rest_angle *= 0.995
            if t < T_FREIN:
                v_frein = v
            cab.velocity = (0, v)
            space.step(dt)
            t += dt
        o = cab.position
        traits = []
        for nom, (bd, sh) in parties.items():
            if isinstance(sh, pymunk.Circle):
                c = bd.local_to_world(sh.offset)
                traits.append(cercle_pts(c[0] - o[0] + CAB_X, c[1] - o[1] + CAB_Y, sh.radius, 20))
            else:
                a, b = bd.local_to_world(sh.a), bd.local_to_world(sh.b)
                traits.append([(a[0] - o[0] + CAB_X, a[1] - o[1] + CAB_Y), (b[0] - o[0] + CAB_X, b[1] - o[1] + CAB_Y)])
        images.append((v / PX * 3.6, cab.position[1] / PX, traits))
    return images


def render(out):
    images = simuler()
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    rng = np.random.default_rng(4)
    for f, (kmh, chute, traits) in enumerate(images):
        t = f / FPS
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        if prec is not None:
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), P((0, 0, 0), 0, 150, fill=True))
        c.save()
        if T_FREIN <= t < T_FREIN + 0.3 or T_CASSE <= t < T_CASSE + 0.15:
            c.translate(rng.normal(0, 7), rng.normal(0, 3))
        # la gaine défile (on tombe)
        dec = (chute * PX) % 140
        for xg in (CAB_X - CAB_W / 2 - 70, CAB_X + CAB_W / 2 + 70):
            faisceau(c, [[(xg - 20, y), (xg + 20, y)] for y in np.arange(560 - dec, 1500, 140)], 1.0, VERT, 0.5, 0.5)
        x0, y0 = CAB_X - CAB_W / 2, CAB_Y - CAB_H / 2
        faisceau(c, [rect_pts(x0, y0, x0 + CAB_W, y0 + CAB_H)], 1.0, AMBRE if T_CASSE <= t < T_FREIN + 0.4 else VERT_PALE, 1.3)
        if t < T_CASSE:
            faisceau(c, [[(CAB_X, 380), (CAB_X, y0)]], 1.0, VERT, 0.9)
        else:
            faisceau(c, [[(CAB_X, 380), (CAB_X + 6, 380 + max(4, 120 - (t - T_CASSE) * 300))]], 1.0, VERT, 0.9)
        faisceau(c, traits, 1.0, VERT_PALE, 1.4)
        c.restore()
        prec = surf.makeImageSnapshot()
        M.ecrit(c, t, -1, "PERSONNAGE PHYSIQUE", W / 2, 230, 64, AMBRE, True, 2.0, vitesse=0.0)
        M.ecrit(c, t, -1, "aucune image animée à la main", W / 2, 290, 30, VERT, vitesse=0.0)
        M.ecrit(c, t, -1, f"{kmh:3.0f} km/h", W / 2, 1520, 70, AMBRE if kmh > 1 else VERT_PALE, True, 1.6, vitesse=0.0)
        etat = ("REPOS" if t < T_CASSE else "CHUTE LIBRE : APESANTEUR" if t < T_FREIN else
                "FREIN : LE CHOC" if t < T_FREIN + 0.8 else "ARRÊT")
        M.ecrit(c, t, -1, etat, W / 2, 1590, 34, VERT_PALE, vitesse=0.0)
        M.ecran(c, t, [T_CASSE, T_FREIN])
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    # son
    n = int(DUREE * MI.SR)
    a = np.zeros(n)
    ev = [(0.0, Z.allumage(0.25)), (T_CASSE, Z.snap(0.5)), (T_CASSE + 0.05, Z.vent(T_FREIN - T_CASSE, 0.25)),
          (T_CASSE + 0.1, Z.crepitement(T_FREIN - T_CASSE, 0.08, 40)), (T_FREIN, Z.boom(0.8, 55)),
          (T_FREIN, Z.clang(160, 0.3, 1.6)), (T_FREIN + 0.15, Z.thump(0.5)), (T_FREIN + 0.35, Z.thump(0.3))]
    for t0, snd in ev:
        i = int(t0 * MI.SR)
        k = min(n - i, len(snd))
        a[i:i + k] += snd[:k]
    a = a / max(1.0, np.abs(a).max() / 0.9)
    with wave.open(f"{tmp}/a.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(MI.SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "output/demo_pantin.mp4")
