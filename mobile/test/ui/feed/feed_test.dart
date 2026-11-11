import 'dart:async';

import 'package:butine/data/api/butine_api.dart';
import 'package:butine/data/repositories/feed_repository.dart';
import 'package:butine/ui/feed/feed_screen.dart';
import 'package:butine/ui/feed/feed_view_model.dart';
import 'package:butine/ui/feed/paper_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

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

  /// When set, pages wait for it: lets a test see the loading state.
  Completer<void>? gate;

  @override
  Future<List<GlobalFeedPaperOut>> page({required int offset}) async {
    offsets.add(offset);
    await gate?.future;
    if (failure != null) throw failure!;
    final end = (offset + feedPageSize).clamp(0, total + shift);
    return [for (var i = offset; i < end; i++) paper(i - shift)];
  }
}

PromptOut drawer(String status) => PromptOut(
  id: 1,
  name: 'Batteries',
  icon: 'bolt',
  text: 'Solid-state electrolytes',
  createdAt: DateTime.utc(2026, 11, 11),
  status: status,
);

Future<FeedViewModel> pumpFeed(
  WidgetTester tester,
  FeedRepository feed, {
  String status = 'ready',
}) async {
  final vm = FeedViewModel(
    feed,
    FakeDrawerRepository(drawers: [drawer(status)]),
  );
  await tester.pumpWidget(MaterialApp(home: FeedScreen(viewModel: vm)));
  await tester.pumpAndSettle();
  return vm;
}

void main() {
  group('view model', () {
    FeedViewModel vmFor(FeedRepository feed) =>
        FeedViewModel(feed, FakeDrawerRepository(drawers: [drawer('ready')]));

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

  group('screen', () {
    testWidgets('shows a spinner while the first page loads', (tester) async {
      final feed = FakeFeedRepository(3)..gate = Completer();
      await tester.pumpWidget(
        MaterialApp(
          home: FeedScreen(
            viewModel: FeedViewModel(feed, FakeDrawerRepository()),
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
