import 'package:flutter/material.dart';

import '../../data/repositories/drawer_repository.dart';
import '../core/drawer_icons.dart';
import 'new_drawer_view_model.dart';

/// Short, precise prompts: they show what a good one looks like.
const promptExamples = [
  'Solid-state battery electrolytes',
  'CRISPR base editing in human cells',
  'Graph neural networks for molecules',
  'Perovskite solar cell stability',
];

class NewDrawerScreen extends StatefulWidget {
  const NewDrawerScreen({super.key, required this.viewModel});

  final NewDrawerViewModel viewModel;

  @override
  State<NewDrawerScreen> createState() => _NewDrawerScreenState();
}

class _NewDrawerScreenState extends State<NewDrawerScreen> {
  final _prompt = TextEditingController();

  NewDrawerViewModel get vm => widget.viewModel;

  @override
  void dispose() {
    _prompt.dispose();
    super.dispose();
  }

  Future<void> _create() async {
    if (await vm.submit() && mounted) {
      Navigator.of(context).pushNamedAndRemoveUntil('/feed', (_) => false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('New drawer')),
      body: ListenableBuilder(
        listenable: vm,
        builder: (context, _) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  TextField(
                    decoration: const InputDecoration(labelText: 'Name'),
                    maxLength: maxNameLength,
                    textCapitalization: TextCapitalization.sentences,
                    onChanged: (v) => vm.update(() => vm.name = v),
                  ),
                  const SizedBox(height: 16),
                  Text('Icon', style: theme.textTheme.titleSmall),
                  const SizedBox(height: 8),
                  Wrap(
                    children: [
                      for (final MapEntry(key: id, value: icon)
                          in drawerIcons.entries)
                        id == vm.icon
                            ? IconButton.filled(
                                tooltip: id,
                                icon: Icon(icon),
                                onPressed: () {},
                              )
                            : IconButton(
                                tooltip: id,
                                icon: Icon(icon),
                                onPressed: () => vm.update(() => vm.icon = id),
                              ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  TextField(
                    controller: _prompt,
                    decoration: const InputDecoration(
                      labelText: 'Prompt',
                      hintText: 'What should this drawer follow?',
                      alignLabelWithHint: true,
                    ),
                    maxLength: maxPromptLength,
                    minLines: 3,
                    maxLines: 6,
                    onChanged: (v) => vm.update(() => vm.text = v),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Examples',
                    style: theme.textTheme.titleSmall!.copyWith(
                      color: colors.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final example in promptExamples)
                        ActionChip(
                          label: Text(example),
                          onPressed: () => vm.update(() {
                            _prompt.text = example;
                            vm.text = example;
                          }),
                        ),
                    ],
                  ),
                ],
              ),
            ),
            // Kept out of the list so Create stays on screen.
            SafeArea(
              top: false,
              minimum: const EdgeInsets.fromLTRB(24, 8, 24, 16),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (vm.error != null) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      color: colors.errorContainer,
                      child: Text(
                        vm.error is DrawerLimitReached
                            ? 'The free plan includes 1 drawer.'
                            : 'Could not reach Butine. Check your connection and try again.',
                        style: TextStyle(color: colors.onErrorContainer),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  FilledButton(
                    onPressed: vm.canSubmit && !vm.saving ? _create : null,
                    child: vm.saving
                        ? const SizedBox.square(
                            dimension: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Create'),
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
