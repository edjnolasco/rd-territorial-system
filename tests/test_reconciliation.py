from rd_territorial_system.reconciliation import load_municipality_overrides


def test_load_municipality_overrides(tmp_path) -> None:
    path = tmp_path / "municipality_overrides.csv"
    path.write_text(
        "province_name,municipality_name,gadm_municipality_name\n"
        "Distrito Nacional,Santo Domingo de Guzmán,Santo Domingo de Guzman\n",
        encoding="utf-8",
    )
    mapping = load_municipality_overrides(path)
    assert ("distrito nacional", "santo domingo de guzman") in mapping
