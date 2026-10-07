"""Démo : remplacer les poses figées de l'écran "1 - L'INERTIE" (e4, oscillo_ep28.py) par un pantin articulé animé
par la physique (pymunk), comme films/styles/pantin_physique.py pour l'ascenseur.

Rien n'est dessiné à la main : un pantin assis (bassin, torse, tête) subit une poussée d'inertie brutale quand
l'avion freine. SANS CEINTURE : le bassin glisse sur le siège et le corps percute le mur/siège de devant.
AVEC CEINTURE : le bassin est retenu (jonction à distance limitée = la sangle), mais le torse et la tête,
eux, continuent un peu en avant avant de revenir — exactement pourquoi la position de sécurité existe.

    python -m films.episodes.ep28_crash_avion.demo_inertie_physique output/demo_inertie.mp4
"""
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
G = 9.81 * 130.0
SEAT_X, SEAT_Y = 420, 1120                  # la hanche, assise, au repos
WALL_X = SEAT_X + 210                       # siège de devant / cloison (sans ceinture)
T_PULSE, D_PULSE = 1.1, 0.22                # l'avion freine brutalement
A_DECEL = 11.0 * G                          # la poussée d'inertie ressentie (≈ 11 g)
DUREE = 3.3


def construire(space, ceinture):
    groupe = pymunk.ShapeFilter(group=1)
    parties = {}

    def rond(nom, c, r, masse):
        bd = pymunk.Body(masse, pymunk.moment_for_circle(masse, 0, r))
        bd.position = c
        sh = pymunk.Circle(bd, r)
        sh.friction, sh.elasticity, sh.filter = 0.85, 0.1, groupe
        space.add(bd, sh)
        parties[nom] = (bd, sh)
        return bd

    def barre(nom, a, b, masse, r=16):
        mil = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        bd = pymunk.Body(masse, pymunk.moment_for_segment(masse, (a[0] - mil[0], a[1] - mil[1]),
                                                           (b[0] - mil[0], b[1] - mil[1]), r))
        bd.position = mil
        sh = pymunk.Segment(bd, (a[0] - mil[0], a[1] - mil[1]), (b[0] - mil[0], b[1] - mil[1]), r)
        sh.friction, sh.elasticity, sh.filter = 0.85, 0.1, groupe
        space.add(bd, sh)
        parties[nom] = (bd, sh)
        return bd

    bassin = rond("bassin", (SEAT_X, SEAT_Y), 30, 14)
    epaule = (SEAT_X, SEAT_Y - 190)
    torse = barre("torse", (SEAT_X, SEAT_Y - 12), epaule, 16, 22)
    tete = rond("tete", (SEAT_X, SEAT_Y - 250), 38, 5)

    hanche = pymunk.PivotJoint(bassin, torse, (SEAT_X, SEAT_Y - 12))
    space.add(hanche, pymunk.RotaryLimitJoint(bassin, torse, -0.95, 0.35))
    r_hanche = pymunk.DampedRotarySpring(bassin, torse, 0.0, 3.2e6, 2.4e5)
    space.add(r_hanche)
    cou = pymunk.PivotJoint(torse, tete, epaule)
    space.add(cou, pymunk.RotaryLimitJoint(torse, tete, -0.8, 0.5))
    r_cou = pymunk.DampedRotarySpring(torse, tete, 0.0, 1.5e6, 1.1e5)
    space.add(r_cou)

    sol = pymunk.Segment(space.static_body, (SEAT_X - 260, SEAT_Y + 30), (WALL_X + 20, SEAT_Y + 30), 6)
    sol.friction = 0.8
    dossier = pymunk.Segment(space.static_body, (SEAT_X - 240, SEAT_Y + 28), (SEAT_X - 240, SEAT_Y - 300), 6)
    mur = pymunk.Segment(space.static_body, (WALL_X, SEAT_Y + 28), (WALL_X, SEAT_Y - 320), 8)
    mur.elasticity, mur.friction = 0.08, 0.6
    space.add(sol, dossier, mur)
    decor = {"sol": sol, "dossier": dossier, "mur": mur}

    ceinture_j = None
    if ceinture:
        ceinture_j = pymunk.SlideJoint(bassin, space.static_body, (0, 0), (SEAT_X, SEAT_Y), 0, 18)
        space.add(ceinture_j)
    return parties, decor, ceinture_j


def simuler(ceinture):
    space = pymunk.Space()
    space.gravity = (0, G)
    space.iterations = 40
    parties, decor, _ = construire(space, ceinture)
    frames = []
    pas, dt = 10, 1 / (FPS * 10)
    t = 0.0
    impact = {"t": None}
    for f in range(int(DUREE * FPS)):
        for _ in range(pas):
            if T_PULSE <= t < T_PULSE + D_PULSE:
                for nom in ("bassin", "torse", "tete"):
                    bd = parties[nom][0]
                    bd.apply_force_at_world_point((bd.mass * A_DECEL, 0), bd.position)
            space.step(dt)
            t += dt
            if impact["t"] is None and not ceinture:
                bx = parties["bassin"][0].position.x
                if bx > WALL_X - 60 or parties["tete"][0].position.x > WALL_X - 40:
                    impact["t"] = t
        traits = []
        for nom, (bd, sh) in parties.items():
            if isinstance(sh, pymunk.Circle):
                c = bd.local_to_world(sh.offset)
                traits.append(("rond", nom, cercle_pts(c.x, c.y, sh.radius, 22)))
            else:
                a, b = bd.local_to_world(sh.a), bd.local_to_world(sh.b)
                traits.append(("barre", nom, [(a.x, a.y), (b.x, b.y)]))
        frames.append((traits, impact["t"]))
    return frames


def jambe(bx, by, sx):
    return [[(bx, by), (bx + sx * 40, by + 30), (bx + sx * 48, by + 150)],
            [(bx + sx * 48, by + 150), (bx + sx * 100, by + 165)]]


def dessiner(c, traits, col_choc):
    for forme, nom, pts in traits:
        col = AMBRE if (col_choc and nom in ("torse", "tete")) else VERT_PALE
        if forme == "rond":
            faisceau(c, [pts], 1.0, col, 1.4 if nom == "tete" else 1.1)
        else:
            faisceau(c, [pts], 1.0, col, 2.4)
    # jambes dessinées à partir du bassin, purement visuelles (non simulées)
    bassin_pts = next(p for f, n, p in traits if n == "bassin")
    cx = sum(p[0] for p in bassin_pts) / len(bassin_pts)
    cy = sum(p[1] for p in bassin_pts) / len(bassin_pts)
    faisceau(c, jambe(cx, cy + 10, -1), 1.0, VERT, 0.9, 0.8)
    faisceau(c, jambe(cx, cy + 10, 1), 1.0, VERT, 0.9, 0.8)


def phase(surf, ff, ceinture, prec):
    frames = simuler(ceinture)
    titre = "SANS CEINTURE" if not ceinture else "AVEC CEINTURE"
    rng = np.random.default_rng(5 if ceinture else 4)
    sons = []
    for f, (traits, impact_t) in enumerate(frames):
        t = f / FPS
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        if prec is not None:
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), P((0, 0, 0), 0, 150, fill=True))
        c.save()
        choc_t = impact_t if impact_t is not None else (T_PULSE + 0.35 if ceinture else None)
        secoue = choc_t is not None and choc_t <= t < choc_t + 0.3
        if secoue:
            c.translate(rng.normal(0, 8), rng.normal(0, 4))
        faisceau(c, [rect_pts(SEAT_X - 260, SEAT_Y + 30, WALL_X + 20, SEAT_Y + 36)], 1.0, VERT, 0.6, 0.7)
        faisceau(c, [[(SEAT_X - 240, SEAT_Y + 28), (SEAT_X - 240, SEAT_Y - 300)]], 1.0, VERT, 1.0, 0.8)
        if not ceinture:
            col_mur = AMBRE if (impact_t is not None and t >= impact_t) else VERT
            faisceau(c, [[(WALL_X, SEAT_Y + 28), (WALL_X, SEAT_Y - 320)]], 1.0, col_mur, 1.2, 0.9)
        en_choc = T_PULSE <= t < T_PULSE + D_PULSE + 0.15
        dessiner(c, traits, en_choc)
        c.restore()
        prec = surf.makeImageSnapshot()
        M.ecrit(c, t, -1, titre, W / 2, 230, 62, AMBRE, True, 2.0, vitesse=0.0)
        M.ecrit(c, t, -1, "pantin physique, aucune pose dessinée à la main", W / 2, 290, 28, VERT, vitesse=0.0)
        if t >= T_PULSE - 0.05:
            M.ecrit(c, t, T_PULSE - 0.05, "L'AVION FREINE", W / 2, 1480, 46, AMBRE, True, 1.6)
        if t >= T_PULSE + 0.1:
            M.ecrit(c, t, T_PULSE + 0.1, "≈ 11 G", W / 2, 1560, 84, AMBRE, True, 2.0, vitesse=0.0)
        if not ceinture and impact_t and t >= impact_t:
            M.ecrit(c, t, impact_t, "IMPACT", W / 2, 1680, 56, AMBRE, True, 1.8, vitesse=0.0)
        elif ceinture and t >= T_PULSE + D_PULSE:
            M.ecrit(c, t, T_PULSE + D_PULSE, "RETENU PAR LE BASSIN", W / 2, 1680, 42, VERT_PALE, True, 1.6)
        M.ecran(c, t, [T_PULSE] if ceinture else ([impact_t] if impact_t else []))
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
        if secoue and not sons:
            sons.append(t)
    return prec, frames, sons


def render(out):
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    _, frames1, sons1 = phase(surf, ff, False, None)
    _, frames2, sons2 = phase(surf, ff, True, None)
    ff.stdin.close()
    ff.wait()
    n = int((DUREE * 2) * MI.SR)
    a = np.zeros(n)
    ev = [(0.0, Z.allumage(0.2)), (T_PULSE - 0.15, Z.riser(0.25, 0.08)), (T_PULSE, Z.whoosh(0.3, 0.12))]
    if sons1:
        ev += [(sons1[0], Z.boom(0.5, 60)), (sons1[0], Z.clang(220, 0.25, 1.4)), (sons1[0] + 0.05, Z.craquement(0.2))]
    else:
        ev.append((T_PULSE + D_PULSE, Z.thump(0.3)))
    ev += [(DUREE + T_PULSE - 0.15, Z.riser(0.25, 0.08)), (DUREE + T_PULSE, Z.whoosh(0.3, 0.12)),
           (DUREE + T_PULSE + D_PULSE, Z.thump(0.4)), (DUREE + T_PULSE + D_PULSE + 0.05, Z.clang(600, 0.15, 0.6))]
    for t0, snd in ev:
        i = int(t0 * MI.SR)
        k = min(n - i, len(snd))
        if k > 0 and i >= 0:
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
    render(sys.argv[1] if len(sys.argv) > 1 else "output/demo_inertie.mp4")
