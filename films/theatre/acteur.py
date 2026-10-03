"""Acteur bâton pour scènes comiques : squelette en angles, ressorts par articulation (fluidité, chevauchement des
mouvements), marche procédurale, rotation face/profil, visage expressif, style « trait fin » (membres en tubes
blancs cernés, grosse tête ronde, mains dessinées, chaussures blanches).

Repère de l'acteur : bassin à l'origine, y vers le bas. Angles en degrés.
  • colonne, tete : inclinaison (positive = vers l'avant / le regard)
  • bras : epaule, coude (0 = pendant ; positif = vers l'extérieur de face, vers l'avant de profil)
  • jambes : hanche, genou (0 = droite ; positif = vers l'avant)
"""
import math
from dataclasses import dataclass, field

import skia

INK = skia.Color(20, 20, 24)
WHITE = skia.Color(255, 255, 255)

L_DOS, L_COU, R_TETE = 175.0, 16.0, 66.0
L_BRAS, L_AVBRAS = 108.0, 100.0
L_CUISSE, L_TIBIA = 138.0, 134.0
ARTICS = ["colonne", "tete", "bg_e", "bg_c", "bd_e", "bd_c", "jg_h", "jg_g", "jd_h", "jd_g"]
# pulsation des ressorts (rad/s) : le haut du corps suit, les extrémités traînent → mouvement en vague
OMEGA = {"colonne": 16, "tete": 13, "bg_e": 18, "bg_c": 13, "bd_e": 18, "bd_c": 13, "jg_h": 30, "jg_g": 30,
         "jd_h": 30, "jd_g": 30, "tour": 12, "x": 0, "y": 0}

POSES = {
    "repos":     {"colonne": 0, "tete": 0, "bg_e": 8, "bg_c": 6, "bd_e": 8, "bd_c": 6, "jg_h": 0, "jg_g": 0,
                  "jd_h": 0, "jd_g": 0},
    "hanches":   {"bg_e": 42, "bg_c": -95, "bd_e": 42, "bd_c": -95},
    "victoire":  {"bg_e": 150, "bg_c": 15, "bd_e": 150, "bd_c": 15, "tete": -8, "colonne": -4},
    "malin":     {"bd_e": 30, "bd_c": 120, "bg_e": 10, "bg_c": 8, "tete": 6},          # doigt sur la tempe
    "rire":      {"colonne": -10, "tete": -12, "bg_e": 28, "bg_c": 60, "bd_e": 40, "bd_c": 70},
    "pointe":    {"bd_e": 85, "bd_c": 4, "bg_e": 10, "bg_c": 10},
    "surpris":   {"bg_e": 55, "bg_c": 80, "bd_e": 55, "bd_c": 80, "colonne": -6, "tete": -6},
    "salut":     {"colonne": 35, "tete": 20, "bg_e": 5, "bg_c": 10, "bd_e": 5, "bd_c": 10},
    "pas_haut":  {"jd_h": 75, "jd_g": -85, "bg_e": 35, "bg_c": 30, "bd_e": 25, "bd_c": 20, "colonne": 4},
    "allonge":   {"colonne": 0, "tete": -10, "bg_e": 25, "bg_c": 10, "bd_e": -15, "bd_c": -10, "jg_h": 8,
                  "jg_g": -6, "jd_h": 18, "jd_g": -15},
    "pouce":     {"bd_e": 120, "bd_c": -30},
}
MAINS = {"repos": ("ouverte", "ouverte"), "hanches": ("poing", "poing"), "victoire": ("ouverte", "ouverte"),
         "malin": ("ouverte", "index"), "rire": ("ouverte", "ouverte"), "pointe": ("ouverte", "index"),
         "surpris": ("ouverte", "ouverte"), "salut": ("ouverte", "ouverte"), "pas_haut": ("ouverte", "ouverte"),
         "allonge": ("ouverte", "ouverte"), "pouce": ("ouverte", "pouce")}


def pose(*noms, **reglages):
    p = dict(POSES["repos"])
    for n in noms:
        p.update(POSES[n])
    p.update(reglages)
    return p


def P(color=INK, stroke=0.0):
    p = skia.Paint(AntiAlias=True, Color=color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


def tube(c, pts, w=7.0, o=3.2):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    c.drawPath(p, P(INK, w + 2 * o))
    c.drawPath(p, P(WHITE, w))


@dataclass
class Jeu:
    """Ce que l'acteur doit faire à un instant (fourni par le script de la scène)."""
    pose: dict
    mains: tuple = ("ouverte", "ouverte")
    x: float = 0.0                 # position du bassin (scène)
    sol: float = 0.0               # hauteur du sol (scène)
    saut: float = 0.0              # élévation au-dessus du sol
    tour: float = 0.0              # -1 profil gauche, 0 face, +1 profil droite
    rotation: float = 0.0          # rotation globale (chutes), degrés
    marche: float = 0.0            # phase de marche (tours de cycle) ; None = pas de marche
    marche_k: float = 0.0          # intensité de la marche 0–1
    humeur: str = "neutre"
    bouche: float = 0.0
    regard: tuple = (0.0, 0.0)
    cligne: bool = False
    accessoire: str = ""


class Acteur:
    def __init__(self, accessoire="meche", fps=30):
        self.acc = accessoire
        self.dt = 1.0 / fps
        self.v = {k: 0.0 for k in ARTICS + ["tour"]}
        self.dv = {k: 0.0 for k in self.v}
        self.init = False

    def avance(self, jeu):
        """Fait avancer les ressorts d'une image vers la pose demandée."""
        cible = dict(jeu.pose)
        cible["tour"] = jeu.tour
        if jeu.marche_k > 0:                                  # cycle de marche superposé
            ph = 2 * math.pi * jeu.marche
            k = jeu.marche_k
            for sd, off in (("g", 0.0), ("d", math.pi)):
                s = math.sin(ph + off)
                cible[f"j{sd}_h"] = cible[f"j{sd}_h"] * (1 - k) + k * 28 * s
                cible[f"j{sd}_g"] = cible[f"j{sd}_g"] * (1 - k) + k * (-38 * max(0.0, math.cos(ph + off + 0.6)))
                cible[f"b{sd}_e"] = cible[f"b{sd}_e"] * (1 - k) + k * (-22 * s)
                cible[f"b{sd}_c"] = cible[f"b{sd}_c"] * (1 - k) + k * (18 + 10 * s)
        if not self.init:
            self.v.update(cible)
            self.init = True
        for _ in range(4):
            h = self.dt / 4
            for k, tgt in cible.items():
                w = OMEGA.get(k, 15)
                if w <= 0:
                    continue
                z = 0.62 if k not in ("jg_h", "jg_g", "jd_h", "jd_g") else 0.9
                self.dv[k] += (w * w * (tgt - self.v[k]) - 2 * z * w * self.dv[k]) * h
                self.v[k] += self.dv[k] * h

    # -------------------------------------------------------------------------------------------- géométrie
    def squelette(self, jeu):
        v = self.v
        tour = max(-1.0, min(1.0, v["tour"]))
        fac = 1 if tour >= 0 else -1
        a = abs(tour)
        hip = (0.0, 0.0)
        incl = v["colonne"] * fac
        cou = add(hip, rot((0, -L_DOS), incl))
        epaule = add(cou, rot((0, 14), incl))
        tete = add(cou, rot((0, -(L_COU + R_TETE)), incl + v["tete"] * fac))
        mem = {}
        for sd, side in (("g", -1), ("d", 1)):
            s = side * (1 - a) + fac * a                          # sens « extérieur/avant » à l'écran
            ae = v[f"b{sd}_e"] * s
            coude = add(epaule, rot((0, L_BRAS), incl - ae))
            main = add(coude, rot((0, L_AVBRAS), incl - ae - v[f"b{sd}_c"] * s))
            mem["b" + sd] = (epaule, coude, main)
            hx = side * 11 * (1 - a)
            hh = add(hip, (hx, 0))
            ah = v[f"j{sd}_h"] * s + side * 5 * (1 - a)
            genou = add(hh, rot((0, L_CUISSE), -ah))
            pied = add(genou, rot((0, L_TIBIA), -ah - v[f"j{sd}_g"] * s))
            mem["j" + sd] = (hh, genou, pied)
        return dict(hip=hip, cou=cou, epaule=epaule, tete=tete, mem=mem, fac=fac, a=a, tour=tour)

    def hauteur_pieds(self, sq):
        return max(sq["mem"]["jg"][2][1], sq["mem"]["jd"][2][1])

    # -------------------------------------------------------------------------------------------- dessin
    def draw(self, c, jeu):
        sq = self.squelette(jeu)
        bas = self.hauteur_pieds(sq) + 10                        # bassin calé pour que le pied le plus bas touche
        c.save()
        c.translate(jeu.x, jeu.sol - jeu.saut)
        # ombre (reste au sol)
        k = max(0.3, 1 - jeu.saut / 300)
        c.drawOval(skia.Rect(-95 * k, -9 * k, 95 * k, 9 * k), P(skia.Color(0, 0, 0, int(55 * k))))
        k = min(1.0, abs(jeu.rotation) / 90)
        c.translate(0, -bas * (1 - k) - 70 * k)
        c.rotate(jeu.rotation)
        fac, a = sq["fac"], sq["a"]
        loin = [m for m in ("bg", "bd", "jg", "jd") if a > 0.5 and ((m[1] == "g") == (fac > 0))]
        for m in ("jg", "jd"):
            if m in loin:
                self.jambe(c, sq["mem"][m], fac, a)
        for m in ("bg", "bd"):
            if m in loin:
                self.bras(c, sq["mem"][m], jeu.mains[0 if m == "bg" else 1], m, sq)
        for m in ("jg", "jd"):
            if m not in loin:
                self.jambe(c, sq["mem"][m], fac, a)
        c.drawLine(*sq["hip"], *sq["cou"], P(INK, 6.5))
        self.tete(c, sq, jeu)
        for m in ("bg", "bd"):
            if m not in loin:
                self.bras(c, sq["mem"][m], jeu.mains[0 if m == "bg" else 1], m, sq)
        c.restore()
        return sq

    def jambe(self, c, mem, fac, a):
        hh, genou, pied = mem
        tube(c, [hh, genou, pied], 7.5)
        d = fac * a + (1 - a) * (1 if pied[0] > hh[0] else -1) * 0.5
        r = skia.Rect(pied[0] - 22 + 12 * d, pied[1] - 6, pied[0] + 22 + 12 * d, pied[1] + 14)
        c.drawOval(r, P(WHITE))
        c.drawOval(r, P(INK, 3.5))

    def bras(self, c, mem, forme, m, sq):
        ep, coude, main = mem
        tube(c, [ep, coude, main], 6.5)
        ang = math.degrees(math.atan2(main[1] - coude[1], main[0] - coude[0]))
        c.save()
        c.translate(*main)
        c.rotate(ang)
        fill, ink = P(WHITE), P(INK, 3.2)
        sd = -1 if m == "bg" else 1
        if forme in ("poing", "index", "pouce"):
            c.drawOval(skia.Rect(-4, -12, 22, 12), fill)
            c.drawOval(skia.Rect(-4, -12, 22, 12), ink)
            if forme == "index":
                r = skia.RRect.MakeRectXY(skia.Rect(14, -6, 46, 5), 5, 5)
                c.drawRRect(r, fill)
                c.drawRRect(r, ink)
            if forme == "pouce":
                c.save()
                c.rotate(-90 * sd)
                r = skia.RRect.MakeRectXY(skia.Rect(6, -5, 34, 5), 5, 5)
                c.drawRRect(r, fill)
                c.drawRRect(r, ink)
                c.restore()
        else:
            c.drawOval(skia.Rect(-3, -12, 21, 12), fill)
            c.drawOval(skia.Rect(-3, -12, 21, 12), ink)
            for k in range(4):
                aa = math.radians(-33 + 22 * k)
                x0, y0 = 16 + 2 * math.cos(aa), 9 * math.sin(aa)
                x1, y1 = x0 + 17 * math.cos(aa), y0 + 17 * math.sin(aa)
                c.drawLine(x0, y0, x1, y1, P(INK, 8.0))
                c.drawLine(x0, y0, x1, y1, P(WHITE, 2.8))
            c.drawLine(6, sd * 10, 12, sd * 24, P(INK, 8.0))
            c.drawLine(6, sd * 10, 12, sd * 24, P(WHITE, 2.8))
        c.restore()

    def tete(self, c, sq, jeu):
        cx, cy = sq["tete"]
        c.drawLine(*sq["cou"], cx, cy + R_TETE - 3, P(INK, 6.0))
        c.drawCircle(cx, cy, R_TETE, P(WHITE))
        c.drawCircle(cx, cy, R_TETE, P(INK, 4.5))
        tr = sq["tour"]
        off = tr * R_TETE * 0.42
        gx, gy = jeu.regard[0] * 6 + off, jeu.regard[1] * 5
        hum = jeu.humeur
        sep = 22 * (1 - 0.35 * abs(tr))
        for sd in (-1, 1):
            ex, ey = cx + gx + sd * sep, cy - 8 + gy
            if jeu.cligne or hum in ("rire", "content"):
                p = skia.Path()
                if hum in ("rire", "content"):
                    p.moveTo(ex - 9, ey + 2)
                    p.quadTo(ex, ey - 10, ex + 9, ey + 2)
                else:
                    p.moveTo(ex - 8, ey)
                    p.lineTo(ex + 8, ey)
                c.drawPath(p, P(INK, 3.5))
            elif hum == "ko":
                for s2 in (-1, 1):
                    c.drawLine(ex - 7, ey - 7 * s2, ex + 7, ey + 7 * s2, P(INK, 3.5))
            else:
                hh = 12 if hum != "surpris" else 15
                c.drawOval(skia.Rect(ex - 6.5, ey - hh, ex + 6.5, ey + hh * 0.55), P(INK))
                c.drawCircle(ex - 1.8, ey - hh * 0.5, 2.4, P(WHITE))
            by = ey - 24
            if hum in ("malin",):
                c.drawLine(ex - 10, by + (5 if sd < 0 else -3), ex + 10, by + (-1 if sd < 0 else 3), P(INK, 3.5))
            elif hum in ("inquiet", "ko"):
                c.drawLine(ex - 10, by - sd * 4 + 2, ex + 10, by + sd * 4, P(INK, 3.5))
            elif hum == "surpris":
                p = skia.Path()
                p.moveTo(ex - 10, by - 4)
                p.quadTo(ex, by - 14, ex + 10, by - 4)
                c.drawPath(p, P(INK, 3.5))
            else:
                p = skia.Path()
                p.moveTo(ex - 10, by + 2)
                p.quadTo(ex, by - 4, ex + 10, by + 2)
                c.drawPath(p, P(INK, 3.5))
        mx, my = cx + gx * 0.9, cy + 28
        p = skia.Path()
        if hum == "rire":
            p.moveTo(mx - 20, my - 6)
            p.quadTo(mx, my + 30, mx + 20, my - 6)
            p.close()
            c.drawPath(p, P(INK))
            c.drawOval(skia.Rect(mx - 9, my + 4, mx + 9, my + 13), P(skia.Color(240, 110, 130)))
        elif hum == "surpris" or jeu.bouche > 0.2:
            r = 8 + 6 * max(jeu.bouche, 0.4 if hum == "surpris" else 0)
            c.drawOval(skia.Rect(mx - r * 0.75, my - r * 0.6, mx + r * 0.75, my + r), P(INK))
        elif hum in ("content", "malin", "neutre_sourire"):
            p.moveTo(mx - 18, my - 4)
            p.quadTo(mx + 2, my + 14, mx + 20, my - 8)
            c.drawPath(p, P(INK, 4.0))
        elif hum in ("inquiet", "ko"):
            p.moveTo(mx - 14, my + 6)
            p.quadTo(mx, my - 6, mx + 14, my + 6)
            c.drawPath(p, P(INK, 4.0))
        else:
            p.moveTo(mx - 14, my)
            p.quadTo(mx, my + 4, mx + 14, my)
            c.drawPath(p, P(INK, 4.0))
        if self.acc == "meche":                                   # petite mèche
            for k in (-1, 0, 1):
                b0 = (cx + k * 9, cy - R_TETE + 2)
                p = skia.Path()
                p.moveTo(*b0)
                p.quadTo(b0[0] + 6 + k * 4, b0[1] - 16, b0[0] + 14 + k * 6, b0[1] - 22)
                c.drawPath(p, P(INK, 3.5))
        elif self.acc == "casquette":
            r = skia.Rect(cx - R_TETE + 6, cy - R_TETE - 10, cx + R_TETE - 6, cy - R_TETE + 44)
            p = skia.Path()
            p.addArc(r, 180, 180)
            p.close()
            c.drawPath(p, P(skia.Color(220, 60, 60)))
            c.drawPath(p, P(INK, 4.0))
            vis = tr if abs(tr) > 0.2 else 0.6
            sx = cx + (R_TETE - 4) * (1 if vis > 0 else -1) * 0.75
            c.drawOval(skia.Rect(sx - 34, cy - R_TETE + 10, sx + 34, cy - R_TETE + 26), P(skia.Color(220, 60, 60)))
            c.drawOval(skia.Rect(sx - 34, cy - R_TETE + 10, sx + 34, cy - R_TETE + 26), P(INK, 4.0))
