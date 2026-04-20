from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Literal

import pandas as pd
import yaml

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

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PACKAGE_ROOT / "data"
CATALOG_ROOT = DATA_ROOT / "catalog"
REGISTRY_PATH = CATALOG_ROOT / "registry.json"

CURRENT_CATALOG_DIRNAME = "current"
PARQUET_FILENAME = "rd_territorial_master.parquet"
CSV_FILENAME = "rd_territorial_master.csv"
ALIASES_DIRNAME = "aliases"

TEXT_FILE_ENCODINGS: tuple[str, ...] = (
    "utf-8-sig",
    "utf-8",
    "cp1252",
    "latin-1",
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
        payload = asdict(self)
        payload["parent_path"] = self.parent_path
        return payload


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
        payload["candidates"] = self.candidates or []
        return payload


@dataclass(frozen=True)
class CatalogVersionInfo:
    active_version: str
    available_versions: tuple[str, ...]
    base_dir: Path
    catalog_parquet_path: Path
    catalog_csv_path: Path
    aliases_dir: Path


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "si", "sí"}


def _normalize_code(value: Any, width: int) -> str:
    text = str(value or "").strip()
    if text == "":
        return "0".zfill(width)
    return text.zfill(width)


def build_composite_code(row: dict[str, Any]) -> str:
    return "-".join(
        [
            _normalize_code(row.get("region_code"), 2),
            _normalize_code(row.get("province_code"), 2),
            _normalize_code(row.get("municipality_code"), 2),
            _normalize_code(row.get("district_municipal_code"), 2),
            _normalize_code(row.get("section_code"), 2),
            _normalize_code(row.get("barrio_paraje_code"), 3),
            _normalize_code(row.get("sub_barrio_code"), 2),
        ]
    )


def infer_level(row: dict[str, Any]) -> str:
    sub_barrio_code = _normalize_code(row.get("sub_barrio_code"), 2)
    barrio_paraje_code = _normalize_code(row.get("barrio_paraje_code"), 3)
    section_code = _normalize_code(row.get("section_code"), 2)
    district_municipal_code = _normalize_code(row.get("district_municipal_code"), 2)
    municipality_code = _normalize_code(row.get("municipality_code"), 2)
    province_code = _normalize_code(row.get("province_code"), 2)

    if sub_barrio_code != "00":
        return "sub_barrio"
    if barrio_paraje_code != "000":
        return "barrio_paraje"
    if section_code != "00":
        return "section"
    if district_municipal_code != "00":
        return "district_municipal"
    if municipality_code != "00":
        return "municipality"
    if province_code != "00":
        return "province"
    return "toponym"


def _read_text_file_with_fallback(path: Path) -> str:
    last_error: UnicodeDecodeError | None = None

    for encoding in TEXT_FILE_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(
        f"Could not decode text file {path} with encodings {TEXT_FILE_ENCODINGS}. "
        f"Last error: {last_error}"
    )


def _open_csv_with_fallback(path: Path) -> list[dict[str, Any]]:
    last_error: UnicodeDecodeError | None = None

    for encoding in TEXT_FILE_ENCODINGS:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return list(reader)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(
        f"Could not decode CSV file {path} with encodings {TEXT_FILE_ENCODINGS}. "
        f"Last error: {last_error}"
    )


def load_registry(path: str | Path = REGISTRY_PATH) -> dict[str, Any]:
    registry_path = Path(path)

    if not registry_path.exists():
        return {
            "default": CURRENT_CATALOG_DIRNAME,
            "available": [CURRENT_CATALOG_DIRNAME],
        }

    raw_text = _read_text_file_with_fallback(registry_path)
    data = json.loads(raw_text)

    default_version = data.get("default") or CURRENT_CATALOG_DIRNAME
    available_versions = data.get("available") or [default_version]

    return {
        "default": default_version,
        "available": available_versions,
    }


def resolve_catalog_version(
    version: str | None = None,
    *,
    registry_path: str | Path = REGISTRY_PATH,
) -> CatalogVersionInfo:
    registry = load_registry(registry_path)
    active_version = version or registry["default"]

    if active_version == CURRENT_CATALOG_DIRNAME:
        base_dir = CATALOG_ROOT / CURRENT_CATALOG_DIRNAME
    else:
        base_dir = CATALOG_ROOT / "versions" / active_version

    return CatalogVersionInfo(
        active_version=active_version,
        available_versions=tuple(registry["available"]),
        base_dir=base_dir,
        catalog_parquet_path=base_dir / PARQUET_FILENAME,
        catalog_csv_path=base_dir / CSV_FILENAME,
        aliases_dir=base_dir / ALIASES_DIRNAME,
    )


def _load_alias_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    raw_text = _read_text_file_with_fallback(path)
    raw = yaml.safe_load(raw_text) or {}

    aliases = raw.get("aliases", {})
    resolved: dict[str, str] = {}

    for key, value in aliases.items():
        normalized_key = normalize_text(key)
        normalized_value = normalize_text(value)
        if normalized_key and normalized_value:
            resolved[normalized_key] = normalized_value

    return resolved


def load_aliases(aliases_dir: str | Path) -> dict[str, dict[str, str]]:
    base = Path(aliases_dir)

    return {
        "province": _load_alias_file(base / "provinces.yml"),
        "municipality": _load_alias_file(base / "municipalities.yml"),
        "district_municipal": _load_alias_file(base / "districts.yml"),
        "section": _load_alias_file(base / "sections.yml"),
        "barrio_paraje": _load_alias_file(base / "barrios.yml"),
        "sub_barrio": _load_alias_file(base / "subbarrios.yml"),
        "toponym": _load_alias_file(base / "toponyms.yml"),
    }


def apply_alias(text: str | None, aliases: dict[str, str]) -> str | None:
    normalized = normalize_text(text)
    if not normalized:
        return None
    return aliases.get(normalized, normalized)


def _entity_from_row(row: dict[str, Any]) -> TerritorialEntity:
    normalized_name = normalize_text(row.get("normalized_name") or row.get("name")) or ""

    return TerritorialEntity(
        region_code=_normalize_code(row.get("region_code"), 2),
        province_code=_normalize_code(row.get("province_code"), 2),
        municipality_code=_normalize_code(row.get("municipality_code"), 2),
        district_municipal_code=_normalize_code(row.get("district_municipal_code"), 2),
        section_code=_normalize_code(row.get("section_code"), 2),
        barrio_paraje_code=_normalize_code(row.get("barrio_paraje_code"), 3),
        sub_barrio_code=_normalize_code(row.get("sub_barrio_code"), 2),
        level=str(row.get("level") or infer_level(row)),
        name=str(row.get("name") or ""),
        official_name=str(row.get("official_name") or row.get("name") or ""),
        normalized_name=normalized_name,
        parent_composite_code=str(row.get("parent_composite_code") or ""),
        composite_code=str(row.get("composite_code") or build_composite_code(row)),
        full_path=str(row.get("full_path") or row.get("name") or ""),
        is_official=_coerce_bool(row.get("is_official", True)),
        source=str(row.get("source")) if row.get("source") not in (None, "") else None,
        valid_from=str(row.get("valid_from")) if row.get("valid_from") not in (None, "") else None,
        valid_to=str(row.get("valid_to")) if row.get("valid_to") not in (None, "") else None,
        notes=str(row.get("notes")) if row.get("notes") not in (None, "") else None,
    )


def load_catalog_rows(version_info: CatalogVersionInfo) -> list[dict[str, Any]]:
    if version_info.catalog_parquet_path.exists():
        df = pd.read_parquet(version_info.catalog_parquet_path)
        return df.fillna("").to_dict(orient="records")

    if version_info.catalog_csv_path.exists():
        return _open_csv_with_fallback(version_info.catalog_csv_path)

    raise FileNotFoundError(
        "Catalog file not found. Expected one of: "
        f"{version_info.catalog_parquet_path} or {version_info.catalog_csv_path}"
    )


def load_catalog(
    *,
    version: str | None = None,
    registry_path: str | Path = REGISTRY_PATH,
) -> list[TerritorialEntity]:
    version_info = resolve_catalog_version(version, registry_path=registry_path)
    rows = load_catalog_rows(version_info)
    return [_entity_from_row(row) for row in rows]


class Catalog:
    def __init__(
        self,
        entities: Iterable[TerritorialEntity],
        *,
        aliases_by_level: dict[str, dict[str, str]] | None = None,
        active_version: str = CURRENT_CATALOG_DIRNAME,
    ):
        self.entities = list(entities)
        self.aliases_by_level = aliases_by_level or {}
        self.active_version = active_version

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
    def from_version(
        cls,
        version: str | None = None,
        *,
        registry_path: str | Path = REGISTRY_PATH,
    ) -> "Catalog":
        version_info = resolve_catalog_version(version, registry_path=registry_path)
        entities = load_catalog(version=version, registry_path=registry_path)
        aliases_by_level = load_aliases(version_info.aliases_dir)

        return cls(
            entities,
            aliases_by_level=aliases_by_level,
            active_version=version_info.active_version,
        )

    def resolve_code(self, composite_code: str) -> TerritorialEntity | None:
        return self.by_code.get(composite_code)

    def _resolve_search_key(self, text: str, *, level: str | None = None) -> str | None:
        normalized = normalize_text(text)
        if not normalized:
            return None

        if level:
            aliases = self.aliases_by_level.get(level, {})
            return aliases.get(normalized, normalized)

        for candidate_level in SUPPORTED_LEVELS:
            aliases = self.aliases_by_level.get(candidate_level, {})
            if normalized in aliases:
                return aliases[normalized]

        return normalized

    def search_entities(
        self,
        text: str,
        *,
        level: str | None = None,
        parent_code: str | None = None,
        limit: int = 20,
    ) -> list[TerritorialEntity]:
        if level is not None and level not in SUPPORTED_LEVELS:
            raise ValueError(f"Unsupported level: {level}")

        key = self._resolve_search_key(text, level=level)
        if not key:
            return []

        if level and parent_code:
            items = [
                entity
                for entity in self.by_name_level.get((key, level), [])
                if entity.parent_composite_code == parent_code
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
        normalized_text = normalize_text(text)
        resolved_key = self._resolve_search_key(text, level=level)

        trace = [f"normalized input -> {normalized_text!r}"]
        if resolved_key and resolved_key != normalized_text:
            trace.append(f"applied alias -> {resolved_key!r}")

        if not resolved_key:
            if strict:
                raise ValueError("Input text is empty after normalization")

            return ResolveResult(
                input=text,
                normalized_text=normalized_text,
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
                normalized_text=resolved_key,
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
                normalized_text=resolved_key,
                matched=True,
                status="matched",
                confidence=1.0,
                match_strategy="exact_catalog",
                entity=entity.to_dict(),
                trace=trace + [f"matched {entity.level} by normalized_name"],
            )

        ranked = self._rank_candidates(candidates, level=level, parent_code=parent_code)
        top_score, top_entity = ranked[0]
        same_score = [item for item in ranked if item[0] == top_score]

        if len(same_score) == 1:
            return ResolveResult(
                input=text,
                normalized_text=resolved_key,
                matched=True,
                status="matched",
                confidence=top_score,
                match_strategy="ranked_catalog",
                entity=top_entity.to_dict(),
                trace=trace + [f"ranked candidates and selected {top_entity.level}"],
            )

        candidate_payload = [entity.to_dict() for _, entity in ranked[:limit]]

        if strict:
            raise LookupError(f"Ambiguous territorial entity for: {text}")

        return ResolveResult(
            input=text,
            normalized_text=resolved_key,
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
        specificity_rank = {name: i for i, name in enumerate(SUPPORTED_LEVELS)}

        for entity in candidates:
            score = 0.80

            if entity.is_official:
                score += 0.05
            if level and entity.level == level:
                score += 0.10
            if parent_code and entity.parent_composite_code == parent_code:
                score += 0.10

            if level is None:
                score += specificity_rank.get(entity.level, 0) / 1000.0

            ranking.append((round(min(score, 0.99), 3), entity))

        ranking.sort(key=lambda item: (-item[0], item[1].composite_code))
        return ranking


@lru_cache(maxsize=8)
def get_catalog(version: str | None = None) -> Catalog:
    return Catalog.from_version(version=version)


def get_default_catalog() -> Catalog:
    registry = load_registry(REGISTRY_PATH)
    default_version = registry.get("default") or CURRENT_CATALOG_DIRNAME
    return get_catalog(default_version)


def resolve_name(
    text: str,
    *,
    level: str | None = None,
    parent_code: str | None = None,
    strict: bool = False,
    version: str | None = None,
    catalog: Catalog | None = None,
) -> dict[str, Any]:
    active_catalog = catalog or (get_catalog(version) if version else get_default_catalog())
    return active_catalog.resolve_name(
        text,
        level=level,
        parent_code=parent_code,
        strict=strict,
    ).to_dict()


def resolve_code(
    composite_code: str,
    *,
    version: str | None = None,
    catalog: Catalog | None = None,
) -> dict[str, Any] | None:
    active_catalog = catalog or (get_catalog(version) if version else get_default_catalog())
    entity = active_catalog.resolve_code(composite_code)
    return entity.to_dict() if entity else None


def search_entities(
    text: str,
    *,
    level: str | None = None,
    parent_code: str | None = None,
    limit: int = 20,
    version: str | None = None,
    catalog: Catalog | None = None,
) -> list[dict[str, Any]]:
    active_catalog = catalog or (get_catalog(version) if version else get_default_catalog())
    return [
        entity.to_dict()
        for entity in active_catalog.search_entities(
            text,
            level=level,
            parent_code=parent_code,
            limit=limit,
        )
    ]