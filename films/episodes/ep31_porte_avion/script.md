# Épisode 31 — La porte d'avion ouverte en plein vol

Même recette que l'ép. 21 (ascenseur, > 5 000 vues) : question que tout le monde s'est posée → « Non » en 4 s →
physique en chiffres → retournement → deux histoires vraies → geste concret. Format jeu vidéo (jeu_ep30.py / son_jeu).
Durée visée ≈ 85 s (≈ 260 mots).

## Texte à lire

Si un passager ouvre la porte de l'avion en plein vol, est-ce que tout le monde est aspiré dehors ?
La réponse est non. Il ne pourrait même pas l'ouvrir. Et la raison va vous surprendre.

À 11 000 mètres, l'air de la cabine pousse sur la porte. Environ 5 tonnes par mètre carré.
Sur toute la porte, à peu près 10 tonnes. Le poids de deux éléphants.
Et cette porte est un bouchon. Elle est plus grande que son trou.
Pour l'ouvrir, il faut d'abord la tirer vers l'intérieur. Contre 10 tonnes.

Mais attention. Plus l'avion descend, plus cette force diminue. Au sol, elle tombe à zéro.
Corée du Sud, 2023. À 200 mètres du sol, deux minutes avant l'atterrissage, un passager ouvre la porte de secours.
Le vent s'engouffre dans la cabine. Personne n'est aspiré. L'avion se pose.

Alors, et si la porte s'arrache toute seule, en altitude ?
C'est arrivé. Janvier 2024, à 5 000 mètres. Un panneau de porte s'arrache d'un Boeing.
Le souffle arrache le t-shirt d'un adolescent. Des téléphones s'envolent. L'un d'eux est retrouvé par terre… intact.
Et les deux sièges juste à côté du trou ? Vides. Ce jour-là, personne n'y était assis.

Et l'homme le plus célèbre à avoir sauté d'un avion de ligne en vol ? D. B. Cooper, 1971, par l'escalier arrière.
On ne l'a jamais retrouvé. Depuis, une petite palette bloque cet escalier en vol.

Alors la prochaine fois qu'un passager regarde la porte d'un peu trop près, restez calme.
Et gardez votre ceinture attachée. C'est elle qui vous protège, pas la porte.

## Découpage (format jeu vidéo)

| Passage | Écran | Jeu (HUD, bandeaux, sons) |
|---|---|---|
| Question | avion en coupe qui vole (déjà en mouvement), altimètre « ALT 11 000 m » qui défile, un passager-sprite tend la main vers la poignée | alarme 1 coup, bips de tracé |
| « La réponse est non » | **NON** géant qui clignote sur l'image figée | ⏸ ARRÊT SUR IMAGE, buzzer |
| 5 t/m², 10 tonnes | la porte en gros plan, flèches de pression qui la poussent ; compteur 0 → 10 T ; deux éléphants tombent sur une balance | tics de pièce, explosion légère sur « 10 tonnes » |
| Le bouchon | coupe de la porte : plus large que le cadre ; la main tire → la porte ne bouge pas | « FORCE DU PASSAGER : 50 KG » vs « 10 000 KG », buzzer |
| La force diminue | altimètre qui descend, la jauge « PRESSION » se vide jusqu'à 0 | glissando descendant |
| Corée 2023 | avion à 200 m au-dessus de la piste, porte ouverte, lignes de vent dans la cabine, passagers qui restent assis | bandeau « ! PORTE OUVERTE », vent |
| Alaska 2024 | Boeing à 5 000 m, panneau qui s'envole, t-shirt qui part, téléphone qui tombe → atterrit intact | explosion, bandeau « ! PANNEAU ARRACHÉ », sons de chute |
| Sièges vides | zoom sur la rangée 26 : deux sièges vides, curseurs de mesure | « 2 SIÈGES VIDES SUR 7 » , power-up |
| D. B. Cooper | Boeing 727 vu de dessous, escalier arrière, parachutiste ; « ? » ; puis la palette qui bloque l'escalier | jingle mystère, puis « niveau » |
| Ceinture | la ceinture qui se boucle, bandeau « CEINTURE : OBJET LE PLUS SÛR » | clic de boucle, fanfare |

## Faits et sources (vérifiés le 9 octobre 2026)

| Phrase | Fait | Source |
|---|---|---|
| ≈ 5 t/m², ≈ 10 t sur la porte | écart de pression en croisière ≈ 8 psi (≈ 0,55 bar ≈ 5,6 t/m²) ; porte ≈ 1,5-1,9 m² → ≈ 9-11 t (notre calcul) | Flying with Fish ; Ask Captain Lim |
| porte-bouchon, tirée vers l'intérieur | portes « plug » plus grandes que l'ouverture, s'ouvrent d'abord vers l'intérieur | Travelpulse ; Afar |
| la force diminue, zéro au sol | l'écart de pression baisse en descente, nul à l'atterrissage | Afar |
| Corée du Sud 2023 | Asiana, 26 mai 2023, A321 Jeju → Daegu, porte ouverte à ≈ 213 m, 2-3 min avant l'atterrissage ; avion posé ; 12 personnes soignées (hyperventilation) | AP / PBS, Korea Times |
| Alaska 2024 | vol 1282, 5 janvier 2024, 737 MAX 9, panneau (« door plug ») arraché à ≈ 16 000 ft (≈ 4 900 m) ; t-shirt d'un adolescent arraché ; téléphones aspirés, un iPhone retrouvé intact ; sièges 26A et 26B non attribués | NTSB via Fox/KTVU ; CBS ; Fox32 |
| D. B. Cooper | 24 novembre 1971, Boeing 727, saut par l'escalier ventral arrière ; jamais identifié (FBI clôt l'enquête active en 2016) ; « Cooper vane » | Aerocorner ; Migflug |
| « le poids de deux éléphants » | éléphant d'Afrique adulte ≈ 4-6 t | ordre de grandeur |

## Dessins à générer — feuilles de sprites (voir films/REGLES_PLANCHES_JEU.md)

### Planche 24 — le passager (4 × 3)
```
Video game sprite sheet, 4 columns × 3 rows grid of 12 cells, each row is one animation of 4 frames read from left to right. In every row the subject keeps exactly the same design, the same size, the same proportions and the same camera angle; it stands on the same invisible baseline at the same height in each cell and stays centered, only the pose changes from frame to frame. No motion blur, no speed lines, no effects, nothing else in the cells. The character: an adult airplane passenger with short hair, a teal sweater and grey trousers, blank face (a plain oval, no eyes, no nose, no mouth), side view facing right. Row 1, walk cycle: four frames of a normal walk. Row 2, opening a door: (1) standing, reaching his hand forward at chest height, (2) both hands gripping an invisible handle in front of him, (3) leaning back and pulling hard, (4) leaning back even more, straining, knees bent. Row 3, seated (draw the airplane seat too, the same seat in every frame): (1) seated calmly, (2) seated and turning his head to look sideways, (3) seated, surprised, both arms raised, (4) seated, both hands buckling his seatbelt. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```
Noms : `sp_passager_marche_1..4`, `sp_passager_tire_1..4`, `sp_passager_assis_1..4`.

### Planche 25 — la porte, l'avion, le téléphone (4 × 3)
```
Video game sprite sheet, 4 columns × 3 rows grid of 12 cells, each row is one animation of 4 frames read from left to right. In every row the subject keeps exactly the same design, the same size, the same proportions and the same camera angle; it stands on the same invisible baseline at the same height in each cell and stays centered, only the pose changes from frame to frame. No motion blur, no speed lines, no effects, nothing else in the cells. Row 1, an airplane passenger door seen from the front with its handle and a small round window, no frame, no wall: (1) flat and closed, (2) the same door slightly tilted as if pulled inward, (3) the same door rotated 45 degrees, flying, (4) the same door rotated 90 degrees, flying. Row 2, a modern twin-engine passenger jet seen from the side facing right: (1) flying level, (2) the same jet with a rectangular hole torn in the fuselage behind the wing, (3) the same jet nose slightly down, descending, (4) the same jet nose slightly up, landing gear down, landing. Row 3, a smartphone tumbling: the same phone rotated 0, 45, 90 and 135 degrees. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```
Noms : `sp_porte_1..4`, `sp_avion_1..4`, `sp_telephone_1..4`.

### Planche 26 — le passager dans le souffle, D. B. Cooper, l'éléphant (4 × 3)
```
Video game sprite sheet, 4 columns × 3 rows grid of 12 cells, each row is one animation of 4 frames read from left to right. In every row the subject keeps exactly the same design, the same size, the same proportions and the same camera angle; it stands on the same invisible baseline at the same height in each cell and stays centered, only the pose changes from frame to frame. No motion blur, no speed lines, no effects, nothing else in the cells. Row 1, a young passenger fully dressed in a teal hooded jacket and grey trousers, seated in an airplane seat, side view facing right, blank face (draw the seat too, the same seat in every frame): (1) seated calmly, (2) leaning back, his hair blown backwards by a strong wind, (3) shielding his face with both forearms, (4) gripping both armrests tightly. Row 2, a man in a dark suit and tie with a parachute pack, side view facing right, blank face: (1) standing, (2) jumping forward, (3) falling head first, arms spread, (4) hanging under an open round parachute. Row 3: (1) an orange t-shirt alone, crumpled, flying through the air, (2) a walking African elephant, side view facing right, left legs forward, (3) the same elephant, right legs forward, (4) an old three-engine airliner (Boeing 727 style) seen from the side, its rear stairs lowered under the tail. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```
Noms : `sp_souffle_1..4`, `sp_cooper_1..4`, `sp_tshirt`, `sp_elephant_1..2`, `sp_727`.

Réutilisés : `vx_cabine`, `vx_balance`, `vx_cerveau`. Code : altimètre, jauge de pression, flèches de pression,
lignes de vent, coupe de la porte (bouchon plus large que le trou), sièges vides (deux rectangles), palette « Cooper
vane », ceinture (deux sangles + boucle), compteurs, bandeaux.

### Planche 27 — le passager tire la porte, 8 images (+ 8 images d'approche), grille 4 × 4

Le passager et la porte sont dessinés ENSEMBLE dans chaque case : ses mains tiennent vraiment la poignée (la porte
ne bouge pas d'une case à l'autre, elle sert de repère fixe).

```
Video game sprite sheet, 4 columns × 4 rows grid of 16 cells, read row by row from left to right. Rows 1 and 2 are ONE smooth animation of 8 frames, rows 3 and 4 are a second smooth animation of 8 frames. In every cell the scene is drawn with exactly the same size, the same camera angle and the same position: a closed airplane passenger door seen from the side on the right of the cell, standing on the same invisible floor line, with a lever handle at the chest height of the man; the door never moves, never changes size, and stays at exactly the same place in every cell. The character: an adult airplane passenger with short dark hair, a teal sweater and grey trousers, blank face (a plain oval, no eyes, no nose, no mouth), side view facing right, the same size in every cell, his feet always on the same floor line. Frames 1 to 8 (rows 1 and 2), pulling the door handle, very small changes between consecutive frames: (1) standing close to the door, both hands gripping the lever handle, (2) starting to lean back, (3) leaning back a little more, arms straight, (4) leaning back further, knees bending, (5) leaning back strongly, heels pushing on the floor, (6) maximum effort, body diagonal, (7) leaning back a little less, (8) almost back to frame 2, still gripping the handle. In all 8 frames both hands stay on the handle. Frames 9 to 16 (rows 3 and 4), walking to the door and grabbing it: (9) to (14) six frames of a walk cycle getting closer to the door, (15) raising both hands toward the handle, (16) both hands gripping the handle. No motion blur, no speed lines, no effects, nothing else in the cells. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```
Noms : `sp_effort_1..8` (lignes 1-2), `sp_approche_1..8` (lignes 3-4).
