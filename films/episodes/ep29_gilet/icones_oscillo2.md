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
