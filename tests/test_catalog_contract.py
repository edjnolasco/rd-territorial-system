from __future__ import annotations

import re

import pandas as pd
import pytest

from rd_territorial_system.catalog import get_default_catalog


EXPECTED_COLUMNS = {
    "region_code",
    "province_code",
    "municipality_code",
    "district_municipal_code",
    "section_code",
    "barrio_paraje_code",
    "sub_barrio_code",
    "level",
    "name",
    "official_name",
    "normalized_name",
    "parent_composite_code",
    "composite_code",
    "full_path",
    "is_official",
    "source",
    "valid_from",
    "valid_to",
    "notes",
}

SUPPORTED_LEVELS = {
    "province",
    "municipality",
    "district_municipal",
    "section",
    "barrio_paraje",
    "sub_barrio",
    "toponym",
}

COMPOSITE_CODE_PATTERN = re.compile(r"^\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{3}-\d{2}$")


@pytest.fixture(scope="module")
def catalog():
    return get_default_catalog()


@pytest.fixture(scope="module")
def df(catalog):
    rows = [entity.to_dict() for entity in catalog.entities]
    return pd.DataFrame(rows)


def test_catalog_is_not_empty(df: pd.DataFrame):
    assert not df.empty
    assert len(df) > 0


def test_catalog_has_expected_columns(df: pd.DataFrame):
    missing = EXPECTED_COLUMNS - set(df.columns)
    assert not missing, f"Faltan columnas en el catálogo: {sorted(missing)}"


def test_composite_code_is_unique(df: pd.DataFrame):
    duplicates = df[df["composite_code"].duplicated(keep=False)]
    assert duplicates.empty, (
        "Se encontraron composite_code duplicados:\n"
        f"{duplicates[['composite_code', 'name', 'level']].to_string(index=False)}"
    )


def test_required_fields_are_not_null_or_empty(df: pd.DataFrame):
    required_cols = [
        "region_code",
        "province_code",
        "municipality_code",
        "district_municipal_code",
        "section_code",
        "barrio_paraje_code",
        "sub_barrio_code",
        "level",
        "name",
        "normalized_name",
        "composite_code",
        "full_path",
    ]

    for col in required_cols:
        assert df[col].notna().all(), f"La columna {col} contiene nulos"
        assert (df[col].astype(str).str.strip() != "").all(), f"La columna {col} contiene vacíos"


def test_level_values_are_supported(df: pd.DataFrame):
    found_levels = set(df["level"].unique())
    invalid = found_levels - SUPPORTED_LEVELS
    assert not invalid, f"Se encontraron levels no soportados: {sorted(invalid)}"


def test_composite_code_format_is_valid(df: pd.DataFrame):
    invalid = df[~df["composite_code"].astype(str).str.match(COMPOSITE_CODE_PATTERN)]
    assert invalid.empty, (
        "Se encontraron composite_code inválidos:\n"
        f"{invalid[['composite_code', 'name', 'level']].to_string(index=False)}"
    )


def test_parent_composite_code_format_is_valid_when_present(df: pd.DataFrame):
    with_parent = df[df["parent_composite_code"].astype(str).str.strip() != ""]
    invalid = with_parent[
        ~with_parent["parent_composite_code"].astype(str).str.match(COMPOSITE_CODE_PATTERN)
    ]
    assert invalid.empty, (
        "Se encontraron parent_composite_code inválidos:\n"
        f"{invalid[['parent_composite_code', 'name', 'level']].to_string(index=False)}"
    )


def test_parent_composite_code_points_to_existing_entity(df: pd.DataFrame):
    valid_codes = set(df["composite_code"])
    with_parent = df[df["parent_composite_code"].astype(str).str.strip() != ""]
    invalid = with_parent[~with_parent["parent_composite_code"].isin(valid_codes)]

    assert invalid.empty, (
        "Se encontraron parent_composite_code que no existen en el catálogo:\n"
        f"{invalid[['parent_composite_code', 'composite_code', 'name', 'level']].to_string(index=False)}"
    )


def test_normalized_name_is_lowercase_trimmed(df: pd.DataFrame):
    normalized = df["normalized_name"].astype(str)

    assert (normalized == normalized.str.strip()).all(), "normalized_name contiene espacios laterales"
    assert (normalized == normalized.str.lower()).all(), "normalized_name no está en minúsculas"


def test_full_path_contains_name(df: pd.DataFrame):
    invalid = df[~df.apply(lambda row: str(row["name"]) in str(row["full_path"]), axis=1)]
    assert invalid.empty, (
        "Se encontraron filas donde full_path no contiene el name:\n"
        f"{invalid[['name', 'full_path', 'composite_code']].to_string(index=False)}"
    )


def test_province_rows_have_empty_parent(df: pd.DataFrame):
    provinces = df[df["level"] == "province"]
    invalid = provinces[provinces["parent_composite_code"].astype(str).str.strip() != ""]

    assert invalid.empty, (
        "Las filas de province no deben tener parent_composite_code:\n"
        f"{invalid[['name', 'parent_composite_code', 'composite_code']].to_string(index=False)}"
    )


def test_non_province_rows_have_parent(df: pd.DataFrame):
    non_provinces = df[df["level"] != "province"]
    invalid = non_provinces[non_provinces["parent_composite_code"].astype(str).str.strip() == ""]

    assert invalid.empty, (
        "Las filas no province deben tener parent_composite_code:\n"
        f"{invalid[['name', 'level', 'composite_code']].to_string(index=False)}"
    )


def test_full_path_depth_is_consistent_with_level(df: pd.DataFrame):
    expected_min_depth = {
        "province": 1,
        "municipality": 2,
        "district_municipal": 3,
        "section": 4,
        "barrio_paraje": 5,
        "sub_barrio": 6,
        "toponym": 1,
    }

    def _depth(path: str) -> int:
        return len([part.strip() for part in str(path).split(">") if part.strip()])

    invalid_rows = []
    for _, row in df.iterrows():
        depth = _depth(row["full_path"])
        min_expected = expected_min_depth[row["level"]]
        if depth < min_expected:
            invalid_rows.append((row["name"], row["level"], row["full_path"], row["composite_code"]))

    assert not invalid_rows, (
        "Se encontraron filas con full_path más corto que lo esperado:\n"
        + "\n".join(
            f"name={name} | level={level} | full_path={path} | code={code}"
            for name, level, path, code in invalid_rows
        )
    )