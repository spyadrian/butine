import 'dart:convert';

import 'package:butine/data/api/butine_api.dart';
import 'package:butine/data/device_store.dart';
import 'package:butine/data/repositories/user_repository.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class FakeDeviceStore implements DeviceStore {
  String? saved;

  @override
  Future<String?> userId() async => saved;

  @override
  Future<void> saveUserId(String id) async => saved = id;
}

void main() {
  test('register creates a user and keeps its id', () async {
    final calls = <http.Request>[];
    final api = ButineApi(
      MockClient((request) async {
        calls.add(request);
        return http.Response(
          jsonEncode({'id': 'u-1', 'plan': 'free'}),
          201,
          headers: {'content-type': 'application/json'},
        );
      }),
      baseUrl: Uri.parse('http://test'),
    ).api;
    final store = FakeDeviceStore();
    final users = UserRepository(api, store);

    await users.register();

    expect(calls.single.method, 'POST');
    expect(calls.single.url.path, '/v1/users');
    expect(users.userId, 'u-1');
    expect(store.saved, 'u-1');
  });

  test('load restores the saved id without calling the API', () async {
    final api = ButineApi(
      MockClient((_) async => fail('no request expected')),
      baseUrl: Uri.parse('http://test'),
    ).api;
    final users = UserRepository(api, FakeDeviceStore()..saved = 'u-2');

    await users.load();

    expect(users.userId, 'u-2');
  });
}
