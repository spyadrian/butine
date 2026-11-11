import 'package:flutter/foundation.dart';

import '../../data/api/butine_api.dart';
import '../../data/repositories/drawer_repository.dart';
import '../../data/repositories/feed_repository.dart';

class FeedViewModel extends ChangeNotifier {
  FeedViewModel(this._feed, this._drawers);

  final FeedRepository _feed;
  final DrawerRepository _drawers;

  final List<GlobalFeedPaperOut> papers = [];
  List<PromptOut> drawers = [];
  bool loading = false;
  bool done = false; // the last page came back short
  Object? error;

  /// Some drawer is still waiting for the worker: its papers are coming.
  bool get reading => drawers.any((d) => d.status == 'pending');

  /// Starts again from the top, drawers included.
  Future<void> refresh() => _load(reset: true);

  Future<void> loadMore() => done ? Future.value() : _load(reset: false);

  Future<void> _load({required bool reset}) async {
    if (loading) return;
    loading = true;
    error = null;
    notifyListeners();
    try {
      final List<GlobalFeedPaperOut> page;
      if (reset) {
        final (drawers, first) = await (
          _drawers.list(),
          _feed.page(offset: 0),
        ).wait;
        this.drawers = drawers;
        papers.clear();
        page = first;
      } else {
        page = await _feed.page(offset: papers.length);
      }
      // Papers arriving on top push older ones down a page: skip repeats.
      final seen = {for (final p in papers) p.externalId};
      papers.addAll(page.where((p) => seen.add(p.externalId)));
      done = page.length < feedPageSize;
    } catch (e) {
      error = e; // shown with Retry
    } finally {
      loading = false;
      notifyListeners();
    }
  }
}
