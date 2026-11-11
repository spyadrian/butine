import 'package:butine/data/repositories/user_repository.dart';
import 'package:butine/ui/drawer/new_drawer_screen.dart';
import 'package:butine/ui/onboarding/onboarding_screen.dart';
import 'package:butine/ui/onboarding/onboarding_view_model.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// Fails [failures] times, then registers.
class FakeUserRepository implements UserRepository {
  FakeUserRepository({this.failures = 0});

  int failures;
  int calls = 0;

  @override
  String? userId;

  @override
  Future<void> load() async {}

  @override
  Future<void> register() async {
    calls++;
    if (failures-- > 0) throw http.ClientException('offline');
    userId = 'u-1';
  }
}

Future<void> pumpOnboarding(WidgetTester tester, UserRepository users) =>
    tester.pumpWidget(
      MaterialApp(
        home: OnboardingScreen(viewModel: OnboardingViewModel(users)),
      ),
    );

void main() {
  test(
    'view model keeps the error, then clears it on a successful retry',
    () async {
      final users = FakeUserRepository(failures: 1);
      final vm = OnboardingViewModel(users);

      await vm.register();
      expect(vm.error, isNotNull);

      await vm.register();
      expect(vm.error, isNull);
      expect(users.userId, 'u-1');
    },
  );

  testWidgets('registers and opens the drawer creation', (tester) async {
    final users = FakeUserRepository();
    await pumpOnboarding(tester, users);

    await tester.tap(find.text('Create my first drawer'));
    await tester.pumpAndSettle();

    expect(users.calls, 1);
    expect(find.byType(NewDrawerScreen), findsOneWidget);
  });

  testWidgets('a network failure shows a message and a working Retry', (
    tester,
  ) async {
    final users = FakeUserRepository(failures: 1);
    await pumpOnboarding(tester, users);

    await tester.tap(find.text('Create my first drawer'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Could not reach Butine'), findsOneWidget);
    expect(find.byType(NewDrawerScreen), findsNothing);

    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(users.calls, 2);
    expect(find.byType(NewDrawerScreen), findsOneWidget);
  });
}
