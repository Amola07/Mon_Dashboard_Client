import 'dart:convert';

import 'package:anime_tiktok_studio/api.dart';
import 'package:anime_tiktok_studio/app_state.dart';
import 'package:anime_tiktok_studio/main.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

http.Response utf8Response(String body, int status) => http.Response.bytes(utf8.encode(body), status);

void main() {
  test('ApiClient envoie le mot de passe et décode le statut', () async {
    final client = MockClient((req) async {
      expect(req.headers['Authorization'], 'Bearer secret');
      expect(req.url.toString(), 'https://srv.example/api/status');
      return http.Response(jsonEncode({'episodes': 12, 'analyzed': 3}), 200);
    });
    final api = ApiClient('https://srv.example/', 'secret', client: client);
    final st = await api.status();
    expect(st['episodes'], 12);
  });

  test('ApiClient traduit les erreurs du serveur', () async {
    final client = MockClient((req) async => utf8Response(jsonEncode({'detail': 'Une tâche est déjà en cours'}), 409));
    final api = ApiClient('https://srv.example', 'secret', client: client);
    expect(
      () => api.startJob({'command': 'analyze'}),
      throwsA(isA<ApiException>().having((e) => e.message, 'message', 'Une tâche est déjà en cours')),
    );
    final unauthorized = ApiClient('https://srv.example', 'faux',
        client: MockClient((req) async => http.Response('{"detail":"x"}', 401)));
    expect(() => unauthorized.status(),
        throwsA(isA<ApiException>().having((e) => e.message, 'message', 'Mot de passe incorrect')));
  });

  test('discoverServerUrl lit la dernière adresse publiée sur ntfy', () async {
    final lines = [
      {'event': 'open'},
      {'event': 'message', 'title': 'anime-tiktok-url', 'message': jsonEncode({'url': 'https://old.trycloudflare.com'})},
      {'event': 'message', 'title': 'Rendu terminé', 'message': 'ok'},
      {'event': 'message', 'title': 'anime-tiktok-url', 'message': jsonEncode({'url': 'https://new.trycloudflare.com'})},
    ].map(jsonEncode).join('\n');
    final client = MockClient((req) async {
      expect(req.url.host, 'ntfy.sh');
      expect(req.url.path, '/mon-sujet/json');
      return utf8Response(lines, 200);
    });
    expect(await discoverServerUrl('mon-sujet', client: client), 'https://new.trycloudflare.com');
  });

  testWidgets('Sans connexion enregistrée, l\'app ouvre l\'écran de connexion', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final state = AppState();
    await state.load();
    await tester.pumpWidget(AnimeTikTokStudio(state: state));
    expect(find.text('Connexion au serveur'), findsOneWidget);
    expect(find.text('Se connecter'), findsOneWidget);
  });
}
