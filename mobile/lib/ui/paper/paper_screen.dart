import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../data/api/butine_api.dart';
import '../core/drawer_icons.dart';
import '../core/theme.dart';

/// One paper in full, from the card's data: no network call.
class PaperScreen extends StatelessWidget {
  const PaperScreen({
    super.key,
    required this.paper,
    this.drawers = const [],
    this.openLink = launchUrl,
  });

  final GlobalFeedPaperOut paper;

  /// The drawers that kept it.
  final List<PromptOut> drawers;

  /// Opens the paper's page in the browser; swapped out in tests.
  final Future<bool> Function(Uri) openLink;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final meta = theme.textTheme.bodyMedium!.copyWith(
      color: theme.colorScheme.onSurfaceVariant,
    );
    final date = paper.publishedAt.asString ?? paper.fetchedAt;
    // "arXiv — Computer Science" → "arXiv"
    final site = paper.source.split(' — ').first;
    return Scaffold(
      appBar: AppBar(),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
        children: [
          Text(
            paper.title,
            style: theme.textTheme.headlineSmall!.copyWith(
              fontFamily: paperFontFamily,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          Text(paper.authors.join(', '), style: meta),
          const SizedBox(height: 4),
          Text(
            '${paper.source} · '
            '${MaterialLocalizations.of(context).formatMediumDate(date)}',
            style: meta,
          ),
          if (drawers.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 12,
              runSpacing: 4,
              children: [
                for (final d in drawers)
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(drawerIcon(d.icon), size: 18, color: meta.color),
                      const SizedBox(width: 4),
                      Text(d.name, style: meta),
                    ],
                  ),
              ],
            ),
          ],
          const SizedBox(height: 20),
          Text(
            paper.abstract2,
            style: theme.textTheme.bodyLarge!.copyWith(
              fontFamily: paperFontFamily,
              height: 1.6,
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton(
            onPressed: () => openLink(Uri.parse(paper.link)),
            child: Text('Read on $site'),
          ),
        ),
      ),
    );
  }
}
