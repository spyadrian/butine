import 'package:butine/ui/core/drawer_icons.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('every id is a valid prompts.icon value', () {
    final valid = RegExp(r'^[a-z0-9_]{1,40}$');
    for (final id in drawerIcons.keys) {
      expect(valid.hasMatch(id), isTrue, reason: id);
    }
  });

  test('the set holds about 24 distinct icons', () {
    expect(drawerIcons.length, inInclusiveRange(20, 28));
    expect(drawerIcons.values.toSet().length, drawerIcons.length);
  });

  test('the migration default "label" is in the set', () {
    expect(drawerIcons, contains(defaultDrawerIcon));
    expect(defaultDrawerIcon, 'label');
  });

  test('a known id gives its icon, an unknown id the default one', () {
    expect(drawerIcon('science'), Icons.science_outlined);
    expect(drawerIcon('no_such_icon'), drawerIcons[defaultDrawerIcon]);
  });
}
