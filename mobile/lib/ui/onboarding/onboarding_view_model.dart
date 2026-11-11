import 'package:flutter/foundation.dart';

import '../../data/repositories/user_repository.dart';

class OnboardingViewModel extends ChangeNotifier {
  OnboardingViewModel(this._users);

  final UserRepository _users;
  bool loading = false;
  Object? error;

  Future<void> register() async {
    if (loading) return;
    loading = true;
    error = null;
    notifyListeners();
    try {
      await _users.register();
    } catch (e) {
      error = e; // shown with Retry
    } finally {
      loading = false;
      notifyListeners();
    }
  }
}
