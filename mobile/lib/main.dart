import 'package:flutter/material.dart';

import 'ui/core/theme.dart';
import 'ui/core/theme_preview.dart';

void main() {
  runApp(const ButineApp());
}

class ButineApp extends StatelessWidget {
  const ButineApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Butine',
      theme: lightTheme,
      darkTheme: darkTheme,
      // shortcut: the theme specimen stands in for a home screen until the first-launch flow exists.
      home: const ThemeSpecimen(),
    );
  }
}
