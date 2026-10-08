# Épisode 29 — « Le gilet de sauvetage : le geste qui peut vous noyer » (suite de l'épisode 28)

Moteur oscilloscope animé (`oscillo_ep28_pro.py` comme modèle) + dessins IA convertis en traits. Une seule voix.
Durée visée ≈ 1 min 35 (même débit que l'épisode 28 : 290 mots → 1 min 41). Suite directe de l'épisode 28, qui finit sur « Le gilet de sauvetage : le geste à ne pas faire
trop tôt — LA SUITE DEMAIN ▶ ». Même fil : **chaque geste a sa loi de physique** (ici : poussée d'Archimède,
conduction de la chaleur, surface d'échange ; en teaser : pression = force ÷ surface).

## Ce qu'on garde de l'épisode 28 et ce qu'on teste

- **Promesse tenue dès la 1re phrase** : la vidéo répond à la question laissée en suspens hier (« le gilet ») et le dit
  tout de suite. Ceux qui arrivent sans avoir vu l'épisode 28 ont quand même la scène et l'enjeu dans la 1re phrase.
- **Personnage et action dès l'image 0** : l'avion est déjà sur l'eau, le passager a son gilet autour du cou.
- **Chaîne de révélations** : Archimède → le piège dans la cabine → le cas réel → le bon geste → le froid → la posture
  → teaser. Pas de révélation finale unique.
- **Fin en série** : phrase coupée sur la suite (le toboggan), carton « LA SUITE DEMAIN ▶ ».
- À mesurer (comparé à l'épisode 28) : part des spectateurs venus du profil ou de l'épisode 28 (sources de trafic),
  visionnage moyen, nouveaux abonnés. C'est le premier vrai test de la série « la suite demain ».

Information générale : en vol, on suit toujours les consignes de l'équipage et la carte de sécurité de la compagnie.

## Texte avec balises (ElevenLabs v3 — sans [short pause], sans [whispers]) — ≈ 270 mots

[tense] Votre avion vient de se poser sur l'eau. Vous avez votre gilet. Et le geste qui paraît le plus logique peut vous noyer : le gonfler tout de suite.

[curious] La raison, c'est Archimède. Dans l'eau, tout est poussé vers le haut par le poids de l'eau qu'il déplace. Un gilet gonflé, c'est environ seize litres d'air. Donc environ seize kilos qui vous tirent vers le haut. [matter-of-fact] Dehors, c'est parfait : votre tête reste hors de l'eau, sans effort.

[serious] Mais dans la cabine, l'eau monte. Et les sorties, elles, sont sous l'eau. Pour les atteindre, il faut plonger. Avec seize kilos qui vous tirent vers le plafond, vous n'y arrivez pas.

[matter-of-fact] En mille neuf cent quatre-vingt-seize, un avion détourné finit dans l'océan, près des Comores. Beaucoup de passagers ont survécu au choc. Et beaucoup avaient gonflé leur gilet dans la cabine.

[serious] Donc : gilet enfilé, sangles serrées, mais pas gonflé. On tire la languette rouge à la porte, une fois dehors. Une cartouche de gaz le remplit en quelques secondes.

[tense] Deuxième ennemi : le froid. L'eau vous vole votre chaleur environ vingt-cinq fois plus vite que l'air. [matter-of-fact] Sur l'Hudson, en deux mille neuf, l'eau était à deux degrés. Les secours sont arrivés en quelques minutes : les cent cinquante-cinq personnes ont survécu.

[curious] En attendant les secours, on ne nage pas : bouger fait fuir la chaleur encore plus vite. On remonte les genoux, on serre les bras, on se colle aux autres. Moins de surface, moins de chaleur perdue.

[mischievously] Et avant le toboggan, il y a une chose à enlever, que presque personne n'enlève. La physique, encore. C'est dans la prochaine vidéo… et vous allez voir que…

## Faits et sources (à relire avant publication)

| Affirmation | Statut | Source / nuance |
|---|---|---|
| Ne pas gonfler le gilet dans la cabine : on ne peut plus plonger pour atteindre les sorties, on reste coincé ; on gonfle en sortant | vérifié | [Autorité de l'aviation civile de Singapour (CAAS)](https://ask.gov.sg/caas/questions/clq3e4u6f004y10ye1tov2juh) : « an inflated lifevest will prevent a passenger from being able to dive underwater to reach exits ». Autres raisons données : gilet abîmé, passage des petites sorties d'aile, position de sécurité impossible. Déjà cité dans l'épisode 28 avec [SKYbrary](https://skybrary.aero/index.php/Emergency_Evacuation_on_Water) |
| Poussée d'Archimède : un corps immergé est poussé vers le haut par le poids du fluide déplacé | principe de physique | — |
| Gilet d'avion adulte : environ 16 litres, environ 16 kg (≈ 150 N) de flottabilité | vérifié, ordre de grandeur | fiches fabricants des gilets approuvés FAA TSO-C13f : volume minimal 970 pouces cubes (16 L), flottabilité 35 lb (≈ 15,9 kg, 150 N) ([Aircraft Spruce](https://aircraftspruce.com/catalog/pnpages/13-13066.php), [Life Support International](https://lifesupportintl.com/products/p01202-xxx)). Le texte de la norme n'a pas été lu : dire « environ » |
| 16 L d'air → environ 16 kg vers le haut | calcul | 1 L d'eau ≈ 1 kg ; cohérent avec les 150 N des fabricants |
| Éthiopien 961, 23 novembre 1996 : avion détourné, panne de carburant, amerrissage près de la Grande Comore ; 125 morts sur 175 ; beaucoup avaient survécu au choc et beaucoup avaient gonflé leur gilet dans la cabine | **rapporté, à relire** | [Wikipédia (miroir)](https://en.wikipedia.com/wiki/Leul_Abate), [BAAA](https://www.baaa-acro.com/node/473964), [Migflug](https://migflug.com/jetflights/flight-961-the-hijacking-that-ended-in-the-ocean/). Le rapport officiel n'a pas été lu. Le résumé du BAAA indique que l'équipage avait aidé des passagers à dégonfler leur gilet avant l'impact. **On ne dit pas** que tous les morts sont dus aux gilets, ni « plaqués au plafond » (c'est une déduction) |
| La languette rouge déclenche une cartouche de gaz (CO₂) qui gonfle le gilet en quelques secondes ; tubes pour souffler en secours | vérifié, général | consignes de sécurité standard des compagnies ; certains gilets ont deux chambres et deux languettes : on dit « la languette rouge » |
| L'eau prend la chaleur du corps environ 25 fois plus vite que l'air à la même température | vérifié, ordre de grandeur | garde-côtes américains et armée américaine ([army.mil, USACE et USCG](https://www.army.mil/article/51309/cold_water_survival_tips_from_usace_and_uscg)) ; les sources vont de 25 à 30 fois : dire « environ vingt-cinq » |
| Hudson, 15 janvier 2009 (US Airways 1549) : eau à environ 2 °C (36 °F), secours en quelques minutes, 155 survivants sur 155 | vérifié | [NBC](https://www.nbcnews.com/id/wbna28678669), [Scientific American](https://www.scientificamerican.com/article/airplane-1549-hudson-hypothermia), [ABC7](https://abc7news.com/archive/6606452) ; un ferry est arrivé en quelques minutes. Beaucoup ont eu une hypothermie : on ne dit pas « sans dommage » |
| Ne pas nager pour se réchauffer ; position HELP (genoux remontés, bras serrés) ; se serrer à plusieurs | vérifié | garde-côtes (USCG, garde-côtes canadiens) : [army.mil](https://www.army.mil/article/212474/tips_to_survive_a_fall_into_cold_water), [Hard Hat Training](https://hardhattraining.com/the-dangers-of-cold-water-and-how-to-help-yourself) ; le mouvement augmente les pertes de chaleur |
| **Teaser** : enlever ses chaussures à talons avant le toboggan (pression = force ÷ surface, risque de percer le toboggan) | **rapporté, à vérifier avant l'épisode 30** | consigne citée par la FAA selon [AZFamily](https://www.azfamily.com/2025/07/29/american-airlines-flight-evacuation-raises-safety-questions) ; raison (perforation) donnée par une hôtesse ([BHG](https://www.bhg.com.au/lifestyle/what-shoes-to-wear-to-airport/)). Le texte de la FAA n'a pas été lu |

Retiré volontairement : la règle « 1-10-1 » (1 min de choc, 10 min de mouvements utiles, 1 h avant l'inconscience),
juste mais un chiffre de trop pour cette durée. Peut servir dans un épisode sur l'eau froide.

## Chaîne de l'épisode : chaque écran naît du précédent

Motifs qui reviennent : **le passager** (notre bonhomme, bonnet, doudoune, gilet autour du cou), **la flèche ambre**
(la poussée d'Archimède, toujours vers le haut), **la ligne d'eau**, **la porte**.

| # | Phrase | Écran | Enchaînement vers le suivant |
|---|---|---|---|
| 1 | L'avion s'est posé sur l'eau… le gonfler tout de suite | image 0 : l'avion sur l'eau qui tangue (`av_eau`) ; le passager debout, gilet dégonflé (`pe_gilet`) ; sa main va vers la languette ; un tampon ambre « PAS MAINTENANT » | transformation : le gilet dégonflé devient le gilet gonflé |
| 2 | Archimède : 16 litres, 16 kilos | le gilet gonflé seul (`eau_gilet_gonfle`) ; une bouteille de 16 L se remplit (compteur 0 → 16 L) ; la flèche ambre vers le haut grandit, « 16 KG » ; le passager flotte dehors, tête hors de l'eau (`pe_flotte`) | plongée dans la ligne d'eau |
| 3 | Dans la cabine, l'eau monte ; les sorties sont sous l'eau | coupe de la cabine (`eau_cabine_moitie` → `eau_cabine_pleine`) : la ligne d'eau monte ; la porte (`eau_porte`) passe sous l'eau ; le passager gonflé est plaqué au plafond (`pe_plafond`), la flèche ambre le retient ; flèche pointillée vers la porte, barrée | transformation : la coupe de la cabine devient l'avion de 1996 |
| 4 | Comores, 1996 | l'avion qui pique vers l'océan, une île à l'horizon ; « COMORES · 1996 » ; « 125 / 175 » en grille de passagers (comme l'écran des 95 % de l'épisode 28) | transformation : la grille devient le passager |
| 5 | Gilet enfilé, pas gonflé ; la languette à la porte | le passager à la porte (`ex_porte`), gilet plat ; coche « ENFILÉ », croix « GONFLÉ » ; il sort, tire la languette (`pe_tire_cordon`) : le gilet se gonfle d'un coup (cartouche, nuage de gaz) | transformation : le passager gonflé dehors → le passager dans l'eau froide |
| 6 | Le froid : 25 fois plus vite ; Hudson, 2 °C, 155 survivants | flèches de chaleur qui quittent le corps : petites dans l'air, 25 fois plus nombreuses dans l'eau ; thermomètre qui descend à « 2 °C » ; l'avion sur la rivière, des passagers sur les ailes, un bateau arrive ; compteur « 155 / 155 » | plongée dans le passager |
| 7 | On ne nage pas ; genoux remontés ; on se colle | le passager qui nage : les flèches de chaleur doublent (croix ambre) ; il se met en boule (position HELP) : les flèches diminuent ; trois passagers serrés en rond | transformation : le groupe devient le toboggan |
| 8 | Le toboggan… une chose à enlever | le toboggan gonflé à la porte (`av_toboggan`), une chaussure à talon entourée d'un « ? » ; phrase coupée ; carton « LA SUITE DEMAIN ▶ » | — |

Relances : écran 1 (« peut vous noyer »), 3 (« vous n'y arrivez pas »), 4 (cas réel), 6 (« deuxième ennemi »), 8 (suite).

## Dessins

### Déjà prêts (planches 3 et 11 de l'épisode 28, dans `films/illustrations/`)

`av_eau`, `av_toboggan`, `pe_gilet`, `pe_tire_cordon`, `pe_flotte`, `pe_plafond`, `pe_nage`, `pe_respire`, `pe_salue`,
`pe_monte_radeau`, `pe_radeau`, `eau_gilet_vide`, `eau_gilet_gonfle`, `eau_cabine_moitie`, `eau_cabine_pleine`,
`eau_porte`, `eau_radeau`, `ex_porte`, `ex_toboggan`, `gr_groupe`.

### À générer : 2 planches (12 dessins)

Même style que l'épisode 28 ; le passager est notre bonhomme habituel (bonnet, doudoune, sans visage).

#### Planche 13 — le passager dans l'eau froide (grille 3 × 2)

```
Character sheet, 6 poses of the same person in a 3 columns × 2 rows grid, generous empty space between cells, no frame borders, no numbers: a young man in a knitted beanie and a puffer jacket, with a blank face (no eyes, no nose, no mouth), wearing an inflated airplane life vest, floating in water with a few wave lines around him, side view facing right, same size and same proportions in every pose. Pose 1: floating upright, head above the water, arms relaxed. Pose 2: floating curled up, knees pulled up to the chest, arms crossed tightly over the life vest. Pose 3: swimming hard, arms stretched forward, splash lines. Pose 4: shivering, arms wrapped around himself, short zigzag lines around his body. Pose 5: standing at an open airplane door, pulling a small tab on the front of the deflated life vest with one hand. Pose 6: standing at an open airplane door with the life vest suddenly inflated, small puff lines around it. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.
```

#### Planche 14 — l'eau, le froid, la physique (grille 3 × 2)

```
Object sheet, 6 separate drawings in a 3 columns × 2 rows grid, generous empty space between cells, no frame borders, no numbers, each drawn at a similar size, all people with blank faces (no eyes, no nose, no mouth), no text: three people in inflated life vests floating close together in a tight circle, holding each other, seen from above, wave lines around them; a passenger airplane floating on a river with several passengers standing on its wings, a small ferry boat approaching, no logo; a clear plastic bottle being filled with air bubbles, with a few level lines on its side and no numbers; a glass thermometer with a plain scale and no numbers; a small gas cartridge with a pull tab attached by a short cord; a woman's high-heeled shoe seen from the side. Minimal single-weight black line drawing on pure white background, no shading, no fill, no gray, no text, clean continuous strokes, consistent line thickness.
```

Noms proposés après conversion (`python -m films.outils.planche_en_traits`) :
planche 13 → `fr_flotte`, `fr_boule`, `fr_nage`, `fr_grelotte`, `fr_tire`, `fr_gonfle` ;
planche 14 → `fr_groupe`, `fr_hudson`, `fr_bouteille`, `fr_thermometre`, `fr_cartouche`, `fr_talon`.

### Où chaque dessin sert

| Écran | Dessins |
|---|---|
| 1 Accroche | `av_eau`, `pe_gilet`, `eau_gilet_vide` |
| 2 Archimède | `eau_gilet_gonfle`, `fr_bouteille`, `pe_flotte` |
| 3 La cabine | `eau_cabine_moitie`, `eau_cabine_pleine`, `eau_porte`, `pe_plafond` |
| 4 Comores 1996 | `av_descente` (épisode 28), mini-passagers de la grille (dessinés par le code) |
| 5 Le bon geste | `ex_porte`, `fr_tire`, `fr_gonfle`, `fr_cartouche` |
| 6 Le froid, Hudson | `fr_flotte`, `fr_thermometre`, `fr_hudson` |
| 7 La posture | `fr_nage`, `fr_boule`, `fr_groupe` |
| 8 Teaser | `av_toboggan` ou `ex_toboggan`, `fr_talon` |

## Étapes de fabrication

1. Relire le tableau des faits (surtout la ligne Comores 1996), puis générer la voix ElevenLabs avec le texte balisé
   → `films/episodes/ep29_gilet/audio/voix.mp3`.
2. `python -m films.outils.minuter_voix films/episodes/ep29_gilet/audio/voix.mp3` puis recopier les phrases dans
   `voix.json`.
3. `python -m films.outils.mots_voix films/episodes/ep29_gilet/audio/voix.mp3` → instant de chaque mot (accents,
   recalages).
4. Générer et convertir les planches 13 et 14.
5. Écrire `oscillo_ep29.py` (écrans) et `oscillo_ep29_pro.py` (caméras, accents, enchaînements) sur le modèle de
   l'épisode 28.

## Description TikTok

Ton avion s'est posé sur l'eau. Le geste le plus logique peut te noyer. 🌊 Tu l'aurais gonflé tout de suite ? 👇
Information générale : suivez toujours les consignes de l'équipage.

#survie #science #physique #lesaviezvous #apprendresurtiktok

Commentaire à épingler : « Tu l'aurais gonflé tout de suite ? La suite demain : la chose à enlever avant le toboggan. »
