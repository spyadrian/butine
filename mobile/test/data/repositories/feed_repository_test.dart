import 'dart:convert';

import 'package:butine/data/api/butine_api.dart';
import 'package:butine/data/repositories/feed_repository.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import '../../ui/onboarding/onboarding_test.dart' show FakeUserRepository;

void main() {
  test('page asks the global feed for 50 papers as the device user', () async {
    final calls = <http.Request>[];
    final feed = FeedRepository(
      ButineApi(
        MockClient((request) async {
          calls.add(request);
          return http.Response('[]', 200);
        }),
        baseUrl: Uri.parse('http://test'),
      ).api,
      FakeUserRepository()..userId = 'u-1',
    );

    expect(await feed.page(offset: 100), isEmpty);

    final request = calls.single;
    expect(request.url.path, '/v1/feed');
    expect(request.url.queryParameters, {'limit': '50', 'offset': '100'});
    expect(request.headers['x-user-id'], 'u-1');
  });

  test("a drawer's page comes from its feed, tagged with the drawer", () async {
    final calls = <http.Request>[];
    final feed = FeedRepository(
      ButineApi(
        MockClient((request) async {
          calls.add(request);
          return http.Response(
            jsonEncode([
              {
                'external_id': 'p0',
                'version': 1,
                'title': 'Paper 0',
                'authors': ['Ada Lovelace'],
                'abstract': 'Abstract',
                'categories': ['cs.LG'],
                'link': 'https://arxiv.org/abs/p0',
                'published_at': null,
                'fetched_at': '2026-11-10T06:00:00Z',
                'source': 'arXiv',
                'score': 0.8,
              },
            ]),
            200,
            headers: {'content-type': 'application/json'},
          );
        }),
        baseUrl: Uri.parse('http://test'),
      ).api,
      FakeUserRepository()..userId = 'u-1',
    );

    final page = await feed.page(offset: 50, drawerId: 7);

    expect(calls.single.url.path, '/v1/prompts/7/feed');
    expect(calls.single.url.queryParameters, {'limit': '50', 'offset': '50'});
    expect(calls.single.headers['x-user-id'], 'u-1');
    expect(page.single.title, 'Paper 0');
    expect(page.single.promptIds, [7]);
  });
}
