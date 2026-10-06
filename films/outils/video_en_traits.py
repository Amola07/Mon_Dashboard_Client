"""Un clip vidéo au trait (généré par IA, caméra fixe, fond blanc) → une suite d'images en traits, à 24 images/s.

    python -m films.outils.video_en_traits clip.mp4 nom [--debut 0.4] [--fin 3.2]
    → films/animations/nom.json  (même format que les feuilles d'animation, avec "fps": 24)

Le personnage garde ses déplacements dans le cadre (le clip est filmé caméra fixe) ; l'échelle est la hauteur du
personnage sur la première image, l'origine est le bas du cadre au centre. Dans un tableau :
    from films.outils.video_en_traits import plan
    faisceau(c, plan("p04_marcher", t - t0, x=540, pied=1330, haut=560), 1.0, VERT_PALE, 1.2)
"""
import argparse
import json
import os
import subprocess

import cv2
import numpy as np

from films.outils.feuille_animation import DOSSIER, animation
from films.outils.image_en_traits import amincir, ordonner, simplifier, suivre

FPS = 24


def images_du_clip(chemin, debut=0.0, fin=None, hauteur=720):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(debut)] + (["-to", str(fin)] if fin else []) + \
          ["-i", chemin, "-vf", f"fps={FPS},scale=-2:{hauteur},format=gray", "-f", "rawvideo", "-"]
    brut = subprocess.run(cmd, capture_output=True, check=True).stdout
    w, h = (int(v) for v in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                             "stream=width,height", "-of", "csv=p=0", chemin],
                                            capture_output=True, text=True).stdout.strip().split(","))
    larg = int(round(w * hauteur / h / 2)) * 2
    return np.frombuffer(brut, np.uint8).reshape(-1, hauteur, larg)


def en_traits(img):
    """Seuil fixe (le même pour toutes les images : pas de scintillement), nettoyage, squelette, lignes."""
    noir = cv2.GaussianBlur(img, (3, 3), 0) < 140
    noir = cv2.morphologyEx(noir.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(noir, 8)
    garde = np.zeros(n, bool)
    garde[1:] = st[1:, cv2.CC_STAT_AREA] >= 20
    return ordonner(simplifier(suivre(amincir(garde[lab])), eps=1.1))


def convertir(chemin, debut=0.0, fin=None):
    imgs = images_du_clip(chemin, debut, fin)
    H, L = imgs.shape[1:]
    images = [[[(x - L / 2, y - H) for x, y in l] for l in en_traits(im)] for im in imgs]
    ys = [y for l in images[0] for _, y in l]
    hauteur = max(ys) - min(ys)
    return {"fps": FPS, "largeur_case": 0.0,
            "images": [[[(round(x / hauteur, 4), round(y / hauteur, 4)) for x, y in l] for l in im] for im in images]}


def plan(nom, u, x, pied, haut, miroir=False):
    """L'image du plan au temps u (secondes depuis son début), tenue sur la dernière à la fin : jamais de boucle."""
    a = animation(nom)
    k = min(len(a["images"]) - 1, max(0, int(u * a.get("fps", FPS))))
    sx = -1 if miroir else 1
    return [[(x + sx * px * haut, pied + py * haut) for px, py in l] for l in a["images"][k]]


def duree(nom):
    a = animation(nom)
    return len(a["images"]) / a.get("fps", FPS)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("clip")
    p.add_argument("nom")
    p.add_argument("--debut", type=float, default=0.0)
    p.add_argument("--fin", type=float, default=None)
    a = p.parse_args()
    d = convertir(a.clip, a.debut, a.fin)
    os.makedirs(DOSSIER, exist_ok=True)
    json.dump(d, open(os.path.join(DOSSIER, a.nom + ".json"), "w"))
    print(f"{a.nom} : {len(d['images'])} images ({len(d['images']) / FPS:.2f} s)")


if __name__ == "__main__":
    main()
