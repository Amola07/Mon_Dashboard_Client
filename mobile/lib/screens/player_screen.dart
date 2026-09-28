import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

/// Lecteur plein écran d'une vidéo servie par le serveur (streaming avec mot de passe).
class PlayerScreen extends StatefulWidget {
  const PlayerScreen({
    super.key,
    required this.title,
    required this.uri,
    required this.headers,
    this.actions = const [],
  });
  final String title;
  final Uri uri;
  final Map<String, String> headers;
  final List<Widget> actions;

  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> {
  late final VideoPlayerController _ctrl;
  String? _error;

  @override
  void initState() {
    super.initState();
    _ctrl = VideoPlayerController.networkUrl(widget.uri, httpHeaders: widget.headers)
      ..setLooping(true)
      ..initialize()
          .then((_) {
            if (mounted) {
              setState(() {});
              _ctrl.play();
            }
          })
          .catchError((Object e) {
            if (mounted) {
              setState(
                () => _error = kIsWeb
                    ? 'Lecture impossible ici. Revenez à la liste et touchez l\'icône « Ouvrir dans Safari ».'
                    : 'Lecture impossible. La vidéo est peut-être trop lourde pour ce '
                          'téléphone (4K à haut fps) : partagez-la ou enregistrez-la dans la galerie.',
              );
            }
          });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(backgroundColor: Colors.black, title: Text(widget.title), actions: widget.actions),
      body: Center(
        child: _error != null
            ? Padding(
                padding: const EdgeInsets.all(24),
                child: Text(_error!, textAlign: TextAlign.center),
              )
            : !_ctrl.value.isInitialized
            ? const CircularProgressIndicator()
            : GestureDetector(
                onTap: () => setState(() => _ctrl.value.isPlaying ? _ctrl.pause() : _ctrl.play()),
                child: Stack(
                  alignment: Alignment.bottomCenter,
                  children: [
                    AspectRatio(aspectRatio: _ctrl.value.aspectRatio, child: VideoPlayer(_ctrl)),
                    VideoProgressIndicator(_ctrl, allowScrubbing: true, padding: const EdgeInsets.all(12)),
                    if (!_ctrl.value.isPlaying)
                      const Positioned.fill(child: Icon(Icons.play_arrow_rounded, size: 80, color: Colors.white70)),
                  ],
                ),
              ),
      ),
    );
  }
}
