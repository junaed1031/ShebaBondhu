import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sheba_bondhu/core/config/app_config.dart';
import 'package:sheba_bondhu/core/network/api_exceptions.dart';
import 'package:sheba_bondhu/core/network/auth_interceptor.dart';

class ApiClient {
  late final Dio dio;

  ApiClient({
    String? baseUrl,
    FirebaseAuth? auth,
    Dio? customDio,
  }) {
    dio = customDio ??
        Dio(
          BaseOptions(
            baseUrl: baseUrl ?? AppConfig.apiBaseUrl,
            connectTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 15),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
          ),
        );

    dio.interceptors.add(AuthInterceptor(dio: dio, auth: auth));
  }

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await dio.get<T>(
        path,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});
