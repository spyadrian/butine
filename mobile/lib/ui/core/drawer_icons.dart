import 'package:flutter/material.dart';

/// Id given to drawers created before icons existed, and used for unknown ids.
const defaultDrawerIcon = 'label';

/// The closed set of drawer icons. Keys are stored in `prompts.icon`: never
/// rename or remove one, only add.
const drawerIcons = <String, IconData>{
  'label': Icons.label_outlined,
  'science': Icons.science_outlined,
  'biotech': Icons.biotech_outlined,
  'coronavirus': Icons.coronavirus_outlined,
  'medical_services': Icons.medical_services_outlined,
  'psychology': Icons.psychology_outlined,
  'eco': Icons.eco_outlined,
  'water_drop': Icons.water_drop_outlined,
  'public': Icons.public_outlined,
  'rocket_launch': Icons.rocket_launch_outlined,
  'bolt': Icons.bolt_outlined,
  'battery_charging_full': Icons.battery_charging_full_outlined,
  'solar_power': Icons.solar_power_outlined,
  'memory': Icons.memory_outlined,
  'smart_toy': Icons.smart_toy_outlined,
  'precision_manufacturing': Icons.precision_manufacturing_outlined,
  'architecture': Icons.architecture_outlined,
  'code': Icons.code_outlined,
  'hub': Icons.hub_outlined,
  'lock': Icons.lock_outlined,
  'functions': Icons.functions_outlined,
  'show_chart': Icons.show_chart_outlined,
  'lightbulb': Icons.lightbulb_outlined,
  'star': Icons.star_outlined,
};

/// The icon for a stored id, or the default one if the id is unknown.
IconData drawerIcon(String id) =>
    drawerIcons[id] ?? drawerIcons[defaultDrawerIcon]!;
