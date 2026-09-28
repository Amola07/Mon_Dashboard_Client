import 'package:flutter/material.dart';

import '../app_state.dart';
import '../ui.dart';
import 'player_screen.dart';

const emotionTags = ['enigme', 'tendu', 'déterminé', 'anxieux', 'inquiet', 'triste', 'posé', 'enthousiasme', 'épique'];

const _emotionColors = {
  'enigme': Colors.deepPurpleAccent,
  'mystere': Colors.deepPurpleAccent,
  'tendu': Colors.redAccent,
  'anxieux': Colors.orangeAccent,
  'inquiet': Colors.amber,
  'triste': Colors.blueGrey,
  'determine': Colors.lightBlueAccent,
  'pose': Colors.tealAccent,
  'calme': Colors.tealAccent,
  'enthousiasme': Colors.pinkAccent,
  'joyeux': Colors.pinkAccent,
  'epique': Colors.deepOrangeAccent,
};

/// Présentations d'animés narrées : liste, création (script) et validation des plans.
class PresentationsTab extends StatefulWidget {
  const PresentationsTab({super.key});

  @override
  State<PresentationsTab> createState() => _PresentationsTabState();
}

class _PresentationsTabState extends State<PresentationsTab> {
  List<dynamic> _items = [];
  bool _loading = false;
  String? _signature;

  Future<void> _load() async {
    final api = AppScope.read(context).api;
    if (api == null) return;
    setState(() => _loading = true);
    try {
      final list = await api.presentations();
      if (mounted) setState(() => _items = list);
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

  void _open(String name) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AppScope(
          state: AppScope.read(context),
          child: PlanScreen(name: name),
        ),
      ),
    );
  }

  Future<void> _create() async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => AppScope(state: AppScope.read(context), child: const ScriptEditor()),
      ),
    );
    if (created == true) _load();
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final job = state.job;
    final preparing = state.jobRunning && job?['command'] == 'present-plan';
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton.extended(
        onPressed: state.jobRunning ? null : _create,
        icon: const Icon(Icons.edit_note),
        label: const Text('Nouveau script'),
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
          children: [
            Text('Présentations narrées', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              'Écrivez un script : la voix off est générée et les plans des épisodes sont choisis pour '
              'illustrer chaque phrase. Vous validez les plans, puis la vidéo est montée.',
              style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 16),
            if (preparing)
              Card(
                child: ListTile(
                  leading: const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2)),
                  title: const Text('Préparation en cours…'),
                  subtitle: Text(job?['step'] ?? '', maxLines: 2, overflow: TextOverflow.ellipsis),
                ),
              ),
            if (_items.isEmpty && !_loading && !preparing)
              const Padding(
                padding: EdgeInsets.only(top: 60),
                child: EmptyState(
                  icon: Icons.record_voice_over_outlined,
                  title: 'Aucune présentation',
                  subtitle: 'Touchez « Nouveau script » pour commencer.',
                ),
              ),
            for (final p in _items)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Card(
                  child: ListTile(
                    leading: const CircleAvatar(
                      backgroundColor: accent,
                      foregroundColor: Colors.white,
                      child: Icon(Icons.movie_filter),
                    ),
                    title: Text((p['title'] as String?)?.isNotEmpty == true ? p['title'] : p['name']),
                    subtitle: Text(
                      '${fmtTime(p['duration'] ?? 0)} · ${p['sentences']} phrases · ${p['slots']} plans · voix ${p['voice']}',
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _open(p['name']),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// Saisie du script, avec insertion rapide des émotions.
class ScriptEditor extends StatefulWidget {
  const ScriptEditor({super.key});

  @override
  State<ScriptEditor> createState() => _ScriptEditorState();
}

class _ScriptEditorState extends State<ScriptEditor> {
  final _name = TextEditingController();
  final _script = TextEditingController();
  List<String> _tracks = [];
  String? _music;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _script.addListener(() => setState(() {}));
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      try {
        final list = await AppScope.read(context).api!.music();
        if (mounted) setState(() => _tracks = [for (final m in list) m['name'] as String]);
      } catch (_) {}
    });
  }

  @override
  void dispose() {
    _name.dispose();
    _script.dispose();
    super.dispose();
  }

  void _insert(String text) {
    final sel = _script.selection;
    final value = _script.text;
    final at = sel.isValid ? sel.start : value.length;
    final prefix = at > 0 && !value.substring(0, at).endsWith('\n') && !value.substring(0, at).endsWith(' ') ? ' ' : '';
    final insert = '$prefix$text ';
    _script.value = TextEditingValue(
      text: value.replaceRange(at, sel.isValid ? sel.end : at, insert),
      selection: TextSelection.collapsed(offset: at + insert.length),
    );
  }

  int get _seconds {
    final words = RegExp(r"[A-Za-zÀ-ÿ0-9']+")
        .allMatches(_script.text.replaceAll(RegExp(r'\[[^\]]*\]|\{[^}]*\}'), ''))
        .length;
    return (words / 2.6).round();
  }

  Future<void> _submit() async {
    if (_script.text.trim().isEmpty) {
      showMessage(context, 'Écrivez d\'abord le script', error: true);
      return;
    }
    final state = AppScope.read(context);
    setState(() => _busy = true);
    final res = await guard(
      context,
      () => state.api!.createPresentation(_script.text, name: _name.text.trim(), music: _music),
      success: 'Préparation lancée : voix off puis choix des plans',
    );
    await state.refresh();
    if (!mounted) return;
    setState(() => _busy = false);
    if (res != null) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).colorScheme.onSurfaceVariant;
    final secs = _seconds;
    return Scaffold(
      appBar: AppBar(title: const Text('Nouveau script')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _name,
            decoration: const InputDecoration(
              labelText: 'Nom (facultatif)',
              hintText: 'ex. Erased',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Text('Émotions (touchez pour insérer)', style: TextStyle(color: muted, fontSize: 12)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final tag in emotionTags) ActionChip(label: Text(tag), onPressed: () => _insert('[$tag]')),
              ActionChip(
                avatar: const Icon(Icons.image_search, size: 16),
                label: const Text('{visuel: …}'),
                onPressed: () => _insert('{visuel: }'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _script,
            minLines: 12,
            maxLines: null,
            keyboardType: TextInputType.multiline,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              alignLabelWithHint: true,
              labelText: 'Script',
              hintText: '[enigme] Il le ramène 18 ans plus tôt…\n[tendu] Cette fois…\n[posé] Cet anime, c\'est Erased.',
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '≈ ${fmtTime(secs)} une fois lu${secs < 60 ? ' · visez plus d\'une minute pour la rémunération TikTok' : ''}',
            style: TextStyle(fontSize: 12, color: secs < 60 ? Colors.amber : muted),
          ),
          const SizedBox(height: 4),
          Text(
            '« Cet anime, c\'est … » affiche le titre en grand. {visuel: neige, salle de classe} précise les plans voulus.',
            style: TextStyle(fontSize: 12, color: muted),
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String?>(
            initialValue: _music,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Musique de fond', border: OutlineInputBorder()),
            items: [
              const DropdownMenuItem(value: null, child: Text('Aucune')),
              for (final t in _tracks)
                DropdownMenuItem(
                  value: t,
                  child: Text(t, overflow: TextOverflow.ellipsis),
                ),
            ],
            onChanged: (v) => setState(() => _music = v),
          ),
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: _busy ? null : _submit,
            icon: const Icon(Icons.record_voice_over),
            label: const Text('Préparer : voix off + plans'),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
          ),
        ],
      ),
    );
  }
}

/// Validation des plans : pour chaque phrase, les plans proposés ; on touche pour changer.
class PlanScreen extends StatefulWidget {
  const PlanScreen({super.key, required this.name});
  final String name;

  @override
  State<PlanScreen> createState() => _PlanScreenState();
}

class _PlanScreenState extends State<PlanScreen> {
  Map<String, dynamic>? _plan;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _load());
  }

  Future<void> _load() async {
    final plan = await guard(context, () => AppScope.read(context).api!.presentation(widget.name));
    if (plan != null && mounted) setState(() => _plan = plan);
  }

  Future<void> _choose(int slot, int choice) async {
    final api = AppScope.read(context).api!;
    final previous = _plan!['slots'][slot]['choice'];
    setState(() => _plan!['slots'][slot]['choice'] = choice);
    final ok = await guard(context, () async {
      await api.chooseShot(widget.name, slot, choice);
      return true;
    });
    if (ok == null && mounted) setState(() => _plan!['slots'][slot]['choice'] = previous);
  }

  Future<void> _render() async {
    final state = AppScope.read(context);
    final ok = await guard(
      context,
      () => state.api!.renderPresentation(widget.name),
      success: 'Rendu lancé : la vidéo arrivera dans l\'onglet Vidéos',
    );
    await state.refresh();
    if (ok != null && mounted) Navigator.of(context).pop();
  }

  Future<void> _delete() async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Supprimer cette présentation ?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Supprimer')),
        ],
      ),
    );
    if (yes != true || !mounted) return;
    final ok = await guard(context, () async {
      await AppScope.read(context).api!.deletePresentation(widget.name);
      return true;
    });
    if (ok != null && mounted) Navigator.of(context).pop();
  }

  void _listen() {
    final api = AppScope.read(context).api!;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) =>
            PlayerScreen(title: 'Voix off', uri: api.presentationVoiceUri(widget.name), headers: api.authHeaders),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final plan = _plan;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          plan == null ? widget.name : ((plan['title'] as String?)?.isNotEmpty == true ? plan['title'] : widget.name),
        ),
        actions: [
          IconButton(tooltip: 'Écouter la voix', icon: const Icon(Icons.headphones), onPressed: _listen),
          IconButton(tooltip: 'Supprimer', icon: const Icon(Icons.delete_outline), onPressed: _delete),
        ],
      ),
      bottomNavigationBar: plan == null
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
                child: FilledButton.icon(
                  onPressed: state.jobRunning ? null : _render,
                  icon: const Icon(Icons.movie_creation_outlined),
                  label: Text(
                    state.jobRunning ? 'Une tâche est en cours' : 'Générer la vidéo (${fmtTime(plan['duration'])})',
                  ),
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(50)),
                ),
              ),
            ),
      body: plan == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(12),
              children: [
                Text(
                  'Touchez un plan pour le choisir. Voix : ${plan['voice']} · choix des plans : '
                  '${plan['matcher'] == 'clip' ? 'IA (texte ↔ image)' : 'ambiance + beauté'}',
                  style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant),
                ),
                const SizedBox(height: 8),
                for (var si = 0; si < (plan['sentences'] as List).length; si++) _sentenceCard(plan, si),
              ],
            ),
    );
  }

  Widget _sentenceCard(Map<String, dynamic> plan, int si) {
    final api = AppScope.read(context).api!;
    final sentence = plan['sentences'][si] as Map<String, dynamic>;
    final slots = [
      for (var k = 0; k < (plan['slots'] as List).length; k++)
        if (plan['slots'][k]['sentence'] == si) k,
    ];
    final color = _emotionColors[sentence['emotion']] ?? Colors.grey;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: color),
                  ),
                  child: Text(sentence['emotion'], style: TextStyle(fontSize: 11, color: color)),
                ),
                const Spacer(),
                Text(fmtTime(sentence['start']), style: const TextStyle(fontSize: 11)),
              ],
            ),
            const SizedBox(height: 6),
            Text(sentence['text']),
            if ((sentence['title'] as String?)?.isNotEmpty == true)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  'Titre affiché : ${sentence['title']}',
                  style: const TextStyle(fontSize: 12, color: accent),
                ),
              ),
            for (final k in slots) ...[
              const SizedBox(height: 8),
              SizedBox(
                height: 74,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: (plan['slots'][k]['candidates'] as List).length,
                  separatorBuilder: (_, _) => const SizedBox(width: 6),
                  itemBuilder: (_, c) {
                    final selected = plan['slots'][k]['choice'] == c;
                    final cand = plan['slots'][k]['candidates'][c];
                    return GestureDetector(
                      onTap: () => _choose(k, c),
                      child: Container(
                        width: 120,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: selected ? accent : Colors.transparent, width: 3),
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: Stack(
                          fit: StackFit.expand,
                          children: [
                            Image.network(
                              api.presentationThumbUrl(widget.name, k, c),
                              headers: api.authHeaders,
                              fit: BoxFit.cover,
                              errorBuilder: (_, _, _) => Container(color: Colors.black26),
                            ),
                            Positioned(
                              left: 4,
                              bottom: 2,
                              child: Text(
                                'ép. ${cand['episode']} · ${fmtTime(cand['start'])}',
                                style: const TextStyle(fontSize: 10, shadows: [Shadow(blurRadius: 3)]),
                              ),
                            ),
                            if (selected)
                              const Positioned(
                                right: 4,
                                top: 4,
                                child: Icon(Icons.check_circle, color: accent, size: 18),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
