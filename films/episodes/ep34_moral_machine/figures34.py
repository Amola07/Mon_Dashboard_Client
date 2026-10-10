"""Figures réalistes de l'épisode 34 (pixel bleu) : humains, chien, chat, poussette, voitures (profil et dessus).

Principes : vraies proportions (7,5 têtes pour un adulte, 4,5 pour un enfant), dos voûté et canne chez les âgés,
ombrage en trois tons avec une seule lumière (en haut à gauche), contour sombre d'un pixel, visages lisibles (œil,
sourcil, nez, bouche, oreille), cheveux en volume avec reflet, vêtements avec plis, col, ceinture, semelles.
Les figures se dessinent sur un calque RGBA puis sont posées sur l'image (miroir possible).
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from films.styles import pixel_bleu as P
from films.styles.pixel_bleu import B0, B1, B2, B3, B4, BLANC, GRIS, GRIS_F, NOIR, ROUGE, ROUGE_F

CONTOUR = (4, 8, 22)
PEAU = ((214, 228, 252), (160, 182, 226), (240, 246, 255))          # base, ombre, lumière
CHEVEUX = {"brun": ((40, 34, 44), (22, 18, 28), (84, 70, 78)), "noir": ((18, 22, 40), (8, 10, 22), (52, 62, 96)),
           "chatain": ((92, 70, 58), (58, 44, 38), (140, 112, 92)), "blanc": ((206, 214, 230), (150, 160, 182), (246, 248, 255)),
           "blond": ((196, 170, 110), (140, 118, 76), (236, 214, 160))}


def teinte(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def tons(c):
    """Base, ombre, lumière d'une couleur de tissu."""
    return c, teinte(c, 0.62), tuple(min(255, int(v * 1.25) + 18) for v in c)


TENUES = {
    "pull": {"haut": tons(B2), "bas": tons((22, 40, 82)), "chaussures": (30, 34, 48)},
    "gris": {"haut": tons((128, 138, 160)), "bas": tons(B1), "chaussures": (36, 30, 34)},
    "clair": {"haut": tons(B3), "bas": tons((70, 80, 102)), "chaussures": (40, 36, 40)},
    "costume": {"haut": tons((46, 58, 92)), "bas": tons((46, 58, 92)), "chaussures": (14, 14, 20), "chemise": True},
    "robe": {"haut": tons((120, 170, 236)), "bas": tons((120, 170, 236)), "chaussures": (60, 40, 50), "robe": True},
    "vieux": {"haut": tons((112, 104, 120)), "bas": tons((60, 66, 88)), "chaussures": (40, 32, 30)},
    "vieille": {"haut": tons((150, 130, 160)), "bas": tons((150, 130, 160)), "chaussures": (50, 40, 40), "robe": True},
    "sport": {"haut": tons(ROUGE), "bas": tons((24, 30, 52)), "chaussures": (220, 226, 240)},
    "raye": {"haut": tons((200, 206, 220)), "bas": tons((40, 44, 60)), "chaussures": (20, 20, 26), "rayures": True},
    "enfant_f": {"haut": tons((236, 120, 140)), "bas": tons((236, 120, 140)), "chaussures": (60, 40, 70), "robe": True},
    "enfant_g": {"haut": tons((90, 190, 160)), "bas": tons((30, 50, 96)), "chaussures": (240, 240, 250)},
}


def _poly(d, pts, col):
    d.polygon([(round(x), round(y)) for x, y in pts], fill=col)


def _segment(d, p, q, w0, w1, cols, lumiere=True):
    """Un membre fuselé : base, ombre sur le côté droit (dos de la lumière), liseré de lumière à gauche."""
    base, ombre, clair = cols
    a = math.atan2(q[1] - p[1], q[0] - p[0])
    nx, ny = -math.sin(a), math.cos(a)
    pts = [(p[0] + nx * w0 / 2, p[1] + ny * w0 / 2), (q[0] + nx * w1 / 2, q[1] + ny * w1 / 2),
           (q[0] - nx * w1 / 2, q[1] - ny * w1 / 2), (p[0] - nx * w0 / 2, p[1] - ny * w0 / 2)]
    _poly(d, pts, base)
    for (x, y), w in ((p, w0), (q, w1)):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=base)
    # l'ombre du côté opposé à la lumière (lumière en haut à gauche → ombre côté droit / bas)
    sgn = 1 if nx > 0 or (nx == 0 and ny > 0) else -1
    k0, k1 = w0 * 0.22, w1 * 0.22
    _poly(d, [(p[0] + sgn * nx * w0 / 2, p[1] + sgn * ny * w0 / 2), (q[0] + sgn * nx * w1 / 2, q[1] + sgn * ny * w1 / 2),
              (q[0] + sgn * nx * (w1 / 2 - k1 * 1.6), q[1] + sgn * ny * (w1 / 2 - k1 * 1.6)),
              (p[0] + sgn * nx * (w0 / 2 - k0 * 1.6), p[1] + sgn * ny * (w0 / 2 - k0 * 1.6))], ombre)
    if lumiere and w0 >= 3:
        d.line([(p[0] - sgn * nx * (w0 / 2 - 1), p[1] - sgn * ny * (w0 / 2 - 1)),
                (q[0] - sgn * nx * (w1 / 2 - 1), q[1] - sgn * ny * (w1 / 2 - 1))], fill=clair)


def _ik(a, cible, l1, l2, sens=1):
    return P._ik(a, cible, l1, l2, sens)


ECHELLE = 1.25                                                     # les figures réalistes, à l'échelle des scènes


def humain(img, pieds, taille=90, tenue="pull", age="adulte", sexe="h", cheveux="brun", miroir=False,
           marche=None, mains=None, tronc=0.0, flexion=0.0, assis=False, enceinte=False, corpulence=1.0,
           canne=False, regard=0.0, bouche="neutre", masque=False):
    """Un humain de profil (vers la droite), pieds au point `pieds`. taille = hauteur totale en pixels.
    age : adulte, enfant, vieux ; mains : point visé par les mains (sinon bras naturels) ; marche : phase."""
    T_ = TENUES[tenue]
    enfant, vieux = age == "enfant", age == "vieux"
    H = taille * ECHELLE
    tete_h = H / (4.6 if enfant else 7.4)
    L = int(H * 2.4) + 20
    cal = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(cal)
    px, py = L / 2, L * 0.8                                        # les pieds dans le calque
    jambe = H * (0.40 if enfant else 0.47)
    cuisse, tibia = jambe * 0.52, jambe * 0.48
    buste = H * (0.30 if enfant else 0.30) - (H * 0.03 if vieux else 0)
    bras1, bras2 = H * (0.17 if enfant else 0.18), H * (0.16 if enfant else 0.17)
    larg_ep = H * (0.13 if sexe == "h" else 0.115) * (0.8 if enfant else 1) * corpulence
    larg_ha = H * (0.11 if sexe == "h" else 0.125) * corpulence
    if vieux:
        flexion = max(flexion, 0.18)
        tronc = tronc + 16
    # le bassin et les pieds
    if assis:
        hanche = (px - cuisse * 0.9, py - tibia * 1.02)
        pied_av, pied_ar = (px + 2, py), (px - 3, py)
    elif marche is not None:
        ph = marche
        pas = H * 0.15
        hanche = (px, py - jambe * (0.95 + 0.03 * abs(math.cos(ph))))
        pied_av = (px + pas * math.sin(ph), py - H * 0.07 * max(0.0, math.cos(ph)))
        pied_ar = (px - pas * math.sin(ph), py - H * 0.07 * max(0.0, -math.cos(ph)))
        tronc += 4
    else:
        hanche = (px - H * 0.06 * flexion, py - jambe * (0.985 - 0.16 * flexion))
        pied_av, pied_ar = (px + H * 0.06, py), (px - H * 0.07, py)
    a = math.radians(tronc)
    epaule = (hanche[0] + buste * math.sin(a), hanche[1] - buste * math.cos(a))
    cou_h = H * 0.035
    cou = (epaule[0] + cou_h * math.sin(a) * (1.6 if vieux else 1), epaule[1] - cou_h * math.cos(a))
    ta = a * (0.4 if vieux else 1) + math.radians(regard)
    tc = (cou[0] + tete_h * 0.5 * math.sin(ta) + (H * 0.02 if vieux else 0), cou[1] - tete_h * 0.5 * math.cos(ta))
    # les mains
    if mains is None:
        if marche is not None:
            bal = H * 0.08 * math.sin(-marche)
            main_av = (epaule[0] + H * 0.03 + bal, epaule[1] + (bras1 + bras2) * 0.96)
            main_ar = (epaule[0] - H * 0.01 - bal, epaule[1] + (bras1 + bras2) * 0.96)
        elif canne:
            main_av = (epaule[0] + H * 0.16, epaule[1] + (bras1 + bras2) * 0.75)
            main_ar = (epaule[0] + H * 0.02, epaule[1] + (bras1 + bras2) * 0.92)
        elif enceinte:
            main_av = (hanche[0] + H * 0.13, hanche[1] - H * 0.06)
            main_ar = (hanche[0] + H * 0.06, hanche[1] - H * 0.13)
        else:
            main_av = (epaule[0] + H * 0.025, epaule[1] + (bras1 + bras2) * 0.97)
            main_ar = (epaule[0] - H * 0.005, epaule[1] + (bras1 + bras2) * 0.97)
    else:
        mx, my = mains[0] - pieds[0] + px, mains[1] - pieds[1] + py
        main_av, main_ar = (mx, my), (mx - H * 0.03, my + H * 0.02)
    haut, bas = T_["haut"], T_["bas"]
    sombre = lambda c: tuple(teinte(x, 0.72) for x in c)
    cuisse_w, mollet_w = H * 0.085 * corpulence, H * 0.06 * corpulence
    bras_w, avbras_w = H * 0.065 * corpulence, H * 0.05
    robe = T_.get("robe")

    def jambe_(pied, cols, chaus):
        g = _ik(hanche, pied, cuisse, tibia, sens=1)
        if not robe:
            _segment(d, hanche, g, cuisse_w, mollet_w * 1.15, cols)
            _segment(d, g, pied, mollet_w * 1.1, mollet_w * 0.7, cols)
        else:
            _segment(d, g, pied, mollet_w * 0.85, mollet_w * 0.6, PEAU if not vieux else tons((150, 140, 170)))
        x, y = pied                                                # la chaussure, semelle claire
        lg = H * 0.085
        d.rounded_rectangle((x - lg * 0.35, y - H * 0.04, x + lg * 0.75, y), max(1, int(H * 0.015)), fill=chaus)
        d.line([(x - lg * 0.35, y), (x + lg * 0.75, y)], fill=teinte(chaus, 1.8) if sum(chaus) < 300 else GRIS)
        return g

    def bras_(main, cols, peau):
        c = _ik(epaule, main, bras1, bras2, sens=-1)
        _segment(d, epaule, c, bras_w, avbras_w * 1.1, cols)
        _segment(d, c, main, avbras_w * 1.05, avbras_w * 0.85, cols)
        r = H * 0.026
        d.ellipse((main[0] - r, main[1] - r, main[0] + r, main[1] + r * 1.2), fill=peau[0])
        d.point((main[0] - r * 0.4, main[1] - r * 0.4), fill=peau[2])
        return c

    # --- le côté éloigné (assombri)
    jambe_(pied_ar, sombre(bas), teinte(T_["chaussures"], 0.7))
    bras_(main_ar, sombre(haut), tuple(teinte(x, 0.8) for x in PEAU))
    # --- le tronc : un vrai buste (épaules larges, taille, bassin), ombré
    perp = (math.cos(a), math.sin(a))
    up = (math.sin(a), -math.cos(a))
    def P2(c, f, s):                                               # point du buste : centre c, décalage front/haut
        return (c[0] + perp[0] * f + up[0] * s, c[1] + perp[1] * f + up[1] * s)
    taille_c = P2(hanche, 0, buste * 0.42)
    dos = -1
    buste_pts = [P2(hanche, -larg_ha / 2, 0), P2(taille_c, -larg_ha * 0.45, 0), P2(epaule, -larg_ep / 2, -H * 0.02),
                 P2(epaule, -larg_ep * 0.3, H * 0.012), P2(epaule, larg_ep * 0.3, H * 0.012), P2(epaule, larg_ep / 2, -H * 0.03),
                 P2(taille_c, larg_ha * 0.42 + (H * 0.02 if sexe == "f" and not enfant else 0), 0), P2(hanche, larg_ha / 2, 0)]
    if vieux:                                                      # le dos voûté
        buste_pts[2] = P2(epaule, -larg_ep / 2 - H * 0.03, -H * 0.04)
    _poly(d, buste_pts, haut[0])
    _poly(d, [buste_pts[4], buste_pts[5], buste_pts[6], buste_pts[7], P2(hanche, larg_ha * 0.18, 0),
              P2(taille_c, larg_ha * 0.15, 0), P2(epaule, larg_ep * 0.12, 0)], haut[1])   # le devant dans l'ombre
    d.line([(round(buste_pts[1][0]), round(buste_pts[1][1])), (round(buste_pts[2][0]), round(buste_pts[2][1]))], fill=haut[2])
    if T_.get("rayures"):
        for k in range(1, 6):
            y0 = P2(hanche, -larg_ha / 2, buste * k / 6)
            y1 = P2(hanche, larg_ha / 2, buste * k / 6)
            d.line([(round(y0[0]), round(y0[1])), (round(y1[0]), round(y1[1]))], fill=(20, 24, 40))
    if T_.get("chemise"):                                          # chemise blanche et cravate
        c0, c1 = P2(epaule, larg_ep * 0.32, -H * 0.005), P2(taille_c, larg_ha * 0.36, buste * 0.1)
        _poly(d, [c0, P2(epaule, larg_ep * 0.12, -H * 0.005), c1], (226, 232, 246))
        d.line([(round(c0[0] - 1), round(c0[1] + 2)), (round(c1[0] - 1), round(c1[1]))], fill=ROUGE_F, width=max(1, int(H * 0.014)))
    if robe:                                                       # la jupe évasée
        g1 = _ik(hanche, pied_av, cuisse, tibia, sens=1)
        bas_j = hanche[1] + jambe * (0.55 if not vieux else 0.75)
        jupe = [P2(hanche, -larg_ha / 2 - 1, 0), P2(hanche, larg_ha / 2 + 1, 0),
                (max(g1[0], hanche[0]) + H * 0.09, bas_j), (hanche[0] - H * 0.1, bas_j)]
        _poly(d, jupe, bas[0])
        _poly(d, [jupe[1], jupe[2], ((jupe[2][0] + jupe[3][0]) / 2 + H * 0.03, bas_j), P2(hanche, larg_ha * 0.1, 0)], bas[1])
        for k in (0.3, 0.6):                                       # plis
            x = jupe[3][0] + (jupe[2][0] - jupe[3][0]) * k
            d.line([(round(x), round(bas_j - H * 0.08)), (round(x - 1), round(bas_j))], fill=bas[1])
        d.line([(round(jupe[3][0]), round(bas_j)), (round(jupe[2][0]), round(bas_j))], fill=bas[2])
    else:
        ceint = (P2(hanche, -larg_ha / 2, H * 0.015), P2(hanche, larg_ha / 2, H * 0.015))
        d.line([(round(ceint[0][0]), round(ceint[0][1])), (round(ceint[1][0]), round(ceint[1][1]))], fill=teinte(bas[0], 0.5),
               width=max(1, int(H * 0.018)))
    if enceinte:                                                   # le ventre rond, éclairé par le haut
        ctr = P2(taille_c, larg_ha * 0.75, -buste * 0.1)
        r = H * 0.09
        d.ellipse((ctr[0] - r, ctr[1] - r * 1.1, ctr[0] + r, ctr[1] + r * 1.1), fill=haut[0])
        d.chord((ctr[0] - r, ctr[1] - r * 1.1, ctr[0] + r, ctr[1] + r * 1.1), 0, 140, fill=haut[1])
        d.arc((ctr[0] - r + 1, ctr[1] - r * 1.1 + 1, ctr[0] + r - 1, ctr[1] + r * 1.1 - 1), 200, 280, fill=haut[2])
    # --- la jambe proche
    jambe_(pied_av, bas if not robe else bas, T_["chaussures"])
    if canne:                                                      # la canne, tenue par la main avant
        cx0 = main_av[0]
        d.line([(round(cx0), round(main_av[1])), (round(cx0 + H * 0.02), round(py))], fill=(110, 84, 70), width=max(1, int(H * 0.018)))
        d.arc((cx0 - H * 0.04, main_av[1] - H * 0.02, cx0 + H * 0.01, main_av[1] + H * 0.03), 180, 360, fill=(110, 84, 70),
              width=max(1, int(H * 0.018)))
    # --- le cou et la tête
    cou_w = H * 0.04
    _segment(d, epaule, cou, cou_w, cou_w, PEAU, lumiere=False)
    rx, ry = tete_h * 0.44, tete_h * 0.5
    X, Y = tc
    d.ellipse((X - rx, Y - ry, X + rx, Y + ry), fill=PEAU[0])
    d.chord((X - rx, Y - ry, X + rx, Y + ry), 100, 260, fill=PEAU[1])              # l'arrière du crâne dans l'ombre
    d.ellipse((X - rx * 0.1, Y - ry, X + rx, Y + ry * 0.9), fill=PEAU[0])
    d.polygon([(X + rx * 0.62, Y + ry * 0.55), (X + rx * 0.95, Y + ry * 0.75), (X + rx * 0.5, Y + ry * 1.0)], fill=PEAU[0])  # menton
    d.polygon([(X + rx * 0.9, Y - ry * 0.08), (X + rx * 1.22, Y + ry * 0.2), (X + rx * 0.92, Y + ry * 0.3)], fill=PEAU[0])   # le nez
    d.point((round(X + rx * 1.0), round(Y + ry * 0.28)), fill=PEAU[1])
    oeil = (round(X + rx * 0.55), round(Y - ry * 0.06))
    d.point(oeil, fill=(14, 18, 34))
    if H >= 70:
        d.point((oeil[0] - 1, oeil[1]), fill=BLANC)
    d.line([(oeil[0] - 1, oeil[1] - max(1, round(H * 0.012))), (oeil[0] + 1, oeil[1] - max(1, round(H * 0.012)))],
           fill=CHEVEUX[cheveux][1] if cheveux != "blanc" else GRIS)                # le sourcil
    by = round(Y + ry * 0.55)
    if bouche == "cri":
        d.ellipse((X + rx * 0.55, by - 1, X + rx * 0.85, by + 2), fill=(60, 20, 30))
    else:
        d.line([(round(X + rx * 0.6), by), (round(X + rx * 0.8), by)], fill=PEAU[1])
    d.ellipse((X - rx * 0.25, Y - ry * 0.2, X + rx * 0.1, Y + ry * 0.25), fill=PEAU[1])   # l'oreille
    d.point((round(X - rx * 0.08), round(Y)), fill=PEAU[0])
    if vieux:                                                      # rides
        d.point((oeil[0] + 1, oeil[1] + 1), fill=PEAU[1])
        d.point((round(X + rx * 0.5), round(Y + ry * 0.35)), fill=PEAU[1])
    # les cheveux : volume, reflet
    hc, ho, hl = CHEVEUX[cheveux]
    if cheveux == "blanc" and sexe == "h":                         # couronne de cheveux blancs, crâne dégarni
        d.chord((X - rx * 1.02, Y - ry * 0.7, X + rx * 0.3, Y + ry * 0.55), 110, 250, fill=hc)
        d.arc((X - rx, Y - ry, X + rx, Y + ry), 220, 300, fill=PEAU[2])
    else:
        d.chord((X - rx * 1.08, Y - ry * 1.12, X + rx * 1.02, Y + ry * 0.55), 160, 345, fill=hc)
        d.chord((X - rx * 1.08, Y - ry * 1.12, X + rx * 1.02, Y + ry * 0.55), 110, 200, fill=hc)
        d.chord((X - rx * 1.08, Y - ry * 1.12, X + rx * 1.02, Y + ry * 0.55), 105, 170, fill=ho)
        d.arc((X - rx * 0.9, Y - ry * 1.0, X + rx * 0.8, Y + ry * 0.4), 215, 290, fill=hl)
        if sexe == "f":                                            # cheveux longs ou chignon
            if vieux:
                d.ellipse((X - rx * 1.25, Y - ry * 0.95, X - rx * 0.45, Y - ry * 0.2), fill=hc, outline=ho)
            else:
                _poly(d, [(X - rx * 1.05, Y - ry * 0.3), (X - rx * 0.2, Y - ry * 0.2), (X - rx * 0.1, Y + ry * (1.4 if not enfant else 0.9)),
                          (X - rx * 1.15, Y + ry * (1.5 if not enfant else 1.0))], hc)
                d.line([(round(X - rx * 0.7), round(Y)), (round(X - rx * 0.75), round(Y + ry * 1.2))], fill=ho)
    if masque:                                                     # le masque du voleur
        d.rectangle((X - rx * 0.3, oeil[1] - max(1, H * 0.014), X + rx * 1.1, oeil[1] + max(1, H * 0.014)), fill=(10, 10, 16))
        d.point((oeil[0], oeil[1]), fill=BLANC)
    # --- le bras proche, par-dessus tout
    bras_(main_av, haut, PEAU)
    # --- contour d'un pixel, puis pose
    al = np.asarray(cal)[..., 3] > 0
    bord = np.zeros_like(al)
    for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bord |= np.roll(np.roll(al, dx_, 1), dy_, 0)
    arr = np.asarray(cal).copy()
    arr[bord & ~al] = (*CONTOUR, 255)
    cal = Image.fromarray(arr)
    if miroir:
        cal = cal.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(cal, (int(pieds[0] - px), int(pieds[1] - py)), cal)


def ombre_sol(d, x, y, w):
    d.ellipse((x - w, y - max(1, w * 0.18), x + w, y + max(1, w * 0.18)), fill=(4, 8, 20))


# ------------------------------------------------------------------------------------------------ animaux, poussette
def _pose(img, cal, x, y, ox, oy, miroir=False):
    al = np.asarray(cal)[..., 3] > 0
    bord = np.zeros_like(al)
    for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bord |= np.roll(np.roll(al, dx_, 1), dy_, 0)
    arr = np.asarray(cal).copy()
    arr[bord & ~al] = (*CONTOUR, 255)
    cal = Image.fromarray(arr)
    if miroir:
        cal = cal.transpose(Image.FLIP_LEFT_RIGHT)
        ox = cal.width - ox
    img.paste(cal, (int(x - ox), int(y - oy)), cal)


def chien(img, x, y, h=40, t=0.0, miroir=False):
    """Un labrador de profil, debout (h = hauteur au garrot + tête)."""
    k = h / 40
    W = int(90 * k)
    cal = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(cal)
    ox, oy = W * 0.45, W * 0.85
    S = lambda px, py: (ox + px * k, oy - py * k)
    base, ombre, clair = (186, 150, 108), (130, 100, 70), (226, 196, 150)
    lb, lo = teinte(base, 0.75), teinte(ombre, 0.75)
    # pattes éloignées (plus sombres)
    for px in (-14, 13):
        _segment(d, S(px, 20), S(px + 1, 9), 5 * k, 4 * k, (lb, lo, lb), False)
        _segment(d, S(px + 1, 9), S(px, 0.5), 4 * k, 3.5 * k, (lb, lo, lb), False)
    # la queue qui remue
    q = math.sin(t * 10) * 4
    _segment(d, S(-20, 22), S(-28, 26 + q), 4 * k, 2.5 * k, (base, ombre, clair), False)
    # le corps
    _poly(d, [S(-21, 26), S(-8, 28), S(10, 28), S(18, 25), S(20, 15), S(8, 13), S(-10, 14), S(-21, 16)], base)
    _poly(d, [S(-21, 17), S(-10, 14), S(8, 13), S(20, 15), S(18, 12), S(-18, 13)], ombre)   # le ventre dans l'ombre
    d.line([S(-18, 27), S(10, 28)], fill=clair)
    # pattes proches
    for px in (-17, 15):
        _segment(d, S(px, 20), S(px + 1, 9), 6 * k, 4.5 * k, (base, ombre, clair))
        _segment(d, S(px + 1, 9), S(px + 0.5, 1), 4.5 * k, 4 * k, (base, ombre, clair))
        d.ellipse((S(px - 1, 2)[0], S(px, 2)[1], S(px + 4, 0)[0], S(px, 0)[1]), fill=ombre)
    # le cou et la tête
    _poly(d, [S(12, 28), S(19, 36), S(26, 34), S(22, 22), S(16, 19)], base)
    _poly(d, [S(18, 40), S(28, 41), S(31, 36), S(38, 34), S(38, 30), S(28, 29), S(19, 31)], base)    # crâne + museau
    _poly(d, [S(28, 29), S(38, 30), S(37, 28), S(29, 27)], ombre)                                       # la mâchoire
    d.ellipse((S(36, 35)[0], S(36, 35)[1], S(39.5, 32)[0], S(39.5, 32)[1]), fill=(20, 16, 20))         # la truffe
    d.point(S(29, 37), fill=(16, 12, 16))                                                               # l'œil
    d.point(S(30, 38), fill=clair)
    _poly(d, [S(20, 40), S(24, 40), S(24, 30), S(19, 31)], ombre)                                       # l'oreille tombante
    d.line([S(19, 40), S(27, 41)], fill=clair)
    _pose(img, cal, x, y, ox, oy, miroir)


def chat(img, x, y, h=30, t=0.0, miroir=False):
    """Un chat assis de profil, la queue enroulée qui bouge du bout."""
    k = h / 30
    W = int(70 * k)
    cal = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(cal)
    ox, oy = W * 0.45, W * 0.85
    S = lambda px, py: (ox + px * k, oy - py * k)
    base, ombre, clair = (150, 158, 178), (98, 104, 126), (200, 206, 222)
    q = math.sin(t * 3) * 3
    _segment(d, S(-8, 2), S(-16, 4), 4 * k, 3.5 * k, (ombre, teinte(ombre, 0.8), base), False)          # la queue
    _segment(d, S(-16, 4), S(-18, 12 + q), 3.5 * k, 3 * k, (ombre, teinte(ombre, 0.8), base), False)
    _poly(d, [S(-10, 1), S(-12, 10), S(-6, 18), S(2, 21), S(7, 16), S(6, 1)], base)                      # le corps assis
    _poly(d, [S(0, 1), S(4, 14), S(7, 16), S(6, 1)], ombre)
    d.line([S(-11, 9), S(-5, 17)], fill=clair)
    _segment(d, S(4, 14), S(5, 1), 4 * k, 3.5 * k, (base, ombre, clair))                               # patte avant
    d.ellipse((S(1, 22)[0], S(1, 22)[1], S(13, 13)[0], S(13, 13)[1]), fill=base)                       # la tête
    d.chord((S(1, 22)[0], S(1, 22)[1], S(13, 13)[0], S(13, 13)[1]), 20, 160, fill=ombre)
    for ex in (2.5, 8):                                                                                 # les oreilles
        _poly(d, [S(ex, 20), S(ex + 1.5, 26), S(ex + 4, 20.5)], base)
        d.point(S(ex + 1.6, 22.5), fill=(210, 150, 170))
    d.point(S(10.5, 18.5), fill=(150, 220, 120))                                                        # l'œil vert
    d.point(S(12.5, 16.5), fill=(210, 150, 170))                                                        # le nez
    for dy in (0, 1):
        d.line([S(12, 16 - dy), S(16, 16.5 - dy * 1.5)], fill=clair)                                    # moustaches
    _pose(img, cal, x, y, ox, oy, miroir)


def poussette(img, x, y, h=40, t=0.0, miroir=False):
    """Un landau de profil : nacelle capitonnée, capote à soufflets, châssis chromé, roues à rayons, bébé."""
    k = h / 40
    W = int(80 * k)
    cal = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(cal)
    ox, oy = W * 0.45, W * 0.85
    S = lambda px, py: (ox + px * k, oy - py * k)
    corps, ombre, clair = (60, 100, 180), (36, 62, 120), (110, 160, 236)
    chrome = (190, 200, 220)
    d.line([S(-10, 8), S(12, 8)], fill=chrome, width=max(1, int(1.5 * k)))                             # châssis
    d.line([S(-10, 8), S(-6, 16)], fill=chrome, width=max(1, int(1.5 * k)))
    d.line([S(12, 8), S(8, 16)], fill=chrome, width=max(1, int(1.5 * k)))
    d.line([S(12, 16), S(22, 34)], fill=chrome, width=max(1, int(2 * k)))                              # la poignée
    d.line([S(20, 34), S(25, 34)], fill=(30, 30, 40), width=max(1, int(2.5 * k)))
    d.chord((S(-16, 30)[0], S(-16, 30)[1], S(16, 6)[0], S(16, 6)[1]), 0, 180, fill=corps)             # la nacelle
    d.chord((S(-16, 30)[0], S(-16, 30)[1], S(16, 6)[0], S(16, 6)[1]), 40, 180, fill=ombre)
    d.line([S(-15, 18), S(15, 18)], fill=clair)
    for px in (-8, 0, 8):                                                                               # capitons
        d.point(S(px, 13), fill=clair)
    capote = [S(-16, 18), S(-16, 26), S(-12, 32), S(-4, 34), S(2, 30), S(4, 18)]
    _poly(d, capote, clair)
    for k2, px in enumerate((-12, -7, -2)):                                                            # soufflets
        d.line([S(px, 18), S(px - 1, 31 + k2)], fill=corps)
    d.ellipse((S(4, 24)[0], S(4, 24)[1], S(11, 18)[0], S(11, 18)[1]), fill=PEAU[0])                   # le bébé
    d.point(S(9, 21.5), fill=(20, 20, 30))
    d.chord((S(4, 24.5)[0], S(4, 24.5)[1], S(11, 20)[0], S(11, 20)[1]), 180, 330, fill=(230, 200, 220))   # bonnet
    for cx in (-10, 12):                                                                                # roues à rayons
        r = 6
        d.ellipse((S(cx - r, r * 2)[0], S(cx, r * 2)[1], S(cx + r, 0)[0], S(cx, 0)[1]), fill=(16, 16, 24))
        d.ellipse((S(cx - r + 1.5, r * 2 - 1.5)[0], S(cx, r * 2 - 1.5)[1], S(cx + r - 1.5, 1.5)[0], S(cx, 1.5)[1]),
                  outline=chrome)
        for j in range(4):
            a = t * 3 + j * math.pi / 4
            c0 = S(cx, r)
            d.line([(c0[0] - 4 * k * math.cos(a), c0[1] - 4 * k * math.sin(a)),
                    (c0[0] + 4 * k * math.cos(a), c0[1] + 4 * k * math.sin(a))], fill=GRIS_F)
    _pose(img, cal, x, y, ox, oy, miroir)


# ------------------------------------------------------------------------------------------------ voitures
def voiture_profil(img, x, y, longueur=160, col=B2, t=0.0, roule=True, phares=True, miroir=False):
    """Une berline de profil (avant vers la droite), pieds des roues sur y : silhouette galbée, passages de roues,
    vitres teintées avec reflets, poignées, jantes à cinq branches, bas de caisse, ombre portée."""
    k = longueur / 160
    W, Hh = int(170 * k), int(70 * k)
    cal = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(cal)
    ox, oy = 5 * k, Hh - 2
    S = lambda px, py: (ox + px * k, oy - py * k)
    base = col
    ombre = teinte(col, 0.58)
    clair = tuple(min(255, int(v * 1.25) + 26) for v in col)
    vitre, vitre_c = (12, 22, 48), (60, 90, 150)
    caisse = [S(0, 14), S(2, 26), S(10, 30), S(40, 32), S(56, 48), S(68, 52), S(104, 52), S(118, 44), S(132, 36),
              S(152, 32), S(159, 27), S(160, 15), S(156, 10), S(4, 10)]
    _poly(d, caisse, base)
    _poly(d, [S(4, 10), S(156, 10), S(160, 15), S(158, 20), S(2, 20), S(0, 14)], ombre)                 # le bas, dans l'ombre
    d.line([S(8, 29), S(42, 31.5)], fill=clair)                                                        # la ligne de caisse
    d.line([S(42, 31.5), S(150, 31)], fill=clair)
    d.line([S(56, 47), S(68, 51), S(103, 51), S(117, 43)], fill=clair)                                  # le pavillon
    _poly(d, [S(60, 46), S(70, 50), S(84, 50), S(84, 34), S(48, 33)], vitre)                           # vitre arrière
    _poly(d, [S(87, 50), S(102, 50), S(114, 43), S(126, 35), S(87, 34)], vitre)                        # vitre avant
    _poly(d, [S(64, 45), S(70, 48.5), S(74, 48.5), S(62, 36), S(56, 36)], vitre_c)                     # reflets
    _poly(d, [S(95, 49), S(100, 49), S(110, 37), S(105, 37)], vitre_c)
    d.line([S(85.5, 50), S(85.5, 33)], fill=ombre, width=max(1, int(2 * k)))                          # montant
    d.line([S(85.5, 33), S(85.5, 13)], fill=ombre)                                                     # portières
    d.line([S(50, 31), S(50, 13)], fill=ombre)
    d.line([S(124, 33), S(126, 14)], fill=ombre)
    for px in (70, 108):
        d.rectangle((S(px, 28)[0], S(px, 28)[1], S(px + 7, 27)[0], S(px, 26.5)[1]), fill=clair)       # poignées
    _poly(d, [S(120, 36), S(126, 40), S(128, 36)], ombre)                                              # rétroviseur
    _poly(d, [S(150, 27), S(159, 26), S(160, 21), S(152, 22)], BLANC if phares else GRIS)              # phare
    _poly(d, [S(0, 25), S(5, 26), S(5, 19), S(0, 18)], ROUGE)                                          # feu arrière
    for cx in (30, 128):                                                                               # passages de roue
        d.ellipse((S(cx - 17, 32)[0], S(cx, 32)[1], S(cx + 17, -2)[0], S(cx, -2)[1]), fill=(0, 0, 0, 0))
        d.chord((S(cx - 17, 32)[0], S(cx, 32)[1], S(cx + 17, -2)[0], S(cx, -2)[1]), 180, 360, fill=(6, 10, 22))
    for cx in (30, 128):
        r = 14
        c = S(cx, r)
        d.ellipse((c[0] - r * k, c[1] - r * k, c[0] + r * k, c[1] + r * k), fill=(14, 14, 20))       # pneu
        d.arc((c[0] - r * k, c[1] - r * k, c[0] + r * k, c[1] + r * k), 200, 280, fill=(60, 64, 80))
        rj = 8.5 * k
        d.ellipse((c[0] - rj, c[1] - rj, c[0] + rj, c[1] + rj), fill=(150, 160, 182))                # jante
        d.ellipse((c[0] - rj + 1, c[1] - rj + 1, c[0] + rj - 1, c[1] + rj - 1), fill=(70, 78, 100))
        a0 = t * 14 if roule else 0.4
        for j in range(5):
            a = a0 + j * 2 * math.pi / 5
            d.line([c, (c[0] + rj * math.cos(a), c[1] + rj * math.sin(a))], fill=(190, 198, 216), width=max(1, int(1.6 * k)))
        d.ellipse((c[0] - 2 * k, c[1] - 2 * k, c[0] + 2 * k, c[1] + 2 * k), fill=(200, 206, 222))
    _pose(img, cal, x, y, ox, oy, miroir)


def voiture_dessus(img, cx, cy, ang=0.0, col=B2, t=0.0, toit=True, alerte=False, freinage=0.0, longueur=74):
    """La voiture autonome vue du dessus (avant vers le haut) : capot galbé, pare-brise teinté avec reflet, toit et
    lidar, lunette, rétroviseurs, roues qui dépassent, phares et feux, ombre portée."""
    k = longueur / 74
    W, Hh = int(64 * k), int(92 * k)
    cal = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(cal)
    S = lambda px, py: (W / 2 + px * k, Hh / 2 + py * k)
    base, ombre, clair = col, teinte(col, 0.6), tuple(min(255, int(v * 1.25) + 26) for v in col)
    for sx in (-1, 1):                                                                                 # roues
        for sy in (-24, 22):
            d.rounded_rectangle((S(sx * 17 - 3, sy - 7)[0], S(0, sy - 7)[1], S(sx * 17 + 3, sy + 7)[0], S(0, sy + 7)[1]),
                                max(1, int(2 * k)), fill=(10, 10, 16))
    corps = [S(-13, -37), S(-6, -39), S(6, -39), S(13, -37), S(16, -30), S(17, -10), S(17, 28), S(15, 35), S(8, 38),
             S(-8, 38), S(-15, 35), S(-17, 28), S(-17, -10), S(-16, -30)]
    _poly(d, corps, base)
    _poly(d, [S(9, -37), S(16, -30), S(17, -10), S(17, 28), S(15, 35), S(10, 37), S(12, 20), S(12, -28)], ombre)   # flanc droit
    d.line([S(-15, -30), S(-16, 28)], fill=clair)                                                      # reflet flanc gauche
    d.line([S(-8, -37), S(-10, -24)], fill=clair)                                                      # nervures du capot
    d.line([S(8, -37), S(10, -24)], fill=ombre)
    _poly(d, [S(-12, -18), S(12, -18), S(14, -8), S(-14, -8)], (14, 26, 56))                           # pare-brise
    _poly(d, [S(-9, -17), S(-4, -17), S(-9, -9), S(-12, -9)], (60, 90, 150))                           # reflet
    for sx in (-1, 1):                                                                                 # rétroviseurs
        _poly(d, [S(sx * 15, -12), S(sx * 21, -14), S(sx * 21, -10), S(sx * 15, -9)], base)
    if toit:
        _poly(d, [S(-13, -8), S(13, -8), S(13, 18), S(-13, 18)], teinte(col, 0.9))
        d.line([S(-12, -7), S(-12, 17)], fill=clair)
        d.ellipse((S(-5, -1)[0], S(0, -1)[1], S(5, 9)[0], S(0, 9)[1]), fill=(30, 40, 70))             # le lidar
        a = t * 8
        c = S(0, 4)
        d.line([c, (c[0] + 4 * k * math.cos(a), c[1] + 4 * k * math.sin(a))], fill=B4)
    else:                                                                                              # habitacle vide
        _poly(d, [S(-13, -8), S(13, -8), S(13, 18), S(-13, 18)], (8, 14, 30))
        for sx in (-7, 7):
            d.rounded_rectangle((S(sx - 5, -4)[0], S(0, -4)[1], S(sx + 5, 0)[0], S(0, 0)[1]), 1, fill=(70, 78, 100))
            d.rounded_rectangle((S(sx - 5, 0)[0], S(0, 0)[1], S(sx + 5, 9)[0], S(0, 9)[1]), 2, fill=(50, 56, 76))
            d.rounded_rectangle((S(sx - 5, 11)[0], S(0, 11)[1], S(sx + 5, 16)[0], S(0, 16)[1]), 1, fill=(50, 56, 76))
        c = S(-7, -6)
        d.ellipse((c[0] - 5 * k, c[1] - 2 * k, c[0] + 5 * k, c[1] + 2 * k), outline=GRIS)              # le volant, seul
        a = t * 5
        d.line([(c[0] - 4 * k * math.cos(a), c[1] - 1.5 * k * math.sin(a)), (c[0] + 4 * k * math.cos(a), c[1] + 1.5 * k * math.sin(a))],
               fill=B4)
    _poly(d, [S(-12, 18), S(12, 18), S(13, 26), S(-13, 26)], (14, 26, 56))                            # lunette arrière
    d.line([S(-9, 20), S(-6, 25)], fill=(60, 90, 150))
    for sx in (-1, 1):                                                                                 # phares, feux
        _poly(d, [S(sx * 6, -39), S(sx * 13, -37), S(sx * 14, -34), S(sx * 7, -36)], BLANC)
        feu = ROUGE if (alerte and int(t * 8) % 2) or freinage > 0 else ROUGE_F
        _poly(d, [S(sx * 6, 38), S(sx * 13, 36), S(sx * 15, 33), S(sx * 7, 35)], feu)
    cal = cal.rotate(-ang, resample=Image.NEAREST, expand=True)
    al = np.asarray(cal)[..., 3] > 0
    bord = np.zeros_like(al)
    for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bord |= np.roll(np.roll(al, dx_, 1), dy_, 0)
    arr = np.asarray(cal).copy()
    arr[bord & ~al] = (*CONTOUR, 255)
    cal = Image.fromarray(arr)
    sh = Image.new("RGBA", cal.size, (0, 0, 0, 0))                                                    # ombre portée
    m = np.asarray(cal)[..., 3] > 0
    sa = np.zeros((*m.shape, 4), np.uint8)
    sa[m] = (2, 4, 12, 170)
    sh = Image.fromarray(sa)
    img.paste(sh, (int(cx - cal.width / 2 + 3), int(cy - cal.height / 2 + 4)), sh)
    img.paste(cal, (int(cx - cal.width / 2), int(cy - cal.height / 2)), cal)
