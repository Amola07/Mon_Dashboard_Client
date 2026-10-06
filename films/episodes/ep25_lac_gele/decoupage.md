# Épisode 25 — découpage technique (24 images/s, aucun mouvement en boucle)

Règles de mise en scène :

- Chaque plan raconte une action complète (début → milieu → fin), calée sur la phrase qu'il illustre.
- On alterne les grosseurs de plan : plan large (la solitude sur le lac), plan moyen (l'action), gros plan / insert
  (les pieds, la main, la chaussure).
- On coupe dans le mouvement (raccord dans l'action), jamais sur un personnage immobile qui attend.
- La caméra est fixe dans les feuilles ; les mouvements (zoom, travelling, panoramique) sont faits au montage
  sur les traits : ils restent nets et le personnage ne se déforme pas.
- Animation à 24 images/s, un dessin par image : feuilles de 24 cases (1 seconde chacune), enchaînées sans boucle.
  Un personnage immobile est tenu sur une image (pose tenue), jamais remis en boucle.

Temps = début de la phrase dans la voix resserrée.

| Plan | Temps | Phrase | Cadre | Action | Montage |
|---|---|---|---|---|---|
| 1 | 0,0 | Si vous êtes coincé sur un lac gelé | plan d'ensemble | il est minuscule au centre, il tourne la tête une fois à gauche puis à droite | zoom avant lent ; titre déjà à l'écran |
| 2 | 2,1 | surtout… ne marchez pas | plan moyen | il lève le pied pour faire un pas | arrêt sur image au moment du pas, flash ambre sur « ne marchez pas » |
| 3 | 4,3 | parfaitement lisse… pour toujours | insert sur les pieds | les chaussures posées sur la glace, un reflet passe | dézoom jusqu'au plan d'ensemble : les bords sont très loin |
| 4 | 7,8 | Marcher ? Vos pieds glissent sur place | plan moyen, profil | il fait un pas, le pied part en arrière, les bras moulinent, il se rattrape au même endroit | coupe franche sur « Ramper » |
| 5 | 10,3 | Ramper ? Pareil | plan large bas | il se met à quatre pattes, avance une main, la main glisse, il s'écrase sur le ventre | — |
| 6 | 11,8 | Sauter ? … au même endroit | plan moyen | il plie les genoux, saute, retombe exactement sur la marque | marque ambre au sol |
| 7 | 14,9 | Un seul geste peut vous sauver | plan rapproché | il se relève et se tourne vers la caméra | zoom avant rapide |
| 8 | 16,7 | Trouvez-le avant la fin… en commentaire | plan moyen | il s'assoit sur la glace, les bras autour des genoux | le chrono apparaît |
| 9 | 19,6 | Vous tortiller ? … pas d'un millimètre | plan moyen, face | il se tortille de plus en plus fort, puis s'arrête, épuisé | croix du centre de gravité fixe |
| 10 | 24,9 | Souffler très fort ? … des heures | profil | il inspire, souffle de toutes ses forces, se penche ; puis insert sur les pieds : ils ont avancé d'un rien | règle graduée sur l'insert |
| 11 | 29,7 | Attendre que la glace fonde ? Des mois | plan large | il est assis, il grelotte, la neige le recouvre peu à peu | accéléré : compteur des jours, 3 coupes rapides |
| 12 | 32,2 | pour avancer, il faut pousser quelque chose | plan moyen, sol normal | il marche normalement, un vrai pas | sol tracé en traits pleins |
| 13 | 36,1 | vous poussez le sol… le sol vous pousse | gros plan sur le pied | le pied pousse le sol vers l'arrière | flèches action / réaction |
| 14 | 40,4 | Sans frottement, plus rien à pousser | même gros plan, sur la glace | le pied glisse dans le vide | flèche barrée |
| 15 | 42,9 | Rien… sauf ce que vous avez sur vous | plan fixe en pied | il est immobile | panoramique vertical lent du bonnet aux chaussures, arrêt sur les chaussures |
| 16 | 45,5 | Les astronautes connaissent ce cauchemar | plan d'ensemble de la station | — | travelling avant dans le module |
| 17 | 47,5 | Flotter… sans rien pour s'agripper | plan moyen | l'astronaute brasse le vide, tend la main vers une paroi trop loin, n'avance pas | flèches vers les parois |
| 18 | 52,2 | Ils ont tous la même solution… trouvée ? | plan rapproché | l'astronaute s'immobilise et tourne la tête vers la caméra | coupe au noir sur « trouvée ? », dernier tic du chrono |
| 19 | 55,1 | Enlevez votre chaussure | plan moyen | il enlève sa chaussure en équilibre sur un pied | — |
| 20 | 56,6 | Et lancez-la… à l'opposé du bord | plan moyen | élan, lancer, la chaussure sort du cadre | élan au ralenti, lancer à vitesse réelle |
| 21 | 59,9 | Vous partez dans l'autre sens | plan large | le recul le fait glisser sur le dos, bras écartés | la caméra le suit (travelling latéral) |
| 22 | 61,8 | Action, réaction… Newton | écran partagé | chaussure à gauche, lui à droite | flèches opposées |
| 23 | 64,9 | Lentement… jusqu'au bord | plan large | il glisse lentement et touche la rive | travelling latéral, arrivée au bord |
| 24 | 68,8 | c'est comme ça qu'avance une fusée | raccord de mouvement | la glissade devient le décollage d'une fusée | raccord sur la même direction |
| 25 | 71,4 | Vous aviez trouvé ? | plan moyen, sur la rive | il se relève et lève les bras | — |
| 26 | 73,6 | abonnez-vous… | plan large | il s'éloigne et sort du cadre | fin sur le lac vide |

Plans animés (feuilles) : 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 23, 25, 26.
Plans faits au montage (image fixe + mouvement de caméra, ou schéma) : 3, 15, 16, 22, 24.

## Feuilles d'animation à générer (24 cases = 1 seconde à 24 images/s, aucune boucle)

Une feuille = 6 colonnes × 4 rangées, lue de gauche à droite puis de haut en bas. Quand un plan a plusieurs
feuilles, joindre l'image de la feuille précédente à la génération : la case 1 reprend exactement la dernière.
Total : 38 feuilles.

### Plan 1 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, stands still on a frozen lake, then slowly turns his head to look over his left shoulder, then back to the right, and stops, worried. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 2 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, standing on ice, slowly lifts his right foot and moves it forward to take a careful first step, the foot ends in the air just before touching the ice. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 4 — feuille 1/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, takes a step on perfectly slippery ice, his front foot starts to slide backward and his arms begin to wheel. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 4 — feuille 2/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, his arms wheel wildly, his body tilts, he nearly falls, then he catches his balance and ends standing at the exact same spot. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 5 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, gets down on all fours on slippery ice, reaches one hand forward, the hand slides away and he flops onto his belly. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 6 — feuille 1/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, bends his knees deeply, swings his arms and jumps straight up, rising to the highest point. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 6 — feuille 2/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, falls straight down, lands at exactly the same spot, knees bending to absorb the landing, then stands up still. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 7 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, medium shot from the waist up, straightens up and turns from a side view to face the camera. Same character, same size, same view and same camera in every frame, the subject at the same place and size in each cell, no ground, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 8 — feuille 1/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, bends his knees and starts to sit down carefully on the ice, hands reaching to the ground. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 8 — feuille 2/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, finishes sitting on the ice and wraps his arms around his knees, then stays still. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 9 — feuille 1/4

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, front view, standing on ice, starts to wriggle his hips and shoulders gently, feet never moving. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 9 — feuille 2/4

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, front view, wriggles harder, swinging his arms and hips from side to side, feet never moving. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 9 — feuille 3/4

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, front view, wriggles as violently as he can, whole body twisting, feet never moving. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 9 — feuille 4/4

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, front view, slows down, stops, and bends forward exhausted, hands on his knees. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 10 — feuille 1/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, standing, takes a huge breath, chest swelling, shoulders rising. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 10 — feuille 2/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, blows as hard as he can toward the right, cheeks puffed, leaning forward, a few breath lines in front of his mouth. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 10 — feuille 3/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, runs out of air, his shoulders drop and he slumps, then stands still. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 11 — feuille 1/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, sits on the ice hugging his knees and starts to shiver, a few snowflakes falling. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 11 — feuille 2/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, shivers more and more while snowflakes slowly pile up on his beanie and shoulders. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 12 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, takes two normal walking steps forward to the right on solid ground and stops. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 13 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, close-up side view of one sneaker on solid ground, the foot pushes firmly backward against the ground, the toes bend, the heel lifts. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 14 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, close-up side view of one sneaker on ice, the foot tries to push backward and simply slides away backward without any grip. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 17 — feuille 1/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: an astronaut in a white spacesuit with a helmet and a life-support backpack, full body, floats weightless and starts to swim with his arms and legs, without moving from the center. Same character, same size, same view and same camera in every frame, the subject at the same place and size in each cell, no ground, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 17 — feuille 2/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: an astronaut in a white spacesuit with a helmet and a life-support backpack, full body, swims harder, reaching out toward something far to the right that he cannot touch. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, the subject at the same place and size in each cell, no ground, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 17 — feuille 3/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: an astronaut in a white spacesuit with a helmet and a life-support backpack, full body, gives up, arms slowly drifting, slowly rotating on himself, still at the center. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, the subject at the same place and size in each cell, no ground, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 18 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: an astronaut in a white spacesuit with a helmet and a life-support backpack, medium shot, floating weightless, stops moving and slowly turns his helmet toward the camera. Same character, same size, same view and same camera in every frame, the subject at the same place and size in each cell, no ground, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 19 — feuille 1/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, standing on ice, lifts his right knee, reaches down and grabs the heel of his sneaker. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 19 — feuille 2/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, full body, side view, pulls the sneaker off while wobbling on one leg, puts his sock foot down and stands holding the shoe. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 20 — feuille 1/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, holding a sneaker in his right hand, slowly winds up his arm far back, body twisting. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 20 — feuille 2/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, throws the sneaker as hard as he can toward the left, the shoe flies out of frame on the left, his body recoils backward to the right. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 21 — feuille 1/1

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, loses his balance backward after the throw, falls softly onto his back and starts to slide toward the right, arms spread. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 23 — feuille 1/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, half sitting on the ice, slides slowly toward the right, arms spread, gently balancing. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 23 — feuille 2/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, keeps sliding toward the right, arms slowly moving for balance, a snowy shore appears on the right. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 23 — feuille 3/3

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, gently bumps into the snowy shore and stops. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 25 — feuille 1/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, sitting on a snowy shore, gets up onto his feet. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 25 — feuille 2/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, raises both fists in the air in victory and holds the pose. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 26 — feuille 1/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, walks away to the right with a slight limp, one foot in a sock. Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.

### Plan 26 — feuille 2/2

Animation sprite sheet, 24 frames in a 6 columns × 4 rows grid, read left to right then top to bottom, one second of motion at 24 frames per second, each frame only very slightly different from the previous one so the motion is perfectly smooth, no loop: a young man in a knitted beanie, a puffer jacket over a hoodie, jeans, one sneaker and one sock, with a blank face, full body, side view, keeps walking with a slight limp and leaves the frame on the right. Frame 1 continues exactly from the last frame of the previous sheet (attached image). Same character, same size, same view and same camera in every frame, feet on the same horizontal ground line in each cell, generous empty space between cells, no frame borders, no numbers. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.
