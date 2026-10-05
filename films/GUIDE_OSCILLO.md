# Guide : faire soi-même un épisode en style oscilloscope

Pour quelqu'un qui a des bases en Python : variables, fonctions, boucles `for`, listes.
Le moteur (faisceau lumineux, persistance, transitions, sous-titres, calage sur la voix, sons, volume) est déjà écrit.
Tu n'écris que **les tableaux**, c'est-à-dire ce qu'on voit, où, et à quel moment de la voix.

---

## 0. Installation (une seule fois)

```bash
pip install -r requirements.txt        # numpy, skia-python, scipy…
# il faut aussi ffmpeg :  sudo apt install ffmpeg   (Mac : brew install ffmpeg)
```

Toutes les commandes se lancent **depuis la racine du projet** (`Mon_Dashboard_Client/`).

Test : `python -m films.episodes.modele_oscillo.oscillo_modele output/modele.mp4` doit produire une vidéo de ≈ 11 s.

---

## 1. Le déroulé d'un épisode

1. **Copier le modèle** :
   `cp -r films/episodes/modele_oscillo films/episodes/ep25_monsujet`
   puis renommer `oscillo_modele.py` en `oscillo_ep25.py`.
2. **Mettre la voix** ElevenLabs dans `films/episodes/ep25_monsujet/audio/voix.mp3`
   et corriger la ligne `M.VOIX = ...` du fichier :
   `M.VOIX = os.path.join(HERE, "audio", "voix.mp3")`.
3. **Caler la voix** :
   `python -m films.outils.minuter_voix films/episodes/ep25_monsujet/audio/voix.mp3`
   → écrit `audio/voix.json`, une ligne par morceau de voix : `[début, fin, "texte"]`.
   Recopie la phrase du script dans chaque ligne. Si une phrase a été coupée en deux morceaux, fusionne-les
   (garde le début du premier et la fin du second).
   Chaque ligne devient une **phrase numérotée** : la première est la phrase 0, puis 1, 2…
4. **Écrire les tableaux** dans `oscillo_ep25.py` (voir ci-dessous).
5. **Vérifier vite avec l'aperçu** (quelques secondes, pas de vidéo) :
   `python -m films.outils.apercu films.episodes.ep25_monsujet.oscillo_ep25 0 3 10 25 40`
   → `output/apercu.png` montre l'écran à 0 s, 3 s, 10 s, 25 s et 40 s.
6. **Rendre la vidéo** (quelques minutes) :
   `python -m films.episodes.ep25_monsujet.oscillo_ep25 output/ep25.mp4`

Astuce : passe 90 % du temps sur l'étape 5 (aperçu), et ne lance la vraie vidéo qu'à la fin.

---

## 2. Les trois idées à comprendre

### a) L'écran et les coordonnées
- 1080 × 1920 pixels. `x` va de gauche (0) à droite (1080), **`y` va de haut (0) en bas (1920)**.
- Zone utile : `y` de **280 à 1500**. Au-dessus, il y a l'interface TikTok ; vers `y = 1650`, les sous-titres
  (automatiques).
- Le centre horizontal, c'est `W / 2` (= 540).

### b) Le temps
- Un **tableau** est une fonction `def tab_xxx(c, t):`. Elle est appelée 30 fois par seconde et
  **redessine tout** à l'instant `t` (en secondes depuis le début de la vidéo).
- `s(i)` = début de la phrase i ; `e(i)` = sa fin. On écrit donc les instants **par rapport à la voix** :
  `s(4) + 0.5` veut dire « une demi-seconde après le début de la phrase 4 ».
- `ease(u)` transforme une progression `u` en mouvement doux, bloqué entre 0 et 1. Le motif à connaître par cœur :

  ```python
  k = ease((t - DEBUT) / DUREE)      # 0 avant DEBUT, monte doucement, 1 après DEBUT + DUREE
  x = 200 + (800 - 200) * k          # de x = 200 à x = 800
  ```

### c) Les « traits »
Tout dessin est une **liste de lignes brisées** ; une ligne brisée est une liste de points `(x, y)`.

```python
[[(100, 500), (300, 500)]]                         # un segment
[[(100, 500), (300, 500)], [(200, 400), (200, 600)]]  # deux segments (une croix)
[rect_pts(100, 400, 300, 600)]                     # un rectangle (x0, y0, x1, y1)
[cercle_pts(540, 900, 120)]                        # un cercle (centre x, centre y, rayon)
fleche(100, 900, 400, 900)                         # une flèche (déjà une liste de lignes)
bonhomme(540, 1300, 3.0, "debout")                 # un personnage, pieds en (540, 1300), taille ×3
```

Pour additionner des dessins : `rect + fleche(...)` (ce sont des listes).

---

## 3. Les fonctions à utiliser (aide-mémoire)

| Fonction | Ce qu'elle fait |
|---|---|
| `trace(c, t, t0, d, traits, col, w)` | trace `traits` au faisceau entre `t0` et `t0 + d` (avec un bip) ; `w` = épaisseur (1 à 2) |
| `faisceau(c, traits, 1.0, col, w)` | dessine `traits` tout de suite, sans tracé ni bip (pour ce qui bouge à chaque image) |
| `ecrit(c, t, t0, "TEXTE", x, y, taille, col)` | tape le texte à partir de `t0` ; `vitesse=0.0` → apparaît d'un coup ; `halo=2.0` → plus lumineux ; `centre=False` → `x` = bord gauche |
| `titres(c, t, [(t0, "TITRE", col, taille), …])` | une ligne de titre en haut (y = 330) qui change au fil de la voix |
| `bonhomme(x, y, ech, "debout", "flotte", k)` | personnage ; passe d'une pose à l'autre quand `k` va de 0 à 1. Poses : `debout`, `flotte` (bras levés), `saut` (accroupi), `allonge` |
| `fleche(x0, y0, x1, y1)`, `rect_pts`, `cercle_pts` | formes de base |

Couleurs : `VERT` (décor), `VERT_PALE` (sujet principal), `AMBRE` (**une seule chose importante à la fois** : danger,
chiffre clé, réponse).

### Montage : les 3 fonctions en bas du fichier
- `tableaux()` : la liste `(début, fonction, transition)`. Transitions : `None`, `"neige"`, `"balayage"`,
  `"glitch"`, `"noir"`. Change de tableau à chaque **nouvelle idée** (≈ toutes les 5 à 10 s).
- `chocs()` : instants de **flash** blanc et de **secousse** (révélations, impacts).
- `effets(tabs)` : la liste `(instant, son)`. Les sons sont dans `films/styles/oscillo_son.py` :
  `thump` (coup sourd), `boom` (impact grave), `clang` (métal), `whoosh`, `riser` (montée), `chirp(f0, f1)`
  (bip qui glisse), `cloche`, `pince` (note), `alarme`, `tictac`, `bulles`, `vent`, `vibration`, `grincement`,
  `craquement`, `crepitement`, `coeur`, `glitch`, `neige`, `souffle`, `foule`, `applaudissements`,
  `ding_ascenseur`… Les bips du faisceau et de la frappe sont automatiques.

---

## 4. Les règles qui font la rétention (tirées de nos statistiques)

1. **Image 0 pleine et en mouvement** : rien ne doit « se dessiner » au départ. Utilise `t0 = -1.0` et
   `vitesse=0.0` pour que tout soit déjà là.
2. **La surprise écrite en grand dès l'image 0**, en ambre, sur deux lignes (≈ 88 px) :
   « VOUS NE POUVEZ / PAS COULER », pas « SABLES MOUVANTS ».
3. **Un nouvel élément chaque seconde environ** (un trait, un mot, un chiffre, une flèche).
4. **Chaque chiffre dit par la voix apparaît à l'écran**, si possible sous forme de compteur qui défile.
5. **Une question à la fin**, à l'écran et dans la voix, avec la flèche vers les commentaires (copie
   `tab_question` de l'épisode 23).

---

## 5. Exercices (dans l'ordre, sur le modèle)

Fais-les dans `films/episodes/modele_oscillo/oscillo_modele.py`, vérifie chacun avec l'aperçu.

1. **Changer le titre** (5 min) : remplace « MON TITRE » par « N'OUVREZ PAS », en vert pâle, taille 100.
2. **Déplacer et recolorer** (10 min) : mets le rectangle plus haut et en ambre ; fais-le apparaître au début de la
   phrase 1 au lieu de 0,2 s.
3. **Un deuxième titre** (10 min) : sous le titre, à `y = 430`, ajoute « LA PORTIÈRE » qui apparaît d'un coup dès l'image 0.
4. **Animer une position** (20 min) : fais glisser le bonhomme de `x = 300` à `x = 780` pendant la phrase 1
   (indice : `k = ease((t - s(1)) / (e(1) - s(1)))`).
5. **Un compteur de temps** (20 min) : dans `tab_deux`, affiche un compte à rebours de 60 à 0 qui descend de 10 par
   seconde à partir de `s(2)`, en ambre, centré à `y = 560`.
6. **Un son et un flash** (15 min) : ajoute un `Z.clang(300, 0.2)` et un flash à l'instant où la flèche apparaît.
7. **Un tableau à toi** (1 h) : ajoute un troisième tableau qui commence à `s(3)` avec une transition `"glitch"`, et
   dessine une voiture vue de côté avec `cote(...)`, copiée de l'épisode 23.

Après ça, ouvre `films/episodes/ep23_voiture_eau/oscillo_ep23.py` : tu comprendras chaque ligne.
C'est ton meilleur exemple complet (8 tableaux, ≈ 76 s).

---

## 6. Erreurs fréquentes

| Symptôme | Cause habituelle |
|---|---|
| Rien ne s'affiche | `y` en dehors de 0–1920, ou `t0` après la fin de la vidéo, ou trait oublié dans une liste `[...]` |
| `IndexError` sur `s(12)` | `voix.json` a moins de phrases que prévu (vérifie la numérotation, qui commence à 0) |
| Tout est décalé par rapport à la voix | les instants de `voix.json` ne correspondent pas à la bonne phrase (fusion oubliée) |
| Texte coupé sur les bords | texte trop long pour sa taille : en police mono, une lettre fait ≈ 0,6 × la taille → 90 px × 18 lettres ≈ 970 px |
| `ModuleNotFoundError: films` | la commande n'est pas lancée depuis la racine du projet |
