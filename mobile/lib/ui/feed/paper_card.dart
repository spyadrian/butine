import 'package:flutter/material.dart';

import '../../data/api/butine_api.dart';
import '../core/drawer_icons.dart';
import '../core/theme.dart';

class PaperCard extends StatelessWidget {
  const PaperCard({super.key, required this.paper, this.drawers = const []});

  final GlobalFeedPaperOut paper;

  /// The drawers that kept it, named under the date.
  final List<PromptOut> drawers;

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
          if (drawers.isNotEmpty) ...[
            const SizedBox(height: 4),
            Wrap(
              spacing: 12,
              children: [
                for (final d in drawers)
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(drawerIcon(d.icon), size: 16, color: meta.color),
                      const SizedBox(width: 4),
                      Text(d.name, style: meta),
                    ],
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
