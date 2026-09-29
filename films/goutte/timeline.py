"""Découpage du plan pilote de « Goutte » (18 s à 24 i/s). Partagé par la scène Blender et la bande-son."""
FPS = 24


def f(seconds):
    return int(round(seconds * FPS)) + 1


DURATION = 18.0
SHOTS = [  # (début en s, caméra) : les coupes entre plans
    (0.0, "large"),       # aube sur les dunes, une lueur tombe du ciel
    (5.0, "proche"),      # la goutte atterrit sur la crête
    (9.0, "visage"),      # elle ouvre les yeux, regarde autour d'elle
    (14.0, "contre"),     # contre-jour : le soleil se lève derrière elle
]
FALL_START = 1.6          # la goutte apparaît haut dans le ciel
LAND = 6.25               # contact avec le sable
EYES_OPEN = (7.8, 8.3)
LOOK_LEFT = (9.6, 10.3)
LOOK_RIGHT = (11.2, 11.9)
BLINK = (12.6, 12.85)
LOOK_BACK = (13.2, 13.7)
SUNRISE = (13.0, 18.0)    # élévation du soleil −2° → 5°
SQUINT = (15.6, 16.1)

# bande-son : (instant, note, intensité) ; note = degré de la gamme pentatonique
CUES = [
    (LAND, 2, 1.0),
    (EYES_OPEN[0] + 0.1, 4, 0.5),
    (LOOK_LEFT[0] + 0.2, 5, 0.35),
    (LOOK_RIGHT[0] + 0.2, 6, 0.35),
    (BLINK[0], 7, 0.3),
    (14.0, 5, 0.6), (14.5, 7, 0.6), (15.0, 9, 0.6), (15.5, 10, 0.7),
]

# texte de la voix off (enregistrée sur Kaggle avec Kokoro)
VOICE = [
    (1.0, "Ce matin-là, il tomba une seule goutte sur tout le désert."),
    (9.5, "Elle ne savait pas où elle était."),
    (14.2, "Mais elle savait une chose : le soleil allait se lever."),
]
