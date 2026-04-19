from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from .config import (
    COVERAGE_REPORT_OUTPUT,
    INGESTION_REPORT_OUTPUT,
    MATCH_REPORT_OUTPUT,
    PROCESSED_DATA_DIR,
)
from .geometry import locate_point_in_features
from .normalization import canonical_municipality, canonical_province


def _load_geojson(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_provinces() -> dict[str, Any]:
    return _load_geojson(PROCESSED_DATA_DIR / "provinces.geojson")


def load_municipalities() -> dict[str, Any]:
    return _load_geojson(PROCESSED_DATA_DIR / "municipalities.geojson")


def load_match_report() -> pd.DataFrame:
    return pd.read_csv(MATCH_REPORT_OUTPUT)


def load_coverage_report() -> pd.DataFrame:
    return pd.read_csv(COVERAGE_REPORT_OUTPUT)


def load_ingestion_report() -> dict[str, Any]:
    with open(INGESTION_REPORT_OUTPUT, "r", encoding="utf-8") as f:
        return json.load(f)


def get_province_names() -> list[str]:
    return [feature["properties"].get("name") for feature in load_provinces()["features"]]


def get_municipality_names() -> list[str]:
    return [feature["properties"].get("name") for feature in load_municipalities()["features"]]


def find_province_by_name(name: str) -> Optional[dict[str, Any]]:
    key = canonical_province(name)
    for feature in load_provinces()["features"]:
        if canonical_province(feature["properties"].get("name")) == key:
            return feature
    return None


def find_municipality_by_name(name: str) -> Optional[dict[str, Any]]:
    key = canonical_municipality(name)
    for feature in load_municipalities()["features"]:
        if canonical_municipality(feature["properties"].get("name")) == key:
            return feature
    return None


def locate_point(lat: float, lon: float) -> dict[str, Any]:
    provinces = load_provinces()
    municipalities = load_municipalities()

    municipality_match = locate_point_in_features(lat, lon, municipalities["features"])
    province_match = locate_point_in_features(lat, lon, provinces["features"])

    result = {
        "latitude": lat,
        "longitude": lon,
        "province": None,
        "municipality": None,
        "precision": "none",
        "status": "not_found",
    }

    if province_match is not None:
        pprops = province_match.get("properties", {})
        result["province"] = pprops.get("name")
        result["precision"] = "province"
        result["status"] = "matched"

    if municipality_match is not None:
        mprops = municipality_match.get("properties", {})
        result["municipality"] = mprops.get("name")
        result["province"] = mprops.get("province_name", result["province"])
        result["precision"] = "municipality"
        result["status"] = "matched"

    return result
