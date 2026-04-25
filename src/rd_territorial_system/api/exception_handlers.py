import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("rd_territorial_system.api")


def _get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = _get_request_id(request)

    logger.warning(
        "http_exception",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
            }
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id,
        },
    )


def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = _get_request_id(request)

    logger.warning(
        "validation_error",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "errors": exc.errors(),
                "path": request.url.path,
            }
        },
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "request_id": request_id,
        },
    )


def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = _get_request_id(request)

    logger.exception(
        "unhandled_exception",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "path": request.url.path,
            }
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "error": "internal_error",
                "message": "Unexpected server error",
            },
            "request_id": request_id,
        },
    )