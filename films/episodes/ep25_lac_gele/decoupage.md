# Épisode 25 — découpage technique (24 images/s, aucun mouvement en boucle)

Règles de mise en scène :

- Chaque plan raconte une action complète (début → milieu → fin), calée sur la phrase qu'il illustre.
- On alterne les grosseurs de plan : plan large (la solitude sur le lac), plan moyen (l'action), gros plan / insert
  (les pieds, la main, la chaussure).
- On coupe dans le mouvement (raccord dans l'action), jamais sur un personnage immobile qui attend.
- La caméra est fixe dans les clips générés ; les mouvements (zoom, travelling, panoramique) sont faits au montage
  sur les traits : ils restent nets et le personnage ne se déforme pas.
- Les clips sont générés à 24 images/s puis convertis en traits image par image.

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

Plans à générer en vidéo : 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 23, 25, 26.
Plans faits au montage (image fixe + mouvement de caméra, ou schéma) : 3, 15, 16, 22, 24.

## Prompts vidéo (image de départ : une case des feuilles déjà générées)

### Plan 1
Image-to-video, 5 seconds, 24 fps, static locked-off camera, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, stands alone on a frozen lake, slowly turns his head to look left, then right, then freezes, worried. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 2
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, standing on ice, lifts his right foot to take a careful first step forward. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 4
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, tries to walk on perfectly slippery ice: his front foot slips backward, his arms wheel wildly, he nearly falls, then catches his balance and ends standing at the exact same spot. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 5
Image-to-video, 2 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, gets down on all fours on slippery ice, reaches one hand forward, the hand slides away and he flops onto his belly. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 6
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, bends his knees, jumps straight up as high as he can, and lands at exactly the same spot, knees bending on landing, then stands still. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 7
Image-to-video, 2 seconds, 24 fps, static locked-off camera, medium shot from the waist up, a young man in a knitted beanie, a puffer jacket over a hoodie, with a blank face, straightens up and turns from a side view to face the camera. One single action with a clear start and end, no loop. Plain white background. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 8
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, sits down carefully on the ice and wraps his arms around his knees. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 9
Image-to-video, 5 seconds, 24 fps, static locked-off camera, front view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, stands on ice and starts wriggling his hips and arms, more and more violently, his feet never moving, then stops, exhausted, hands on his knees. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 10
Image-to-video, 4 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, takes a huge breath, chest swelling, then blows as hard as he can toward the right, cheeks puffed, leaning forward, until he runs out of air and slumps. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 11
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, sits on the ice hugging his knees and shivers more and more while snowflakes fall and slowly pile up on his beanie and shoulders. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 12
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, takes two normal walking steps forward on solid ground, the camera does not follow him. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 13
Image-to-video, 3 seconds, 24 fps, static locked-off camera, close-up side view of one sneaker on solid ground, the foot pushes firmly backward against the ground, the toes bend, the heel lifts. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 14
Image-to-video, 2 seconds, 24 fps, static locked-off camera, close-up side view of one sneaker on ice, the foot tries to push backward and simply slides away backward without any grip. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 17
Image-to-video, 5 seconds, 24 fps, static locked-off camera, full body, an astronaut in a white spacesuit with a helmet and a life-support backpack floats weightless, swims with his arms and legs, reaches out toward something far to the right that he cannot touch, and stays at the same place, slowly rotating. One single action with a clear start and end, no loop. Plain white background, no ground. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 18
Image-to-video, 3 seconds, 24 fps, static locked-off camera, medium shot, an astronaut in a white spacesuit with a helmet floats weightless, stops moving and slowly turns his helmet toward the camera. One single action with a clear start and end, no loop. Plain white background, no ground. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 19
Image-to-video, 2 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and sneakers, with a blank face, standing on ice, lifts his right knee, grabs the heel of his sneaker, pulls it off while wobbling on one leg, and stands holding the shoe. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 20
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and one sneaker, with a blank face, holding his other sneaker, winds up his arm far back and throws the shoe as hard as he can toward the left, the shoe flies out of frame on the left, his body recoils backward to the right. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 21
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and one sneaker, with a blank face, loses his balance backward after a throw, falls softly onto his back and starts sliding toward the right, arms spread for balance. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 23
Image-to-video, 4 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and one sneaker, with a blank face, half sitting on the ice, slides slowly toward the right, arms spread, and gently bumps into a snowy shore on the right, where he stops. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 25
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and one sneaker, with a blank face, sitting on a snowy shore, gets up and raises both fists in the air in victory. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.

### Plan 26
Image-to-video, 3 seconds, 24 fps, static locked-off camera, side view, full body, a young man in a knitted beanie, a puffer jacket over a hoodie, jeans and one sneaker, with a blank face, walks away to the right with a slight limp, one foot in a sock, and leaves the frame. One single action with a clear start and end, no loop. Plain white background, a single thin horizontal ground line. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness, the drawing style stays identical in every frame.
