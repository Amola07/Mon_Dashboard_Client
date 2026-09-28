import 'package:flutter/material.dart';

import '../app_state.dart';
import '../ui.dart';
import 'connect_screen.dart';

/// Réglages du pipeline enregistrés sur le serveur, et connexion.
class SettingsTab extends StatefulWidget {
  const SettingsTab({super.key});

  @override
  State<SettingsTab> createState() => _SettingsTabState();
}

class _Field {
  const _Field(this.key, this.label, {this.help, this.number = true, this.decimal = false});
  final String key, label;
  final String? help;
  final bool number, decimal;
}

const _fields = [
  _Field('delivery.anime', 'Nom de l\'animé', help: 'Utilisé dans les légendes et hashtags', number: false),
  _Field('selection.clips_total', 'Nombre d\'extraits proposés'),
  _Field('selection.max_per_episode', 'Maximum par épisode'),
  _Field('selection.min_seconds', 'Durée min. d\'un extrait (s)', decimal: true),
  _Field('selection.max_seconds', 'Durée max. d\'un extrait (s)', decimal: true),
  _Field('analysis.skip_start', 'Ignorer le début de chaque épisode (s)', decimal: true),
  _Field('analysis.skip_end', 'Ignorer la fin de chaque épisode (s)', decimal: true),
];

const _resolutions = {
  '4K (2160×3840)': [2160, 3840],
  '1440p (1440×2560)': [1440, 2560],
  '1080p (1080×1920)': [1080, 1920],
};

class _SettingsTabState extends State<SettingsTab> {
  Map<String, dynamic>? _values;
  final Map<String, TextEditingController> _ctrls = {};
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _load());
  }

  @override
  void dispose() {
    for (final c in _ctrls.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    final api = AppScope.read(context).api;
    if (api == null) return;
    final values = await guard(context, api.settings);
    if (values == null || !mounted) return;
    setState(() {
      _values = values;
      for (final f in _fields) {
        _ctrls.putIfAbsent(f.key, TextEditingController.new).text = '${values[f.key] ?? ''}';
      }
    });
  }

  Future<void> _save() async {
    final state = AppScope.read(context);
    final out = <String, dynamic>{};
    for (final f in _fields) {
      final text = _ctrls[f.key]!.text.trim().replaceAll(',', '.');
      if (!f.number) {
        out[f.key] = text;
      } else {
        final v = f.decimal ? double.tryParse(text) : int.tryParse(text);
        if (v == null) {
          showMessage(context, 'Valeur invalide : ${f.label}', error: true);
          return;
        }
        out[f.key] = v;
      }
    }
    out['render.fps'] = _values!['render.fps'];
    out['render.width'] = _values!['render.width'];
    out['render.height'] = _values!['render.height'];
    setState(() => _saving = true);
    final saved = await guard(context, () => state.api!.saveSettings(out), success: 'Réglages enregistrés');
    if (!mounted) return;
    setState(() {
      _saving = false;
      if (saved != null) _values = saved;
    });
    state.refresh();
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final v = _values;
    final resKey = _resolutions.entries
        .firstWhere((e) => v != null && e.value[0] == v['render.width'] && e.value[1] == v['render.height'],
            orElse: () => const MapEntry('', []))
        .key;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Rendu', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        if (v == null)
          const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()))
        else ...[
          DropdownButtonFormField<String>(
            initialValue: resKey.isEmpty ? null : resKey,
            decoration: const InputDecoration(labelText: 'Résolution', border: OutlineInputBorder()),
            items: [for (final k in _resolutions.keys) DropdownMenuItem(value: k, child: Text(k))],
            onChanged: (k) => setState(() {
              v['render.width'] = _resolutions[k]![0];
              v['render.height'] = _resolutions[k]![1];
            }),
          ),
          const SizedBox(height: 12),
          SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 60, label: Text('60 fps')),
              ButtonSegment(value: 120, label: Text('120 fps')),
              ButtonSegment(value: 240, label: Text('240 fps')),
            ],
            selected: {(v['render.fps'] as num).toInt()},
            onSelectionChanged: (s) => setState(() => v['render.fps'] = s.first),
          ),
          const SizedBox(height: 20),
          Text('Sélection des extraits', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          for (final f in _fields)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: TextField(
                controller: _ctrls[f.key],
                keyboardType: f.number ? TextInputType.numberWithOptions(decimal: f.decimal) : TextInputType.text,
                decoration: InputDecoration(labelText: f.label, helperText: f.help, border: const OutlineInputBorder()),
              ),
            ),
          FilledButton.icon(
            onPressed: _saving ? null : _save,
            icon: const Icon(Icons.save),
            label: const Text('Enregistrer'),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
          ),
        ],
        const SizedBox(height: 28),
        Text('Connexion', style: Theme.of(context).textTheme.titleMedium),
        Card(
          child: ListTile(
            leading: const Icon(Icons.dns_outlined),
            title: Text(state.serverUrl, overflow: TextOverflow.ellipsis),
            subtitle: Text(state.ntfyTopic.isEmpty ? 'Adresse fixe' : 'Sujet ntfy : ${state.ntfyTopic}'),
            trailing: const Icon(Icons.edit),
            onTap: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => const ConnectScreen(canPop: true),
            )),
          ),
        ),
        const SizedBox(height: 12),
        Text(
          'Astuce : installez l\'application ntfy et abonnez-vous au même sujet pour être notifié '
          'quand un rendu est terminé, même application fermée.',
          style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant),
        ),
      ],
    );
  }
}
