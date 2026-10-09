"""Épisode 30 — version « jeu vidéo » (comme l'ép. 21, la vidéo qui a fait le plus de vues).

Même voix, mêmes tableaux que oscillo2_ep30.py, plus :
- le son d'un jeu 8 bits à la place de la nappe (films/styles/son_jeu.py) : un bip quand le faisceau trace, un clic
  par lettre du titre, des tics de pièce quand un compteur tourne, power-up, explosion, buzzer, ennemi, fanfare… ;
- un écran de jeu : « NIVEAU k » en haut à gauche, une barre de vie « FORÊT » en haut à droite (elle se remplit quand
  la forêt double, se vide quand elle s'épuise), des bandeaux d'événement qui clignotent, « ⏸ PAUSE » sur MAIS
  ATTENDEZ ;
- les sous-titres en bas, tapés au rythme de la voix.

    python -m films.episodes.ep30_foret.jeu_ep30 output/ep30_jeu.mp4 [t0 t1]
"""
import json
import math
import os
import sys
import wave

import numpy as np

from films import montage_ia as MI
from films.episodes.ep30_foret import oscillo2_ep30 as E
from films.styles import anim_pro as A
from films.styles import oscillo2 as O
from films.styles import oscillo_son as Z
from films.styles import son_jeu as J
from films.styles.oscillo2 import AMBRE, VERT, VERT_PALE, VERT_SOMBRE, W

T = E.T
SONS = {}                                 # les sons déclenchés par l'image : clé → (instant, son)


def ajoute(cle, t0, fabrique):
    if cle not in SONS and t0 >= 0:
        SONS[cle] = (t0, fabrique)


# ------------------------------------------------------------------------------------------------ l'image fait du bruit
_phrase, _apparait, _icone, _tampon, _compteur, _foret = E.phrase, E.apparait, E.icone, E.tampon, E.compteur, E.foret_carte


def phrase(c, t, t0, lignes, t1=None, y=300, h=64):
    n = min(12, sum(len(l.replace("*", "").replace(" ", "")) for l in lignes))
    for i in range(n):                                     # une lettre qui s'écrit = un clic
        ajoute(("lettre", t0, i), t0 + 0.4 * i / n, J.lettre)
    _phrase(c, t, t0, lignes, t1, y, h)


def _f(nom):
    return 600 + (sum(map(ord, nom)) % 7) * 90


def apparait(c, t, t0, nom, cx, bas, h, a=1.0, d=0.6, hach=("ambre", "vert")):
    for i in range(max(1, int(d / 0.13))):                 # le faisceau trace : un bip toutes les 0,13 s
        ajoute(("trace", nom, round(t0, 2), i), t0 + 0.13 * i, (lambda f: lambda: J.trace(f))(_f(nom) + 120 * (i % 3)))
    _apparait(c, t, t0, nom, cx, bas, h, a, d, hach)


def icone(c, nom, cx, bas, h, a=1.0, u=None, hach=("ambre", "vert")):
    if u is None and E._T0 > 0:
        for i in range(6):
            ajoute(("trace", nom, round(E._T0, 2), i), E._T0 - 0.25 + 0.13 * i,
                   (lambda f: lambda: J.trace(f))(_f(nom) + 120 * (i % 3)))
    return _icone(c, nom, cx, bas, h, a, u, hach)


def tampon(c, t, t0, txt, cx, cy, ang=-7, h=46):
    ajoute(("tampon", round(t0, 2)), t0, J.faux if txt == "CLICHÉ" else J.niveau)
    ajoute(("tampon_x", round(t0, 2)), t0, lambda: J.explosion(0.12, 0.3))
    _tampon(c, t, t0, txt, cx, cy, ang, h)


def compteur(c, t, t0, v0, v1, x, y, h, d=0.9, fmt="{:.0f}", col=AMBRE, a=1.0):
    for i in range(int(d / 0.06)):
        ajoute(("compte", round(t0, 2), i), t0 + 0.06 * i, (lambda i: lambda: J.tic_compteur(i))(i))
    ajoute(("compte_fin", round(t0, 2)), t0 + d, J.piece)
    _compteur(c, t, t0, v0, v1, x, y, h, d, fmt, col, a)


def foret_carte(c, t, t0, n, a=1.0, d=1.2):
    for i in range(0, min(n, 200), 4):                     # les arbres qui poussent en rafale
        ajoute(("arbre", round(t0, 2), i), t0 + d * i / max(1, n), (lambda i: lambda: J.trace(900 + 60 * (i % 8), 0.03))(i))
    _foret(c, t, t0, n, a, d)


E.phrase, E.apparait, E.icone, E.tampon, E.compteur, E.foret_carte = phrase, apparait, icone, tampon, compteur, foret_carte


# ------------------------------------------------------------------------------------------------ l'écran de jeu
def niveaux():
    ec = E.ecrans()
    return [(ec[i][0], k) for k, i in enumerate((0, 2, 3, 6, 9, 10, 12, 13), start=1)]


def vie(t):
    """La barre de vie de la forêt : 0,5 en 1830, pleine quand elle a doublé, puis elle s'épuise."""
    v = 0.5
    v += 0.5 * A.lisse((t - T["dixsept"]) / 1.2)
    v -= 0.38 * A.lisse((t - T["trente"]) / 0.8)                 # le puits de carbone : −38 %
    v -= 0.2 * A.lisse((t - T["meurent"]) / 1.0)                 # la mortalité
    v += 0.06 * A.lisse((t - T["dixsept2"]) / 1.0)               # le stock qui grossit encore un peu
    return max(0.05, v)


def hud(c, t):
    k = [n for t0, n in niveaux() if t >= t0 - 0.25][-1]
    O.dessiner(c, O.texte(f"NIVEAU {k}", 90, 190, 30, centre=False, gras=True), VERT, 1.8, 0.9)
    x0, x1, y = 640, 990, 172
    v = vie(t)
    O.dessiner(c, O.texte("FORÊT", x0 - 18 - O.largeur_texte("FORÊT", 26), y + 18, 26, centre=False), VERT, 1.6, 0.9)
    O.dessiner(c, [E.rect(x0, y, x1, y + 22)], VERT_PALE, 2, 0.9)
    bas = v < 0.45 and int(t * 4) % 2 == 0                       # la barre clignote quand elle est basse
    col = AMBRE if v < 0.45 else VERT
    n = int(22 * v)
    O.dessiner(c, [E.rect(x0 + 5 + i * 15.4, y + 5, x0 + 15 + i * 15.4, y + 17) for i in range(n)], col, 2.2,
               0.4 if bas else 1.0)


BANDEAUX = [  # (repère, décalage, durée, texte)
    ("autriche", 0.9, 1.6, "+ 8 000 000 HA"), ("normal", 0.0, 1.2, "! CLICHÉ DÉTECTÉ"), ("double", 0.0, 1.4, "BONUS x2"),
    ("dixhuit2", 0.0, 1.5, "! NOUVELLE LOI"), ("jamais", 0.0, 0.7, "! INFO MANQUANTE"), ("trente", 0.1, 1.5, "! ALERTE CO2"),
    ("meurent", 0.0, 1.4, "- VIE"), ("scolyte", 0.0, 1.6, "! ENNEMI : LE SCOLYTE"), ("metres", 0.3, 1.2, "K.O."),
    ("dixsept2", 1.0, 1.2, "+ 17 % STOCK"), ("epuise", 0.0, 1.4, "! FORÊT ÉPUISÉE"), ("justement", 0.0, 1.4, "NIVEAU SUIVANT : 2125")]


def bandeaux(c, t):
    for rep, dt, d, txt in BANDEAUX:
        t0 = T[rep] + dt
        if t0 <= t < t0 + d and (int((t - t0) * 6) % 2 == 0 or t - t0 > 0.5):
            lg = O.largeur_texte(txt, 34) + 50
            O.dessiner(c, [E.rect(W / 2 - lg / 2, 560, W / 2 + lg / 2, 612)], AMBRE, 2.4)
            O.dessiner(c, O.texte(txt, W / 2, 600, 34, gras=True), AMBRE, 2.2)


def pause(c, t):
    t0 = T["attendez"] - 0.2
    if t0 <= t < T["foret3"] - 0.1:
        O.dessiner(c, [E.rect(90, 660, 104, 700), E.rect(116, 660, 130, 700)], VERT_PALE, 3)
        O.dessiner(c, O.texte("ARRÊT SUR IMAGE", 150, 692, 30, centre=False), VERT_PALE, 1.6)


# les sous-titres : le texte affiché de chaque morceau de voix (avec les chiffres), tapé au rythme de la voix
AFFICHE = """La France a gagné une forêt grande comme l'Autriche.|Et presque|personne n'est au courant.|Quand je dis forêt française, vous pensez sûrement à ça :|des coupes rases,|des incendies,|des arbres qui disparaissent.|Normal,|moi aussi.|Sauf qu'en 1830,|la forêt couvrait 9 millions d'hectares.|Aujourd'hui ?|17 millions et demi.|Un tiers du pays.|Elle a presque doublé.|Et l'histoire des Landes|m'a complètement scotché.|Comment c'est possible ?|Les paysans sont partis en ville.|Les champs abandonnés sont redevenus des bois.|Tout seuls.|Et les Landes ?|Il y a 170 ans, c'était une immense lande,|souvent marécageuse,|où les bergers se déplaçaient sur des échasses.|En 1857,|une loi oblige les communes à planter.|Résultat :|près d'un million d'hectares de pins.|Cette forêt que vous traversez sur la route des vacances ?|Elle a été plantée par l'homme.|Alors pourquoi on est|tous persuadés que la forêt recule ?|Le truc,|c'est que notre cerveau retient ce qui se dégrade,|pas ce qui s'améliore.|Un incendie passe au journal de 20 heures.|Un arbre qui pousse,|jamais.|Mais attendez,|parce que c'est là que ça devient inquiétant.|Une forêt, c'est une éponge à CO2.|Entre 2005 et 2013, la nôtre en absorbait 63 millions de tonnes par an.|Et aujourd'hui,|à votre avis ?|39.||Presque|40 % de moins,|en dix ans.|Pourquoi ?|Parce que les arbres meurent.|Il meurt deux fois plus de bois qu'il y a quinze ans.|La sécheresse les affaiblit.|Et un insecte finit le travail :|le scolyte.|5 millimètres.|Il tue des épicéas de 30 mètres.|Et pourtant,|le carbone stocké dans la forêt continue d'augmenter :|+ 17 %|depuis 2009.|Elle grossit.|Mais elle respire de plus en plus mal.|Alors,|est-ce qu'on a peur de la bonne chose ?|Le problème, ce n'est pas une forêt qui disparaît.|C'est une forêt qui s'épuise.|Et je sais ce que vous allez me dire :|il suffit de planter des arbres.|Justement.|Un arbre planté aujourd'hui aura 100 ans en 2125.|Il faut donc planter pour un climat qui n'existe|pas encore.|Et les forestiers ont trouvé une idée…|mais je n'ai plus le temps ici,|donc je vous la montre demain,|et vous allez voir|que…""".split("|")
MORCEAUX = []                             # (début, fin, texte) dans le temps de la vidéo


def lignes_st(txt, larg=880, h=36):
    mots, out, cour = txt.split(), [], ""
    for m in mots:
        essai = (cour + " " + m).strip()
        if O.largeur_texte(essai, h) > larg and cour:
            out.append(cour)
            cour = m
        else:
            cour = essai
    return out + [cour] if cour else out


def sous_titres(c, t):
    for a, b, txt in MORCEAUX:
        if a - 0.05 <= t < b + 0.35 and txt:
            u = min(1.0, (t - a + 0.05) / max(0.3, b - a))           # tapé au rythme de la voix
            ls = lignes_st(txt.upper())
            total = sum(len(l) for l in ls)
            k = int(total * u + 0.999)
            for i, l in enumerate(ls):
                vis = l[:max(0, k)]
                k -= len(l)
                if vis:
                    x = W / 2 - O.largeur_texte(l, 36) / 2
                    O.dessiner(c, O.texte(vis, x, 1745 + i * 50 - 50 * (len(ls) - 1), 36, centre=False),
                               VERT_PALE, 1.8, 0.9)
            return


_image = E.image


def image(c, t):
    _image(c, t)
    if t < T["fin"]:
        hud(c, t)
        bandeaux(c, t)
        pause(c, t)
        sous_titres(c, t)


E.image = image


# ------------------------------------------------------------------------------------------------ le son
def sons_jeu():
    ec = E.ecrans()
    ev = [(0.0, J.selection), (0.05, lambda: J.alerte(1, 0.05))]
    ev += [(b - 0.2, lambda: Z.whoosh(0.35, 0.05)) for b, f in ec[1:-1] if f is not E.e8]
    ev += [(T["autriche"] + 0.9, J.powerup), (T["personne"], J.piece),
           (T["coupes"] - 0.1, J.tronconneuse), (T["incendies"], lambda: Z.crepitement(1.2, 0.07)),
           (T["disparaissent"], J.degat), (T["sauf"] - 0.05, J.selection),
           (T["neuf"], J.piece), (T["landes1"], J.selection), (T["landes1"] + 0.4, J.selection),
           (T["redevenus"], J.powerup), (T["seuls"], J.piece),
           (T["bergers"], J.saut), (T["planter"], J.powerup), (T["resultat"], J.piece),
           (T["cette"], lambda: J.moteur(T["plantee"] - T["cette"] + 1.0)),
           (T["cerveau"], J.selection), (T["ameliore"], J.degat), (T["incendie"] + 0.2, lambda: Z.crepitement(0.9, 0.06)),
           (T["jamais"], J.faux),
           (T["attendez"] - 0.2, J.pause), (T["attendez"] - 0.2, lambda: Z.neige(0.22, 0.2)),
           (T["inquietant"], lambda: J.alerte(2)),
           (T["eponge"], J.aspire), (T["avis"], J.selection), (T["trente"], lambda: J.explosion(0.22)),
           (T["trente"] + 0.1, J.degat), (T["quarante"], lambda: J.alerte(1)),
           (T["meurent"], J.degat), (T["meurent"] + 0.4, J.degat), (T["secheresse"], lambda: Z.craquement(0.15)),
           (T["scolyte"], J.ennemi), (T["metres"] + 0.3, lambda: J.explosion(0.25)), (T["metres"] + 0.35, J.faux),
           (T["pourtant"], J.selection), (T["respire"], lambda: Z.souffle(1.2, 0.08, True)),
           (T["respire"] + 1.3, lambda: Z.souffle(1.2, 0.06, False)),
           (T["disparait"] + 0.3, J.faux), (T["epuise"], J.degat), (T["epuise"] + 0.05, lambda: J.explosion(0.15)),
           (T["justement"], J.niveau), (T["cent"], lambda: J.montee(2.0)), (T["climat"], lambda: J.alerte(2, 0.05)),
           (T["forestiers"], J.selection), (T["idee"], J.pause),
           (T["fin"], lambda: J.explosion(0.2, 0.5)), (T["fin"] + 0.1, J.suite_demain)]
    tp = T["paysans"] - 0.2                                  # les pas du paysan
    ev += [(tp + 0.28 * i, J.pas_) for i in range(int((T["champs"] - tp) / 0.28))]
    for x0, v in ((T["cinq"], 63), (T["trente"], 39)):       # les barres qui montent
        ev += [(x0 + 0.05 * i, (lambda i: lambda: J.tic_compteur(i))(i)) for i in range(14)]
    ta = T["aujourdhui"]                                     # l'année et les hectares qui défilent
    ev += [(ta + 0.05 * i, (lambda i: lambda: J.tic_compteur(i))(i)) for i in range(20)]
    ev += [(T["dixsept"] + 0.05 * i, (lambda i: lambda: J.tic_compteur(i + 2))(i)) for i in range(18)]
    ev += [(T["dixsept"] + 1.0, J.piece)]
    if T["avis"] < T["trente"]:                              # le « ? » qui clignote
        ev += [(T["avis"] + 0.5 * i, lambda: J.trace(1200)) for i in range(int((T["trente"] - T["avis"]) / 0.5))]
    return ev


def mixage(chemin, voix, dur):
    n = int(dur * MI.SR)
    v = np.zeros(n)
    v[:min(n, len(voix))] = voix[:n]
    v *= 10 ** (-16 / 20) / (np.sqrt((v[np.abs(v) > 0.01] ** 2).mean()) + 1e-9)
    fx = np.zeros(n)
    for t0, fab in list(SONS.values()) + sons_jeu():       # pas de nappe : le son suit l'image
        snd = fab()
        i = int(t0 * MI.SR)
        k = min(n - i, len(snd))
        if k > 0 and i >= 0:
            fx[i:i + k] += snd[:k]
    a = v + 0.8 * fx
    a *= np.minimum(1, (n - np.arange(n)) / (0.6 * MI.SR))
    a = a / max(1.0, np.abs(a).max() / 0.95)
    with wave.open(chemin, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(MI.SR)
        f.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


E.mixage = mixage


def preparer():
    voix = _preparer()
    ici = os.path.dirname(os.path.abspath(__file__))
    _, N, _ = MI.tighten(MI.load_voice(os.path.join(ici, "audio", "voix.mp3")), max_gap=0.40, thr_db=-38.0)
    d = json.load(open(os.path.join(ici, "audio", "voix.json")))
    MORCEAUX[:] = [(N(a), N(b), txt) for (a, b, _), txt in zip(d, AFFICHE)]
    return voix


_preparer = E.preparer
E.preparer = preparer


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "output/ep30_jeu.mp4"
    if len(sys.argv) > 3:
        E.rendre(out, float(sys.argv[2]), float(sys.argv[3]))
    else:
        E.rendre(out)
