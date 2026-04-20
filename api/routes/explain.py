from fastapi import APIRouter, HTTPException

from api.models import ExplainRequest, ExplainResponse
from api.services.resolver import resolve_real

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    try:
        result = resolve_real(
            text=req.text,
            level=req.level,
            rules_version=req.rules_version,
            strict=False,
            parent_code=req.parent_code,
        )

        return {
            "input": result.get("input"),
            "normalized_text": result.get("normalized_text"),
            "status": result.get("status"),
            "matched": result.get("matched"),
            "match_strategy": result.get("match_strategy"),
            "trace": result.get("trace", []),
            "entity": result.get("entity"),
            "candidates": result.get("candidates", []),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))