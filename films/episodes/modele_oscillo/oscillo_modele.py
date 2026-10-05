"""MODÈLE d'épisode oscilloscope — à copier pour commencer un nouvel épisode.

Il réutilise la voix de l'épisode 23 (ses 4 premières phrases seulement) pour pouvoir tester tout de suite :
    python -m films.outils.apercu films.episodes.modele_oscillo.oscillo_modele 0 2 4.5 7 8.5   (images fixes)
    python -m films.episodes.modele_oscillo.oscillo_modele output/modele.mp4                    (vidéo, ≈ 11 s)

Règles du jeu :
  - l'écran fait 1080 × 1920 ; x va de gauche à droite, y de HAUT en BAS (y = 0 tout en haut) ;
  - zone utile : y ≈ 280 → 1500 (au-dessus : interface TikTok ; vers 1650 : sous-titres automatiques) ;
  - s(i) = début de la phrase i dans la voix (en secondes), e(i) = sa fin ; i commence à 0 ;
  - chaque tableau est une fonction (c, t) appelée 30 fois par seconde : elle redessine TOUT à l'instant t.
"""
import math
import os
import sys

from films.episodes.ep21_ascenseur import oscillo_ep21 as M
from films.episodes.ep21_ascenseur.oscillo_ep21 import (AMBRE, VERT, VERT_PALE, W, bonhomme, cercle_pts, ease, ecrit,
                                                         faisceau, fleche, rect_pts, titres, trace)
from films.styles import oscillo_son as Z

HERE = os.path.dirname(os.path.abspath(__file__))
M.VOIX = os.path.join(HERE, "..", "ep23_voiture_eau", "audio", "voix.mp3")   # ← mets ta voix ici
M.SEGS = os.path.join(HERE, "audio", "voix.json")                           # ← et son minutage ici
s, e = M.s, M.e


def tab_un(c, t):
    """Phrases 0 et 1 : un titre, une boîte, un bonhomme, une flèche, un compteur."""
    # 1) TEXTE affiché dès l'image 0 (t0 = -1 → déjà là), vitesse=0 → apparaît d'un coup
    ecrit(c, t, -1.0, "MON TITRE", W / 2, 330, 84, AMBRE, True, 2.0, vitesse=0.0)
    # 2) TRAIT tracé au faisceau : commence à 0,2 s, dure 0,6 s
    trace(c, t, 0.2, 0.6, [rect_pts(240, 700, 840, 1300)], VERT_PALE, 1.3)
    # 3) BONHOMME : apparaît au début de la phrase 1, puis passe de « debout » à « flotte » en 0,5 s
    k = ease((t - s(1) - 0.3) / 0.5)
    trace(c, t, s(1), 0.4, bonhomme(540, 1290, 3.0, "debout", "flotte", k), VERT_PALE, 1.2)
    # 4) FLÈCHE ambre, 1 s après le début de la phrase 1
    trace(c, t, s(1) + 1.0, 0.3, fleche(900, 1200, 900, 800), AMBRE, 1.5)
    # 5) COMPTEUR qui monte de 0 à 200 pendant 2 s (vitesse=0 → pas d'effet de frappe)
    v = 200 * ease((t - 0.5) / 2.0)
    ecrit(c, t, 0.5, f"{v:3.0f} kg", W / 2, 560, 90, AMBRE, True, 1.6, vitesse=0.0)


def tab_deux(c, t):
    """Phrases 2 et 3 : un titre par phrase, un cercle qui se trace, un point qui tourne."""
    titres(c, t, [(s(2), "POURQUOI ?", VERT_PALE, 70), (s(3), "LA PRESSION", AMBRE, 70)])
    trace(c, t, s(2), 0.8, [cercle_pts(540, 900, 250, 60)], VERT_PALE, 1.2)
    a = (t - s(2)) * 3                                    # angle qui tourne avec le temps
    faisceau(c, [cercle_pts(540 + 250 * math.cos(a), 900 + 250 * math.sin(a), 14, 16)], 1.0, AMBRE, 1.5)


def tableaux():
    # (instant de début, fonction, transition d'entrée : None, "neige", "balayage", "glitch" ou "noir")
    return [(0.0, tab_un, None), (s(2) - 0.1, tab_deux, "neige")]


def chocs():
    flashs = [s(3)]                     # flash blanc à ces instants
    secousses = [(s(3), 0.2)]           # (instant, durée) : l'image tremble
    return flashs, secousses


def effets(tabs):
    # (instant, son) — tous les sons sont dans films/styles/oscillo_son.py
    ev = [(0.0, Z.thump(0.35)), (s(1) + 1.0, Z.whoosh(0.4, 0.1)), (s(3), Z.boom(0.5, 60))]
    for t0, _, tr in tabs[1:]:          # un son par transition
        ev.append((t0, Z.neige(0.22, 0.2)))
    return ev


M.tableaux = tableaux
M.chocs = chocs
M.effets = effets

if __name__ == "__main__":
    M.render(sys.argv[1] if len(sys.argv) > 1 else "output/modele.mp4")
