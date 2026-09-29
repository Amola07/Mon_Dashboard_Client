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
FALL_START = 1.6          # la goutte apparaît dans le ciel
FALL_HEIGHT = 18.0
LAND = 6.25               # contact avec le sable
EYES_OPEN = (7.8, 8.4)    # s'ouvrent lentement, puis double clignement
LOOK_LEFT = (9.6, 10.3)
SURPRISE = (9.9, 11.0)    # petite bouche en « o »
LOOK_RIGHT = (11.2, 11.9)
SMILE = (12.0, 12.5)      # un petit sourire apparaît
BLINK = (12.6, 12.85)
LOOK_BACK = (13.2, 13.7)
SUNRISE = (13.9, 18.0)    # le soleil franchit l'horizon
SQUINT = (15.2, 15.6)     # plisse les yeux dans la lumière
HOP = (16.3, 16.9)        # petit saut de joie


def fall_z(t):
    """Hauteur de la goutte pendant la chute (accélération constante)."""
    u = min(max((t - FALL_START) / (LAND - FALL_START), 0.0), 1.0)
    return FALL_HEIGHT * (1 - u * u)


# bande-son : (instant, note, intensité) ; note = degré de la gamme pentatonique
CUES = [
    (LAND, 2, 1.0),
    (EYES_OPEN[1], 4, 0.5),
    (SURPRISE[0], 7, 0.45),
    (SMILE[0], 5, 0.45), (SMILE[0] + 0.25, 7, 0.4),
    (BLINK[0], 9, 0.25),
    (14.0, 5, 0.6), (14.6, 7, 0.6), (15.2, 9, 0.6), (15.8, 10, 0.7),
    (HOP[0], 7, 0.5), (HOP[0] + 0.3, 12, 0.6),
]
