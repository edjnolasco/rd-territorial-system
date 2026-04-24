from pathlib import Path

import pandas as pd


MASTER_CSV = Path("data/catalog/current/rd_territorial_master.csv")


def test_runtime_catalog_csv_is_valid():
    assert MASTER_CSV.exists(), f"No existe CSV master: {MASTER_CSV}"

    df = pd.read_csv(MASTER_CSV, dtype=str, encoding="utf-8-sig").fillna("")

    assert len(df) == 1554
    assert sorted(df["province_code"].unique()) == ["01", "02", "03"]

    required_columns = {
        "province_code",
        "level",
        "name",
        "normalized_name",
        "composite_code",
        "parent_composite_code",
        "full_path",
    }
    missing = required_columns - set(df.columns)
    assert not missing, f"Faltan columnas requeridas: {sorted(missing)}"


def test_brisas_del_norte_homonyms_are_valid():
    df = pd.read_csv(MASTER_CSV, dtype=str, encoding="utf-8-sig").fillna("")

    brisas = df[df["name"].str.casefold().eq("brisas del norte")]

    assert len(brisas) == 3

    # DN: Brisas del Norte bajo Los Peralejos
    assert (
        (brisas["composite_code"] == "10-01-01-01-01-001-03")
        & (brisas["parent_composite_code"] == "10-01-01-01-01-001-00")
        & (brisas["level"] == "sub_barrio")
    ).any()

    # Baoruco: Brisas del Norte como barrio/paraje
    assert (
        (brisas["province_code"] == "03")
        & (brisas["level"] == "barrio_paraje")
    ).any()

    # Baoruco: Brisas del Norte como sub_barrio hijo del anterior
    assert (
        (brisas["province_code"] == "03")
        & (brisas["level"] == "sub_barrio")
    ).any()

def test_dn_brisas_del_norte_exists_under_los_peralejos():
    df = pd.read_csv(MASTER_CSV, dtype=str, encoding="utf-8-sig").fillna("")

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