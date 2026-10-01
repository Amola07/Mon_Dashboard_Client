"""« Si tu tombais dans un trou noir » : démo de rendu physique (≈ 17 s, sans voix).

Image : trou noir calculé rayon par rayon (rayons.py), étalonnage filmique, halo, traînée anamorphique, grain.
Mise en scène : orbite lente → l'Orbe tombe et, vue de loin, ralentit, rougit et se fige au bord (dilatation du
temps) pendant un effet vertigo (la caméra avance en élargissant l'objectif : le trou garde sa taille, le ciel
se tord) → plongée subjective jusqu'à l'horizon → noir.
Son : souffle du disque qui grossit, note de l'Orbe qui descend et s'éteint avec son image (décalage vers le
rouge rendu audible), son de Shepard (montée infinie) qui accélère, coupure nette au passage de l'horizon.
"""
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import skia

from films.persos.orbe import Etat, draw_orbe
from films.trait import son as S
from films.trait.espace import blur_add, post
from films.trait.trait import FPS, H, W, caption, ease, ease_out, lerp, win
from films.trou_noir import rayons as R

DUR = 17.0
RW, RH = 720, 1280                                         # résolution du lancer de rayons (agrandie ×1,5)
T_FALL, T_VERT, T_PLUNGE, T_CROSS = 3.4, 6.0, 10.2, 14.6
EL = math.radians(7.5)
TAN0 = 27.0 * math.tan(math.radians(18))                   # vertigo : distance × tan(fov/2) constant

CAPS = [(0.25, 3.3, "Imagine que tu tombes dans un trou noir."),
        (4.2, 6.9, "Vu de loin… tu n'y arriverais jamais."),
        (7.0, 10.0, "Ton image ralentirait, rougirait… et se figerait au bord. Pour toujours."),
        (10.4, 14.3, "Mais pour toi, rien ne s'arrête."),
        (15.1, DUR, "Tu traverses. Et de l'autre côté… personne ne sait.")]


# ------------------------------------------------------------------------------------------------ caméra
def camera(t):
    """→ position, cible, champ (degrés), roulis."""
    az = lerp(-0.42, -0.12, t / T_PLUNGE)
    if t < T_VERT:
        d = lerp(34.0, 27.0, ease_out(t / T_VERT))
        fov = 36.0
    elif t < T_PLUNGE:
        d = math.exp(lerp(math.log(27.0), math.log(12.5), ease((t - T_VERT) / (T_PLUNGE - T_VERT))))
        fov = math.degrees(2 * math.atan(TAN0 / d))
    else:
        u = min(1.0, (t - T_PLUNGE) / (T_CROSS - T_PLUNGE))
        d = 1.12 + 11.4 * (1 - u) ** 1.6                   # la chute accélère
        fov = lerp(math.degrees(2 * math.atan(TAN0 / 12.5)), 100.0, ease(u))
    el = EL + (math.radians(9) * ease((t - T_PLUNGE) / 4.0) if t > T_PLUNGE else 0)
    roll = math.radians(22) * ease((t - T_PLUNGE) / 4.4) if t > T_PLUNGE else 0.0
    pos = np.array([d * math.cos(el) * math.sin(az), d * math.sin(el), -d * math.cos(el) * math.cos(az)])
    tgt = np.zeros(3)
    if t > T_PLUNGE:                                       # pendant la chute on lève les yeux vers le ciel tordu,
        u = (t - T_PLUNGE) / (T_CROSS - T_PLUNGE)          # puis on bascule face au noir au dernier moment
        look = ease(u / 0.35) * (1 - ease((u - 0.72) / 0.28))
        tgt = np.array([0.3 * d * look, 0.6 * d * look, 0.0])
    return pos, tgt, fov, roll, d


# ------------------------------------------------------------------------------------------------ l'Orbe qui tombe
_TG = np.arange(0, DUR + 0.5, 1 / 240)


def _orbe_r(t):
    """Distance au centre (unités : horizon = 1) vue par un observateur lointain : elle tend vers 1 sans l'atteindre."""
    if t < T_FALL:
        return 7.5
    s = (t - T_FALL) / 2.4
    return 1.0 + 6.5 * math.exp(-1.6 * s ** 1.5)


_ZF = np.array([math.sqrt(max(0.0, 1 - 1 / _orbe_r(t))) for t in _TG])
_TAU = np.concatenate([[0], np.cumsum(_ZF[:-1] / 240)])    # temps propre ressenti par l'Orbe (vu de loin)


def orbe_state(t):
    i = min(len(_TG) - 1, int(t * 240))
    return _orbe_r(t), _ZF[i], _TAU[i]


def orbe_dir():
    pos0, *_ = camera(T_FALL)
    u = pos0 / np.linalg.norm(pos0)
    side = np.cross(u, [0, 1, 0])
    side /= np.linalg.norm(side)
    v = u * 0.93 + side * 0.25 + np.array([0, 0.27, 0])
    return v / np.linalg.norm(v)


U_ORBE = orbe_dir()


def project(p, pos, tgt, fov, roll):
    f, r, u = R.camera_basis(pos, tgt, roll)
    d = p - pos
    z = d @ f
    if z <= 0.05:
        return None
    foc = (H / 2) / math.tan(math.radians(fov) / 2)
    return W / 2 + foc * (d @ r) / z, H / 2 - foc * (d @ u) / z, foc / z


def draw_orbe_fall(c, t, pos, tgt, fov, roll):
    if t > T_PLUNGE + 0.6:
        return
    r, zf, tau = orbe_state(t)
    if t < T_FALL:                                         # elle arrive devant la caméra puis se laisse tomber
        k = ease_out(t / 1.2)
        p = U_ORBE * (7.5 + 12 * (1 - k))
    else:
        p = U_ORBE * r
    pr = project(p, pos, tgt, fov, roll)
    if pr is None:
        return
    x, y, sc = pr
    s = sc * 0.55 / 140.0
    if s < 0.004:
        return
    a = (zf ** 1.4) * (1 - ease((t - T_PLUNGE) / 0.5))
    if a < 0.01:
        return
    g, b = zf ** 0.9, zf ** 2.2                            # décalage vers le rouge
    m = [1, 0, 0, 0, 0, 0, g, 0, 0, 0, 0, 0, b, 0, 0, 0, 0, 0, a, 0]
    expr = "surpris" if T_FALL < t < T_FALL + 1.6 else "neutre"
    e = Etat(expr=expr, age=max(0.0, tau - T_FALL) if t > T_FALL else tau, humeur_mix=1.0)
    e.cligne = False
    c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))
    c.translate(x, y)
    c.scale(s, s)
    draw_orbe(c, tau, e, parle_pulse=False)               # son temps à elle ralentit puis se fige
    c.restore()


# ------------------------------------------------------------------------------------------------ image
def filmic(x):
    """Courbe ACES (approximation de Narkowicz) puis gamma écran."""
    y = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
    return np.clip(y, 0, 1) ** (1 / 2.2)


def to_image(a):
    rgba = np.empty(a.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = (a * 255).astype(np.uint8)
    rgba[..., 3] = 255
    return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)


def frame(c, t):
    pos, tgt, fov, roll, d = camera(t)
    if t < T_CROSS + 0.05:
        lin = R.trace(RW, RH, pos, tgt, fov, t, roll, star_scale=300.0, max_steps=1100)
        exposure = 1.25
        base = to_image(filmic(lin * exposure))
        bright = to_image(filmic(np.maximum(lin * exposure - 0.9, 0) * 0.8))
        c.clear(skia.ColorBLACK)
        c.save()
        c.scale(W / RW, H / RH)
        c.drawImage(base, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
        c.restore()
        big = skia.Surface(W, H)
        bc = big.getCanvas()
        bc.clear(skia.ColorBLACK)
        bc.scale(W / RW, H / RH)
        bc.drawImage(bright, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
        bimg = big.makeImageSnapshot()
        for sig, al in ((40, 0.5), (12, 0.45)):
            blur_add(c, bimg, sig, al)
        # traînée anamorphique (objectif de cinéma) : flou très étiré horizontalement, teinté bleu
        small = skia.Surface(W // 4, H // 4)
        sc_ = small.getCanvas()
        sc_.clear(skia.ColorBLACK)
        sc_.scale(0.25, 0.25)
        sc_.drawImage(bimg, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear),
                      skia.Paint(ImageFilter=skia.ImageFilters.Blur(90, 1.2),
                                 ColorFilter=skia.ColorFilters.Matrix([0.25, 0, 0, 0, 0, 0, 0.45, 0, 0, 0,
                                                                       0, 0, 0.9, 0, 0, 0, 0, 0, 1, 0])))
        p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
        p.setAlphaf(0.6)
        c.save()
        c.scale(4, 4)
        c.drawImage(small.makeImageSnapshot(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
        c.restore()
        draw_orbe_fall(c, t, pos, tgt, fov, roll)
        # passage de l'horizon : tout se resserre dans le noir
        k = ease((t - (T_CROSS - 0.5)) / 0.55)
        if k > 0:
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * k))))
    else:
        c.clear(skia.ColorBLACK)
    post(c, t, aberration=1.4 if t < T_PLUNGE else 1.4 + 2.5 * ease((t - T_PLUNGE) / 4), grain=0.06)
    for a0, a1, s in CAPS:
        caption(c, s, win(t, a0, a1, 0.3, 0.3))
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * (1 - ease(t / 0.25))))))


# ------------------------------------------------------------------------------------------------ son
def soundtrack(path):
    n = int(DUR * S.SR) + 1                                # même longueur que S.Mix
    tt = np.arange(n) / S.SR
    mx = S.Mix(DUR)
    mx.add(0, S.air(DUR, 0.05), send=0.2)
    mx.add(0, S.chord((S.A1, S.E2, S.A2), T_CROSS + 0.4, 0.07), send=0.5)
    mx.add(0, S.sub_hit(0.35), send=0.4)
    mx.add(0.05, S.shimmer(3.0, S.A2, 0.035), send=0.8)
    # grondement du disque : bruit grave qui enfle quand on approche
    dd = np.array([camera(x)[4] for x in tt[::480]])
    prox = np.interp(tt, tt[::480], np.clip(6.0 / dd, 0, 3))
    rum = S.lowpass(np.random.default_rng(3).standard_normal((n, 2)), 160) * 6
    mx.add(0, rum * (0.02 + 0.05 * prox)[:, None] * (tt < T_CROSS)[:, None], send=0.2)
    # note de l'Orbe : sa hauteur suit le décalage vers le rouge, son volume s'éteint avec son image
    zf = np.interp(tt, _TG, _ZF)
    on = np.clip((tt - 0.5) / 0.6, 0, 1) * (tt < T_PLUNGE + 0.6)
    trem = 1 + 0.25 * np.sin(2 * np.pi * np.cumsum(5.0 * zf) / S.SR)
    tone = S.glide_tone(330.0 * zf ** 1.3, 0.05 * on * zf ** 1.1 * trem)
    mx.add(0, S.pan(S.lowpass(tone, 1500), -0.25), send=0.6)
    mx.add(T_FALL, S.whoosh(1.4, 0.07, -0.2, 0.0, 200, 700), send=0.5)
    # Shepard : la montée infinie, qui accélère pendant la plongée
    sh = S.shepard(T_CROSS - T_VERT + 0.05, rate=0.18, amp=1.0, accel=0.09)
    m = len(sh)
    env = np.minimum(1, np.arange(m) / (2.5 * S.SR)) * (0.04 + 0.08 * (np.arange(m) / m) ** 1.5)
    mx.add(T_VERT, S.pan(sh * env, 0.0), send=0.25)
    mx.add(T_PLUNGE - 0.2, S.whoosh(4.6, 0.09, 0.4, -0.4, 150, 900, seed=12), send=0.3)
    mx.add(T_PLUNGE, S.riser(4.5, 0.05), send=0.3)
    y = mx.dry + S.reverb(mx.wet, mix=1.0) * 0.6
    cut = np.clip((T_CROSS + 0.03 - tt) / 0.03, 0, 1)      # coupure nette : l'horizon avale tout, même l'écho
    y *= cut[:, None]
    after = S.Mix(DUR)
    after.add(T_CROSS + 0.75, S.heartbeat(0.3), send=0.6)
    after.add(T_CROSS + 0.75, S.sub_hit(0.16), send=0.7)
    after.add(T_CROSS + 0.9, S.shimmer(2.2, S.A1 * 2, 0.04), send=0.9)
    y = y + after.dry + S.reverb(after.wet, dur=4.0, decay=1.3, mix=1.0) * 0.6
    y *= 10 ** (-21 / 20) / (np.sqrt((y[: int(T_CROSS * S.SR)] ** 2).mean()) + 1e-9)
    lim = 10 ** (-6 / 20)
    y = lim * np.tanh(y / lim)
    y *= np.minimum(1, (len(y) - np.arange(len(y))) / (0.6 * S.SR))[:, None]
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(S.SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------------------------------------ rendu
def render(out_path):
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
                           "-preset", "medium", f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(int(DUR * FPS)):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out_path], check=True)


def stills(out_dir, times):
    os.makedirs(out_dir, exist_ok=True)
    surf = skia.Surface(W, H)
    for t in times:
        frame(surf.getCanvas(), t)
        surf.makeImageSnapshot().save(os.path.join(out_dir, f"f_{t:05.2f}.png"))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "stills":
        stills(sys.argv[2], [float(x) for x in sys.argv[3:]])
    elif len(sys.argv) > 2 and sys.argv[1] == "son":
        soundtrack(sys.argv[2])
    else:
        render(sys.argv[1] if len(sys.argv) > 1 else "output/trou_noir.mp4")
