import '../api/butine_api.dart';
import 'user_repository.dart';

const feedPageSize = 50;

/// The papers kept for the user's drawers.
class FeedRepository {
  FeedRepository(this._api, this._users);

  final ApiClient _api;
  final UserRepository _users;

  /// Newest first: all drawers together, or only [drawerId]'s papers.
  Future<List<GlobalFeedPaperOut>> page({
    required int offset,
    int? drawerId,
  }) async {
    if (drawerId == null) {
      return _api.globalFeed(
        xUserId: _users.userId,
        limit: feedPageSize,
        offset: offset,
      );
    }
    final papers = await _api.promptFeed(
      promptId: drawerId,
      xUserId: _users.userId,
      limit: feedPageSize,
      offset: offset,
    );
    // One paper type for the screen: a drawer's paper is kept by that drawer.
    return [
      for (final p in papers)
        GlobalFeedPaperOut.fromJson({
          ...p.toJson(),
          'prompt_ids': [drawerId],
        }),
    ];
  }
}
