"""Le dessin d'origine, tel quel, révélé trait par trait (comme une plume qui le dessine) : aucun détail perdu.

Au lieu de remplacer le dessin par des lignes d'un pixel (squelette), on garde l'image de la planche (traits fins, épaisseurs,
boucles des cheveux, ombres) et on la découvre le long du chemin de tracé : le squelette ne sert plus qu'à donner l'ordre
et la position de la plume. À la fin du tracé, tout le dessin est là, exactement comme sur la planche.

    python -m films.examaster_tiktok.trace_raster planche.webp 3x3 output/essai_plume.mp4
"""
import math
import subprocess
import sys

import cv2
import numpy as np

from films.examaster_tiktok.couleur import convertir_case, coupures, premier_plan

W, H, FPS = 1080, 1920, 30
PAPIER = np.array([247, 251, 252], np.float32)          # BGR
ENCRE = np.array([16, 14, 14], np.float32)


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


class Case:
    """Une case de la planche : son encre (0 = papier, 1 = noir) agrandie à l'écran, et son chemin de tracé."""

    def __init__(self, img, k):
        d = convertir_case(img, np.zeros((0, 3), np.float32), 45)
        x0, y0, x1, y1 = d["bbox"]
        x0, y0, x1, y1 = max(x0 - 4, 0), max(y0 - 4, 0), min(x1 + 5, img.shape[1]), min(y1 + 5, img.shape[0])
        gris = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
        encre = np.clip((0.97 - gris) / 0.85, 0, 1)                    # le papier un peu gris de l'IA devient blanc
        fg = d.pop("masque_fg")[y0:y1, x0:x1] if "masque_fg" in d else None
        if fg is not None:
            encre *= cv2.dilate(fg.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
        self.w, self.h = int((x1 - x0) * k), int((y1 - y0) * k)
        a = cv2.resize(encre, (self.w, self.h), interpolation=cv2.INTER_LANCZOS4)
        flou = cv2.GaussianBlur(a, (0, 0), 1.2 * k / 2.7)
        self.encre = np.clip(a + 0.7 * (a - flou), 0, 1)               # un peu d'accentuation : le trait reste net
        self.lignes = [np.array([((x - x0) * k, (y - y0) * k) for x, y in l], np.float32) for l in d["lignes"] if len(l) > 1]
        self.longueurs = [float(np.linalg.norm(np.diff(l, axis=0), axis=1).sum()) for l in self.lignes]
        self.total = max(sum(self.longueurs), 1.0)
        self.epaisseur = max(6, int(round(5.5 * k)))

    def masque(self, u):
        """Ce que la plume a déjà dessiné à la fraction u du chemin ; renvoie aussi la position de la plume."""
        m = np.zeros((self.h, self.w), np.uint8)
        reste = self.total * u
        tete = None
        for l, L in zip(self.lignes, self.longueurs):
            if reste <= 0:
                break
            if reste >= L:
                cv2.polylines(m, [l.astype(np.int32)], False, 255, self.epaisseur, cv2.LINE_AA)
                reste -= L
                continue
            seg = np.linalg.norm(np.diff(l, axis=0), axis=1)
            cum = np.concatenate([[0], np.cumsum(seg)])
            i = int(np.searchsorted(cum, reste)) - 1
            f = (reste - cum[i]) / max(seg[i], 1e-6)
            tete = l[i] + (l[i + 1] - l[i]) * f
            pts = np.vstack([l[:i + 1], tete[None]])
            cv2.polylines(m, [pts.astype(np.int32)], False, 255, self.epaisseur, cv2.LINE_AA)
            break
        return cv2.GaussianBlur(m, (0, 0), 1.5).astype(np.float32) / 255, tete

    def poser(self, img, u, cx, bas, fondu=0.0, opacite=1.0):
        """Colle la case dessinée à la fraction u (et fondu = part du dessin complet ajoutée en fin de tracé)."""
        if u >= 1 and fondu >= 1:
            a, tete = self.encre, None
        else:
            m, tete = self.masque(u)
            a = self.encre * np.maximum(m, fondu)
        a = a * opacite
        x, y = int(cx - self.w / 2), int(bas - self.h)
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + self.w, W), min(y + self.h, H)
        a = a[y0 - y:y1 - y, x0 - x:x1 - x, None]
        zone = img[y0:y1, x0:x1].astype(np.float32)
        img[y0:y1, x0:x1] = (zone * (1 - a) + ENCRE * a).astype(np.uint8)
        if tete is not None and opacite >= 1:                           # la pointe de la plume
            cv2.circle(img, (int(x + tete[0]), int(y + tete[1])), 5, (40, 40, 40), -1, cv2.LINE_AA)


POSES = [(0, 0.0, 1.0), (1, 2.6, 2.4), (2, 3.6, 2.4), (3, 4.6, 2.4), (4, 5.6, 2.4), (5, 6.6, 2.4), (6, 7.6, 2.4), (7, 8.6, 2.4),
         (8, 9.6, 2.4)]
DUREE = 10.8


def rendre(chemin, grille, sortie, k=2.7):
    planche = cv2.imread(chemin)
    cols, rangs = (int(v) for v in grille.split("x"))
    fg = premier_plan(planche)
    bl, br = coupures(fg, cols, 1), coupures(fg, rangs, 0)
    cases = []
    for i in range(cols * rangs):
        r, c = divmod(i, cols)
        cases.append(Case(planche[br[r]:br[r + 1], bl[c]:bl[c + 1]], k))
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-an", sortie], stdin=subprocess.PIPE)
    fond = np.empty((H, W, 3), np.uint8)
    fond[:] = PAPIER.astype(np.uint8)
    for fr in range(int(DUREE * FPS)):
        t = fr / FPS
        i, t0, v = max([p for p in POSES if p[1] <= t], key=lambda p: p[1])
        tl = (t - t0) * v
        duree_trace = 2.0
        u = ease(tl / duree_trace)
        fondu = ease((tl - duree_trace) / 0.4)
        bob = 4 * math.sin(t * 2.2) if u >= 1 else 0
        img = fond.copy()
        rang = [p[0] for p in POSES].index(i)
        if rang > 0 and tl < 0.9:                                       # la pose précédente s'efface pendant que la nouvelle se trace
            cases[POSES[rang - 1][0]].poser(img, 1.0, 540, 1600 + bob, 1.0, 1 - ease(tl / 0.9))
        cases[i].poser(img, u, 540, 1600 + bob, fondu)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print("OK", sortie)


if __name__ == "__main__":
    rendre(sys.argv[1], sys.argv[2], sys.argv[3])
