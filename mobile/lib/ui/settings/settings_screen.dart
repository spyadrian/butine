import 'package:flutter/material.dart';

import 'settings_view_model.dart';

/// Kept equal to pubspec.yaml's version by a test.
const appVersion = '0.1.0';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key, required this.viewModel});

  final SettingsViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    Widget heading(String text) => Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Text(
        text,
        style: theme.textTheme.titleSmall!.copyWith(
          color: theme.colorScheme.primary,
        ),
      ),
    );
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          heading('Theme'),
          ValueListenableBuilder(
            valueListenable: viewModel.themeMode,
            builder: (context, mode, _) => RadioGroup<ThemeMode>(
              groupValue: mode,
              onChanged: (m) => viewModel.setThemeMode(m!),
              child: const Column(
                children: [
                  RadioListTile(value: ThemeMode.system, title: Text('System')),
                  RadioListTile(value: ThemeMode.light, title: Text('Light')),
                  RadioListTile(value: ThemeMode.dark, title: Text('Dark')),
                ],
              ),
            ),
          ),
          heading('Sources'),
          const ListTile(title: Text('arXiv')),
          const ListTile(title: Text('bioRxiv')),
          heading('About'),
          const ListTile(title: Text('Version'), trailing: Text(appVersion)),
        ],
      ),
    );
  }
}
