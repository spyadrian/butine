import 'package:butine/data/device_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('the theme follows the system until one is chosen', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final store = DeviceStore();
    expect(await store.themeMode(), ThemeMode.system);

    await store.saveThemeMode(ThemeMode.dark);
    expect(await DeviceStore().themeMode(), ThemeMode.dark);
  });

  test('an unknown saved theme falls back to the system', () async {
    FlutterSecureStorage.setMockInitialValues({'theme_mode': 'sepia'});
    expect(await DeviceStore().themeMode(), ThemeMode.system);
  });
}
