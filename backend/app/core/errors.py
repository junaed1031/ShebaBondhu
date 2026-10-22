import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ShebaBondhuError(Exception):
    """Base exception for all app errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(ShebaBondhuError):
    status_code = 401
    error_code = "AUTH_ERROR"
    message = "Authentication failed"


class AuthorizationError(ShebaBondhuError):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "Permission denied"


class NotFoundError(ShebaBondhuError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class NotRegisteredError(NotFoundError):
    status_code = 404
    error_code = "NOT_REGISTERED"
    message = "User is not registered"


class ValidationError(ShebaBondhuError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Validation error"


class RateLimitError(ShebaBondhuError):
    status_code = 429
    error_code = "RATE_LIMITED"
    message = "Rate limit exceeded"


class LLMError(ShebaBondhuError):
    status_code = 503
    error_code = "LLM_UNAVAILABLE"
    message = "AI assistant is temporarily unavailable"


HTTP_STATUS_TO_CODE: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "AUTH_ERROR",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "LLM_UNAVAILABLE",
}


def get_request_id(request: Request) -> str:
    """Retrieve request_id from request state or header."""
    return (
        getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-ID")
        or "unknown"
    )


async def sheba_error_handler(request: Request, exc: ShebaBondhuError) -> JSONResponse:
    request_id = get_request_id(request)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id,
            }
        },
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = get_request_id(request)
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
                "request_id": request_id,
            }
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    request_id = get_request_id(request)
    error_code = HTTP_STATUS_TO_CODE.get(exc.status_code, "ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    details = exc.detail if isinstance(exc.detail, dict) else {}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    request_id = get_request_id(request)
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
                "request_id": request_id,
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all global error handlers on the FastAPI application."""
    app.add_exception_handler(ShebaBondhuError, sheba_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
