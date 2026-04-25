from fastapi.testclient import TestClient

from rd_territorial_system.api.main import app

client = TestClient(app)


def test_client_id_header_is_present_without_api_key():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "X-Client-ID" in response.headers
    assert response.headers["X-Client-ID"].startswith("ip:")


def test_client_id_header_uses_registered_client_when_api_key_is_known():
    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    assert "X-Client-ID" in response.headers
    assert response.headers["X-Client-ID"] == "client:dev-client"


def test_client_id_falls_back_to_hashed_api_key_when_unknown():
    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "unknown-key"},
    )

    assert response.status_code == 200
    assert "X-Client-ID" in response.headers
    assert response.headers["X-Client-ID"].startswith("api_key:")


def test_client_id_does_not_expose_raw_api_key():
    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    client_id = response.headers["X-Client-ID"]

    assert client_id != "api_key:test-key"
    assert "test-key" not in client_id