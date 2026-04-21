from __future__ import annotations

import pandas as pd

from scripts.build_master_catalog import transform_source_to_catalog


def test_transform_source_to_catalog_builds_expected_structure():
    df_source = pd.DataFrame(
        [
            {
                "Región": "10",
                "Provincia": "01",
                "Municipio": "00",
                "Distrito municipal": "00",
                "Sección": "00",
                "Barrio/paraje": "000",
                "Sub-barrio": "00",
                "Toponimia o Nombre": "Distrito Nacional",
            },
            {
                "Región": "10",
                "Provincia": "01",
                "Municipio": "01",
                "Distrito municipal": "00",
                "Sección": "00",
                "Barrio/paraje": "000",
                "Sub-barrio": "00",
                "Toponimia o Nombre": "Santo Domingo de Guzmán",
            },
            {
                "Región": "10",
                "Provincia": "01",
                "Municipio": "01",
                "Distrito municipal": "01",
                "Sección": "01",
                "Barrio/paraje": "001",
                "Sub-barrio": "03",
                "Toponimia o Nombre": "Brisas del Norte",
            },
        ]
    )

    out = transform_source_to_catalog(
        df_source,
        source_label="ONE 2021",
        valid_from="2021-01-01",
    )

    assert len(out) == 3
    assert "composite_code" in out.columns
    assert "parent_composite_code" in out.columns
    assert "normalized_name" in out.columns
    assert "full_path" in out.columns

    province = out[out["name"] == "Distrito Nacional"].iloc[0]
    assert province["level"] == "province"
    assert province["composite_code"] == "10-01-00-00-00-000-00"

    municipality = out[out["name"] == "Santo Domingo de Guzmán"].iloc[0]
    assert municipality["level"] == "municipality"
    assert municipality["parent_composite_code"] == "10-01-00-00-00-000-00"

    sub_barrio = out[out["name"] == "Brisas del Norte"].iloc[0]
    assert sub_barrio["level"] == "sub_barrio"
    assert sub_barrio["composite_code"] == "10-01-01-01-01-001-03"
    assert sub_barrio["normalized_name"] == "brisas del norte"
