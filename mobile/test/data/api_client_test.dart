import 'dart:convert';
import 'dart:io';

import 'package:butine/data/api/butine_api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

void main() {
  test('globalFeed sends the user id and decodes a feed', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => server.close(force: true));
    late HttpRequest seen;
    server.listen((request) {
      seen = request;
      request.response
        ..headers.contentType = ContentType.json
        ..write(
          jsonEncode([
            {
              'external_id': '2511.00001',
              'version': 1,
              'title': 'Solid-state batteries',
              'authors': ['Øystein Kvalvåg'],
              'abstract': 'We study…',
              'categories': ['cond-mat'],
              'link': 'https://arxiv.org/abs/2511.00001',
              'published_at': null,
              'fetched_at': '2026-11-10T08:00:00Z',
              'source': 'arxiv',
              'score': 0.82,
              'prompt_ids': [3],
            },
          ]),
        )
        ..close();
    });
    final client = http.Client();
    addTearDown(client.close);
    final api = ButineApi(
      client,
      baseUrl: Uri.parse('http://${server.address.host}:${server.port}'),
    ).api;

    final feed = await api.globalFeed(xUserId: 'u-1', limit: 50, offset: 0);

    expect(seen.uri.path, '/v1/feed');
    expect(seen.uri.queryParameters, {'limit': '50', 'offset': '0'});
    expect(seen.headers.value('x-user-id'), 'u-1');
    final paper = feed.single;
    expect(paper.title, 'Solid-state batteries');
    expect(paper.authors, ['Øystein Kvalvåg']);
    expect(paper.publishedAt.hasNull, isTrue);
    expect(paper.fetchedAt, DateTime.utc(2026, 11, 10, 8));
    expect(paper.promptIds, [3]);
  });
}
