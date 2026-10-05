---
titre: Installer les outils
apercu: Python, ffmpeg et trois bibliothèques. Dix minutes, une seule fois.
---
# Installer les outils

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

> **Important :** toutes les commandes se lancent **depuis la racine du projet** (le dossier `Mon_Dashboard_Client`). Sinon : `ModuleNotFoundError: films`.
