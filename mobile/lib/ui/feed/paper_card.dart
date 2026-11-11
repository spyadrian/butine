import 'package:flutter/material.dart';

import '../../data/api/butine_api.dart';
import '../core/theme.dart';

class PaperCard extends StatelessWidget {
  const PaperCard({super.key, required this.paper});

  final GlobalFeedPaperOut paper;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final meta = theme.textTheme.bodySmall!.copyWith(
      color: theme.colorScheme.onSurfaceVariant,
    );
    // Some bioRxiv items have no publication date: fall back to when Butine read them.
    final date = paper.publishedAt.asString ?? paper.fetchedAt;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            paper.title,
            style: theme.textTheme.titleMedium!.copyWith(
              fontFamily: paperFontFamily,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            paper.authors.join(', '),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: meta,
          ),
          Text(
            '${paper.source} · '
            '${MaterialLocalizations.of(context).formatMediumDate(date)}',
            style: meta,
          ),
        ],
      ),
    );
  }
}
