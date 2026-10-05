---
titre: Les erreurs fréquentes
apercu: Rien ne s'affiche ? Tout est décalé ? Le texte est coupé ? Les causes et les solutions.
---
# Les erreurs fréquentes

## Rien ne s'affiche

Trois causes, dans l'ordre :

1. `y` est **en dehors** de 0 à 1920 (souvent : oublié que `y` descend)
2. `t0` est **après la fin** de la vidéo
3. Un trait n'est **pas dans une liste** : `rect_pts(...)` au lieu de `[rect_pts(...)]`

## `IndexError` sur `s(12)`

`voix.json` contient **moins de phrases** que prévu. La numérotation commence à **0** : avec 12 lignes, la dernière est `s(11)`.

## Tout est décalé par rapport à la voix

Une phrase coupée en deux dans `voix.json` n'a pas été **fusionnée**. Toutes les phrases suivantes ont un numéro de trop.

## Le texte est coupé sur les bords

Le texte est trop long pour sa taille. Rappel :

$$\text{largeur} \approx \text{lettres} \times 0{,}6 \times \text{taille}$$

Coupez sur deux lignes, ou baissez la taille.

## `ModuleNotFoundError: films`

La commande n'est pas lancée **depuis la racine du projet** (`Mon_Dashboard_Client`).

## Le chiffre d'un compteur « clignote »

Vous avez oublié `vitesse=0.0` : le texte est retapé à chaque image.

## Le rendu est lent

C'est normal : 30 images par seconde, 80 secondes, donc 2 400 images. Utilisez l'**aperçu** pour tout régler, et ne lancez le rendu qu'une fois à la fin.
