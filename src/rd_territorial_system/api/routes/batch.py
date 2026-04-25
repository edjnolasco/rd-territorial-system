from __future__ import annotations

from fastapi import APIRouter

from rd_territorial_system.api.errors import raise_for_strict_result
from rd_territorial_system.api.openapi_responses import (
    STRICT_RESOLVE_ERROR_RESPONSES,
)
from rd_territorial_system.api.routes.resolve import enrich_resolve_payload
from rd_territorial_system.api.schemas import BatchResolveRequest, ResolveResponse
from rd_territorial_system.catalog import resolve_name

router = APIRouter(tags=["batch"])


@router.post(
    "/batch-resolve",
    response_model=list[ResolveResponse],
    summary="Resolve multiple territorial entities",
    description=(
        "Resolves multiple user-provided territorial names against the national "
        "catalog. Supports optional level filtering, parent disambiguation and "
        "strict error behavior."
    ),
    response_description="List of resolved entities or candidate lists",
    responses=STRICT_RESOLVE_ERROR_RESPONSES,
)
def batch_resolve(payload: BatchResolveRequest) -> list[ResolveResponse]:
    results = []

    for item in payload.items:
        result = resolve_name(
            item,
            level=payload.level,
            parent_code=payload.parent_code,
            strict=False,
        )

        result = enrich_resolve_payload(result, payload.rules_version)

        if payload.strict:
            raise_for_strict_result(result)

        results.append(result)

    return results