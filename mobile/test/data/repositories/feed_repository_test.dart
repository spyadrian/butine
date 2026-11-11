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
}
