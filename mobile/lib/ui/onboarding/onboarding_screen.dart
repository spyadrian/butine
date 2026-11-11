import 'package:flutter/material.dart';

import '../../data/repositories/drawer_repository.dart';
import '../drawer/new_drawer_screen.dart';
import '../drawer/new_drawer_view_model.dart';
import 'onboarding_view_model.dart';

/// First launch: presents Butine, registers the device, then opens the
/// creation of the first drawer.
class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({
    super.key,
    required this.viewModel,
    required this.drawers,
  });

  final OnboardingViewModel viewModel;
  final DrawerRepository drawers;

  Future<void> _start(BuildContext context) async {
    await viewModel.register();
    if (viewModel.error == null && context.mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute<void>(
          builder: (_) =>
              NewDrawerScreen(viewModel: NewDrawerViewModel(drawers)),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: ListenableBuilder(
            listenable: viewModel,
            builder: (context, _) => Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Spacer(),
                Text('Butine', style: theme.textTheme.headlineMedium),
                const SizedBox(height: 16),
                Text(
                  'Butine reads arXiv and bioRxiv every day and keeps the '
                  'papers that match what you follow.',
                  style: theme.textTheme.bodyLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  'Each drawer follows one topic, described in a few words.',
                  style: theme.textTheme.bodyLarge!.copyWith(
                    color: colors.onSurfaceVariant,
                  ),
                ),
                const Spacer(),
                if (viewModel.error != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    color: colors.errorContainer,
                    child: Text(
                      'Could not reach Butine. Check your connection and try again.',
                      style: TextStyle(color: colors.onErrorContainer),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                FilledButton(
                  onPressed: viewModel.loading ? null : () => _start(context),
                  child: viewModel.loading
                      ? const SizedBox.square(
                          dimension: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(
                          viewModel.error == null
                              ? 'Create my first drawer'
                              : 'Retry',
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
