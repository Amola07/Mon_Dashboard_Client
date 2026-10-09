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

## Dessins à générer — planche 24 (aplats, même style que la planche 18)

```
Flat vector icon sheet, 9 separate drawings in a 3 columns × 3 rows grid, each isolated and centered in its cell, drawn at a similar size, with NOTHING around it: no ground, no sky, no background scenery. All people have a blank face (a plain oval, no eyes, no nose, no mouth). 1. an airplane passenger seen from the side, standing and pulling the handle of an emergency exit door with both hands. 2. a closed airplane passenger door seen from the front, with its handle and a small round window. 3. an airplane emergency exit door flying away through the air, tilted. 4. a teenager sitting in an airplane seat seen from the side, his t-shirt flying off above his head. 5. a smartphone tumbling in the air. 6. two adjacent empty airplane seats seen from the front. 7. an old three-engine airliner (Boeing 727 style) seen from below and behind, with its rear stairs lowered under the tail. 8. a man in a suit and tie falling with a parachute opening above him. 9. an African elephant, side view. Flat vector style, simple bold shapes, large flat color areas, no outlines, no gradients, no texture, no small details, each color used in at most two tones (base and one darker tone for shadows), strictly limited palette: teal #28AFAF, dark teal #1A6E70, orange #FF8A3D, dark orange #A8481A, off-white #ECF2F0, grey #788284, on a pure solid black background #000000, no text, no numbers, no frame borders, generous empty black space between cells.
```

Noms : `vx_passager_porte`, `vx_porte_avion`, `vx_porte_volante`, `vx_ado_tshirt`, `vx_telephone`, `vx_sieges_vides`,
`vx_727_escalier`, `vx_cooper`, `vx_elephant`. Réutilisés : `vx_avion`, `vx_cabine`, `vx_porte`, `vx_avion_pique`.
Code : altimètre, jauge de pression, balance, flèches de pression, coupe de la porte et du cadre, lignes de vent.
