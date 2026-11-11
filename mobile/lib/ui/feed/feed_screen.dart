import 'package:flutter/material.dart';

import 'drawer_pills.dart';
import 'feed_view_model.dart';
import 'paper_card.dart';

/// Main screen: the papers of every drawer, newest first.
class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key, required this.viewModel});

  final FeedViewModel viewModel;

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  FeedViewModel get vm => widget.viewModel;

  @override
  void initState() {
    super.initState();
    vm.open();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Butine'),
        actions: [
          // Without the pills, + would be out of reach.
          ListenableBuilder(
            listenable: vm,
            builder: (context, _) => vm.showPills || vm.loading
                ? const SizedBox.shrink()
                : const NewDrawerButton(),
          ),
        ],
      ),
      body: ListenableBuilder(
        listenable: vm,
        builder: (context, _) => Column(
          children: [
            if (vm.showPills)
              DrawerPills(
                drawers: vm.drawers,
                selectedId: vm.selected?.id,
                onSelected: vm.select,
              ),
            Expanded(child: _list(context)),
          ],
        ),
      ),
    );
  }

  Widget _list(BuildContext context) {
    // Under the pills, scrolling away with the papers: what is being shown.
    final header = vm.showPills ? 1 : 0;
    return NotificationListener<ScrollNotification>(
      onNotification: (n) {
        // Near the bottom; a failed page waits for Retry.
        if (n.metrics.extentAfter < 600 && vm.error == null) {
          vm.loadMore();
        }
        return false;
      },
      child: RefreshIndicator(
        onRefresh: vm.refresh,
        child: ListView.separated(
          // Pull to refresh works even when the list is short or empty.
          physics: const AlwaysScrollableScrollPhysics(),
          itemCount: header + vm.papers.length + 1,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (context, i) {
            if (i < header) return _header(context);
            i -= header;
            return i < vm.papers.length
                ? PaperCard(
                    paper: vm.papers[i],
                    drawers: vm.drawersOf(vm.papers[i]),
                    isNew: vm.isNew(vm.papers[i]),
                  )
                : _footer(context);
          },
        ),
      ),
    );
  }

  /// The selected drawer's prompt, or how many drawers All gathers.
  Widget _header(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
      child: Text(
        vm.selected?.text ?? '${vm.drawers.length} drawers',
        style: theme.textTheme.bodyMedium!.copyWith(
          color: theme.colorScheme.onSurfaceVariant,
        ),
      ),
    );
  }

  /// Below the last paper: what comes next, or why nothing does.
  Widget _footer(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final muted = theme.textTheme.bodyMedium!.copyWith(
      color: colors.onSurfaceVariant,
    );
    final Widget child;
    if (vm.error != null) {
      child = Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            color: colors.errorContainer,
            child: Text(
              'Could not reach Butine. Check your connection and try again.',
              style: TextStyle(color: colors.onErrorContainer),
            ),
          ),
          const SizedBox(height: 8),
          OutlinedButton(
            onPressed: vm.papers.isEmpty ? vm.refresh : vm.loadMore,
            child: const Text('Retry'),
          ),
        ],
      );
    } else if (vm.loading) {
      child = const Center(child: CircularProgressIndicator());
    } else if (vm.papers.isEmpty) {
      child = Text(
        vm.reading ? 'Butine is reading the latest papers…' : 'No papers yet',
        textAlign: TextAlign.center,
        style: theme.textTheme.bodyLarge,
      );
    } else if (vm.done) {
      child = Text(
        "That's all for now",
        textAlign: TextAlign.center,
        style: muted,
      );
    } else {
      return const SizedBox(height: 48);
    }
    return Padding(padding: const EdgeInsets.all(24), child: child);
  }
}
