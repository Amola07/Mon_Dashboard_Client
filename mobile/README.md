# Anime TikTok Studio (application mobile)

Télécommande Flutter du pipeline animé → TikTok : elle se connecte au serveur lancé par le notebook
(`python -m anime_tiktok serve`) et permet d'analyser les épisodes, valider les extraits, choisir le style
du jour, lancer le rendu, regarder les vidéos et les partager vers TikTok.

Installation, signature et connexion : voir la section « Application mobile » du README principal.

```bash
flutter pub get
flutter analyze && flutter test
flutter build apk --release        # nécessite le SDK Android
```
