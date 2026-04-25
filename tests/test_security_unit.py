
from rd_territorial_system.api.security import (
    forbidden_response,
    get_required_scope,
    hash_api_key,
    is_public_path,
    unauthorized_response,
)


def test_hash_api_key_returns_none_for_missing_key():
    assert hash_api_key(None) is None


def test_hash_api_key_does_not_expose_raw_key():
    hashed = hash_api_key("test-key")

    assert hashed is not None
    assert hashed != "test-key"
    assert len(hashed) == 12


def test_public_paths_are_detected():
    assert is_public_path("/api/v1/health")
    assert is_public_path("/docs")
    assert is_public_path("/openapi.json")


def test_required_scope_for_known_paths():
    assert get_required_scope("/api/v1/resolve") == "resolve:read"
    assert get_required_scope("/api/v1/search") == "search:read"
    assert get_required_scope("/api/v1/batch-resolve") == "batch:write"
    assert get_required_scope("/api/v1/catalog/stats") == "meta:read"
    assert get_required_scope("/api/v1/entities/10") == "entities:read"
    assert get_required_scope("/api/v1/provinces/01/entities") == "entities:read"


def test_required_scope_for_unknown_path_is_none():
    assert get_required_scope("/api/v1/health") is None


def test_unauthorized_response_shape():
    response = unauthorized_response("req-123")

    assert response.status_code == 401


def test_forbidden_response_shape():
    response = forbidden_response("req-123", "batch:write")

    assert response.status_code == 403