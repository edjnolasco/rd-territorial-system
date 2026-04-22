from __future__ import annotations

from pathlib import Path

from scripts.build_master_catalog import _read_txt_with_fallback, transform_source_to_catalog


FIXTURE = Path("tests/fixtures/azua_sample.txt")


def test_build_azua_dataframe_from_fixture() -> None:
    df_source = _read_txt_with_fallback(FIXTURE)
    df_catalog = transform_source_to_catalog(
        df_source,
        source_label="AZUA_TEST",
    )

    assert not df_catalog.empty
    assert "composite_code" in df_catalog.columns
    assert "parent_composite_code" in df_catalog.columns
    assert "level" in df_catalog.columns
    assert "name" in df_catalog.columns
    assert df_catalog["composite_code"].duplicated().sum() == 0


def test_fixture_preserves_repeated_names() -> None:
    df_source = _read_txt_with_fallback(FIXTURE)
    df_catalog = transform_source_to_catalog(
        df_source,
        source_label="AZUA_TEST",
    )

    rows = df_catalog[df_catalog["name"] == "Las Barías"]
    assert len(rows) == 2
    assert rows["composite_code"].nunique() == 2


def test_fixture_builds_valid_parent_chain() -> None:
    df_source = _read_txt_with_fallback(FIXTURE)
    df_catalog = transform_source_to_catalog(
        df_source,
        source_label="AZUA_TEST",
    )

    non_root = df_catalog[df_catalog["parent_composite_code"].fillna("").ne("")]
    missing_parent = non_root.loc[
        ~non_root["parent_composite_code"].isin(df_catalog["composite_code"])
    ]

    assert missing_parent.empty, (
        "Padres inexistentes detectados:\n"
        f"{missing_parent[['composite_code', 'parent_composite_code', 'name', 'level']].to_string(index=False)}"
    )