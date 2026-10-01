"""Son immersif en stéréo : accords tenus qui changent avec les plans, pulsation grave, souffle d'air, whooshes
qui suivent le mouvement de caméra (panoramique gauche/droite), impacts graves, montées, réverbération.
Tout reste doux et grave (pas d'aigus agressifs). Fréquence 48 kHz, sortie (n, 2).
"""
import math
import wave

import numpy as np

SR = 48000


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(x, fc):
    """Filtre passe-bas doux (spectral, sans déphasage) ; x : (n,) ou (n, 2)."""
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / np.sqrt(1 + (f / fc) ** 4)
    return np.fft.irfft(X * (g[:, None] if x.ndim == 2 else g), n=len(x), axis=0)


def bandpass(x, f0, q=1.0):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-3
    g = 1 / np.sqrt(1 + (q * (f / f0 - f0 / f)) ** 2)
    return np.fft.irfft(X * (g[:, None] if x.ndim == 2 else g), n=len(x), axis=0)


def pan(x, p):
    """Mono → stéréo, p de −1 (gauche) à +1 (droite), scalaire ou tableau (loi à puissance constante)."""
    a = (np.asarray(p, float) + 1) * math.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def reverb(x, dur=3.2, decay=2.6, mix=0.35, seed=1, fc=3500):
    """Réverbération par convolution avec une réponse impulsionnelle synthétique (deux bruits décorrélés)."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-tt * decay)[:, None]
    ir = lowpass(ir, fc)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    ir /= np.sqrt((ir ** 2).sum(0))
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    m = len(x) + n
    L = 1 << (m - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, L, axis=0) * np.fft.rfft(ir, L, axis=0), L, axis=0)[:len(x)]
    return x * (1 - mix) + wet * mix * 3.0


# ------------------------------------------------------------------------------------------------ éléments
def note(f, dur, amp=1.0, att=1.2, rel=1.6, detune=0.0025, seed=0):
    """Nappe : trois oscillateurs légèrement désaccordés, harmoniques douces, enveloppe lente."""
    tt = _t(dur)
    rng = np.random.default_rng(seed)
    y = np.zeros_like(tt)
    for d in (-detune, 0.0, detune):
        ph = rng.uniform(0, 6.28)
        ff = f * (1 + d)
        y += np.sin(2 * np.pi * ff * tt + ph) + 0.28 * np.sin(4 * np.pi * ff * tt + ph) + 0.1 * np.sin(6 * np.pi * ff * tt)
    env = np.minimum(1, tt / att) * np.minimum(1, np.maximum(0, (dur - tt) / rel))
    return y / 3 * env * amp


def chord(freqs, dur, amp=0.1, seed=0):
    out = np.zeros((int(dur * SR), 2))
    for i, f in enumerate(freqs):
        p = (i / max(1, len(freqs) - 1)) * 1.0 - 0.5     # notes réparties dans l'espace stéréo
        out += pan(note(f, dur, amp, seed=seed + i), p)
    return out


def kick(amp=0.3):
    """Pulsation grave et ronde, comme un battement de cœur lointain."""
    tt = _t(0.7)
    f = 48 + 40 * np.exp(-tt / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.16) * np.minimum(1, tt / 0.003) * amp


def heartbeat(amp=0.3):
    out = np.zeros(int(0.9 * SR))
    k = kick(amp)
    out[:len(k)] += k
    i = int(0.24 * SR)
    out[i:i + len(k)] += kick(amp * 0.6)[:len(out) - i]
    return out


def whoosh(dur=1.0, amp=0.2, p0=-0.7, p1=0.7, f0=300, f1=1400, seed=3):
    """Souffle filtré qui balaie le spectre et l'espace stéréo (suit un mouvement de caméra)."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    x = np.random.default_rng(seed).standard_normal(n)
    # balayage : somme de quelques bandes pondérées dans le temps
    y = np.zeros(n)
    for k, fc in enumerate(np.geomspace(f0, f1, 6)):
        w = np.exp(-((u - k / 5) / 0.22) ** 2)
        y += bandpass(x, fc, 2.0) * w
    env = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.6
    return pan(y * env * amp / 2.5, p0 + (p1 - p0) * u)


def sub_hit(amp=0.4):
    tt = _t(2.4)
    f = 34 + 46 * np.exp(-tt / 0.15)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.75)
    thud = lowpass(np.random.default_rng(4).standard_normal(len(tt)), 180) * np.exp(-tt / 0.06) * 2
    return (boom + thud) * np.minimum(1, tt / 0.004) * amp


def riser(dur=1.5, amp=0.12, seed=5):
    tt = _t(dur)
    u = tt / dur
    x = lowpass(np.random.default_rng(seed).standard_normal(len(tt)), 900)
    tone = np.sin(2 * np.pi * np.cumsum(110 + 110 * u ** 2) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(165 + 165 * u ** 2) / SR)
    y = (x * 1.5 + tone * 0.5) * u ** 2.5 * amp
    y[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    return y


def air(dur, amp=0.05, seed=9):
    """Souffle d'espace : bruit très filtré qui respire et se déplace lentement."""
    tt = _t(dur)
    rng = np.random.default_rng(seed)
    l = lowpass(rng.standard_normal(len(tt)), 420)
    r = lowpass(rng.standard_normal(len(tt)), 420)
    b = 0.7 + 0.3 * np.sin(2 * np.pi * tt / 7.0)
    return np.stack([l * b, r * (1.4 - b)], 1) * amp * 3


def mallet(f=330, amp=0.1):
    """Petit coup feutré (marimba grave), pour les points qui s'allument."""
    tt = _t(1.2)
    y = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * f * 4.0 * tt) * np.exp(-tt / 0.03)) * np.exp(-tt / 0.28)
    return y * np.minimum(1, tt / 0.002) * amp


def shimmer(dur=2.0, f=220, amp=0.05, seed=2):
    """Nappe scintillante douce (accord d'harmoniques avec léger vibrato), pour les révélations."""
    tt = _t(dur)
    y = sum(np.sin(2 * np.pi * f * h * tt + 0.3 * np.sin(tt * (2 + h))) / h for h in (1, 1.5, 2, 3))
    env = np.minimum(1, tt / 0.6) * np.minimum(1, (dur - tt) / 1.0)
    return y * env * amp


def shepard(dur, rate=0.25, amp=0.1, f_low=40.0, octaves=7, center=220.0, width=1.1, accel=0.0):
    """Son de Shepard : des octaves qui montent sans fin (illusion de chute / de vertige infini).
    rate : octaves par seconde (négatif = descend) ; accel : la montée s'accélère avec le temps."""
    tt = _t(dur)
    pos = rate * tt + 0.5 * accel * tt * tt              # position en octaves
    y = np.zeros_like(tt)
    for k in range(octaves):
        o = (k + pos) % octaves
        f = f_low * 2 ** o
        w = np.exp(-((np.log2(f / center)) / width) ** 2)  # cloche sur l'échelle des octaves
        ph = 2 * np.pi * np.cumsum(f) / SR
        y += w * (np.sin(ph) + 0.2 * np.sin(2 * ph))
    env = np.minimum(1, tt / 0.8)
    return lowpass(y, 1800) * env * amp


def glide_tone(freq_curve, amp_curve, vib=0.0):
    """Note dont la hauteur et le volume suivent des courbes échantillonnées (une valeur par échantillon)."""
    ph = 2 * np.pi * np.cumsum(freq_curve) / SR
    return (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)) * amp_curve


# ------------------------------------------------------------------------------------------------ mixage
class Mix:
    def __init__(self, dur):
        self.dur = dur
        self.dry = np.zeros((int(dur * SR) + 1, 2))
        self.wet = np.zeros_like(self.dry)                 # envoyé dans la réverbération

    def add(self, t0, x, gain=1.0, p=0.0, send=0.3):
        if x.ndim == 1:
            x = pan(x, p)
        i = int(t0 * SR)
        m = min(len(self.dry) - i, len(x))
        if m <= 0:
            return
        self.dry[i:i + m] += x[:m] * gain * (1 - send * 0.5)
        self.wet[i:i + m] += x[:m] * gain * send

    def master(self, peak_db=-6.0, rms_db=-21.0):
        """Niveau moyen visé (rms_db) puis limiteur doux : les impacts graves ne dictent plus le volume global."""
        y = self.dry + reverb(self.wet, mix=1.0) * 0.6
        y *= 10 ** (rms_db / 20) / (np.sqrt((y ** 2).mean()) + 1e-9)
        lim = 10 ** (peak_db / 20)
        y = lim * np.tanh(y / lim)
        n = len(y)
        y *= np.minimum(1, (n - np.arange(n)) / (0.8 * SR))[:, None]
        return y

    def write(self, path, peak_db=-6.0, rms_db=-21.0):
        y = self.master(peak_db, rms_db)
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


# notes (Hz)
A1, C2, D2, E2, F2, G2, A2 = 55.0, 65.41, 73.42, 82.41, 87.31, 98.0, 110.0
B2, C3, D3, E3, F3, G3, A3 = 123.47, 130.81, 146.83, 164.81, 174.61, 196.0, 220.0
