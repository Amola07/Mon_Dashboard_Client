import 'dart:typed_data';

import 'package:share_plus/share_plus.dart';
import 'package:web/web.dart' as web;

import '../api.dart';

/// Safari n'autorise la feuille de partage qu'en réponse directe à un toucher : après un long
/// téléchargement, il faut donc un second toucher sur « Partager ».
const bool shareNeedsSecondTap = true;

class VideoStore {
  // Vidéos gardées en mémoire (les deux dernières seulement : une 4K pèse vite des centaines de Mo).
  final Map<String, Uint8List> _bytes = {};

  bool isReady(String key) => _bytes.containsKey(key);

  Future<void> prepare(ApiClient api, Uri source, String key, int size, void Function(double) onProgress) async {
    if (_bytes.containsKey(key)) return;
    final data = await api.downloadBytes(source, onProgress: onProgress);
    while (_bytes.length >= 2) {
      _bytes.remove(_bytes.keys.first);
    }
    _bytes[key] = data;
  }

  // Seulement le fichier : sur iOS, un texte joint fait parfois disparaître la vidéo du partage.
  // La légende est copiée dans le presse-papiers à la place.
  Future<void> share(String key, String name, String caption) => SharePlus.instance.share(
    ShareParams(
      files: [XFile.fromData(_bytes[key]!, mimeType: 'video/mp4', name: name)],
    ),
  );
}

/// Ouvre la vidéo dans un nouvel onglet Safari (lecture, enregistrement dans Photos, partage).
void openInBrowser(Uri uri) {
  web.window.open(uri.toString(), '_blank');
}
