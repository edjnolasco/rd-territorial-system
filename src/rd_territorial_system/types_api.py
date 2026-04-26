from typing import Optional, TypedDict


class Normalized(TypedDict):
    province: str
    municipality: str
    level: str
    name: str
    composite_code: str


class ResolveResponse(TypedDict):
    status: str
    input: str
    normalized: Optional[Normalized]
    confidence: float