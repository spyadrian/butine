import 'dart:convert';

import 'package:butine/data/api/butine_api.dart';
import 'package:butine/data/repositories/drawer_repository.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import '../../ui/onboarding/onboarding_test.dart' show FakeUserRepository;

DrawerRepository drawersAnswering(int status, [List<http.Request>? calls]) =>
    DrawerRepository(
      ButineApi(
        MockClient((request) async {
          calls?.add(request);
          return http.Response(
            jsonEncode({
              'id': 1,
              'name': 'Batteries',
              'icon': 'bolt',
              'text': 'Solid-state electrolytes',
              'created_at': '2026-11-11T08:00:00Z',
              'status': 'pending',
            }),
            status,
            headers: {'content-type': 'application/json'},
          );
        }),
        baseUrl: Uri.parse('http://test'),
      ).api,
      FakeUserRepository()..userId = 'u-1',
    );

void main() {
  test('create posts the drawer as the device user', () async {
    final calls = <http.Request>[];

    await drawersAnswering(
      201,
      calls,
    ).create(name: 'Batteries', icon: 'bolt', text: 'Solid-state electrolytes');

    final request = calls.single;
    expect(request.method, 'POST');
    expect(request.url.path, '/v1/prompts');
    expect(request.headers['x-user-id'], 'u-1');
    expect(jsonDecode(request.body), {
      'name': 'Batteries',
      'icon': 'bolt',
      'text': 'Solid-state electrolytes',
    });
  });

  test('a 403 means the plan limit is reached', () async {
    expect(
      drawersAnswering(403).create(name: 'a', icon: 'bolt', text: 'b'),
      throwsA(isA<DrawerLimitReached>()),
    );
  });

  test('other failures stay client exceptions', () async {
    expect(
      drawersAnswering(500).create(name: 'a', icon: 'bolt', text: 'b'),
      throwsA(isA<http.ClientException>()),
    );
  });
}
