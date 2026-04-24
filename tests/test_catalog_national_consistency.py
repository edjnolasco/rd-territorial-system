import pandas as pd

MASTER = "data/catalog/current/rd_territorial_master.csv"


def test_every_province_has_municipalities():
    df = pd.read_csv(MASTER, dtype=str).fillna("")

    provinces = df[df["level"] == "province"]["province_code"].unique()

    for code in provinces:
        has_municipality = not df[
            (df["province_code"] == code)
            & (df["level"] == "municipality")
        ].empty

        assert has_municipality, f"Provincia {code} sin municipios"


def test_every_barrio_has_parent():
    df = pd.read_csv(MASTER, dtype=str).fillna("")

    barrios = df[df["level"] == "barrio_paraje"]

    missing = barrios[
        barrios["parent_composite_code"].str.strip() == ""
    ]

    assert missing.empty