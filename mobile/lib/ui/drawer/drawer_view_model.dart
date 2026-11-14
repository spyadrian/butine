import 'package:flutter/foundation.dart';

import '../../data/api/butine_api.dart';
import '../../data/repositories/drawer_repository.dart';

class DrawerViewModel extends ChangeNotifier {
  DrawerViewModel(this._drawers, this.drawer);

  final DrawerRepository _drawers;
  final PromptOut drawer;

  /// Delete was pressed once: the screen asks to confirm.
  bool confirming = false;
  bool deleting = false;
  Object? error;

  void askToDelete(bool ask) {
    confirming = ask;
    error = null;
    notifyListeners();
  }

  /// True once the drawer is gone.
  Future<bool> delete() async {
    if (deleting) return false;
    deleting = true;
    error = null;
    notifyListeners();
    try {
      await _drawers.delete(drawer.id);
      return true;
    } catch (e) {
      error = e;
      return false;
    } finally {
      deleting = false;
      notifyListeners();
    }
  }
}
