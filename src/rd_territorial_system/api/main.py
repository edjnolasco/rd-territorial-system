import importlib
import logging
import pkgutil
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

import rd_territorial_system.api.routes as routes_pkg
from rd_territorial_system.api.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from rd_territorial_system.api.logging_config import configure_logging
from rd_territorial_system.api.rate_limit import (
    get_client_key,
    rate_limit_response,
    rate_limiter,
)
from rd_territorial_system.api.settings import get_settings

# ------------------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------------------

settings = get_settings()


# ------------------------------------------------------------------------------
# Logging config
# ------------------------------------------------------------------------------

configure_logging(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("rd_territorial_system.api")


# ------------------------------------------------------------------------------
# App
# ------------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_tags=[
        {
            "name": "meta",
            "description": "Health checks and catalog metadata.",
        },
        {
            "name": "resolve",
            "description": "Territorial name resolution.",
        },
        {
            "name": "batch",
            "description": "Batch territorial resolution.",
        },
        {
            "name": "explain",
            "description": "Explain resolver decisions.",
        },
        {
            "name": "search",
            "description": "Territorial entity search.",
        },
        {
            "name": "entities",
            "description": "Territorial entity lookup.",
        },
    ],
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# ------------------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Middleware: logging + rate limiting + headers
# ------------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    start_time = time.perf_counter()

    # --------------------------------------------------
    # RATE LIMIT (antes de procesar request)
    # --------------------------------------------------
    remaining = None

    if settings.rate_limit_enabled:
        client_key = get_client_key(request)

        allowed, remaining = rate_limiter.is_allowed(
            key=client_key,
            max_requests=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "client_key": client_key,
                        "path": request.url.path,
                    }
                },
            )

            response = rate_limit_response(request_id)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
            response.headers["X-RateLimit-Remaining"] = "0"
            return response

    # --------------------------------------------------
    # PROCESAR REQUEST
    # --------------------------------------------------
    response = await call_next(request)

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # --------------------------------------------------
    # HEADERS
    # --------------------------------------------------
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    if settings.rate_limit_enabled:
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            remaining if remaining is not None else 0
        )

    # --------------------------------------------------
    # LOGGING
    # --------------------------------------------------
    logger.info(
        "request_completed",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            }
        },
    )

    return response


# ------------------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------------------

for module_info in pkgutil.iter_modules(routes_pkg.__path__):
    module_name = module_info.name

    if module_name.startswith("_"):
        continue

    module = importlib.import_module(f"{routes_pkg.__name__}.{module_name}")
    router = getattr(module, "router", None)

    if router is not None:
        app.include_router(router, prefix=settings.api_prefix)

        logger.info(
            "router_mounted",
            extra={
                "extra_fields": {
                    "router": module_name,
                    "prefix": settings.api_prefix,
                }
            },
        )