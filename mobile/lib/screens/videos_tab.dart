import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../app_state.dart';
import '../platform/video_store.dart';
import '../ui.dart';
import 'player_screen.dart';

/// Vidéos livrées : regarder, copier la légende, télécharger et partager vers TikTok.
class VideosTab extends StatefulWidget {
  const VideosTab({super.key});

  @override
  State<VideosTab> createState() => _VideosTabState();
}

class _VideosTabState extends State<VideosTab> {
  List<dynamic> _outputs = [];
  bool _loading = false;
  String? _signature;
  final Map<String, double> _downloads = {};
  final VideoStore _store = VideoStore();

  Future<void> _load() async {
    final api = AppScope.read(context).api;
    if (api == null) return;
    setState(() => _loading = true);
    try {
      final list = await api.outputs();
      if (mounted) setState(() => _outputs = list);
    } catch (e) {
      if (mounted) showMessage(context, e, error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final job = AppScope.of(context).job;
    final sig = '${job?['id']}:${job?['status']}';
    if (sig != _signature) {
      _signature = sig;
      _load();
    }
  }

  String _key(String folder, Map<String, dynamic> video) => '$folder/${video['name']}';

  /// Télécharge la vidéo (sur le téléphone, ou en mémoire pour la web app). Renvoie true si prête.
  Future<bool> _prepare(String folder, Map<String, dynamic> video) async {
    final api = AppScope.read(context).api!;
    final key = _key(folder, video);
    if (_store.isReady(key)) return true;
    setState(() => _downloads[key] = 0);
    try {
      await _store.prepare(
        api,
        api.outputUri(folder, video['name']),
        key,
        video['size'] as int,
        (p) => mounted ? setState(() => _downloads[key] = p) : null,
      );
      return true;
    } catch (e) {
      if (mounted) showMessage(context, e, error: true);
      return false;
    } finally {
      if (mounted) setState(() => _downloads.remove(key));
    }
  }

  Future<void> _share(String folder, Map<String, dynamic> video) async {
    final key = _key(folder, video);
    final caption = video['caption'] as String? ?? '';
    if (!_store.isReady(key)) {
      final ok = await _prepare(folder, video);
      if (!ok || !mounted) return;
      if (shareNeedsSecondTap) {
        // Safari exige un nouveau toucher pour ouvrir la feuille de partage.
        setState(() {});
        showMessage(context, 'Vidéo prête : touchez « Partager » pour l\'envoyer vers TikTok');
        return;
      }
    }
    // Presse-papiers et partage lancés dans le même toucher (exigence de Safari).
    if (caption.isNotEmpty) Clipboard.setData(ClipboardData(text: caption));
    try {
      await _store.share(key, video['name'], caption);
      if (mounted && caption.isNotEmpty) showMessage(context, 'Légende copiée : collez-la dans TikTok');
    } catch (e) {
      if (mounted) showMessage(context, 'Partage impossible : $e', error: true);
    }
  }

  Future<void> _delete(String folder) async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Supprimer ce lot ?'),
        content: const Text('Les vidéos seront effacées du serveur.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Supprimer')),
        ],
      ),
    );
    if (yes != true || !mounted) return;
    await guard(context, () => AppScope.read(context).api!.deleteOutput(folder), success: 'Supprimé');
    _load();
  }

  void _play(String folder, Map<String, dynamic> video) {
    final api = AppScope.read(context).api!;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PlayerScreen(
          title: video['name'],
          uri: api.outputUri(folder, video['name']),
          headers: api.authHeaders,
          actions: [IconButton(icon: const Icon(Icons.share), onPressed: () => _share(folder, video))],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_outputs.isEmpty) {
      return RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          children: [
            SizedBox(
              height: 500,
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : const EmptyState(
                      icon: Icons.video_library_outlined,
                      title: 'Pas encore de vidéos',
                      subtitle: 'Validez des extraits puis lancez « Générer les vidéos ».',
                    ),
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          for (final out in _outputs) ...[
            Padding(
              padding: const EdgeInsets.fromLTRB(4, 12, 0, 4),
              child: Row(
                children: [
                  Chip(label: Text(out['style']), visualDensity: VisualDensity.compact),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _date(out['created']),
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
                    ),
                  ),
                  IconButton(icon: const Icon(Icons.delete_outline), onPressed: () => _delete(out['folder'])),
                ],
              ),
            ),
            for (final v in out['videos']) _videoTile(out['folder'], Map<String, dynamic>.from(v)),
          ],
        ],
      ),
    );
  }

  Widget _videoTile(String folder, Map<String, dynamic> v) {
    final progress = _downloads['$folder/${v['name']}'];
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(4, 4, 4, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ListTile(
              leading: const CircleAvatar(
                backgroundColor: accent,
                foregroundColor: Colors.white,
                child: Icon(Icons.play_arrow),
              ),
              title: Text(v['name'], overflow: TextOverflow.ellipsis),
              subtitle: Text(fmtSize(v['size'])),
              onTap: () => _play(folder, v),
            ),
            if ((v['caption'] as String).isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  v['caption'],
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant),
                ),
              ),
            if (progress != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: LinearProgressIndicator(value: progress > 0 ? progress : null),
              ),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton.icon(
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(text: v['caption'] ?? ''));
                    if (mounted) showMessage(context, 'Légende copiée');
                  },
                  icon: const Icon(Icons.copy, size: 18),
                  label: const Text('Légende'),
                ),
                if (kIsWeb)
                  IconButton(
                    tooltip: 'Ouvrir dans Safari',
                    onPressed: () => openInBrowser(AppScope.read(context).api!.outputUri(folder, v['name'])),
                    icon: const Icon(Icons.open_in_new, size: 20),
                  ),
                FilledButton.tonalIcon(
                  onPressed: progress != null ? null : () => _share(folder, v),
                  icon: Icon(
                    shareNeedsSecondTap && !_store.isReady(_key(folder, v)) ? Icons.download : Icons.ios_share,
                    size: 18,
                  ),
                  label: Text(shareNeedsSecondTap && !_store.isReady(_key(folder, v)) ? 'Préparer' : 'Partager'),
                ),
                const SizedBox(width: 8),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _date(num seconds) {
    final d = DateTime.fromMillisecondsSinceEpoch((seconds * 1000).round());
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(d.day)}/${two(d.month)} à ${two(d.hour)}:${two(d.minute)}';
  }
}
