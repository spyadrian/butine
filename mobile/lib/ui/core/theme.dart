import 'package:flutter/material.dart';

/// Brand colors from design/logo/palette.json (rules in docs/BRAND.md).
/// The only place in the app where colors are written by hand.
abstract final class ButineColors {
  static const honey = Color(0xFFF2A93B);
  static const honeyDeep = Color(0xFFB9781A);
  static const anthracite = Color(0xFF2B2520);
  static const offwhite = Color(0xFFFAF6EE);
  static const night = Color(0xFF1C1815);
  static const greyLight = Color(0xFF766C62);
  static const greyDark = Color(0xFFA39A90);
  static const error = Color(0xFFA23B4E);
  static const errorDark = Color(0xFFE97F86);
  static const errorTint = Color(0xFFF7E7E6);
  static const errorTintDark = Color(0xFF3A2326);
}

/// Interface font; papers (titles, abstracts) use [paperFontFamily].
const uiFontFamily = 'Inter';
const paperFontFamily = 'Literata';

/// The "New" dot: honey only holds on light backgrounds as deep honey (BRAND.md).
Color newSignalColor(ColorScheme scheme) =>
    scheme.brightness == Brightness.light
    ? ButineColors.honeyDeep
    : ButineColors.honey;

final lightTheme = _theme(
  Brightness.light,
  background: ButineColors.offwhite,
  text: ButineColors.anthracite,
  metadata: ButineColors.greyLight,
  // Honey fails as text on the light background, so accents stay anthracite.
  primary: ButineColors.anthracite,
  onPrimary: ButineColors.offwhite,
  error: ButineColors.error,
  onError: ButineColors.offwhite,
  errorTint: ButineColors.errorTint,
);

final darkTheme = _theme(
  Brightness.dark,
  background: ButineColors.night,
  text: ButineColors.offwhite,
  metadata: ButineColors.greyDark,
  primary: ButineColors.honey,
  onPrimary: ButineColors.anthracite,
  error: ButineColors.errorDark,
  onError: ButineColors.night,
  errorTint: ButineColors.errorTintDark,
);

ThemeData _theme(
  Brightness brightness, {
  required Color background,
  required Color text,
  required Color metadata,
  required Color primary,
  required Color onPrimary,
  required Color error,
  required Color onError,
  required Color errorTint,
}) {
  // The seed fills the tones we don't set (surface containers…) with warm neutrals.
  final scheme =
      ColorScheme.fromSeed(
        seedColor: ButineColors.honey,
        brightness: brightness,
        dynamicSchemeVariant: DynamicSchemeVariant.neutral,
      ).copyWith(
        surface: background,
        onSurface: text,
        onSurfaceVariant: metadata,
        outline: metadata,
        primary: primary,
        onPrimary: onPrimary,
        // Honey is rare: main button and the "New" signal only, always with dark text.
        primaryContainer: ButineColors.honey,
        onPrimaryContainer: ButineColors.anthracite,
        error: error,
        onError: onError,
        errorContainer: errorTint,
        onErrorContainer: error,
      );
  return ThemeData(
    colorScheme: scheme,
    scaffoldBackgroundColor: background,
    fontFamily: uiFontFamily,
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: scheme.primaryContainer,
        foregroundColor: scheme.onPrimaryContainer,
      ),
    ),
  );
}
