# Épisode 30 — les planches à générer

Même méthode que la planche 18 : objets isolés, aplats de couleur, palette stricte, fond noir. Chaque planche est
convertie en dessins vectoriels précis :

    python -m films.outils.planche_vecteur planche21.webp 3x3 nom1 … nom9

Générer en carré, la plus grande définition possible (2048 × 2048 ou plus).

## Réutilisé (déjà dans le dépôt)

`fe_flammes`, `fe_fumee` (incendie), `voiture` (route des vacances), `molecule`, `nuage` (CO2),
`fr_thermometre` / `px_thermometre` (climat).

## Dessiné par le code (pas d'image)

Cartes de France et d'Autriche (tracées depuis les vraies frontières, paquet npm `world-atlas`), grille de 100 cases,
barres 63 → 39, compteurs en segments, frise 2025 → 2125, flèches CO2, jauge +17 %, marais (lignes d'eau), champ
(sillons), curseurs de mesure 5 mm / 30 m.

## Planche 21 — les arbres (3 × 3)

```
Flat vector icon sheet, 9 separate trees in a 3 columns × 3 rows grid, each tree isolated and centered in its cell, drawn at a similar height, with NOTHING around it: no ground line, no grass, no sky, no background scenery. 1. a healthy broadleaf oak tree with a full round green crown, side view. 2. the same oak tree dead and dry: bare twisted branches, no leaves. 3. a tall healthy spruce tree, narrow cone shape. 4. the same spruce tree dead: brown-orange dry needles, some bare grey branches. 5. a maritime pine tree with a tall bare straight trunk and a flat umbrella-shaped crown on top. 6. a group of five cut tree stumps of different sizes, seen slightly from above, a clear-cut. 7. a tree burning: orange flames rising from its crown. 8. a tiny sapling with three leaves in a small mound of soil. 9. a gigantic hundred-year-old oak tree with a very thick trunk and a huge wide crown. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms : `vx_chene`, `vx_chene_mort`, `vx_epicea`, `vx_epicea_mort`, `vx_pin`, `vx_souches`, `vx_arbre_feu`,
`vx_pousse`, `vx_chene_centenaire`.

## Planche 22 — les personnages et l'histoire (3 × 3)

```
Flat vector character and object sheet, 9 separate drawings in a 3 columns × 3 rows grid, each isolated and centered in its cell, with NOTHING around it: no ground, no background scenery. All people have a blank face (a plain oval, no eyes, no nose, no mouth). 1. a 19th-century shepherd from the Landes of Gascony standing on very tall wooden stilts, holding a long staff, wearing a wool cape and a beret, side view facing right. 2. a sheep, side view facing left. 3. a 19th-century peasant with a cloth bundle on a stick over his shoulder, walking away to the right, side view. 4. a small 19th-century industrial town: a few houses and two factory chimneys with smoke, side view. 5. an abandoned small farmhouse with a broken roof, side view. 6. a forester in work clothes and a helmet, kneeling and planting a young sapling with both hands, side view facing right. 7. a hand holding a tiny sapling with its root ball. 8. an old box-shaped television set with a blank empty screen and two small antennas. 9. a family car seen from the side facing right, with luggage and a bicycle on its roof rack. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms : `vx_berger_echasses`, `vx_mouton`, `vx_paysan`, `vx_ville_1850`, `vx_ferme`, `vx_forestier`,
`vx_main_pousse`, `vx_tele`, `vx_voiture_vacances`.

## Planche 23 — la science et le cerveau (3 × 3)

```
Flat vector icon sheet, 9 separate objects in a 3 columns × 3 rows grid, each object isolated and centered in its cell, drawn at a similar size, with NOTHING around it: no background scenery. 1. a human brain, side view. 2. a natural sea sponge, round and full of holes. 3. a bark beetle seen from directly above, magnified, six legs, short antennae. 4. a magnifying glass, tilted. 5. a square patch of dry cracked earth seen from above, deep cracks. 6. a blazing sun with short thick rays. 7. a pair of human lungs, front view. 8. a chainsaw, side view. 9. a balance scale with two empty pans, perfectly level. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms : `vx_cerveau`, `vx_eponge`, `vx_scolyte`, `vx_loupe`, `vx_sol_sec`, `vx_soleil`, `vx_poumons`,
`vx_tronconneuse`, `vx_balance`.

## Où chaque dessin sert

| Passage du texte | Dessins |
|---|---|
| « une forêt grande comme l'Autriche » | cartes (code), `vx_chene` en rafale dans la carte |
| « coupes rases, incendies, arbres qui disparaissent » | `vx_tronconneuse`, `vx_souches`, `vx_arbre_feu` / `fe_flammes` — tamponnés CLICHÉ |
| « 9 millions… 17 millions et demi… un tiers du pays » | carte qui se remplit (code), grille 100 cases (code) |
| « les paysans sont partis en ville… redevenus des bois » | `vx_paysan`, `vx_ville_1850`, `vx_ferme`, champ (code) → `vx_pousse` → `vx_chene` |
| « les Landes… bergers sur des échasses… 1857… pins » | marais (code), `vx_berger_echasses`, `vx_mouton`, `vx_pin` en rangées |
| « la route des vacances » | `vx_voiture_vacances` qui roule entre les `vx_pin` |
| « notre cerveau retient ce qui se dégrade » | `vx_cerveau`, `vx_balance` qui penche |
| « un incendie passe au journal de 20 heures » | `vx_tele` avec `vx_arbre_feu` dans l'écran, puis `vx_pousse` dans l'écran (barrée « JAMAIS ») |
| « une éponge à CO2… 63… 39 » | `vx_chene` → `vx_eponge` (transformation), `nuage` / `molecule`, barres (code) |
| « les arbres meurent… la sécheresse » | `vx_chene` → `vx_chene_mort`, `vx_soleil`, `vx_sol_sec`, compteur ×2 |
| « le scolyte, cinq millimètres… épicéas de trente mètres » | `vx_loupe`, `vx_scolyte`, `vx_epicea` → `vx_epicea_mort`, curseurs (code) |
| « elle grossit, mais elle respire de plus en plus mal » | jauge (code), `vx_poumons` |
| « il suffit de planter… cent ans en 2125… un climat qui n'existe pas encore » | `vx_main_pousse`, `vx_forestier`, frise (code) → `vx_chene_centenaire`, `fr_thermometre` |
