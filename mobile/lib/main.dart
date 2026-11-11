import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'data/api/butine_api.dart';
import 'data/device_store.dart';
import 'data/repositories/user_repository.dart';
import 'ui/core/theme.dart';
import 'ui/core/theme_preview.dart';
import 'ui/onboarding/onboarding_screen.dart';
import 'ui/onboarding/onboarding_view_model.dart';

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue:
      'http://10.0.2.2:8000', // the host's localhost, seen from the emulator
);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final api = ButineApi(http.Client(), baseUrl: Uri.parse(apiBaseUrl)).api;
  final users = UserRepository(api, DeviceStore());
  await users.load();
  runApp(ButineApp(users: users));
}

class ButineApp extends StatelessWidget {
  const ButineApp({super.key, required this.users});

  final UserRepository users;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Butine',
      theme: lightTheme,
      darkTheme: darkTheme,
      home: users.userId == null
          ? OnboardingScreen(viewModel: OnboardingViewModel(users))
          // shortcut: the theme specimen stands in for the feed until it exists.
          : const ThemeSpecimen(),
    );
  }
}
