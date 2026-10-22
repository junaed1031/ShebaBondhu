import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sheba_bondhu/core/l10n/app_localizations.dart';
import 'package:sheba_bondhu/core/network/api_client.dart';
import 'package:sheba_bondhu/features/home/home_screen.dart';

void main() {
  testWidgets('HomeScreen renders Bangla text properly',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          locale: Locale('bn'),
          home: HomeScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify Bangla welcome text is rendered
    expect(find.text('সেবাবন্ধুতে স্বাগতম'), findsOneWidget);

    // Verify Bangla app title is rendered in AppBar
    expect(find.text('সেবাবন্ধু'), findsOneWidget);

    // Verify Bangla button label is rendered
    expect(find.text('ব্যাকএন্ড পরীক্ষা করুন'), findsOneWidget);
  });

  testWidgets('HomeScreen check backend button calls API and displays status',
      (WidgetTester tester) async {
    final dio = Dio();
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          if (options.path == '/health') {
            return handler.resolve(
              Response(
                requestOptions: options,
                statusCode: 200,
                data: {
                  'status': 'ok',
                  'version': '1.0.0',
                  'firestore': 'connected',
                  'timestamp': '2026-10-23T00:00:00Z',
                },
              ),
            );
          }
          return handler.next(options);
        },
      ),
    );

    final testApiClient = ApiClient(customDio: dio);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(testApiClient),
        ],
        child: const MaterialApp(
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          locale: Locale('bn'),
          home: HomeScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Tap "Check backend" button
    await tester.tap(find.text('ব্যাকএন্ড পরীক্ষা করুন'));
    await tester.pumpAndSettle();

    // Verify response is displayed
    expect(find.text('Backend Response'), findsOneWidget);
    expect(find.textContaining('Status: ok'), findsOneWidget);
    expect(find.textContaining('Firestore: connected'), findsOneWidget);
  });
}
