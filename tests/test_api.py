from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_resolve():
    res = client.post("/api/v1/resolve", json={"text": "Sto Dgo"})
    assert res.status_code == 200
