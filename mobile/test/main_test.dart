import 'package:butine/main.dart';
import 'package:butine/ui/feed/feed_screen.dart';
import 'package:butine/ui/feed/paper_card.dart';
import 'package:butine/ui/onboarding/onboarding_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'data/repositories/user_repository_test.dart' show FakeDeviceStore;
import 'ui/drawer/new_drawer_test.dart' show FakeDrawerRepository;
import 'ui/feed/feed_test.dart' show FakeFeedRepository;
import 'ui/onboarding/onboarding_test.dart' show FakeUserRepository;

void main() {
  testWidgets('a new device sees the welcome screen', (tester) async {
    await tester.pumpWidget(
      ButineApp(
        users: FakeUserRepository(),
        drawers: FakeDrawerRepository(),
        feed: FakeFeedRepository(0),
        store: FakeDeviceStore(),
        themeMode: ValueNotifier(ThemeMode.system),
      ),
    );
    expect(find.byType(OnboardingScreen), findsOneWidget);
  });

  testWidgets('a registered device opens the feed', (tester) async {
    await tester.pumpWidget(
      ButineApp(
        users: FakeUserRepository()..userId = 'u-1',
        drawers: FakeDrawerRepository(),
        feed: FakeFeedRepository(0),
        store: FakeDeviceStore(),
        themeMode: ValueNotifier(ThemeMode.system),
      ),
    );
    expect(find.byType(OnboardingScreen), findsNothing);
    expect(find.byType(FeedScreen), findsOneWidget);
  });

  testWidgets('Settings, from the feed, switches the theme at once', (
    tester,
  ) async {
    final store = FakeDeviceStore();
    await tester.pumpWidget(
      ButineApp(
        users: FakeUserRepository()..userId = 'u-1',
        drawers: FakeDrawerRepository(),
        feed: FakeFeedRepository(3),
        store: store,
        themeMode: ValueNotifier(ThemeMode.system),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Settings'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Dark'));
    await tester.pumpAndSettle();

    final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(app.themeMode, ThemeMode.dark);
    expect(store.themeModeSaved, ThemeMode.dark);

    // The feed underneath keeps its papers through the rebuild.
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.byType(PaperCard), findsNWidgets(3));
  });
}
