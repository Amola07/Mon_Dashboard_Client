import 'package:file_picker/file_picker.dart';
import 'package:flutter/widgets.dart';

import 'api.dart';
import 'ui.dart';

/// Choisit un fichier sur le téléphone et l'envoie au serveur (en flux, Android comme web app).
/// Renvoie le nom du fichier envoyé, ou null (annulé / erreur affichée).
Future<String?> pickAndUpload(BuildContext context, ApiClient api, String kind, FileType type) async {
  final files = await FilePicker.pickFiles(type: type);
  if (files.isEmpty || !context.mounted) return null;
  final file = files.first;
  final length = file.lengthSync() ?? await file.length();
  if (length == null) {
    if (context.mounted) showMessage(context, 'Fichier illisible', error: true);
    return null;
  }
  if (!context.mounted) return null;
  showMessage(context, 'Envoi de ${file.name} (${fmtSize(length)})…');
  final ok = await guard(context, () async {
    await api.upload(kind, file.name, file.readAsByteStream(), length);
    return true;
  }, success: '${file.name} envoyé');
  return ok == true ? file.name : null;
}
