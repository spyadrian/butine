import 'package:butine/ui/core/theme.dart';
import 'package:butine/ui/drawer/drawer_screen.dart';
import 'package:butine/ui/drawer/drawer_view_model.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import '../feed/feed_test.dart' show drawer;
import 'new_drawer_test.dart' show FakeDrawerRepository;

void main() {
  /// What the drawer screen popped with.
  Object? popped;

  /// The drawer screen pushed over a home page, to see it pop.
  Future<void> pumpDrawer(
    WidgetTester tester,
    FakeDrawerRepository repo, {
    String status = 'ready',
    ThemeData? theme,
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: Builder(
          builder: (context) => TextButton(
            onPressed: () async {
              popped = await Navigator.of(context).push(
                MaterialPageRoute<bool>(
                  builder: (_) => DrawerScreen(
                    viewModel: DrawerViewModel(repo, drawer(status)),
                  ),
                ),
              );
            },
            child: const Text('home'),
          ),
        ),
      ),
    );
    await tester.tap(find.text('home'));
    await tester.pumpAndSettle();
  }

  final deleteButton = find.widgetWithText(OutlinedButton, 'Delete');
  final confirmButton = find.widgetWithText(FilledButton, 'Delete');

  testWidgets('shows name, prompt and state', (tester) async {
    await pumpDrawer(tester, FakeDrawerRepository());
    expect(find.text('Batteries'), findsOneWidget);
    expect(find.text('Prompt of Batteries'), findsOneWidget);
    expect(find.text('Ready'), findsOneWidget);
  });

  testWidgets('a pending drawer says Butine is reading', (tester) async {
    await pumpDrawer(tester, FakeDrawerRepository(), status: 'pending');
    expect(find.text('Butine is reading the latest papers…'), findsOneWidget);
  });

  testWidgets('Delete asks in the screen, Cancel keeps the drawer', (
    tester,
  ) async {
    final repo = FakeDrawerRepository();
    await pumpDrawer(tester, repo);

    await tester.tap(deleteButton);
    await tester.pumpAndSettle();
    expect(find.byType(Dialog), findsNothing);
    expect(confirmButton, findsOneWidget);

    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(confirmButton, findsNothing);
    expect(repo.deleted, isEmpty);
  });

  testWidgets('confirming deletes and goes back', (tester) async {
    final repo = FakeDrawerRepository();
    await pumpDrawer(tester, repo);

    await tester.tap(deleteButton);
    await tester.pumpAndSettle();
    await tester.tap(confirmButton);
    await tester.pumpAndSettle();

    expect(repo.deleted, [1]);
    expect(find.byType(DrawerScreen), findsNothing);
    expect(popped, isTrue);
  });

  testWidgets('a network error says so; Retry deletes', (tester) async {
    final repo = FakeDrawerRepository(failure: http.ClientException('down'));
    await pumpDrawer(tester, repo);

    await tester.tap(deleteButton);
    await tester.pumpAndSettle();
    await tester.tap(confirmButton);
    await tester.pumpAndSettle();
    expect(find.textContaining('Could not reach Butine'), findsOneWidget);
    expect(find.byType(DrawerScreen), findsOneWidget);

    repo.failure = null;
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(repo.deleted, [1]);
    expect(find.byType(DrawerScreen), findsNothing);
  });

  for (final (name, theme) in [('light', lightTheme), ('dark', darkTheme)]) {
    testWidgets('readable in the $name theme', (tester) async {
      await pumpDrawer(tester, FakeDrawerRepository(), theme: theme);
      await tester.tap(deleteButton);
      await tester.pumpAndSettle();
      await expectLater(tester, meetsGuideline(textContrastGuideline));
      await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    });
  }
}
