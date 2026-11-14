import 'package:flutter/material.dart';

import '../core/drawer_icons.dart';
import 'drawer_view_model.dart';

/// One drawer: what it holds, and Delete. Pops with true once deleted.
class DrawerScreen extends StatelessWidget {
  const DrawerScreen({super.key, required this.viewModel});

  final DrawerViewModel viewModel;

  Future<void> _delete(BuildContext context) async {
    final navigator = Navigator.of(context);
    if (await viewModel.delete()) navigator.pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final d = viewModel.drawer;
    return Scaffold(
      appBar: AppBar(),
      body: ListenableBuilder(
        listenable: viewModel,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
          children: [
            Row(
              children: [
                Icon(drawerIcon(d.icon), size: 32, color: colors.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(d.name, style: theme.textTheme.headlineSmall),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              d.status == 'pending'
                  ? 'Butine is reading the latest papers…'
                  : 'Ready',
              style: theme.textTheme.bodyMedium!.copyWith(
                color: colors.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            Text('Prompt', style: theme.textTheme.titleSmall),
            const SizedBox(height: 8),
            Text(d.text, style: theme.textTheme.bodyLarge),
            const SizedBox(height: 32),
            if (viewModel.error != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                color: colors.errorContainer,
                child: Text(
                  'Could not reach Butine. Check your connection and try again.',
                  style: TextStyle(color: colors.onErrorContainer),
                ),
              ),
              const SizedBox(height: 8),
              FilledButton(
                onPressed: viewModel.deleting ? null : () => _delete(context),
                child: const Text('Retry'),
              ),
            ] else if (viewModel.confirming) ...[
              Text(
                'Delete this drawer? Its papers leave your feed.',
                style: theme.textTheme.bodyLarge,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: viewModel.deleting
                          ? null
                          : () => viewModel.askToDelete(false),
                      child: const Text('Cancel'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      style: FilledButton.styleFrom(
                        backgroundColor: colors.error,
                        foregroundColor: colors.onError,
                      ),
                      onPressed: viewModel.deleting
                          ? null
                          : () => _delete(context),
                      child: const Text('Delete'),
                    ),
                  ),
                ],
              ),
            ] else
              OutlinedButton(
                style: OutlinedButton.styleFrom(foregroundColor: colors.error),
                onPressed: () => viewModel.askToDelete(true),
                child: const Text('Delete'),
              ),
          ],
        ),
      ),
    );
  }
}
