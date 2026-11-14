import 'package:butine/data/api/butine_api.dart';
import 'package:butine/ui/core/theme.dart';
import 'package:butine/ui/feed/paper_card.dart';
import 'package:butine/ui/paper/paper_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../feed/feed_test.dart'
    show FakeFeedRepository, drawer, paper, pumpFeed;

GlobalFeedPaperOut biorxiv() => GlobalFeedPaperOut.fromJson({
  ...paper(0).toJson(),
  'source': 'bioRxiv — Genomics',
  'link': 'https://www.biorxiv.org/content/10.1101/x',
});

void main() {
  Future<List<Uri>> pumpPaper(
    WidgetTester tester,
    GlobalFeedPaperOut p, {
    ThemeData? theme,
  }) async {
    final opened = <Uri>[];
    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: PaperScreen(
          paper: p,
          drawers: [
            drawer('ready'),
            drawer('ready', id: 2, name: 'Solar'),
          ],
          openLink: (uri) async {
            opened.add(uri);
            return true;
          },
        ),
      ),
    );
    return opened;
  }

  testWidgets('shows title, every author, source, date, abstract, drawers', (
    tester,
  ) async {
    await pumpPaper(tester, paper(0));

    expect(find.text('Paper 0'), findsOneWidget);
    expect(find.text('Ada Lovelace, Alan Turing'), findsOneWidget);
    expect(find.textContaining('arXiv — Computer Science'), findsOneWidget);
    expect(find.textContaining('Nov 10'), findsOneWidget);
    expect(find.text('Abstract'), findsOneWidget);
    expect(find.text('Batteries'), findsOneWidget);
    expect(find.text('Solar'), findsOneWidget);
  });

  testWidgets('the abstract is set in Literata', (tester) async {
    await pumpPaper(tester, paper(0));

    final abstract = tester.widget<Text>(find.text('Abstract'));
    expect(abstract.style!.fontFamily, paperFontFamily);
  });

  testWidgets('the button follows the source and opens the link', (
    tester,
  ) async {
    final opened = await pumpPaper(tester, paper(0));
    await tester.tap(find.text('Read on arXiv'));
    expect(opened, [Uri.parse('https://arxiv.org/abs/p0')]);

    final bio = await pumpPaper(tester, biorxiv());
    await tester.tap(find.text('Read on bioRxiv'));
    expect(bio, [Uri.parse('https://www.biorxiv.org/content/10.1101/x')]);
  });

  for (final (name, theme) in [('light', lightTheme), ('dark', darkTheme)]) {
    testWidgets('readable in the $name theme', (tester) async {
      await pumpPaper(tester, paper(0), theme: theme);
      await expectLater(tester, meetsGuideline(textContrastGuideline));
      await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    });
  }

  testWidgets('tapping a card opens its detail without a network call', (
    tester,
  ) async {
    final feed = FakeFeedRepository(1);
    await pumpFeed(tester, feed);
    final calls = feed.offsets.length;

    await tester.tap(find.byType(PaperCard));
    await tester.pumpAndSettle();

    expect(find.byType(PaperScreen), findsOneWidget);
    expect(find.text('Read on arXiv'), findsOneWidget);
    expect(feed.offsets.length, calls);
  });
}
