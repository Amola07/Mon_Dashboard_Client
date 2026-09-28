import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Erreur renvoyée par le serveur (message en français, prêt à afficher).
class ApiException implements Exception {
  ApiException(this.message, [this.statusCode]);
  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

/// Client de l'API du serveur de contrôle (anime_tiktok/server.py).
class ApiClient {
  ApiClient(String baseUrl, this.token, {http.Client? client})
      : baseUrl = baseUrl.trim().replaceAll(RegExp(r'/+$'), ''),
        _http = client ?? http.Client();

  final String baseUrl;
  final String token;
  final http.Client _http;

  Map<String, String> get authHeaders => {'Authorization': 'Bearer $token'};

  Uri uri(String path, [Map<String, String>? query]) =>
      Uri.parse('$baseUrl$path').replace(queryParameters: query);

  Future<dynamic> _send(String method, String path, {Object? body, Duration? timeout}) async {
    final req = http.Request(method, uri(path))..headers.addAll(authHeaders);
    if (body != null) {
      req.headers['Content-Type'] = 'application/json';
      req.body = jsonEncode(body);
    }
    final http.Response res;
    try {
      res = await http.Response.fromStream(
          await _http.send(req).timeout(timeout ?? const Duration(seconds: 20)));
    } on TimeoutException {
      throw ApiException('Le serveur ne répond pas (délai dépassé)');
    } on SocketException {
      throw ApiException('Serveur injoignable : vérifiez l\'adresse et que le notebook tourne');
    } on http.ClientException catch (e) {
      throw ApiException('Connexion impossible : ${e.message}');
    }
    final text = utf8.decode(res.bodyBytes, allowMalformed: true);
    if (res.statusCode >= 400) {
      var message = 'Erreur ${res.statusCode}';
      try {
        final detail = jsonDecode(text)['detail'];
        if (detail is String) message = detail;
      } catch (_) {}
      if (res.statusCode == 401) message = 'Mot de passe incorrect';
      if (res.statusCode == 502 || res.statusCode == 530) {
        message = 'Le serveur est arrêté (session Kaggle/Colab terminée ?)';
      }
      throw ApiException(message, res.statusCode);
    }
    return text.isEmpty ? null : jsonDecode(text);
  }

  Future<Map<String, dynamic>> ping() async => Map<String, dynamic>.from(await _send('GET', '/api/ping'));
  Future<Map<String, dynamic>> status() async => Map<String, dynamic>.from(await _send('GET', '/api/status'));
  Future<Map<String, dynamic>> settings() async => Map<String, dynamic>.from(await _send('GET', '/api/settings'));
  Future<Map<String, dynamic>> saveSettings(Map<String, dynamic> values) async =>
      Map<String, dynamic>.from(await _send('PUT', '/api/settings', body: values));

  Future<List<dynamic>> episodes() async => List<dynamic>.from(await _send('GET', '/api/episodes'));
  Future<List<dynamic>> clips() async => List<dynamic>.from(await _send('GET', '/api/clips'));
  Future<List<dynamic>> outputs() async => List<dynamic>.from(await _send('GET', '/api/outputs'));
  Future<List<dynamic>> music() async => List<dynamic>.from(await _send('GET', '/api/music'));

  Future<Map<String, dynamic>> startJob(Map<String, dynamic> body) async =>
      Map<String, dynamic>.from(await _send('POST', '/api/jobs', body: body));
  Future<void> cancelJob() => _send('POST', '/api/jobs/cancel');
  Future<Map<String, dynamic>> currentJob() async =>
      Map<String, dynamic>.from(await _send('GET', '/api/jobs/current'));

  Future<int> setKeep(Map<String, bool> changes) async =>
      (await _send('PUT', '/api/clips/keep', body: {'keep': changes}))['kept'] as int;

  Future<void> deleteOutput(String folder) =>
      _send('DELETE', '/api/outputs/${Uri.encodeComponent(folder)}');

  String thumbUrl(String clipId) => uri('/api/clips/${Uri.encodeComponent(clipId)}/thumb').toString();
  Uri previewUri(String clipId) => uri('/api/clips/${Uri.encodeComponent(clipId)}/preview');
  Uri outputUri(String folder, String name) =>
      uri('/api/outputs/${Uri.encodeComponent(folder)}/${Uri.encodeComponent(name)}');

  /// Envoie un fichier (musique ou épisode) au serveur.
  Future<void> upload(String kind, String path) async {
    final req = http.MultipartRequest('POST', uri('/api/upload/$kind'))
      ..headers.addAll(authHeaders)
      ..files.add(await http.MultipartFile.fromPath('file', path));
    final res = await http.Response.fromStream(await _http.send(req));
    if (res.statusCode >= 400) {
      var message = 'Envoi impossible (${res.statusCode})';
      try {
        message = jsonDecode(utf8.decode(res.bodyBytes, allowMalformed: true))['detail'] as String;
      } catch (_) {}
      throw ApiException(message, res.statusCode);
    }
  }

  /// Télécharge un fichier en suivant la progression (0..1).
  Future<File> download(Uri source, File dest, {void Function(double)? onProgress}) async {
    final req = http.Request('GET', source)..headers.addAll(authHeaders);
    final res = await _http.send(req);
    if (res.statusCode >= 400) throw ApiException('Téléchargement impossible (${res.statusCode})');
    final total = res.contentLength ?? 0;
    var received = 0;
    final sink = dest.openWrite();
    try {
      await for (final chunk in res.stream) {
        sink.add(chunk);
        received += chunk.length;
        if (total > 0) onProgress?.call(received / total);
      }
    } finally {
      await sink.close();
    }
    return dest;
  }
}

/// Retrouve l'adresse publique du serveur publiée sur ntfy.sh au démarrage du notebook.
Future<String?> discoverServerUrl(String topic, {http.Client? client}) async {
  final c = client ?? http.Client();
  final url = Uri.parse('https://ntfy.sh/${Uri.encodeComponent(topic.trim())}/json')
      .replace(queryParameters: {'poll': '1', 'since': '24h'});
  final res = await c.get(url).timeout(const Duration(seconds: 15));
  if (res.statusCode != 200) return null;
  String? found;
  for (final line in const LineSplitter().convert(utf8.decode(res.bodyBytes, allowMalformed: true))) {
    if (line.trim().isEmpty) continue;
    try {
      final msg = jsonDecode(line) as Map<String, dynamic>;
      if (msg['event'] == 'message' && msg['title'] == 'anime-tiktok-url') {
        found = (jsonDecode(msg['message'] as String) as Map<String, dynamic>)['url'] as String?;
      }
    } catch (_) {}
  }
  return found;
}
