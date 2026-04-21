def test_catalog_dn_snapshot():
    import pandas as pd

    df = pd.read_csv("data/catalog/current/rd_territorial_master.csv", dtype=str).fillna("")

    # tamaño base esperado (ajústalo si crece)
    assert len(df) >= 5

    # entidades críticas
    assert "Los Peralejos" in df["name"].values
    assert "Brisas del Norte" in df["name"].values
    assert "Santo Domingo de Guzmán" in df["name"].values
