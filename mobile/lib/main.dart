import 'package:flutter/material.dart';

void main() {
  runApp(const ButineApp());
}

class ButineApp extends StatelessWidget {
  const ButineApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      title: 'Butine',
      home: Scaffold(body: Center(child: Text('Butine'))),
    );
  }
}
