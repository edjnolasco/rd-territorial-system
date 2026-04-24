from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

MASTER_CSV = Path("data/catalog/current/rd_territorial_master.csv")
MANIFEST_PATH = Path("data/catalog/config/provinces_manifest.json")


def _load_master() -> pd.DataFrame:
    assert MASTER_CSV.exists(), f"No existe CSV master: {MASTER_CSV}"
    return pd.read_csv(MASTER_CSV, dtype=str, encoding="utf-8-sig").fillna("")


def _manifest_expected_loaded_codes() -> set[str]:
    """
    Devuelve SOLO las provincias realmente integradas al catálogo.

    Prioridad:
    1. manifest.integrated == True
    2. manifest.loaded == True
    3. fallback seguro si no existe ninguno (primeras provincias)
    """
    assert MANIFEST_PATH.exists(), f"No existe manifest: {MANIFEST_PATH}"

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    provinces = data.get("provinces", [])

    codes = {
        str(item["province_code"]).zfill(2)
        for item in provinces
        if item.get("integrated", False) or item.get("loaded", False)
    }

    # 🔁 fallback: si el manifest aún no está versionado correctamente
    if not codes:
        return {"01", "02", "03", "04"}

    return codes


def test_runtime_catalog_csv_is_valid():
    df = _load_master()

    # ✔ estructura mínima
    required_columns = {
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

    missing = required_columns - set(df.columns)
    assert not missing, f"Faltan columnas requeridas: {sorted(missing)}"

    # ✔ catálogo no vacío y creciendo
    assert len(df) > 1000

    # ✔ provincias presentes
    actual_codes = {
        str(code).strip().zfill(2)
        for code in df["province_code"].dropna().unique()
        if str(code).strip()
    }

    expected_codes = _manifest_expected_loaded_codes()

    assert expected_codes.issubset(actual_codes), {
        "missing_from_catalog": sorted(expected_codes - actual_codes),
        "expected_loaded_manifest_codes": sorted(expected_codes),
        "actual_catalog_codes": sorted(actual_codes),
    }


def test_catalog_has_no_duplicate_composite_code():
    df = _load_master()

    duplicated = df[df["composite_code"].duplicated(keep=False)]

    assert duplicated.empty, (
        "El catálogo tiene composite_code duplicados. "
        f"Ejemplos:\n"
        f"{duplicated[['province_code', 'level', 'name', 'composite_code']].head(20).to_string(index=False)}"
    )


def test_catalog_parent_codes_are_resolvable():
    df = _load_master()

    parent_series = df["parent_composite_code"].astype(str).str.strip()
    composite_codes = set(df["composite_code"].astype(str).str.strip())

    non_root = df[parent_series != ""].copy()

    missing_parent = non_root[
        ~non_root["parent_composite_code"].astype(str).str.strip().isin(composite_codes)
    ]

    assert missing_parent.empty, (
        "Hay parent_composite_code sin correspondencia. "
        f"Ejemplos:\n"
        f"{missing_parent[['province_code', 'level', 'name', 'composite_code', 'parent_composite_code']].head(20).to_string(index=False)}"
    )


def test_brisas_del_norte_homonyms_are_valid():
    df = _load_master()

    brisas = df[df["name"].str.casefold().eq("brisas del norte")]

    # ✔ debe haber múltiples ocurrencias (modelo nacional correcto)
    assert len(brisas) >= 3

    # ✔ caso DN correcto
    assert (
        (brisas["composite_code"] == "10-01-01-01-01-001-03")
        & (brisas["parent_composite_code"] == "10-01-01-01-01-001-00")
        & (brisas["level"] == "sub_barrio")
    ).any()

    # ✔ Baoruco barrio/paraje
    assert (
        (brisas["province_code"] == "03")
        & (brisas["level"] == "barrio_paraje")
    ).any()

    # ✔ Baoruco sub_barrio hijo
    assert (
        (brisas["province_code"] == "03")
        & (brisas["level"] == "sub_barrio")
    ).any()


def test_dn_brisas_del_norte_exists_under_los_peralejos():
    df = _load_master()

    dn_brisas = df[
        (df["name"].str.casefold().eq("brisas del norte"))
        & (df["level"] == "sub_barrio")
        & (df["parent_composite_code"] == "10-01-01-01-01-001-00")
    ]

    assert len(dn_brisas) == 1

    row = dn_brisas.iloc[0]

    assert row["composite_code"] == "10-01-01-01-01-001-03"
    assert row["full_path"] == (
        "Distrito Nacional > Santo Domingo de Guzmán > "
        "Santo Domingo de Guzmán > Santo Domingo de Guzmán (Zona urbana) > "
        "Los Peralejos > Brisas del Norte"
    )