import 'dart:io';

import 'package:butine/ui/core/theme.dart';
import 'package:butine/ui/settings/settings_screen.dart';
import 'package:butine/ui/settings/settings_view_model.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../data/repositories/user_repository_test.dart' show FakeDeviceStore;

void main() {
  Future<(SettingsViewModel, FakeDeviceStore)> pumpSettings(
    WidgetTester tester, {
    ThemeData? theme,
  }) async {
    final store = FakeDeviceStore();
    final vm = SettingsViewModel(store, ValueNotifier(ThemeMode.system));
    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: SettingsScreen(viewModel: vm),
      ),
    );
    return (vm, store);
  }

  testWidgets('System is picked by default', (tester) async {
    await pumpSettings(tester);
    final group = tester.widget<RadioGroup<ThemeMode>>(
      find.byType(RadioGroup<ThemeMode>),
    );
    expect(group.groupValue, ThemeMode.system);
  });

  testWidgets('picking a theme applies it and keeps it', (tester) async {
    final (vm, store) = await pumpSettings(tester);

    await tester.tap(find.text('Dark'));
    await tester.pumpAndSettle();

    expect(vm.themeMode.value, ThemeMode.dark);
    expect(store.themeModeSaved, ThemeMode.dark);
  });

  testWidgets('shows the app version and the followed sources', (tester) async {
    await pumpSettings(tester);
    final pubspec = File('pubspec.yaml').readAsStringSync();
    final version = RegExp(
      r'^version: ([^+\s]+)',
      multiLine: true,
    ).firstMatch(pubspec)!.group(1)!;

    expect(appVersion, version);
    expect(find.text(appVersion), findsOneWidget);
    expect(find.text('arXiv'), findsOneWidget);
    expect(find.text('bioRxiv'), findsOneWidget);
  });

  for (final (name, theme) in [('light', lightTheme), ('dark', darkTheme)]) {
    testWidgets('readable in the $name theme', (tester) async {
      await pumpSettings(tester, theme: theme);
      await expectLater(tester, meetsGuideline(textContrastGuideline));
      await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    });
  }
}
