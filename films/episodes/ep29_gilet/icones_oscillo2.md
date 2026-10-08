# Épisode 29 en « oscilloscope 2.0 » — ce qu'on réutilise et ce qu'il faut générer

Les icônes sont converties en vecteurs par `films/styles/oscillo2.dessiner_icone_sobre` : silhouette au faisceau,
contours des grandes zones en trait fin, hachures sur les zones orange (ambre). Ça marche bien pour les personnages
et les objets isolés, mal pour les scènes dont l'IA a peint le fond (eau, herbe, rivière) : le fond devient des taches.

## Réutilisées telles quelles (planches pixel 15 et 17)

Personnage : `px_gilet_plat`, `px_tire`, `px_gonfle`, `px_flotte`, `px_plafond`, `px_nage`, `px_boule`, `px_grelotte`,
`px_groupe`. Objets : `px_thermometre`, `px_cartouche`, `px_chrono`, `px_talon`, `px_mini_passager`.

## Dessinés par le code (pas d'image)

Eau, cuve, cube, cases, flèches, chiffres en segments, texte, gilet gonflé seul, quadrillage, tampons, cabine en
coupe de l'écran Comores, courbe de Lissajous.

## À générer : 1 planche (9 dessins), objets ISOLÉS, sans aucun fond

```
Flat vector icon sheet, 9 separate objects in a 3 columns × 3 rows grid, each object isolated and centered in its cell, drawn at a similar size, with NOTHING around it: no ground, no water, no sky, no background scenery. 1. a passenger airplane, side view facing right, no logo. 2. the same passenger airplane diving nose-down, side view facing right. 3. a passenger airplane seen from directly above, top view, nose pointing up. 4. a small passenger ferry boat, side view facing left. 5. a side cross-section of an airplane cabin: only the curved fuselage outline, a row of round windows, a row of seats seen from the side and a closed exit door at the right end. 6. an open airplane exit door with its frame, seen from the front, empty doorway. 7. an inflated evacuation slide on its own, side view, without the airplane. 8. the bust of an ancient Greek scholar with a curly beard, side view facing right, simple shapes, blank face. 9. a small tropical island with two palm trees, the island only, no water. Flat vector style, simple bold geometric shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms après conversion : `vx_avion`, `vx_avion_pique`, `vx_avion_dessus`, `vx_ferry`, `vx_cabine`, `vx_porte`,
`vx_toboggan`, `vx_archimede`, `vx_ile` (conversion : `python -m films.outils.planche_pixel planche.webp 3x3 4 …` ;
le facteur 4 garde assez de détail pour des formes plates en haute définition).

## Où chaque dessin sert

| Écran | Dessins |
|---|---|
| 1 Accroche | `vx_avion` sur l'eau du code, `px_gilet_plat` → `px_gonfle` |
| 2 Archimède | `vx_archimede`, puis cuve et cube (code) |
| 3 Le gilet : 16 L, 16 kg | gilet, cases, flèche (code) |
| 4 Dehors | `px_flotte` ou le nageur du code |
| 5 La cabine | `vx_cabine`, `px_plafond`, eau qui monte (code) |
| 6 Comores 1996 | `vx_avion_pique`, `vx_ile`, cabine en coupe et petits passagers (code) |
| 7 Le bon geste | `px_gilet_plat`, `vx_porte`, `px_tire`, `px_gonfle`, `px_cartouche` |
| 8 Le froid ×25 | `px_grelotte`, `px_thermometre` |
| 9 L'Hudson | `vx_avion_dessus` sur l'eau du code, `vx_ferry`, `px_chrono`, 155 cases (code) |
| 10 La position | `px_nage`, `px_boule`, `px_groupe` |
| 11 Le toboggan | `vx_toboggan`, `px_talon` |

## Précision (8 octobre, après le premier rendu complet)

Les dessins sont maintenant convertis depuis la planche en pleine définition (`films/outils/planche_vecteur.py`,
planches dans `films/planches_ia/`), et non plus depuis les icônes réduites en pixels : bords nets, formes justes.
Les objets de la planche 18 (aplats de couleur) sont précis. Les personnages restent grossiers parce que leur planche
est en pixel art : pour qu'ils soient aussi nets que les objets, il faut les regénérer dans le même style.

### Planche 19 — le personnage en aplats de couleur, 9 poses (grille 3 × 3)

```
Flat vector character sheet, 9 poses of the same character in a 3 columns × 3 rows grid, each pose isolated and centered in its cell, drawn at the same size and the same proportions, with NOTHING around him: no ground, no water, no background. A young man with a knitted beanie, a puffer jacket with a few horizontal quilting lines, trousers and sneakers, with a blank face (a plain oval, no eyes, no nose, no mouth). Pose 1: standing, front view, a flat deflated life vest around his neck, arms down. Pose 2: standing, side view facing right, pulling a small tab at the bottom of the deflated life vest with one hand. Pose 3: standing, front view, the life vest fully inflated, big and round around his neck and chest. Pose 4: floating, front view, seen from the chest up, inflated life vest, arms spread out to the sides. Pose 5: lying flat horizontally on his back, side view, the inflated life vest on his chest, legs hanging down. Pose 6: swimming crawl, side view facing right, one arm stretched forward. Pose 7: curled up in a ball, side view, knees pulled up to the chest, arms crossed over the inflated life vest. Pose 8: standing, front view, shivering, arms wrapped around himself. Pose 9: three people in inflated life vests holding each other in a tight circle, seen from above. Flat vector style, simple bold shapes, large flat color areas, clear separation between body parts (the far arm and far leg one tone darker), no outlines, no gradients, no texture, each color used in at most two tones: beanie and trousers teal #28AFAF and dark teal #1A6E70, life vest orange #FF8A3D and dark orange #A8481A, face and hands off-white #ECF2F0, jacket grey #788284 with off-white #ECF2F0 highlights, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms : `fx_gilet_plat`, `fx_tire`, `fx_gonfle`, `fx_flotte`, `fx_plafond`, `fx_nage`, `fx_boule`, `fx_grelotte`,
`fx_groupe` (conversion : `python -m films.outils.planche_vecteur planche.webp 3x3 fx_…`).

### Planche 20 — les petits objets en aplats (grille 3 × 2)

```
Flat vector icon sheet, 6 separate objects in a 3 columns × 2 rows grid, each object isolated and centered in its cell, drawn at a similar size, with NOTHING around it: 1. a small metal gas cartridge with a pull tab on a short cord. 2. a glass thermometer with a low level of liquid. 3. a woman's high-heeled shoe, side view. 4. a stopwatch with a button on top and a plain dial with no numbers. 5. a flat deflated life vest seen from the front. 6. an inflated life vest seen from the front, round and puffy. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones, strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms : `fx_cartouche`, `fx_thermometre`, `fx_talon`, `fx_chrono`, `fx_gilet_vide`, `fx_gilet_gonfle`.
