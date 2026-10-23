import 'package:dio/dio.dart';

class ApiException implements Exception {
  final String code;
  final String message;
  final Map<String, dynamic> details;
  final String? requestId;
  final int? statusCode;

  const ApiException({
    required this.code,
    required this.message,
    this.details = const {},
    this.requestId,
    this.statusCode,
  });

  factory ApiException.fromDioException(DioException dioException) {
    final response = dioException.response;
    final statusCode = response?.statusCode;
    final requestId = response?.headers.value('x-request-id');

    if (response?.data is Map<String, dynamic>) {
      final data = response!.data as Map<String, dynamic>;
      if (data['error'] is Map<String, dynamic>) {
        final err = data['error'] as Map<String, dynamic>;
        return ApiException(
          code: err['code']?.toString() ?? _defaultCodeForStatus(statusCode),
          message: err['message']?.toString() ?? 'An unexpected error occurred',
          details: err['details'] is Map<String, dynamic>
              ? err['details'] as Map<String, dynamic>
              : {},
          requestId: err['request_id']?.toString() ?? requestId,
          statusCode: statusCode,
        );
      }
    }

    return ApiException(
      code: _defaultCodeForStatus(statusCode),
      message: _defaultMessageForStatus(statusCode, dioException),
      requestId: requestId,
      statusCode: statusCode,
    );
  }

  static String _defaultCodeForStatus(int? statusCode) {
    switch (statusCode) {
      case 401:
        return 'AUTH_ERROR';
      case 403:
        return 'FORBIDDEN';
      case 404:
        return 'NOT_FOUND';
      case 422:
        return 'VALIDATION_ERROR';
      case 429:
        return 'RATE_LIMITED';
      case 500:
        return 'INTERNAL_ERROR';
      case 503:
        return 'LLM_UNAVAILABLE';
      default:
        return 'NETWORK_ERROR';
    }
  }

  static String _defaultMessageForStatus(int? statusCode, DioException err) {
    switch (statusCode) {
      case 401:
        return 'Authentication required or token expired.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 422:
        return 'The submitted data was invalid.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'An internal server error occurred.';
      case 503:
        return 'The service is temporarily unavailable.';
      default:
        return err.message ?? 'A network error occurred. Please check your connection.';
    }
  }

  @override
  String toString() =>
      'ApiException(code: $code, message: $message, requestId: $requestId, statusCode: $statusCode)';
}
