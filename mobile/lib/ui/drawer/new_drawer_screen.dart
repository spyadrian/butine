import 'package:flutter/material.dart';

// shortcut: empty screen so onboarding has somewhere to go; the form comes with drawer creation.
class NewDrawerScreen extends StatelessWidget {
  const NewDrawerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(appBar: AppBar(title: const Text('New drawer')));
  }
}
