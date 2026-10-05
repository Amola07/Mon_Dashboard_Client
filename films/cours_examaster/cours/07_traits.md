---
titre: Les traits
apercu: Tout dessin est une liste de lignes brisées. Rectangles, cercles, flèches et personnages compris.
---
# Les traits

## La règle

Tout dessin est une **liste de lignes brisées**.
Une ligne brisée est une **liste de points** `(x, y)`.

```python
# un segment
[[(100, 500), (300, 500)]]

# une croix : deux segments
[[(100, 400), (300, 600)],
 [(300, 400), (100, 600)]]
```

## Les formes toutes prêtes

| Fonction | Ce qu'elle donne |
|---|---|
| `rect_pts(x0, y0, x1, y1)` | un rectangle (une ligne brisée) |
| `cercle_pts(x, y, r)` | un cercle (une ligne brisée) |
| `fleche(x0, y0, x1, y1)` | une flèche (déjà une **liste** de lignes) |
| `bonhomme(x, y, taille, pose)` | un personnage (déjà une **liste**) |

> **Attention aux crochets :** `rect_pts` et `cercle_pts` donnent **une** ligne ; il faut les mettre dans une liste : `[rect_pts(...)]`. `fleche` et `bonhomme` sont déjà des listes.

## Additionner des dessins

Ce sont des listes : on les additionne avec `+`.

```python
boite = [rect_pts(240, 700, 840, 1300)]
dessin = boite + fleche(900, 1200, 900, 800)
```

## Les trois couleurs

| Couleur | Usage |
|---|---|
| `VERT` | le décor |
| `VERT_PALE` | le sujet principal |
| `AMBRE` | **une seule** chose importante à la fois |

L'ambre est rare : c'est ce qui le rend fort.
