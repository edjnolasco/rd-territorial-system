from __future__ import annotations

import json

import pandas as pd

from .config import (
    COVERAGE_REPORT_OUTPUT,
    GADM_ADM1_ZIP,
    GADM_ADM2_ZIP,
    INGESTION_REPORT_OUTPUT,
    LOW_CONFIDENCE_OUTPUT,
    MASTER_OUTPUT,
    MATCH_REPORT_OUTPUT,
    MUNICIPALITIES_OUTPUT,
    ONE_RAW_DIR,
    PROVINCES_OUTPUT,
    UNMATCHED_MUNICIPALITIES_OUTPUT,
)
from .ingestion import (
    discover_one_main_table,
    load_geojson_from_zip,
    load_one_hierarchy_auto,
)
from .normalization import canonical_municipality, canonical_province, match_score
from .reconciliation import load_municipality_overrides
from .reporting import build_coverage_report

from .ingestion import (
    discover_one_main_table,
    load_geojson_from_zip,
    load_one_hierarchy_auto,
)

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
    lookup: dict[tuple[str, str], dict] = {}
    for feature in features:
        props = feature.get("properties", {})
        pkey = canonical_province(props.get("NAME_1") or props.get("province_name"))
        mkey = canonical_municipality(props.get("NAME_2") or props.get("name"))
        lookup[(pkey, mkey)] = feature
    return lookup


def _best_municipality_match(
    province_key: str,
    municipality_name: str,
    municipality_lookup: dict[tuple[str, str], dict],
    overrides: dict[tuple[str, str], str],
) -> tuple[dict | None, str, int]:
    direct_key = (province_key, canonical_municipality(municipality_name))

    if direct_key in overrides:
        override_key = (province_key, overrides[direct_key])
        if override_key in municipality_lookup:
            return municipality_lookup[override_key], "override", 100

    if direct_key in municipality_lookup:
        return municipality_lookup[direct_key], "direct", 100

    candidates: list[tuple[int, dict, str]] = []
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


def build_from_one_gadm(
    sheet_name: str | None = None,
    low_confidence_threshold: int = 85,
) -> dict[str, int]:
    # Descubrir explícitamente el archivo fuente usando ONE_RAW_DIR actual.
    # Esto evita depender de defaults internos difíciles de monkeypatchear en tests.
    source_path = discover_one_main_table()
    one_df, ingestion_report = load_one_hierarchy_auto(
            path=source_path,
            sheet_name=sheet_name,
    )

    gadm_adm1 = load_geojson_from_zip(GADM_ADM1_ZIP)
    gadm_adm2 = load_geojson_from_zip(GADM_ADM2_ZIP)
    overrides = load_municipality_overrides()

    province_lookup = _build_province_lookup(gadm_adm1["features"])
    municipality_lookup = _build_municipality_lookup(gadm_adm2["features"])

    provinces_out: list[dict] = []
    municipalities_out: list[dict] = []
    master_rows: list[dict] = []
    report_rows: list[dict] = []

    one_pairs = (
        one_df[["province_name", "municipality_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["province_name", "municipality_name"])
        .reset_index(drop=True)
    )

    used_provinces: set[str] = set()
    used_municipalities: set[str] = set()

    for _, row in one_pairs.iterrows():
        province_name = str(row["province_name"]).strip()
        municipality_name = str(row["municipality_name"]).strip()

        pkey = canonical_province(province_name)
        mkey = canonical_municipality(municipality_name)

        province_feature = province_lookup.get(pkey)
        municipality_feature, match_type, score = _best_municipality_match(
            pkey,
            municipality_name,
            municipality_lookup,
            overrides,
        )

        if province_feature is not None and pkey not in used_provinces:
            props = dict(province_feature.get("properties", {}))
            province_id = props.get("ID_1") or props.get("HASC_1") or pkey
            props.update(
                {
                    "id": str(province_id),
                    "name": province_name,
                    "level": 1,
                    "type_unit": "provincia",
                    "parent_id": "RD",
                    "source_semantic": "ONE",
                    "source_geometry": "GADM",
                }
            )
            provinces_out.append(
                {
                    "type": "Feature",
                    "properties": props,
                    "geometry": province_feature.get("geometry"),
                }
            )
            used_provinces.add(pkey)

        matched_municipality = municipality_feature is not None
        municipality_id = None

        if matched_municipality:
            props = dict(municipality_feature.get("properties", {}))
            province_id = props.get("ID_1") or props.get("HASC_1") or pkey
            municipality_id = (
                props.get("ID_2")
                or props.get("HASC_2")
                or f"{pkey}:{mkey}"
            )
            dedupe_key = str(municipality_id)

            if dedupe_key not in used_municipalities:
                props.update(
                    {
                        "id": str(municipality_id),
                        "name": municipality_name,
                        "level": 2,
                        "type_unit": "municipio",
                        "parent_id": str(province_id),
                        "province_name": province_name,
                        "province_key": pkey,
                        "municipality_key": mkey,
                        "match_type": match_type,
                        "match_score": score,
                        "source_semantic": "ONE",
                        "source_geometry": "GADM",
                    }
                )
                municipalities_out.append(
                    {
                        "type": "Feature",
                        "properties": props,
                        "geometry": municipality_feature.get("geometry"),
                    }
                )
                used_municipalities.add(dedupe_key)

        master_rows.append(
            {
                "province_name": province_name,
                "municipality_name": municipality_name,
                "province_key": pkey,
                "municipality_key": mkey,
                "matched_province": province_feature is not None,
                "matched_municipality": matched_municipality,
                "match_type": match_type,
                "match_score": score,
                "municipality_id": municipality_id,
            }
        )

        report_rows.append(
            {
                "entity_type": "municipality",
                "province_name": province_name,
                "municipality_name": municipality_name,
                "matched": matched_municipality,
                "match_type": match_type,
                "match_score": score,
            }
        )

    PROVINCES_OUTPUT.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": provinces_out},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    MUNICIPALITIES_OUTPUT.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": municipalities_out},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    master_df = pd.DataFrame(master_rows)
    match_df = pd.DataFrame(report_rows)

    master_df.to_csv(MASTER_OUTPUT, index=False)
    match_df.to_csv(MATCH_REPORT_OUTPUT, index=False)
    build_coverage_report(master_df).to_csv(COVERAGE_REPORT_OUTPUT, index=False)

    unmatched = master_df[master_df["matched_municipality"] == False].copy()
    low_confidence = master_df[
        (master_df["matched_municipality"] == True)
        & (master_df["match_score"] < low_confidence_threshold)
        & (master_df["match_type"] != "override")
    ].copy()

    unmatched.to_csv(UNMATCHED_MUNICIPALITIES_OUTPUT, index=False)
    low_confidence.to_csv(LOW_CONFIDENCE_OUTPUT, index=False)

    ingestion_report["rows_input"] = int(len(one_df))
    ingestion_report["rows_used_unique_pairs"] = int(len(one_pairs))
    ingestion_report["rows_matched_municipality"] = int(
        master_df["matched_municipality"].fillna(False).sum()
    )
    ingestion_report["rows_unmatched_municipality"] = int(
        (master_df["matched_municipality"] == False).sum()
    )
    ingestion_report["rows_low_confidence"] = int(len(low_confidence))
    ingestion_report["override_count"] = int(
        (master_df["match_type"] == "override").sum()
    )

    INGESTION_REPORT_OUTPUT.write_text(
        json.dumps(ingestion_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "provinces_output": len(provinces_out),
        "municipalities_output": len(municipalities_out),
        "master_rows": len(master_rows),
        "municipality_unmatched": int(
            (master_df["matched_municipality"] == False).sum()
        ),
        "low_confidence_rows": int(len(low_confidence)),
    }