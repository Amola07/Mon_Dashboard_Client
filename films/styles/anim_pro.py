"""Outils d'animation « pro » pour le style oscilloscope : courbes avec rebond, ressorts, caméra virtuelle,
transformation d'un dessin en un autre (morphing de traits), flexion d'un corps dessiné, traits qui « vivent ».

Tout travaille sur les dessins du projet : des listes de lignes brisées [[(x, y), …], …].

    from films.styles import anim_pro as A
    k = A.rebond((t - t0) / 0.4)                       # 0 → dépasse un peu → 1
    cam = A.Camera([(0, 1.0, 540, 900), (12, 1.06, 540, 900)], chocs=[(15.2, 0.3, 14)])
    cam.appliquer(c, t)                                # à faire avant de dessiner (c.save() / c.restore() autour)
    traits = A.morph("as_neutre", "as_attache", A_traits, B_traits, k)
"""
import math

import numpy as np
from scipy.optimize import linear_sum_assignment

W, H = 1080, 1920


# ------------------------------------------------------------------------------------------------ courbes
def borne(u):
    return max(0.0, min(1.0, u))


def lisse(u):
    u = borne(u)
    return u * u * (3 - 2 * u)


def sortie(u, p=3.0):
    """Départ vif, arrivée douce (ease-out)."""
    return 1 - (1 - borne(u)) ** p


def rebond(u, s=1.9):
    """Arrive en dépassant un peu sa cible, puis s'y pose (ease-out-back)."""
    u = borne(u) - 1
    return 1 + (s + 1) * u ** 3 + s * u ** 2


def anticipe(u, s=1.6):
    """Recule un peu avant de partir (ease-in-back)."""
    u = borne(u)
    return (s + 1) * u ** 3 - s * u ** 2


def ressort(dt, freq=2.2, amort=5.0):
    """Réponse d'un ressort amorti à un échelon : 0 → dépasse 1 → oscille → 1."""
    if dt <= 0:
        return 0.0
    return 1 - math.exp(-amort * dt) * math.cos(2 * math.pi * freq * dt)


def secousse(dt, freq=2.0, amort=4.0):
    """Une impulsion qui part, revient et s'éteint (pic ≈ 1 vers dt = 1 / (4 freq))."""
    if dt <= 0:
        return 0.0
    return math.exp(-amort * dt) * math.sin(2 * math.pi * freq * dt) / math.exp(-amort / (4 * freq))


def pop(t, t0, d=0.35):
    """Échelle d'apparition d'un élément : 0 → 1,08 → 1."""
    return rebond((t - t0) / d, 2.4) if t >= t0 else 0.0


# ------------------------------------------------------------------------------------------------ bruit
def _bruit(*k):
    """Bruit déterministe dans [-1, 1] (même résultat à chaque rendu)."""
    x = math.sin(sum(v * m for v, m in zip(k, (12.9898, 78.233, 37.719, 4.581)))) * 43758.5453
    return 2 * (x - math.floor(x)) - 1


def doux(t, graine=0.0):
    """Bruit lent et continu dans [-1, 1] (somme de sinus), pour les mouvements de vie."""
    return 0.55 * math.sin(1.3 * t + graine) + 0.3 * math.sin(2.9 * t + 1.7 * graine) + 0.15 * math.sin(6.1 * t + 3.1 * graine)


# ------------------------------------------------------------------------------------------------ caméra
class Camera:
    """Caméra virtuelle 2D : zoom et point visé interpolés entre des clés, plus des secousses.

    cles   : [(t, zoom, cx, cy)] — à l'instant t, le point (cx, cy) est au centre de l'écran, grossi `zoom` fois.
             Entre deux clés : mouvement doux. Une clé peut avoir un 5e terme : la durée du mouvement qui y mène
             (par défaut tout l'intervalle ; une durée courte donne un zoom « coup de poing »).
    chocs  : [(t, durée, amplitude en pixels)].
    """

    def __init__(self, cles, chocs=()):
        self.cles = sorted(cles, key=lambda k: k[0])
        self.chocs = list(chocs)

    def etat(self, t):
        c = self.cles
        if t <= c[0][0]:
            return c[0][1:4]
        for a, b in zip(c, c[1:]):
            if t < b[0]:
                d = b[4] if len(b) > 4 else b[0] - a[0]
                u = (t - (b[0] - d)) / d if d > 0 else 1.0
                u = lisse(u) if len(b) <= 4 else sortie(u, 4)
                return tuple(x + (y - x) * u for x, y in zip(a[1:4], b[1:4]))
        return c[-1][1:4]

    def tremble(self, t):
        dx = dy = rot = 0.0
        for t0, d, amp in self.chocs:
            if t0 <= t < t0 + d:
                f = int(t * 60)
                a = amp * (1 - (t - t0) / d) ** 2
                dx += a * _bruit(f, 1)
                dy += 0.6 * a * _bruit(f, 2)
                rot += 0.04 * a * _bruit(f, 3)
        return dx, dy, rot

    def appliquer(self, c, t):
        z, cx, cy = self.etat(t)
        dx, dy, rot = self.tremble(t)
        c.translate(W / 2 + dx, H / 2 + dy)
        c.rotate(rot)
        c.scale(z, z)
        c.translate(-cx, -cy)


# ------------------------------------------------------------------------------------------------ traits
def deplace(traits, dx=0.0, dy=0.0):
    return [[(x + dx, y + dy) for x, y in l] for l in traits]


def echelle(traits, k, cx, cy):
    return [[(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in l] for l in traits]


def tourne(traits, ang, cx, cy):
    """Rotation de `ang` degrés (sens horaire à l'écran) autour de (cx, cy)."""
    a = math.radians(ang)
    co, si = math.cos(a), math.sin(a)
    return [[(cx + (x - cx) * co - (y - cy) * si, cy + (x - cx) * si + (y - cy) * co) for x, y in l] for l in traits]


def plier(traits, ang, pivot, poids):
    """Fléchit un dessin autour de `pivot` : chaque point tourne de ang × poids(x, y) degrés.

    Avec un poids qui passe doucement de 0 (bassin) à 1 (épaules), le buste se penche sans casser les traits.
    """
    px, py = pivot
    out = []
    for l in traits:
        m = []
        for x, y in l:
            a = math.radians(ang * poids(x, y))
            co, si = math.cos(a), math.sin(a)
            m.append((px + (x - px) * co - (y - py) * si, py + (x - px) * si + (y - py) * co))
        out.append(m)
    return out


def vivant(traits, t, amp=0.9, fps=12, graine=0):
    """Traits qui « bouillonnent » comme un dessin animé tracé à la main : un léger décalage qui change
    `fps` fois par seconde (assez lent pour être lu comme un style, pas comme un défaut)."""
    f = int(t * fps)
    out = []
    for i, l in enumerate(traits):
        dx, dy = amp * _bruit(f, i, graine, 1), amp * _bruit(f, i, graine, 2)
        out.append([(x + dx + 0.4 * amp * _bruit(f, i, j, 3), y + dy + 0.4 * amp * _bruit(f, i, j, 4))
                    for j, (x, y) in enumerate(l)])
    return out


# ------------------------------------------------------------------------------------------------ morphing
def _reechantillonne(l, n):
    a = np.asarray(l, dtype=float)
    if len(a) < 2:
        return np.repeat(a[:1], n, axis=0)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(a, axis=0).T))]
    if d[-1] == 0:
        return np.repeat(a[:1], n, axis=0)
    s = np.linspace(0, d[-1], n)
    return np.c_[np.interp(s, d, a[:, 0]), np.interp(s, d, a[:, 1])]


def apparier(A, B, n=24):
    """Prépare la transformation du dessin A en dessin B : (départ, arrivée), deux tableaux (S, n, 2).

    Chaque trait de A est associé au trait de B le plus proche (position et longueur, algorithme hongrois) ;
    un trait sans partenaire naît ou disparaît sur place (il se réduit à son centre).
    """
    RA = [_reechantillonne(l, n) for l in A]
    RB = [_reechantillonne(l, n) for l in B]
    ca = np.array([r.mean(0) for r in RA])
    cb = np.array([r.mean(0) for r in RB])
    la = np.array([np.hypot(*np.diff(r, axis=0).T).sum() for r in RA])
    lb = np.array([np.hypot(*np.diff(r, axis=0).T).sum() for r in RB])
    cout = np.linalg.norm(ca[:, None] - cb[None], axis=2) + 0.5 * np.abs(la[:, None] - lb[None])
    ia, ib = linear_sum_assignment(cout)
    dep, arr = [], []
    for i, j in zip(ia, ib):
        a, b = RA[i], RB[j]
        if np.abs(a - b[::-1]).sum() < np.abs(a - b).sum():                  # même sens de parcours
            b = b[::-1]
        dep.append(a)
        arr.append(b)
    for i in set(range(len(RA))) - set(ia):
        dep.append(RA[i])
        arr.append(np.repeat(ca[i][None], n, axis=0))
    for j in set(range(len(RB))) - set(ib):
        dep.append(np.repeat(cb[j][None], n, axis=0))
        arr.append(RB[j])
    return np.array(dep), np.array(arr)


_PAIRES = {}


def morph(cle, A, B, k, n=24):
    """Le dessin intermédiaire entre A (k = 0) et B (k = 1). `cle` identifie la paire (calcul mis en cache)."""
    if k <= 0:
        return A
    if k >= 1:
        return B
    if cle not in _PAIRES:
        _PAIRES[cle] = apparier(A, B, n)
    dep, arr = _PAIRES[cle]
    m = dep + (arr - dep) * k
    return [list(map(tuple, l)) for l in m]


def _densifie(traits, pas):
    out = []
    for l in traits:
        a = np.asarray(l, dtype=float)
        L = np.hypot(*np.diff(a, axis=0).T).sum() if len(a) > 1 else 0.0
        out.append(_reechantillonne(l, max(2, int(L / pas) + 1)))
    return out


_FLUX = {}


def flux(cle, A, B, k, pas=5.0):
    """Passage du dessin A au dessin B quand leurs traits ne se correspondent pas un à un (deux poses d'un même
    personnage dessinées séparément) : chaque point de A glisse vers le trait de B le plus proche en s'éteignant,
    chaque point de B part du trait de A le plus proche en s'allumant. Les lignes restent sur le dessin à tout
    instant, rien n'éclate.

    Renvoie [(traits, intensité), …] à dessiner avec faisceau(…, intense=intensité).
    """
    if k <= 0:
        return [(A, 1.0)]
    if k >= 1:
        return [(B, 1.0)]
    if cle not in _FLUX:
        from scipy.spatial import cKDTree
        DA, DB = _densifie(A, pas), _densifie(B, pas)
        pa, pb = np.concatenate(DA), np.concatenate(DB)
        ta, tb = cKDTree(pa), cKDTree(pb)
        cibles_a = [pb[tb.query(l)[1]] for l in DA]
        sources_b = [pa[ta.query(l)[1]] for l in DB]
        _FLUX[cle] = (DA, cibles_a, DB, sources_b)
    DA, cibles_a, DB, sources_b = _FLUX[cle]
    m = lisse(k)
    a = [list(map(tuple, l + (c - l) * m)) for l, c in zip(DA, cibles_a)]
    b = [list(map(tuple, s + (l - s) * m)) for l, s in zip(DB, sources_b)]
    return [(a, (1 - k) ** 1.5), (b, k ** 0.7)]
