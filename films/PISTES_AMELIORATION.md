# Pistes d'amélioration — style oscilloscope

État au 6 octobre 2026. Ce qui est **en production** et ce qui est **en réserve** (testé, gardé pour plus tard).

## En production

- Personnages : bonshommes en traits d'origine (`bonhomme()` de l'épisode 21). Décision du 5 octobre : on garde cette
  version, les autres restent en réserve.
- Image 0 pleine et en mouvement ; la surprise écrite en grand dès l'image 0 (épisodes 22 et 23).
- Effets sonores synthétisés variés (`films/styles/oscillo_son.py`), sans musique de fond.
- Question finale à l'écran et dans la voix.

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
