from __future__ import annotations

from typing import Any


def map_entity(entity_dict: dict[str, Any] | None) -> dict[str, Any] | None:
    if entity_dict is None:
        return None
    return entity_dict


def enrich_resolve_payload(
    payload: dict[str, Any],
    rules_version: str = "v1",
) -> dict[str, Any]:
    entity = payload.get("entity")

    payload["canonical_name"] = entity.get("name") if entity else None
    payload["entity_id"] = entity.get("composite_code") if entity else None
    payload["entity_type"] = entity.get("level") if entity else None
    payload["rules_version"] = rules_version

    payload["entity"] = map_entity(payload.get("entity"))
    payload["candidates"] = [
        candidate
        for candidate in (map_entity(item) for item in payload.get("candidates", []))
        if candidate is not None
    ]

    return payload