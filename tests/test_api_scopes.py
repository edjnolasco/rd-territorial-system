import json

from fastapi.testclient import TestClient

from rd_territorial_system.api.api_key_store import load_api_clients
from rd_territorial_system.api.main import app

client = TestClient(app)


def test_registered_client_has_scopes():
    api_clients = load_api_clients()
    dev_client = next(c for c in api_clients if c.client_id == "dev-client")

    assert "resolve:read" in dev_client.scopes
    assert "batch:write" in dev_client.scopes
    assert dev_client.has_scope("resolve:read")


def test_scope_model_supports_wildcard(tmp_path):
    payload = {
        "clients": [
            {
                "client_id": "admin-client",
                "client_name": "Admin Client",
                "api_key": "admin-key",
                "status": "active",
                "scopes": ["*"],
            }
        ]
    }

    path = tmp_path / "api_keys.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    load_api_clients.cache_clear()
    clients = load_api_clients(path)

    assert clients[0].has_scope("resolve:read")
    assert clients[0].has_scope("batch:write")

    load_api_clients.cache_clear()


def test_known_client_can_access_resolve_with_scope():
    response = client.post(
        "/api/v1/resolve",
        headers={"X-API-Key": "test-key"},
        json={"text": "Distrito Nacional"},
    )

    assert response.status_code == 200