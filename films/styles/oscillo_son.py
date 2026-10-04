"""Banque de sons synthétisés pour le style oscilloscope (tout est généré, aucun échantillon externe).

Effets : allumage d'écran, câble qui casse, grondement grave, métal, cliquets, vent de chute, sifflement, souffle,
coup de vent (whoosh), montée (riser), arrêt de bande, glitch, neige télé, foule, applaudissements, battement de cœur,
alarme, cordes pincées, carillon d'ascenseur…
Musique : synthé rétro (nappe, basse, arpège, grosse caisse, charleston) dont l'humeur suit des sections.

Tous les sons sont des tableaux numpy mono en float, à SR = 48 kHz.
"""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
RNG = np.random.default_rng(7)


def _t(d):
    return np.arange(int(d * SR)) / SR


def bruit(d):
    return RNG.normal(0, 1, int(d * SR))


def pb(x, fc, o=2):
    return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)


def ph(x, fc, o=2):
    return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)


def bp(x, f1, f2, o=2):
    return sosfilt(butter(o, [f1, min(f2, SR / 2 - 100)], "band", fs=SR, output="sos"), x)


def lisser(x, n):
    """Moyenne glissante centrée sur n échantillons (rapide, par somme cumulée)."""
    c = np.concatenate([[0.0], np.cumsum(np.pad(x, (n // 2, n - n // 2), mode="edge"))])
    return (c[n:] - c[:-n])[:len(x)] / n


def norm(x, amp):
    return x / (np.abs(x).max() + 1e-9) * amp


def sinus_glisse(f0, f1, d, courbe=1.0):
    t = _t(d)
    f = f0 + (f1 - f0) * (t / d) ** courbe
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def balayage_bruit(d, fa, fb, env):
    """Bruit filtré dont la bande glisse de fa à fb (fondu entre plusieurs bandes fixes)."""
    t = _t(d)
    n = len(t)
    x = bruit(d)
    out = np.zeros(n)
    K = 10
    for k in range(K):
        c = fa * (fb / fa) ** (k / (K - 1))
        g = np.exp(-0.5 * ((t / d - k / (K - 1)) / (0.9 / K)) ** 2)
        out += bp(x, c * 0.7, c * 1.45) * g
    return out * env(t / d)


# ------------------------------------------------------------------------------------------------ effets
def whoosh(d=0.45, amp=0.3, monte=True):
    fa, fb = (300, 5000) if monte else (5000, 300)
    return norm(balayage_bruit(d, fa, fb, lambda u: np.sin(np.pi * u) ** 1.5), amp)


def riser(d=1.5, amp=0.25):
    x = balayage_bruit(d, 200, 7000, lambda u: u ** 2)
    t = _t(d)
    ton = sinus_glisse(150, 900, d, 1.5) * (1 + 0.3 * np.sin(2 * np.pi * (4 + 12 * t / d) * t)) * (t / d) ** 2
    return norm(x + 0.5 * norm(ton, 1), amp)


def boom(amp=0.6, f0=65, d=1.6):
    t = _t(d)
    f = 32 + (f0 * 2.2 - 32) * np.exp(-t / 0.06)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    s += 0.5 * pb(bruit(d), 700) * np.exp(-t / 0.03)
    return norm(np.tanh(2.2 * s), amp)


def thump(amp=0.4):
    t = _t(0.35)
    s = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t / 0.08) + 40) / SR) * np.exp(-t / 0.1)
    return norm(s + 0.3 * pb(bruit(0.35), 400) * np.exp(-t / 0.02), amp)


def clang(f0=420, amp=0.3, d=1.6):
    t = _t(d)
    out = np.zeros(len(t))
    for r, dec, a in ((1, 1.2, 1), (2.76, 0.8, 0.6), (5.40, 0.5, 0.45), (8.93, 0.35, 0.3), (13.34, 0.2, 0.2),
                      (1.51, 0.9, 0.4)):
        out += a * np.sin(2 * np.pi * f0 * r * t + RNG.uniform(0, 6)) * np.exp(-t / dec)
    out += 0.6 * ph(bruit(d), 2500) * np.exp(-t / 0.008)
    return norm(out, amp)


def cliquet(amp=0.2):
    t = _t(0.06)
    return norm(ph(bruit(0.06), 2500) * np.exp(-t / 0.003) + 0.6 * np.sin(2 * np.pi * 3300 * t) * np.exp(-t / 0.015), amp)


def craquement(amp=0.4):
    t = _t(0.12)
    return norm(bp(bruit(0.12), 1200, 8000) * np.exp(-t / 0.012), amp)


def snap(amp=0.5):
    """Câble d'acier qui casse : craquement sec + corde qui vibre + résonance métallique."""
    d = 1.4
    t = _t(d)
    cr = np.zeros(len(t))
    cr[:int(0.12 * SR)] = craquement(1.0)
    f = 60 + 180 * np.exp(-t / 0.25) + 6 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.4)
    tw = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / 0.35)
    return norm(cr + 0.35 * pb(tw, 1800) + 0.5 * clang(520, 1.0, d), amp)


def vent(d, amp=0.25, fa=150, fb=2600):
    """Souffle de chute qui s'intensifie."""
    x = balayage_bruit(d, fa, fb, lambda u: 0.15 + 0.85 * u ** 1.4)
    x[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    return norm(x, amp)


def sifflement(d, amp=0.08, f0=1900, f1=500):
    t = _t(d)
    return norm(sinus_glisse(f0, f1, d) * np.minimum(1, t / 0.3) * (1 - 0.3 * t / d), amp)


def crepitement(d, amp=0.12, dens=40):
    n = int(d * SR)
    out = np.zeros(n)
    c = craquement(1.0)[:int(0.03 * SR)]
    for _ in range(int(d * dens)):
        i = RNG.integers(0, max(1, n - len(c)))
        out[i:i + len(c)] += c * RNG.uniform(0.2, 1)
    return norm(out, amp)


def arret_bande(d=0.6, amp=0.3):
    """Arrêt sur image : le son « ralentit » et tombe."""
    t = _t(d)
    f = 30 + 520 * (1 - t / d) ** 2
    s = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 5))
    return norm((s + 0.3 * pb(bruit(d), 900)) * (1 - t / d), amp)


def glitch(d=0.25, amp=0.25):
    n = int(d * SR)
    out = np.zeros(n)
    b = int(0.025 * SR)
    for i in range(0, n, b):
        r = RNG.random()
        tt = np.arange(min(b, n - i)) / SR
        if r < 0.4:
            out[i:i + len(tt)] = np.sign(np.sin(2 * np.pi * RNG.uniform(200, 3000) * tt))
        elif r < 0.7:
            out[i:i + len(tt)] = RNG.normal(0, 0.7, len(tt))
    out = np.round(out * 4) / 4                                            # écrasement des bits
    return norm(out, amp)


def neige(d=0.22, amp=0.22):
    t = _t(d)
    return norm(ph(bruit(d), 900) * (1 - t / d) ** 1.5 + crepitement(d, 0.6, 120), amp)


def allumage(amp=0.35):
    """Allumage d'écran cathodique : choc grave, ronflement qui monte, sifflement aigu."""
    d = 1.2
    t = _t(d)
    hum = sum(np.sin(2 * np.pi * 50 * k * t) / k for k in (1, 2, 3, 4, 6)) * np.minimum(1, t / 0.15) * np.exp(-t / 0.5)
    whine = np.sin(2 * np.pi * 7800 * t) * np.exp(-t / 0.25) * 0.15
    out = 0.6 * hum + whine
    out[:int(0.35 * SR)] += thump(1.0)
    return norm(out, amp)


def foule(d, amp=0.12):
    """Murmure de foule : plusieurs voix (bruit filtré modulé lentement)."""
    n = int(d * SR)
    out = np.zeros(n)
    for _ in range(8):
        c = RNG.uniform(300, 900)
        m = pb(RNG.normal(0, 1, n), 4)
        m = np.maximum(0, m / (np.abs(m).max() + 1e-9))
        out += bp(RNG.normal(0, 1, n), c, c * 1.8) * m
    t = np.arange(n) / SR
    return norm(out * np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.6), amp)


def exclamation(amp=0.2):
    """« Oh ! » de la foule."""
    d = 0.9
    t = _t(d)
    x = bp(bruit(d), 400, 1400) + 0.5 * bp(bruit(d), 2000, 3000)
    return norm(x * np.minimum(1, t / 0.05) * np.exp(-t / 0.3), amp)


def applaudissements(d=2.2, amp=0.15):
    n = int(d * SR)
    out = np.zeros(n)
    cl = bp(bruit(0.02), 900, 5000) * np.exp(-_t(0.02) / 0.004)
    for _ in range(int(d * 90)):
        i = RNG.integers(0, n - len(cl))
        out[i:i + len(cl)] += cl * RNG.uniform(0.3, 1)
    t = np.arange(n) / SR
    return norm(out * np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 0.9), amp)


def coeur(amp=0.3):
    t = _t(0.5)
    def coup(f, a, t0):
        u = np.maximum(0, t - t0)
        return a * np.sin(2 * np.pi * f * u) * np.exp(-u / 0.05) * (t >= t0)
    return norm(pb(coup(55, 1, 0) + coup(48, 0.7, 0.2), 200), amp)


def alarme(amp=0.12, n=2):
    out = []
    for _ in range(n):
        for f in (880, 660):
            t = _t(0.11)
            out.append(np.sign(np.sin(2 * np.pi * f * t)) * np.minimum(1, (0.11 - t) / 0.01))
    return norm(pb(np.concatenate(out), 4000), amp)


def chirp(f0, f1, d=0.3, amp=0.15):
    t = _t(d)
    return norm(sinus_glisse(f0, f1, d) * np.minimum(1, t / 0.01) * np.minimum(1, (d - t) / 0.05), amp)


def pince(f, amp=0.15, d=0.9):
    t = _t(d)
    s = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (2 + 2.5 * k)) / k for k in range(1, 7))
    return norm(s * np.minimum(1, t / 0.003), amp)


def cloche(f=784, amp=0.2, d=2.2):
    t = _t(d)
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / dc) for r, a, dc in
            ((1, 1, 1.4), (2, 0.4, 0.8), (3, 0.2, 0.5), (4.2, 0.12, 0.3)))
    return norm(s * np.minimum(1, t / 0.004), amp)


def ding_ascenseur(amp=0.22):
    a, b = cloche(1318.5, 1.0, 1.6), cloche(1046.5, 1.0, 2.0)
    out = np.zeros(int(2.4 * SR))
    out[:len(a)] += a
    out[int(0.32 * SR):int(0.32 * SR) + len(b)] += b
    return norm(out, amp)


def scintillement(d=2.0, amp=0.07):
    """Petites notes cristallines aléatoires (apesanteur)."""
    n = int(d * SR)
    out = np.zeros(n)
    for _ in range(int(d * 6)):
        f = RNG.choice([1760, 2093, 2349, 2637, 3136])
        c = cloche(f, 1.0, 0.6)
        i = RNG.integers(0, n - len(c))
        out[i:i + len(c)] += c * RNG.uniform(0.3, 1)
    return norm(out, amp)


def tictac(d, amp=0.1, pas=0.1):
    n = int(d * SR)
    out = np.zeros(n)
    for k, i in enumerate(range(0, n - 3000, int(pas * SR))):
        tt = np.arange(1500) / SR
        out[i:i + 1500] += np.sin(2 * np.pi * (2600 if k % 2 else 1900) * tt) * np.exp(-tt / 0.006)
    return norm(out, amp)


def souffle(d=1.1, amp=0.12, inspire=True):
    x = balayage_bruit(d, 500, 2600, (lambda u: np.sin(np.pi * u ** 0.7) ** 2) if inspire
                       else (lambda u: np.sin(np.pi * u ** 1.4) ** 2))
    return norm(x if inspire else x[::-1], amp)


def porte(d=1.6, amp=0.12):
    t = _t(d)
    moteur = sum(np.sin(2 * np.pi * 110 * k * t) / k for k in (1, 2, 3)) * 0.4
    return norm((moteur + pb(bruit(d), 600)) * np.sin(np.pi * t / d) ** 2, amp)


# ------------------------------------------------------------------------------------------------ musique
def _f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


D, DM9, BB, A, GM, F, C, AM, GMD = ((62, 65, 69), (62, 65, 69, 76), (58, 62, 65), (57, 61, 64), (55, 62, 67),
                                    (60, 65, 69), (60, 64, 67), (57, 60, 64), (62, 67, 70, 74))
HUMEURS = {
    #              accords                    nappe basse arpège caisse charley  arpège/temps
    "tension":  ([D, D, BB, A],              .55, 1.0, .7, 0.0, .5, 4),
    "chute":    ([D, D, BB, A],              .55, .0, .0, 0.0, .0, 4),
    "pulsation": ([D, BB, GM, A],            .4, 1.0, 1.0, 1.0, .8, 4),
    "flottant": ([DM9, GMD],                 .9, 0.0, .35, 0.0, .0, 2),
    "reflexion": ([BB, F, GM, A],            .7, .5, .5, 0.0, .0, 2),
    "lumineux": ([F, C, D, BB],              .5, .9, .9, .7, .7, 4),
    "tension2": ([D, BB, GM, A],             .5, 1.0, .9, 1.0, 1.0, 4),
    "silence":  ([D],                        0, 0, 0, 0, 0, 4),
    "chaleur":  ([F, AM, BB, C],             .8, .4, .45, 0.0, .0, 2),
}


def musique(dur, sections, bpm=96):
    """sections : [(début, humeur)] — les couches se fondent d'une humeur à l'autre (0,3 s)."""
    n = int(dur * SR)
    beat = 60 / bpm
    bar = 4 * beat
    piste = {k: np.zeros(n) for k in ("nappe", "basse", "arpege", "caisse", "charley")}
    gains = {k: np.zeros(n) for k in piste}
    tt = np.arange(n) / SR

    def humeur(t):
        return [h for t0, h in sections if t0 <= t + 1e-6][-1]

    for i, (t0, h) in enumerate(sections):
        t1 = sections[i + 1][0] if i + 1 < len(sections) else dur
        m = (tt >= t0) & (tt < t1)
        for k, g in zip(piste, HUMEURS[h][1:6]):
            gains[k][m] = g
    lisse = int(0.3 * SR)
    for k in gains:
        gains[k] = lisser(gains[k], lisse)

    def poser(k, i0, s):
        i0 = int(i0)
        if i0 >= n:
            return
        j = min(n, i0 + len(s))
        piste[k][i0:j] += s[:j - i0]

    for b in range(int(dur / bar) + 1):
        tb = b * bar
        h = humeur(tb)
        acc = HUMEURS[h][0][b % len(HUMEURS[h][0])]
        div = HUMEURS[h][6]
        # nappe : trois dents de scie désaccordées par note
        d = bar + 0.6
        t = _t(d)
        env = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.6)
        s = sum(((t * _f(m) * (1 + dt)) % 1 - 0.5) for m in acc for dt in (-0.004, 0, 0.005))
        poser("nappe", tb * SR, s * env)
        # basse : croches
        for k in range(8):
            t = _t(beat / 2)
            fb = _f(acc[0] - 24)
            poser("basse", (tb + k * beat / 2) * SR, ((t * fb) % 1 - 0.5) * np.exp(-t / 0.12))
        # arpège : notes de l'accord à l'octave, carré
        notes = [m + 12 for m in acc] + [acc[1] + 24]
        for k in range(4 * div):
            t = _t(beat / div)
            f = _f(notes[k % len(notes)])
            poser("arpege", (tb + k * beat / div) * SR, np.sign(np.sin(2 * np.pi * f * t)) * np.exp(-t / 0.08))
        for k in range(4):
            t = _t(0.25)
            poser("caisse", (tb + k * beat) * SR,
                  np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.12))
            poser("charley", (tb + k * beat + beat / 2) * SR, ph(bruit(0.03), 7000) * np.exp(-_t(0.03) / 0.008))
    piste["nappe"] = pb(piste["nappe"], 1400)
    piste["basse"] = pb(piste["basse"], 380)
    arp = pb(piste["arpege"], 2600)
    dl = int(beat * 0.75 * SR)
    arp[dl:] += 0.35 * arp[:-dl]                                           # écho
    piste["arpege"] = arp
    mix = {"nappe": 0.10, "basse": 0.30, "arpege": 0.07, "caisse": 0.45, "charley": 0.05}
    return sum(piste[k] * gains[k] * mix[k] for k in piste)


def bulles(d=1.2, amp=0.15, dens=14):
    """Glouglous : petites bulles qui remontent (sable mouillé, succion)."""
    n = int(d * SR)
    out = np.zeros(n)
    for _ in range(max(1, int(d * dens))):
        f0 = RNG.uniform(160, 520)
        t = _t(0.08)
        b = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.8 * t / 0.08)) / SR) * np.exp(-t / 0.025)
        i = RNG.integers(0, max(1, n - len(b)))
        out[i:i + len(b)] += b * RNG.uniform(0.4, 1)
    return norm(out, amp)


def vibration(d=1.2, amp=0.2):
    """Grondement qui tremble (le sol qui vibre)."""
    t = _t(d)
    s = np.sin(2 * np.pi * 70 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 16 * t)) + 0.4 * pb(bruit(d), 220)
    return norm(s * np.sin(np.pi * t / d) ** 0.7, amp)


def grincement(d=1.0, amp=0.15):
    """Effort qui force : grave tendu qui grince."""
    t = _t(d)
    am = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * (22 + 6 * np.sin(2 * np.pi * 1.3 * t)) * t))
    s = sinus_glisse(95, 70, d) * am + 0.4 * bp(bruit(d), 300, 900) * am
    return norm(pb(s, 1500) * np.minimum(1, t / 0.1) * np.minimum(1, (d - t) / 0.15), amp)
