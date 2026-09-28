import 'package:flutter/material.dart';

const accent = Color(0xFFFE2C55); // rose TikTok
const accent2 = Color(0xFF25F4EE); // cyan TikTok

String fmtTime(num seconds) {
  final s = seconds.round();
  return '${s ~/ 60}:${(s % 60).toString().padLeft(2, '0')}';
}

String fmtSize(num bytes) {
  if (bytes >= 1e9) return '${(bytes / 1e9).toStringAsFixed(1)} Go';
  if (bytes >= 1e6) return '${(bytes / 1e6).toStringAsFixed(0)} Mo';
  return '${(bytes / 1e3).toStringAsFixed(0)} ko';
}

const jobLabels = {
  'analyze': 'Analyse des épisodes',
  'select': 'Sélection des extraits',
  'make': 'Rendu et montage',
  'download': 'Téléchargement',
};

const statusLabels = {
  'running': 'En cours',
  'done': 'Terminé',
  'failed': 'Échec',
  'cancelled': 'Annulé',
};

void showMessage(BuildContext context, Object message, {bool error = false}) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(
      content: Text('$message'),
      backgroundColor: error ? Colors.red.shade700 : null,
      behavior: SnackBarBehavior.floating,
    ));
}

/// Exécute une action réseau et affiche l'erreur éventuelle.
Future<T?> guard<T>(BuildContext context, Future<T> Function() action, {String? success}) async {
  try {
    final result = await action();
    if (success != null && context.mounted) showMessage(context, success);
    return result;
  } catch (e) {
    if (context.mounted) showMessage(context, e, error: true);
    return null;
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.icon, required this.title, this.subtitle, this.action});
  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).colorScheme.onSurfaceVariant;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, size: 56, color: muted),
          const SizedBox(height: 12),
          Text(title, style: Theme.of(context).textTheme.titleMedium, textAlign: TextAlign.center),
          if (subtitle != null) ...[
            const SizedBox(height: 6),
            Text(subtitle!, style: TextStyle(color: muted), textAlign: TextAlign.center),
          ],
          if (action != null) ...[const SizedBox(height: 16), action!],
        ]),
      ),
    );
  }
}
