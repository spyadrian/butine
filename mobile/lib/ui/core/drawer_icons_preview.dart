import 'package:flutter/material.dart';
import 'package:flutter/widget_previews.dart';

import 'drawer_icons.dart';
import 'theme.dart';

/// Every drawer icon with its id, to review the set by eye.
class DrawerIconsSpecimen extends StatelessWidget {
  const DrawerIconsSpecimen({super.key});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme.labelSmall;
    return Scaffold(
      body: GridView.extent(
        maxCrossAxisExtent: 112,
        padding: const EdgeInsets.all(16),
        children: [
          for (final MapEntry(key: id, value: icon) in drawerIcons.entries)
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 32),
                const SizedBox(height: 8),
                Text(id, style: text, textAlign: TextAlign.center),
              ],
            ),
        ],
      ),
    );
  }
}

@Preview(group: 'Drawer icons', name: 'Light')
Widget lightDrawerIconsPreview() =>
    Theme(data: lightTheme, child: const DrawerIconsSpecimen());

@Preview(group: 'Drawer icons', name: 'Dark')
Widget darkDrawerIconsPreview() =>
    Theme(data: darkTheme, child: const DrawerIconsSpecimen());
