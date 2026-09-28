import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../api.dart';

/// Sur Android, le partage peut suivre directement le téléchargement.
const bool shareNeedsSecondTap = false;

class VideoStore {
  final Map<String, String> _paths = {};

  bool isReady(String key) => _paths.containsKey(key);

  Future<void> prepare(ApiClient api, Uri source, String key, int size, void Function(double) onProgress) async {
    final dir = await getApplicationDocumentsDirectory();
    final dest = File('${dir.path}/$key');
    if (await dest.exists() && await dest.length() == size) {
      _paths[key] = dest.path;
      return;
    }
    await dest.parent.create(recursive: true);
    final res = await api.openStream(source);
    final total = res.contentLength ?? size;
    var received = 0;
    final sink = dest.openWrite();
    try {
      await for (final chunk in res.stream) {
        sink.add(chunk);
        received += chunk.length;
        if (total > 0) onProgress(received / total);
      }
      await sink.close();
    } catch (_) {
      await sink.close();
      if (await dest.exists()) await dest.delete();
      rethrow;
    }
    _paths[key] = dest.path;
  }

  Future<void> share(String key, String name, String caption) => SharePlus.instance.share(
    ShareParams(
      files: [XFile(_paths[key]!, mimeType: 'video/mp4', name: name)],
      text: caption.isEmpty ? null : caption,
    ),
  );
}

/// Ouvre une adresse dans le navigateur (utilisé seulement par la web app).
void openInBrowser(Uri uri) {}
