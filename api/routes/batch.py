from fastapi import APIRouter
from api.services.resolver import resolve_real

router = APIRouter()

@router.post("/batch-resolve")
def batch(data: dict):
    return [resolve_real(i) for i in data["items"]]