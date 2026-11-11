import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// What the app keeps on the device between launches.
class DeviceStore {
  DeviceStore([this._secure = const FlutterSecureStorage()]);

  final FlutterSecureStorage _secure;

  static const _userIdKey = 'user_id';

  Future<String?> userId() => _secure.read(key: _userIdKey);

  Future<void> saveUserId(String id) =>
      _secure.write(key: _userIdKey, value: id);
}
