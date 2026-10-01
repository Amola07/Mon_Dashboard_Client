"""Épisode 9 — « Le Soleil pourrait disparaître à cet instant… et tu ne remarquerais RIEN ».

Ouverture en écran partagé : en haut « EN RÉALITÉ » (le Soleil implose dès la 1re image, la dernière lumière
part, compteur 8:20), en bas « CE QUE TU VOIS » (ciel bleu, l'Orbe bronze). Puis : le trajet de la lumière,
la « photo » du Soleil vieille de 8 minutes, la disparition, la journée qui continue, le noir soudain, la gravité
qui orbite autour du vide, le ciel comme fenêtre sur le passé. La fin rejoint la première image (boucle).

    python -m films.episodes.ep09_soleil.ep09 output/ep09_soleil.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
import skia

from films import hook as HK
from films.episodes.ep01_triangle import ep01 as E1
from films.episodes.ep01_triangle.ep01 import CYAN, GOLD, PINK, VIOLET, WHITE, P, ease, lerp, pop
from films.persos.orbe import Etat, draw_orbe

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
VOIX = os.path.join(HERE, "audio", "voix.mp3")
_FD = os.path.join(os.path.dirname(os.path.dirname(HERE)), "fonts")
F_MED = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-Medium.ttf"))
F_BOLD = skia.Typeface.MakeFromFile(os.path.join(_FD, "Montserrat-ExtraBold.ttf"))

SEG = [("h1", "Le Soleil pourrait disparaître à cet instant…", 0.00, 2.32),
       ("h2", "et pendant plus de 8 minutes,", 2.89, 4.44),
       ("h3", "tu ne remarquerais absolument RIEN.", 4.68, 6.41),
       ("lum", "Tu continuerais à voir sa lumière.", 6.91, 8.54),
       ("vie", "Tu continuerais à vivre normalement.", 9.08, 10.81),
       ("ciel", "Tu pourrais même être en train de regarder le ciel…", 11.25, 13.52),
       ("plus", "sans savoir que le Soleil n'existe déjà plus.", 14.08, 16.39),
       ("raison", "Et la raison va complètement changer ta façon de regarder le ciel.", 16.88, 20.04),
       ("met", "La lumière du Soleil met environ 8 minutes et 20 secondes pour atteindre la Terre.", 20.55, 24.91),
       ("quand", "Quand tu le regardes, tu ne le vois pas tel qu'il est maintenant…", 25.48, 28.33),
       ("etait", "mais tel qu'il était il y a plus de 8 minutes.", 28.79, 30.95),
       ("imag", "Alors imaginons qu'il disparaisse…", 31.49, 33.25),
       ("maint", "exactement maintenant.", 33.74, 34.88),
       ("ici", "Ici, rien ne changerait.", 35.41, 36.83),
       ("lumin", "Le ciel resterait lumineux.", 37.34, 38.81),
       ("ois", "Les oiseaux continueraient de voler.", 39.29, 40.92),
       ("gens", "Les gens continueraient leur journée.", 41.38, 42.95),
       ("soud", "Puis, soudain…", 43.42, 44.01),
       ("dern", "la dernière lumière arriverait.", 44.48, 45.94),
       ("eteint", "Et le ciel s'éteindrait.", 46.46, 47.62),
       ("pastout", "Mais ce n'est pas tout.", 48.13, 48.88),
       ("grav", "Sa gravité, elle aussi, voyage à la vitesse de la lumière.", 49.38, 52.65),
       ("pend", "Pendant ces 8 minutes,", 53.18, 54.36),
       ("tourne", "la Terre continuerait de tourner…", 54.58, 56.25),
       ("autour", "autour d'un Soleil qui n'existe plus.", 56.52, 58.46),
       ("fasc", "Et c'est ça qui est fascinant :", 58.93, 60.23),
       ("passe", "quand tu regardes le ciel, tu regardes le passé.", 60.64, 63.30),
       ("retard", "Le Soleil a 8 minutes de retard.", 63.77, 65.49),
       ("lune", "La Lune, à peu près 1 seconde.", 66.06, 67.80),
       ("etoiles", "Et certaines étoiles que tu vois sont peut-être déjà mortes…", 68.27, 71.17),
       ("voyage", "leur dernière lumière n'a simplement pas fini son voyage.", 71.87, 74.93),
       ("proch", "Alors la prochaine fois que tu lèveras les yeux, souviens-toi :", 75.44, 78.20),
       ("fenetre", "le ciel n'est pas une fenêtre sur le présent.", 78.70, 80.88),
       ("passe2", "C'est une fenêtre sur le passé…", 81.41, 82.94),
       ("arrive", "qui est encore en train d'arriver.", 83.47, 84.92)]
_T = {k: (a, b) for k, _, a, b in SEG}


def S(k):
    return _T[k][0]


def E(k):
    return _T[k][1]


DUR = 85.6
SPLIT_END = E("raison") + 0.2                               # fin de l'écran partagé
T_IMPL2 = S("maint") + 0.05                                 # 2e disparition (« exactement maintenant »)
T_LAST = S("dern") + 0.2                                    # la dernière lumière arrive
T_BLACK = S("eteint") + 0.55                                # « s'éteindrait » : noir
T_LOOP = DUR - 0.7


def win(t, a, b, fi=0.4, fo=0.4):
    return ease((t - a) / fi) * (1 - ease((t - b) / fo))


def eo(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def text(c, s, x, y, size, col=WHITE, a=255, font=None, center=True, glow=None):
    f = skia.Font(font or F_BOLD, size)
    w = f.measureText(s)
    xx = x - w / 2 if center else x
    if glow:
        c.drawString(s, xx, y, f, P(glow, a * 0.7, blur=size * 0.25))
    c.drawString(s, xx, y, f, P((8, 6, 22), a, stroke=max(4, size * 0.09)))
    c.drawString(s, xx, y, f, P(col, a))


def orbe(c, t, x, y, s, expr="neutre", age=1.0, regard=(0, 0), alpha=255, cligne=None, tint=None):
    if alpha <= 1 or s <= 0.005:
        return
    e = Etat(expr=expr, age=age, regard=regard, humeur_mix=1.0)
    e.cligne = ((t % 3.9) < 0.1) if cligne is None else cligne
    if tint is not None:                                    # éclairage (nuit : bleu froid, assombri)
        r, g, b = tint
        m = [r, 0, 0, 0, 0, 0, g, 0, 0, 0, 0, 0, b, 0, 0, 0, 0, 0, alpha / 255, 0]
        c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))
    else:
        c.saveLayerAlpha(None, int(alpha))
    c.translate(x, y)
    c.scale(s, s)
    draw_orbe(c, t, e)
    c.restore()


_rng = np.random.default_rng(9)
STARS = np.stack([_rng.uniform(0, W, 260), _rng.uniform(0, H, 260), _rng.uniform(0.8, 2.6, 260),
                  _rng.uniform(0, 6.3, 260)], 1)


def stars(c, t, a, y0=0, y1=H):
    if a <= 0.01:
        return
    for x, y, r, ph in STARS:
        if y0 <= y <= y1:
            c.drawCircle(x, y, r, P(WHITE, a * (110 + 90 * math.sin(t * 1.4 + ph))))


def sun(c, x, y, r, t, a=1.0, warm=1.0):
    """Le Soleil dans le style de l'Orbe : disque doré, couronne qui respire, rayons lents."""
    if a <= 0.01 or r <= 0.5:
        return
    c.drawCircle(x, y, r * 2.4, P((255, 170, 60), 70 * a * warm, blur=r * 0.9))
    c.drawCircle(x, y, r * 1.45, P((255, 210, 110), 120 * a, blur=r * 0.35))
    for k in range(12):
        ang = t * 0.25 + k * math.pi / 6
        l1, l2 = r * 1.15, r * (1.55 + 0.12 * math.sin(t * 2 + k))
        c.drawLine(x + l1 * math.cos(ang), y + l1 * math.sin(ang), x + l2 * math.cos(ang), y + l2 * math.sin(ang),
                   P((255, 220, 140), 150 * a, stroke=max(2, r * 0.07)))
    sh = skia.GradientShader.MakeRadial(skia.Point(x - r * 0.3, y - r * 0.3), r * 1.3,
                                        [skia.Color(255, 250, 220, int(255 * a)), skia.Color(255, 200, 80, int(255 * a)),
                                         skia.Color(255, 140, 40, int(255 * a))], [0.0, 0.55, 1.0])
    c.drawCircle(x, y, r, P(shader=sh))


def implode(c, x, y, r, u):
    """u ∈ [0, 1] : le Soleil se contracte en un point, flash, onde de choc. Renvoie le rayon restant."""
    rr = r * (1 - eo(u / 0.55))
    if u > 0.45:
        k = (u - 0.45) / 0.55
        c.drawCircle(x, y, r * (0.2 + 2.6 * eo(k)), P((255, 230, 180), 230 * (1 - k), stroke=10 * (1 - k) + 2))
        c.drawCircle(x, y, r * 1.2 * (1 - k) + 6, P(WHITE, 255 * (1 - k), blur=20))
    return rr


def countdown(t, t0, t1):
    """Secondes restantes sur 8:20 (500 s) entre t0 et t1, temps accéléré."""
    u = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
    return 500 * (1 - u)


def draw_timer(c, x, y, secs, a, size=96, col=WHITE):
    s = int(math.ceil(secs))
    text(c, f"{s // 60}:{s % 60:02d}", x, y, size, col, a, glow=(255, 120, 90) if s < 60 else (255, 200, 120))


# ------------------------------------------------------------------------------------------------ décor « surface »
GROUND = (0.33, 0.44)                                      # hauteur du sol (bords, sommet) en part de la hauteur


def ground_y(top, bottom):
    return bottom - (bottom - top) * (GROUND[0] + GROUND[1]) / 2 - 6


BIRDS = [(_rng.uniform(-200, 1000), _rng.uniform(0.2, 0.55), _rng.uniform(70, 140), _rng.uniform(0, 6)) for _ in range(7)]


def surface(c, t, top, bottom, day=1.0, sun_xy=None, sun_r=95, birds=0.0, walkers=0.0):
    """Ciel + sol vus depuis la Terre, entre top et bottom (y écran). day : 1 = plein jour, 0 = nuit noire."""
    h = bottom - top
    c.save()
    c.clipRect(skia.Rect(0, top, W, bottom))
    sky_day = [skia.Color(70, 140, 235), skia.Color(150, 190, 245), skia.Color(255, 205, 170)]
    sky_night = [skia.Color(4, 4, 14), skia.Color(10, 8, 30), skia.Color(22, 14, 44)]
    cols = [skia.Color(*[int(lerp(getattr(skia, "ColorGet" + ch)(n), getattr(skia, "ColorGet" + ch)(d), day))
                         for ch in ("R", "G", "B")]) for d, n in zip(sky_day, sky_night)]
    c.drawRect(skia.Rect(0, top, W, bottom), P(shader=skia.GradientShader.MakeLinear(
        [skia.Point(0, top), skia.Point(0, bottom - h * 0.2)], cols)))
    stars(c, t, 1 - day, top, bottom - h * 0.25)
    if sun_xy and day > 0.01:
        sun(c, sun_xy[0], sun_xy[1], sun_r, t, day)
    for x0, fy, sp, ph in BIRDS:                            # oiseaux : de petits « v » qui battent des ailes
        if birds <= 0.01:
            break
        x = (x0 + sp * t) % 1300 - 110
        y = top + h * fy + 12 * math.sin(t * 1.3 + ph)
        flap = 10 * math.sin(t * 9 + ph)
        path = skia.Path()
        path.moveTo(x - 22, y - flap)
        path.quadTo(x - 10, y - 6, x, y + 2)
        path.quadTo(x + 10, y - 6, x + 22, y - flap)
        c.drawPath(path, P((40, 30, 70), 230 * birds, stroke=4))
    # sol : une colline arrondie (la courbure de la Terre), bord éclairé
    g = skia.Path()
    g.moveTo(-50, bottom)
    g.lineTo(-50, bottom - h * GROUND[0])
    g.quadTo(W / 2, bottom - h * GROUND[1], W + 50, bottom - h * GROUND[0])
    g.lineTo(W + 50, bottom)
    g.close()
    gc = (int(lerp(18, 70, day)), int(lerp(14, 50, day)), int(lerp(36, 110, day)))
    c.drawPath(g, P(gc))
    c.drawPath(g, P((255, 200, 160) if day > 0.5 else (120, 140, 255), 110 * max(day, 0.4), stroke=4))
    for k in range(4):                                      # passants : de petites Orbes qui traversent
        if walkers <= 0.01:
            break
        x = (k * 340 + 90 * t) % 1400 - 160
        y = ground_y(top, bottom) - 30 + 6 * abs(math.sin(t * 6 + k))
        orbe(c, t + k, x, y, 0.22, "joie" if k % 2 else "neutre", regard=(1, 0), alpha=255 * walkers)
    c.restore()


# ------------------------------------------------------------------------------------------------ scènes
def scene_split(c, t):
    a = 1 - ease((t - (SPLIT_END - 0.5)) / 0.5)
    if t > SPLIT_END or a <= 0.01:
        return
    c.saveLayerAlpha(None, int(255 * a))
    # --- en haut : la réalité (espace)
    c.save()
    c.clipRect(skia.Rect(0, 0, W, 900))
    c.drawRect(skia.Rect(0, 0, W, 900), P((6, 4, 18)))
    stars(c, t, 1.0, 0, 900)
    sx, sy, sr = 540, 330, 135
    u = (t + 0.12) / 0.75                                  # déjà en train d'imploser à la 1re image
    rr = implode(c, sx, sy, sr, u) if u < 1 else 0
    if u < 0.55:
        sun(c, sx, sy, max(rr, 1), t)
    if t > 0.6:                                             # là où était le Soleil : un vide cerclé
        k = ease((t - 0.6) / 0.5)
        c.drawCircle(sx, sy, sr, P((255, 120, 110), 120 * k, stroke=3))
        if t > S("plus"):
            text(c, "?", sx, sy + 34, 96, (255, 140, 130), 255 * ease((t - S("plus")) / 0.3), font=F_BOLD)
        # la dernière lumière part vers la Terre (un front lumineux)
        rf = 30 + 470 * (t - 0.6) / (44.5 - 0.6)
        c.drawCircle(sx, sy, rf, P((255, 220, 150), 170 * k, stroke=5))
        c.drawCircle(sx, sy, rf, P((255, 200, 120), 90 * k, stroke=26, blur=14))
    c.drawCircle(540, 830, 42, P((70, 140, 255)))           # la Terre, en bas du panneau
    c.drawCircle(540, 830, 42, P((180, 220, 255), 200, stroke=3))
    draw_timer(c, 540, 140, countdown(t, 0.0, 44.5), 255)
    text(c, "EN RÉALITÉ", 40, 880, 34, (255, 150, 140), 230, font=F_BOLD, center=False)
    c.restore()
    # --- en bas : ce que tu vois (ciel bleu, l'Orbe au soleil)
    surface(c, t, 900, H, day=1.0, sun_xy=(820, 1090), sun_r=80, birds=1.0, walkers=ease((t - S("vie")) / 0.5))
    text(c, "CE QUE TU VOIS", 40, 960, 34, (255, 255, 255), 230, font=F_BOLD, center=False)
    c.drawRect(skia.Rect(0, 896, W, 904), P((255, 230, 200), 230))
    # l'Orbe : allongée au soleil, puis elle se lève, puis elle regarde le ciel
    up = ease((t - S("ciel")) / 0.6)
    look = (0.7, -0.75) if t > S("ciel") else (0, 0)
    expr = "joie" if t < S("ciel") else "neutre"
    oy0 = ground_y(900, H) - 0.7 * 140
    ox, oy = 380, lerp(oy0 + 25, oy0, ease((t - S("vie")) / 0.5)) - 12 * abs(math.sin(t * 3)) * ease((t - S("vie")) / 0.5) * (1 - up)
    orbe(c, t, ox, oy, 0.7, expr, age=t, regard=look, cligne=(t < S("vie")) or None)
    if t < S("vie"):                                        # « zzz » de la sieste au soleil
        for k in range(3):
            ph = (t * 0.6 + k / 3) % 1
            text(c, "z", ox + 90 + 40 * ph, oy - 120 - 120 * ph, 34 + 16 * k, WHITE, 200 * math.sin(math.pi * ph),
                 font=F_MED)
    c.restore()


SUN_D, EARTH_D = (300, 520), (790, 1290)


def light_path(u):
    return lerp(SUN_D[0], EARTH_D[0], u), lerp(SUN_D[1], EARTH_D[1], u)


def scene_space(c, t):
    """Le trajet de la lumière, la « photo » vieille de 8 min, puis la 2e disparition."""
    a = win(t, SPLIT_END - 0.5, S("ici") - 0.3, 0.6, 0.4)
    if a <= 0.01:
        return
    c.saveLayerAlpha(None, int(255 * a))
    E1.draw_background(c, t)
    stars(c, t, 0.7)
    # pointillés du trajet
    for k in range(40):
        x, y = light_path(k / 40)
        c.drawCircle(x, y, 3, P(WHITE, 60))
    alive = t < T_IMPL2
    if alive:
        sun(c, *SUN_D, 110, t)
    else:
        rr = implode(c, *SUN_D, 110, (t - T_IMPL2) / 0.75)
        if rr > 1:
            sun(c, *SUN_D, rr, t)
        c.drawCircle(*SUN_D, 110, P((255, 120, 110), 140 * ease((t - T_IMPL2 - 0.6) / 0.4), stroke=3))
    c.drawCircle(*EARTH_D, 52, P((70, 140, 255)))
    c.drawCircle(*EARTH_D, 52, P((180, 220, 255), 220, stroke=3))
    orbe(c, t, EARTH_D[0] - 6, EARTH_D[1] - 82, 0.26, "neutre", regard=(-0.7, -0.6))
    # « met 8 minutes 20 » : un photon voyage, chrono qui défile à côté
    if S("met") - 0.2 <= t < S("imag"):
        u = min(1.0, max(0.0, (t - S("met")) / (E("met") - S("met"))))
        x, y = light_path(u)
        for k in range(10):
            xx, yy = light_path(max(0, u - k * 0.012))
            c.drawCircle(xx, yy, 14 - k, P((255, 230, 150), 200 - 18 * k, blur=4))
        secs = 500 * u
        text(c, f"{int(secs) // 60} min {int(secs) % 60:02d} s", 540, 300, 72, GOLD,
             255 * win(t, S("met"), S("quand") - 0.2, 0.3, 0.3))
    # « tel qu'il était il y a 8 minutes » : une carte-photo du Soleil voyage vers l'Orbe
    if S("quand") <= t < S("imag") + 0.5:
        u = ease((t - S("quand")) / 3.0)
        x, y = light_path(0.15 + 0.7 * u)
        al = 255 * win(t, S("quand"), S("imag"), 0.3, 0.4)
        c.save()
        c.translate(x, y - 40)
        c.rotate(-8 + 6 * math.sin(t))
        c.drawRoundRect(skia.Rect(-110, -130, 110, 130), 14, 14, P((250, 245, 235), al))
        c.drawRect(skia.Rect(-92, -112, 92, 60), P((30, 24, 60), al))
        sun(c, 0, -26, 48, t, al / 255)
        text(c, "il y a 8 min", 0, 106, 30, (60, 40, 110), al, font=F_BOLD)
        c.restore()
        if t > S("etait"):
            text(c, "TEL QU'IL ÉTAIT", 540, 300, 64, PINK, 255 * win(t, S("etait"), S("imag"), 0.3, 0.3))
    # 2e disparition : nouveau compte à rebours
    if t > T_IMPL2:
        draw_timer(c, 540, 300, countdown(t, T_IMPL2, T_LAST), 255 * ease((t - T_IMPL2) / 0.2), 110)
    c.restore()


def scene_day(c, t):
    """« Ici, rien ne changerait » : la journée continue sous un Soleil qui n'existe plus ; puis le noir."""
    if not (S("ici") - 0.6 <= t < T_BLACK + 3.0):
        return
    a = ease((t - (S("ici") - 0.6)) / 0.5) * (1 - ease((t - (S("pastout") + 0.3)) / 0.5))
    if a <= 0.01:
        return
    c.saveLayerAlpha(None, int(255 * a))
    day = 1.0 if t < T_BLACK else 0.0
    flick = 0.0
    if T_LAST <= t < T_BLACK:                               # le Soleil vacille juste avant
        flick = 0.35 * (0.5 + 0.5 * math.sin(t * 40)) * ease((t - T_LAST) / 0.8)
    surface(c, t, 0, H, day=day * (1 - flick * 0.5), sun_xy=(760, 520), sun_r=120,
            birds=ease((t - S("ois")) / 0.4) * day, walkers=ease((t - S("gens")) / 0.4) * day)
    secs = countdown(t, T_IMPL2, T_LAST)
    if t < T_BLACK:
        draw_timer(c, 540, 200, secs, 255, 110, (255, 120, 110) if secs < 60 else WHITE)
        # barre : la dernière lumière approche
        u = 1 - secs / 500
        c.drawRoundRect(skia.Rect(140, 250, 940, 266), 8, 8, P(WHITE, 60))
        c.drawRoundRect(skia.Rect(140, 250, 140 + 800 * u, 266), 8, 8, P((255, 200, 120), 230))
    expr = "joie" if t < T_LAST else ("surpris" if t < T_BLACK + 1.5 else "neutre")
    tint = None if t < T_BLACK else (0.45, 0.5, 0.85)
    orbe(c, t, 380, ground_y(0, H) - 0.8 * 140 - 10 * abs(math.sin(t * 2.5)) * (t < T_LAST), 0.8, expr, age=t - T_BLACK if t > T_BLACK else t,
         regard=(0.6, -0.7) if t > T_LAST else (0.3, 0), tint=tint)
    if t >= T_BLACK:                                        # « !» quand tout s'éteint
        k = t - (S("pastout"))
        if 0 <= k < 1.0:
            c.save()
            c.translate(500, 1300)
            sc = pop(k) * 1.3
            c.scale(sc, sc)
            c.drawCircle(0, 0, 46, P(WHITE, 230))
            text(c, "!", 0, 22, 64, (60, 40, 110), 255)
            c.restore()
    c.restore()


def scene_grav(c, t):
    """La gravité voyage elle aussi ; la Terre continue de tourner autour du vide."""
    a = win(t, S("pastout") + 0.3, S("fasc") - 0.2, 0.5, 0.5)
    if a <= 0.01:
        return
    c.saveLayerAlpha(None, int(255 * a))
    E1.draw_background(c, t)
    stars(c, t, 0.7)
    cx, cy, R = 540, 900, 380
    c.drawCircle(cx, cy, 110, P((255, 120, 110), 130, stroke=3))           # le vide où était le Soleil
    text(c, "?", cx, cy + 34, 96, (255, 140, 130), 200)
    for k in range(4):                                                     # ondes de gravité = vitesse lumière
        if t < S("grav"):
            break
        r = ((t - S("grav")) * 160 + k * 120) % 520
        c.drawCircle(cx, cy, r + 110, P(CYAN, 140 * (1 - r / 520), stroke=4))
    # orbite pointillée, la Terre la suit autour de rien
    for k in range(60):
        ang = k / 60 * 2 * math.pi
        c.drawCircle(cx + R * math.cos(ang), cy + R * math.sin(ang), 3, P(WHITE, 70))
    ang = -math.pi / 2 + 0.35 * (t - S("pastout"))
    ex, ey = cx + R * math.cos(ang), cy + R * math.sin(ang)
    c.drawCircle(ex, ey, 46, P((70, 140, 255)))
    c.drawCircle(ex, ey, 46, P((180, 220, 255), 220, stroke=3))
    orbe(c, t, ex, ey - 72, 0.24, "reflechit" if t > S("autour") else "neutre", age=t - S("autour"),
         regard=(-(ex - cx) / R, -(ey - cy) / R))
    if t > S("pend"):
        text(c, "8 MIN", 540, 330, 96, GOLD, 255 * win(t, S("pend"), S("fasc"), 0.3, 0.4), glow=(255, 160, 80))
    c.restore()


SKY_TAGS = [("retard", (300, 420), "−8 min", "soleil"), ("lune", (800, 330), "−1 s", "lune"),
            ("etoiles", (220, 760), "−600 ans", "etoile"), ("etoiles", (760, 640), "−2 000 ans", "etoile"),
            ("etoiles", (560, 220), "−4 000 ans", "morte")]


def scene_past(c, t):
    """Nuit : le ciel comme fenêtre sur le passé (étiquettes d'âge, étoile peut-être morte, fenêtre)."""
    a = win(t, S("fasc") - 0.4, DUR + 1, 0.6, 0.4)
    if a <= 0.01:
        return
    c.saveLayerAlpha(None, int(255 * a))
    surface(c, t, 0, H, day=0.0)
    for key, (x, y), lab, kind in SKY_TAGS:
        if t < S(key):
            continue
        k = ease((t - S(key)) / 0.4)
        if kind == "soleil":
            sun(c, x, y, 46, t, 0.9 * k)
        elif kind == "lune":
            c.drawCircle(x, y, 44, P((230, 230, 245), 255 * k))
            c.drawCircle(x + 14, y - 10, 38, P((10, 8, 30), 255 * k))      # croissant
        else:
            dead = kind == "morte" and t > S("etoiles") + 1.6
            r = 9 + 3 * math.sin(t * 3)
            c.drawCircle(x, y, r * 3, P((255, 230, 200), 90 * k, blur=12))
            c.drawCircle(x, y, r, P(WHITE, 255 * k))
            if dead:                                                        # « peut-être déjà morte » : un fantôme
                kk = ease((t - S("etoiles") - 1.6) / 0.5)
                c.drawCircle(x, y - 70, 26, P((255, 120, 110), 200 * kk, stroke=3))
                text(c, "†", x, y - 56, 40, (255, 140, 130), 230 * kk, font=F_BOLD)
                if t > S("voyage"):                                         # sa lumière voyage encore vers l'Orbe
                    u = ((t - S("voyage")) * 0.35) % 1
                    px, py = lerp(x, 400, u), lerp(y, 1380, u)
                    c.drawCircle(px, py, 10, P((255, 230, 180), 230, blur=3))
        text(c, lab, x, y + (90 if kind == "soleil" else 64), 40, GOLD if kind != "morte" else (255, 150, 140),
             255 * k)
    # la fenêtre : « pas sur le présent » → « sur le passé »
    if t > S("fenetre") - 0.2:
        k = ease((t - (S("fenetre") - 0.2)) / 0.5)
        r = skia.Rect(150, 160, 930, 1060)
        c.drawRoundRect(r, 30, 30, P(WHITE, 200 * k, stroke=10))
        c.drawLine(540, 160, 540, 1060, P(WHITE, 140 * k, stroke=6))
        c.drawLine(150, 610, 930, 610, P(WHITE, 140 * k, stroke=6))
        if t < S("passe2"):
            text(c, "PRÉSENT", 540, 1150, 72, WHITE, 255 * k)
            if t > S("fenetre") + 1.0:
                kk = ease((t - S("fenetre") - 1.0) / 0.3)
                c.drawLine(330, 1125, 330 + 420 * kk, 1125, P((255, 90, 90), 255, stroke=10))
        else:
            text(c, "PASSÉ", 540, 1150, 84, GOLD, 255 * ease((t - S("passe2")) / 0.3), glow=(255, 170, 80))
    # l'Orbe regarde le ciel
    expr = "surpris" if S("etoiles") + 1.6 < t < S("voyage") + 0.8 else ("reflechit" if t < S("passe2") else "neutre")
    orbe(c, t, 400, ground_y(0, H) - 0.8 * 140, 0.8, expr, age=t - S("etoiles") - 1.6, regard=(0.2, -0.85), tint=(0.5, 0.55, 0.9))
    if t > S("arrive"):                                                     # une lumière lui arrive dans l'œil
        u = ease((t - S("arrive")) / 1.2)
        px, py = lerp(560, 410, u), lerp(220, 1390, u)
        c.drawCircle(px, py, 12, P((255, 240, 200), 255 * (1 - 0.3 * u), blur=3))
        if u >= 1:
            c.drawCircle(410, 1390, 60, P((255, 230, 180), 140, blur=20))
    c.restore()


def scene_loop(c, t):
    """Fin : on revient à la toute première image (le Soleil intact au-dessus de l'écran partagé) → boucle."""
    if t < T_LOOP:
        return
    k = ease((t - T_LOOP) / 0.6)
    c.saveLayerAlpha(None, int(255 * k))
    scene_split(c, 0.0)
    c.restore()


def frame(c, t):
    c.clear(skia.ColorBLACK)
    scene_split(c, t)
    scene_space(c, t)
    scene_day(c, t)
    scene_grav(c, t)
    scene_past(c, t)
    scene_loop(c, t)
    if t < T_LOOP:
        E1.TIMING = [(txt, a, b) for _, txt, a, b in SEG]
        E1.draw_subtitle(c, t)
    if S("imag") - 0.3 < t < S("ici") + 1:                  # mention honnête
        text(c, "Expérience de pensée", 540, 1580, 30, (220, 210, 240), 180 * win(t, S("imag"), S("ici"), 0.3, 0.3),
             font=F_MED)


# ------------------------------------------------------------------------------------------------ son
SR = E1.SR


def soundtrack(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOIX, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    voice = np.frombuffer(raw, np.int16).astype(float) / 32768
    n = int(DUR * SR)
    mix = np.zeros(n)
    mix[:min(n, len(voice))] += voice[:n]
    fx = np.zeros(n)

    def add(t, s_, g=1.0):
        i = int(t * SR)
        m = min(n - i, len(s_))
        if m > 0:
            fx[i:i + m] += s_[:m] * g

    add(0.0, HK.sub_drop(0.45))                             # implosion à la 1re image
    add(0.02, E1.swish(0.6, 0.14))
    for k in range(int(SPLIT_END)):                         # tic-tac grave du compte à rebours
        add(0.5 + k, E1.tock(0.05))
    add(S("lum"), E1.sparkle(0.08))
    add(S("plus"), E1.swell(0.14))
    add(S("raison") + 2.6, E1.swish(0.9, 0.1))
    add(S("met"), E1.swish(4.0, 0.06))
    add(E("met") - 0.1, E1.ding(660, 0.1))
    add(S("quand"), E1.pop_s(480, 0.12))
    add(S("etait"), E1.ding(523, 0.1))
    add(T_IMPL2, HK.sub_drop(0.4))
    add(T_IMPL2, E1.swish(0.6, 0.12))
    for k in range(int((T_LAST - T_IMPL2) * 2)):            # le compte à rebours s'accélère
        add(T_IMPL2 + 0.5 * k, E1.tock(0.04 + 0.03 * k / 20))
    add(S("ois"), E1.chirp(1800, 2400, 0.12, 0.04))
    add(S("ois") + 0.3, E1.chirp(2000, 2600, 0.1, 0.03))
    add(S("soud"), E1.swell(0.2))
    add(T_BLACK, HK.sub_drop(0.5))
    add(S("pastout"), E1.pop_s(560, 0.12))
    for k in range(4):
        add(S("grav") + 0.75 * k, E1.swish(0.7, 0.05))
    add(S("autour"), E1.swell(0.12))
    add(S("passe"), E1.sparkle(0.1))
    for key in ("retard", "lune"):
        add(S(key), E1.ding(587, 0.08))
    add(S("etoiles") + 1.6, E1.ding(392, 0.1))
    add(S("fenetre") + 1.0, E1.swish(0.4, 0.08))
    add(S("passe2"), E1.ding(784, 0.12))
    add(S("passe2") + 0.05, E1.swell(0.14))
    add(S("arrive") + 1.2, E1.sparkle(0.12))
    add(T_LOOP, HK.sub_drop(0.25))
    mus = E1.music(DUR)
    env = np.convolve(np.abs(mix), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
    duck = 1 - 0.55 * np.minimum(1, env / 0.05)
    tt = np.arange(n) / SR
    hole = 1 - (1 - np.clip(np.abs(tt - (T_BLACK + 0.3)) / 0.35, 0, 1))       # silence de la musique au noir
    out_ = mix + E1.soften(fx, 6) * 0.8 + mus * duck * hole
    fade = np.ones(n)
    k = int(0.6 * SR)
    fade[-k:] = np.linspace(1, 0, k)
    out_ = np.tanh(out_ * fade * 1.3) / np.tanh(1.3)
    st = np.stack([out_, out_], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------------------------------------ rendu
def _chunk(args):
    f0, f1, path = args
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", path],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for f in range(f0, f1):
        frame(surf.getCanvas(), f / FPS)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def render(out_path, procs=4):
    from multiprocessing import Pool
    tmp = tempfile.mkdtemp()
    n = int(DUR * FPS)
    k = procs * 3
    jobs = [(i * n // k, (i + 1) * n // k, f"{tmp}/c{i:02d}.mp4") for i in range(k)]
    with Pool(procs) as p:
        parts = p.map(_chunk, jobs)
    with open(f"{tmp}/list.txt", "w") as f:
        f.writelines(f"file '{q}'\n" for q in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy",
                    f"{tmp}/v.mp4"], check=True)
    soundtrack(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)


def stills(out_dir, times):
    os.makedirs(out_dir, exist_ok=True)
    surf = skia.Surface(W, H)
    for t in times:
        frame(surf.getCanvas(), t)
        surf.makeImageSnapshot().save(os.path.join(out_dir, f"e_{t:05.2f}.png"))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "stills":
        stills(sys.argv[2], [float(x) for x in sys.argv[3:]])
    else:
        render(sys.argv[1] if len(sys.argv) > 1 else "output/ep09_soleil.mp4")
