def test_catalog_integrity():
    import pandas as pd

    df = pd.read_csv("data/catalog/current/rd_territorial_master.csv", dtype=str).fillna("")

    # composite_code debe ser único
    assert df["composite_code"].is_unique

    # parent_composite_code debe existir en el catálogo
    codes = set(df["composite_code"])

    for parent in df["parent_composite_code"]:
        if parent:
            assert parent in codes

    # niveles válidos
    valid_levels = {
        "province",
        "municipality",
        "district_municipal",
        "section",
        "barrio_paraje",
        "sub_barrio",
        "toponym",
    }

    assert df["level"].isin(valid_levels).all()
