from rd_territorial_system.api.api_key_store import (
    find_client_by_api_key,
    load_api_clients,
)


def test_load_api_clients_from_file():
    clients = load_api_clients()

    assert clients
    assert clients[0].client_id == "dev-client"
    assert clients[0].status == "active"


def test_find_client_by_api_key():
    client = find_client_by_api_key("test-key")

    assert client is not None
    assert client.client_id == "dev-client"


def test_unknown_api_key_returns_none():
    client = find_client_by_api_key("unknown-key")

    assert client is None