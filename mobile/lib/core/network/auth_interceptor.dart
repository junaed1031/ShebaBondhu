import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';

class AuthInterceptor extends QueuedInterceptor {
  final Dio dio;
  final FirebaseAuth? auth;

  AuthInterceptor({
    required this.dio,
    this.auth,
  });

  FirebaseAuth? get _firebaseAuth {
    if (auth != null) return auth;
    try {
      return FirebaseAuth.instance;
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final firebaseAuth = _firebaseAuth;
    final user = firebaseAuth?.currentUser;
    if (user != null) {
      try {
        final token = await user.getIdToken();
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
      } catch (_) {
        // Proceed without token if retrieval fails
      }
    }
    return handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final is401 = err.response?.statusCode == 401;
    final alreadyRetried = err.requestOptions.extra['auth_retried'] == true;

    if (is401 && !alreadyRetried) {
      final firebaseAuth = _firebaseAuth;
      final user = firebaseAuth?.currentUser;
      if (user != null) {
        try {
          final newToken = await user.getIdToken(true);
          if (newToken != null && newToken.isNotEmpty) {
            final requestOptions = err.requestOptions;
            requestOptions.headers['Authorization'] = 'Bearer $newToken';
            requestOptions.extra['auth_retried'] = true;

            final response = await dio.fetch(requestOptions);
            return handler.resolve(response);
          }
        } catch (_) {
          // Token refresh failed, continue with original error
        }
      }
    }

    return handler.next(err);
  }
}
