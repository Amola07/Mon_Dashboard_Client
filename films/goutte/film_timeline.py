"""Chorégraphie du film complet « Goutte » (2 min, 24 i/s) : lieux, trajet de la goutte, expressions, lumière,
caméras et musique. Pur Python : partagé par la scène Blender (film.py) et la bande-son (render_film.py)."""
import math

FPS = 24
DURATION = 120.0


def f(seconds):
    return int(round(seconds * FPS)) + 1


# ---------------------------------------------------------------- terrain
CREST = (5.0, 7.0, 2.0)          # demi-axes de la grande dune où tout se passe ; sommet en (0, 0, 0)


def ground(x, y):
    a, b, c = CREST
    q = 1 - (x / a) ** 2 - (y / b) ** 2
    return -c + c * math.sqrt(q) if q > 0 else -c


ROCK = (3.3, 1.1)
SPROUT = (4.3, -0.6)
CLOUD = (4.3, 3.2, 5.2)
END = (3.4, -1.6)                 # la goutte de pluie finale atterrit ici


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def interp(keys, t, ease=smooth):
    """keys : [(t, valeur ou tuple)] triés ; interpolation adoucie entre deux clés."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            if isinstance(v0, tuple):
                return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return keys[-1][1]


# ---------------------------------------------------------------- trajet de la goutte (x, y au sol)
PATH = [
    (0.0, (0.0, 0.0)), (16.6, (0.0, 0.0)),
    (18.4, (2.6, 0.3)),                           # toboggan
    (19.2, (2.4, 0.3)), (20.8, (0.2, 0.1)),       # remonte en sautillant
    (21.0, (0.2, 0.1)), (22.4, (2.8, -0.2)),      # deuxième glissade, avec une vrille
    (42.5, (2.8, -0.2)), (44.0, (3.15, 0.2)),     # va se cacher dans l'ombre du caillou
    (51.0, (3.15, 0.2)), (54.5, (2.35, 1.0)),     # suit l'ombre qui tourne
    (55.8, (2.35, 1.0)), (56.4, (2.05, 0.7)),     # le caillou bascule : bond en arrière
    (59.0, (2.05, 0.7)), (64.0, (3.95, -0.6)),    # épuisée, rejoint la tache verte
    (76.0, (3.95, -0.6)), (77.2, (4.15, -0.62)),  # se blottit contre la tige
    (114.9, (4.15, -0.62)), (115.0, END),         # (invisible) : la goutte de pluie finale
]
# sauts : (début, fin, hauteur)
HOPS = [(19.3, 19.8, 0.25), (19.85, 20.3, 0.25), (20.35, 20.8, 0.22),
        (42.6, 43.2, 0.3), (43.3, 43.9, 0.3),
        (51.2, 51.9, 0.22), (52.4, 53.1, 0.22), (53.7, 54.4, 0.22),
        (55.8, 56.4, 0.35),
        (59.2, 59.9, 0.12), (60.6, 61.3, 0.1), (62.0, 62.7, 0.08)]
FALL_START, FALL_HEIGHT, LAND = 0.0, 24.0, 6.25
FINAL_FALL = (115.0, 116.6, 9.0)                 # début, contact, hauteur
# taille : rétrécit au soleil, donne son eau à la pousse, s'évapore, renaît en goutte de pluie
SIZE = [(0.0, 1.0), (34.0, 1.0), (42.0, 0.9), (57.0, 0.72), (64.0, 0.66), (76.5, 0.66), (83.0, 0.28),
        (86.0, 0.28), (88.0, 0.0), (114.9, 0.0), (115.0, 1.0)]
SPIN = [(0.0, 0.0), (21.0, 0.0), (22.4, 2 * math.pi), (40, 2 * math.pi)]


def hop_z(t):
    for t0, t1, h in HOPS:
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            return 4 * h * u * (1 - u)
    return 0.0


def drop_state(t):
    """Position (x, y, z), écrasement (sx, sy, sz) et rotation z de la goutte à l'instant t."""
    x, y = interp(PATH, t, ease=lambda u: u if 17.0 < t < 18.4 or 21 < t < 22.4 else smooth(u))
    z = ground(x, y) + hop_z(t)
    if t < LAND:                                  # chute depuis le ciel
        u = min(max((t - FALL_START) / (LAND - FALL_START), 0), 1)
        z = FALL_HEIGHT * (1 - u * u)
    if FINAL_FALL[0] <= t < FINAL_FALL[1]:
        u = (t - FINAL_FALL[0]) / (FINAL_FALL[1] - FINAL_FALL[0])
        z = ground(*END) + FINAL_FALL[2] * (1 - u * u)
    size = interp(SIZE, t)
    sx = sz = 1.0
    falling = t < LAND - 0.05 or FINAL_FALL[0] <= t < FINAL_FALL[1] - 0.05
    if falling:
        sx, sz = 0.85, 1.25
    for land in (LAND, FINAL_FALL[1]) + tuple(h[1] for h in HOPS):
        dt = t - land
        if 0 <= dt < 0.6:                          # écrasement à chaque atterrissage, puis rebond amorti
            k = math.exp(-dt * 7) * math.cos(dt * 22)
            sx, sz = 1 + 0.28 * k, 1 - 0.36 * k
    for t0, t1, _ in HOPS:                        # étirement en l'air
        if t0 < t < t1:
            sx, sz = 0.92, 1.12
    if 44.5 < t < 50.5:                           # se tasse pour tenir dans la petite ombre
        k = smooth((t - 44.5) / 0.4) * (1 - smooth((t - 50.1) / 0.4))
        sx, sz = sx * (1 + 0.18 * k), sz * (1 - 0.3 * k)
    if 8.5 < t < 100 and not falling:              # respiration
        b = 0.015 * math.sin(2 * math.pi * t / 1.5)
        sx, sz = sx * (1 + b), sz * (1 - b)
    rz = interp(SPIN, t)
    if 45 < t < 50:                                # se tortille
        rz += 0.25 * math.sin(2 * math.pi * (t - 45) * 1.6)
    look = interp(LOOKS, t)
    return (x, y, z), (sx * size, sx * size, sz * size), rz + look[2]


# ---------------------------------------------------------------- expressions
OPEN, HALF, CLOSED = -70.0, 40.0, 92.0          # angle des paupières (degrés)
LIDS = [(0, CLOSED), (7.8, CLOSED), (8.15, HALF), (8.4, OPEN), (8.7, OPEN), (8.8, CLOSED), (8.9, OPEN),
        (9.02, CLOSED), (9.12, OPEN), (12.6, OPEN), (12.72, CLOSED), (12.85, OPEN),
        (18.3, OPEN), (18.45, 55), (19.3, 55), (19.5, OPEN),            # yeux plissés de rire
        (22.3, OPEN), (22.5, 55), (24.0, 55), (24.3, OPEN),
        (29.0, OPEN), (29.4, HALF), (33.0, HALF), (33.4, OPEN),         # ébloui
        (47.0, OPEN), (47.1, CLOSED), (47.2, OPEN),
        (56.3, OPEN), (56.35, -85), (57.2, -85), (57.5, OPEN),          # yeux écarquillés
        (58.0, OPEN), (58.5, 20), (63.5, 20), (64.0, OPEN),             # fatiguée
        (72.0, OPEN), (72.3, 25), (74.5, 25), (75.0, OPEN),             # hésite
        (75.2, OPEN), (75.5, 50), (76.5, 50), (76.8, OPEN),             # sourire tendre
        (86.5, OPEN), (87.2, 60), (88, 60),
        (115.0, CLOSED), (117.4, CLOSED), (117.8, HALF), (118.1, OPEN)]
WINK = [(84.3, OPEN), (84.55, CLOSED), (84.95, CLOSED), (85.2, OPEN)]   # clin d'œil (œil gauche)
# bouches : (instant, « o », sourire) ; sourire négatif = triste
MOUTH = [(0, 0.0, 0.0), (0.2, 1.0, 0.0), (5.5, 1.0, 0.0), (6.3, 0.0, 0.0),
         (9.9, 0.0, 0.0), (10.1, 1.0, 0.0), (11.0, 1.0, 0.0), (11.2, 0.0, 0.0), (12.0, 0.0, 0.0), (12.5, 0.0, 0.7),
         (17.5, 0.0, 0.7), (18.4, 0.0, 1.3), (24.0, 0.0, 1.3), (25.0, 0.0, 0.8),
         (36.0, 0.0, 0.8), (36.8, 0.0, 0.0), (38.4, 0.0, 0.0), (38.6, 0.7, 0.0), (39.4, 0.7, 0.0), (39.6, 0.0, 0.0),
         (45.0, 0.0, 0.0), (45.3, 0.8, 0.0), (49.8, 0.8, 0.0), (50.0, 0.0, 0.0),
         (55.9, 0.0, 0.0), (56.1, 1.2, 0.0), (57.5, 1.2, 0.0), (57.8, 0.0, -0.5),
         (66.0, 0.0, -0.5), (70.0, 0.0, -0.6), (74.5, 0.0, -0.6), (75.2, 0.0, 0.8), (86.0, 0.0, 0.8),
         (115.0, 0.0, 0.0), (118.3, 0.0, 0.0), (118.8, 0.0, 1.0)]
# regards : (dx pupilles, dz pupilles, rotation du corps)
LOOKS = [(0, (0.0, 0.0, 0.0)), (9.6, (0.0, 0.0, 0.0)), (10.3, (-0.045, 0.0, 0.18)), (11.2, (-0.045, 0.0, 0.18)),
         (11.9, (0.045, 0.0, -0.18)), (13.2, (0.045, 0.0, -0.18)), (13.7, (0.0, 0.0, 0.0)),
         (36.8, (0.0, 0.0, 0.0)), (37.2, (0.0, 0.035, 0.0)), (38.3, (0.0, 0.035, 0.0)), (38.6, (0.0, 0.0, 0.0)),
         (57.5, (0.0, 0.0, 0.0)), (58.2, (0.04, 0.0, -0.3)), (59.0, (0.04, 0.0, -0.3)), (59.5, (0.0, 0.0, 0.0)),
         (70.0, (0.0, 0.0, 0.0)), (70.6, (0.03, 0.0, -0.4)), (71.6, (0.03, 0.0, -0.4)),      # la pousse
         (72.0, (0.0, 0.04, 0.0)), (73.0, (0.0, 0.04, 0.0)),                                  # le soleil
         (73.4, (0.0, -0.04, 0.0)), (74.4, (0.0, -0.04, 0.0)),                                # elle-même
         (74.8, (0.03, 0.0, -0.4)), (77.0, (0.03, 0.0, -0.4)), (77.5, (0.0, 0.0, 0.0))]
HAND = [(0, 0.0), (29.3, 0.0), (29.7, 1.0), (33.0, 1.0), (33.4, 0.0)]      # bras en visière
WISPS = [(36.5, 39.0), (39.5, 42.0), (47.0, 50.0), (58.0, 61.0)]            # vapeur au-dessus de la tête
SOUL = (86.0, 92.5)                                                          # la volute brillante qui monte


def soul_pos(t):
    """Position de la volute brillante (l'« âme » de la goutte) qui monte vers le nuage."""
    sx, sy = 4.15, -0.62
    g = ground(sx, sy)
    if t <= SOUL[0]:
        return (sx, sy, g + 0.1)
    u = smooth((t - SOUL[0]) / (SOUL[1] - SOUL[0]))
    return (sx + (CLOUD[0] - sx) * u, sy + (CLOUD[1] - sy) * u, g + 0.3 + (CLOUD[2] - 1.0 - g) * u)

# ---------------------------------------------------------------- pousse, nuage, pluie, fleurs
SPROUT_ALIVE = [(0, 0.0), (78.0, 0.0), (84.0, 0.75), (106.0, 0.75), (108.0, 1.0)]
CLOUD_GROW = [(0, 0.0), (91.5, 0.0), (98.0, 1.0)]
CLOUD_FROWN = [(0, 0.0), (99.0, 0.0), (100.2, 1.0), (104.0, 1.0), (105.0, 0.0)]
CLOUD_WISPS = [((1.0, -2.5), 90.0), ((7.0, 1.0), 90.6), ((-1.0, 2.0), 91.2), ((5.5, -3.0), 91.8)]
RAIN = (100.8, 113.5)
FLOWERS = (106.0, 113.5)
BIG_FLOWER = (107.0, 113.0)

# ---------------------------------------------------------------- lumière : (t, élévation, rotation, énergie, étoiles, clarté du ciel)
SKY = [(0, -4.0, 0, 0.0, 1.0, 0.2), (6, -2.5, 0, 0.0, 0.8, 0.35), (16, 1.5, 0, 1.5, 0.2, 0.7), (28, 5, 0, 3.5, 0, 1.0),
       (36, 25, 15, 4.5, 0, 1.0), (42, 48, 20, 5.0, 0, 1.0), (50, 50, 20, 5.0, 0, 1.0), (56, 50, 80, 5.0, 0, 1.0),
       (65, 35, 110, 4.5, 0, 1.0), (80, 18, 130, 4.0, 0, 1.0), (90, 12, 140, 3.5, 0, 0.9),
       (98, 10, 140, 0.7, 0, 0.45), (113, 8, 140, 0.7, 0, 0.45), (116, 6, 150, 3.2, 0, 0.8), (120, 3, 150, 2.4, 0.1, 0.7)]

# ---------------------------------------------------------------- plans : (début, nom, objectif, ouverture, caméra, visée)
# caméra et visée : ("goutte", dx, dy, dz) relatif à la goutte, ou ("fixe", x, y, z)
SHOTS = [
    (0.0, "accroche", 85, 2.0, ("goutte", 0.1, -3.4, 0.15), ("goutte", 0, 0, 0.55)),
    (2.0, "chute", 30, 8.0, ("fixe", 0.6, -14, 1.2), ("goutte", 0, 0, 0.5)),
    (6.0, "atterrissage", 60, 1.8, ("fixe", 0.3, -4.4, 0.5), ("fixe", 0, 0, 0.6)),
    (9.0, "découverte", 85, 1.6, ("goutte", 0.1, -3.4, 0.35), ("goutte", 0, 0, 0.55)),
    (16.0, "toboggan", 40, 4.0, ("fixe", 1.4, -6.5, 0.2), ("goutte", 0, 0, 0.4)),
    (28.0, "soleil", 50, 1.8, ("goutte", -0.4, -2.8, 0.15), ("goutte", 0, 0.5, 0.7)),
    (36.0, "vapeur", 70, 2.0, ("goutte", 0.1, -2.8, 0.6), ("goutte", 0, 0, 0.85)),
    (42.0, "caillou", 45, 2.8, ("fixe", 2.4, -3.6, -0.05), ("fixe", 3.1, 0.6, -0.1)),
    (50.0, "ombre", 55, 2.2, ("goutte", 0.6, -3.0, 0.3), ("goutte", 0, 0, 0.45)),
    (57.0, "épuisée", 35, 4.0, ("fixe", 2.4, -4.8, 0.1), ("goutte", 0, 0, 0.3)),
    (65.0, "pousse", 55, 1.8, ("fixe", 5.9, -1.9, -0.72), ("fixe", 4.25, -0.6, -0.72)),
    (70.0, "hésitation", 85, 1.6, ("goutte", 0.35, -2.6, 0.2), ("goutte", 0, 0, 0.35)),
    (76.0, "don", 60, 1.8, ("fixe", 4.5, -3.0, -0.75), ("fixe", 4.2, -0.6, -0.7)),
    (83.0, "adieu", 85, 1.6, ("fixe", 4.75, -2.1, -0.72), ("fixe", 4.15, -0.62, -0.82)),
    (90.0, "nuage", 24, 5.0, ("fixe", 4.8, -3.2, -0.8), ("fixe", 4.3, 3.2, 5.0)),
    (98.0, "pluie", 26, 6.0, ("fixe", 2.4, -7.0, 0.2), ("fixe", 4.2, 2.0, 2.8)),
    (106.0, "fleurs", 30, 4.0, ("fixe", 1.2, -3.6, 0.5), ("fixe", 4.3, -0.4, -0.3)),
    (114.0, "retour", 50, 2.0, ("fixe", 3.7, -4.6, -0.15), ("fixe", 3.4, -1.6, -0.1)),
]
CAMERA_MOVES = {  # petits mouvements dans les plans fixes : décalage final de la caméra (dx, dy, dz)
    "chute": (0, 1.5, -0.2), "toboggan": (0.8, 0.3, 0.0), "caillou": (0.2, 0.3, 0), "épuisée": (1.0, 0.4, 0),
    "pousse": (0.1, 0.5, 0.05), "nuage": (0, 0.6, 0.3), "pluie": (0.6, 2.5, 0), "fleurs": (1.8, 0.6, 0.2),
    "retour": (0, 0.5, 0), "adieu": (0.2, -0.6, 1.4),
}

# ---------------------------------------------------------------- musique : sections (début, fin, tonalité, suite, timbre, niveau de nappe)
MUSIC = [(0, 16, "ré", 0, "cristal", 0.5), (16, 36, "ré", 1, "kalimba", 0.5), (36, 65, "sol", 4, "goutte", 0.4),
         (65, 90, "la", 2, "piano doux", 0.65), (90, 120, "ré", 0, "cristal", 0.7)]
ARPEGGIO = [(16.5, 28.0, 0.25), (36.0, 64.0, 0.4), (98.0, 114.0, 0.2)]   # notes régulières (début, fin, écart)
CUES = [(LAND, 2, 1.0), (8.4, 4, 0.5), (10.1, 7, 0.45), (12.5, 5, 0.45), (12.75, 7, 0.4),
        (18.4, 9, 0.6), (22.4, 10, 0.6), (29.7, 7, 0.5), (38.6, 3, 0.5), (56.3, 1, 1.0),
        (75.2, 5, 0.5), (77.3, 7, 0.4), (79, 9, 0.45), (81, 10, 0.45), (84.6, 12, 0.5),
        (88.0, 7, 0.5), (88.5, 9, 0.5), (89.0, 12, 0.6), (98.0, 5, 0.6), (100.8, 9, 0.7),
        (107, 7, 0.5), (108, 9, 0.5), (109, 10, 0.5), (110, 12, 0.6), (111, 14, 0.7),
        (116.6, 2, 1.0), (118.1, 4, 0.5), (118.8, 7, 0.5)]
# fonds sonores : (type, [(t, intensité)])
BEDS = [("vent", [(0, 0.3), (1.0, 0.5), (6.0, 1.0), (6.3, 0.2), (40, 0.35), (60, 0.5), (90, 0.3), (120, 0.2)]),
        ("sable", [(0, 0), (100.5, 0), (101.5, 1.0), (112.5, 1.0), (114, 0), (120, 0)]),       # pluie
        ("vent", [(0, 0), (115.0, 0), (116.5, 0.9), (116.6, 0), (120, 0)])]                   # dernière chute
