from fastapi import APIRouter, HTTPException

from api.models import BatchResolveRequest, ResolveResponse
from api.services.resolver import resolve_real

router = APIRouter()


@router.post("/batch-resolve", response_model=list[ResolveResponse])
def batch_resolve(req: BatchResolveRequest):
    try:
        results = [
            resolve_real(
                text=item,
                level=req.level,
                rules_version=req.rules_version,
                strict=req.strict,
                parent_code=req.parent_code,
            )
            for item in req.items
        ]
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))