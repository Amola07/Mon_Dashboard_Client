---
titre: Le déroulé d'un épisode
apercu: De la voix ElevenLabs à la vidéo publiée, en six étapes.
---
# Le déroulé d'un épisode

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

> **Le meilleur exemple complet :** `films/episodes/ep23_voiture_eau/oscillo_ep23.py` — 8 tableaux, 76 secondes. Après cette UE, vous en comprendrez chaque ligne.
