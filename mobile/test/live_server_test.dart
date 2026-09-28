// Vérifie le contrat entre l'application et un vrai serveur (python -m anime_tiktok serve).
// Ignoré sauf si LIVE_SERVER est défini, par ex. :
//   LIVE_SERVER=http://127.0.0.1:8765 LIVE_TOKEN=secret flutter test test/live_server_test.dart
import 'dart:io';

import 'package:anime_tiktok_studio/api.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final server = Platform.environment['LIVE_SERVER'];
  final token = Platform.environment['LIVE_TOKEN'] ?? '';

  test('contrat API avec le serveur Python', () async {
    final api = ApiClient(server!, token);
    expect((await api.ping())['app'], 'anime-tiktok');

    final st = await api.status();
    for (final key in ['episodes', 'analyzed', 'clips', 'kept', 'styles', 'music', 'render', 'anime']) {
      expect(st.containsKey(key), isTrue, reason: key);
    }
    expect((st['render'] as Map).keys, containsAll(['width', 'height', 'fps']));

    final settings = await api.settings();
    expect(settings.keys, containsAll(['render.fps', 'delivery.anime', 'selection.clips_total']));

    final eps = await api.episodes();
    expect(eps, isNotEmpty);
    expect((eps.first as Map).keys, containsAll(['name', 'size', 'analyzed', 'duration', 'excluded']));

    final clips = await api.clips();
    expect(clips, isNotEmpty);
    final clip = clips.first as Map;
    expect(clip.keys, containsAll(['id', 'keep', 'episode', 'start', 'end', 'duration', 'score']));
    expect(clip['keep'], isA<bool>());
    expect(await api.setKeep({clip['id'] as String: true}), greaterThan(0));

    final thumb = await HttpClient().getUrl(Uri.parse(api.thumbUrl(clip['id'] as String)))
      ..headers.add('Authorization', 'Bearer $token');
    final res = await thumb.close();
    expect(res.statusCode, 200);
    await res.drain<void>();

    final outputs = await api.outputs();
    expect(outputs, isNotEmpty);
    final out = outputs.first as Map;
    final video = (out['videos'] as List).first as Map;
    var progress = 0.0;
    final bytes = await api.downloadBytes(api.outputUri(out['folder'] as String, video['name'] as String),
        onProgress: (p) => progress = p);
    expect(bytes.length, video['size']);
    expect(progress, 1.0);

    await expectLater(api.startJob({'command': 'inconnue'}), throwsA(isA<ApiException>()));
    await expectLater(ApiClient(server, 'faux').status(),
        throwsA(isA<ApiException>().having((e) => e.message, 'message', 'Mot de passe incorrect')));
  }, skip: server == null ? 'LIVE_SERVER non défini' : false);
}
