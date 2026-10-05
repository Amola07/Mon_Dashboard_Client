---
titre: Exercices 1 à 4 (corrigés)
apercu: Changer un titre, déplacer une forme, ajouter une ligne, animer un personnage. Avec les corrigés.
---
# Exercices 1 à 4

Travaillez dans `films/episodes/modele_oscillo/oscillo_modele.py`. Vérifiez **chaque** exercice avec l'aperçu.

## Exercice 1 — Changer le titre (5 min)

Remplacez « MON TITRE » par « N'OUVREZ PAS », en vert pâle, taille 100.

**Corrigé :**

```python
ecrit(c, t, -1.0, "N'OUVREZ PAS",
      W / 2, 330, 100, VERT_PALE,
      True, 2.0, vitesse=0.0)
```

## Exercice 2 — Déplacer et recolorer (10 min)

Mettez le rectangle plus haut et en ambre ; faites-le apparaître au début de la phrase 1.

**Corrigé :**

```python
trace(c, t, s(1), 0.6,
      [rect_pts(240, 560, 840, 1160)],
      AMBRE, 1.3)
```

> Pensez à remonter aussi les pieds du personnage (`y = 1150`), sinon il sort de la boîte.

## Exercice 3 — Une deuxième ligne (10 min)

Sous le titre, à `y = 430`, ajoutez « LA PORTIÈRE », présent dès l'image 0.

**Corrigé :**

```python
ecrit(c, t, -1.0, "LA PORTIÈRE",
      W / 2, 430, 100, VERT_PALE,
      True, 2.0, vitesse=0.0)
```

## Exercice 4 — Faire glisser le personnage (20 min)

Le personnage doit aller de `x = 300` à `x = 780` pendant la phrase 1.

**Corrigé :**

```python
g = ease((t - s(1)) / (e(1) - s(1)))
x = 300 + (780 - 300) * g
dessin = bonhomme(x, 1290, 3.0,
                  "debout", "flotte", k)
trace(c, t, s(1), 0.4, dessin, VERT_PALE, 1.2)
```

On utilise une **autre** variable (`g`) pour ne pas écraser `k`, qui sert déjà à la pose.
