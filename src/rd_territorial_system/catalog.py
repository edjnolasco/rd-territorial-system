from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Literal
import csv

from .normalization import normalize_text

Level = Literal[
    "province",
    "municipality",
    "district_municipal",
    "section",
    "barrio_paraje",
    "sub_barrio",
    "toponym",
]

SUPPORTED_LEVELS: tuple[str, ...] = (
    "province",
    "municipality",
    "district_municipal",
    "section",
    "barrio_paraje",
    "sub_barrio",
    "toponym",
)

DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "rd_territorial_master.csv"
)


@dataclass(frozen=True)
class TerritorialEntity:
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
    is_official: bool = True
    source: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    notes: str | None = None

    @property
    def parent_path(self) -> list[str]:
        return [part.strip() for part in self.full_path.split(">")[:-1] if part.strip()]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["parent_path"] = self.parent_path
        return data


@dataclass(frozen=True)
class ResolveResult:
    input: str
    normalized_text: str | None
    matched: bool
    status: str
    confidence: float
    match_strategy: str
    entity: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] | None = None
    trace: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["trace"] = self.trace or []
        if payload["candidates"] is None:
            payload["candidates"] = []
        return payload


def build_composite_code(row: dict[str, Any]) -> str:
    return "-".join(
        [
            str(row.get("region_code", "")).zfill(2),
            str(row.get("province_code", "")).zfill(2),
            str(row.get("municipality_code", "")).zfill(2),
            str(row.get("district_municipal_code", "")).zfill(2),
            str(row.get("section_code", "")).zfill(2),
            str(row.get("barrio_paraje_code", "")).zfill(3),
            str(row.get("sub_barrio_code", "")).zfill(2),
        ]
    )


def infer_level(row: dict[str, Any]) -> str:
    if row.get("sub_barrio_code") not in ("", "00", None):
        return "sub_barrio"
    if row.get("barrio_paraje_code") not in ("", "000", None):
        return "barrio_paraje"
    if row.get("section_code") not in ("", "00", None):
        return "section"
    if row.get("district_municipal_code") not in ("", "00", None):
        return "district_municipal"
    if row.get("municipality_code") not in ("", "00", None):
        return "municipality"
    if row.get("province_code") not in ("", "00", None):
        return "province"
    return "toponym"


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "si", "sí"}


class Catalog:
    def __init__(self, entities: Iterable[TerritorialEntity]):
        self.entities = list(entities)
        self.by_code: dict[str, TerritorialEntity] = {}
        self.by_name: dict[str, list[TerritorialEntity]] = defaultdict(list)
        self.by_name_level: dict[tuple[str, str], list[TerritorialEntity]] = defaultdict(list)
        self.by_name_parent: dict[tuple[str, str], list[TerritorialEntity]] = defaultdict(list)

        for entity in self.entities:
            self.by_code[entity.composite_code] = entity
            self.by_name[entity.normalized_name].append(entity)
            self.by_name_level[(entity.normalized_name, entity.level)].append(entity)
            if entity.parent_composite_code:
                self.by_name_parent[(entity.normalized_name, entity.parent_composite_code)].append(entity)

    @classmethod
    def from_csv(cls, path: str | Path = DEFAULT_CATALOG_PATH) -> "Catalog":
        entities = load_catalog(path)
        return cls(entities)

    def resolve_code(self, composite_code: str) -> TerritorialEntity | None:
        return self.by_code.get(composite_code)

    def search_entities(
        self,
        text: str,
        *,
        level: str | None = None,
        parent_code: str | None = None,
        limit: int = 20,
    ) -> list[TerritorialEntity]:
        key = normalize_text(text)
        if not key:
            return []

        if level is not None and level not in SUPPORTED_LEVELS:
            raise ValueError(f"Unsupported level: {level}")

        if level and parent_code:
            items = [
                e for e in self.by_name_level.get((key, level), [])
                if e.parent_composite_code == parent_code
            ]
            return items[:limit]

        if level:
            return self.by_name_level.get((key, level), [])[:limit]

        if parent_code:
            return self.by_name_parent.get((key, parent_code), [])[:limit]

        return self.by_name.get(key, [])[:limit]

    def resolve_name(
        self,
        text: str,
        *,
        level: str | None = None,
        parent_code: str | None = None,
        strict: bool = False,
        limit: int = 10,
    ) -> ResolveResult:
        key = normalize_text(text)
        trace = [f"normalized input -> {key!r}"]

        if not key:
            if strict:
                raise ValueError("Input text is empty after normalization")
            return ResolveResult(
                input=text,
                normalized_text=key,
                matched=False,
                status="invalid_input",
                confidence=0.0,
                match_strategy="none",
                trace=trace + ["input collapsed to empty string"],
            )

        candidates = self.search_entities(
            text,
            level=level,
            parent_code=parent_code,
            limit=limit,
        )

        if not candidates:
            if strict:
                raise LookupError(f"No territorial entity found for: {text}")
            return ResolveResult(
                input=text,
                normalized_text=key,
                matched=False,
                status="not_found",
                confidence=0.0,
                match_strategy="exact_catalog",
                trace=trace + ["no candidates found in catalog"],
            )

        if len(candidates) == 1:
            entity = candidates[0]
            return ResolveResult(
                input=text,
                normalized_text=key,
                matched=True,
                status="matched",
                confidence=1.0,
                match_strategy="exact_catalog",
                entity=entity.to_dict(),
                trace=trace + [f"matched {entity.level} by normalized_name"],
            )

        ranked = self._rank_candidates(candidates, level=level, parent_code=parent_code)
        top = ranked[0]
        same_score = [item for item in ranked if item[0] == top[0]]

        if len(same_score) == 1:
            entity = top[1]
            return ResolveResult(
                input=text,
                normalized_text=key,
                matched=True,
                status="matched",
                confidence=top[0],
                match_strategy="ranked_catalog",
                entity=entity.to_dict(),
                trace=trace + [f"ranked candidates and selected {entity.level}"],
            )

        candidate_payload = [entity.to_dict() for _, entity in ranked[:limit]]
        if strict:
            raise LookupError(f"Ambiguous territorial entity for: {text}")

        return ResolveResult(
            input=text,
            normalized_text=key,
            matched=False,
            status="ambiguous",
            confidence=0.0,
            match_strategy="exact_catalog",
            candidates=candidate_payload,
            trace=trace + [f"ambiguous match: {len(candidate_payload)} candidates"],
        )

    def _rank_candidates(
        self,
        candidates: list[TerritorialEntity],
        *,
        level: str | None,
        parent_code: str | None,
    ) -> list[tuple[float, TerritorialEntity]]:
        ranking: list[tuple[float, TerritorialEntity]] = []
        level_rank = {name: i for i, name in enumerate(SUPPORTED_LEVELS)}

        for entity in candidates:
            score = 0.80
            if entity.is_official:
                score += 0.05
            if level and entity.level == level:
                score += 0.10
            if parent_code and entity.parent_composite_code == parent_code:
                score += 0.10

            # Prefer more specific entities only when level is not constrained.
            if level is None:
                score += level_rank.get(entity.level, 0) / 1000.0

            ranking.append((round(min(score, 0.99), 3), entity))

        ranking.sort(key=lambda item: (-item[0], item[1].composite_code))
        return ranking


def load_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> list[TerritorialEntity]:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Catalog not found: {csv_path}")

    entities: list[TerritorialEntity] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized_name = normalize_text(row.get("normalized_name") or row.get("name"))
            composite_code = row.get("composite_code") or build_composite_code(row)
            level = row.get("level") or infer_level(row)

            entity = TerritorialEntity(
                region_code=str(row.get("region_code", "")).zfill(2),
                province_code=str(row.get("province_code", "")).zfill(2),
                municipality_code=str(row.get("municipality_code", "")).zfill(2),
                district_municipal_code=str(row.get("district_municipal_code", "")).zfill(2),
                section_code=str(row.get("section_code", "")).zfill(2),
                barrio_paraje_code=str(row.get("barrio_paraje_code", "")).zfill(3),
                sub_barrio_code=str(row.get("sub_barrio_code", "")).zfill(2),
                level=level,
                name=row.get("name", "") or "",
                official_name=row.get("official_name") or row.get("name", "") or "",
                normalized_name=normalized_name or "",
                parent_composite_code=row.get("parent_composite_code", "") or "",
                composite_code=composite_code,
                full_path=row.get("full_path", "") or row.get("name", "") or "",
                is_official=_coerce_bool(row.get("is_official", True)),
                source=row.get("source") or None,
                valid_from=row.get("valid_from") or None,
                valid_to=row.get("valid_to") or None,
                notes=row.get("notes") or None,
            )
            entities.append(entity)
    return entities


@lru_cache(maxsize=1)
def get_default_catalog() -> Catalog:
    return Catalog.from_csv(DEFAULT_CATALOG_PATH)


def resolve_name(
    text: str,
    *,
    level: str | None = None,
    parent_code: str | None = None,
    strict: bool = False,
    catalog: Catalog | None = None,
) -> dict[str, Any]:
    active_catalog = catalog or get_default_catalog()
    return active_catalog.resolve_name(
        text,
        level=level,
        parent_code=parent_code,
        strict=strict,
    ).to_dict()


def resolve_code(
    composite_code: str,
    *,
    catalog: Catalog | None = None,
) -> dict[str, Any] | None:
    active_catalog = catalog or get_default_catalog()
    entity = active_catalog.resolve_code(composite_code)
    return entity.to_dict() if entity else None


def search_entities(
    text: str,
    *,
    level: str | None = None,
    parent_code: str | None = None,
    limit: int = 20,
    catalog: Catalog | None = None,
) -> list[dict[str, Any]]:
    active_catalog = catalog or get_default_catalog()
    return [
        entity.to_dict()
        for entity in active_catalog.search_entities(
            text,
            level=level,
            parent_code=parent_code,
            limit=limit,
        )
    ]
