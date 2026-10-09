# Règle : les planches sont des feuilles de sprites, pour animer comme un jeu vidéo (9 octobre 2026)

Demande de l'utilisateur : les images générées doivent être faites pour être animées en jeu vidéo.

1. **Une ligne = une animation de 4 images** (lues de gauche à droite) : marcher, tirer, tomber, tourner…
2. **Même personnage, même taille, même angle, même ligne de sol** dans toutes les cases d'une ligne : seule la pose
   change. Pas de flou de mouvement, pas de traits de vitesse, pas d'effets (le code les ajoute).
3. **Les pièces qui bougent séparément sont dessinées à part** (la porte sans le passager, le t-shirt seul, le
   parachute…), pour que le code puisse les déplacer.
4. Vue de profil tournée vers la droite pour les personnages (sauf indication) ; visage vide.
5. Grille 4 × 3, fond noir pur, palette stricte, aplats (conversion : planche_vecteur, mêmes familles de couleurs).
6. Conversion : garder l'échelle commune d'une ligne (pas de recadrage case par case), pour que les 4 images se
   superposent exactement.

Début de prompt type :
```
Video game sprite sheet, 4 columns × 3 rows grid of 12 cells, each row is one animation of 4 frames read from left to right. In every row the subject keeps exactly the same design, the same size, the same proportions and the same camera angle; it stands on the same invisible baseline at the same height in each cell and stays centered, only the pose changes from frame to frame. No motion blur, no speed lines, no effects, nothing else in the cells.
```
Fin de prompt type :
```
Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```
