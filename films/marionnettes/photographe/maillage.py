"""Personnage entier (pieces/complet.png) animé par capture de mouvement : maillage déformable + skinning 2D.

Principe (comme AnimatedDrawings de Meta) : l'image est triangulée ; chaque sommet suit un ou plusieurs os avec des
poids doux (flexion progressive aux articulations) ; la pose de chaque image vient d'un mouvement CMU projeté en 2D,
recalé sur les longueurs d'os du dessin. Les bras sont des maillages séparés (sinon le torse se déformerait avec eux).
"""
import math
import os

import cv2
import numpy as np
import skia

from films.constellation.corps import KEEP, Mouvement

HERE = os.path.dirname(os.path.abspath(__file__))
J = {k: i for i, k in enumerate(KEEP)}

# squelette au repos, coordonnées de complet.png (côté « g » = à gauche de l'écran = bras droit du personnage)
REST = {"bassin": (140, 440), "cou": (150, 165), "tete": (148, 20),
        "epaule_g": (62, 205), "coude_g": (40, 335), "poignet_g": (55, 470), "main_g": (60, 530),
        "epaule_d": (212, 200), "coude_d": (230, 335), "poignet_d": (225, 450), "main_d": (232, 505),
        "hanche_g": (100, 450), "genou_g": (95, 640), "cheville_g": (82, 800), "orteil_g": (45, 865),
        "hanche_d": (182, 450), "genou_d": (185, 640), "cheville_d": (192, 800), "orteil_d": (225, 862)}
# os : (nom, articulation de départ, d'arrivée)
OS = [("tronc", "bassin", "cou"), ("tete", "cou", "tete"),
      ("bras_g", "epaule_g", "coude_g"), ("avbras_g", "coude_g", "poignet_g"), ("main_g", "poignet_g", "main_g"),
      ("bras_d", "epaule_d", "coude_d"), ("avbras_d", "coude_d", "poignet_d"), ("main_d", "poignet_d", "main_d"),
      ("cuisse_g", "hanche_g", "genou_g"), ("tibia_g", "genou_g", "cheville_g"), ("pied_g", "cheville_g", "orteil_g"),
      ("cuisse_d", "hanche_d", "genou_d"), ("tibia_d", "genou_d", "cheville_d"), ("pied_d", "cheville_d", "orteil_d")]
OI = {o[0]: i for i, o in enumerate(OS)}
# mocap → articulations du dessin (le bras droit du personnage est à gauche de l'écran)
MOCAP = {"bassin": "Hips", "cou": "Neck", "tete": "Head_end",
         "epaule_g": "RightArm", "coude_g": "RightForeArm", "poignet_g": "RightHand", "main_g": "RightHandIndex1",
         "epaule_d": "LeftArm", "coude_d": "LeftForeArm", "poignet_d": "LeftHand", "main_d": "LeftHandIndex1",
         "hanche_g": "RightUpLeg", "genou_g": "RightLeg", "cheville_g": "RightFoot", "orteil_g": "RightToeBase",
         "hanche_d": "LeftUpLeg", "genou_d": "LeftLeg", "cheville_d": "LeftFoot", "orteil_d": "LeftToeBase"}
BRAS_G = np.array([(0, 175), (66, 175), (86, 262), (89, 430), (86, 570), (0, 570)], np.int32)
BRAS_D = np.array([(203, 175), (255, 175), (255, 570), (196, 570), (196, 430), (198, 262)], np.int32)


def _seg_dist(p, a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    u = np.clip(((p - a) @ d) / (d @ d), 0, 1)
    return np.linalg.norm(p - (a + u[:, None] * d), axis=1)


class Personnage:
    def __init__(self, png=os.path.join(HERE, "pieces", "complet.png"), pas=9):
        self.gauche = None
        im = cv2.imread(png, cv2.IMREAD_UNCHANGED)
        self.h, self.w = im.shape[:2]
        rgba = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
        self.image = skia.Image.fromarray(np.ascontiguousarray(rgba))
        alpha = im[:, :, 3] > 20
        zone = np.zeros(alpha.shape, np.uint8)          # 0 corps, 1/2 bras gauche/droit, 3/4 jambe gauche/droite
        zone[470:, :141] = 3
        zone[470:, 141:] = 4
        cv2.fillPoly(zone, [BRAS_G], 1)
        cv2.fillPoly(zone, [BRAS_D], 2)
        # dans la zone des bras, le pantalon (noir, loin de toute peau ou manche) reste au corps / aux jambes
        hsv = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2HSV)
        clair = (hsv[:, :, 2] > 75) & alpha
        loin = cv2.distanceTransform((~clair).astype(np.uint8), cv2.DIST_L2, 3) > 3.5
        bras = (zone == 1) | (zone == 2)
        rows = np.arange(self.h)[:, None] > 430
        pant = bras & loin & rows & alpha
        zone[pant & (np.arange(self.w)[None, :] < 141)] = 3
        zone[pant & (np.arange(self.w)[None, :] >= 141)] = 4
        # les petits îlots d'une zone (bouts de contour isolés) rejoignent la zone voisine dominante
        for _ in range(2):
            for z in range(5):
                n, lab, st, _ = cv2.connectedComponentsWithStats(((zone == z) & alpha).astype(np.uint8), 8)
                if n <= 2:
                    continue
                big = 1 + int(np.argmax(st[1:, 4]))
                for i in range(1, n):
                    if i == big or st[i, 4] > 0.25 * st[big, 4]:
                        continue
                    comp = lab == i
                    ring = cv2.dilate(comp.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~comp & alpha
                    vals = zone[ring]
                    vals = vals[vals != z]
                    if len(vals):
                        zone[comp] = np.bincount(vals).argmax()
        self.parts = []
        for z, allowed in ((3, ["tronc", "cuisse_g", "tibia_g", "pied_g"]), (4, ["tronc", "cuisse_d", "tibia_d", "pied_d"]),
                           (0, ["tronc", "tete", "cuisse_g", "cuisse_d"]),
                           (1, ["tronc", "bras_g", "avbras_g", "main_g"]), (2, ["tronc", "bras_d", "avbras_d", "main_d"])):
            m = alpha & (zone == z)
            if z in (3, 4):                                         # recouvrement sous le bas du pull
                m = m | (alpha & (zone == 0) & (np.arange(self.h)[:, None] > 455)
                         & ((np.arange(self.w)[None, :] < 141) == (z == 3)))
            self.parts.append(self._mesh(m.astype(np.uint8), allowed, z))

    def _mesh(self, m, allowed, z):
        m = cv2.dilate(m, np.ones((3, 3), np.uint8))
        pts = [(x, y) for y in range(0, self.h, 9) for x in range(0, self.w, 9) if m[y, x]]
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for cnt in cs:
            pts += [tuple(int(v) for v in q[0]) for q in cnt[::4]]
        pts = np.array(sorted(set(pts)), np.float32)
        sub = cv2.Subdiv2D((-2, -2, self.w + 4, self.h + 4))
        for p in pts:
            sub.insert((float(p[0]), float(p[1])))
        index = {(round(float(p[0]), 2), round(float(p[1]), 2)): i for i, p in enumerate(pts)}
        tris = []
        mm = cv2.dilate(m, np.ones((3, 3), np.uint8))
        for t in sub.getTriangleList():
            q = [(round(float(t[k]), 2), round(float(t[k + 1]), 2)) for k in (0, 2, 4)]
            if not all(k in index for k in q):
                continue
            cx, cy = sum(a for a, _ in q) / 3, sum(b for _, b in q) / 3
            ok = all(mm[min(self.h - 1, int(round(y))), min(self.w - 1, int(round(x)))]
                     for x, y in [(cx, cy)] + [((cx + a) / 2, (cy + b) / 2) for a, b in q])
            if ok:
                tris.append([index[k] for k in q])
        tris = np.array(tris, np.int32)
        # poids : gaussienne de la distance à chaque os autorisé, avec contraintes de région
        Wt = np.zeros((len(pts), len(OS)))
        for name in allowed:
            i = OI[name]
            _, a, b = OS[i]
            d = _seg_dist(pts.astype(float), REST[a], REST[b])
            s = 22.0 if name != "tronc" else 40.0
            Wt[:, i] = np.exp(-(d / s) ** 2) + 1e-6
        x, y = pts[:, 0], pts[:, 1]
        if z == 0:
            jambes = y > 470
            gauche = x < 141
            for name in ("cuisse_g", "tibia_g", "pied_g"):
                Wt[(y > 455) & ~gauche, OI[name]] = 0
            for name in ("cuisse_d", "tibia_d", "pied_d"):
                Wt[(y > 455) & gauche, OI[name]] = 0
            Wt[y < 400, OI["cuisse_g"]] = Wt[y < 400, OI["cuisse_d"]] = 0
            Wt[jambes, OI["tronc"]] *= np.exp(-((y[jambes] - 470) / 25) ** 2)
            Wt[y > 175, OI["tete"]] = 0
            Wt[y < 140, OI["tronc"]] = 0
        else:
            Wt[:, OI["tronc"]] *= np.exp(-(np.maximum(0, y - 205) / 18) ** 2)    # épaule seulement
        Wt /= Wt.sum(1, keepdims=True)
        # lissage des poids sur le maillage (diffusion) : pas de rupture entre sommets voisins
        n = len(pts)
        A = np.zeros((n, n), np.float32) if n < 6000 else None
        if A is not None and len(tris):
            for i, j in ((0, 1), (1, 2), (2, 0)):
                A[tris[:, i], tris[:, j]] = 1
                A[tris[:, j], tris[:, i]] = 1
            deg = A.sum(1, keepdims=True) + 1e-9
            fixe = Wt.copy()
            for _ in range(40):
                Wt = 0.5 * Wt + 0.5 * (A @ Wt) / deg
            Wt = 0.85 * Wt + 0.15 * fixe
            Wt /= Wt.sum(1, keepdims=True)
        return pts, tris, Wt

    # -------------------------------------------------------------------------------------------- poses
    def pose_depuis(self, P, lacet=25.0, ref=None):
        """Positions 2D des articulations : directions des os prises dans le mocap projeté, longueurs du dessin."""
        th = math.radians(lacet)
        P = P * np.array([-1.0, 1.0, 1.0])                         # les données converties sont en miroir
        Lv = P[J["LeftUpLeg"]] - P[J["RightUpLeg"]]
        Lv = np.array([Lv[0], Lv[1], 0.0]) if self.gauche is None else self.gauche
        Lv /= np.linalg.norm(Lv)
        Fv = np.cross(Lv, [0, 0, 1.0])
        ax = Lv * math.cos(th) + Fv * math.sin(th)                  # axe horizontal de l'écran

        def proj(v):
            return np.array([float(v @ ax), -float(v[2])])
        Q = {k: proj(P[J[v]]) for k, v in MOCAP.items()}
        R = {k: np.array(v, float) for k, v in REST.items()}
        out = {"bassin": R["bassin"].copy()}
        if ref is not None:                                         # déplacement du bassin (échelle du dessin)
            out["bassin"] += (Q["bassin"] - ref) * 510.0 * np.array([1.0, 0.6])   # 893 px ≈ 1,75 m

        def suit(parent, child):
            d = Q[child] - Q[parent]
            n = np.linalg.norm(d) + 1e-9
            L = np.linalg.norm(R[child] - R[parent])
            out[child] = out[parent] + d / n * L

        def rigide(parent, child, base_a, base_b):
            """child accroché à parent par un décalage du repos qui tourne avec l'os (base_a → base_b)."""
            a0 = R[base_b] - R[base_a]
            a1 = out[base_b] - out[base_a]
            ang = math.atan2(a1[1], a1[0]) - math.atan2(a0[1], a0[0])
            off = R[child] - R[parent]
            c, s = math.cos(ang), math.sin(ang)
            out[child] = out[parent] + np.array([c * off[0] - s * off[1], s * off[0] + c * off[1]])
        suit("bassin", "cou")
        suit("cou", "tete")
        for sd in ("g", "d"):
            rigide("cou", f"epaule_{sd}", "bassin", "cou")
            rigide("bassin", f"hanche_{sd}", "bassin", "cou")
            for a, b in ((f"epaule_{sd}", f"coude_{sd}"), (f"coude_{sd}", f"poignet_{sd}"), (f"poignet_{sd}", f"main_{sd}"),
                         (f"hanche_{sd}", f"genou_{sd}"), (f"genou_{sd}", f"cheville_{sd}"),
                         (f"cheville_{sd}", f"orteil_{sd}")):
                suit(a, b)
        return out

    def _transforms(self, pose):
        T = []
        for _, a, b in OS:
            a0, b0 = np.array(REST[a], float), np.array(REST[b], float)
            a1, b1 = pose[a], pose[b]
            ang = math.atan2(*(b1 - a1)[::-1]) - math.atan2(*(b0 - a0)[::-1])
            c, s = math.cos(ang), math.sin(ang)
            Rm = np.array([[c, -s], [s, c]])
            T.append((Rm, a1 - Rm @ a0))
        return T

    def draw(self, c, pose):
        T = self._transforms(pose)
        paint = skia.Paint(AntiAlias=True)
        paint.setShader(self.image.makeShader(skia.TileMode.kDecal, skia.TileMode.kDecal,
                                              skia.SamplingOptions(skia.FilterMode.kLinear)))
        for k in range(len(self.parts)):                            # jambes, corps, puis les deux bras par-dessus
            pts, tris, Wt = self.parts[k]
            V = np.zeros_like(pts, dtype=np.float64)
            for i, (Rm, tv) in enumerate(T):
                w = Wt[:, i]
                if w.max() < 1e-4:
                    continue
                V += w[:, None] * (pts @ Rm.T + tv)
            pos = [skia.Point(float(x), float(y)) for x, y in V]
            tex = [skia.Point(float(x), float(y)) for x, y in pts]
            v = skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode, pos, tex, None, tris.flatten().tolist())
            c.drawVertices(v, paint, skia.BlendMode.kModulate)


def test(out, mouvement="marche_neutre", n=8):
    """Planche : le dessin animé par le mouvement, avec le squelette en surimpression."""
    pe = Personnage()
    mv = Mouvement(mouvement)
    surf = skia.Surface(260 * n, 920)
    c = surf.getCanvas()
    c.clear(skia.Color(150, 210, 140))
    P0 = mv.P[30]
    L0 = P0[J["LeftUpLeg"]] - P0[J["RightUpLeg"]]
    pe.gauche = np.array([L0[0], L0[1], 0.0])
    for i in range(n):
        P = mv.at((30 + i * (mv.n - 31) / n) / 30, loop=False)
        pose = pe.pose_depuis(P)
        c.save()
        c.translate(260 * i, 10)
        pe.draw(c, pose)
        for _, a, b in OS:
            c.drawLine(*pose[a], *pose[b], skia.Paint(Color=skia.Color(255, 0, 0, 150), StrokeWidth=2))
        c.restore()
    cv2.imwrite(out, cv2.cvtColor(surf.makeImageSnapshot().toarray(), cv2.COLOR_BGRA2BGR))


def video(out, W=1080, H=1920, FPS=30):
    """Démo : il traverse le décor en marchant, puis montre du doigt (mouvements CMU réels)."""
    import subprocess
    import tempfile
    from films import montage_ia as MI
    from films.marionnettes.photographe.demo import decor
    pe = Personnage()
    bg = decor()
    plans = [("marche_neutre", 30, 150, True), ("montrer_du_doigt", 60, 300, False)]
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    n = 0
    for nom, f0, f1, deplace in plans:
        mv = Mouvement(nom)
        P0 = mv.P[f0] * np.array([-1.0, 1.0, 1.0])
        L0 = P0[J["LeftUpLeg"]] - P0[J["RightUpLeg"]]
        pe.gauche = np.array([L0[0], L0[1], 0.0])
        th = math.radians(25.0)
        Lv = pe.gauche / np.linalg.norm(pe.gauche)
        ax = Lv * math.cos(th) + np.cross(Lv, [0, 0, 1.0]) * math.sin(th)
        ref = np.array([float(P0[0] @ ax), -float(P0[0][2])])
        for f in range(f0, min(f1, mv.n)):
            pose = pe.pose_depuis(mv.P[f], ref=ref)
            if not deplace:
                pose = {k: v - np.array([pose["bassin"][0] - REST["bassin"][0], 0]) for k, v in pose.items()}
            c = surf.getCanvas()
            c.drawImage(bg, 0, 0)
            c.save()
            sc = 0.8 if deplace else 1.18
            x0 = -60 if deplace else 330
            c.translate(x0, 480 + (893 * (1.18 - sc)) if deplace else 480)
            c.scale(sc, sc)
            sh = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 55))
            bx = pose["bassin"][0]
            c.drawOval(skia.Rect(bx - 150, 860, bx + 150, 900), sh)
            pe.draw(c, pose)
            c.restore()
            ff.stdin.write(surf.makeImageSnapshot().tobytes())
            n += 1
    ff.stdin.close()
    ff.wait()
    dur = n / FPS
    MI.soundtrack(f"{tmp}/a.wav", np.zeros(int(dur * MI.SR)) + 1e-4, dur)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK", out, f"{dur:.1f} s")
