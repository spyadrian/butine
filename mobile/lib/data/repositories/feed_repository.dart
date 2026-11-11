import '../api/butine_api.dart';
import 'user_repository.dart';

const feedPageSize = 50;

/// The papers kept for the user's drawers.
class FeedRepository {
  FeedRepository(this._api, this._users);

  final ApiClient _api;
  final UserRepository _users;

  /// All drawers together, newest first.
  Future<List<GlobalFeedPaperOut>> page({required int offset}) => _api
      .globalFeed(xUserId: _users.userId, limit: feedPageSize, offset: offset);
}
