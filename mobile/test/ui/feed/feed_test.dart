import 'dart:async';

import 'package:butine/data/api/butine_api.dart';
import 'package:butine/data/repositories/feed_repository.dart';
import 'package:butine/ui/feed/feed_screen.dart';
import 'package:butine/ui/feed/feed_view_model.dart';
import 'package:butine/ui/feed/paper_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import '../../data/repositories/user_repository_test.dart' show FakeDeviceStore;
import '../drawer/new_drawer_test.dart' show FakeDrawerRepository;

GlobalFeedPaperOut paper(int i) => GlobalFeedPaperOut(
  externalId: 'p$i',
  version: 1,
  title: 'Paper $i',
  authors: const ['Ada Lovelace', 'Alan Turing'],
  abstract2: 'Abstract',
  categories: const ['cs.LG'],
  link: 'https://arxiv.org/abs/p$i',
  publishedAt: GlobalFeedPaperOutPublishedAt.fromJson('2026-11-10T00:00:00Z'),
  fetchedAt: DateTime.utc(2026, 11, 10, 6),
  source: 'arXiv — Computer Science',
  score: 0.8,
  promptIds: const [1],
);

/// Serves [total] papers, newest first, in pages; throws [failure] if set.
class FakeFeedRepository implements FeedRepository {
  FakeFeedRepository(this.total);

  int total;
  Object? failure;

  /// Papers that arrived on top since the first page.
  int shift = 0;
  final offsets = <int>[];

  /// The drawer asked for with each page; null is All.
  final drawerIds = <int?>[];

  /// When set, pages wait for it: lets a test see the loading state.
  Completer<void>? gate;

  @override
  Future<List<GlobalFeedPaperOut>> page({
    required int offset,
    int? drawerId,
  }) async {
    offsets.add(offset);
    drawerIds.add(drawerId);
    await gate?.future;
    if (failure != null) throw failure!;
    final end = (offset + feedPageSize).clamp(0, total + shift);
    return [for (var i = offset; i < end; i++) paper(i - shift)];
  }
}

/// The honey dot, labelled for screen readers.
final newDot = find.byWidgetPredicate(
  (w) => w is Semantics && w.properties.label == 'New',
);

PromptOut drawer(String status, {int id = 1, String name = 'Batteries'}) =>
    PromptOut(
      id: id,
      name: name,
      icon: 'bolt',
      text: 'Prompt of $name',
      createdAt: DateTime.utc(2026, 11, 11),
      status: status,
    );

final threeDrawers = [
  drawer('ready'),
  drawer('ready', id: 2, name: 'Solar'),
  drawer('pending', id: 3, name: 'Robots'),
];

Future<FeedViewModel> pumpFeed(
  WidgetTester tester,
  FeedRepository feed, {
  String status = 'ready',
  List<PromptOut>? drawers,
  FakeDeviceStore? store,
}) async {
  final vm = FeedViewModel(
    feed,
    FakeDrawerRepository(drawers: drawers ?? [drawer(status)]),
    store ?? FakeDeviceStore(),
  );
  await tester.pumpWidget(
    MaterialApp(
      home: FeedScreen(viewModel: vm),
      routes: {'/new-drawer': (_) => const Text('New drawer screen')},
    ),
  );
  await tester.pumpAndSettle();
  return vm;
}

void main() {
  group('view model', () {
    FeedViewModel vmFor(FeedRepository feed) => FeedViewModel(
      feed,
      FakeDrawerRepository(drawers: [drawer('ready')]),
      FakeDeviceStore(),
    );

    test('pages by 50 with no duplicate or gap, then stops', () async {
      final feed = FakeFeedRepository(120);
      final vm = vmFor(feed);

      await vm.refresh();
      await vm.loadMore();
      await vm.loadMore();
      await vm.loadMore(); // past the end: no call

      expect(feed.offsets, [0, 50, 100]);
      expect(vm.papers.map((p) => p.externalId), [
        for (var i = 0; i < 120; i++) 'p$i',
      ]);
      expect(vm.done, isTrue);
    });

    test('a paper pushed down by a new arrival is not shown twice', () async {
      final feed = FakeFeedRepository(60);
      final vm = vmFor(feed);
      await vm.refresh();

      feed.shift = 1; // a new paper on top: p49 comes back at offset 50
      await vm.loadMore();

      expect(vm.papers.map((p) => p.externalId), [
        for (var i = 0; i < 60; i++) 'p$i',
      ]);
    });

    test('refresh starts again from the top', () async {
      final feed = FakeFeedRepository(120);
      final vm = vmFor(feed);
      await vm.refresh();
      await vm.loadMore();

      feed.total = 3;
      await vm.refresh();

      expect(feed.offsets.last, 0);
      expect(vm.papers, hasLength(3));
      expect(vm.done, isTrue);
    });

    test('an error is kept, and a retry clears it', () async {
      final feed = FakeFeedRepository(3)
        ..failure = http.ClientException('offline');
      final vm = vmFor(feed);

      await vm.refresh();
      expect(vm.error, isNotNull);

      feed.failure = null;
      await vm.refresh();
      expect(vm.error, isNull);
      expect(vm.papers, hasLength(3));
    });
  });

  group('drawers', () {
    test('selecting a drawer loads its feed, All goes back', () async {
      final feed = FakeFeedRepository(3);
      final vm = FeedViewModel(
        feed,
        FakeDrawerRepository(drawers: threeDrawers),
        FakeDeviceStore(),
      );
      await vm.refresh();

      await vm.select(2);
      expect(vm.selected?.name, 'Solar');
      expect(feed.drawerIds.last, 2);

      await vm.select(null);
      expect(vm.selected, isNull);
      expect(feed.drawerIds.last, isNull);
    });

    test('a selection made while a page loads wins', () async {
      final feed = FakeFeedRepository(3)..gate = Completer();
      final vm = FeedViewModel(
        feed,
        FakeDrawerRepository(drawers: threeDrawers),
        FakeDeviceStore(),
      );
      final first = vm.refresh();
      final second = vm.select(2);
      feed.gate!.complete();
      await (first, second).wait;

      expect(feed.drawerIds, [null, 2]);
      expect(vm.loading, isFalse);
      expect(vm.papers, hasLength(3));
    });

    test('reading follows the selected drawer', () async {
      final vm = FeedViewModel(
        FakeFeedRepository(0),
        FakeDrawerRepository(drawers: threeDrawers),
        FakeDeviceStore(),
      );
      await vm.refresh();
      expect(vm.reading, isTrue); // Robots is pending

      await vm.select(2);
      expect(vm.reading, isFalse);
    });
  });

  group('New', () {
    final opened = DateTime.utc(2026, 11, 11, 8);

    FeedViewModel vmWith(FakeDeviceStore store) => FeedViewModel(
      FakeFeedRepository(3),
      FakeDrawerRepository(drawers: [drawer('ready')]),
      store,
      now: () => opened,
    );

    test('first open: nothing is New, and the open is kept', () async {
      final store = FakeDeviceStore();
      final vm = vmWith(store);
      await vm.open();

      expect(vm.papers.where(vm.isNew), isEmpty);
      expect(store.feedOpenedAt, opened);
    });

    test(
      'papers fetched since the last open are New, older ones not',
      () async {
        // Papers are fetched at 06:00 on Nov 10.
        final before = vmWith(
          FakeDeviceStore()..feedOpenedAt = DateTime.utc(2026, 11, 10, 5),
        );
        await before.open();
        expect(before.papers.every(before.isNew), isTrue);

        final after = vmWith(
          FakeDeviceStore()..feedOpenedAt = DateTime.utc(2026, 11, 10, 7),
        );
        await after.open();
        expect(after.papers.where(after.isNew), isEmpty);
      },
    );

    test('a refresh keeps the signal and the date', () async {
      final store = FakeDeviceStore()
        ..feedOpenedAt = DateTime.utc(2026, 11, 10, 5);
      final vm = vmWith(store);
      await vm.open();
      await vm.refresh();
      await vm.select(null);

      expect(store.feedOpenSaves, 1);
      expect(vm.papers.every(vm.isNew), isTrue);
    });

    testWidgets('a New paper carries the honey dot, others do not', (
      tester,
    ) async {
      await pumpFeed(
        tester,
        FakeFeedRepository(1),
        store: FakeDeviceStore()..feedOpenedAt = DateTime.utc(2026, 11, 10, 5),
      );
      expect(newDot, findsOneWidget);
      expect(find.text('New'), findsNothing); // never as text
    });

    testWidgets('no dot on the first open', (tester) async {
      await pumpFeed(tester, FakeFeedRepository(1));
      expect(newDot, findsNothing);
    });
  });

  group('pills', () {
    testWidgets('hidden with a single drawer, + moves to the bar', (
      tester,
    ) async {
      await pumpFeed(tester, FakeFeedRepository(1));
      expect(find.byType(ChoiceChip), findsNothing);

      await tester.tap(find.byTooltip('New drawer'));
      await tester.pumpAndSettle();
      expect(find.text('New drawer screen'), findsOneWidget);
    });

    testWidgets('All, one pill per drawer in order, then +', (tester) async {
      await pumpFeed(tester, FakeFeedRepository(1), drawers: threeDrawers);

      final labels = tester
          .widgetList<ChoiceChip>(find.byType(ChoiceChip))
          .map((c) => (c.label as Text).data);
      expect(labels, ['All', 'Batteries', 'Solar', 'Robots']);
      expect(find.text('3 drawers'), findsOneWidget);

      final plus = find.byTooltip('New drawer');
      expect(
        find.ancestor(of: plus, matching: find.byType(ActionChip)),
        findsOneWidget,
      );
      await tester.tap(plus);
      await tester.pumpAndSettle();
      expect(find.text('New drawer screen'), findsOneWidget);
    });

    testWidgets('a pill filters the feed and shows its prompt', (tester) async {
      final feed = FakeFeedRepository(2);
      await pumpFeed(tester, feed, drawers: threeDrawers);

      await tester.tap(find.widgetWithText(ChoiceChip, 'Solar'));
      await tester.pumpAndSettle();
      expect(feed.drawerIds.last, 2);
      expect(find.text('Prompt of Solar'), findsOneWidget);
      expect(find.text('3 drawers'), findsNothing);

      await tester.tap(find.widgetWithText(ChoiceChip, 'All'));
      await tester.pumpAndSettle();
      expect(feed.drawerIds.last, isNull);
      expect(find.text('3 drawers'), findsOneWidget);
    });

    testWidgets('in All, a card names every drawer that kept it', (
      tester,
    ) async {
      final feed = _TwoDrawerPaper();
      await pumpFeed(tester, feed, drawers: threeDrawers);

      final card = find.byType(PaperCard);
      expect(
        find.descendant(of: card, matching: find.text('Batteries')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: card, matching: find.text('Solar')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: card, matching: find.text('Robots')),
        findsNothing,
      );

      await tester.tap(find.widgetWithText(ChoiceChip, 'Solar'));
      await tester.pumpAndSettle();
      expect(
        find.descendant(of: card, matching: find.text('Batteries')),
        findsNothing,
      );
    });
  });

  group('screen', () {
    testWidgets('shows a spinner while the first page loads', (tester) async {
      final feed = FakeFeedRepository(3)..gate = Completer();
      await tester.pumpWidget(
        MaterialApp(
          home: FeedScreen(
            viewModel: FeedViewModel(
              feed,
              FakeDrawerRepository(),
              FakeDeviceStore(),
            ),
          ),
        ),
      );
      await tester.pump();
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      feed.gate!.complete();
      await tester.pumpAndSettle();
      expect(find.byType(PaperCard), findsNWidgets(3));
    });

    testWidgets('a card shows title, authors, source and date', (tester) async {
      await pumpFeed(tester, FakeFeedRepository(1));

      expect(find.text('Paper 0'), findsOneWidget);
      expect(find.text('Ada Lovelace, Alan Turing'), findsOneWidget);
      expect(find.textContaining('arXiv — Computer Science'), findsOneWidget);
      expect(find.textContaining('Nov 10'), findsOneWidget);
    });

    testWidgets('a pending drawer says Butine is reading', (tester) async {
      await pumpFeed(tester, FakeFeedRepository(0), status: 'pending');
      expect(find.text('Butine is reading the latest papers…'), findsOneWidget);
    });

    testWidgets('a ready drawer with nothing says No papers yet', (
      tester,
    ) async {
      await pumpFeed(tester, FakeFeedRepository(0));
      expect(find.text('No papers yet'), findsOneWidget);
    });

    testWidgets('an error offers Retry, which reloads', (tester) async {
      final feed = FakeFeedRepository(2)
        ..failure = http.ClientException('offline');
      await pumpFeed(tester, feed);
      expect(find.textContaining('Could not reach Butine'), findsOneWidget);

      feed.failure = null;
      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();
      expect(find.byType(PaperCard), findsNWidgets(2));
    });

    testWidgets('scrolling to the bottom loads the next page, then the end', (
      tester,
    ) async {
      final feed = FakeFeedRepository(70);
      await pumpFeed(tester, feed);

      await tester.scrollUntilVisible(find.text('Paper 69'), 500);
      await tester.pumpAndSettle();
      expect(feed.offsets, [0, 50]);

      await tester.scrollUntilVisible(find.text("That's all for now"), 500);
      expect(feed.offsets, [0, 50]);
    });

    testWidgets('pull to refresh reloads from the top', (tester) async {
      final feed = FakeFeedRepository(3);
      await pumpFeed(tester, feed);

      await tester.fling(find.text('Paper 0'), const Offset(0, 400), 1000);
      await tester.pumpAndSettle();
      expect(feed.offsets, [0, 0]);
    });
  });
}

/// One paper, kept by drawers 1 and 2.
class _TwoDrawerPaper extends FakeFeedRepository {
  _TwoDrawerPaper() : super(1);

  @override
  Future<List<GlobalFeedPaperOut>> page({
    required int offset,
    int? drawerId,
  }) async {
    drawerIds.add(drawerId);
    final p = paper(0);
    return [
      GlobalFeedPaperOut.fromJson({
        ...p.toJson(),
        'prompt_ids': [1, 2],
      }),
    ];
  }
}
