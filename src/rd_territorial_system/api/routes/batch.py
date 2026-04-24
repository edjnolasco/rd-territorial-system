from fastapi import APIRouter, HTTPException

from rd_territorial_system.api.routes.resolve import enrich_resolve_payload
from rd_territorial_system.api.schemas import BatchResolveRequest, ResolveResponse
from rd_territorial_system.catalog import resolve_name

router = APIRouter()


@router.post("/batch-resolve", response_model=list[ResolveResponse])
def batch_resolve(payload: BatchResolveRequest):
    results = []

    for item in payload.items:
        try:
            result = resolve_name(
                item,
                level=payload.level,
                parent_code=payload.parent_code,
                strict=payload.strict,
            )
        except (LookupError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        results.append(
            enrich_resolve_payload(result, rules_version=payload.rules_version)
        )

    return results