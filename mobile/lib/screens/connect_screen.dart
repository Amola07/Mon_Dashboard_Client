import 'package:flutter/material.dart';

import '../api.dart';
import '../app_state.dart';
import '../ui.dart';

/// Connexion au serveur : sujet ntfy (adresse trouvée automatiquement) ou adresse saisie, + mot de passe.
class ConnectScreen extends StatefulWidget {
  const ConnectScreen({super.key, this.canPop = false});
  final bool canPop;

  @override
  State<ConnectScreen> createState() => _ConnectScreenState();
}

class _ConnectScreenState extends State<ConnectScreen> {
  late final TextEditingController _url, _token, _topic;
  bool _busy = false;
  bool _showToken = false;

  @override
  void initState() {
    super.initState();
    final s = AppScope.read(context);
    _url = TextEditingController(text: s.serverUrl);
    _token = TextEditingController(text: s.token);
    _topic = TextEditingController(text: s.ntfyTopic);
  }

  @override
  void dispose() {
    _url.dispose();
    _token.dispose();
    _topic.dispose();
    super.dispose();
  }

  Future<void> _discover() async {
    if (_topic.text.trim().isEmpty) {
      showMessage(context, 'Indiquez le sujet ntfy choisi dans le notebook', error: true);
      return;
    }
    setState(() => _busy = true);
    try {
      final url = await discoverServerUrl(_topic.text);
      if (!mounted) return;
      if (url == null) {
        showMessage(context, 'Aucune adresse publiée : le notebook est-il lancé ?', error: true);
      } else {
        _url.text = url;
        showMessage(context, 'Serveur trouvé');
      }
    } catch (e) {
      if (mounted) showMessage(context, 'Recherche impossible : $e', error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _connect() async {
    var url = _url.text.trim();
    if (url.isEmpty && _topic.text.trim().isNotEmpty) {
      await _discover();
      if (!mounted) return;
      url = _url.text.trim();
    }
    if (url.isEmpty || _token.text.trim().isEmpty) {
      showMessage(context, 'Adresse et mot de passe requis', error: true);
      return;
    }
    if (!url.startsWith('http')) url = 'https://$url';
    setState(() => _busy = true);
    try {
      final api = ApiClient(url, _token.text.trim());
      await api.ping();
      await api.status();
      if (!mounted) return;
      await AppScope.read(context).saveConnection(url: url, token: _token.text, topic: _topic.text);
      if (mounted && widget.canPop) Navigator.of(context).pop();
    } catch (e) {
      if (mounted) showMessage(context, e, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).colorScheme.onSurfaceVariant;
    return Scaffold(
      appBar: AppBar(title: const Text('Connexion au serveur')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Icon(Icons.movie_filter_rounded, size: 64, color: accent),
          const SizedBox(height: 12),
          Text('Anime TikTok Studio', textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(
            'Lancez la cellule « Télécommande » du notebook Kaggle ou Colab, puis entrez ici le même '
            'sujet ntfy et le même mot de passe.',
            textAlign: TextAlign.center,
            style: TextStyle(color: muted),
          ),
          const SizedBox(height: 24),
          TextField(
            controller: _topic,
            decoration: const InputDecoration(
              labelText: 'Sujet ntfy (recommandé)',
              helperText: 'Permet de retrouver le serveur à chaque nouvelle session',
              prefixIcon: Icon(Icons.satellite_alt_outlined),
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              onPressed: _busy ? null : _discover,
              icon: const Icon(Icons.search),
              label: const Text('Trouver l\'adresse'),
            ),
          ),
          TextField(
            controller: _url,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(
              labelText: 'Adresse du serveur',
              hintText: 'https://xxxx.trycloudflare.com',
              prefixIcon: Icon(Icons.link),
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _token,
            obscureText: !_showToken,
            decoration: InputDecoration(
              labelText: 'Mot de passe',
              prefixIcon: const Icon(Icons.key),
              border: const OutlineInputBorder(),
              suffixIcon: IconButton(
                icon: Icon(_showToken ? Icons.visibility_off : Icons.visibility),
                onPressed: () => setState(() => _showToken = !_showToken),
              ),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _busy ? null : _connect,
            icon: _busy
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.power_settings_new),
            label: const Text('Se connecter'),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
          ),
        ],
      ),
    );
  }
}
