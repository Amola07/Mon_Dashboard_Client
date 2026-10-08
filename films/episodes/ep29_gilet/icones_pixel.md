# Épisode 29 en style « infographie pixel » — icônes à générer

Style validé le 8 octobre (test : `pixel_archimede.py`, boîte à outils : `films/styles/pixel_info.py`).
Ce qui est simple reste dessiné par le code : cuve, cube, cases, flèches, eau, gilet gonflé, compteurs, grilles,
coches, croix, ligne de mer. Les icônes ci-dessous sont celles que le code ne sait pas bien dessiner.

## Règles pour que les icônes passent bien dans la vidéo

- **Fond noir pur** (#000000) : le code le rend transparent. Nos couleurs les plus sombres ne sont jamais noires.
- **Palette imposée** dans le prompt ; le code ramène ensuite chaque pixel à la couleur la plus proche de notre palette
  (les petites différences de teinte de l'IA disparaissent).
- **Gros pixels visibles, sans lissage** : le code retrouve la taille réelle du pixel et réduit l'image à sa vraie
  définition, puis l'agrandit ×4 comme le reste.
- **Grille avec beaucoup d'espace noir** entre les cases, sans cadre ni numéro : le code découpe les cases tout seul.
- Même personnage partout : jeune homme, bonnet tricoté bleu-vert, doudoune grise, visage vide, gilet orange.

## Planche 15 — le personnage, 9 poses (grille 3 × 3)

```
Pixel art sprite sheet, 9 poses of the same character in a 3 columns × 3 rows grid: a young man with a teal knitted beanie, a grey puffer jacket and dark teal trousers, with a blank off-white face (no eyes, no nose, no mouth), same size and same proportions in every pose. Pose 1: standing, front view, a flat deflated orange life vest around his neck, arms down. Pose 2: standing, side view facing right, pulling a small tab at the bottom of the deflated orange life vest with one hand. Pose 3: standing, front view, the orange life vest fully inflated, big and round around his neck and chest. Pose 4: floating in the sea, front view, only his head, shoulders and the inflated orange life vest above a teal water line, arms spread on the water. Pose 5: lying flat horizontally, side view, pressed under a straight horizontal ceiling line, the inflated orange life vest on his chest, legs hanging down. Pose 6: swimming hard, side view facing right, arms stretched forward, small teal splashes. Pose 7: floating curled up in a ball, side view, knees pulled up to the chest, arms crossed over the inflated orange life vest, teal water line at chest height. Pose 8: standing waist-deep in teal water, front view, shivering, arms wrapped around himself, a few short off-white shiver lines around him. Pose 9: three people in inflated orange life vests floating close together in a tight circle, holding each other, seen from above, teal water around them. Pixel art, chunky visible pixels, each figure about 64 pixels tall, upscaled with nearest neighbour, no anti-aliasing, no black outlines, flat shading with only 2 or 3 tones per color, strictly limited palette: teal #28AFAF, dark teal #1A6E70, very dark teal #0E3438, orange #FF8A3D, light orange #FFC48C, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no gradient, no glow, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms après conversion : `px_gilet_plat`, `px_tire`, `px_gonfle`, `px_flotte`, `px_plafond`, `px_nage`, `px_boule`,
`px_grelotte`, `px_groupe`.

## Planche 16 — les avions et la cabine (grille 3 × 2)

```
Pixel art scene sheet, 6 separate drawings in a 3 columns × 2 rows grid, each drawn at a similar width, passenger airplanes with no logo and no text: 1. a passenger airplane floating on a calm sea, side view facing right, the bottom of the fuselage in teal water, a few wave lines. 2. a passenger airplane diving nose-down toward the sea, side view facing right, a small island with two palm trees on the horizon at the right. 3. a passenger airplane floating on a river, seen from slightly above, tiny people standing on both wings, a small ferry boat approaching from the right. 4. a side cross-section of an airplane cabin: the curved fuselage outline, a row of round windows, a row of seats seen from the side, and a closed exit door at the right end, empty cabin, no water. 5. an open airplane exit door seen from inside the cabin, a bright teal sky beyond the opening. 6. an inflatable evacuation slide going from an open airplane door down to the ground, side view. Pixel art, chunky visible pixels, each drawing about 96 pixels wide, upscaled with nearest neighbour, no anti-aliasing, no black outlines, flat shading with only 2 or 3 tones per color, strictly limited palette: teal #28AFAF, dark teal #1A6E70, very dark teal #0E3438, orange #FF8A3D, light orange #FFC48C, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no gradient, no glow, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms : `px_avion_mer`, `px_avion_pique`, `px_hudson`, `px_cabine`, `px_porte`, `px_toboggan`.

## Planche 17 — les objets (grille 3 × 3)

```
Pixel art icon sheet, 9 separate objects in a 3 columns × 3 rows grid, each object centered in its cell and drawn at a similar size: 1. a small metal gas cartridge with a pull tab on a short cord. 2. a glass thermometer with a low level of teal liquid. 3. a woman's high-heeled shoe, side view. 4. a stopwatch with a button on top and a plain dial with no numbers. 5. a tiny seated airplane passenger seen from the front, teal beanie, orange life vest, blank face. 6. a flat deflated life vest, folded, seen from the front. 7. the bust of an ancient Greek scholar with a curly beard and a toga, blank face, side view facing right. 8. a small tropical island with two palm trees on a teal sea. 9. a small inflatable round life raft with a canopy, seen from the side, on teal water. Pixel art, chunky visible pixels, each icon about 48 pixels tall, upscaled with nearest neighbour, no anti-aliasing, no black outlines, flat shading with only 2 or 3 tones per color, strictly limited palette: teal #28AFAF, dark teal #1A6E70, very dark teal #0E3438, orange #FF8A3D, light orange #FFC48C, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no gradient, no glow, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms : `px_cartouche`, `px_thermometre`, `px_talon`, `px_chrono`, `px_mini_passager`, `px_gilet_plie`,
`px_archimede`, `px_ile`, `px_radeau`.

## Où chaque icône sert dans l'épisode 29

| Écran | Icônes de l'IA | Dessiné par le code |
|---|---|---|
| 1 Accroche | `px_avion_mer`, `px_gilet_plat`, `px_tire` | tampon « PAS TOUT DE SUITE », gilet gonflé barré |
| 2 Archimède | `px_archimede` | cuve, cube, eau, flèche, pourcentage (fait) |
| 3 Le gilet : 16 L, 16 kg | — | gilet, 16 cases, flèche « 16 KG » (fait) |
| 4 Dehors | `px_flotte` (ou le nageur du code) | eau, flèche, « SANS EFFORT » (fait) |
| 5 La cabine | `px_cabine`, `px_plafond` | l'eau qui monte, la porte sous l'eau, le chemin barré |
| 6 Comores 1996 | `px_avion_pique`, `px_ile`, `px_mini_passager` | grille de passagers qui montent au plafond |
| 7 Le bon geste | `px_gilet_plat`, `px_porte`, `px_tire`, `px_gonfle`, `px_cartouche` | coches et croix |
| 8 Le froid ×25 | `px_flotte`, `px_thermometre` | flèches de chaleur, « × 25 » |
| 9 L'Hudson | `px_hudson`, `px_chrono` | « 2 °C », « 155 / 155 » en grille |
| 10 La position | `px_nage`, `px_boule`, `px_groupe` | flèches de chaleur qui diminuent |
| 11 Le toboggan | `px_toboggan`, `px_talon` | « ? » |

`px_grelotte` et `px_radeau` sont en réserve (épisode suivant).

## Ensuite

Quand les 3 planches sont générées : un outil `planche_pixel` les découpe, rend le fond transparent, retrouve la
taille réelle des pixels et ramène les couleurs à la palette, puis j'écris l'épisode 29 complet dans ce style.
