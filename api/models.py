from pydantic import BaseModel, Field
from typing import List, Optional

class ResolveRequest(BaseModel):
    text: str = Field(..., min_length=2)
    level: str = "province"
    rules_version: str = "v1"
    strict: bool = False

class ResolveResponse(BaseModel):
    input: str
    canonical_name: Optional[str]
    entity_id: Optional[str]
    confidence: float
    matched: bool
    rules_version: str