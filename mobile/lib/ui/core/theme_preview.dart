import 'package:flutter/material.dart';
import 'package:flutter/widget_previews.dart';

import 'theme.dart';

/// A sample of every theme token, to check the theme by eye.
class ThemeSpecimen extends StatelessWidget {
  const ThemeSpecimen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final text = theme.textTheme;
    final colors = theme.colorScheme;
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Butine', style: text.headlineMedium),
            const SizedBox(height: 16),
            Text(
              'Attention is all you need',
              style: text.titleLarge!.copyWith(
                fontFamily: paperFontFamily,
                fontWeight: FontWeight.w600,
              ),
            ),
            Text(
              'A. Vaswani, N. Shazeer · arXiv · 2017-06-12',
              style: text.bodySmall!.copyWith(color: colors.onSurfaceVariant),
            ),
            const SizedBox(height: 8),
            Text(
              'The dominant sequence transduction models are based on complex recurrent or '
              'convolutional neural networks that include an encoder and a decoder.',
              style: text.bodyLarge!.copyWith(fontFamily: paperFontFamily),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              children: [
                FilledButton(
                  onPressed: () {},
                  child: const Text('Create a drawer'),
                ),
                TextButton(onPressed: () {}, child: const Text('Cancel')),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              color: colors.errorContainer,
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: colors.onErrorContainer),
                  const SizedBox(width: 8),
                  Text(
                    'Could not reach the server.',
                    style: TextStyle(color: colors.onErrorContainer),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

@Preview(group: 'Theme', name: 'Light')
Widget lightThemePreview() =>
    Theme(data: lightTheme, child: const ThemeSpecimen());

@Preview(group: 'Theme', name: 'Dark')
Widget darkThemePreview() =>
    Theme(data: darkTheme, child: const ThemeSpecimen());
