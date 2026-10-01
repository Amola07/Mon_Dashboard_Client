# Rendre les plans cosmos sur le GPU gratuit de Kaggle

## Une seule fois
1. Crée un compte sur kaggle.com.
2. **Vérifie ton numéro de téléphone** (Settings → Phone verification) : sans ça, pas de GPU ni d'Internet.

## À chaque série de plans
1. kaggle.com → **Create** → **New Notebook**.
2. Menu **File** → **Import Notebook** → choisis `rendu_cosmos.ipynb`.
3. Panneau de droite → **Session options** :
   - **Accelerator** : `GPU T4 x2` (sinon `GPU P100`) ;
   - **Internet** : `On`.
4. Ouvre la cellule **« Plans à rendre »** et choisis tes plans (scène, durée, palette…).
   - Premier essai : mets `APERCU = True` (petit et rapide, environ 15 min) pour vérifier.
   - Ensuite : `APERCU = False` pour la vraie qualité (quelques heures).
5. **Run All** (▶▶ en haut). Tu peux fermer l'onglet : choisis plutôt **Save Version → Save & Run All**
   pour que le rendu continue même si tu quittes la page.
6. À la fin : onglet **Output** → télécharge `videos_cosmos.zip` (un `.mp4` par plan).
7. Envoie-moi les `.mp4` : je fais le montage (rythme, musique, texte, Orbe, accroche dès 0:00).

## Réglages utiles par scène
| Scène | Options | Effet |
|---|---|---|
| `nebuleuse` | `--palette bleu / feu / emeraude / rose`, `--seed N`, `--couverture 0.2` | une graine = une nébuleuse différente ; couverture = quantité de gaz |
| `planete` | `--type gazeuse / glace / rose / rocheuse`, `--inclinaison 24`, `--lune 0/1` | type de planète, angle des anneaux |
| `hyperespace` | `--vitesse 1.0`, `--etoiles 7000` | vol dans les étoiles (ouverture idéale) |
| `galaxie` | `--bras 2`, `--torsion 2.2` | nombre et enroulement des bras |

Quota Kaggle : environ 30 h de GPU par semaine, sessions de 12 h maximum.
Colab marche aussi (Exécution → Modifier le type d'exécution → GPU), mais la session gratuite peut couper plus tôt.
