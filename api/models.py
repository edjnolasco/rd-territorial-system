from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


LevelType = Literal[
    "province",
    "municipality",
    "district_municipal",
    "section",
    "barrio_paraje",
    "sub_barrio",
    "toponym",
]


class ResolveRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=2,
        examples=["Santo Domingo", "Sto Dgo", "Los Peralejos"],
    )
    level: LevelType | None = Field(
        default=None,
        examples=["province", "municipality", "barrio_paraje"],
    )
    rules_version: str = Field(
        default="v1",
        examples=["v1", "current", "2024.1"],
    )
    strict: bool = Field(
        default=False,
        examples=[False],
    )
    parent_code: str | None = Field(
        default=None,
        examples=["10-01-01-01-01-001-00"],
        description="Código compuesto del padre para ayudar a desambiguar.",
    )


class TerritorialEntityResponse(BaseModel):
    region_code: str
    province_code: str
    municipality_code: str
    district_municipal_code: str
    section_code: str
    barrio_paraje_code: str
    sub_barrio_code: str
    level: str
    name: str
    official_name: str
    normalized_name: str
    parent_composite_code: str
    composite_code: str
    full_path: str
    parent_path: list[str] = Field(default_factory=list)
    is_official: bool = True
    source: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    notes: str | None = None


class ResolveResponse(BaseModel):
    input: str
    normalized_text: str | None = None
    canonical_name: str | None = None
    entity_id: str | None = None
    entity_type: str | None = None
    confidence: float
    matched: bool
    status: str
    match_strategy: str
    rules_version: str
    entity: TerritorialEntityResponse | None = None
    candidates: list[TerritorialEntityResponse] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)


class BatchResolveRequest(BaseModel):
    items: list[str] = Field(
        ...,
        min_length=1,
        examples=[["Santo Domingo", "Sto Dgo", "Los Peralejos"]],
    )
    level: LevelType | None = None
    rules_version: str = "v1"
    strict: bool = False
    parent_code: str | None = None


class ExplainRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=2,
        examples=["Sto Dgo"],
    )
    level: LevelType | None = None
    rules_version: str = "v1"
    parent_code: str | None = None


class ExplainResponse(BaseModel):
    input: str
    normalized_text: str | None = None
    status: str
    matched: bool
    match_strategy: str
    trace: list[str] = Field(default_factory=list)
    entity: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = Field(default_factory=list)