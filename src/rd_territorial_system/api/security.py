import hashlib

from fastapi import Request
from fastapi.responses import JSONResponse

from rd_territorial_system.api.api_key_store import ApiClient, find_client_by_api_key
from rd_territorial_system.api.settings import get_settings

settings = get_settings()

PUBLIC_PATHS = {
    "/api/v1/health",
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
}

ROUTE_SCOPES = {
    "/api/v1/resolve": "resolve:read",
    "/api/v1/explain": "resolve:read",
    "/api/v1/search": "search:read",
    "/api/v1/batch-resolve": "batch:write",
    "/api/v1/catalog/stats": "meta:read",
}


def is_public_path(path: str) -> bool:
    return any(path.startswith(p) for p in PUBLIC_PATHS)


def get_required_scope(path: str) -> str | None:
    if path.startswith("/api/v1/entities/"):
        return "entities:read"

    if path.startswith("/api/v1/provinces/"):
        return "entities:read"

    return ROUTE_SCOPES.get(path)


def get_api_key(request: Request) -> str | None:
    return request.headers.get("X-API-Key")


def hash_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None

    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]


def get_client_from_request(request: Request) -> ApiClient | None:
    return find_client_by_api_key(get_api_key(request))


def get_client_id(request: Request) -> str:
    client = get_client_from_request(request)

    if client:
        return f"client:{client.client_id}"

    api_key = get_api_key(request)

    if api_key:
        return f"api_key:{hash_api_key(api_key)}"

    forwarded_for = request.headers.get("X-Forwarded-For")

    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"

    if request.client:
        return f"ip:{request.client.host}"

    return "unknown"


def unauthorized_response(request_id: str | None) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "detail": {
                "error": "unauthorized",
                "message": "Missing or invalid API key",
            },
            "request_id": request_id,
        },
    )


def forbidden_response(request_id: str | None, required_scope: str) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "detail": {
                "error": "forbidden",
                "message": f"Missing required scope: {required_scope}",
            },
            "request_id": request_id,
        },
    )


def check_api_key(request: Request, request_id: str | None):
    api_key = get_api_key(request)
    client = find_client_by_api_key(api_key)

    if client:
        if client.is_active:
            return None

        return unauthorized_response(request_id)

    if api_key and api_key in settings.api_keys:
        return None

    return unauthorized_response(request_id)


def check_scope(request: Request, request_id: str | None):
    required_scope = get_required_scope(request.url.path)

    if required_scope is None:
        return None

    client = get_client_from_request(request)

    if client is None:
        return None

    if client.has_scope(required_scope):
        return None

    return forbidden_response(request_id, required_scope)