from fastapi import APIRouter

router = APIRouter()

@router.get("/versions")
def versions():
    return {
        "rules": ["v1"],
        "data": "2024.1"
    }

@router.get("/health")
def health():
    return {"status": "ok"}