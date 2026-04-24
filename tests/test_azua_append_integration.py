from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts.build_master_catalog import (
    _read_txt_with_fallback,
    ingest_azua_to_catalog,
    transform_source_to_catalog,
)


FIXTURE = Path("tests/fixtures/azua_sample.txt")


def _write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")


# ----------------------------------------------------------------------
# TEST 1: append no altera filas existentes
# ----------------------------------------------------------------------
def test_append_azua_does_not_touch_existing_rows(tmp_path: Path) -> None:
    master_path = tmp_path / "rd_territorial_master.csv"
    output_path = tmp_path / "rd_territorial_master_candidate.csv"

    master_df = pd.DataFrame(
        [
            {
                "region_code": "01",
                "province_code": "01",
                "municipality_code": "00",
                "district_municipal_code": "00",
                "section_code": "00",
                "barrio_paraje_code": "000",
                "sub_barrio_code": "00",
                "level": "province",
                "name": "Distrito Nacional",
                "official_name": "Distrito Nacional",
                "normalized_name": "distrito nacional",
                "parent_composite_code": "",
                "composite_code": "01-01-00-00-00-000-00",
                "full_path": "Distrito Nacional",
                "is_official": True,
                "source": "BASELINE",
                "valid_from": None,
                "valid_to": None,
                "notes": None,
            },
            {
                "region_code": "01",
                "province_code": "01",
                "municipality_code": "01",
                "district_municipal_code": "00",
                "section_code": "00",
                "barrio_paraje_code": "000",
                "sub_barrio_code": "00",
                "level": "municipality",
                "name": "Distrito Nacional",
                "official_name": "Distrito Nacional",
                "normalized_name": "distrito nacional",
                "parent_composite_code": "01-01-00-00-00-000-00",
                "composite_code": "01-01-01-00-00-000-00",
                "full_path": "Distrito Nacional > Distrito Nacional",
                "is_official": True,
                "source": "BASELINE",
                "valid_from": None,
                "valid_to": None,
                "notes": None,
            },
        ]
    )

    _write_csv(master_path, master_df)

    destination = ingest_azua_to_catalog(
        azua_txt_path=str(FIXTURE),
        master_catalog_path=str(master_path),
        output_catalog_path=str(output_path),
        source_label="AZUA_TEST",
        overwrite_existing=False,
    )

    combined = _read_csv(destination)

    original_dn = combined[
        combined["composite_code"].isin(master_df["composite_code"])
    ]

    assert len(original_dn) == len(master_df)
    assert set(original_dn["name"]) == {"Distrito Nacional"}


# ----------------------------------------------------------------------
# TEST 2: detección de colisiones
# ----------------------------------------------------------------------
def test_append_azua_rejects_collisions(tmp_path: Path) -> None:
    master_path = tmp_path / "rd_territorial_master.csv"
    output_path = tmp_path / "rd_territorial_master_candidate.csv"

    df_source = _read_txt_with_fallback(FIXTURE)
    azua_df = transform_source_to_catalog(df_source, source_label="AZUA_TEST")

    colliding_code = azua_df.iloc[0]["composite_code"]

    master_df = pd.DataFrame(
        [
            {
                "region_code": "99",
                "province_code": "99",
                "municipality_code": "99",
                "district_municipal_code": "99",
                "section_code": "99",
                "barrio_paraje_code": "999",
                "sub_barrio_code": "99",
                "level": "province",
                "name": "Dummy",
                "official_name": "Dummy",
                "normalized_name": "dummy",
                "parent_composite_code": "",
                "composite_code": colliding_code,
                "full_path": "Dummy",
                "is_official": True,
                "source": "BASELINE",
                "valid_from": None,
                "valid_to": None,
                "notes": None,
            }
        ]
    )

    _write_csv(master_path, master_df)

    with pytest.raises(AssertionError, match="Colisión de composite_code"):
        ingest_azua_to_catalog(
            azua_txt_path=str(FIXTURE),
            master_catalog_path=str(master_path),
            output_catalog_path=str(output_path),
            source_label="AZUA_TEST",
            overwrite_existing=False,
        )