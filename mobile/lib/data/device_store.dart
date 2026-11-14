import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// What the app keeps on the device between launches.
class DeviceStore {
  DeviceStore([this._secure = const FlutterSecureStorage()]);

  final FlutterSecureStorage _secure;

  static const _userIdKey = 'user_id';
  static const _feedOpenKey = 'feed_opened_at';
  static const _themeKey = 'theme_mode';

  Future<String?> userId() => _secure.read(key: _userIdKey);

  Future<void> saveUserId(String id) =>
      _secure.write(key: _userIdKey, value: id);

  /// When the feed was last opened; papers fetched since are New.
  Future<DateTime?> lastFeedOpen() async {
    final at = await _secure.read(key: _feedOpenKey);
    return at == null ? null : DateTime.tryParse(at);
  }

  Future<void> saveLastFeedOpen(DateTime at) =>
      _secure.write(key: _feedOpenKey, value: at.toUtc().toIso8601String());

  /// The theme picked in Settings; the system's until one is.
  Future<ThemeMode> themeMode() async {
    final name = await _secure.read(key: _themeKey);
    return ThemeMode.values.asNameMap()[name] ?? ThemeMode.system;
  }

  Future<void> saveThemeMode(ThemeMode mode) =>
      _secure.write(key: _themeKey, value: mode.name);
}
