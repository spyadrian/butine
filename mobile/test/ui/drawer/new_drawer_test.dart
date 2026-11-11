import 'package:butine/data/api/butine_api.dart';
import 'package:butine/data/repositories/drawer_repository.dart';
import 'package:butine/ui/core/drawer_icons.dart';
import 'package:butine/ui/drawer/new_drawer_screen.dart';
import 'package:butine/ui/drawer/new_drawer_view_model.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// Records what it creates, or throws [failure]; [list] returns [drawers].
class FakeDrawerRepository implements DrawerRepository {
  FakeDrawerRepository({this.failure, this.drawers = const []});

  Object? failure;
  List<PromptOut> drawers;
  final created = <(String, String, String)>[];

  @override
  Future<List<PromptOut>> list() async {
    if (failure != null) throw failure!;
    return drawers;
  }

  @override
  Future<PromptOut> create({
    required String name,
    required String icon,
    required String text,
  }) async {
    if (failure != null) throw failure!;
    created.add((name, icon, text));
    return PromptOut(
      id: created.length,
      name: name,
      icon: icon,
      text: text,
      createdAt: DateTime(2026, 11, 11),
      status: 'pending',
    );
  }
}

Future<void> pumpNewDrawer(WidgetTester tester, DrawerRepository drawers) =>
    tester.pumpWidget(
      MaterialApp(
        home: NewDrawerScreen(viewModel: NewDrawerViewModel(drawers)),
        routes: {'/feed': (_) => const Text('feed')},
      ),
    );

FilledButton createButton(WidgetTester tester) =>
    tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Create'));

void main() {
  group('validation', () {
    NewDrawerViewModel valid() => NewDrawerViewModel(FakeDrawerRepository())
      ..name = 'Batteries'
      ..text = 'Solid-state electrolytes';

    test('a name and a prompt are enough', () {
      final vm = valid();
      expect(vm.canSubmit, isTrue);
      expect(vm.icon, defaultDrawerIcon);
    });

    test('blank, or too long once trimmed, is invalid', () {
      expect((valid()..name = '   ').canSubmit, isFalse);
      expect((valid()..name = 'x' * 25).canSubmit, isFalse);
      expect((valid()..name = '  ${'x' * 24}  ').canSubmit, isTrue);
      expect((valid()..text = '\n').canSubmit, isFalse);
      expect((valid()..text = 'x' * 501).canSubmit, isFalse);
      expect((valid()..text = 'x' * 500).canSubmit, isTrue);
    });

    test('submit sends trimmed values and refuses invalid ones', () async {
      final drawers = FakeDrawerRepository();
      final vm = NewDrawerViewModel(drawers)
        ..name = ' Batteries '
        ..icon = 'bolt'
        ..text = ' Solid-state electrolytes\n';

      expect(await vm.submit(), isTrue);
      expect(drawers.created.single, (
        'Batteries',
        'bolt',
        'Solid-state electrolytes',
      ));

      expect(await (vm..name = '').submit(), isFalse);
      expect(drawers.created, hasLength(1));
    });
  });

  testWidgets('Create stays disabled until both fields are valid', (
    tester,
  ) async {
    await pumpNewDrawer(tester, FakeDrawerRepository());
    expect(createButton(tester).onPressed, isNull);

    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Batteries');
    await tester.pump();
    expect(createButton(tester).onPressed, isNull);

    await tester.tap(find.byType(ActionChip).first);
    await tester.pump();
    expect(createButton(tester).onPressed, isNotNull);
  });

  testWidgets('creates the drawer with the picked icon, then opens the feed', (
    tester,
  ) async {
    final drawers = FakeDrawerRepository();
    await pumpNewDrawer(tester, drawers);

    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Batteries');
    await tester.enterText(
      find.widgetWithText(TextField, 'Prompt'),
      'Solid-state electrolytes',
    );
    await tester.tap(find.byTooltip('bolt'));
    await tester.pump();
    await tester.tap(find.text('Create'));
    await tester.pumpAndSettle();

    expect(drawers.created.single, (
      'Batteries',
      'bolt',
      'Solid-state electrolytes',
    ));
    expect(find.text('feed'), findsOneWidget);
    expect(find.byType(NewDrawerScreen), findsNothing);
  });

  testWidgets('a 403 shows the plan limit and stays on the form', (
    tester,
  ) async {
    await pumpNewDrawer(
      tester,
      FakeDrawerRepository(failure: const DrawerLimitReached()),
    );

    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Second');
    await tester.enterText(find.widgetWithText(TextField, 'Prompt'), 'More');
    await tester.pump();
    await tester.tap(find.text('Create'));
    await tester.pumpAndSettle();

    expect(find.text('The free plan includes 1 drawer.'), findsOneWidget);
    expect(find.byType(NewDrawerScreen), findsOneWidget);
  });

  testWidgets('a network failure says so', (tester) async {
    await pumpNewDrawer(
      tester,
      FakeDrawerRepository(failure: http.ClientException('offline')),
    );

    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'A');
    await tester.enterText(find.widgetWithText(TextField, 'Prompt'), 'B');
    await tester.pump();
    await tester.tap(find.text('Create'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Could not reach Butine'), findsOneWidget);
  });

  testWidgets('every icon is a tap target of at least 48 dp', (tester) async {
    await pumpNewDrawer(tester, FakeDrawerRepository());

    for (final id in drawerIcons.keys) {
      final size = tester.getSize(
        find.ancestor(
          of: find.byTooltip(id),
          matching: find.byType(IconButton),
        ),
      );
      expect(size.width, greaterThanOrEqualTo(48), reason: id);
      expect(size.height, greaterThanOrEqualTo(48), reason: id);
    }
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
  });
}
