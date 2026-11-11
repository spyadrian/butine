import 'package:butine/ui/core/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// WCAG 2 contrast ratio between two opaque colors.
double contrast(Color a, Color b) {
  final la = a.computeLuminance(), lb = b.computeLuminance();
  return (la > lb ? la + 0.05 : lb + 0.05) / (la > lb ? lb + 0.05 : la + 0.05);
}

void main() {
  test('contrast matches the ratios published in BRAND.md', () {
    expect(
      contrast(ButineColors.anthracite, ButineColors.offwhite),
      closeTo(14.0, 0.05),
    );
    expect(
      contrast(ButineColors.honey, ButineColors.offwhite),
      closeTo(1.9, 0.05),
    );
  });

  for (final (name, theme) in [('light', lightTheme), ('dark', darkTheme)]) {
    group('$name theme', () {
      final s = theme.colorScheme;
      final textPairs = {
        'text on background': (s.onSurface, s.surface),
        'metadata on background': (s.onSurfaceVariant, s.surface),
        'text on primary': (s.onPrimary, s.primary),
        'text on honey': (s.onPrimaryContainer, s.primaryContainer),
        'error on background': (s.error, s.surface),
        'text on error': (s.onError, s.error),
        'error on its tint': (s.onErrorContainer, s.errorContainer),
      };
      textPairs.forEach((pair, colors) {
        test('$pair passes AA (4.5:1)', () {
          expect(contrast(colors.$1, colors.$2), greaterThanOrEqualTo(4.5));
        });
      });

      test('outline passes AA for UI elements (3:1)', () {
        expect(contrast(s.outline, s.surface), greaterThanOrEqualTo(3));
      });

      test('main button is honey with dark text', () {
        expect(s.primaryContainer, ButineColors.honey);
        expect(s.onPrimaryContainer, ButineColors.anthracite);
      });

      test('the New signal passes AA for UI elements (3:1)', () {
        expect(contrast(newSignalColor(s), s.surface), greaterThanOrEqualTo(3));
      });

      test('uses Inter for the interface', () {
        expect(theme.textTheme.bodyMedium!.fontFamily, 'Inter');
        expect(theme.textTheme.labelLarge!.fontFamily, 'Inter');
      });
    });
  }

  test('New is deep honey on light, honey on dark', () {
    expect(newSignalColor(lightTheme.colorScheme), ButineColors.honeyDeep);
    expect(newSignalColor(darkTheme.colorScheme), ButineColors.honey);
  });

  test('never uses honey as text or icon color on the light background', () {
    final s = lightTheme.colorScheme;
    expect([
      s.primary,
      s.onSurface,
      s.onSurfaceVariant,
      s.error,
    ], isNot(contains(ButineColors.honey)));
  });
}
