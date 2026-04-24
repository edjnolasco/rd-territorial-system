from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from rd_territorial_system.api.errors import raise_for_strict_result
from rd_territorial_system.api.schemas import (
    ResolveRequest,
    ResolveResponse,
    TerritorialEntity,
)
from rd_territorial_system.catalog import resolve_name

router = APIRouter()


def map_entity(entity_dict: dict[str, Any] | None) -> TerritorialEntity | None:
    if entity_dict is None:
        return None
    return TerritorialEntity(**entity_dict)


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
        for candidate in (
            map_entity(item) for item in payload.get("candidates", [])
        )
        if candidate is not None
    ]

    return payload


@router.post("/resolve", response_model=ResolveResponse)
def resolve(payload: ResolveRequest):
    result = resolve_name(
        payload.text,
        level=payload.level,
        parent_code=payload.parent_code,
        strict=False,
    )

    result = enrich_resolve_payload(result, payload.rules_version)

    if payload.strict:
        raise_for_strict_result(result)

    return result