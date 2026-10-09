"""Mixage « pro » : ce que fait un monteur son, en numpy.

- Chaque bruitage est rangé dans une famille (interface, effet, accent, ambiance) et ramené au niveau de sa
  famille (mesure RMS, pas la crête) : les bips ne couvrent plus la voix, les accents frappent.
- Stéréo : chaque bruitage est placé à gauche ou à droite (pan à puissance constante).
- Les bips 8 bits sont adoucis (filtre passe-bas) ; les effets partagent une petite réverbération (même espace).
- Effacement automatique (« ducking ») : les effets baissent de ≈ 7 dB quand la voix parle, remontent dans les
  silences.
- Voix : coupe des graves inutiles (< 90 Hz), compression douce, un peu de présence (2-4 kHz).
- Bus final : compression de colle légère, puis limiteur ; la sonie finale (−14 LUFS, crête −1,5 dB) est réglée en
  deux passes par ffmpeg (loudnorm mesuré puis appliqué).
"""
import json
import subprocess
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt, sosfiltfilt

from films import montage_ia as MI

SR = MI.SR
NIVEAUX = {"interface": -34.0, "effet": -26.0, "accent": -21.0, "ambiance": -32.0}   # dBFS RMS par famille


def _db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def _filtre(x, f, type_):
    return sosfiltfilt(butter(2, f, btype=type_, fs=SR, output="sos"), x)


def _enveloppe(x, att=0.01, rel=0.3, pas=0.01):
    """Enveloppe RMS lissée (montée rapide, descente lente), échantillonnée tous les `pas` s puis interpolée."""
    n = int(pas * SR)
    m = len(x) // n
    e = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1))
    out = np.zeros_like(e)
    ka, kr = np.exp(-pas / att), np.exp(-pas / rel)
    v = 0.0
    for i, s in enumerate(e):
        k = ka if s > v else kr
        v = k * v + (1 - k) * s
        out[i] = v
    return np.interp(np.arange(len(x)), np.arange(m) * n + n / 2, out)


def compresser(x, seuil_db=-22.0, ratio=3.0, att=0.005, rel=0.15):
    env = _enveloppe(x, att, rel, 0.005)
    lv = 20 * np.log10(env + 1e-9)
    gain_db = np.where(lv > seuil_db, (seuil_db - lv) * (1 - 1 / ratio), 0.0)
    return x * 10 ** (gain_db / 20)


def voix_pro(v):
    v = _filtre(v, 90, "high")
    presence = sosfiltfilt(butter(2, [2000, 4500], btype="band", fs=SR, output="sos"), v)
    v = v + 0.25 * presence
    v = compresser(v, -24, 2.5)
    return v * 10 ** ((-18 - _db(v[np.abs(v) > 1e-3])) / 20)


def reverb_ir(d=0.45, pre=0.012):
    """Réponse impulsionnelle synthétique : petite pièce, bruit qui décroît, aigus amortis."""
    n = int(d * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    ir = np.zeros((n, 2))
    for c in range(2):
        b = rng.normal(0, 1, n) * np.exp(-t / (d / 6.9 * 2.3))
        ir[:, c] = sosfilt(butter(1, 5000, fs=SR, output="sos"), b)
    ir[: int(pre * SR)] = 0
    return ir / np.abs(ir).sum(0).max() * 6


def mixer(chemin, voix, dur, evenements):
    """evenements : [(instant, tableau mono, famille, pan -1..1)]. Écrit un wav stéréo 48 kHz (avant loudnorm)."""
    n = int(dur * SR)
    v = np.zeros(n)
    v[:min(n, len(voix))] = voix[:n]
    v = voix_pro(v)
    bus = {f: np.zeros((n, 2)) for f in NIVEAUX}
    for t0, snd, fam, pan in evenements:
        if len(snd) == 0:
            continue
        s = snd - snd.mean()
        if fam == "interface":
            s = _filtre(s, 5500, "low")
        s = s * 10 ** ((NIVEAUX[fam] - _db(s[np.abs(s) > 1e-4] if np.any(np.abs(s) > 1e-4) else s)) / 20)
        a = (pan + 1) * np.pi / 4
        g = np.array([np.cos(a), np.sin(a)]) * np.sqrt(2)
        i = int(t0 * SR)
        k = min(n - i, len(s))
        if k > 0 and i >= 0:
            bus[fam][i:i + k] += s[:k, None] * g
    fx = sum(bus.values())
    ir = reverb_ir()
    for c in range(2):                                      # un peu d'espace commun
        fx[:, c] += 0.18 * fftconvolve(fx[:, c], ir[:, c])[:n]
    fx[:, 0] = _filtre(fx[:, 0], 60, "high")
    fx[:, 1] = _filtre(fx[:, 1], 60, "high")
    env = _enveloppe(v, 0.02, 0.35)                         # effacement sous la voix
    parle = np.clip((20 * np.log10(env + 1e-9) + 45) / 15, 0, 1)
    fx *= (10 ** (-7 * parle / 20))[:, None]
    m = fx + v[:, None]
    for c in range(2):                                      # colle + limiteur doux
        m[:, c] = compresser(m[:, c], -16, 1.8, 0.01, 0.2)
    m = np.tanh(m / 0.9) * 0.9
    m *= np.minimum(1, (n - np.arange(n)) / (0.6 * SR))[:, None]
    with wave.open(chemin, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((np.clip(m, -1, 1) * 32767).astype(np.int16).tobytes())


def loudnorm(wav_in, cible=-14.0, crete=-1.5):
    """Filtre ffmpeg loudnorm en deux passes (mesure, puis réglage linéaire exact)."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav_in, "-af",
                          f"loudnorm=I={cible}:TP={crete}:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(log[log.rindex("{"):log.rindex("}") + 1])
    return (f"loudnorm=I={cible}:TP={crete}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
