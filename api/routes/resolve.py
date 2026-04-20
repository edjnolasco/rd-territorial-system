from fastapi import APIRouter, HTTPException
from api.models import ResolveRequest
from api.services.resolver import resolve_real

router = APIRouter()

@router.post("/resolve")
def resolve(req: ResolveRequest):
    try:
        return resolve_real(req.text, req.strict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))