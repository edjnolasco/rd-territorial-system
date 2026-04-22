from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest


CATALOG_CANDIDATES = [
    Path("data/catalog/current/rd_territorial_master_candidate.parquet"),
    Path("data/catalog/current/rd_territorial_master.parquet"),
    Path("data/catalog/current/rd_territorial_master_candidate.csv"),
    Path("data/catalog/current/rd_territorial_master.csv"),
]

REQUIRED_COLUMNS = {
    "composite_code",
    "parent_composite_code",
    "level",
    "name",
}

EXPECTED_LEVELS = {
    "province",
    "municipality",
    "district_municipal",
    "section",
    "barrio_paraje",
    "sub_barrio",
    "toponym",
}


def _find_catalog_path() -> Path:
    env_path = os.getenv("RD_CATALOG_UNDER_TEST")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        raise FileNotFoundError(
            f"RD_CATALOG_UNDER_TEST apunta a una ruta inexistente: {path}"
        )

    for path in CATALOG_CANDIDATES:
        if path.exists():
            return path

    raise FileNotFoundError(
        "No se encontró el catálogo maestro/candidato en ninguna de las rutas esperadas: "
        f"{[str(p) for p in CATALOG_CANDIDATES]}"
    )


def _load_catalog() -> pd.DataFrame:
    path = _find_catalog_path()

    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, dtype=str)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise AssertionError(
            f"El catálogo no contiene las columnas mínimas requeridas para estas reglas: {sorted(missing)}"
        )

    df = df.copy()
    for col in REQUIRED_COLUMNS:
        df[col] = df[col].astype("string")

    return df


@pytest.fixture(scope="module")
def catalog_df() -> pd.DataFrame:
    return _load_catalog()


def test_catalog_has_unique_identity_by_composite_code(catalog_df: pd.DataFrame) -> None:
    duplicated = catalog_df[catalog_df["composite_code"].duplicated(keep=False)]

    assert duplicated.empty, (
        "El catálogo tiene colisiones de identidad por composite_code. "
        f"Ejemplos:\n{duplicated[['composite_code', 'name', 'level']].head(20).to_string(index=False)}"
    )


def test_catalog_does_not_require_unique_name(catalog_df: pd.DataFrame) -> None:
    repeated_names = catalog_df.groupby("name", dropna=False)["composite_code"].nunique()
    repeated_names = repeated_names[repeated_names > 1]

    assert len(repeated_names) > 0, (
        "No se detectaron nombres repetidos. "
        "Este test protege la regla de que name no es identidad."
    )


def test_repeated_names_do_not_collapse_identity(catalog_df: pd.DataFrame) -> None:
    repeated = catalog_df.groupby("name", dropna=False).filter(
        lambda x: x["composite_code"].nunique() > 1
    )

    if repeated.empty:
        pytest.skip("No hay nombres repetidos en este catálogo todavía.")

    collisions = repeated.groupby("name")["composite_code"].apply(
        lambda s: s.duplicated().any()
    )
    bad = collisions[collisions]

    assert bad.empty, (
        "Se detectó colapso indebido de identidad dentro de nombres repetidos. "
        f"Nombres afectados: {bad.index.tolist()[:20]}"
    )


def test_parent_composite_code_exists_for_non_root_rows(catalog_df: pd.DataFrame) -> None:
    roots = catalog_df["parent_composite_code"].isna() | (
        catalog_df["parent_composite_code"].str.strip() == ""
    )
    non_roots = catalog_df.loc[~roots].copy()

    missing_parent = non_roots.loc[
        ~non_roots["parent_composite_code"].isin(catalog_df["composite_code"])
    ]

    assert missing_parent.empty, (
        "Hay filas con parent_composite_code inexistente. "
        f"Ejemplos:\n{missing_parent[['composite_code', 'parent_composite_code', 'name', 'level']].head(20).to_string(index=False)}"
    )


def test_level_names_are_valid(catalog_df: pd.DataFrame) -> None:
    invalid = sorted(set(catalog_df["level"].dropna().unique()) - EXPECTED_LEVELS)

    assert not invalid, f"Se detectaron level no esperados: {invalid}"


def test_dn_baseline_still_exists(catalog_df: pd.DataFrame) -> None:
    dn_rows = catalog_df[
        catalog_df["name"].str.contains("Distrito Nacional", case=False, na=False)
    ]

    assert not dn_rows.empty, "DN desapareció del catálogo, lo cual no debe ocurrir."


def test_catalog_keeps_identity_even_when_name_case_varies(catalog_df: pd.DataFrame) -> None:
    temp = catalog_df.copy()
    temp["name_folded"] = temp["name"].str.strip().str.casefold()

    folded_repeated = temp.groupby("name_folded")["composite_code"].nunique()
    folded_repeated = folded_repeated[folded_repeated > 1]

    if folded_repeated.empty:
        pytest.skip("No hay variantes visibles por capitalización en este catálogo.")

    bad_groups = []
    for folded_name in folded_repeated.index:
        subset = temp[temp["name_folded"] == folded_name]
        if subset["composite_code"].duplicated().any():
            bad_groups.append(folded_name)

    assert not bad_groups, (
        "Se detectaron grupos donde variantes de capitalización parecen haber colapsado identidad. "
        f"Grupos afectados: {bad_groups[:20]}"
    )


def test_no_name_based_uniqueness_constraint(catalog_df: pd.DataFrame) -> None:
    unique_names = catalog_df["name"].nunique(dropna=False)
    total_rows = len(catalog_df)

    assert unique_names < total_rows, (
        "El catálogo parece estar forzando unicidad por name o no contiene repetidos; "
        "esto sería riesgoso para el modelo nacional."
    )


def test_root_levels_have_no_parent(catalog_df: pd.DataFrame) -> None:
    province_rows = catalog_df[catalog_df["level"] == "province"].copy()

    assert not province_rows.empty, "No se encontraron filas de nivel province."

    has_parent = province_rows["parent_composite_code"].notna() & (
        province_rows["parent_composite_code"].str.strip() != ""
    )

    bad = province_rows.loc[has_parent]

    assert bad.empty, (
        "Las filas de nivel province no deben tener parent_composite_code. "
        f"Ejemplos:\n{bad[['composite_code', 'parent_composite_code', 'name']].head(20).to_string(index=False)}"
    )