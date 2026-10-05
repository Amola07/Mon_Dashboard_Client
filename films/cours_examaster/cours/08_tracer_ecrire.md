---
titre: Tracer, écrire, titrer
apercu: Les trois fonctions que vous utiliserez dans chaque tableau.
---
# Tracer, écrire, titrer

## `trace` : dessiner au faisceau

```python
trace(c, t, t0, d, traits, col, w)
```

Dessine `traits` progressivement entre `t0` et `t0 + d`, avec un bip au départ.

| Paramètre | Rôle |
|---|---|
| `t0` | quand le tracé commence |
| `d` | sa durée (0 = d'un coup) |
| `col` | la couleur |
| `w` | l'épaisseur, de 1 à 2 |

```python
trace(c, t, s(1), 0.6,
      [rect_pts(240, 700, 840, 1300)],
      VERT_PALE, 1.3)
```

> Pour ce qui **bouge à chaque image** (un point qui tourne), utilisez plutôt `faisceau(c, traits, 1.0, col, w)` : pas de tracé progressif, pas de bip.

## `ecrit` : un texte

```python
ecrit(c, t, t0, "TEXTE", x, y, taille, col)
```

Options utiles :

- `vitesse=0.0` → le texte apparaît **d'un coup** (sinon il est tapé lettre par lettre)
- `halo=2.0` → plus lumineux
- `centre=False` → `x` désigne le bord gauche au lieu du centre

## Un texte présent dès l'image 0

```python
ecrit(c, t, -1.0, "N'OUVREZ PAS",
      W / 2, 300, 88, AMBRE,
      True, 2.2, vitesse=0.0)
```

`t0 = -1.0` : il « a commencé » avant la vidéo, il est donc **déjà là** à la première image. C'est la règle n°1.

## `titres` : la ligne de titre qui change

```python
titres(c, t, [
    (s(2), "POURQUOI ?", VERT_PALE, 70),
    (s(3), "LA PRESSION", AMBRE, 70),
])
```

Une seule ligne en haut (`y = 330`) : à chaque instant, le **dernier titre commencé** s'affiche.
