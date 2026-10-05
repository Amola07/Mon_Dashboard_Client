---
titre: Exercices 5 à 7 (corrigés)
apercu: Un compte à rebours, un son avec un flash, et votre premier tableau à vous.
---
# Exercices 5 à 7

## Exercice 5 — Un compte à rebours (20 min)

Dans `tab_deux`, affichez un compte à rebours de 60 à 0, qui descend de 10 par seconde à partir de `s(2)`, en ambre, centré à `y = 560`.

**Corrigé :**

```python
reste = max(0, 60 - 10 * (t - s(2)))
ecrit(c, t, s(2), f"{reste:2.0f} s",
      W / 2, 560, 90, AMBRE,
      True, 1.6, vitesse=0.0)
```

## Exercice 6 — Un son et un flash (15 min)

Ajoutez un bruit métallique et un flash à l'instant où la flèche apparaît (`s(1) + 1.0`).

**Corrigé :**

```python
def chocs():
    flashs = [s(1) + 1.0, s(3)]
    secousses = [(s(3), 0.2)]
    return flashs, secousses
```

et dans `effets()` :

```python
ev.append((s(1) + 1.0, Z.clang(300, 0.2)))
```

## Exercice 7 — Votre tableau (1 h)

Ajoutez un troisième tableau qui commence à `s(3)` avec une transition `"glitch"`, et dessinez-y une voiture vue de côté.

**Pistes :**

1. Copiez la fonction `cote(...)` de l'épisode 23 (`ep23_voiture_eau/oscillo_ep23.py`)
2. Écrivez `tab_trois(c, t)` qui trace `v["caisse"] + v["roues"]`
3. Ajoutez une ligne d'eau qui ondule avec `math.sin(x / 34 + t * 4)`
4. Déclarez-le dans `tableaux()` :

```python
(s(3) - 0.1, tab_trois, "glitch")
```

> **Bravo.** Si vous avez fait les sept exercices, vous savez tout ce qu'il faut pour un épisode complet. Ouvrez l'épisode 23 : vous y reconnaîtrez chaque ligne.
