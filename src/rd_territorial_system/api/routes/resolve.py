from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from rd_territorial_system.api.catalog_metadata import inject_catalog_version  # 👈 NUEVO
from rd_territorial_system.api.errors import raise_for_strict_result
from rd_territorial_system.api.openapi_responses import (
    STRICT_RESOLVE_ERROR_RESPONSES,
)
from rd_territorial_system.api.schemas import (
    ResolveRequest,
    ResolveResponse,
    TerritorialEntity,
)
from rd_territorial_system.catalog import resolve_name
from rd_territorial_system.metrics.metrics_schema import RequestMetrics
from rd_territorial_system.metrics.runtime import metrics

router = APIRouter(tags=["resolve"])


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


def infer_result_type(payload: dict[str, Any]) -> str:
    entity = payload.get("entity")
    candidates = payload.get("candidates", [])

    if entity is not None:
        return "matched"

    if candidates:
        return "ambiguous"

    return "no_match"


@router.post(
    "/resolve",
    response_model=ResolveResponse,
    summary="Resolve a territorial entity",
    description=(
        "Resolves a user-provided territorial name into a structured entity "
        "from the national catalog. Supports optional level filtering and "
        "parent disambiguation."
    ),
    response_description="Resolved entity or candidate list",
    responses=STRICT_RESOLVE_ERROR_RESPONSES,
)
def resolve(payload: ResolveRequest, request: Request) -> ResolveResponse:
    result = resolve_name(
        payload.text,
        level=payload.level,
        parent_code=payload.parent_code,
        strict=False,
    )

    result = enrich_resolve_payload(result, payload.rules_version)

    # 🔥 MÉTRICAS NIVEL 2
    try:
        result_type = infer_result_type(result)

        metrics.record(
            RequestMetrics(
                request_id=getattr(request.state, "request_id", ""),
                client_id=getattr(request.state, "client_id", "unknown"),
                endpoint="/api/v1/resolve",
                status_code=200,
                latency_ms=0.0,  # ya medido en middleware
                query=payload.text,
                level_requested=payload.level,
                level_resolved=result.get("entity_type"),
                result_type=result_type,
                api_key_hash=getattr(request.state, "api_key_hash", None),
            )
        )
    except Exception:
        pass

    if payload.strict:
        raise_for_strict_result(result)

    # 👇 INYECCIÓN FINAL (ÚNICO CAMBIO REAL)
    return inject_catalog_version(result)