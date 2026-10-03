"""Épisode 18, version « scanner » : même moteur que l'épisode 17 (recadrages automatiques, 6 transitions), avec les
images, la voix et les événements d'interface de cet épisode.

    python -m films.episodes.ep18_present.scanner_ep18 output/ep18_scanner.mp4
"""
import os
import sys

from films.episodes.ep17_sucre import scanner_ep17 as S
from films.styles.test_scanner import BLANC, ORANGE

HERE = os.path.dirname(os.path.abspath(__file__))

# (phrase ou (phrase, décalage), image, zoom début → fin, point visé, événements) — coordonnées écran 1080 × 1920
PLANS = [
    (0, "01", (1.0, 1.12), (626, 953), [
        ("lock", 0.5, (420, 750, 830, 1160), "SUJET // TOI"),
    ]),
    (1, "02", (1.0, 1.1), (538, 990), [
        ("lock", 0.2, (208, 187, 871, 1580), "TEMPS PRÉSENT"),
        ("tag", 0.6, (538, 1813, 22, 40), "TOI", -1),
        ("texte", 1.6, (90, 300), "STATUT : INTROUVABLE", 32, ORANGE),
    ]),
    (3, "03", (1.0, 1.2), (861, 936), [
        ("tag", 0.3, (861, 936, 24, 24), "RÉTINE", -1),
        ("texte", 1.2, (90, 300), "LUMIÈRE → ÉLECTRICITÉ", 32, ORANGE),
    ]),
    (4, "04", (1.0, 1.15), (600, 900), [
        ("compteur", 0.0, 1.6, (80, 300), 0, 86_000_000_000, "", "NEURONES"),
        ("tag", 0.6, (319, 1494, 30, 60), "TOI", 1),
    ]),
    (5, "05", (1.0, 1.4), (484, 1038), [
        ("texte", 0.2, (90, 300), "VITESSE DU SIGNAL ≈ 100 m/s", 30, BLANC),
    ]),
    (6, "06", (1.0, 1.25), (818, 840), [
        ("tag", 0.1, (818, 840, 20, 20), "ENTRÉE DU SIGNAL", -1),
        ("compteur", 0.3, 1.2, (80, 300), 0, 100, " ms", "RETARD"),
    ]),
    (7, "07", (1.0, 1.15), (561, 961), [
        ("lock", 0.2, (382, 748, 736, 1184), "IMAGE REÇUE // −0,1 s"),
    ]),
    (9, "06", (1.3, 1.5), (520, 700), [
        ("texte", 0.2, (90, 300), "ALERTE", 40, ORANGE),
    ]),
    (10, "08", (1.0, 1.2), (620, 912), [
        ("tag", 0.2, (620, 912, 26, 26), "SIGNAL 1 : NEZ", -1),
    ]),
    ((10, 0.9), "09", (1.0, 1.15), (416, 1329), [
        ("tag", 0.1, (416, 1329, 60, 40), "SIGNAL 2 : PIED", 1),
        ("texte", 1.3, (90, 300), "ARRIVÉE SIMULTANÉE ?", 32, ORANGE),
    ]),
    (12, "10", (1.0, 1.1), (520, 900), [
        ("tag", 0.2, (455, 443, 22, 22), "NEZ → CERVEAU : ~20 cm", 1),
        ("tag", 1.2, (407, 1629, 40, 30), "PIED → CERVEAU : ~1,6 m", 1),
    ]),
    (13, "11", (1.0, 1.2), (557, 903), [
        ("lock", 0.2, (237, 583, 877, 1223), "SYNCHRONISATION"),
        ("texte", 1.4, (90, 300), "ATTENTE DU SIGNAL LE PLUS LENT", 28, ORANGE),
    ]),
    (15, "12", (1.0, 1.25), (687, 1077), [
        ("lock", 0.1, (592, 982, 782, 1172), "IMAGE RETOUCHÉE"),
    ]),
    (16, "13", (1.0, 1.3), (566, 942), [
        ("tag", 0.2, (566, 942, 60, 60), "ŒIL", 1),
        ("compteur", 1.4, 1.2, (80, 300), 0, 3, " / s", "SAUTS DE L'ŒIL"),
    ]),
    (18, "14", (1.0, 1.15), (474, 1145), [
        ("texte", 0.3, (90, 300), "SIGNAL VISUEL : COUPÉ", 34, ORANGE),
    ]),
    (19, "15", (1.0, 1.15), (730, 910), [
        ("lock", 0.2, (658, 709, 803, 1111), "TROU DÉTECTÉ"),
        ("texte", 1.6, (90, 300), "REMPLISSAGE AUTOMATIQUE", 32, ORANGE),
    ]),
    (21, "16", (1.0, 1.12), (540, 900), [
        ("tag", 0.2, (465, 1058, 40, 140), "OBSERVATEUR", -1),
        ("texte", 1.4, (90, 300), "DISTANCE = TEMPS", 36, ORANGE),
    ]),
    (22, "17", (1.0, 1.15), (542, 864), [
        ("lock", 0.2, (300, 622, 784, 1106), "LUNE // −1,3 s"),
    ]),
    (23, "18", (1.0, 1.15), (600, 900), [
        ("tag", 0.1, (857, 1421, 50, 50), "TERRE", -1),
        ("texte", 0.5, (90, 300), "LUMIÈRE DU SOLEIL : −8 min 20 s", 30, ORANGE),
    ]),
    (24, "19", (1.0, 1.3), (402, 414), [
        ("tag", 0.4, (402, 414, 26, 26), "BÉTELGEUSE // ~600 a.-l.", 1),
    ]),
    (25, "20", (1.0, 1.2), (542, 970), [
        ("lock", 0.1, (342, 770, 742, 1170), "STATUT : INCONNU"),
    ]),
    (26, "21", (1.0, 1.15), (700, 870), [
        ("tag", 0.2, (624, 908, 20, 20), "LUMIÈRE EN ROUTE", -1),
        ("tag", 1.0, (837, 835, 32, 32), "TERRE", -1),
    ]),
    (27, "22", (1.0, 1.12), (540, 1100), [
        ("tag", 0.6, (358, 1155, 100, 330), "TOI", -1),
        ("tag", 2.2, (736, 1135, 130, 330), "TOI // −0,1 s", 1),
    ]),
]

S.IMG = os.path.join(HERE, "images")
S.VOIX = os.path.join(HERE, "audio", "voix.mp3")
S.VOIX2 = os.path.join(HERE, "audio", "voix_serree.wav")
S.SEGS = os.path.join(HERE, "audio", "voix.json")
S.PLANS = PLANS
S.ACCROCHE = ("TU N'AS JAMAIS VU", "LE PRÉSENT")

if __name__ == "__main__":
    S.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep18_scanner.mp4")
