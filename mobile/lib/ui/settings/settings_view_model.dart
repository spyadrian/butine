import 'package:flutter/material.dart';

import '../../data/device_store.dart';

class SettingsViewModel {
  SettingsViewModel(this._store, this.themeMode);

  final DeviceStore _store;

  /// Shared with the app: setting it repaints every screen.
  final ValueNotifier<ThemeMode> themeMode;

  Future<void> setThemeMode(ThemeMode mode) {
    themeMode.value = mode;
    return _store.saveThemeMode(mode);
  }
}
