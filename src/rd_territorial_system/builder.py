from __future__ import annotations

import json
import pandas as pd

from .config import (
    COVERAGE_REPORT_OUTPUT,
    DISTRICT_MUNICIPALS_OUTPUT,
    GADM_ADM1_ZIP,
    GADM_ADM2_ZIP,
    INGESTION_REPORT_OUTPUT,
    MASTER_OUTPUT,
    MATCH_REPORT_OUTPUT,
    MUNICIPALITIES_OUTPUT,
    ONE_DISTRICT_RAW_CSV,
    PROVINCES_OUTPUT,
)
from .ingestion import load_geojson_from_zip, load_one_district_csv, load_one_hierarchy_auto
from .normalization import (
    canonical_district_municipal,
    canonical_municipality,
    canonical_province,
    match_score,
)
from .reporting import build_coverage_report


def _feature_name(feature: dict, *keys: str) -> str:
    props = feature.get("properties", {})
    for key in keys:
        value = props.get(key)
        if value:
            return str(value)
    raise ValueError("Feature sin nombre utilizable")


def _build_province_lookup(features: list[dict]) -> dict[str, dict]:
    return {
        canonical_province(_feature_name(feature, "NAME_1", "name")): feature
        for feature in features
    }


def _build_municipality_lookup(features: list[dict]) -> dict[tuple[str, str], dict]:
    lookup = {}
    for feature in features:
        props = feature.get("properties", {})
        pkey = canonical_province(props.get("NAME_1") or props.get("province_name"))
        mkey = canonical_municipality(props.get("NAME_2") or props.get("name"))
        lookup[(pkey, mkey)] = feature
    return lookup


def _best_municipality_match(province_key: str, municipality_name: str, municipality_lookup: dict[tuple[str, str], dict]):
    direct_key = (province_key, canonical_municipality(municipality_name))
    if direct_key in municipality_lookup:
        return municipality_lookup[direct_key], "direct", 100

    candidates = []
    for (pkey, mkey), feature in municipality_lookup.items():
        if pkey != province_key:
            continue
        score = match_score(municipality_name, mkey)
        if score > 0:
            candidates.append((score, feature, mkey))

    if not candidates:
        return None, "unmatched", 0

    candidates.sort(key=lambda x: x[0], reverse=True)
    score, feature, _ = candidates[0]
    return feature, "fuzzy", score


def build_from_one_gadm(sheet_name: str | None = None) -> dict[str, int]:
    one_df, ingestion_report = load_one_hierarchy_auto(sheet_name=sheet_name)
    gadm_adm1 = load_geojson_from_zip(GADM_ADM1_ZIP)
    gadm_adm2 = load_geojson_from_zip(GADM_ADM2_ZIP)

    province_lookup = _build_province_lookup(gadm_adm1["features"])
    municipality_lookup = _build_municipality_lookup(gadm_adm2["features"])

    provinces_out = []
    municipalities_out = []
    master_rows = []
    report_rows = []

    one_pairs = (
        one_df[["province_name", "municipality_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["province_name", "municipality_name"])
    )

    used_provinces = set()
    used_municipalities = set()

    for _, row in one_pairs.iterrows():
        province_name = str(row["province_name"]).strip()
        municipality_name = str(row["municipality_name"]).strip()

        pkey = canonical_province(province_name)
        province_feature = province_lookup.get(pkey)
        municipality_feature, match_type, score = _best_municipality_match(
            pkey, municipality_name, municipality_lookup
        )

        if province_feature is not None and pkey not in used_provinces:
            props = dict(province_feature.get("properties", {}))
            province_id = props.get("ID_1") or props.get("HASC_1") or pkey
            props.update({
                "id": str(province_id),
                "name": province_name,
                "level": 1,
                "type_unit": "provincia",
                "parent_id": "RD",
                "source_semantic": "ONE",
                "source_geometry": "GADM",
            })
            provinces_out.append({
                "type": "Feature",
                "properties": props,
                "geometry": province_feature.get("geometry"),
            })
            used_provinces.add(pkey)

        matched_municipality = municipality_feature is not None
        municipality_id = None

        if matched_municipality:
            props = dict(municipality_feature.get("properties", {}))
            province_id = props.get("ID_1") or props.get("HASC_1") or pkey
            municipality_id = props.get("ID_2") or props.get("HASC_2") or f"{pkey}:{canonical_municipality(municipality_name)}"
            dedupe_key = str(municipality_id)

            if dedupe_key not in used_municipalities:
                props.update({
                    "id": str(municipality_id),
                    "name": municipality_name,
                    "level": 2,
                    "type_unit": "municipio",
                    "parent_id": str(province_id),
                    "province_name": province_name,
                    "province_key": pkey,
                    "municipality_key": canonical_municipality(municipality_name),
                    "match_type": match_type,
                    "match_score": score,
                    "source_semantic": "ONE",
                    "source_geometry": "GADM",
                })
                municipalities_out.append({
                    "type": "Feature",
                    "properties": props,
                    "geometry": municipality_feature.get("geometry"),
                })
                used_municipalities.add(dedupe_key)

        master_rows.append({
            "province_name": province_name,
            "municipality_name": municipality_name,
            "province_key": pkey,
            "municipality_key": canonical_municipality(municipality_name),
            "matched_province": province_feature is not None,
            "matched_municipality": matched_municipality,
            "match_type": match_type,
            "match_score": score,
            "municipality_id": municipality_id,
        })

        report_rows.append({
            "entity_type": "municipality",
            "province_name": province_name,
            "municipality_name": municipality_name,
            "matched": matched_municipality,
            "match_type": match_type,
            "match_score": score,
        })

    PROVINCES_OUTPUT.write_text(
        json.dumps({"type": "FeatureCollection", "features": provinces_out}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    MUNICIPALITIES_OUTPUT.write_text(
        json.dumps({"type": "FeatureCollection", "features": municipalities_out}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    master_df = pd.DataFrame(master_rows)
    master_df.to_csv(MASTER_OUTPUT, index=False)
    pd.DataFrame(report_rows).to_csv(MATCH_REPORT_OUTPUT, index=False)
    build_coverage_report(master_df).to_csv(COVERAGE_REPORT_OUTPUT, index=False)

    ingestion_report["rows_input"] = int(len(one_df))
    ingestion_report["rows_used_unique_pairs"] = int(len(one_pairs))
    ingestion_report["rows_matched_municipality"] = int(master_df["matched_municipality"].fillna(False).sum())
    INGESTION_REPORT_OUTPUT.write_text(json.dumps(ingestion_report, ensure_ascii=False, indent=2), encoding="utf-8")

    district_rows = []
    if ONE_DISTRICT_RAW_CSV.exists():
        districts_df = load_one_district_csv(ONE_DISTRICT_RAW_CSV)
        for _, row in districts_df.iterrows():
            district_rows.append({
                "province_name": str(row["province_name"]).strip(),
                "municipality_name": str(row["municipality_name"]).strip(),
                "district_municipal_name": str(row["district_municipal_name"]).strip(),
                "province_key": canonical_province(row["province_name"]),
                "municipality_key": canonical_municipality(row["municipality_name"]),
                "district_key": canonical_district_municipal(row["district_municipal_name"]),
            })
        pd.DataFrame(district_rows).to_csv(DISTRICT_MUNICIPALS_OUTPUT, index=False)

    return {
        "provinces_output": len(provinces_out),
        "municipalities_output": len(municipalities_out),
        "master_rows": len(master_rows),
        "municipality_unmatched": int((master_df["matched_municipality"] == False).sum()),
        "district_rows": len(district_rows),
    }
