import 'package:flutter/material.dart';

import 'app_state.dart';
import 'screens/connect_screen.dart';
import 'screens/home_screen.dart';
import 'ui.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final state = AppState();
  await state.load();
  if (state.configured) state.refresh();
  runApp(AnimeTikTokStudio(state: state));
}

class AnimeTikTokStudio extends StatelessWidget {
  const AnimeTikTokStudio({super.key, required this.state});
  final AppState state;

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(
      seedColor: accent,
      brightness: Brightness.dark,
      primary: accent,
      secondary: accent2,
      surface: const Color(0xFF121212),
    );
    return AppScope(
      state: state,
      child: MaterialApp(
        title: 'Anime TikTok Studio',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: scheme,
          useMaterial3: true,
          scaffoldBackgroundColor: const Color(0xFF0B0B0B),
          cardTheme: const CardThemeData(color: Color(0xFF1A1A1A), margin: EdgeInsets.zero),
        ),
        home: Builder(
          builder: (context) => AppScope.of(context).configured ? const HomeScreen() : const ConnectScreen(),
        ),
      ),
    );
  }
}
