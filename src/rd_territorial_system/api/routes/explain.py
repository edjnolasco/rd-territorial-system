from __future__ import annotations

from fastapi import APIRouter

from rd_territorial_system.api.errors import raise_for_strict_result
from rd_territorial_system.api.openapi_responses import (
    STRICT_RESOLVE_ERROR_RESPONSES,
)
from rd_territorial_system.api.schemas import ResolveRequest, ResolveResponse
from rd_territorial_system.catalog import resolve_name
from rd_territorial_system.core.enrichment import enrich_resolve_payload

router = APIRouter(tags=["explain"])


@router.post(
    "/explain",
    response_model=ResolveResponse,
    summary="Explain territorial resolution",
    description=(
        "Resolves a territorial name and returns the decision trace generated "
        "by the resolver, including normalization, matching and ambiguity details."
    ),
    response_description="Resolution result with explanation trace",
    responses=STRICT_RESOLVE_ERROR_RESPONSES,
)
def explain(payload: ResolveRequest) -> ResolveResponse:
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