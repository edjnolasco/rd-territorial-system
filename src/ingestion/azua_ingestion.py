from __future__ import annotations

from pathlib import Path

import pandas as pd

from .territorial_txt import read_territorial_txt, territorial_rows_to_dataframe

AZUA_REQUIRED_COLUMNS = {
    "region_code",
    "province_code",
    "municipality_code",
    "district_municipal_code",
    "section_code",
    "barrio_paraje_code",
    "sub_barrio_code",
    "raw_name",
    "display_name",
    "raw_code",
    "composite_code",
    "parent_composite_code",
    "level_depth",
    "level_name",
    "is_municipal_seat",
    "source_line_number",
}


def build_azua_dataframe(path: str | Path) -> pd.DataFrame:
    rows = read_territorial_txt(path)
    df = territorial_rows_to_dataframe(rows)

    validate_azua_batch(df)

    # metadatos de batch
    df["source_file"] = Path(path).name
    df["source_province_name"] = "Azua"
    df["source_province_code"] = "02"

    return df


def validate_azua_batch(df: pd.DataFrame) -> None:
    if df.empty:
        raise AssertionError("El batch de Azua quedó vacío")

    missing = AZUA_REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise AssertionError(f"Faltan columnas requeridas: {sorted(missing)}")

    if df["raw_code"].duplicated().any():
        dupes = df.loc[df["raw_code"].duplicated(), "raw_code"].tolist()
        raise AssertionError(f"Duplicados por raw_code: {dupes[:10]}")

    if df["composite_code"].duplicated().any():
        dupes = df.loc[df["composite_code"].duplicated(), "composite_code"].tolist()
        raise AssertionError(f"Duplicados por composite_code: {dupes[:10]}")

    if set(df["province_code"]) != {"02"}:
        raise AssertionError("El archivo de Azua contiene province_code distinto de 02")

    valid_levels = {
        "province",
        "municipality",
        "district_municipal",
        "section",
        "barrio_paraje",
        "sub_barrio",
    }
    if not df["level_name"].isin(valid_levels).all():
        invalid = sorted(
            df.loc[~df["level_name"].isin(valid_levels), "level_name"].unique()
        )
        raise AssertionError(f"Niveles inválidos detectados: {invalid}")

    # todo padre debe existir dentro del mismo batch
    missing_parents = df.loc[
        df["parent_composite_code"].notna()
        & ~df["parent_composite_code"].isin(df["composite_code"])
    ]
    if not missing_parents.empty:
        sample = missing_parents[
            ["raw_code", "composite_code", "parent_composite_code"]
        ].head(10)
        raise AssertionError(
            f"Padres inexistentes detectados:\n{sample.to_string(index=False)}"
        )

    expected_counts = {
        "province": 1,
        "municipality": 10,
    }
    for level_name, expected in expected_counts.items():
        observed = int((df["level_name"] == level_name).sum())
        if observed != expected:
            raise AssertionError(
                f"Conteo inesperado para {level_name}: esperado={expected}, observado={observed}"
            )


# ----------------------------------------------------------------------
# 🔥 CSV-ONLY APPEND
# ----------------------------------------------------------------------
def append_catalog_batch(
    master_catalog_path: str | Path,
    batch_df: pd.DataFrame,
) -> pd.DataFrame:
    master_path = Path(master_catalog_path)

    if not master_path.exists():
        raise AssertionError(f"No existe el catálogo maestro: {master_path}")

    # 🔥 SOLO CSV
    master_df = pd.read_csv(master_path, dtype=str, encoding="utf-8-sig").fillna("")

    required_master_columns = {
        "composite_code",
        "parent_composite_code",
        "level_name",
        "display_name",
    }
    missing_master = required_master_columns - set(master_df.columns)
    if missing_master:
        raise AssertionError(
            f"El catálogo maestro no contiene columnas requeridas para append: {sorted(missing_master)}"
        )

    collisions = set(master_df["composite_code"]).intersection(
        set(batch_df["composite_code"])
    )
    if collisions:
        sample = sorted(collisions)[:20]
        raise AssertionError(
            f"Colisión de composite_code contra catálogo maestro: {sample}"
        )

    combined = pd.concat([master_df, batch_df], ignore_index=True, sort=False)

    if combined["composite_code"].duplicated().any():
        dupes = combined.loc[
            combined["composite_code"].duplicated(), "composite_code"
        ].tolist()
        raise AssertionError(
            f"El append produjo composite_code duplicados: {dupes[:20]}"
        )

    return combined