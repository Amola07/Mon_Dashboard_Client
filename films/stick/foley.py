"""Bruitage synthétisé (aucun fichier externe) : chaque action a son propre son.

Tout est généré en numpy à 48 kHz : pas, chocs sourds, claquements de pierre (plus aigus pour les petites),
souffles qui suivent la vitesse, bourdonnement de la flèche (plus grave quand la gravité est forte),
explosions, tintements métalliques, « bonk » comique. Chaque son est placé à gauche ou à droite selon l'écran.
"""
import numpy as np

SR = 48000
RNG = np.random.default_rng(7)


def _env(n, attack=0.002, decay=0.1):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / decay)


def _noise(n):
    return RNG.standard_normal(n)


def _lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):                                     # filtre du 1er ordre (sons courts : rapide)
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def _bandpass(x, f, q=8.0):
    """Résonateur (biquad passe-bande)."""
    w = 2 * np.pi * f / SR
    alpha = np.sin(w) / (2 * q)
    b0, b2 = alpha, -alpha
    a0, a1, a2 = 1 + alpha, -2 * np.cos(w), 1 - alpha
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        v = (b0 * x[i] + b2 * x2 - a1 * y1 - a2 * y2) / a0
        x2, x1 = x1, x[i]
        y2, y1 = y1, v
        y[i] = v
    return y


def step(strength=0.5):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (95 - 300 * t) * t) * _env(n, 0.001, 0.025)
    click = _bandpass(_noise(n), 2400, 3) * _env(n, 0.0005, 0.008)
    return (0.8 * thump + 0.35 * click) * strength


def thud(strength=0.8):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 70 * np.exp(-t * 6) + 38
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.16)
    dust = _lowpass(_noise(n), 900) * _env(n, 0.001, 0.07)
    return (1.0 * body + 0.9 * dust) * strength


def clack(strength=0.5, size=22.0):
    n = int(0.12 * SR)
    f = 5200 * (20.0 / max(size, 8.0))                          # petite pierre : plus aigu
    x = _noise(n) * _env(n, 0.0002, 0.012)
    y = _bandpass(x, f, 14) * 3 + _bandpass(x, f * 1.83, 18) * 1.5
    return y * strength * 0.9


def whoosh(duration, strength=0.6, pitch=900.0):
    n = int(duration * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / duration, 0, 1)) ** 2
    x = _bandpass(_noise(n), pitch, 1.2)
    return x * env * strength * 0.8


def boom(strength=1.0):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (55 * np.exp(-t * 1.5) + 28) * t) * _env(n, 0.003, 0.5)
    crack = _lowpass(_noise(n), 3000) * _env(n, 0.0005, 0.06)
    tail = _lowpass(_noise(n), 500) * _env(n, 0.05, 0.6) * 0.4
    return (1.2 * sub + 0.8 * crack + tail) * strength


def clang(strength=0.9):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for f, a, d in ((523, 1.0, 0.5), (1397, 0.6, 0.3), (2215, 0.4, 0.2), (3080, 0.25, 0.12), (787, 0.5, 0.4)):
        y += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    y *= np.clip(t / 0.001, 0, 1)
    return y * strength * 0.35


def bonk(strength=0.9):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    f = 900 * np.exp(-t * 9) + 260
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.001, 0.07)
    return y * strength * 0.8


def snap(strength=1.0):
    n = int(0.5 * SR)
    x = _noise(n) * _env(n, 0.0003, 0.03)
    y = _bandpass(x, 3500, 2) * 2 + _lowpass(_noise(n), 400) * _env(n, 0.001, 0.2)
    return y * strength


def pan(sig, p):
    """p : -1 (gauche) … +1 (droite), panoramique à puissance constante."""
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], axis=1)


class Mixer:
    def __init__(self, duration):
        self.n = int(duration * SR) + SR
        self.out = np.zeros((self.n, 2))

    def add(self, t, sig, p=0.0, gain=1.0):
        i = int(t * SR)
        if i >= self.n or i < 0:
            return
        s = pan(sig * gain, p)
        j = min(self.n, i + len(s))
        self.out[i:j] += s[:j - i]

    def add_stream(self, sig, gain=1.0, p=None):
        m = min(self.n, len(sig))
        if sig.ndim == 1:
            self.out[:m] += np.stack([sig[:m], sig[:m]], axis=1) * gain
        else:
            self.out[:m] += sig[:m] * gain


def hum_stream(freq, amp, duration):
    """Bourdonnement continu (fréquence et amplitude données par image, 60 i/s)."""
    n = int(duration * SR)
    tt = np.arange(n) / SR * 60
    f = np.interp(tt, np.arange(len(freq)), freq)
    a = np.interp(tt, np.arange(len(amp)), amp)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3.01 * ph)) * a
    return y * 0.18


def wind_stream(level, duration):
    """Souffle continu dont le volume suit une courbe (60 i/s)."""
    n = int(duration * SR)
    tt = np.arange(n) / SR * 60
    a = np.interp(tt, np.arange(len(level)), level)
    x = _noise(n)
    # filtre rapide vectorisé : moyenne glissante pour un souffle doux
    k = 40
    x = np.convolve(x, np.ones(k) / k, mode="same")
    x2 = np.convolve(_noise(n), np.ones(8) / 8, mode="same")
    return (x * 2.5 + x2 * 0.5) * a * 0.5
