import 'package:http/http.dart' as http;

import '../api/butine_api.dart';
import 'user_repository.dart';

/// The user's plan does not allow one more drawer (`403`).
class DrawerLimitReached implements Exception {
  const DrawerLimitReached();
}

/// The user's drawers, stored as prompts by the API.
class DrawerRepository {
  DrawerRepository(this._api, this._users);

  final ApiClient _api;
  final UserRepository _users;

  /// In creation order.
  Future<List<PromptOut>> list() => _api.listPrompts(xUserId: _users.userId);

  Future<PromptOut> create({
    required String name,
    required String icon,
    required String text,
  }) async {
    try {
      return await _api.createPrompt(
        xUserId: _users.userId,
        body: PromptIn(name: name, icon: icon, text: text),
      );
    } on http.ClientException catch (e) {
      // The generated client only keeps the status in its message.
      if (e.message == 'HTTP 403') throw const DrawerLimitReached();
      rethrow;
    }
  }
}
