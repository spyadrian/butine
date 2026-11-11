import 'package:butine/main.dart';
import 'package:butine/ui/onboarding/onboarding_screen.dart';
import 'package:flutter_test/flutter_test.dart';

import 'ui/onboarding/onboarding_test.dart' show FakeUserRepository;

void main() {
  testWidgets('a new device sees the welcome screen', (tester) async {
    await tester.pumpWidget(ButineApp(users: FakeUserRepository()));
    expect(find.byType(OnboardingScreen), findsOneWidget);
  });

  testWidgets('a registered device skips the welcome screen', (tester) async {
    await tester.pumpWidget(
      ButineApp(users: FakeUserRepository()..userId = 'u-1'),
    );
    expect(find.byType(OnboardingScreen), findsNothing);
  });
}
