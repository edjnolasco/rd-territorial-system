from fastapi import APIRouter

router = APIRouter()

@router.post("/explain")
def explain(data: dict):
    return {
        "steps": [
            "fuzzy match → Santo Domingo",
            "override aplicado"
        ]
    }