---
titre: Premier rendu et aperçu rapide
apercu: Deux commandes à connaître par cœur — l'aperçu (3 secondes) et le rendu (quelques minutes).
---
# Premier rendu et aperçu rapide

## Le modèle

Le fichier `films/episodes/modele_oscillo/oscillo_modele.py` est un épisode **complet et minuscule** : deux tableaux, une voix de 11 secondes. Voici ce qu'il produit :

![Le modèle à 0,3 s, 2 s, 5,5 s et 8,5 s](illustrations/modele.jpg)

## Commande 1 : l'aperçu (quelques secondes)

```bash
python -m films.outils.apercu \
  films.episodes.modele_oscillo.oscillo_modele \
  0 2 4.5 7 8.5
```

Elle écrit `output/apercu.png` : l'écran **à chacun des instants donnés** (en secondes), côte à côte.

> **Le secret de la vitesse :** passez **90 % de votre temps** sur l'aperçu. Vous modifiez, vous relancez, vous regardez. Trois secondes à chaque fois.

## Commande 2 : le rendu (quelques minutes)

```bash
python -m films.episodes.modele_oscillo.oscillo_modele \
  output/modele.mp4
```

Ne la lancez qu'à la fin, quand l'aperçu vous plaît.

## Ce que fait le rendu

1. Il resserre les silences de la voix (au plus 0,4 s)
2. Il dessine **30 images par seconde**
3. Il ajoute les bips, les sons, les sous-titres
4. Il règle le volume au niveau TikTok
