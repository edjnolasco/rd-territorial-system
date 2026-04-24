from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel

STRICT_STATUS_TO_HTTP = {
    "not_found": 404,
    "ambiguous": 409,
    "invalid_input": 422,
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()

    if isinstance(value, list):
        return [_json_safe(item) for item in value]

    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}

    return value


def raise_for_strict_result(result: dict[str, Any]) -> None:
    status = result.get("status")

    if status == "matched":
        return

    candidates = _json_safe(result.get("candidates", []) or [])
    trace = _json_safe(result.get("trace", []) or [])

    http_status = STRICT_STATUS_TO_HTTP.get(status, 400)

    raise HTTPException(
        status_code=http_status,
        detail={
            "status": status,
            "matched": result.get("matched", False),
            "message": _message_for_status(status),
            "candidate_count": len(candidates),
            "candidates": candidates,
            "trace": trace,
        },
    )


def _message_for_status(status: str | None) -> str:
    if status == "not_found":
        return "No territorial entity found for the given input."

    if status == "ambiguous":
        return "Multiple territorial entities match the input."

    if status == "invalid_input":
        return "Input text is invalid after normalization."

    return "Territorial resolution failed."