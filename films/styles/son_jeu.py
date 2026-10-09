"""Sons de jeu vidéo rétro (puces 8 bits : ondes carrées, triangle, bruit), synthétisés en numpy.

Esprit de l'épisode 21 (la vidéo qui a fait le plus de vues) : pas de nappe de fond, le son suit tout ce qui bouge —
un bip quand le faisceau trace, un clic par lettre, une pièce quand un compteur tourne, un « power-up » sur les
révélations, une explosion sur les chiffres-chocs.
Tous les sons sont des tableaux numpy mono à MI.SR, amplitude ≈ ±amp.
"""
import numpy as np

from films import montage_ia as MI

SR = MI.SR


def _t(d):
    return np.arange(int(d * SR)) / SR


def _doux(y, k=6):
    """Arrondit les carrés (un vrai 8 bits passé dans un petit haut-parleur, pas une scie dans l'oreille)."""
    return np.convolve(y, np.ones(k) / k, mode="same")


def carre(f, d, amp=0.1, rapport=0.5, att=0.003, decl=None):
    """Note carrée (f peut être un tableau : glissando). decl = constante de déclin (None : tenue)."""
    t = _t(d)
    f = np.broadcast_to(np.asarray(f, float), t.shape)
    ph = np.cumsum(f) / SR % 1.0
    y = np.where(ph < rapport, 1.0, -1.0)
    env = np.minimum(1, t / att) * (np.exp(-t / decl) if decl else 1.0)
    env *= np.minimum(1, (d - t) / 0.006)
    return _doux(y * env) * amp


def triangle(f, d, amp=0.15, decl=None):
    t = _t(d)
    f = np.broadcast_to(np.asarray(f, float), t.shape)
    ph = np.cumsum(f) / SR % 1.0
    y = 4 * np.abs(ph - 0.5) - 1
    env = np.minimum(1, t / 0.004) * (np.exp(-t / decl) if decl else 1.0) * np.minimum(1, (d - t) / 0.01)
    return y * env * amp


def bruit(d, amp=0.1, decl=0.08, pas=1):
    """Bruit 8 bits (échantillons tenus `pas` fois : plus le pas est grand, plus c'est grave)."""
    n = int(d * SR)
    y = np.repeat(np.random.default_rng(int(d * 1e4) + pas).uniform(-1, 1, n // pas + 1), pas)[:n]
    return y * np.exp(-_t(d) / decl) * amp


def suite(notes, amp=0.1, rapport=0.5, decl=None):
    """Des notes à la suite : [(fréquence, durée)]."""
    return np.concatenate([carre(f, d, amp, rapport, decl=decl) for f, d in notes])


def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------------------------------------------ le catalogue
def trace(f=880, amp=0.035):
    """Le bip du faisceau qui trace (très court)."""
    return carre(f, 0.035, amp, 0.25, decl=0.02)


def lettre(amp=0.03):
    """Le clic d'une lettre qui s'écrit (dialogue de jeu rétro)."""
    return carre(1760, 0.018, amp, 0.125, decl=0.008)


def selection(amp=0.08):
    """Curseur de menu : deux notes brèves."""
    return suite([(note(84), 0.04), (note(91), 0.07)], amp, 0.25, decl=0.05)


def piece(amp=0.09):
    """La pièce (si → mi aigus)."""
    return suite([(note(83), 0.06), (note(88), 0.28)], amp, 0.5, decl=0.12)


def tic_compteur(i=0, amp=0.04):
    return carre(note(79 + (i % 5)), 0.025, amp, 0.25, decl=0.012)


def powerup(amp=0.08):
    """Arpège qui monte vite (révélation)."""
    return suite([(note(m), 0.045) for m in (60, 64, 67, 72, 76, 79, 84, 88)], amp, 0.5, decl=0.06)


def niveau(amp=0.09):
    """Petite fanfare de niveau gagné."""
    return suite([(note(72), 0.09), (note(76), 0.09), (note(79), 0.09), (note(84), 0.3)], amp, 0.5, decl=0.2)


def explosion(amp=0.25, d=0.7):
    return bruit(d, amp, 0.18, 6) + carre(np.linspace(180, 40, int(d * SR)), d, amp * 0.4, decl=0.15)


def degat(amp=0.1):
    """Coup reçu : glissando qui descend."""
    d = 0.35
    return carre(np.linspace(700, 120, int(d * SR)), d, amp, 0.5, decl=0.2)


def faux(amp=0.1):
    """Buzzer « mauvaise réponse »."""
    return suite([(note(43), 0.12), (note(39), 0.32)], amp, 0.5)


def saut(amp=0.08):
    d = 0.22
    return carre(np.geomspace(300, 1100, int(d * SR)), d, amp, 0.5, decl=0.15)


def aspire(amp=0.08):
    """Glissando qui descend lentement : quelque chose est absorbé."""
    d = 0.6
    return triangle(np.geomspace(1400, 220, int(d * SR)), d, amp * 1.5) + carre(np.geomspace(1400, 220, int(d * SR)), d, amp * 0.3, 0.125)


def alerte(n=2, amp=0.07):
    return suite([(note(81), 0.12), (note(76), 0.12)] * n, amp, 0.5)


def pause(amp=0.08):
    """Jingle de pause."""
    return suite([(note(88), 0.07), (note(84), 0.07), (note(88), 0.07), (note(84), 0.2)], amp, 0.5, decl=0.15)


def ennemi(amp=0.09):
    """Apparition d'un ennemi : arpège grave et inquiétant."""
    return suite([(note(m), 0.08) for m in (45, 48, 51, 54, 45, 48, 51, 54)], amp, 0.25)


def pas_(amp=0.04):
    return bruit(0.05, amp, 0.015, 3)


def moteur(d, amp=0.03):
    t = _t(d)
    return carre(70 + 8 * np.sin(2 * np.pi * 3 * t), d, amp, 0.25)


def tronconneuse(d=0.8, amp=0.05):
    t = _t(d)
    return carre(110 + 30 * np.sin(2 * np.pi * 9 * t), d, amp, 0.2) + bruit(d, amp * 0.6, d, 2)


def montee(d=1.6, amp=0.06):
    """Une note qui monte pendant d secondes (la croissance)."""
    return carre(np.geomspace(200, 1200, int(d * SR)), d, amp, 0.25)


def suite_demain(amp=0.1):
    """Jingle de fin, en suspens (« à suivre »)."""
    return suite([(note(72), 0.12), (note(74), 0.12), (note(76), 0.12), (note(79), 0.12), (note(83), 0.5)],
                 amp, 0.5, decl=0.4)


# ------------------------------------------------------------------------------------------------ vrais bruitages
# Banque CC0 (films/sons, voir LICENCE.md) : interface de jeu Kenney, échantillons Sonic Pi / Adafruit.
import os as _os
import wave as _wave

_SONS = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "sons")
_CACHE = {}


def fichier(nom, amp=0.3, d=None):
    """Un bruitage de la banque, crête ramenée à amp ; d coupe la fin (avec un fondu de 50 ms)."""
    if nom not in _CACHE:
        with _wave.open(_os.path.join(_SONS, nom + ".wav")) as f:
            y = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float64) / 32768
        _CACHE[nom] = y / (np.abs(y).max() + 1e-9)
    y = _CACHE[nom] * amp
    if d is not None and len(y) > int(d * SR):
        y = y[:int(d * SR)].copy()
        k = int(0.05 * SR)
        y[-k:] *= np.linspace(1, 0, k)
    return y
