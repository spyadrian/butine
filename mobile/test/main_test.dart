import 'package:butine/main.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('shows the placeholder Butine screen', (tester) async {
    await tester.pumpWidget(const ButineApp());
    expect(find.text('Butine'), findsOneWidget);
  });
}
