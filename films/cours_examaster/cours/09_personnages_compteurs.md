---
titre: Personnages, flèches et compteurs
apercu: Un personnage qui change de pose, et un chiffre qui défile — les deux éléments qui font le plus d'effet.
---
# Personnages, flèches et compteurs

## Le personnage

```python
bonhomme(x, y, taille, pose)
```

- `(x, y)` : la position **des pieds**
- `taille` : 1 = environ 76 pixels de haut ; 3 = environ 230
- `pose` : `"debout"`, `"flotte"` (bras levés), `"saut"` (accroupi), `"allonge"`

### Changer de pose en douceur

```python
k = ease((t - s(1) - 0.3) / 0.5)
dessin = bonhomme(540, 1290, 3.0,
                  "debout", "flotte", k)
trace(c, t, s(1), 0.4, dessin, VERT_PALE, 1.2)
```

Quand `k` passe de 0 à 1, le personnage lève les bras.

## Les flèches

```python
fleche(x0, y0, x1, y1)
```

La pointe est en `(x1, y1)`. Une flèche **vers le haut** : `y1` plus **petit** que `y0`.

## Le compteur

Un chiffre qui défile est l'élément le plus efficace pour retenir l'attention.

```python
v = 200 * ease((t - s(4)) / 2.0)
ecrit(c, t, s(4), f"{v:3.0f} kg",
      W / 2, 560, 90, AMBRE,
      True, 1.6, vitesse=0.0)
```

- `v` monte de 0 à 200 en 2 secondes
- `f"{v:3.0f}"` l'écrit **sans décimale**, sur 3 caractères
- `vitesse=0.0` : sinon le chiffre serait « tapé » à chaque image

### Un compte à rebours

```python
reste = max(0, 60 - 10 * (t - s(2)))
```

Il part de 60 et perd 10 par seconde, sans descendre sous 0.
