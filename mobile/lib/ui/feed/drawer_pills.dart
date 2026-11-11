import 'package:flutter/material.dart';

import '../../data/api/butine_api.dart';
import '../core/drawer_icons.dart';

/// All, one pill per drawer, then + to create one. Scrolls sideways.
class DrawerPills extends StatelessWidget {
  const DrawerPills({
    super.key,
    required this.drawers,
    required this.selectedId,
    required this.onSelected,
  });

  final List<PromptOut> drawers;
  final int? selectedId; // null is All
  final ValueChanged<int?> onSelected;

  @override
  Widget build(BuildContext context) {
    Widget pill(int? id, String label, [IconData? icon]) => ChoiceChip(
      label: Text(label),
      avatar: icon == null ? null : Icon(icon),
      showCheckmark: false,
      selected: selectedId == id,
      onSelected: (_) => onSelected(id),
    );
    return SizedBox(
      height: 56,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          for (final w in [
            pill(null, 'All'),
            for (final d in drawers) pill(d.id, d.name, drawerIcon(d.icon)),
          ])
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(child: w), // a sideways list stretches its children
            ),
          Center(
            child: ActionChip(
              tooltip: 'New drawer',
              label: const Icon(Icons.add, size: 18),
              onPressed: () => Navigator.of(context).pushNamed('/new-drawer'),
            ),
          ),
        ],
      ),
    );
  }
}

/// Opens the new drawer screen from the app bar, when the pills are hidden.
class NewDrawerButton extends StatelessWidget {
  const NewDrawerButton({super.key});

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: 'New drawer',
    icon: const Icon(Icons.add),
    onPressed: () => Navigator.of(context).pushNamed('/new-drawer'),
  );
}
