# Pistes d'amélioration — style oscilloscope

État au 6 octobre 2026. Ce qui est **en production** et ce qui est **en réserve** (testé, gardé pour plus tard).

## En production

- Personnages : dessins IA convertis en traits, animés par feuilles d'animation (voir plus bas). Les bonshommes en
  traits d'origine (`bonhomme()` de l'épisode 21) restent utilisables pour les schémas.
- Image 0 pleine et en mouvement ; la surprise écrite en grand dès l'image 0 (épisodes 22 et 23).
- Effets sonores synthétisés variés (`films/styles/oscillo_son.py`), sans musique de fond.
- Question finale à l'écran et dans la voix.

## En production — réalisation (décision du 6 octobre, après l'épisode 25)

- Animation à 24 images/s, une image différente à chaque image (« sur les uns »).
- Aucune action en boucle : chaque plan raconte une action complète (début → fin), calée sur sa phrase.
- Découpage technique écrit avant le montage (`decoupage.md` dans l'épisode) : grosseurs de plan variées (ensemble,
  moyen, insert), coupe dans le mouvement, raccords de mouvement, arrêts sur image, ralentis.
- Feuilles d'animation de 24 cases (6 × 4) = 1 seconde par feuille, enchaînées pour les plans plus longs
  (`plan()` dans `films/outils/feuille_animation.py`) ; caméra fixe dans les feuilles, mouvements de caméra au montage.
- Testé et écarté : interpolation automatique entre cases (flux optique) → contours dédoublés dès que le mouvement est
  grand ; générateur vidéo → refusé (on garde les images générées).

## Feuilles d'animation (avant le passage aux clips vidéo)

Décision du 6 octobre : chaque action du personnage, importante ou non, a sa feuille d'animation (8 à 12 cases).
Les poses fixes ne servent plus qu'en secours. Les actions qui durent (patiner, flotter, attendre) sont des boucles :
la dernière case ramène à la première.

### Détails de l'outil

Une image IA en grille montre la même action à 8 instants (ou plus). `films/outils/feuille_animation.py` découpe
les cases (chaque objet lancé rejoint le personnage le plus proche), recale chaque image sur sa ligne de sol, et
les joue image par image (`image_anim`, 12 i/s par défaut, durée réglable par image). Essai : `lancer` (épisode 25),
`films/outils/demo_feuille_animation.py`. Limite : les détails bougent un peu d'une image à l'autre (lignes qui
« vibrent ») ; 8 cases au minimum, 12 c'est mieux.

## En réserve — animation des personnages

| Piste | Où | État | Notes |
|---|---|---|---|
| Mouvements générés par une phrase (MoMask) | `films/outils/momask/`, `films/mouvements/` | fonctionne, 10 s pour 3 mouvements, sans carte graphique | appris sur des mouvements au sol : pas d'apesanteur |
| Pantin physique (chutes, chocs, apesanteur) | `films/styles/pantin_physique.py` | démo faite (ascenseur) | jambes un peu raides au choc : régler le tonus des genoux |
| Corps en volume (silhouette humaine) | `films/styles/mouvement.py` → `corps()`, `dessiner()` | testé sur l'épisode 23 | style « mannequin d'artiste » |
| Traits souples (courbes, extrémités en retard, fondus) | `films/styles/mouvement.py` → `figure()`, `traits()`, `melange()` | testé sur l'épisode 23 | garde le style en traits |
| Capture de mouvement par vidéo (se filmer) | — | non testé | MediaPipe ; il faut télécharger le modèle de pose |
| Base de mouvements réels de Carnegie Mellon (2 500 BVH, libres) | — | non testé | mocap.cs.cmu.edu (domaine à autoriser) |
| AnimatedDrawings (Meta) : animer un dessin de personnage | — | non testé | dépôt archivé mais utilisable |

## En réserve — dessins et sons

| Piste | État | Notes |
|---|---|---|
| Illustrations au trait générées par IA puis converties en traits | convertisseur `films/outils/image_en_traits.py` | voir ci-dessous |
| Bibliothèque d'illustrations vectorielles (Noun Project, Streamline, Flaticon) | non acheté | dessins fixes, pas « vivants » |
| Objets animés Lottie (LottieFiles) | non testé | skia-python n'a pas Skottie ; essayer `rlottie-python` |
| Effets sonores ElevenLabs (déjà dans l'abonnement ?) | non testé | sons réalistes sur description |

## En réserve — rétention et abonnés (d'après les statistiques)

- Vidéos de 62 à 68 s : accroche → explication → solution → récapitulatif + question. Pas de section qui revient en
  arrière après la solution (épisode 23 : 2,5 % de visionnage complet, la fin était trop loin).
- Le récapitulatif est le moment préféré (pic de J'aime à 1:11 sur l'épisode 23) : le rendre fort, rythmé.
- Une question courte juste après la solution, une autre à la fin ; épingler la question en commentaire.
- Série reconnaissable : bandeau « SURVIE · N°… » et phrase de fin « Abonne-toi pour le n°… ».
- Le contenu « utile » est enregistré et partagé (épisode 23 : 11 enregistrements, 5 partages en 5 h).

## Illustrations générées par IA → traits

1. Générer l'image avec une IA d'images, consigne type :
   « *minimal single-weight black line drawing on pure white background, side view of a sedan car, no shading,
   no fill, no text, clean continuous strokes, centered* ».
2. `python -m films.outils.image_en_traits image.png voiture` → `films/illustrations/voiture.json` + aperçu.
3. Dans un tableau : `trace(c, t, t0, d, dessin("voiture", x, y, largeur), VERT_PALE, 1.2)`.

Le convertisseur amincit les traits à 1 pixel (squelette), les suit en lignes continues, les simplifie, et les range
dans un ordre de tracé naturel (de proche en proche). Il marche le mieux sur des traits nets, d'épaisseur régulière,
sans aplats ni ombres.

## Piste — modèle d'intervalles (image de début + description ou image de fin → 24 images)

Idée du 6 octobre. Ne pas entraîner de zéro (il faudrait des millions de clips) : adapter un modèle existant
d'interpolation générative de dessin animé (ToonCrafter, libre : image de début + image de fin → images entre les deux)
ou un modèle vidéo libre (Wan, LTX-Video, CogVideoX) avec un LoRA dans notre style.

1. Test sans entraînement : ToonCrafter sur nos cases de début et de fin (il faut une carte graphique louée).
2. Constituer le jeu de données au fil des épisodes : chaque feuille de 24 cases réussie = une séquence (24 images +
   la description de chaque groupe de 3 cases + le nom de l'action). On garde les feuilles brutes hors du dépôt public.
3. Entraîner un LoRA quand on aura 150 à 300 séquences réussies (3 600 à 7 200 images), réparties sur 30 à 50
   actions différentes, avec 10 à 20 % gardés pour l'évaluation. Une carte de 24 à 48 Go, quelques heures.

## Analyse de 3 vidéos d'un autre créateur, qui marchent (6 octobre)

Leçons seulement (aucun contenu repris). Durée 1 min 50 à 2 min. Fond noir, une seule couleur d'accent (rouge),
dessins en pixels, une idée par écran (≈ toutes les 3-4 s), chiffres rendus visibles (grilles de carrés).

- **Accroche** : une scène concrète + un enjeu chiffré dès la 1re phrase (« Cet homme est en train de tomber de 45 m »,
  « Ce cube contient tous les déchets… », « Une énergie 800 fois plus meurtrière… et elle ne fait peur à personne »).
- **Image fausse puis vraie** : « Vous imaginiez plutôt ça ? » (cliché montré, tamponné FICTION), puis « Sauf qu'en vrai ».
- **Relances toutes les 15-20 s** : « Normal. Moi aussi. », « À votre avis ? », « Mais attendez », « Je vais vous
  retourner le cerveau », « je brise le suspense » ; une promesse lancée tôt et tenue plus tard.
- **Deuxième rebondissement plus fort** dans le dernier tiers (le réacteur naturel du Gabon, les morts de l'évacuation).
- **Fins** (le plus intéressant) :
  1. Coupé au milieu d'une phrase : « Mais je n'ai plus le temps, donc je vous poste la suite demain, et vous allez
     voir à quel point… » + carton « LA SUITE DEMAIN ▶ ». → on revoit, on s'abonne pour la suite.
  2. Il anticipe l'objection du spectateur : « Je sais ce que vous allez me dire : et les déchets, alors ?
     Justement, c'est le sujet de la prochaine vidéo. Et vous allez voir que… » + « PROCHAINE VIDÉO ▶ ».
     Les vidéos s'enchaînent en série (énergie → déchets → « encore un truc que personne ne sait »).
  3. Partage lié au sujet : « Si vous connaissez quelqu'un qui ne me connaît pas, envoyez-lui cette vidéo : ça lui fera
     toujours un souvenir de plus. » (la vidéo parlait des souvenirs).
  Pas de « abonnez-vous » ni de « dites-le en commentaire » plat : l'envie de la suite fait le travail.

### L'enchaînement logique des éléments (le point fort de ces vidéos)

Un nouvel élément toutes les 3-4 s (≈ 30 écrans en 2 min), et chacun **naît du précédent** :
- un même objet porte plusieurs phrases et se transforme : la grille de carrés du combustible devient « 95 % uranium »,
  puis « 4 % le vrai déchet », puis « 0,2 % des déchets / 95 % de la radioactivité » ; la courbe « éternité » devient
  « ÷ 1000 » ; la coupe du sol passe de 0 m à 500 m ;
- des motifs reviennent (le cerveau quand il « retourne le cerveau », l'usine à charbon, le cube) ;
- le chiffre se construit à l'écran (compteur, carrés qui s'allument, +36 %) au lieu d'être écrit d'un bloc ;
- presque pas de coupe franche : on zoome, on remplit, on barre, on tamponne FAUX / FICTION.

Chez nous : un tableau par idée, remplacé d'un coup (neige, glitch), et des textes posés à côté du dessin.
Règle pour la suite : écrire le découpage comme une chaîne « l'élément A devient B parce que… » ; garder au moins un
élément d'un tableau au suivant ; montrer chaque chiffre en grille ou en compteur ; transitions par transformation
(zoom, déplacement, remplissage) plutôt que par effet.

### Pas de révélation finale : une chaîne de révélations (7 octobre, constat de l'utilisateur)

Dans les vidéos de référence, toute la vidéo est une révélation : chaque segment de 15-20 s répond à une question et en
ouvre une autre (ex. temps : 22 s « personne ne lit les chiffres » → 38 s « le temps n'a pas ralenti » → 42 s « et c'est
pourquoi le temps passe plus vite quand on vieillit » → 83 s « le scroll » → 91 s conclusion pratique). Il n'y a aucun
moment où le spectateur a « tout compris » et peut partir.

Notre format énigme (épisode 25 v2) tient une seule question jusqu'à 59 s sur 107 : quand la solution tombe, la tension
s'effondre et le spectateur scrolle (même cause que les 2,5 % de visionnage complet de l'épisode 23).

Règle remplacée : « la solution n'est révélée qu'à la fin » → **la solution arrive tôt et ouvre les questions suivantes**
(comment ? à quelle vitesse ? et si on n'a rien ?). Plan type : hook (0-10 s) → solution annoncée (10-25 s) → première
question qui en découle (25-45 s) → généralisation / deuxième rebondissement (45-65 s) → objection du spectateur + fin
coupée (65-90 s).

## Statistiques au 7 octobre 2026 (4 vidéos publiées)

| Vidéo | Vues | Visionnage moyen | % moyen suivi | % qui vont au bout | Abonnés | J'aime | J'aime / vue | Abonnés / 1000 vues |
|---|---|---|---|---|---|---|---|---|
| Ép. 21 ascenseur | 4 800 | 30 s | 38 % | 7 % | 5 | 138 | 2,9 % | 1,0 |
| Ép. 23 voiture à l'eau | 3 000 | 28,6 s | 37 % | 3 % | 3 | 161 | 5,4 % | 1,0 |
| Ép. 22 sables mouvants | 353 | 26 s | 33 % | 4 % | 0 | 31 | 8,8 % | 0 |
| Ép. 24 Miller | 464 | 10 s | 12 % | 3 % | 1 | 18 | 3,9 % | 2,2 (bruit) |

Lecture : (1) les 3 premières ont le même visionnage moyen (26-30 s) : les gens partent vers 30 s, quel que soit le sujet ;
(2) l'ép. 24 s'effondre dès le début (10 s) : l'accroche n'a pas tenu ; (3) les j'aime par vue sont bons : ceux qui restent
aiment ; (4) ≈ 1 abonné pour 1000 vues : rien ne donne envie de suivre (les fins « la suite demain » ne sont pas encore
publiées) ; (5) les vues chutent d'un facteur 10 sur les 2 dernières : c'est de la distribution (test sur un petit groupe),
pas seulement de la qualité (l'ép. 22 a des chiffres proches de l'ép. 23). Les 2 meilleures : scénario de survie à la
2e personne (« tu es dans un ascenseur qui tombe », « ta voiture tombe à l'eau »). Rien dans ces chiffres ne dit que la
fluidité de l'animation est le problème. À demander : courbe de rétention de chaque vidéo, sources de trafic, heure de
publication, description et hashtags utilisés.
