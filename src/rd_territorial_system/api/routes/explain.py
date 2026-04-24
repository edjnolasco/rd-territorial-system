from fastapi import APIRouter, HTTPException

from rd_territorial_system.api.routes.resolve import enrich_resolve_payload
from rd_territorial_system.api.schemas import ResolveRequest, ResolveResponse
from rd_territorial_system.catalog import resolve_name

router = APIRouter()


@router.post("/explain", response_model=ResolveResponse)
def explain(payload: ResolveRequest):
    try:
        result = resolve_name(
            payload.text,
            level=payload.level,
            parent_code=payload.parent_code,
            strict=False,
        )
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return enrich_resolve_payload(result, rules_version=payload.rules_version)