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
  int? _selectedId; // null is All
  bool loading = false;
  bool done = false; // the last page came back short
  Object? error;

  /// Bumped by each reset: a page from an older one is dropped.
  int _generation = 0;

  /// The drawer whose feed is shown; null is All.
  PromptOut? get selected =>
      drawers.where((d) => d.id == _selectedId).firstOrNull;

  /// The pills only make sense with a choice to make.
  bool get showPills => drawers.length > 1;

  /// Some shown drawer is still waiting for the worker: its papers are coming.
  bool get reading => (selected == null ? drawers : [selected!]).any(
    (d) => d.status == 'pending',
  );

  /// The drawers that kept [paper], named on its card in All only.
  List<PromptOut> drawersOf(GlobalFeedPaperOut paper) =>
      showPills && _selectedId == null
      ? drawers.where((d) => paper.promptIds.contains(d.id)).toList()
      : const [];

  /// Shows one drawer's feed, or All with null.
  Future<void> select(int? drawerId) {
    _selectedId = drawerId;
    papers.clear(); // another drawer's papers must not linger
    return refresh();
  }

  /// Starts again from the top, drawers included.
  Future<void> refresh() => _load(reset: true);

  Future<void> loadMore() => done ? Future.value() : _load(reset: false);

  Future<void> _load({required bool reset}) async {
    if (loading && !reset) return;
    final generation = reset ? ++_generation : _generation;
    loading = true;
    error = null;
    notifyListeners();
    try {
      final List<GlobalFeedPaperOut> page;
      if (reset) {
        final (drawers, first) = await (
          _drawers.list(),
          _feed.page(offset: 0, drawerId: _selectedId),
        ).wait;
        if (generation != _generation) return;
        this.drawers = drawers;
        papers.clear();
        page = first;
      } else {
        page = await _feed.page(offset: papers.length, drawerId: _selectedId);
        if (generation != _generation) return;
      }
      // Papers arriving on top push older ones down a page: skip repeats.
      final seen = {for (final p in papers) p.externalId};
      papers.addAll(page.where((p) => seen.add(p.externalId)));
      done = page.length < feedPageSize;
    } catch (e) {
      if (generation == _generation) error = e; // shown with Retry
    } finally {
      if (generation == _generation) {
        loading = false;
        notifyListeners();
      }
    }
  }
}
