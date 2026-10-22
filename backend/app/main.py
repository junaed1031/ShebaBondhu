import contextvars
import logging
import sys
import time
import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.errors import register_error_handlers
from app.modules.health.router import router as health_router

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


class RequestIdFilter(logging.Filter):
    """Logging filter that injects the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "system"
        return True


def setup_logging() -> None:
    """Configure root logging to display request_id on all log lines."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [req_id=%(request_id)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]


setup_logging()
logger = logging.getLogger("shebabondhu")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates/extracts a request_id for every request,
    stores it in request.state and contextvars, and logs request lifecycle.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        incoming_request_id = request.headers.get("X-Request-ID")
        request_id = incoming_request_id.strip() if incoming_request_id else str(uuid.uuid4())
        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)

        start_time = time.perf_counter()
        logger.info("Request started: %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
            process_time = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Request finished: %s %s status=%d duration=%.2fms",
                request.method,
                request.url.path,
                response.status_code,
                process_time,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Request failed: %s %s duration=%.2fms error=%s",
                request.method,
                request.url.path,
                process_time,
                exc,
            )
            raise
        finally:
            request_id_ctx.reset(token)


def create_app() -> FastAPI:
    """FastAPI application factory."""
    application = FastAPI(
        title="ShebaBondhu API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    application.add_middleware(RequestLoggingMiddleware)

    # Global Exception Handlers
    register_error_handlers(application)

    # Routers
    application.include_router(health_router)

    return application


app = create_app()
