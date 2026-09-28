import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api.dart';

/// État global : connexion au serveur et dernier statut connu (rafraîchi régulièrement).
class AppState extends ChangeNotifier {
  String serverUrl = '';
  String token = '';
  String ntfyTopic = '';
  ApiClient? api;

  Map<String, dynamic>? status;
  String? error;
  Timer? _timer;
  bool _polling = false;

  bool get configured => serverUrl.isNotEmpty && token.isNotEmpty;
  Map<String, dynamic>? get job => status?['job'] as Map<String, dynamic>?;
  bool get jobRunning => job?['status'] == 'running';

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    serverUrl = prefs.getString('serverUrl') ?? '';
    token = prefs.getString('token') ?? '';
    ntfyTopic = prefs.getString('ntfyTopic') ?? '';
    if (configured) api = ApiClient(serverUrl, token);
    notifyListeners();
  }

  Future<void> saveConnection({required String url, required String token, required String topic}) async {
    serverUrl = url.trim();
    this.token = token.trim();
    ntfyTopic = topic.trim();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('serverUrl', serverUrl);
    await prefs.setString('token', this.token);
    await prefs.setString('ntfyTopic', ntfyTopic);
    api = ApiClient(serverUrl, this.token);
    status = null;
    error = null;
    notifyListeners();
    await refresh();
  }

  /// Si le serveur a changé d'adresse (nouvelle session Kaggle/Colab), la retrouve via ntfy.
  Future<bool> rediscover() async {
    if (ntfyTopic.isEmpty) return false;
    final url = await discoverServerUrl(ntfyTopic);
    if (url == null || url == serverUrl) return false;
    await saveConnection(url: url, token: token, topic: ntfyTopic);
    return true;
  }

  Future<void> refresh() async {
    final client = api;
    if (client == null || _polling) return;
    _polling = true;
    try {
      status = await client.status();
      error = null;
    } on ApiException catch (e) {
      error = e.message;
      if (e.statusCode != 401 && ntfyTopic.isNotEmpty) {
        try {
          if (await rediscover()) return;
        } catch (_) {}
      }
    } catch (e) {
      error = '$e';
    } finally {
      _polling = false;
      notifyListeners();
      _schedule();
    }
  }

  void _schedule() {
    _timer?.cancel();
    _timer = Timer(Duration(seconds: jobRunning ? 2 : 10), refresh);
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}

/// Donne accès à [AppState] dans l'arbre de widgets.
class AppScope extends InheritedNotifier<AppState> {
  const AppScope({super.key, required AppState state, required super.child}) : super(notifier: state);

  static AppState of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AppScope>()!.notifier!;

  static AppState read(BuildContext context) =>
      context.getInheritedWidgetOfExactType<AppScope>()!.notifier!;
}
