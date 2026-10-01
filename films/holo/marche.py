"""Cycle de marche pour l'humain hologramme (squelette MakeHuman simplifié, voir humain.skin).

Conventions (axes du repos) : le personnage regarde vers +z ; rot("x", -a) avance un membre vers +z.
"""
import math

import numpy as np

from films.holo.humain import rot, skin

CYCLE = 1.1                                               # secondes par cycle (deux pas)
STRIDE = 1.26                                             # mètres parcourus par cycle


def walk_pose(t, speed=1.0, arms_down=33.0):
    """Pose de marche au temps t. Renvoie (rotations, translation du bassin)."""
    ph = 2 * math.pi * (t / CYCLE) * speed
    rots = {}
    for side, sgn, off in (("L", 1, 0.0), ("R", -1, math.pi)):
        p = ph + off
        hip = 24 * math.sin(p)                            # cuisse : avant (+) / arrière (−)
        knee = 6 + 58 * max(0.0, math.cos(p - 0.35)) ** 2 + 10 * max(0.0, -math.sin(p)) ** 2
        ankle = 12 * math.sin(p + 0.9) - 4
        rots[f"upperleg01.{side}"] = rot("x", -hip) @ rot("z", -3.5 * sgn)
        rots[f"lowerleg01.{side}"] = rot("x", knee) @ rot("z", -1.0 * sgn)
        rots[f"foot.{side}"] = rot("x", ankle)
        swing = -20 * math.sin(p)                         # bras opposé à la jambe
        rots[f"clavicle.{side}"] = rot("z", -3 * sgn)
        rots[f"upperarm01.{side}"] = rot("x", -swing) @ rot("z", -arms_down * sgn)
        rots[f"lowerarm01.{side}"] = rot("x", 34 - (10 + 12 * max(0.0, math.sin(p + math.pi)))) @ rot("y", 18 * sgn)
    rots["spine05"] = rot("y", 4 * math.sin(ph))          # le bassin tourne un peu
    rots["spine02"] = rot("y", -6 * math.sin(ph)) @ rot("x", 3)   # les épaules contre-tournent
    rots["neck01"] = rot("y", 2 * math.sin(ph)) @ rot("x", -4)
    rots["root"] = rot("z", 2 * math.sin(ph))
    bob = 0.018 * math.cos(2 * ph) - 0.012
    sway = 0.012 * math.sin(ph)
    return rots, np.array([sway, bob, 0.0])


def walk(t, speed=1.0, forward=True):
    """Sommets déformés et transformations, avec avancée vers +z."""
    rots, root = walk_pose(t, speed)
    if forward:
        root = root + np.array([0, 0, STRIDE * t / CYCLE * speed])
    return skin(rots, root)
