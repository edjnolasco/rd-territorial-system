from __future__ import annotations

from fastapi import APIRouter

from rd_territorial_system.api.errors import raise_for_strict_result
from rd_territorial_system.api.routes.resolve import enrich_resolve_payload
from rd_territorial_system.api.schemas import ResolveRequest, ResolveResponse
from rd_territorial_system.catalog import resolve_name

router = APIRouter()


@router.post("/explain", response_model=ResolveResponse)
def explain(payload: ResolveRequest):
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