from typing import Any

from fastapi import APIRouter, HTTPException

from rd_territorial_system.api.schemas import ResolveRequest, ResolveResponse
from rd_territorial_system.catalog import resolve_name

router = APIRouter()


def enrich_resolve_payload(payload: dict[str, Any], rules_version: str = "v1") -> dict[str, Any]:
    entity = payload.get("entity")

    payload["canonical_name"] = entity.get("name") if entity else None
    payload["entity_id"] = entity.get("composite_code") if entity else None
    payload["entity_type"] = entity.get("level") if entity else None
    payload["rules_version"] = rules_version

    return payload


@router.post("/resolve", response_model=ResolveResponse)
def resolve(payload: ResolveRequest):
    try:
        result = resolve_name(
            payload.text,
            level=payload.level,
            parent_code=payload.parent_code,
            strict=payload.strict,
        )
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return enrich_resolve_payload(result, rules_version=payload.rules_version)