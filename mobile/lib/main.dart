import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'data/api/butine_api.dart';
import 'data/device_store.dart';
import 'data/repositories/drawer_repository.dart';
import 'data/repositories/feed_repository.dart';
import 'data/repositories/user_repository.dart';
import 'ui/core/theme.dart';
import 'ui/drawer/drawer_screen.dart';
import 'ui/drawer/drawer_view_model.dart';
import 'ui/drawer/new_drawer_screen.dart';
import 'ui/drawer/new_drawer_view_model.dart';
import 'ui/feed/feed_screen.dart';
import 'ui/feed/feed_view_model.dart';
import 'ui/onboarding/onboarding_screen.dart';
import 'ui/onboarding/onboarding_view_model.dart';
import 'ui/settings/settings_screen.dart';
import 'ui/settings/settings_view_model.dart';

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue:
      'http://10.0.2.2:8000', // the host's localhost, seen from the emulator
);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final api = ButineApi(http.Client(), baseUrl: Uri.parse(apiBaseUrl)).api;
  final store = DeviceStore();
  final users = UserRepository(api, store);
  await users.load();
  final themeMode = ValueNotifier(await store.themeMode());
  runApp(
    ButineApp(
      users: users,
      drawers: DrawerRepository(api, users),
      feed: FeedRepository(api, users),
      store: store,
      themeMode: themeMode,
    ),
  );
}

class ButineApp extends StatelessWidget {
  const ButineApp({
    super.key,
    required this.users,
    required this.drawers,
    required this.feed,
    required this.store,
    required this.themeMode,
  });

  final UserRepository users;
  final DrawerRepository drawers;
  final FeedRepository feed;
  final DeviceStore store;
  final ValueNotifier<ThemeMode> themeMode;

  Widget _feedScreen(BuildContext _) =>
      FeedScreen(viewModel: FeedViewModel(feed, drawers, store));

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(
      valueListenable: themeMode,
      builder: (context, mode, _) => MaterialApp(
        title: 'Butine',
        theme: lightTheme,
        darkTheme: darkTheme,
        themeMode: mode,
        home: users.userId == null
            ? OnboardingScreen(
                viewModel: OnboardingViewModel(users),
                drawers: drawers,
              )
            : _feedScreen(context),
        // Named, so the drawer screens can reach it without carrying repositories.
        routes: {
          '/feed': _feedScreen,
          '/new-drawer': (_) =>
              NewDrawerScreen(viewModel: NewDrawerViewModel(drawers)),
          '/settings': (_) =>
              SettingsScreen(viewModel: SettingsViewModel(store, themeMode)),
          '/drawer': (context) => DrawerScreen(
            viewModel: DrawerViewModel(
              drawers,
              ModalRoute.of(context)!.settings.arguments! as PromptOut,
            ),
          ),
        },
      ),
    );
  }
}
