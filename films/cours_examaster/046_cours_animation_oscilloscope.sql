-- ════════════════════════════════════════════════════════════════════════════
-- 046 — UE « Animation en code : le style oscilloscope »
-- ════════════════════════════════════════════════════════════════════════════
--
-- Dépose une UE complète : 7 chapitres, 14 cours publiés, au nom d'un enseignant.
-- À coller tel quel dans Supabase → SQL Editor → Run. Sans risque à relancer : si l'UE existe déjà
-- chez ce compte, rien n'est écrit. Sans compte ni formation (base vierge), rien n'est écrit non plus.
--
-- Réglages (début du bloc) :
--   v_email : le compte qui publie ; NULL = le super administrateur ;
--   v_code  : le code de la formation ; NULL = celle où ce compte publie déjà le plus d'UE ;
--   v_prix  : en F CFA, 0 = gratuite.
--
-- Généré par films/cours_examaster/generer_migration.py (dépôt Mon_Dashboard_Client) ;
-- les illustrations sont servies depuis ce dépôt public, figées sur un commit.

DO $depot$
DECLARE
  v_email TEXT    := NULL;
  v_code  TEXT    := NULL;
  v_prix  INTEGER := 0;

  v_nom   TEXT := $n$Animation en code : le style oscilloscope$n$;
  v_img   TEXT := 'https://raw.githubusercontent.com/Amola07/Mon_Dashboard_Client/30b4ebf48d38a528a48d177517600bfa120cec8e/films/cours_examaster/illustrations/';
  v_prof  UUID;
  v_prog  UUID;
  v_ue    UUID;
  v_ch    UUID;
BEGIN
  IF v_email IS NOT NULL THEN
    SELECT id INTO v_prof FROM auth.users WHERE lower(email) = lower(v_email);
  ELSE
    SELECT user_id INTO v_prof FROM public.admin_users
     WHERE role = 'superadmin' ORDER BY granted_at LIMIT 1;
  END IF;
  IF v_prof IS NULL THEN
    RAISE NOTICE 'UE oscilloscope : aucun compte enseignant trouvé, rien n''est écrit.';
    RETURN;
  END IF;

  IF v_code IS NOT NULL THEN
    SELECT id INTO v_prog FROM public.programmes WHERE code = v_code;
  ELSE
    SELECT programme_id INTO v_prog FROM public.ues WHERE professeur = v_prof
     GROUP BY programme_id ORDER BY count(*) DESC LIMIT 1;
    IF v_prog IS NULL THEN
      SELECT id INTO v_prog FROM public.programmes ORDER BY cree_le LIMIT 1;
    END IF;
  END IF;
  IF v_prog IS NULL THEN
    RAISE NOTICE 'UE oscilloscope : aucune formation trouvée, rien n''est écrit.';
    RETURN;
  END IF;

  IF EXISTS (SELECT 1 FROM public.ues
              WHERE programme_id = v_prog AND professeur = v_prof AND nom = v_nom) THEN
    RAISE NOTICE 'UE oscilloscope : déjà présente chez ce compte, rien n''est écrit.';
    RETURN;
  END IF;

  INSERT INTO public.ues (programme_id, nom, professeur, description, ordre)
  VALUES (v_prog, v_nom, v_prof, $d$Apprenez à créer vous-même des vidéos animées en Python, dans un style d'écran d'oscilloscope : des traits verts lumineux qui se dessinent au rythme d'une voix off. Ce style a doublé le temps de visionnage de nos vidéos TikTok. Vous partez d'un moteur prêt à l'emploi et vous n'écrivez que ce qu'on voit à l'écran, où et à quel moment. Prérequis : des bases en Python (variables, fonctions, listes). Sept exercices corrigés.$d$,
          (SELECT count(*) FROM public.ues WHERE programme_id = v_prog)::SMALLINT)
  RETURNING id INTO v_ue;
  INSERT INTO public.prix_ue (ue_id, professeur, prix) VALUES (v_ue, v_prof, v_prix);

  -- ── 1. Découvrir le style ─────────────────────────────────────────────────
  INSERT INTO public.unites (programme_id, ue_id, nom, ordre)
  VALUES (v_prog, v_ue, $n$1. Découvrir le style$n$, 0) RETURNING id INTO v_ch;

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Ce que vous allez apprendre$t$,
    $a$Un écran noir, des traits verts qui se dessinent au rythme d'une voix, un chiffre ambre qui défile… Ce cours vous apprend à fabriquer ce style vous-même, en Python, avec un moteur déjà prêt.$a$,
    replace($c$# Ce que vous allez apprendre

À la fin de cette UE, vous saurez fabriquer **seul** une vidéo comme celle-ci :

![Trois images de l'épisode « Voiture à l'eau »](illustrations/exemple_ep23.jpg)

## Le style en une phrase

> Un écran noir d'oscilloscope, des **traits verts lumineux** qui se dessinent au rythme d'une voix off, et **une seule couleur ambre** pour ce qui compte.

## Ce qui est déjà fait pour vous

Le **moteur** s'occupe de tout ce qui est difficile :

| Le moteur fait | Vous faites |
|---|---|
| L'effet de faisceau lumineux | Choisir quoi dessiner |
| Les traînées (persistance) | Choisir où le placer |
| Les transitions entre tableaux | Choisir à quel moment de la voix |
| Les sous-titres automatiques | Choisir les sons |
| Le calage sur la voix | |
| Le mixage et le volume | |

## Le chemin

1. Découvrir le style et **pourquoi il retient l'attention**
2. Installer les outils et lancer un **premier rendu**
3. Les **trois idées de base** : l'écran, le temps, les traits
4. Les **outils de dessin** : tracer, écrire, personnages, compteurs
5. **Monter un épisode** complet, avec sons et transitions
6. **Sept exercices corrigés**

## Combien de temps ?

- **2 à 4 semaines** à raison d'une heure par jour pour faire votre premier épisode
- Ensuite, **4 à 8 h** par vidéo de 80 secondes, puis **2 à 4 h** avec l'habitude

> **Prérequis :** des bases en Python — variables, fonctions, boucles `for`, listes. Rien de plus.$c$, '](illustrations/', '](' || v_img),
    true, 0);

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Pourquoi ce style retient l'attention$t$,
    $a$Nos chiffres réels — 924 vues en 3 heures, 38 secondes de visionnage moyen — et les cinq règles qu'on en a tirées.$a$,
    replace($c$# Pourquoi ce style retient l'attention

## Les chiffres

Même chaîne, mêmes sujets « faits qui retournent le cerveau » :

| Vidéo | Style | Visionnage moyen |
|---|---|---|
| Le sucre | Images + scanner | 9 s |
| L'Antarctique | Images d'archives | 19 s |
| **L'ascenseur** | **Oscilloscope** | **38 s** |

Le temps de visionnage a **doublé**. Et après les 10 premières secondes, la courbe de rétention est **presque plate** : ceux qui restent regardent jusqu'au bout.

## Pourquoi ça marche

- **Ça bouge tout le temps.** Un nouvel élément apparaît environ chaque seconde : l'œil n'a jamais le temps de s'ennuyer.
- **Ça explique.** Un trait qui se dessine montre un mécanisme ; une photo ne le fait pas.
- **C'est reconnaissable.** Personne d'autre ne fait ça : on reconnaît la chaîne en une image.

## Le point faible : la première seconde

Sur TikTok, **la plupart des départs ont lieu à la première seconde.** Celui qui fait défiler décide sur l'image, souvent **sans le son**.

## Les cinq règles

1. **Image 0 pleine et en mouvement.** Rien ne doit « se dessiner » au départ.
2. **La surprise écrite en grand dès l'image 0**, en ambre : « VOUS NE POUVEZ PAS COULER », pas « SABLES MOUVANTS ».
3. **Un nouvel élément chaque seconde** : un trait, un mot, un chiffre, une flèche.
4. **Chaque chiffre dit par la voix s'affiche**, si possible en compteur qui défile.
5. **Une question à la fin**, à l'écran et dans la voix, avec une flèche vers les commentaires.

> Retenez surtout la règle 2 : la première seconde se gagne avec une **affirmation surprenante**, pas avec un titre descriptif.$c$, '](illustrations/', '](' || v_img),
    true, 1);

  -- ── 2. Installer et lancer ────────────────────────────────────────────────
  INSERT INTO public.unites (programme_id, ue_id, nom, ordre)
  VALUES (v_prog, v_ue, $n$2. Installer et lancer$n$, 1) RETURNING id INTO v_ch;

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Installer les outils$t$,
    $a$Python, ffmpeg et trois bibliothèques. Dix minutes, une seule fois.$a$,
    replace($c$# Installer les outils

Une seule fois, sur votre ordinateur.

## 1. Récupérer le projet

```bash
git clone https://github.com/Amola07/Mon_Dashboard_Client
cd Mon_Dashboard_Client
```

## 2. Les bibliothèques Python

```bash
pip install -r requirements.txt
```

Les trois qui comptent ici :

| Bibliothèque | À quoi elle sert |
|---|---|
| `skia-python` | dessiner les traits et les textes |
| `numpy` | les calculs |
| `scipy` | les filtres des sons |

## 3. ffmpeg

C'est lui qui assemble les images et le son en vidéo.

- **Linux :** `sudo apt install ffmpeg`
- **Mac :** `brew install ffmpeg`
- **Windows :** téléchargez-le sur ffmpeg.org et ajoutez-le au `PATH`

## 4. Vérifier

```bash
python -m films.episodes.modele_oscillo.oscillo_modele output/modele.mp4
```

Si tout va bien, vous obtenez `output/modele.mp4`, une vidéo de **11 secondes**.

> **Important :** toutes les commandes se lancent **depuis la racine du projet** (le dossier `Mon_Dashboard_Client`). Sinon : `ModuleNotFoundError: films`.$c$, '](illustrations/', '](' || v_img),
    true, 0);

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Premier rendu et aperçu rapide$t$,
    $a$Deux commandes à connaître par cœur — l'aperçu (3 secondes) et le rendu (quelques minutes).$a$,
    replace($c$# Premier rendu et aperçu rapide

## Le modèle

Le fichier `films/episodes/modele_oscillo/oscillo_modele.py` est un épisode **complet et minuscule** : deux tableaux, une voix de 11 secondes. Voici ce qu'il produit :

![Le modèle à 0,3 s, 2 s, 5,5 s et 8,5 s](illustrations/modele.jpg)

## Commande 1 : l'aperçu (quelques secondes)

```bash
python -m films.outils.apercu \
  films.episodes.modele_oscillo.oscillo_modele \
  0 2 4.5 7 8.5
```

Elle écrit `output/apercu.png` : l'écran **à chacun des instants donnés** (en secondes), côte à côte.

> **Le secret de la vitesse :** passez **90 % de votre temps** sur l'aperçu. Vous modifiez, vous relancez, vous regardez. Trois secondes à chaque fois.

## Commande 2 : le rendu (quelques minutes)

```bash
python -m films.episodes.modele_oscillo.oscillo_modele \
  output/modele.mp4
```

Ne la lancez qu'à la fin, quand l'aperçu vous plaît.

## Ce que fait le rendu

1. Il resserre les silences de la voix (au plus 0,4 s)
2. Il dessine **30 images par seconde**
3. Il ajoute les bips, les sons, les sous-titres
4. Il règle le volume au niveau TikTok$c$, '](illustrations/', '](' || v_img),
    true, 1);

  -- ── 3. Les trois idées de base ────────────────────────────────────────────
  INSERT INTO public.unites (programme_id, ue_id, nom, ordre)
  VALUES (v_prog, v_ue, $n$3. Les trois idées de base$n$, 2) RETURNING id INTO v_ch;

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$L'écran et les coordonnées$t$,
    $a$1080 × 1920 pixels, et un piège : y va de haut en bas.$a$,
    replace($c$# L'écran et les coordonnées

![L'écran, ses axes et ses zones](illustrations/coordonnees.jpg)

## Les dimensions

L'écran fait **1080 pixels de large** et **1920 de haut** (format vertical TikTok).

- `x` va de **gauche (0)** à **droite (1080)**
- `y` va de **haut (0)** en **bas (1920)**

> **Le piège :** en maths, `y` monte. Ici, **`y` descend**. Un objet qui « tombe » voit son `y` **augmenter**.

## Les zones à respecter

| Zone | Valeurs de `y` | À quoi elle sert |
|---|---|---|
| Haut | 0 → 280 | caché par l'interface TikTok |
| **Zone utile** | **280 → 1500** | **vos dessins** |
| Sous-titres | ≈ 1650 | automatiques, laissez libre |

Le titre se place à `y = 330`.

## Le centre

Le milieu horizontal s'écrit `W / 2` (c'est-à-dire 540).

## Un repère pour la taille des textes

En police à chasse fixe, **une lettre fait environ 0,6 × la taille**. Un texte de 18 lettres en taille 90 fait donc :

$$18 \times 0{,}6 \times 90 \approx 970 \text{ pixels}$$

C'est presque toute la largeur : au-delà, il sera coupé.$c$, '](illustrations/', '](' || v_img),
    true, 0);

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Le temps calé sur la voix$t$,
    $a$s(4) + 0.5, ease(), et le seul motif d'animation que vous devez connaître par cœur.$a$,
    replace($c$# Le temps calé sur la voix

## Un tableau = une fonction redessinée 30 fois par seconde

```python
def tab_mon_tableau(c, t):
    ...
```

- `c` est la toile sur laquelle on dessine
- `t` est l'**instant**, en secondes depuis le début de la vidéo

La fonction **redessine tout** à chaque image. Pour animer, on calcule les positions **à partir de `t`**.

## Parler en phrases, pas en secondes

La voix est découpée en **phrases numérotées à partir de 0**.

| Écriture | Signification |
|---|---|
| `s(4)` | début de la phrase 4 |
| `e(4)` | fin de la phrase 4 |
| `s(4) + 0.5` | une demi-seconde après le début de la phrase 4 |

> Écrivez **toujours** vos instants avec `s()` et `e()`. Si vous refaites la voix, tout reste calé.

## Le motif à connaître par cœur

![La courbe de ease](illustrations/ease.jpg)

```python
k = ease((t - DEBUT) / DUREE)
x = 200 + (800 - 200) * k
```

- Avant `DEBUT` : `k = 0`, donc `x = 200`
- Pendant : `k` monte **doucement** de 0 à 1
- Après `DEBUT + DUREE` : `k = 1`, donc `x = 800`

`ease` démarre et s'arrête en douceur : c'est ce qui rend les mouvements naturels.

## Exemple : glisser pendant une phrase

```python
k = ease((t - s(1)) / (e(1) - s(1)))
x = 300 + (780 - 300) * k
```

L'objet traverse l'écran **exactement** pendant la phrase 1.$c$, '](illustrations/', '](' || v_img),
    true, 1);

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Les traits$t$,
    $a$Tout dessin est une liste de lignes brisées. Rectangles, cercles, flèches et personnages compris.$a$,
    replace($c$# Les traits

## La règle

Tout dessin est une **liste de lignes brisées**.
Une ligne brisée est une **liste de points** `(x, y)`.

```python
# un segment
[[(100, 500), (300, 500)]]

# une croix : deux segments
[[(100, 400), (300, 600)],
 [(300, 400), (100, 600)]]
```

## Les formes toutes prêtes

| Fonction | Ce qu'elle donne |
|---|---|
| `rect_pts(x0, y0, x1, y1)` | un rectangle (une ligne brisée) |
| `cercle_pts(x, y, r)` | un cercle (une ligne brisée) |
| `fleche(x0, y0, x1, y1)` | une flèche (déjà une **liste** de lignes) |
| `bonhomme(x, y, taille, pose)` | un personnage (déjà une **liste**) |

> **Attention aux crochets :** `rect_pts` et `cercle_pts` donnent **une** ligne ; il faut les mettre dans une liste : `[rect_pts(...)]`. `fleche` et `bonhomme` sont déjà des listes.

## Additionner des dessins

Ce sont des listes : on les additionne avec `+`.

```python
boite = [rect_pts(240, 700, 840, 1300)]
dessin = boite + fleche(900, 1200, 900, 800)
```

## Les trois couleurs

| Couleur | Usage |
|---|---|
| `VERT` | le décor |
| `VERT_PALE` | le sujet principal |
| `AMBRE` | **une seule** chose importante à la fois |

L'ambre est rare : c'est ce qui le rend fort.$c$, '](illustrations/', '](' || v_img),
    true, 2);

  -- ── 4. Les outils de dessin ───────────────────────────────────────────────
  INSERT INTO public.unites (programme_id, ue_id, nom, ordre)
  VALUES (v_prog, v_ue, $n$4. Les outils de dessin$n$, 3) RETURNING id INTO v_ch;

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Tracer, écrire, titrer$t$,
    $a$Les trois fonctions que vous utiliserez dans chaque tableau.$a$,
    replace($c$# Tracer, écrire, titrer

## `trace` : dessiner au faisceau

```python
trace(c, t, t0, d, traits, col, w)
```

Dessine `traits` progressivement entre `t0` et `t0 + d`, avec un bip au départ.

| Paramètre | Rôle |
|---|---|
| `t0` | quand le tracé commence |
| `d` | sa durée (0 = d'un coup) |
| `col` | la couleur |
| `w` | l'épaisseur, de 1 à 2 |

```python
trace(c, t, s(1), 0.6,
      [rect_pts(240, 700, 840, 1300)],
      VERT_PALE, 1.3)
```

> Pour ce qui **bouge à chaque image** (un point qui tourne), utilisez plutôt `faisceau(c, traits, 1.0, col, w)` : pas de tracé progressif, pas de bip.

## `ecrit` : un texte

```python
ecrit(c, t, t0, "TEXTE", x, y, taille, col)
```

Options utiles :

- `vitesse=0.0` → le texte apparaît **d'un coup** (sinon il est tapé lettre par lettre)
- `halo=2.0` → plus lumineux
- `centre=False` → `x` désigne le bord gauche au lieu du centre

## Un texte présent dès l'image 0

```python
ecrit(c, t, -1.0, "N'OUVREZ PAS",
      W / 2, 300, 88, AMBRE,
      True, 2.2, vitesse=0.0)
```

`t0 = -1.0` : il « a commencé » avant la vidéo, il est donc **déjà là** à la première image. C'est la règle n°1.

## `titres` : la ligne de titre qui change

```python
titres(c, t, [
    (s(2), "POURQUOI ?", VERT_PALE, 70),
    (s(3), "LA PRESSION", AMBRE, 70),
])
```

Une seule ligne en haut (`y = 330`) : à chaque instant, le **dernier titre commencé** s'affiche.$c$, '](illustrations/', '](' || v_img),
    true, 0);

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Personnages, flèches et compteurs$t$,
    $a$Un personnage qui change de pose, et un chiffre qui défile — les deux éléments qui font le plus d'effet.$a$,
    replace($c$# Personnages, flèches et compteurs

## Le personnage

```python
bonhomme(x, y, taille, pose)
```

- `(x, y)` : la position **des pieds**
- `taille` : 1 = environ 76 pixels de haut ; 3 = environ 230
- `pose` : `"debout"`, `"flotte"` (bras levés), `"saut"` (accroupi), `"allonge"`

### Changer de pose en douceur

```python
k = ease((t - s(1) - 0.3) / 0.5)
dessin = bonhomme(540, 1290, 3.0,
                  "debout", "flotte", k)
trace(c, t, s(1), 0.4, dessin, VERT_PALE, 1.2)
```

Quand `k` passe de 0 à 1, le personnage lève les bras.

## Les flèches

```python
fleche(x0, y0, x1, y1)
```

La pointe est en `(x1, y1)`. Une flèche **vers le haut** : `y1` plus **petit** que `y0`.

## Le compteur

Un chiffre qui défile est l'élément le plus efficace pour retenir l'attention.

```python
v = 200 * ease((t - s(4)) / 2.0)
ecrit(c, t, s(4), f"{v:3.0f} kg",
      W / 2, 560, 90, AMBRE,
      True, 1.6, vitesse=0.0)
```

- `v` monte de 0 à 200 en 2 secondes
- `f"{v:3.0f}"` l'écrit **sans décimale**, sur 3 caractères
- `vitesse=0.0` : sinon le chiffre serait « tapé » à chaque image

### Un compte à rebours

```python
reste = max(0, 60 - 10 * (t - s(2)))
```

Il part de 60 et perd 10 par seconde, sans descendre sous 0.$c$, '](illustrations/', '](' || v_img),
    true, 1);

  -- ── 5. Monter un épisode complet ──────────────────────────────────────────
  INSERT INTO public.unites (programme_id, ue_id, nom, ordre)
  VALUES (v_prog, v_ue, $n$5. Monter un épisode complet$n$, 4) RETURNING id INTO v_ch;

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Le déroulé d'un épisode$t$,
    $a$De la voix ElevenLabs à la vidéo publiée, en six étapes.$a$,
    replace($c$# Le déroulé d'un épisode

## 1. Copier le modèle

```bash
cp -r films/episodes/modele_oscillo \
      films/episodes/ep25_monsujet
```

Renommez `oscillo_modele.py` en `oscillo_ep25.py`.

## 2. Mettre la voix

Placez le fichier ElevenLabs dans `ep25_monsujet/audio/voix.mp3`, puis corrigez la ligne dans le code :

```python
M.VOIX = os.path.join(HERE, "audio", "voix.mp3")
```

## 3. Caler la voix

```bash
python -m films.outils.minuter_voix \
  films/episodes/ep25_monsujet/audio/voix.mp3
```

L'outil écrit `audio/voix.json` : une ligne `[début, fin, "texte"]` par morceau de voix.

- **Recopiez** la phrase du script dans chaque ligne
- Si une phrase a été **coupée en deux**, fusionnez : gardez le début de la première et la fin de la seconde

Chaque ligne devient une phrase numérotée : 0, 1, 2…

## 4. Écrire les tableaux

Un tableau par **idée** (environ toutes les 5 à 10 secondes). Puis la liste dans `tableaux()` :

```python
def tableaux():
    return [
        (0.0, tab_accroche, None),
        (s(4) - 0.1, tab_explication, "neige"),
    ]
```

## 5. Vérifier à l'aperçu

```bash
python -m films.outils.apercu \
  films.episodes.ep25_monsujet.oscillo_ep25 \
  0 3 10 25 40
```

## 6. Rendre

```bash
python -m films.episodes.ep25_monsujet.oscillo_ep25 \
  output/ep25.mp4
```

> **Le meilleur exemple complet :** `films/episodes/ep23_voiture_eau/oscillo_ep23.py` — 8 tableaux, 76 secondes. Après cette UE, vous en comprendrez chaque ligne.$c$, '](illustrations/', '](' || v_img),
    true, 0);

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Transitions, flashs et sons$t$,
    $a$Les trois fonctions du bas du fichier qui font le montage.$a$,
    replace($c$# Transitions, flashs et sons

En bas de chaque épisode, trois fonctions font le **montage**.

## `tableaux()` : l'ordre et les transitions

```python
(début, fonction, transition)
```

| Transition | Effet |
|---|---|
| `None` | aucune (le premier tableau) |
| `"neige"` | neige de télévision |
| `"balayage"` | une ligne lumineuse qui balaie l'écran |
| `"glitch"` | des bandes décalées |
| `"noir"` | retour au noir, puis tout se redessine |

> **Variez-les.** La même transition à chaque fois devient invisible.

## `chocs()` : flashs et secousses

```python
def chocs():
    flashs = [s(3)]
    secousses = [(s(3), 0.2)]
    return flashs, secousses
```

À réserver aux **révélations** : un impact, un chiffre énorme, le « NON ».

## `effets()` : les sons

```python
def effets(tabs):
    ev = [
        (0.0, Z.thump(0.35)),
        (s(3), Z.boom(0.5, 60)),
    ]
    return ev
```

Les bips du faisceau et de la frappe sont **automatiques**. Vous ajoutez les sons qui racontent.

## La boîte à sons

| Famille | Sons |
|---|---|
| Impacts | `thump`, `boom`, `clang`, `craquement` |
| Mouvements | `whoosh`, `riser`, `chirp(f0, f1)` |
| Notes | `cloche`, `pince`, `ding_ascenseur` |
| Ambiances | `vent`, `bulles`, `vibration`, `foule`, `applaudissements` |
| Tension | `tictac`, `alarme`, `coeur`, `grincement` |
| Effets d'écran | `glitch`, `neige` |

> **Astuce son :** un silence juste avant une révélation la rend deux fois plus forte.$c$, '](illustrations/', '](' || v_img),
    true, 1);

  -- ── 6. Exercices corrigés ─────────────────────────────────────────────────
  INSERT INTO public.unites (programme_id, ue_id, nom, ordre)
  VALUES (v_prog, v_ue, $n$6. Exercices corrigés$n$, 5) RETURNING id INTO v_ch;

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Exercices 1 à 4 (corrigés)$t$,
    $a$Changer un titre, déplacer une forme, ajouter une ligne, animer un personnage. Avec les corrigés.$a$,
    replace($c$# Exercices 1 à 4

Travaillez dans `films/episodes/modele_oscillo/oscillo_modele.py`. Vérifiez **chaque** exercice avec l'aperçu.

## Exercice 1 — Changer le titre (5 min)

Remplacez « MON TITRE » par « N'OUVREZ PAS », en vert pâle, taille 100.

**Corrigé :**

```python
ecrit(c, t, -1.0, "N'OUVREZ PAS",
      W / 2, 330, 100, VERT_PALE,
      True, 2.0, vitesse=0.0)
```

## Exercice 2 — Déplacer et recolorer (10 min)

Mettez le rectangle plus haut et en ambre ; faites-le apparaître au début de la phrase 1.

**Corrigé :**

```python
trace(c, t, s(1), 0.6,
      [rect_pts(240, 560, 840, 1160)],
      AMBRE, 1.3)
```

> Pensez à remonter aussi les pieds du personnage (`y = 1150`), sinon il sort de la boîte.

## Exercice 3 — Une deuxième ligne (10 min)

Sous le titre, à `y = 430`, ajoutez « LA PORTIÈRE », présent dès l'image 0.

**Corrigé :**

```python
ecrit(c, t, -1.0, "LA PORTIÈRE",
      W / 2, 430, 100, VERT_PALE,
      True, 2.0, vitesse=0.0)
```

## Exercice 4 — Faire glisser le personnage (20 min)

Le personnage doit aller de `x = 300` à `x = 780` pendant la phrase 1.

**Corrigé :**

```python
g = ease((t - s(1)) / (e(1) - s(1)))
x = 300 + (780 - 300) * g
dessin = bonhomme(x, 1290, 3.0,
                  "debout", "flotte", k)
trace(c, t, s(1), 0.4, dessin, VERT_PALE, 1.2)
```

On utilise une **autre** variable (`g`) pour ne pas écraser `k`, qui sert déjà à la pose.$c$, '](illustrations/', '](' || v_img),
    true, 0);

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Exercices 5 à 7 (corrigés)$t$,
    $a$Un compte à rebours, un son avec un flash, et votre premier tableau à vous.$a$,
    replace($c$# Exercices 5 à 7

## Exercice 5 — Un compte à rebours (20 min)

Dans `tab_deux`, affichez un compte à rebours de 60 à 0, qui descend de 10 par seconde à partir de `s(2)`, en ambre, centré à `y = 560`.

**Corrigé :**

```python
reste = max(0, 60 - 10 * (t - s(2)))
ecrit(c, t, s(2), f"{reste:2.0f} s",
      W / 2, 560, 90, AMBRE,
      True, 1.6, vitesse=0.0)
```

## Exercice 6 — Un son et un flash (15 min)

Ajoutez un bruit métallique et un flash à l'instant où la flèche apparaît (`s(1) + 1.0`).

**Corrigé :**

```python
def chocs():
    flashs = [s(1) + 1.0, s(3)]
    secousses = [(s(3), 0.2)]
    return flashs, secousses
```

et dans `effets()` :

```python
ev.append((s(1) + 1.0, Z.clang(300, 0.2)))
```

## Exercice 7 — Votre tableau (1 h)

Ajoutez un troisième tableau qui commence à `s(3)` avec une transition `"glitch"`, et dessinez-y une voiture vue de côté.

**Pistes :**

1. Copiez la fonction `cote(...)` de l'épisode 23 (`ep23_voiture_eau/oscillo_ep23.py`)
2. Écrivez `tab_trois(c, t)` qui trace `v["caisse"] + v["roues"]`
3. Ajoutez une ligne d'eau qui ondule avec `math.sin(x / 34 + t * 4)`
4. Déclarez-le dans `tableaux()` :

```python
(s(3) - 0.1, tab_trois, "glitch")
```

> **Bravo.** Si vous avez fait les sept exercices, vous savez tout ce qu'il faut pour un épisode complet. Ouvrez l'épisode 23 : vous y reconnaîtrez chaque ligne.$c$, '](illustrations/', '](' || v_img),
    true, 1);

  -- ── 7. Dépannage ──────────────────────────────────────────────────────────
  INSERT INTO public.unites (programme_id, ue_id, nom, ordre)
  VALUES (v_prog, v_ue, $n$7. Dépannage$n$, 6) RETURNING id INTO v_ch;

  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)
  VALUES (v_ch, v_prof, $t$Les erreurs fréquentes$t$,
    $a$Rien ne s'affiche ? Tout est décalé ? Le texte est coupé ? Les causes et les solutions.$a$,
    replace($c$# Les erreurs fréquentes

## Rien ne s'affiche

Trois causes, dans l'ordre :

1. `y` est **en dehors** de 0 à 1920 (souvent : oublié que `y` descend)
2. `t0` est **après la fin** de la vidéo
3. Un trait n'est **pas dans une liste** : `rect_pts(...)` au lieu de `[rect_pts(...)]`

## `IndexError` sur `s(12)`

`voix.json` contient **moins de phrases** que prévu. La numérotation commence à **0** : avec 12 lignes, la dernière est `s(11)`.

## Tout est décalé par rapport à la voix

Une phrase coupée en deux dans `voix.json` n'a pas été **fusionnée**. Toutes les phrases suivantes ont un numéro de trop.

## Le texte est coupé sur les bords

Le texte est trop long pour sa taille. Rappel :

$$\text{largeur} \approx \text{lettres} \times 0{,}6 \times \text{taille}$$

Coupez sur deux lignes, ou baissez la taille.

## `ModuleNotFoundError: films`

La commande n'est pas lancée **depuis la racine du projet** (`Mon_Dashboard_Client`).

## Le chiffre d'un compteur « clignote »

Vous avez oublié `vitesse=0.0` : le texte est retapé à chaque image.

## Le rendu est lent

C'est normal : 30 images par seconde, 80 secondes, donc 2 400 images. Utilisez l'**aperçu** pour tout régler, et ne lancez le rendu qu'une fois à la fin.$c$, '](illustrations/', '](' || v_img),
    true, 0);

  RAISE NOTICE 'UE oscilloscope déposée : 7 chapitres, 14 cours (UE %).', v_ue;
END
$depot$;
