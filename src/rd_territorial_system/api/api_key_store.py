from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class ApiClient:
    client_id: str
    client_name: str
    api_key: str
    status: str
    scopes: list[str] = field(default_factory=list)
    rate_limit_requests: int | None = None
    rate_limit_window_seconds: int | None = None
    created_at: str | None = None

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def has_scope(self, scope: str) -> bool:
        return "*" in self.scopes or scope in self.scopes


class ApiKeyStoreError(Exception):
    pass


@lru_cache
def load_api_clients(path: str | Path = "data/api_keys.json") -> list[ApiClient]:
    file_path = Path(path)

    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:
        raise ApiKeyStoreError(f"Failed to read API key store: {exc}") from exc

    clients = payload.get("clients", [])

    return [
        ApiClient(
            client_id=item["client_id"],
            client_name=item["client_name"],
            api_key=item["api_key"],
            status=item.get("status", "active"),
            scopes=item.get("scopes", []),
            rate_limit_requests=item.get("rate_limit_requests"),
            rate_limit_window_seconds=item.get("rate_limit_window_seconds"),
            created_at=item.get("created_at"),
        )
        for item in clients
    ]


def find_client_by_api_key(api_key: str | None) -> ApiClient | None:
    if not api_key:
        return None

    for client in load_api_clients():
        if client.api_key == api_key:
            return client

    return None