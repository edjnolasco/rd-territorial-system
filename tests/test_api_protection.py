from fastapi.testclient import TestClient

from rd_territorial_system.api.main import app

client = TestClient(app)


def test_security_headers_are_present():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "X-Request-ID" in response.headers


def test_rate_limit_headers_are_present():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers