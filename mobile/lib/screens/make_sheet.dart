import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../app_state.dart';
import '../ui.dart';

const _styleInfo = {
  'brut': ('Brut', 'Une vidéo par extrait, moment fort en accroche'),
  'hype': ('Hype', 'Edit rythmé sur une musique, zooms et flashs'),
  'cinematique': ('Cinématique', 'Image entière sur fond flou, fondus'),
};

/// Choix du style du jour, du fps et de la musique, puis lancement du rendu + montage.
Future<void> showMakeSheet(BuildContext context) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => AppScope(state: AppScope.read(context), child: const _MakeSheet()),
  );
}

class _MakeSheet extends StatefulWidget {
  const _MakeSheet();

  @override
  State<_MakeSheet> createState() => _MakeSheetState();
}

class _MakeSheetState extends State<_MakeSheet> {
  String _style = 'brut';
  int _fps = 120;
  String? _music;
  List<String> _tracks = [];
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    final s = AppScope.read(context);
    _fps = (s.status?['render']?['fps'] as num?)?.toInt() ?? 120;
    _loadMusic();
  }

  Future<void> _loadMusic() async {
    final api = AppScope.read(context).api;
    if (api == null) return;
    try {
      final list = await api.music();
      if (mounted) setState(() => _tracks = [for (final m in list) m['name'] as String]);
    } catch (_) {}
  }

  Future<void> _uploadMusic() async {
    final files = await FilePicker.pickFiles(type: FileType.audio);
    if (files.isEmpty || files.first.path == null || !mounted) return;
    final api = AppScope.read(context).api!;
    setState(() => _busy = true);
    await guard(context, () => api.upload('music', files.first.path!), success: 'Musique envoyée');
    await _loadMusic();
    if (mounted) {
      setState(() {
        _busy = false;
        _music = files.first.name;
      });
    }
  }

  Future<void> _start() async {
    final state = AppScope.read(context);
    setState(() => _busy = true);
    final ok = await guard(context, () async {
      final current = (state.status?['render']?['fps'] as num?)?.toInt();
      if (current != _fps) await state.api!.saveSettings({'render.fps': _fps});
      return state.api!.startJob({'command': 'make', 'style': _style, if (_music != null) 'music': _music});
    }, success: 'Rendu lancé');
    await state.refresh();
    if (!mounted) return;
    setState(() => _busy = false);
    if (ok != null) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final styles = List<String>.from(state.status?['styles'] ?? _styleInfo.keys);
    final kept = state.status?['kept'] ?? 0;
    final render = state.status?['render'];
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 0, 20, 20 + MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
          Text('Générer les vidéos', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          Text('$kept extrait(s) retenu(s) · ${render?['width']}×${render?['height']}',
              style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
          const SizedBox(height: 16),
          const Text('Style du jour'),
          const SizedBox(height: 8),
          for (final s in styles)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _StyleTile(
                name: _styleInfo[s]?.$1 ?? s,
                description: _styleInfo[s]?.$2 ?? 'Style personnalisé (config.yaml)',
                selected: _style == s,
                onTap: () => setState(() => _style = s),
              ),
            ),
          const SizedBox(height: 8),
          const Text('Images par seconde'),
          const SizedBox(height: 8),
          SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 60, label: Text('60')),
              ButtonSegment(value: 120, label: Text('120')),
              ButtonSegment(value: 240, label: Text('240')),
            ],
            selected: {_fps},
            onSelectionChanged: (v) => setState(() => _fps = v.first),
          ),
          const SizedBox(height: 16),
          Row(children: [
            const Expanded(child: Text('Musique')),
            TextButton.icon(onPressed: _busy ? null : _uploadMusic, icon: const Icon(Icons.upload), label: const Text('Envoyer')),
          ]),
          DropdownButtonFormField<String?>(
            initialValue: _tracks.contains(_music) ? _music : null,
            isExpanded: true,
            decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
            items: [
              const DropdownMenuItem(value: null, child: Text('Au hasard parmi les musiques du serveur')),
              for (final t in _tracks) DropdownMenuItem(value: t, child: Text(t, overflow: TextOverflow.ellipsis)),
            ],
            onChanged: (v) => setState(() => _music = v),
          ),
          const SizedBox(height: 4),
          Text('Utilisée par les styles rythmés (hype).',
              style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: _busy || kept == 0 || state.jobRunning ? null : _start,
            icon: const Icon(Icons.auto_awesome),
            label: Text(state.jobRunning ? 'Une tâche est déjà en cours' : 'Lancer le rendu'),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
          ),
        ]),
      ),
    );
  }
}

class _StyleTile extends StatelessWidget {
  const _StyleTile({required this.name, required this.description, required this.selected, required this.onTap});
  final String name, description;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? accent.withValues(alpha: 0.15) : const Color(0xFF1A1A1A),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: selected ? accent : Colors.transparent),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(children: [
            Icon(selected ? Icons.radio_button_checked : Icons.radio_button_off, color: selected ? accent : null),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(name, style: const TextStyle(fontWeight: FontWeight.w600)),
                Text(description, style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}
