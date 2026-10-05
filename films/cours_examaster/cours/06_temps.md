---
titre: Le temps calé sur la voix
apercu: s(4) + 0.5, ease(), et le seul motif d'animation que vous devez connaître par cœur.
---
# Le temps calé sur la voix

## Un tableau = une fonction redessinée 30 fois par seconde

```python
def tab_mon_tableau(c, t):
    ...
```

- `c` est la toile sur laquelle on dessine
- `t` est l'**instant**, en secondes depuis le début de la vidéo

La fonction **redessine tout** à chaque image. Pour animer, on calcule les positions **à partir de `t`**.

## Parler en phrases, pas en secondes

La voix est découpée en **phrases numérotées à partir de 0**.

| Écriture | Signification |
|---|---|
| `s(4)` | début de la phrase 4 |
| `e(4)` | fin de la phrase 4 |
| `s(4) + 0.5` | une demi-seconde après le début de la phrase 4 |

> Écrivez **toujours** vos instants avec `s()` et `e()`. Si vous refaites la voix, tout reste calé.

## Le motif à connaître par cœur

![La courbe de ease](illustrations/ease.jpg)

```python
k = ease((t - DEBUT) / DUREE)
x = 200 + (800 - 200) * k
```

- Avant `DEBUT` : `k = 0`, donc `x = 200`
- Pendant : `k` monte **doucement** de 0 à 1
- Après `DEBUT + DUREE` : `k = 1`, donc `x = 800`

`ease` démarre et s'arrête en douceur : c'est ce qui rend les mouvements naturels.

## Exemple : glisser pendant une phrase

```python
k = ease((t - s(1)) / (e(1) - s(1)))
x = 300 + (780 - 300) * k
```

L'objet traverse l'écran **exactement** pendant la phrase 1.
