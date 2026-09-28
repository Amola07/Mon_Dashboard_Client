# Animé → TikTok (4K, 120/240 fps)

Pipeline qui prend une saison d'animé (12 épisodes ou plus), repère les moments forts, les rend en
**vertical 9:16, 4K, 120 ou 240 fps**, puis fait le montage selon le style du jour et livre des vidéos
prêtes à publier, avec leur légende.

```
épisodes ──► 1. analyse ──► 2. sélection ──► (vous validez) ──► 3. rendu 4K/HFR ──► 4. montage ──► vidéos + légendes
             plans, son,     top extraits,                      recadrage 9:16,      style du jour
             mouvement,      aperçu HTML                        RIFE, Real-ESRGAN
             OP/ED ignorés
```

## Présentations narrées (onglet « Narration »)

Format « présentation d'animé » : vous écrivez un script, une voix off est générée et les plans des
épisodes sont choisis pour illustrer chaque phrase, puis la vidéo est montée (voix, musique de fond
baissée sous la voix, titre de l'animé en grand, 1080×1920 à 60 fps).

```
[enigme] Il le ramène 18 ans plus tôt. À l'époque où il était encore un enfant... {visuel: enfants dans la neige}
[tendu] Cette fois, ce n'est pas un accident qu'il doit empêcher.
[posé] Cet anime, c'est Erased.
[enthousiasme] Si tu veux savoir jusqu'où le temps va le laisser aller... tu sais quoi faire.
```

- `[émotion]` règle le ton (vitesse, pauses) et l'ambiance des plans : enigme, tendu, déterminé, anxieux,
  inquiet, triste, posé, enthousiasme, épique…
- `{visuel: …}` décrit les plans voulus pour la phrase (facultatif, améliore beaucoup le choix).
- « Cet anime, c'est X » (ou `{titre: X}`) affiche le titre à ce moment.
- **Voix** : Kokoro-82M (licence Apache 2.0, usage commercial autorisé), voix française `ff_siwis`,
  sur le GPU de Kaggle ; repli sur espeak-ng si Kokoro n'est pas installé.
- **Choix des plans** : CLIP multilingue compare chaque phrase (en français) aux images des épisodes,
  combiné à l'ambiance de l'émotion, à la beauté du plan et à l'ordre de l'histoire. Pour chaque plan,
  5 candidats sont proposés dans l'application : un toucher pour changer.
- Visez plus d'une minute (≈ 160 mots) : c'est la durée minimale des vidéos rémunérées sur TikTok.

En ligne de commande : `python -m anime_tiktok present-plan --script script.txt --name erased`, puis
`python -m anime_tiktok present-render --name erased`.

## Vidéos « oddly satisfying » générées (`satisfying/`)

Vidéos 100 % créées par le code : image, son et légende. Aucun épisode, aucun média extérieur, donc aucun
problème de droits, et au-delà d'une minute elles sont éligibles à la rémunération TikTok. Pas de GPU : une
vidéo de 64 s en 1080×1920 à 60 fps se rend en 5 à 7 minutes sur un processeur ordinaire.

```bash
sudo apt-get install -y libegl1 && pip install skia-python numpy
python -m satisfying                      # concept choisi automatiquement (le moins récemment utilisé)
python -m satisfying --concept pendulum   # ou grow, escape, spiro, multiply
python -m satisfying --preview 6          # test rapide : 6 premières secondes
```

| Concept | Ce qui se passe | Fin |
|---|---|---|
| `grow` | une balle grossit à chaque rebond jusqu'à remplir le cercle | elle redevient petite : la vidéo boucle |
| `escape` | une balle s'échappe d'anneaux qui tournent, chacun éclate en billes | les anneaux se reforment |
| `pendulum` | vague de pendules vue de dessus : motifs, désordre, réalignement | réalignement parfait : boucle exacte |
| `spiro` | des bras articulés dessinent lentement une rosace | la rosace s'efface |
| `multiply` | chaque rebond fait naître une balle, le cercle se remplit | toutes se rejoignent en une seule |

Chaque vidéo tire au hasard sa palette (pastels clairs ou nuit douce), son timbre (goutte, kalimba, cristal,
piano doux), sa tonalité, sa suite d'accords et tous les paramètres du concept : deux vidéos du même concept
ne se ressemblent pas. Chaque impact joue une note juste dans l'accord en cours, sur une nappe très discrète.
`satisfying/history.json` garde la trace des vidéos produites pour alterner les concepts et les palettes.
Sortie : `output/satisfying/<date>_<concept>_<graine>.mp4` et un `.txt` avec la légende et les hashtags.

Ajouter un concept : un module dans `satisfying/concepts/` avec `TITLE` et `render(ctx)`, puis son nom dans
`concepts.NAMES`.

## Utilisation rapide (Kaggle ou Colab)

Ouvrez `notebooks/anime_tiktok.ipynb` dans Kaggle (*File → Import Notebook*) ou Colab, activez le GPU,
puis exécutez les cellules dans l'ordre. Le notebook installe tout, analyse, affiche les extraits
proposés, vous laisse en écarter, puis rend et monte les vidéos.

- **Kaggle** : ajoutez les épisodes comme *Dataset*, activez *Internet*. Résultat : `livraison.zip` dans l'onglet *Output*.
- **Colab** : déposez les épisodes dans `Mon Drive/anime_tiktok/episodes`. Les résultats et le travail déjà fait
  sont enregistrés sur Drive : une session coupée reprend là où elle s'était arrêtée.

## Application mobile (tout piloter depuis le téléphone)

L'application Android **Anime TikTok Studio** (`mobile/`, Flutter) sert de télécommande au pipeline :

| Onglet | Ce qu'on y fait |
|---|---|
| Accueil | état du serveur, tâche en cours (progression, journal, arrêt), 1. analyser, 2. proposer les extraits, 3. générer ; ajouter des épisodes (lien direct ou fichier du téléphone) |
| Extraits | vignettes, aperçu vidéo de chaque extrait, garder / écarter, puis « Générer » |
| Vidéos | regarder, copier la légende, télécharger et **partager vers TikTok** |
| Réglages | nom de l'animé, résolution, fps, nombre et durée des extraits ; connexion |

Au moment de générer, on choisit le style du jour, le fps (60/120/240) et la musique (on peut en envoyer
depuis le téléphone).

### iPhone : web app sur l'écran d'accueil (gratuit)
La même application existe en version web. Chaque modification de `mobile/` la compile (workflow
« Web app (iPhone) ») et la publie sur la branche `web-build`. Deux façons de l'ouvrir :

- **Adresse fixe (recommandé, une seule fois)** : compte gratuit Cloudflare → *Workers & Pages → Create →
  Import a repository* → ce dépôt. Dans *Settings → Build* du Worker créé :
  **branche de production `web-build`**, **commande de build vide**, commande de déploiement
  `npx wrangler deploy` (celle par défaut). La branche contient déjà `wrangler.jsonc` ; si votre Worker ne
  s'appelle pas `mon-dashboard-client`, changez `"name"` dans `mobile/web/wrangler.jsonc`.
  Vous obtenez une adresse `https://<nom>.<compte>.workers.dev`, mise à jour à chaque modification.
  (Cloudflare Pages ou Netlify fonctionnent aussi : branche `web-build`, pas de commande de build, dossier `/`.)
- **Sans compte** : la télécommande du notebook sert aussi la web app, à l'adresse publique affichée par la
  cellule (`https://xxxx.trycloudflare.com`). Cette adresse change à chaque session.

Sur l'iPhone : ouvrez l'adresse dans **Safari** → bouton Partager → **Sur l'écran d'accueil**. L'app s'ouvre
ensuite en plein écran. Pour partager une vidéo vers TikTok : « Préparer » (téléchargement), puis
« Partager » (Safari exige ce second toucher). L'icône ↗ ouvre la vidéo dans Safari (lecture, enregistrement
dans Photos).

### Android : installer l'APK
Chaque modification de `mobile/` poussée sur GitHub déclenche le workflow « Application Android », qui
compile l'APK et le publie dans une Release. Sur le téléphone, ouvrez :

`https://github.com/Amola07/Mon_Dashboard_Client/releases/latest/download/anime-tiktok-studio.apk`

puis autorisez l'installation depuis le navigateur. Si le dépôt est privé, connectez-vous d'abord à GitHub
dans le navigateur du téléphone.

**Mises à jour sans désinstaller** : Android n'accepte une nouvelle version que si elle est signée avec la
même clé. Créez une clé une fois (sur un PC avec Java) :
```bash
keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
base64 -w0 upload-keystore.jks   # à copier dans le secret ANDROID_KEYSTORE_BASE64
```
puis ajoutez dans GitHub (*Settings → Secrets and variables → Actions*) : `ANDROID_KEYSTORE_BASE64`,
`ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` (`upload`) et, si différent, `ANDROID_KEY_PASSWORD`.
Sans ces secrets, l'APK est signé avec une clé temporaire : il faudra désinstaller l'ancienne version
avant d'installer la nouvelle.

### Connecter l'application
1. Dans le notebook, cellule « Télécommande » : choisissez `MOT_DE_PASSE` et `SUJET_NTFY` (un nom unique,
   ex. `anime-tiktok-k7x2p9`).
2. Kaggle : *Save Version → Save & Run All* (tourne jusqu'à 12 h en arrière-plan). Colab : exécutez les
   cellules et laissez l'onglet ouvert.
3. Dans l'application : entrez le même sujet ntfy et le même mot de passe, puis « Se connecter ».

Le serveur ouvre une adresse publique https (tunnel Cloudflare) et la publie sur ntfy.sh : l'application la
retrouve toute seule, même quand elle change à chaque nouvelle session. Pour être notifié à la fin d'un
rendu application fermée, abonnez-vous au même sujet dans l'application **ntfy**.

Hors notebook : `python -m anime_tiktok serve --tunnel --token MOT_DE_PASSE --ntfy-topic SUJET`.

## Utilisation en ligne de commande

```bash
pip install -r requirements.txt
bash scripts/setup_tools.sh             # ffmpeg (NVENC), RIFE, Real-ESRGAN, modèles

python -m anime_tiktok analyze          # analyse input/episodes
python -m anime_tiktok select           # propose les extraits -> work/selection/clips.csv + review.html
# ouvrez review.html, mettez keep=0 dans clips.csv pour écarter un extrait
python -m anime_tiktok make --style brut
python -m anime_tiktok make --style hype --music input/music/son.mp3
python -m anime_tiktok make --style cinematique --set render.fps=240

python -m anime_tiktok run --style brut # tout d'un coup, sans validation
python -m anime_tiktok backends         # affiche les outils GPU détectés
```

Toute valeur de `config.yaml` se surcharge avec `--set cle.sous_cle=valeur`.

## Les étapes en détail

### 1. Analyse (`anime_tiktok/analyze.py`, `op_ed.py`)
Sans IA payante : chaque épisode est décodé en basse résolution pour mesurer, toutes les 0,5 s,
le volume, les attaques sonores (impacts, coups), le mouvement à l'image et les changements de plan.
Les passages dont le son se répète d'un épisode à l'autre (opening, ending, récap) sont détectés et exclus.

### 2. Sélection (`select.py`)
Un score d'intensité combine ces mesures (poids réglables dans `selection.weights`). Les extraits candidats
commencent et finissent sur des changements de plan ; les meilleurs sont retenus avec un maximum par épisode.
Sortie : `clips.csv` (colonne `keep` à éditer) et `review.html` (vignettes au moment fort).

### 3. Rendu (`reframe.py`, `enhance.py`)
- **Recadrage 9:16** : `crop` suit l'action (visages d'animé, sinon zones de détail et de mouvement), avec
  une position fixe par plan pour éviter les tremblements ; `blur` garde l'image entière sur un fond flouté.
- **Suppression des images dupliquées** (`render.dedupe`) : un animé répète souvent chaque dessin 2 ou 3 fois ;
  les retirer avant l'interpolation donne un mouvement régulier au lieu de saccades.
- **Interpolation** : RIFE v4.6 (GPU, Vulkan) jusqu'au fps cible ; repli automatique sur ffmpeg `minterpolate`.
- **Agrandissement** : Real-ESRGAN `animevideov3` via PyTorch/CUDA (ou ncnn/Vulkan) ; repli sur Lanczos.
- **Encodage** : HEVC NVENC sur GPU (repli libx265). Les images passent en flux et par lots, donc l'espace disque
  reste faible même en 4K à 240 fps.

Les extraits rendus sont mis en cache dans `work/rendered/<recadrage>/` : changer de style réutilise les rendus.

### 4. Montage et livraison (`montage.py`)
Styles fournis (modifiables et extensibles dans `config.yaml`) :

| Style | Recadrage | Montage |
|---|---|---|
| `brut` | suit l'action | une vidéo par extrait, accroche d'1,5 s sur le moment fort, flash de transition |
| `hype` | suit l'action | edit de 30 s coupé sur les temps d'une musique (tempo détecté), zoom « punch », flashs |
| `cinematique` | image entière + fond flou | une vidéo par extrait, fondus |

Chaque vidéo est livrée dans `output/<date>_<style>/` avec un `.txt` contenant la légende et les hashtags
(`delivery.caption`).

## Temps de calcul
L'analyse est rapide (quelques minutes par épisode, sur CPU). Le rendu est l'étape lourde : un extrait de
30 s en 4K à 120 fps représente 3 600 images à interpoler, agrandir et encoder, et le 240 fps double ce
travail. Commencez par quelques extraits pour mesurer le temps sur votre GPU, puis ajustez
`selection.clips_total` et `selection.max_seconds`.

## Tests
```bash
python tests/test_pipeline.py   # génère de faux épisodes et vérifie toute la chaîne (backends CPU)
python tests/test_server.py     # API du serveur de contrôle
cd mobile && flutter analyze && flutter test
```
