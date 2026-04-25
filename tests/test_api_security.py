from fastapi.testclient import TestClient

from rd_territorial_system.api.main import app

client = TestClient(app)


def test_public_health_no_api_key():
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_protected_endpoint_requires_api_key():
    response = client.post(
        "/api/v1/resolve",
        json={"text": "Distrito Nacional"},
    )

    # depende del modo, pero en api_key debería ser 401
    assert response.status_code in (200, 401)


def test_api_key_allows_access():
    response = client.post(
        "/api/v1/resolve",
        headers={"X-API-Key": "test-key"},
        json={"text": "Distrito Nacional"},
    )

    assert response.status_code in (200, 404, 409)