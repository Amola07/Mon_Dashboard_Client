import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../app_state.dart';
import '../ui.dart';
import '../upload.dart';
import 'make_sheet.dart';

/// Accueil : état du serveur, tâche en cours, et les 3 grandes actions du pipeline.
class DashboardTab extends StatefulWidget {
  const DashboardTab({super.key, required this.onOpenTab});
  final void Function(int) onOpenTab;

  @override
  State<DashboardTab> createState() => _DashboardTabState();
}

class _DashboardTabState extends State<DashboardTab> {
  bool _showLog = false;
  List<String> _log = [];
  List<dynamic> _episodes = [];
  String? _lastJobState;

  Future<void> _loadDetails() async {
    final api = AppScope.read(context).api;
    if (api == null) return;
    try {
      final eps = await api.episodes();
      final job = _showLog ? await api.currentJob() : null;
      if (!mounted) return;
      setState(() {
        _episodes = eps;
        if (job != null) _log = List<String>.from(job['log'] ?? []);
      });
    } catch (_) {}
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final job = AppScope.of(context).job;
    // Journal ouvert : on le recharge à chaque nouvelle étape de la tâche.
    final Object? step = _showLog && job != null ? job['step'] : null;
    final key = '${job?['id']}:${job?['status']}:$step';
    if (key != _lastJobState) {
      _lastJobState = key;
      _loadDetails();
    }
  }

  Future<void> _start(String command, {Map<String, dynamic> extra = const {}}) async {
    final state = AppScope.read(context);
    await guard(
      context,
      () => state.api!.startJob({'command': command, ...extra}),
      success: '${jobLabels[command]} lancée',
    );
    await state.refresh();
  }

  Future<void> _chooseSelection() async {
    final mode = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.local_fire_department_outlined),
              title: const Text('Moments forts'),
              subtitle: const Text('Combats, cris, action : extraits de 12 à 45 s (styles brut, hype)'),
              onTap: () => Navigator.pop(ctx, 'action'),
            ),
            ListTile(
              leading: const Icon(Icons.landscape_outlined),
              title: const Text('Beaux plans'),
              subtitle: const Text('Plans calmes, colorés et nets de quelques secondes (style aesthetic)'),
              onTap: () => Navigator.pop(ctx, 'aesthetic'),
            ),
          ],
        ),
      ),
    );
    if (mode != null && mounted) await _start('select', extra: {'mode': mode});
  }

  Future<void> _addEpisode() async {
    final choice = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.link),
              title: const Text('Depuis un lien direct'),
              subtitle: const Text('Le serveur télécharge lui-même (rapide)'),
              onTap: () => Navigator.pop(ctx, 'url'),
            ),
            ListTile(
              leading: const Icon(Icons.phone_android),
              title: const Text('Depuis le téléphone'),
              subtitle: const Text('Envoi par votre connexion (lent pour de gros fichiers)'),
              onTap: () => Navigator.pop(ctx, 'file'),
            ),
          ],
        ),
      ),
    );
    if (!mounted || choice == null) return;
    final api = AppScope.read(context).api!;
    if (choice == 'url') {
      final ctrl = TextEditingController();
      final url = await showDialog<String>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Lien de l\'épisode'),
          content: TextField(
            controller: ctrl,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(hintText: 'https://…/episode_01.mkv'),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () => Navigator.pop(ctx, ctrl.text.trim()), child: const Text('Télécharger')),
          ],
        ),
      );
      if (url != null && url.isNotEmpty) await _start('download', extra: {'url': url});
    } else {
      await pickAndUpload(context, api, 'episodes', FileType.video);
      if (mounted) _loadDetails();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final st = state.status;
    final job = state.job;
    final running = state.jobRunning;

    return RefreshIndicator(
      onRefresh: () async {
        await state.refresh();
        await _loadDetails();
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              const Icon(Icons.movie_filter_rounded, color: accent),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  st?['anime']?.toString().isNotEmpty == true ? st!['anime'] : 'Anime TikTok Studio',
                  style: Theme.of(context).textTheme.titleLarge,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              _ConnectionDot(ok: state.error == null && st != null),
            ],
          ),
          if (state.error != null) ...[
            const SizedBox(height: 12),
            Card(
              color: Colors.red.shade900.withValues(alpha: 0.4),
              child: ListTile(
                leading: const Icon(Icons.cloud_off),
                title: Text(state.error!),
                subtitle: const Text('Relancez la cellule « Télécommande » du notebook si la session est terminée.'),
              ),
            ),
          ],
          const SizedBox(height: 16),
          if (st != null)
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _Stat(label: 'Épisodes prêts', value: '${st['analyzed']}/${st['episodes']}'),
                  const SizedBox(width: 8),
                  _Stat(label: 'Extraits retenus', value: '${st['kept']}/${st['clips']}'),
                  const SizedBox(width: 8),
                  _Stat(
                    label: 'Sortie',
                    value:
                        '${st['render']['height'] >= 3840 ? '4K' : '${st['render']['height']}p'} ${st['render']['fps']}',
                  ),
                ],
              ),
            ),
          const SizedBox(height: 16),
          if (job != null)
            _JobCard(
              job: job,
              showLog: _showLog,
              log: _log,
              onToggleLog: () {
                setState(() => _showLog = !_showLog);
                _loadDetails();
              },
              onCancel: () => guard(context, () => state.api!.cancelJob(), success: 'Annulation demandée'),
            ),
          const SizedBox(height: 16),
          _ActionTile(
            step: 1,
            icon: Icons.analytics_outlined,
            title: 'Analyser les épisodes',
            subtitle: 'Plans, son, mouvement ; génériques ignorés',
            enabled: !running && (st?['episodes'] ?? 0) > 0,
            onTap: () => _start('analyze'),
          ),
          _ActionTile(
            step: 2,
            icon: Icons.auto_awesome_motion_outlined,
            title: 'Proposer les extraits',
            subtitle: 'Les meilleurs moments, à valider ensuite',
            enabled: !running && (st?['analyzed'] ?? 0) > 0,
            onTap: _chooseSelection,
            trailing: (st?['clips'] ?? 0) > 0
                ? TextButton(onPressed: () => widget.onOpenTab(1), child: const Text('Voir'))
                : null,
          ),
          _ActionTile(
            step: 3,
            icon: Icons.movie_creation_outlined,
            title: 'Générer les vidéos',
            subtitle: 'Style du jour, 4K, 120/240 fps',
            enabled: !running && (st?['kept'] ?? 0) > 0,
            onTap: () => showMakeSheet(context),
            trailing: TextButton(onPressed: () => widget.onOpenTab(3), child: const Text('Vidéos')),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Text('Épisodes', style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              TextButton.icon(
                onPressed: running ? null : _addEpisode,
                icon: const Icon(Icons.add),
                label: const Text('Ajouter'),
              ),
            ],
          ),
          if (_episodes.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Text('Aucun épisode sur le serveur pour l\'instant.'),
            ),
          for (final e in _episodes)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Icon(
                e['analyzed'] == true ? Icons.check_circle : Icons.radio_button_unchecked,
                color: e['analyzed'] == true ? accent2 : null,
              ),
              title: Text(e['name'], overflow: TextOverflow.ellipsis),
              subtitle: Text(
                [
                  fmtSize(e['size']),
                  if (e['duration'] != null) fmtTime(e['duration']),
                  if ((e['excluded'] as List).isNotEmpty)
                    'ignoré : ${(e['excluded'] as List).map((r) => '${fmtTime(r[0])}–${fmtTime(r[1])}').join(', ')}',
                ].join(' · '),
              ),
            ),
        ],
      ),
    );
  }
}

class _ConnectionDot extends StatelessWidget {
  const _ConnectionDot({required this.ok});
  final bool ok;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(shape: BoxShape.circle, color: ok ? Colors.greenAccent : Colors.redAccent),
      ),
      const SizedBox(width: 6),
      Text(ok ? 'Connecté' : 'Hors ligne', style: const TextStyle(fontSize: 12)),
    ],
  );
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});
  final String label, value;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(value, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurfaceVariant)),
          ],
        ),
      ),
    ),
  );
}

class _JobCard extends StatelessWidget {
  const _JobCard({
    required this.job,
    required this.showLog,
    required this.log,
    required this.onToggleLog,
    required this.onCancel,
  });
  final Map<String, dynamic> job;
  final bool showLog;
  final List<String> log;
  final VoidCallback onToggleLog, onCancel;

  @override
  Widget build(BuildContext context) {
    final status = job['status'] as String;
    final progress = (job['progress'] as num?)?.toDouble();
    final running = status == 'running';
    final color = switch (status) {
      'done' => Colors.greenAccent,
      'failed' => Colors.redAccent,
      'cancelled' => Colors.orangeAccent,
      _ => accent2,
    };
    final started = DateTime.fromMillisecondsSinceEpoch(((job['started'] as num) * 1000).round());
    final end = job['ended'] != null
        ? DateTime.fromMillisecondsSinceEpoch(((job['ended'] as num) * 1000).round())
        : DateTime.now();
    final minutes = end.difference(started).inMinutes;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    jobLabels[job['command']] ?? job['command'],
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                ),
                Text('${statusLabels[status] ?? status} · $minutes min', style: TextStyle(color: color, fontSize: 12)),
              ],
            ),
            const SizedBox(height: 10),
            LinearProgressIndicator(
              value: running ? progress : 1,
              color: color,
              minHeight: 6,
              borderRadius: BorderRadius.circular(3),
            ),
            const SizedBox(height: 8),
            Text(
              job['step'] ?? '',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
            Row(
              children: [
                TextButton.icon(
                  onPressed: onToggleLog,
                  icon: Icon(showLog ? Icons.expand_less : Icons.terminal),
                  label: Text(showLog ? 'Masquer le journal' : 'Journal'),
                ),
                const Spacer(),
                if (running)
                  TextButton.icon(onPressed: onCancel, icon: const Icon(Icons.stop), label: const Text('Arrêter')),
              ],
            ),
            if (showLog)
              Container(
                width: double.infinity,
                constraints: const BoxConstraints(maxHeight: 260),
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(8)),
                child: SingleChildScrollView(
                  reverse: true,
                  child: Text(log.join('\n'), style: const TextStyle(fontFamily: 'monospace', fontSize: 11)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.step,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.enabled,
    required this.onTap,
    this.trailing,
  });
  final int step;
  final IconData icon;
  final String title, subtitle;
  final bool enabled;
  final VoidCallback onTap;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Card(
        child: ListTile(
          enabled: enabled,
          onTap: enabled ? onTap : null,
          leading: CircleAvatar(
            backgroundColor: enabled ? accent : Colors.white12,
            foregroundColor: Colors.white,
            child: Icon(icon, size: 20),
          ),
          title: Text('$step. $title'),
          subtitle: Text(subtitle),
          trailing: trailing ?? const Icon(Icons.chevron_right),
        ),
      ),
    );
  }
}
