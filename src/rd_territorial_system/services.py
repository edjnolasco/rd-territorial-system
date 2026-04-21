from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import (
    COVERAGE_REPORT_OUTPUT,
    INGESTION_REPORT_OUTPUT,
    LOW_CONFIDENCE_OUTPUT,
    MATCH_REPORT_OUTPUT,
    PROCESSED_DATA_DIR,
    UNMATCHED_MUNICIPALITIES_OUTPUT,
)
from .geometry import locate_point_in_features
from .normalization import canonical_municipality, canonical_province


def _load_geojson(path: Path) -> dict[str, Any]:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _load_csv(path: Path) -> pd.DataFrame:
    path = Path(path)
    return pd.read_csv(path)


def load_provinces() -> dict[str, Any]:
    return _load_geojson(PROCESSED_DATA_DIR / "provinces.geojson")


def load_municipalities() -> dict[str, Any]:
    return _load_geojson(PROCESSED_DATA_DIR / "municipalities.geojson")


def load_match_report() -> pd.DataFrame:
    return _load_csv(MATCH_REPORT_OUTPUT)


def load_coverage_report() -> pd.DataFrame:
    return _load_csv(COVERAGE_REPORT_OUTPUT)


def load_ingestion_report() -> dict[str, Any]:
    with open(INGESTION_REPORT_OUTPUT, "r", encoding="utf-8") as file:
        return json.load(file)


def load_unmatched_municipalities() -> pd.DataFrame:
    return _load_csv(UNMATCHED_MUNICIPALITIES_OUTPUT)


def load_low_confidence_matches() -> pd.DataFrame:
    return _load_csv(LOW_CONFIDENCE_OUTPUT)


def get_province_names() -> list[str]:
    features = load_provinces().get("features", [])
    return [
        feature.get("properties", {}).get("name")
        for feature in features
        if feature.get("properties", {}).get("name")
    ]


def get_municipality_names() -> list[str]:
    features = load_municipalities().get("features", [])
    return [
        feature.get("properties", {}).get("name")
        for feature in features
        if feature.get("properties", {}).get("name")
    ]


def find_province_by_name(name: str) -> dict[str, Any] | None:
    key = canonical_province(name)
    if key is None:
        return None

    for feature in load_provinces().get("features", []):
        feature_name = feature.get("properties", {}).get("name")
        if canonical_province(feature_name) == key:
            return feature

    return None


def find_municipality_by_name(name: str) -> dict[str, Any] | None:
    key = canonical_municipality(name)
    if key is None:
        return None

    for feature in load_municipalities().get("features", []):
        feature_name = feature.get("properties", {}).get("name")
        if canonical_municipality(feature_name) == key:
            return feature

    return None


def locate_point(lat: float, lon: float) -> dict[str, Any]:
    provinces = load_provinces()
    municipalities = load_municipalities()

    province_features = provinces.get("features", [])
    municipality_features = municipalities.get("features", [])

    municipality_match = locate_point_in_features(lat, lon, municipality_features)
    province_match = locate_point_in_features(lat, lon, province_features)

    result: dict[str, Any] = {
        "latitude": lat,
        "longitude": lon,
        "province": None,
        "province_id": None,
        "municipality": None,
        "municipality_id": None,
        "precision": "none",
        "status": "not_found",
    }

    if province_match is not None:
        province_props = province_match.get("properties", {})
        result["province"] = province_props.get("name")
        result["province_id"] = province_props.get("id")
        result["precision"] = "province"
        result["status"] = "matched"

    if municipality_match is not None:
        municipality_props = municipality_match.get("properties", {})
        result["municipality"] = municipality_props.get("name")
        result["municipality_id"] = municipality_props.get("id")
        result["province"] = municipality_props.get("province_name", result["province"])
        result["precision"] = "municipality"
        result["status"] = "matched"

    return result
