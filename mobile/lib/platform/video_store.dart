/// Téléchargement et partage des vidéos, selon la plateforme :
/// - Android (natif) : fichier dans le stockage de l'app, partagé directement ;
/// - web app (iPhone / Safari) : vidéo gardée en mémoire, partagée par la feuille de partage iOS.
library;

export 'video_store_io.dart' if (dart.library.js_interop) 'video_store_web.dart';
