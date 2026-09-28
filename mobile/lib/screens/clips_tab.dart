import 'package:flutter/material.dart';

import '../app_state.dart';
import '../ui.dart';
import 'make_sheet.dart';
import 'player_screen.dart';

/// Validation des extraits proposés : aperçu vidéo, garder / écarter, puis générer.
class ClipsTab extends StatefulWidget {
  const ClipsTab({super.key});

  @override
  State<ClipsTab> createState() => _ClipsTabState();
}

class _ClipsTabState extends State<ClipsTab> {
  List<Map<String, dynamic>> _clips = [];
  bool _loading = false;
  String? _signature;

  Future<void> _load() async {
    final api = AppScope.read(context).api;
    if (api == null) return;
    setState(() => _loading = true);
    try {
      final list = await api.clips();
      if (mounted) setState(() => _clips = [for (final c in list) Map<String, dynamic>.from(c)]);
    } catch (e) {
      if (mounted) showMessage(context, e, error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Recharge quand la sélection change côté serveur (nouvelle tâche « select » terminée).
    final st = AppScope.of(context).status;
    final job = st?['job'];
    final sig = '${st?['clips']}:${job?['command']}:${job?['status']}';
    if (sig != _signature) {
      _signature = sig;
      _load();
    }
  }

  Future<void> _toggle(Map<String, dynamic> clip, bool keep) async {
    final state = AppScope.read(context);
    setState(() => clip['keep'] = keep);
    final ok = await guard(context, () => state.api!.setKeep({clip['id'] as String: keep}));
    if (ok == null && mounted) setState(() => clip['keep'] = !keep);
    state.refresh();
  }

  Future<void> _setAll(bool keep) async {
    final state = AppScope.read(context);
    await guard(context, () => state.api!.setKeep({for (final c in _clips) c['id'] as String: keep}));
    await _load();
    state.refresh();
  }

  void _preview(Map<String, dynamic> clip) {
    final state = AppScope.read(context);
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => PlayerScreen(
        title: 'Épisode ${clip['episode']} · ${fmtTime(clip['start'])}',
        uri: state.api!.previewUri(clip['id']),
        headers: state.api!.authHeaders,
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final kept = _clips.where((c) => c['keep'] == true).length;
    if (_clips.isEmpty) {
      return RefreshIndicator(
        onRefresh: _load,
        child: ListView(children: [
          SizedBox(
            height: 500,
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : const EmptyState(
                    icon: Icons.auto_awesome_motion_outlined,
                    title: 'Aucun extrait proposé',
                    subtitle: 'Depuis l\'accueil : analysez les épisodes puis lancez « Proposer les extraits ».',
                  ),
          ),
        ]),
      );
    }
    return Column(children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 8, 4),
        child: Row(children: [
          Expanded(child: Text('$kept / ${_clips.length} retenus', style: Theme.of(context).textTheme.titleMedium)),
          PopupMenuButton<bool>(
            icon: const Icon(Icons.checklist),
            onSelected: _setAll,
            itemBuilder: (_) => const [
              PopupMenuItem(value: true, child: Text('Tout garder')),
              PopupMenuItem(value: false, child: Text('Tout écarter')),
            ],
          ),
        ]),
      ),
      Expanded(
        child: RefreshIndicator(
          onRefresh: _load,
          child: GridView.builder(
            padding: const EdgeInsets.fromLTRB(12, 4, 12, 90),
            gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
              maxCrossAxisExtent: 260,
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              childAspectRatio: 0.92,
            ),
            itemCount: _clips.length,
            itemBuilder: (_, i) => _ClipCard(
              clip: _clips[i],
              thumbUrl: state.api!.thumbUrl(_clips[i]['id']),
              headers: state.api!.authHeaders,
              onToggle: (v) => _toggle(_clips[i], v),
              onPreview: () => _preview(_clips[i]),
            ),
          ),
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
        child: FilledButton.icon(
          onPressed: kept == 0 || state.jobRunning ? null : () => showMakeSheet(context),
          icon: const Icon(Icons.movie_creation_outlined),
          label: Text('Générer $kept vidéo(s)'),
          style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(50)),
        ),
      ),
    ]);
  }
}

class _ClipCard extends StatelessWidget {
  const _ClipCard({
    required this.clip,
    required this.thumbUrl,
    required this.headers,
    required this.onToggle,
    required this.onPreview,
  });
  final Map<String, dynamic> clip;
  final String thumbUrl;
  final Map<String, String> headers;
  final ValueChanged<bool> onToggle;
  final VoidCallback onPreview;

  @override
  Widget build(BuildContext context) {
    final keep = clip['keep'] == true;
    return Opacity(
      opacity: keep ? 1 : 0.45,
      child: Card(
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: keep ? accent : Colors.transparent, width: 1.5),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          AspectRatio(
            aspectRatio: 16 / 9,
            child: InkWell(
              onTap: onPreview,
              child: Stack(fit: StackFit.expand, children: [
                Image.network(thumbUrl, headers: headers, fit: BoxFit.cover,
                    errorBuilder: (_, _, _) => Container(color: Colors.black26, child: const Icon(Icons.image_not_supported))),
                const Center(child: Icon(Icons.play_circle_fill, size: 40, color: Colors.white70)),
                Positioned(
                  right: 6,
                  bottom: 6,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(color: Colors.black87, borderRadius: BorderRadius.circular(4)),
                    child: Text('${(clip['duration'] as num).round()} s', style: const TextStyle(fontSize: 11)),
                  ),
                ),
              ]),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(10, 8, 4, 0),
            child: Row(children: [
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Épisode ${clip['episode']}', style: const TextStyle(fontWeight: FontWeight.w600)),
                  Text('${fmtTime(clip['start'])} → ${fmtTime(clip['end'])}',
                      style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
                  Text('score ${(clip['score'] as num).toStringAsFixed(2)}',
                      style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurfaceVariant)),
                ]),
              ),
              Switch(value: keep, onChanged: onToggle),
            ]),
          ),
        ]),
      ),
    );
  }
}
