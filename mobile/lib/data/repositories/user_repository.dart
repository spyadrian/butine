import '../api/butine_api.dart';
import '../device_store.dart';

/// The device's user. Its [userId] is the `X-User-Id` of every user request.
class UserRepository {
  UserRepository(this._api, this._store);

  final ApiClient _api;
  final DeviceStore _store;

  /// Null until the device has registered.
  String? userId;

  Future<void> load() async => userId = await _store.userId();

  Future<void> register() async {
    final user = await _api.createUser();
    await _store.saveUserId(user.id);
    userId = user.id;
  }
}
