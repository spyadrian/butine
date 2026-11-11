import 'package:flutter/foundation.dart';

import '../../data/repositories/drawer_repository.dart';
import '../core/drawer_icons.dart';

/// Same bounds as the API, after trimming.
const maxNameLength = 24;
const maxPromptLength = 500;

class NewDrawerViewModel extends ChangeNotifier {
  NewDrawerViewModel(this._drawers);

  final DrawerRepository _drawers;

  String name = '';
  String icon = defaultDrawerIcon;
  String text = '';
  bool saving = false;
  Object? error;

  bool get canSubmit {
    final n = name.trim().length, t = text.trim().length;
    return n >= 1 && n <= maxNameLength && t >= 1 && t <= maxPromptLength;
  }

  /// Field setters go through here so the Create button follows them.
  void update(VoidCallback change) {
    change();
    notifyListeners();
  }

  /// True once the drawer exists.
  Future<bool> submit() async {
    if (saving || !canSubmit) return false;
    saving = true;
    error = null;
    notifyListeners();
    try {
      await _drawers.create(name: name.trim(), icon: icon, text: text.trim());
      return true;
    } catch (e) {
      error = e;
      return false;
    } finally {
      saving = false;
      notifyListeners();
    }
  }
}
