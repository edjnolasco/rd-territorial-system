from fastapi import APIRouter, HTTPException

from api.models import ResolveRequest, ResolveResponse
from api.services.resolver import resolve_real

router = APIRouter()


@router.post("/resolve", response_model=ResolveResponse)
def resolve(req: ResolveRequest):
    try:
        return resolve_real(
            text=req.text,
            level=req.level,
            rules_version=req.rules_version,
            strict=req.strict,
            parent_code=req.parent_code,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))