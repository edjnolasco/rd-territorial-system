from typing import Any, Literal

from pydantic import BaseModel, Field

Level = Literal[
    "province",
    "municipality",
    "district_municipal",
    "section",
    "barrio_paraje",
    "sub_barrio",
    "toponym",
]

Status = Literal["matched", "ambiguous", "not_found", "invalid_input"]


class ResolveRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        json_schema_extra={"example": "Brisas del Norte"},
    )
    level: Level | None = Field(
        default=None,
        json_schema_extra={"example": "sub_barrio"},
    )
    parent_code: str | None = Field(
        default=None,
        json_schema_extra={"example": "10-01-01-01-01-001-00"},
    )
    strict: bool = False
    rules_version: str = "v1"


class BatchResolveRequest(BaseModel):
    items: list[str] = Field(..., min_length=1, max_length=100)
    level: Level | None = None
    parent_code: str | None = None
    strict: bool = False
    rules_version: str = "v1"


class SearchRequest(BaseModel):
    text: str = Field(..., min_length=1)
    level: Level | None = None
    parent_code: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class ResolveResponse(BaseModel):
    input: str
    normalized_text: str | None
    matched: bool
    status: Status
    confidence: float
    match_strategy: str
    canonical_name: str | None = None
    entity_id: str | None = None
    entity_type: str | None = None
    entity: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = []
    trace: list[str] = []
    rules_version: str = "v1"


class EntityLookupResponse(BaseModel):
    matched: bool
    status: Status
    entity: dict[str, Any] | None = None
    message: str | None = None


class SearchResponse(BaseModel):
    input: str
    normalized_text: str | None
    count: int
    items: list[dict[str, Any]]


class ChildrenResponse(BaseModel):
    parent_code: str
    count: int
    items: list[dict[str, Any]]


class ProvinceEntitiesResponse(BaseModel):
    province_code: str
    count: int
    items: list[dict[str, Any]]


class CatalogStatsResponse(BaseModel):
    catalog_version: str
    country: str
    province_count: int
    entity_count: int
    levels: dict[str, int]
    source_of_truth: str


class HealthResponse(BaseModel):
    status: str
    service: str
    api_version: str
    catalog_format: str
    catalog_loaded: bool